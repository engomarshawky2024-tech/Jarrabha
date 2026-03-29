from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models import Course, CourseCategory, CourseComment, CourseFile, db

course_bp = Blueprint('course', __name__)

@course_bp.route('/', methods=['GET'])
@login_required
def browse_courses():
    courses = Course.query.filter_by(is_published=True).all()
    categories = CourseCategory.query.all()
    # Admin can see unpublished
    if current_user.role == 'admin':
        courses = Course.query.all()
        
    return render_template('course/browse.html', courses=courses, categories=categories)

@course_bp.route('/<int:course_id>', methods=['GET'])
@login_required
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    if not course.is_published and current_user.role != 'admin':
        flash('Course not available.', 'danger')
        return redirect(url_for('course.browse_courses'))
        
    comments = CourseComment.query.filter_by(course_id=course.id, parent_id=None).order_by(CourseComment.timestamp.desc()).all()
    
    return render_template('course/view.html', course=course, comments=comments)

@course_bp.route('/<int:course_id>/comment', methods=['POST'])
@login_required
def add_comment(course_id):
    course = Course.query.get_or_404(course_id)
    if not course.is_published and current_user.role != 'admin':
        return jsonify({'error': 'Not allowing comments'}), 403
        
    content = request.form.get('content')
    parent_id = request.form.get('parent_id')
    
    if not content:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('course.view_course', course_id=course_id))
        
    if parent_id and parent_id.isdigit():
        parent_id = int(parent_id)
    else:
        parent_id = None
        
    comment = CourseComment(course_id=course_id, user_id=current_user.id, content=content, parent_id=parent_id)
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added.', 'success')
    return redirect(url_for('course.view_course', course_id=course_id))

@course_bp.route('/comment/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    comment = CourseComment.query.get_or_404(comment_id)
    comment.likes += 1
    db.session.commit()
    return jsonify({'success': True, 'likes': comment.likes})
