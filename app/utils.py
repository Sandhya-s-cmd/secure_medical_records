import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization, padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.backends import default_backend
import base64
import secrets

class CryptoUtils:
    """Cryptographic utilities for secure medical record storage"""
    
    @staticmethod
    def generate_aes_key():
        """Generate a random 256-bit AES key"""
        return os.urandom(32)  # 32 bytes = 256 bits
    
    @staticmethod
    def generate_rsa_key_pair():
        """Generate RSA key pair for asymmetric encryption"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    @staticmethod
    def serialize_public_key(public_key):
        """Serialize public key to PEM format"""
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    
    @staticmethod
    def serialize_private_key(private_key, password=None):
        """Serialize private key to PEM format with optional password protection"""
        encryption = serialization.NoEncryption()
        if password:
            encryption = serialization.BestAvailableEncryption(password.encode('utf-8'))
        
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        )
    
    @staticmethod
    def load_public_key(pem_data):
        """Load public key from PEM format"""
        return serialization.load_pem_public_key(
            pem_data.encode('utf-8'),
            backend=default_backend()
        )
    
    @staticmethod
    def load_private_key(pem_data, password=None):
        """Load private key from PEM format"""
        # Handle both string and bytes input
        if isinstance(pem_data, bytes):
            return serialization.load_pem_private_key(
                pem_data,
                password=password.encode('utf-8') if password else None,
                backend=default_backend()
            )
        else:
            return serialization.load_pem_private_key(
                pem_data.encode('utf-8'),
                password=password.encode('utf-8') if password else None,
                backend=default_backend()
            )
    
    @staticmethod
    def encrypt_aes(data, key):
        """Encrypt data using AES-256-CBC"""
        # Generate random IV
        iv = os.urandom(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Apply PKCS7 padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return IV + encrypted data
        return iv + encrypted
    
    @staticmethod
    def decrypt_aes(encrypted_data, key):
        """Decrypt data using AES-256-CBC"""
        # Extract IV and encrypted data
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data
    
    @staticmethod
    def encrypt_rsa(data, public_key):
        """Encrypt data using RSA-OAEP"""
        encrypted = public_key.encrypt(
            data,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def decrypt_rsa(encrypted_data, private_key):
        """Decrypt data using RSA-OAEP"""
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        decrypted = private_key.decrypt(
            encrypted_bytes,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted
    
    @staticmethod
    def calculate_sha256(data):
        """Calculate SHA-256 hash of data"""
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def sign_data(data, private_key):
        """Create digital signature using RSA-PSS"""
        signature = private_key.sign(
            data,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
    
    @staticmethod
    def verify_signature(data, signature, public_key):
        """Verify digital signature using RSA-PSS"""
        try:
            signature_bytes = base64.b64decode(signature.encode('utf-8'))
            public_key.verify(
                signature_bytes,
                data,
                asym_padding.PSS(
                    mgf=asym_padding.MGF1(hashes.SHA256()),
                    salt_length=asym_padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

class KeyManager:
    """Manages RSA key storage and retrieval"""
    
    def __init__(self, keys_dir='keys'):
        self.keys_dir = keys_dir
        self.doctors_dir = os.path.join(keys_dir, 'doctors')
        self.patients_dir = os.path.join(keys_dir, 'patients')
        
        # Create directories if they don't exist
        os.makedirs(self.doctors_dir, exist_ok=True)
        os.makedirs(self.patients_dir, exist_ok=True)
    
    def save_user_keys(self, user_id, role, private_key, public_key, password=None):
        """Save user's RSA key pair"""
        if role == 'doctor':
            key_dir = self.doctors_dir
        elif role == 'patient':
            key_dir = self.patients_dir
        else:
            raise ValueError("Invalid role for key storage")
        
        # Save private key
        private_key_path = os.path.join(key_dir, f"user_{user_id}_private.pem")
        private_key_pem = CryptoUtils.serialize_private_key(private_key, password)
        with open(private_key_path, 'wb') as f:
            f.write(private_key_pem)
        
        # Save public key
        public_key_path = os.path.join(key_dir, f"user_{user_id}_public.pem")
        public_key_pem = CryptoUtils.serialize_public_key(public_key)
        with open(public_key_path, 'w') as f:
            f.write(public_key_pem)
        
        return private_key_path, public_key_path
    
    def load_user_private_key(self, user_id, role, password=None):
        """Load user's private key"""
        if role == 'doctor':
            key_dir = self.doctors_dir
        elif role == 'patient':
            key_dir = self.patients_dir
        else:
            raise ValueError("Invalid role for key storage")
        
        private_key_path = os.path.join(key_dir, f"user_{user_id}_private.pem")
        with open(private_key_path, 'rb') as f:
            private_key_pem = f.read()
        
        return CryptoUtils.load_private_key(private_key_pem, password)
    
    def load_user_public_key(self, user_id, role):
        """Load user's public key"""
        if role == 'doctor':
            key_dir = self.doctors_dir
        elif role == 'patient':
            key_dir = self.patients_dir
        else:
            raise ValueError("Invalid role for key storage")
        
        public_key_path = os.path.join(key_dir, f"user_{user_id}_public.pem")
        with open(public_key_path, 'r') as f:
            public_key_pem = f.read()
        
        return CryptoUtils.load_public_key(public_key_pem)

class SecurityUtils:
    """Security utilities for access control and validation"""
    
    @staticmethod
    def generate_session_token():
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_file_upload(file):
        """Validate uploaded file for security"""
        # Check file size (max 16MB)
        if len(file.read()) > 16 * 1024 * 1024:
            file.seek(0)
            return False, "File too large. Maximum size is 16MB."
        
        file.seek(0)
        
        # Check file type
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.dicom'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return False, f"File type {file_ext} not allowed."
        
        return True, "File validation passed."
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename to prevent directory traversal"""
        # Remove path separators and dangerous characters
        filename = os.path.basename(filename)
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        return filename[:255]  # Limit length
