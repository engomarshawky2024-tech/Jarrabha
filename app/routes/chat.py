import os
import uuid
from flask import Blueprint, jsonify, request, current_app, render_template, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Message, Task, db, Notification

chat_bp = Blueprint('chat', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar', 'doc', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@chat_bp.route('/<int:task_id>/messages/<int:receiver_id>', methods=['GET'])
@chat_bp.route('/<int:task_id>/messages', methods=['GET'])
@login_required
def get_messages(task_id, receiver_id=None):
    # Only allow participants
    task = Task.query.get_or_404(task_id)
    
    # Needs logic based on whether we pass receiver_id to filter the exact thread
    if current_user.role == 'student':
        from app.models import Submission
        sub = Submission.query.filter_by(student_id=current_user.id, task_id=task.id).first()
        if not sub:
            return jsonify({'error': 'Unauthorized'}), 403
        partner_id = task.company_id
    elif current_user.role == 'company':
        if task.company_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        partner_id = receiver_id if receiver_id else request.args.get('student_id')
        if not partner_id:
            return jsonify({'error': 'Missing student_id constraint for company view'}), 400
    else:
        # Admin can maybe see? Deny for now unless strictly needed
        return jsonify({'error': 'Unauthorized'}), 403
            
    # Fetch messages between current_user and partner_id for this task
    messages = Message.query.filter(
        (Message.task_id == task.id) & 
        (
            ((Message.sender_id == current_user.id) & (Message.receiver_id == partner_id)) |
            ((Message.sender_id == partner_id) & (Message.receiver_id == current_user.id))
        )
    ).order_by(Message.timestamp.asc()).all()
    
    data = []
    for msg in messages:
        if msg.receiver_id == current_user.id and not msg.is_read:
            msg.is_read = True
            
        data.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'receiver_id': msg.receiver_id,
            'content': msg.content,
            'file_url': msg.file_url,
            'is_read': msg.is_read,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    db.session.commit()
    return jsonify(data)

@chat_bp.route('/<int:task_id>/send', methods=['POST'])
@login_required
def send_message(task_id):
    # Support both JSON and form data
    if request.is_json:
        content = request.json.get('content')
        receiver_id = request.json.get('receiver_id')
    else:
        content = request.form.get('content', '')
        receiver_id = request.form.get('receiver_id')
        
    task = Task.query.get_or_404(task_id)
    
    # Determine receiver automatically if student
    if current_user.role == 'student':
        receiver_id = task.company_id
    elif current_user.role == 'company':
        if not receiver_id:
             return jsonify({'error': 'Receiver required for company response'}), 400
    else:
        return jsonify({'error': 'Action not permitted'}), 403
        
    file_url = None
    
    # Handle File Upload
    if 'file' in request.files:
        val_file = request.files['file']
        if val_file and val_file.filename != '':
            if not allowed_file(val_file.filename):
                return jsonify({'error': 'Invalid file type'}), 400
                
            # Check size
            val_file.seek(0, os.SEEK_END)
            file_size = val_file.tell()
            val_file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                return jsonify({'error': 'File exceeds 10MB limit'}), 400
                
            original_filename = secure_filename(val_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            val_file.save(save_path)
            file_url = f"/static/uploads/{unique_filename}"
            
    if not content and not file_url:
        return jsonify({'error': 'Content or file required'}), 400
            
    msg = Message(task_id=task.id, sender_id=current_user.id, receiver_id=receiver_id, content=content, file_url=file_url)
    db.session.add(msg)
    
    # Task Workflow: File sent in chat = task submission
    if file_url and current_user.role == 'student':
        from app.models import Submission
        # Check if one exists
        sub = Submission.query.filter_by(task_id=task.id, student_id=current_user.id).first()
        if sub:
            sub.file_url = file_url
            sub.notes = content
        else:
            sub = Submission(task_id=task.id, student_id=current_user.id, file_url=file_url, notes=content)
            db.session.add(sub)
            
    # Create notification for the receiver
    note = Notification(user_id=receiver_id, type='message', content=f'New message regarding "{task.title}"')
    db.session.add(note)
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'msg': {
            'id': msg.id,
            'content': msg.content,
            'file_url': msg.file_url,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@chat_bp.route('/inbox', methods=['GET'])
@login_required
def inbox():
    from app.models import User, Submission
    active_task_id = request.args.get('task_id', type=int)
    student_id = request.args.get('student_id', type=int)
    
    threads = []
    
    if current_user.role == 'student':
        involved_msgs = Message.query.filter(
            (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
        ).all()
        task_ids = set([m.task_id for m in involved_msgs])
        if active_task_id:
            task_ids.add(active_task_id)
            
        tasks = Task.query.filter(Task.id.in_(task_ids)).all() if task_ids else []
        for t in tasks:
            threads.append({
                'task': t,
                'target_user': User.query.get(t.company_id),
                'url': url_for('chat.inbox', task_id=t.id)
            })
            
    elif current_user.role == 'company':
        msgs = Message.query.filter(
            (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
        ).all()
        
        pairs = set()
        for m in msgs:
            s_id = m.receiver_id if m.sender_id == current_user.id else m.sender_id
            pairs.add((m.task_id, s_id))
            
        for t_id, s_id in pairs:
            t = Task.query.get(t_id)
            s = User.query.get(s_id)
            if t and s:
                threads.append({
                    'task': t,
                    'target_user': s,
                    'url': url_for('chat.inbox', task_id=t.id, student_id=s.id)
                })

    active_task = None
    target_user = None
    if active_task_id:
        active_task = Task.query.get(active_task_id)
        if current_user.role == 'student':
            target_user = User.query.get(active_task.company_id)
        elif current_user.role == 'company' and student_id:
            target_user = User.query.get(student_id)

    return render_template('chat/inbox.html', threads=threads, active_task=active_task, target_user=target_user)

@chat_bp.route('/<int:task_id>/messages/<int:msg_id>', methods=['PUT'])
@login_required
def edit_message(task_id, msg_id):
    msg = Message.query.get_or_404(msg_id)
    if msg.sender_id != current_user.id or msg.task_id != task_id:
        return jsonify({'error': 'Unauthorized action'}), 403
    content = request.json.get('content')
    if not content:
        return jsonify({'error': 'Content cannot be empty'}), 400
    msg.content = content
    db.session.commit()
    return jsonify({'success': True})

@chat_bp.route('/<int:task_id>/messages/<int:msg_id>', methods=['DELETE'])
@login_required
def delete_message(task_id, msg_id):
    msg = Message.query.get_or_404(msg_id)
    if msg.sender_id != current_user.id or msg.task_id != task_id:
        return jsonify({'error': 'Unauthorized action'}), 403
    db.session.delete(msg)
    db.session.commit()
    return jsonify({'success': True})

@chat_bp.route('/unread_count', methods=['GET'])
@login_required
def get_unread_count():
    count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})
