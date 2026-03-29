from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Profile, AdminInviteCode, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_role(current_user.role)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password. Please try again.', 'danger')
            return redirect(url_for('auth.login'))

        if user.role != role:
            flash(f'Role Mismatch: This account is registered as a {user.role.capitalize()}. Please select the correct login role.', 'warning')
            return redirect(url_for('auth.login'))
            
        if user.role == 'company' and getattr(user, 'status', 'Approved') == 'Pending':
            flash('Account Pending: Your company profile is awaiting admin verification.', 'info')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        return redirect_role(user.role)

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    import os
    import uuid
    from flask import current_app
    from werkzeug.utils import secure_filename
    
    if current_user.is_authenticated:
        return redirect_role(current_user.role)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if role not in ['student', 'company', 'admin']:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('auth.register'))

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists.', 'danger')
            return redirect(url_for('auth.register'))

        # Auto-generate unique username since UI doesn't collect explicit 'username' anymore
        base_uname = email.split('@')[0]
        username = f"{base_uname}_{uuid.uuid4().hex[:6]}"

        # Admin Invite Code Validation
        invite_record = None
        if role == 'admin':
            admin_invite_code = request.form.get('admin_invite_code')
            if not admin_invite_code:
                flash('Admin Invite Code is required for Admin registration.', 'danger')
                return redirect(url_for('auth.register'))
            
            invite_record = AdminInviteCode.query.filter_by(code=admin_invite_code, is_used=False).first()
            if not invite_record:
                flash('Invalid or already used Admin Invite Code.', 'danger')
                return redirect(url_for('auth.register'))

        status = 'Pending' if role == 'company' else 'Approved'
        new_user = User(email=email, username=username, password=generate_password_hash(password), role=role, status=status)
        db.session.add(new_user)
        db.session.flush() # To get new_user.id
        
        # Link code if admin
        if role == 'admin' and invite_record:
            invite_record.is_used = True
            invite_record.used_by_id = new_user.id
            db.session.add(invite_record)

        # Profile Processing
        # File Upload Helpers
        def process_upload(file_input_name):
            if file_input_name in request.files:
                val_file = request.files[file_input_name]
                if val_file and val_file.filename != '':
                    original_filename = secure_filename(val_file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
                    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                    val_file.save(save_path)
                    return f"/static/uploads/{unique_filename}"
            return 'default.png'

        if role == 'admin':
            full_name = request.form.get('admin_name')
            new_profile = Profile(user_id=new_user.id, full_name=full_name, rank='Admin')
            
        elif role == 'student':
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            university = request.form.get('university')
            field_of_study = request.form.get('field_of_study')
            skills = request.form.get('skills')
            bio = request.form.get('bio')
            avatar_url = process_upload('student_avatar')
            
            full_name = f"{first_name} {last_name}"
            new_profile = Profile(
                user_id=new_user.id, full_name=full_name, rank='Beginner',
                first_name=first_name, last_name=last_name, university=university,
                field_of_study=field_of_study, skills=skills, bio=bio, avatar=avatar_url
            )
            
        elif role == 'company':
            company_name = request.form.get('company_name')
            country = request.form.get('country')
            website = request.form.get('website')
            description = request.form.get('description')
            logo_url = process_upload('company_avatar')
            
            new_profile = Profile(
                user_id=new_user.id, full_name=company_name, rank='Company',
                company_name=company_name, country=country, website=website, 
                bio=description, avatar=logo_url
            )

        db.session.add(new_profile)
        db.session.commit()

        if role == 'company':
            flash('Registration successful! Please wait for Admin approval before logging in.', 'info')
            return redirect(url_for('auth.login'))
        else:
            login_user(new_user)
            return redirect_role(new_user.role)

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

def redirect_role(role):
    if role == 'student':
        return redirect(url_for('student.dashboard'))
    elif role == 'company':
        return redirect(url_for('company.dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('main.index'))
