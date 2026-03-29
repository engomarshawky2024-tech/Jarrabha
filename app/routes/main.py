from flask import Blueprint, render_template
from flask_login import current_user
from app.models import Profile, User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'student':
            from flask import redirect, url_for
            return redirect(url_for('student.dashboard'))
        elif current_user.role == 'company':
            from flask import redirect, url_for
            return redirect(url_for('company.dashboard'))
        elif current_user.role == 'admin':
            from flask import redirect, url_for
            return redirect(url_for('admin.dashboard'))
            
    from app.models import Task, Certificate
    stats = {
        'students_count': User.query.filter_by(role='student').count(),
        'companies_count': User.query.filter_by(role='company').count(),
        'tasks_completed': Task.query.filter_by(status='Completed').count(),
        'certs_issued': Certificate.query.count()
    }
    return render_template('index.html', stats=stats)

@main_bp.route('/leaderboard')
def leaderboard():
    # Show students ranked by rating
    top_students = Profile.query.join(User).filter(User.role == 'student').order_by(Profile.rating.desc()).limit(10).all()
    return render_template('leaderboard.html', top_students=top_students)

@main_bp.route('/api/ai-config')
def get_ai_config():
    from app.models import PlatformConfig
    from flask import jsonify
    
    # Get all configs and convert to dict
    all_configs = PlatformConfig.query.all()
    config_dict = {c.key: c.value for c in all_configs}
    
    # Defaults if not set
    return jsonify({
        'welcome_message': config_dict.get('ai_welcome_message', 'Greetings. I am the Jarrabha Orbital Assistant. How can I guide your mission today?'),
        'system_instruction': config_dict.get('ai_system_instruction', 'You are the Jarrabha AI assistant. You help users navigate the freelance platform. Be professional, concise, and helpful.')
    })
