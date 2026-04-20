# Secure Medical Record Storage - CNS Project Plan

## 1. Project Vision

Build a comprehensive secure web application where:
- Doctors upload encrypted medical records using military-grade cryptography
- Patients securely access and view only their own records
- Administrators manage users and monitor system security
- All data is encrypted at rest and protected in transit
- File integrity and authenticity are cryptographically verified


The system should demonstrate modern security principles with professional, trustworthy UI design.

## 2. Full System Architecture Plan

### Architecture Type: 3-Tier Secure Architecture

```
Frontend (Secure UI Layer)
    ↓ HTTPS/TLS
Backend (Application + Crypto Engine)
    ↓ Encrypted Connection
Database (Encrypted Storage)
```

### Security Layers Implementation

1. **Authentication Layer**
   - bcrypt password hashing
   - Session management
   - Role-based access control (RBAC)

2. **Authorization Layer**
   - Admin, Doctor, Patient roles
   - Permission-based route protection
   - Resource ownership validation

3. **Encryption Layer**
   - AES-256 for file encryption
   - RSA-2048 for key exchange
   - SHA-256 for integrity verification
   - Digital signatures for authenticity

4. **Integrity Layer**
   - Hash verification on all files
   - Digital signature validation
   - Tamper detection mechanisms

5. **Secure Communication Layer**
   - HTTPS/TLS encryption
   - CSRF protection
   - Secure headers

## 3. UI / Frontend Plan (Interactive Security Theme)

### Color Scheme for Trust & Security

