from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, MedicalRecord, AccessLog
from app.utils import CryptoUtils, KeyManager, SecurityUtils
import os
import tempfile
from datetime import datetime

records_bp = Blueprint('records', __name__)

@records_bp.before_request
def check_records_access():
    """Ensure proper access to records routes"""
    # Allow access to login and register routes
    if request.endpoint and ('login' in request.endpoint or 'register' in request.endpoint):
        return
    
    # Check if user is authenticated for protected routes
    if request.endpoint and not request.endpoint.endswith('login') and not request.endpoint.endswith('register'):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

@records_bp.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    """Doctor dashboard - view and upload records"""
    if not current_user.is_doctor():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    # Get all patients
    patients = User.query.filter_by(role='patient', is_active=True).all()
    
    # Get records uploaded by this doctor
    records = MedicalRecord.query.filter_by(doctor_id=current_user.id).order_by(MedicalRecord.created_at.desc()).all()
    
    return render_template('doctor_dashboard.html', patients=patients, records=records)

@records_bp.route('/patient/dashboard')
@login_required
def patient_dashboard():
    """Patient dashboard - view own records"""
    if not current_user.is_patient():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    # Get records for this patient
    records = MedicalRecord.query.filter_by(patient_id=current_user.id).order_by(MedicalRecord.created_at.desc()).all()
    
    return render_template('patient_dashboard.html', records=records)

