from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'jarrabha-super-secret-key-12345'
    
    # Environment variable for DB config, fallback to SQLite
    db_uri = os.environ.get('DATABASE_URL', 'sqlite:///jarrabha.db')
    if db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    with app.app_context():
        from .models import User, AdminInviteCode
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        # Register Blueprints
        from .routes.auth import auth_bp
        from .routes.main import main_bp
        from .routes.student import student_bp
        from .routes.company import company_bp
        from .routes.chat import chat_bp
        from .routes.admin import admin_bp
        from .routes.course import course_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(student_bp, url_prefix='/student')
        app.register_blueprint(company_bp, url_prefix='/company')
        app.register_blueprint(chat_bp, url_prefix='/chat')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(course_bp, url_prefix='/course')
        
        db.create_all()

        # Generate up to 10 Admin Invite Codes on startup if fewer exist
        existing_count = AdminInviteCode.query.count()
        target_total = 10
        if existing_count < target_total:
            import random
            import string
            print("--- GENERATING ADMIN INVITE CODES ---")
            for _ in range(target_total - existing_count):
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                new_code = AdminInviteCode(code=code)
                db.session.add(new_code)
                print(f"ADMIN CODE: {code}")
            db.session.commit()
            print("--- ADMIN INVITE CODES SAVED ---")
        else:
            print(f"Admin invite codes already at target count ({existing_count}). No new codes generated.")

    return app