- **Primary**: Deep Blue (#0A1F44) → Trust, medical authority
- **Accent**: Teal (#00C9A7) → Health, freshness, security  
- **Warning**: Soft Red (#FF6B6B) → Security alerts
- **Success**: Emerald (#2ECC71) → Verified, secure
- **Background**: Dark Blue → Light Teal gradient

### Design Elements
- Glassmorphism effects for modern look
- Floating cards with soft shadows
- Animated buttons with hover states
- Smooth transitions and micro-interactions
- Security status indicators (locked/unlocked icons)

### Required Pages

#### 1. Landing Page
- **Title**: "Secure Medical Vault"
- **Features**: Animated shield icon, trust indicators
- **Actions**: Login/Register buttons with gradient backgrounds
- **Background**: Subtle animation with medical imagery

#### 2. Registration Page
- **Fields**: Name, Email, Role selection, Password, Confirm Password
- **UI**: Floating labels, real-time password strength indicator
- **Security**: Generate RSA-2048 key pair during registration
- **Animation**: Success animation with green checkmark

#### 3. Login Page
- **Fields**: Email, Password
- **Security**: Failed attempt lockout after 5 tries
- **UI**: Secure login animation, error messages in soft red

#### 4. Admin Dashboard
- **Cards**: Total Users, Total Records, Active Sessions, Security Status
- **Actions**: Add User, View Records, System Logs
- **Theme**: Blue background with glowing teal action buttons

#### 5. Doctor Dashboard  
- **Cards**: Upload Record, View Patients, Recent Activity
- **Upload**: Drag-and-drop with encryption progress animation
- **Theme**: Professional medical interface

#### 6. Patient Dashboard
- **Cards**: My Records, Security Status, Download History
- **Security**: Visual indicators for encryption/verification status
- **Theme**: Patient-focused, reassuring security messaging

## 4. Backend Technical Implementation

### Core Modules

#### Authentication Module
```python
- Password hashing with bcrypt (salt: 12 rounds)
- JWT session tokens with expiration
- Role-based permission checking
- Login attempt rate limiting
```

#### Cryptographic Engine Module
```python
- AES-256-CBC encryption for files
- RSA-2048-OAEP for key exchange  
- SHA-256 hashing for integrity
- RSA-PSS for digital signatures
- Secure random key generation
```

#### Record Management Module
```python
- Secure file upload with validation
- Hybrid encryption workflow
- Decryption with signature verification
- Comprehensive audit logging
```

#### Security Hardening Module
```python
- CSRF token validation
- SQL injection prevention
- XSS protection
- Input sanitization
- Session timeout management
```

## 5. Encryption Workflow Implementation

### Doctor Upload Process:
1. **Generate** random AES-256 key
2. **Encrypt** medical file with AES-CBC
3. **Encrypt** AES key with patient's RSA public key
4. **Generate** SHA-256 hash of original file
5. **Sign** hash with doctor's private RSA key
6. **Store** encrypted data + metadata in database

### Patient Download Process:
1. **Authenticate** patient login
2. **Retrieve** encrypted file + encrypted AES key
3. **Decrypt** AES key with patient's private RSA key
4. **Decrypt** medical file with AES key
5. **Verify** doctor's digital signature
6. **Validate** SHA-256 hash integrity
7. **Display** file only if all checks pass

## 6. Database Schema Design

### Tables Structure:

#### Users Table
```sql
- user_id (PK)
- username (UNIQUE)
- email (UNIQUE) 
- password_hash (bcrypt)
- role (ENUM: admin/doctor/patient)
- public_key (TEXT) - RSA public key
- created_at, last_login, is_active
```

#### MedicalRecords Table
```sql
- record_id (PK)
- patient_id (FK → Users)
- doctor_id (FK → Users)
- encrypted_file (LONGBLOB) - AES encrypted
- encrypted_aes_key (TEXT) - RSA encrypted
- file_hash (VARCHAR 64) - SHA-256
- digital_signature (TEXT) - RSA signature
- metadata (filename, size, mime_type)
- timestamps, access_tracking
```

#### AccessLogs Table
```sql
- log_id (PK)
- user_id (FK → Users)
- record_id (FK → MedicalRecords, NULLABLE)
- action (ENUM: login/logout/upload/view/download)
- ip_address, user_agent
- timestamp, success, failure_reason
```

## 7. Advanced Security Features (Major Project Level)

### Core Security:
- ✅ AES-256 file encryption
- ✅ RSA-2048 key exchange
- ✅ SHA-256 integrity verification
- ✅ Digital signatures (RSA-PSS)
- ✅ Role-based access control
- ✅ Comprehensive audit logging

### Enhanced Security:
- 🔄 Two-Factor Authentication (TOTP)
- 🔄 Rate limiting (5 failed attempts = 15min lockout)
- 🔄 CSRF token validation
- 🔄 Input validation and sanitization
- 🔄 SQL injection prevention
- 🔄 Session timeout (30 minutes)
- 🔄 Failed attempt logging

### Optional Advanced Features:
- 🔄 Blockchain audit trail integration
- 🔄 Biometric authentication support
- 🔄 Zero-knowledge proof implementation
- 🔄 Homomorphic encryption for computations

## 8. Development Timeline

### Phase 1 – UI/UX Design (3-4 days)
- [ ] Design landing page with security theme
- [ ] Create registration/login forms
- [ ] Build dashboard layouts
- [ ] Implement responsive design
- [ ] Add animations and transitions

### Phase 2 – Authentication System (2-3 days)  
- [ ] User registration with RSA key generation
- [ ] Login system with bcrypt
- [ ] Session management
- [ ] Role-based access control
- [ ] Password reset functionality

### Phase 3 – Cryptographic Module (4-5 days)
- [ ] AES-256 encryption implementation
- [ ] RSA-2048 key management
- [ ] SHA-256 hashing functions
- [ ] Digital signature creation/verification
- [ ] Secure random number generation

### Phase 4 – File Management (3 days)
- [ ] Secure file upload workflow
- [ ] Hybrid encryption implementation
- [ ] Decryption with verification
- [ ] File access logging
- [ ] Download functionality

### Phase 5 – Security Hardening (2 days)
- [ ] HTTPS/TLS configuration
- [ ] CSRF protection implementation
- [ ] Input validation middleware
- [ ] Rate limiting setup
- [ ] Security headers configuration

### Phase 6 – Testing & Optimization (3 days)
- [ ] Unit testing for crypto functions
- [ ] Integration testing for workflows
- [ ] Performance benchmarking
- [ ] Security penetration testing
- [ ] Load testing optimization

**Total Development Time**: 17-20 days (3-4 weeks)

## 9. Testing Strategy

### Security Test Cases:
1. **Encryption Testing**
   - Verify AES encryption/decryption accuracy
   - Test RSA key generation and exchange
   - Validate digital signature creation/verification

2. **Authentication Testing**
   - Test login with valid/invalid credentials
   - Verify role-based access control
   - Test session management and timeout

3. **File Integrity Testing**
   - Upload file and verify hash integrity
   - Test signature verification workflow
   - Attempt tampering detection

4. **Performance Testing**
   - Benchmark encryption times for 1MB, 5MB, 10MB files
   - Measure CPU usage during crypto operations
   - Test concurrent user access

### Security Penetration Testing:
- SQL injection attempts
- XSS attack vectors
- CSRF token validation
- Unauthorized access attempts
- Brute force attack simulation

## 10. Documentation Structure (Final CNS Report)

### Required Sections:
1. **Abstract** - Project overview and security objectives
2. **Introduction** - Background and motivation
3. **Literature Survey** - Existing solutions and research
4. **Problem Statement** - Specific security challenges addressed
5. **System Architecture** - Detailed technical architecture
6. **Data Flow Diagrams** - Encryption/decryption workflows
7. **Algorithms Used** - AES, RSA, SHA-256, Digital Signatures
8. **Implementation Details** - Code structure and key functions
9. **Security Analysis** - Threat modeling and mitigation
10. **Testing Results** - Performance and security test outcomes
11. **Screenshots** - System interface demonstrations
12. **Conclusion** - Summary and achievements
13. **Future Scope** - Enhancements and research directions

### Deliverables:
- ✅ Complete working system with all features
- ✅ Source code with documentation
- ✅ Security analysis report
- ✅ Performance benchmarks
- ✅ Demonstration video
- ✅ Final CNS project report

## 11. Success Metrics

### Security Metrics:
- ✅ Zero successful unauthorized access attempts
- ✅ 100% file encryption at rest
- ✅ Complete audit trail for all actions
- ✅ Digital signature verification on all files

### Performance Metrics:
- ✅ <2s encryption time for 10MB files
- ✅ <1s decryption time for patient access
- ✅ Support for 50+ concurrent users
- ✅ 99.9% system uptime

### User Experience Metrics:
- ✅ Intuitive role-based interfaces
- ✅ Clear security status indicators
- ✅ Responsive design for all devices
- ✅ Comprehensive help documentation

---

## Implementation Priority

**High Priority (Core Functionality):**
1. User authentication and role management
2. AES-256 + RSA-2048 encryption system
3. Secure file upload/download workflow
4. Basic admin dashboard

**Medium Priority (Enhanced Security):**
1. Two-factor authentication
2. Advanced audit logging
3. Rate limiting and CSRF protection
4. Security monitoring dashboard

**Low Priority (Advanced Features):**
1. Blockchain audit integration
2. Biometric authentication
3. Advanced analytics
4. Mobile application

This comprehensive plan ensures your CNS project demonstrates enterprise-level security implementation with modern cryptography and professional user experience.
