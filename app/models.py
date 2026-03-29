from . import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'student', 'company', or 'admin'
    status = db.Column(db.String(50), default='Approved') # 'Pending', 'Approved', 'Rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False)
    tasks = db.relationship('Task', backref='company', lazy=True, foreign_keys='Task.company_id')
    submissions = db.relationship('Submission', backref='student', lazy=True, foreign_keys='Submission.student_id')
    sent_messages = db.relationship('Message', backref='sender', lazy='dynamic', foreign_keys='Message.sender_id')
    received_messages = db.relationship('Message', backref='receiver', lazy='dynamic', foreign_keys='Message.receiver_id')
    notifications = db.relationship('Notification', backref='user', lazy=True)
    certificates = db.relationship('Certificate', backref='student', lazy=True)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Shared / Existing
    full_name = db.Column(db.String(150), nullable=True) # Used broadly or distinctively
    bio = db.Column(db.Text, nullable=True)
    skills = db.Column(db.String(500), nullable=True) # comma separated
    avatar = db.Column(db.String(250), nullable=True, default='default.png')
    rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    rank = db.Column(db.String(50), default='Beginner') # Beginner, Intermediate, Expert

    # Student Specific
    first_name = db.Column(db.String(150), nullable=True)
    last_name = db.Column(db.String(150), nullable=True)
    university = db.Column(db.String(250), nullable=True)
    field_of_study = db.Column(db.String(250), nullable=True)

    # Company Specific
    company_name = db.Column(db.String(250), nullable=True)
    country = db.Column(db.String(150), nullable=True)
    website = db.Column(db.String(250), nullable=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(50), nullable=False) # Easy, Medium, Hard
    status = db.Column(db.String(50), default='Open') # Open, In Progress, Completed, Closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    submissions = db.relationship('Submission', backref='task', lazy=True)
    messages = db.relationship('Message', backref='task', lazy=True)
    comments = db.relationship('Comment', backref='task', lazy=True)
    likes = db.relationship('Like', backref='task', lazy=True)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending') # Pending, Approved, Rejected
    file_url = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False) # e.g., 'message', 'submission', 'approval'
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_url = db.Column(db.String(255), nullable=True)
    
    task = db.relationship('Task', backref='certificates', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    user = db.relationship('User', backref='comments')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='likes')

class AdminInviteCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Linked after registration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CourseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    courses = db.relationship('Course', backref='category', lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('course_category.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    thumbnail_url = db.Column(db.String(500), nullable=True) # URL or path to course image
    video_url = db.Column(db.String(500), nullable=True)     # YouTube link
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    lessons = db.relationship('Lesson', backref='course', lazy=True)
    files = db.relationship('CourseFile', backref='course', lazy=True)
    comments = db.relationship(
    'CourseComment',
    backref='course',
    cascade="all, delete-orphan",
    lazy=True
)
class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)
    video_embed_url = db.Column(db.String(500), nullable=True) # E.g., YouTube iframe src
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CourseFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CourseComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('course_comment.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ أضف السطر ده
    user = db.relationship('User', backref='course_comments')
    
class PlatformConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
