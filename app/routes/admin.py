from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, MedicalRecord, AccessLog
from app.utils import CryptoUtils, KeyManager
import os
import random
import string

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
def check_admin():
    """Ensure only admin can access admin routes"""
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('auth.login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard with system overview"""
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    # Get statistics
    total_users = User.query.count()
    total_doctors = User.query.filter_by(role='doctor').count()
    total_patients = User.query.filter_by(role='patient').count()
    total_records = MedicalRecord.query.count()
    
    # Get recent activity
    recent_logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', 
                         total_users=total_users,
                         total_doctors=total_doctors,
                         total_patients=total_patients,
                         total_records=total_records,
                         recent_logs=recent_logs)

@admin_bp.route('/users')
@login_required
def users_list():
    """List all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    """Create new user"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    if request.method == 'GET':
        return render_template('admin_create_user.html')
    
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        is_active = request.form.get('is_active') == 'on'
        
        # Validate input
        if not all([username, email, password, full_name, role]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if len(password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            is_active=is_active
        )
        user.set_password(password)
        
        # Generate RSA key pair for doctor/patient
        if role in ['doctor', 'patient']:
            private_key, public_key = CryptoUtils.generate_rsa_key_pair()
            user.public_key = CryptoUtils.serialize_public_key(public_key)
            
            # Save keys to file system
            key_manager = KeyManager()
            key_manager.save_user_keys(user.id, role, private_key, public_key, password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User created successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error creating user: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>')
@login_required
def get_user(user_id):
    """Get user data for editing"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'is_active': user.is_active
    })

@admin_bp.route('/users/<int:user_id>', methods=['POST'])
@login_required
def update_user():
    """Update existing user"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        is_active = request.form.get('is_active') == 'on'
        
        user = User.query.get_or_404(user_id)
        
        # Check if username/email already exists for other users
        if User.query.filter(User.username == username, User.id != user_id).first():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        if User.query.filter(User.email == email, User.id != user_id).first():
            return jsonify({'success': False, 'message': 'Email already exists'}), 400
        
        # Update user
        user.username = username
        user.email = email
        user.full_name = full_name
        user.role = role
        user.is_active = is_active
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating user: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
def reset_user_password(user_id):
    """Reset user password"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        # Use user_id from URL parameter, not form data
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        user = User.query.get_or_404(user_id)
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password reset successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error resetting password: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Delete user"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent deletion of admin users
        if user.is_admin():
            return jsonify({'success': False, 'message': 'Cannot delete admin users'}), 400
        
        # Check if user has medical records that need to be deleted first
        medical_records = MedicalRecord.query.filter(
            (MedicalRecord.doctor_id == user_id) | (MedicalRecord.patient_id == user_id)
        ).all()
        
        if medical_records:
            # Delete medical records first to avoid foreign key constraints
            for record in medical_records:
                db.session.delete(record)
            db.session.commit()
        
        # Check if user has access logs that need to be deleted
        access_logs = AccessLog.query.filter_by(user_id=user_id).all()
        if access_logs:
            for log in access_logs:
                db.session.delete(log)
            db.session.commit()
        
        # Delete user's key files (with error handling)
        try:
            key_manager = KeyManager()
            if user.is_doctor():
                private_key_path = os.path.join(key_manager.doctors_dir, f'user_{user_id}_private.pem')
                public_key_path = os.path.join(key_manager.doctors_dir, f'user_{user_id}_public.pem')
            elif user.is_patient():
                private_key_path = os.path.join(key_manager.patients_dir, f'user_{user_id}_private.pem')
                public_key_path = os.path.join(key_manager.patients_dir, f'user_{user_id}_public.pem')
            else:
                private_key_path = None
                public_key_path = None
            
            if private_key_path and os.path.exists(private_key_path):
                os.remove(private_key_path)
            if public_key_path and os.path.exists(public_key_path):
                os.remove(public_key_path)
        except Exception as key_error:
            # Log key deletion error but don't fail the user deletion
            print(f"Warning: Could not delete key files for user {user_id}: {str(key_error)}")
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error deleting user: {str(e)}'
        print(f"Delete user error: {error_msg}")  # Debug logging
        return jsonify({'success': False, 'message': error_msg}), 500

@admin_bp.route('/records')
@login_required
def records_list():
    """List all medical records"""
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    records = MedicalRecord.query.order_by(MedicalRecord.created_at.desc()).all()
    return render_template('admin_records.html', records=records)

@admin_bp.route('/records/<int:record_id>')
@login_required
def get_record(record_id):
    """Get record details for admin"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    record = MedicalRecord.query.get_or_404(record_id)
    return jsonify({
        'success': True,
        'record': {
            'id': record.id,
            'original_filename': record.original_filename,
            'file_size': record.file_size,
            'file_size_formatted': "%.2f MB" % (record.file_size / (1024 * 1024)),
            'mime_type': record.mime_type,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'accessed_at': record.accessed_at.strftime('%Y-%m-%d %H:%M:%S') if record.accessed_at else None,
            'access_count': record.access_count,
            'patient_full_name': record.patient.full_name if record.patient else 'Unknown',
            'patient_email': record.patient.email if record.patient else 'Unknown',
            'doctor_full_name': record.doctor.full_name if record.doctor else 'Unknown',
            'doctor_email': record.doctor.email if record.doctor else 'Unknown'
        }
    })

@admin_bp.route('/records/<int:record_id>', methods=['DELETE'])
@login_required
def delete_record_admin(record_id):
    """Delete medical record (admin only)"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        record = MedicalRecord.query.get_or_404(record_id)
        
        # Log deletion
        log = AccessLog(
            user_id=current_user.id,
            record_id=record.id,
            action='delete',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=True
        )
        db.session.add(log)
        
        # Delete record (cascade will handle related data)
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Medical record deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting record: {str(e)}'}), 500

@admin_bp.route('/logs')
@login_required
def access_logs():
    """View access logs"""
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Build query with filters
    query = AccessLog.query
    
    # Apply filters
    action_filter = request.args.get('action')
    if action_filter:
        query = query.filter(AccessLog.action == action_filter)
    
    success_filter = request.args.get('success')
    if success_filter is not None:
        success_bool = success_filter == 'true'
        query = query.filter(AccessLog.success == success_bool)
    
    date_filter = request.args.get('date')
    if date_filter:
        query = query.filter(AccessLog.timestamp >= date_filter)
    
    user_filter = request.args.get('user')
    if user_filter:
        query = query.join(User).filter(User.username.contains(user_filter))
    
    ip_filter = request.args.get('ip')
    if ip_filter:
        query = query.filter(AccessLog.ip_address.contains(ip_filter))
    
    # Order by timestamp
    query = query.order_by(AccessLog.timestamp.desc())
    
    # Paginate
    logs = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Calculate statistics
    total_logs = AccessLog.query.count()
    success_count = AccessLog.query.filter_by(success=True).count()
    failed_count = AccessLog.query.filter_by(success=False).count()
    unique_ips = db.session.query(AccessLog.ip_address).distinct().count()
    
    return render_template('admin_logs.html', 
                         logs=logs,
                         total_logs=total_logs,
                         success_count=success_count,
                         failed_count=failed_count,
                         unique_ips=unique_ips)

@admin_bp.route('/status')
@login_required
def system_status():
    """System status and health check"""
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    # Database status
    try:
        db.session.execute('SELECT 1')
        db_status = 'Healthy'
    except Exception:
        db_status = 'Error'
    
    # Key storage status
    key_manager = KeyManager()
    doctors_keys_exist = os.path.exists(key_manager.doctors_dir)
    patients_keys_exist = os.path.exists(key_manager.patients_dir)
    
    # Storage statistics
    total_records = MedicalRecord.query.count()
    try:
        total_storage = sum(len(record.encrypted_file) for record in MedicalRecord.query.all())
    except Exception:
        total_storage = 0
    
    return render_template('admin_status.html',
                         db_status=db_status,
                         doctors_keys_exist=doctors_keys_exist,
                         patients_keys_exist=patients_keys_exist,
                         total_records=total_records,
                         total_storage=total_storage)