@records_bp.route('/upload', methods=['POST'])
@login_required
def upload_record():
    """Upload and encrypt medical record"""
    if not current_user.is_doctor():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        patient_id = request.form.get('patient_id')
        file = request.files.get('medical_file')
        
        if not patient_id or not file:
            return jsonify({'success': False, 'message': 'Patient and file are required'}), 400
        
        # Validate patient exists
        patient = User.query.filter_by(id=patient_id, role='patient').first()
        if not patient:
            return jsonify({'success': False, 'message': 'Invalid patient'}), 400
        
        # Validate file
        is_valid, message = SecurityUtils.validate_file_upload(file)
        if not is_valid:
            return jsonify({'success': False, 'message': message}), 400
        
        # Read file data
        file_data = file.read()
        original_filename = SecurityUtils.sanitize_filename(file.filename)
        
        # Step 1: Generate AES key
        aes_key = CryptoUtils.generate_aes_key()
        
        # Step 2: Encrypt medical record using AES
        encrypted_file = CryptoUtils.encrypt_aes(file_data, aes_key)
        
        # Step 3: Get patient's public key and encrypt AES key
        if not patient.public_key:
            return jsonify({'success': False, 'message': 'Patient has no public key'}), 400
        
        patient_public_key = CryptoUtils.load_public_key(patient.public_key)
        encrypted_aes_key = CryptoUtils.encrypt_rsa(aes_key, patient_public_key)
        
        # Step 4: Generate SHA-256 hash of original file
        file_hash = CryptoUtils.calculate_sha256(file_data)
        
        # Step 5: Digitally sign the hash using doctor's private key
        key_manager = KeyManager()
        
        # Try to load doctor's private key - if it's encrypted, we need the password
        try:
            doctor_private_key = key_manager.load_user_private_key(current_user.id, 'doctor')
        except Exception as e:
            # If private key is encrypted, we need the password from the form
            doctor_password = request.form.get('doctor_password')
            if not doctor_password:
                return jsonify({'success': False, 'message': 'Doctor password required for digital signature'}), 400
            
            try:
                doctor_private_key = key_manager.load_user_private_key(current_user.id, 'doctor', doctor_password)
            except Exception as e:
                return jsonify({'success': False, 'message': f'Invalid doctor password: {str(e)}'}), 400
        
        digital_signature = CryptoUtils.sign_data(file_data, doctor_private_key)
        
        # Step 6: Store in database
        record = MedicalRecord(
            patient_id=patient_id,
            doctor_id=current_user.id,
            encrypted_file=encrypted_file,
            encrypted_aes_key=encrypted_aes_key,
            file_hash=file_hash,
            digital_signature=digital_signature,
            original_filename=original_filename,
            file_size=len(file_data),
            mime_type=file.content_type or 'application/octet-stream'
        )
        
        db.session.add(record)
        db.session.commit()
        
        # Log successful upload
        log = AccessLog(
            user_id=current_user.id,
            record_id=record.id,
            action='upload',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=True
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Record uploaded successfully'})
        
    except Exception as e:
        db.session.rollback()
        # Log failed upload
        log = AccessLog(
            user_id=current_user.id,
            record_id=None,
            action='upload',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=False,
            failure_reason=str(e)
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500

@records_bp.route('/details/<int:record_id>')
@login_required
def get_record_details(record_id):
    """Get record details for display"""
    try:
        # Get record
        record = MedicalRecord.query.get_or_404(record_id)
        
        # Check access permissions
        if current_user.is_patient() and record.patient_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        if current_user.is_doctor() and record.doctor_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Return record details
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
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@records_bp.route('/view/<int:record_id>')
@login_required
def view_record(record_id):
    """View and decrypt medical record"""
    try:
        # Get record
        record = MedicalRecord.query.get_or_404(record_id)
        
        # Check access permissions
        if current_user.is_patient() and record.patient_id != current_user.id:
            flash('Access denied', 'error')
            return redirect(url_for('records.patient_dashboard'))
        
        if current_user.is_doctor() and record.doctor_id != current_user.id:
            flash('Access denied', 'error')
            return redirect(url_for('records.doctor_dashboard'))
        
        # For testing: Try to get the raw file content first
        try:
            # Step 1: Get encrypted AES key
            encrypted_aes_key = record.encrypted_aes_key
            
            # Step 2: Patient's private key decrypts AES key
            if current_user.is_patient():
                try:
                    key_manager = KeyManager()
                    patient_private_key = key_manager.load_user_private_key(current_user.id, 'patient')
                    if not patient_private_key:
                        flash('Patient private key not found. Please regenerate your keys.', 'error')
                        return redirect(url_for('records.patient_dashboard'))
                    aes_key = CryptoUtils.decrypt_rsa(encrypted_aes_key, patient_private_key)
                except Exception as e:
                    flash(f'Error with patient keys: {str(e)}. Please regenerate your keys.', 'error')
                    return redirect(url_for('records.patient_dashboard'))
            else:
                # For testing: allow doctors to download too
                flash('Only patients can download decrypted records for now', 'error')
                return redirect(url_for('records.doctor_dashboard'))
            
            # Step 3: AES key decrypts medical file
            decrypted_file = CryptoUtils.decrypt_aes(record.encrypted_file, aes_key)
            
            # Step 4: Verify doctor's digital signature
            try:
                doctor_public_key = key_manager.load_user_public_key(record.doctor_id, 'doctor')
                signature_valid = CryptoUtils.verify_signature(decrypted_file, record.digital_signature, doctor_public_key)
                
                if not signature_valid:
                    # Log failed signature verification
                    log = AccessLog(
                        user_id=current_user.id,
                        record_id=record.id,
                        action='view',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent'),
                        success=False,
                        failure_reason='Digital signature verification failed'
                    )
                    db.session.add(log)
                    db.session.commit()
                    
                    flash('Security Alert: Digital signature verification failed! The file may have been tampered with.', 'error')
                    return redirect(url_for('records.patient_dashboard'))
                    
            except Exception as e:
                # Log signature verification error
                log = AccessLog(
                    user_id=current_user.id,
                    record_id=record.id,
                    action='view',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    success=False,
                    failure_reason=f'Signature verification error: {str(e)}'
                )
                db.session.add(log)
                db.session.commit()
                
                flash(f'Security Alert: Unable to verify digital signature: {str(e)}', 'error')
                return redirect(url_for('records.patient_dashboard'))
            
            # Step 5: Recalculate SHA-256 hash and compare
            calculated_hash = CryptoUtils.calculate_sha256(decrypted_file)
            if calculated_hash != record.file_hash:
                # Log hash mismatch
                log = AccessLog(
                    user_id=current_user.id,
                    record_id=record.id,
                    action='view',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    success=False,
                    failure_reason='File integrity check failed - hash mismatch'
                )
                db.session.add(log)
                db.session.commit()
                
                flash('Security Alert: File integrity check failed! The file may be corrupted or tampered with.', 'error')
                return redirect(url_for('records.patient_dashboard'))
            
            # Security checks passed - file is authentic and intact
            flash('Security verification passed: Digital signature and file integrity verified.', 'success')
            
            # Update access tracking
            record.accessed_at = datetime.utcnow()
            record.access_count += 1
            record.last_accessed_by = current_user.id
            
            # Log successful access
            log = AccessLog(
                user_id=current_user.id,
                record_id=record.id,
                action='view',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                success=True
            )
            db.session.add(log)
            db.session.commit()
            
            # Create temporary file for download
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(decrypted_file)
                tmp_file_path = tmp_file.name
            
            # Send file to user
            return send_file(
                tmp_file_path,
                as_attachment=True,
                download_name=record.original_filename,
                mimetype=record.mime_type
            )
            
        except Exception as e:
            flash(f'Decryption process failed: {str(e)}', 'error')
            return redirect(url_for('records.patient_dashboard'))
            
    except Exception as e:
        flash(f'Error accessing record: {str(e)}', 'error')
        return redirect(url_for('records.patient_dashboard'))
        
    except Exception as e:
        # Log failed access
        log = AccessLog(
            user_id=current_user.id,
            record_id=record_id,
            action='view',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=False,
            failure_reason=str(e)
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Error accessing record: {str(e)}', 'error')
        return redirect(url_for('records.patient_dashboard'))

@records_bp.route('/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    """Delete medical record (doctor only)"""
    if not current_user.is_doctor():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        record = MedicalRecord.query.get_or_404(record_id)
        
        # Check if doctor owns this record
        if record.doctor_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
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
        
        # Delete record
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Record deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Deletion failed: {str(e)}'}), 500
