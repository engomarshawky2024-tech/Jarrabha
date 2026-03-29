from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import User, Task, Course, CourseCategory, AdminInviteCode
from .. import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def require_admin():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/dashboard')
def dashboard():
    users_count = User.query.count()
    tasks_count = Task.query.count()
    courses_count = Course.query.count()
    codes = AdminInviteCode.query.all()
    
    return render_template('admin/dashboard.html', 
                           users_count=users_count,
                           tasks_count=tasks_count,
                           courses_count=courses_count,
                           codes=codes)

@admin_bp.route('/courses')
def manage_courses():
    courses = Course.query.all()
    categories = CourseCategory.query.all()
    return render_template('admin/courses.html', courses=courses, categories=categories)

@admin_bp.route('/course/new', methods=['POST'])
def add_course():
    import os
    import uuid
    from flask import current_app
    from werkzeug.utils import secure_filename
    
    title = request.form.get('title')
    description = request.form.get('description')
    category_id = request.form.get('category_id')
    video_url = request.form.get('video_url')
    is_published = True if request.form.get('is_published') else False
    
    thumbnail_url = None
    if 'thumbnail' in request.files:
        val_file = request.files['thumbnail']
        if val_file and val_file.filename != '':
            original_filename = secure_filename(val_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            val_file.save(save_path)
            thumbnail_url = f"/static/uploads/{unique_filename}"
    
    if not category_id:
        cat = CourseCategory.query.first()
        if not cat:
            cat = CourseCategory(name="General")
            db.session.add(cat)
            db.session.commit()
        category_id = cat.id
        
    course = Course(title=title, description=description, category_id=category_id, 
                    thumbnail_url=thumbnail_url, video_url=video_url, is_published=is_published)
    db.session.add(course)
    db.session.commit()
    flash('Course deployed to orbit successfully.', 'success')
    return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
def edit_course(course_id):
    import os
    import uuid
    from flask import current_app
    from werkzeug.utils import secure_filename
    
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.is_published = True if request.form.get('is_published') else False
        
        lesson_title = request.form.get('lesson_title')
        lesson_content = request.form.get('lesson_content')
        lesson_video = request.form.get('lesson_video')
        if lesson_title and lesson_content:
            from ..models import Lesson
            lesson = Lesson(course_id=course.id, title=lesson_title, content=lesson_content, video_embed_url=lesson_video)
            db.session.add(lesson)
            
        if 'course_file' in request.files:
            val_file = request.files['course_file']
            if val_file and val_file.filename != '':
                original_filename = secure_filename(val_file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                val_file.save(save_path)
                file_url = f"/static/uploads/{unique_filename}"
                from ..models import CourseFile
                c_file = CourseFile(course_id=course.id, filename=original_filename, file_url=file_url)
                db.session.add(c_file)
                
        db.session.commit()
        flash('Course updated successfully.', 'success')
        return redirect(url_for('admin.edit_course', course_id=course.id))
        
    return render_template('admin/edit_course.html', course=course)

@admin_bp.route('/course/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted.', 'success')
    return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/users')
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/approve', methods=['POST'])
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'Approved'
    db.session.commit()
    flash('User approved.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/reject', methods=['POST'])
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'Rejected'
    db.session.commit()
    flash('User rejected.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Cannot delete yourself.', 'danger')
        return redirect(url_for('admin.manage_users'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/chats')
def global_chats():
    from ..models import Message
    # Fetch all unique conversation threads
    # For a simple representation, we'll get last 50 messages
    messages = Message.query.order_by(Message.timestamp.desc()).limit(100).all()
    return render_template('admin/chats.html', messages=messages)

@admin_bp.route('/ai-config', methods=['GET', 'POST'])
def ai_config():
    from ..models import PlatformConfig
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('config_'):
                clean_key = key.replace('config_', '')
                cfg = PlatformConfig.query.filter_by(key=clean_key).first()
                if not cfg:
                    cfg = PlatformConfig(key=clean_key)
                    db.session.add(cfg)
                cfg.value = value
        db.session.commit()
        flash('AI Intelligence parameters updated.', 'success')
        return redirect(url_for('admin.ai_config'))
    
    configs = {cfg.key: cfg.value for cfg in PlatformConfig.query.all()}
    # Ensure default keys exist
    defaults = {
        'ai_system_instruction': 'You are the Jarrabha Orbital Assistant. Help users navigate the platform, suggest missions, and explain learning paths.',
        'ai_welcome_message': 'Establishing connection... How can I assist your mission today?'
    }
    for k, v in defaults.items():
        if k not in configs:
            configs[k] = v
            
    return render_template('admin/ai_config.html', configs=configs)
