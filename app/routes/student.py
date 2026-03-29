from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Task, Submission, db, Certificate

student_bp = Blueprint('student', __name__)

def student_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.role != 'student':
            flash('Access denied. Students only.', 'danger')
            return redirect(url_for('main.index'))
        return func(*args, **kwargs)
    return decorated_view

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    # User Profile Data
    profile = current_user.profile
    
    # Active Tasks
    active_submissions = Submission.query.filter_by(student_id=current_user.id).filter(Submission.status != 'Approved').all()
    active_tasks = [sub.task for sub in active_submissions]
    
    # Completed Tasks / Certificates
    certificates = Certificate.query.filter_by(student_id=current_user.id).all()
    
    return render_template('student/dashboard.html', 
                             profile=profile, 
                             active_tasks=active_tasks, 
                             active_submissions=active_submissions, 
                             certificates=certificates)

@student_bp.route('/tasks')
@login_required
@student_required
def browse_tasks():
    # Filter out tasks the student already applied to or completed
    my_sub_task_ids = [sub.task_id for sub in current_user.submissions]
    available_tasks = Task.query.filter(Task.status == 'Open').filter(~Task.id.in_(my_sub_task_ids) if my_sub_task_ids else True).all()
    return render_template('student/tasks.html', tasks=available_tasks)

@student_bp.route('/task/<int:task_id>/start', methods=['POST'])
@login_required
@student_required
def start_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.status != 'Open':
        flash('This task is no longer open.', 'danger')
        return redirect(url_for('student.browse_tasks'))
        
    # Check duplicate submission
    existing = Submission.query.filter_by(student_id=current_user.id, task_id=task.id).first()
    if existing:
        flash('You have already started this task.', 'warning')
        return redirect(url_for('student.task_workspace', task_id=task.id))
        
    # Create submission (Pending work)
    submission = Submission(student_id=current_user.id, task_id=task.id, status='In Progress')
    db.session.add(submission)
    db.session.commit()
    
    # Redirect directly to chat for this task
    return redirect(url_for('chat.inbox', task_id=task.id))

@student_bp.route('/task/<int:task_id>/workspace')
@login_required
@student_required
def task_workspace(task_id):
    task = Task.query.get_or_404(task_id)
    # Get submission details
    submission = Submission.query.filter_by(student_id=current_user.id, task_id=task.id).first()
    if not submission:
        flash('You must start the task first.', 'warning')
        return redirect(url_for('student.browse_tasks'))
        
    return render_template('task_workspace.html', task=task, submission=submission)
