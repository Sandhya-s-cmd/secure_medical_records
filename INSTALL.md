# Installation Guide

## Prerequisites
- Python 3.8+
- MySQL 5.7+
- pip package manager

## Step-by-Step Installation

### 1. Install Python Dependencies
```bash
cd secure_medical_records
pip install -r requirements.txt
```

### 2. Set Up MySQL Database
```bash
# Log in to MySQL as root
mysql -u root -p

# Create database (optional - schema.sql does this)
CREATE DATABASE medical_records;

# Import the schema
mysql -u root -p medical_records < database/schema.sql
```

### 3. Configure Database Connection
Edit `app/__init__.py` and update the database URI:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://your_username:your_password@localhost/medical_records'
```

### 4. Run the Application
```bash
python run.py
```

### 5. Access the System
- Open browser: http://localhost:5000
- Default admin login:
  - Username: `admin`
  - Password: `admin123`

## Troubleshooting

### Common Issues

1. **Import Error: No module named 'cryptography'**
   ```bash
   pip install cryptography
   ```

2. **Database Connection Error**
   - Check MySQL service is running
   - Verify username/password in database URI
   - Ensure database exists

3. **Permission Denied**
   - Run with administrator privileges
   - Check file permissions for keys directory

4. **Port Already in Use**
   ```bash
   # Kill process on port 5000 (Windows)
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   
   # Or run on different port
   python run.py --port 5001
   ```

## Quick Start Script (Windows)
```batch
@echo off
echo Installing Secure Medical Records System...
echo.

echo Step 1: Installing Python packages...
pip install -r requirements.txt

echo Step 2: Setting up database...
mysql -u root -p < database/schema.sql

echo Step 3: Starting application...
python run.py

pause
```
