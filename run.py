#!/usr/bin/env python3
"""
Secure Medical Records System
Cryptographic & Network Security Project

Main application entry point
"""

import os
from app import create_app, db
from app.models import User, MedicalRecord, AccessLog

def init_database():
    """Initialize database with tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

def create_admin_user():
    """Create default admin user if not exists"""
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@medical.com',
                full_name='System Administrator',
                role='admin',
                is_active=True
            )
            admin.set_password('Sandhya@Sand98')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created (username: admin, password: Sandhya@Sand98)")
        else:
            print("Admin user already exists")

def create_directories():
    """Create necessary directories"""
    directories = [
        'uploads',
        'keys/doctors',
        'keys/patients',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Directory '{directory}' created/verified")

if __name__ == '__main__':
    # Create Flask app
    app = create_app()
    
    # Initialize system
    print("Initializing Secure Medical Records System...")
    create_directories()
    init_database()
    create_admin_user()
    
    print("\n" + "="*60)
    print("SECURE MEDICAL RECORDS SYSTEM")
    print("="*60)
    print("System initialized successfully!")
    print("\nDefault Login Credentials:")
    print("  Username: admin")
    print("  Password: Sandhya@Sand98")
    print("\nAccess URLs:")
    print("  Login: http://localhost:8080/auth/login")
    print("  Register: http://localhost:8080/auth/register")
    print("\nSecurity Features:")
    print("  ✓ AES-256 encryption for medical files")
    print("  ✓ RSA-2048 for key exchange")
    print("  ✓ Digital signatures for authenticity")
    print("  ✓ SHA-256 hashing for integrity")
    print("  ✓ Role-based access control")
    print("  ✓ Comprehensive audit logging")
    print("="*60)
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True,
        ssl_context=('cert.pem', 'key.pem') if os.path.exists('cert.pem') else None
    )
