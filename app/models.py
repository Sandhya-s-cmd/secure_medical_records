from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from app import db
import bcrypt

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'doctor', 'patient', name='user_roles'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    public_key = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    uploaded_records = db.relationship('MedicalRecord', foreign_keys='MedicalRecord.doctor_id', backref='doctor')
    patient_records = db.relationship('MedicalRecord', foreign_keys='MedicalRecord.patient_id', backref='patient')
    
    def set_password(self, password):
        """Hash and set password"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_doctor(self):
        return self.role == 'doctor'
    
    def is_patient(self):
        return self.role == 'patient'

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Encrypted data
    encrypted_file = db.Column(db.LargeBinary, nullable=False)
    encrypted_aes_key = db.Column(db.Text, nullable=False)
    
    # Integrity and authenticity
    file_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash
    digital_signature = db.Column(db.Text, nullable=False)
    
    # Metadata
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accessed_at = db.Column(db.DateTime, nullable=True)
    
    # Access tracking
    access_count = db.Column(db.Integer, default=0)
    last_accessed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=True)
    action = db.Column(db.Enum('upload', 'view', 'download', 'delete', name='access_actions'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    failure_reason = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='access_logs')
    record = db.relationship('MedicalRecord', backref='access_logs')
