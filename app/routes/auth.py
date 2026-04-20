from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, AccessLog
from app.utils import CryptoUtils, KeyManager
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/landing')
def landing():
    """Landing page"""
    return render_template('landing.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate input
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Account is deactivated', 'error')
                return render_template('login.html')
            
            # Log user in
            login_user(user)
            
            # Log access
            log = AccessLog(
                user_id=user.id,
                record_id=None,
                action='view',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                success=True
            )
            db.session.add(log)
            db.session.commit()
            
            # Redirect based on role
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif user.is_doctor():
                return redirect(url_for('records.doctor_dashboard'))
            else:
                return redirect(url_for('records.patient_dashboard'))
        else:
            # Log failed access attempt
            if user:
                log = AccessLog(
                    user_id=user.id,
                    record_id=None,
                    action='view',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    success=False,
                    failure_reason='Invalid password'
                )
                db.session.add(log)
                db.session.commit()
            
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration endpoint"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        
        # Validate input
        if not all([username, email, password, confirm_password, full_name, role]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role
        )
        user.set_password(password)
        
        # Generate RSA key pair for doctor/patient
        if role in ['doctor', 'patient']:
            private_key, public_key = CryptoUtils.generate_rsa_key_pair()
            
            # Save keys to file system
            key_manager = KeyManager()
            private_key_path, public_key_path = key_manager.save_user_keys(
                None, role, private_key, public_key, password
            )
            
            # Store public key in database
            user.public_key = CryptoUtils.serialize_public_key(public_key)
        
        db.session.add(user)
        db.session.commit()
        
        # Update key files with actual user ID
        if role in ['doctor', 'patient']:
            key_manager = KeyManager()
            old_private_path = os.path.join(key_manager.keys_dir, role + 's', f'user_None_private.pem')
            old_public_path = os.path.join(key_manager.keys_dir, role + 's', f'user_None_public.pem')
            
            new_private_path = os.path.join(key_manager.keys_dir, role + 's', f'user_{user.id}_private.pem')
            new_public_path = os.path.join(key_manager.keys_dir, role + 's', f'user_{user.id}_public.pem')
            
            if os.path.exists(old_private_path):
                os.rename(old_private_path, new_private_path)
            if os.path.exists(old_public_path):
                os.rename(old_public_path, new_public_path)
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout endpoint"""
    # Log logout
    log = AccessLog(
        user_id=current_user.id,
        record_id=None,
        action='view',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        success=True
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_new_password')
        
        # Validate input
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error changing password: {str(e)}'}), 500

@auth_bp.route('/regenerate-keys', methods=['POST'])
@login_required
def regenerate_keys():
    """Regenerate user's RSA keys"""
    try:
        password = request.form.get('key_password')
        
        if not password:
            return jsonify({'success': False, 'message': 'Password is required'}), 400
        
        # Verify password
        if not current_user.check_password(password):
            return jsonify({'success': False, 'message': 'Incorrect password'}), 400
        
        # Generate new RSA key pair
        private_key, public_key = CryptoUtils.generate_rsa_key_pair()
        
        # Update user's public key in database
        current_user.public_key = CryptoUtils.serialize_public_key(public_key)
        
        # Save new keys to file system
        key_manager = KeyManager()
        key_manager.save_user_keys(current_user.id, current_user.role, private_key, public_key, password)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'RSA keys regenerated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error regenerating keys: {str(e)}'}), 500

@auth_bp.route('/download-public-key')
@login_required
def download_public_key():
    """Download user's public key"""
    try:
        if not current_user.public_key:
            return jsonify({'success': False, 'message': 'No public key found'}), 404
        
        # Create response with public key
        from flask import Response
        response = Response(
            current_user.public_key,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename={current_user.username}_public_key.pem'}
        )
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error downloading public key: {str(e)}'}), 500
