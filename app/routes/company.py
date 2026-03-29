from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Task, Submission, Profile, User, Certificate, Notification, db

company_bp = Blueprint('company', __name__)

def company_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.role != 'company':
            flash('Access denied. Companies only.', 'danger')
            return redirect(url_for('main.index'))
        if getattr(current_user, 'status', 'Approved') != 'Approved':
            flash('Access denied. Your company account is pending approval.', 'danger')
            return redirect(url_for('main.index'))
        return func(*args, **kwargs)
    return decorated_view

@company_bp.route('/dashboard')
@login_required
@company_required
def dashboard():
    tasks = current_user.tasks
    return render_template('company/dashboard.html', tasks=tasks)

@company_bp.route('/task/new', methods=['GET', 'POST'])
@login_required
@company_required
def create_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        difficulty = request.form.get('difficulty')
        
        task = Task(title=title, description=description, difficulty=difficulty, company_id=current_user.id)
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully.', 'success')
        return redirect(url_for('company.dashboard'))
        
    return render_template('company/create_task.html')

@company_bp.route('/task/<int:task_id>/submissions')
@login_required
@company_required
def task_submissions(task_id):
    task = Task.query.get_or_404(task_id)
    if task.company_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.dashboard'))
        
    submissions = Submission.query.filter_by(task_id=task.id).all()
    return render_template('company/submissions.html', task=task, submissions=submissions)

@company_bp.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
@company_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.company_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('company.dashboard'))
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully.', 'success')
    return redirect(url_for('company.dashboard'))

@company_bp.route('/submission/<int:submission_id>/review', methods=['POST'])
@login_required
@company_required
def review_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    task = submission.task
    if task.company_id != current_user.id:
        return 'Unauthorized', 403
        
    action = request.form.get('action') # 'approve' or 'reject'
    student = User.query.get(submission.student_id)
    student_profile = Profile.query.filter_by(user_id=student.id).first()

    if action == 'approve':
        submission.status = 'Approved'
        # Grant Certificate
        cert = Certificate(student_id=student.id, task_id=task.id)
        db.session.add(cert)
        
        # Increase Rating
        if student_profile:
            student_profile.rating += int(request.form.get('rating', 5))
            student_profile.rating_count += 1
            
        # Notify
        note = Notification(user_id=student.id, type='approval', content=f'Your submission for "{task.title}" was approved!')
        db.session.add(note)
        
    elif action == 'reject':
        submission.status = 'Rejected'
        # Notify
        note = Notification(user_id=student.id, type='rejection', content=f'Your submission for "{task.title}" was rejected. Please review feedback.')
        db.session.add(note)

    db.session.commit()
    flash(f"Submission {action}d successfully.", 'success')
    return redirect(url_for('company.task_submissions', task_id=task.id))
