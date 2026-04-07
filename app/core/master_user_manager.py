"""
Master User Management System
Admin kullanıcıları yönetir - 2FA ile giriş
"""

from database import db_manager, MasterUser, Member, AuditLog
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from passlib.hash import argon2
import pyotp
import qrcode
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os


class MasterUserManager:
    """Master kullanıcı yönetimi"""
    
    def __init__(self):
        self.db = db_manager
        self.master_key = db_manager.master_key_manager
    
    def create_master_user(self, username: str, email: str, password: str) -> Dict:
        """
        Yeni master kullanıcı oluştur
        
        Returns:
            Dict with user info and TOTP QR code URI
        """
        session = self.db.get_session()
        
        try:
            # Kullanıcı zaten var mı kontrol et
            existing = session.query(MasterUser).filter(
                (MasterUser.username == username) | (MasterUser.email == email)
            ).first()
            
            if existing:
                raise ValueError("Username or email already exists")
            
            # Password hash (Argon2)
            password_hash = argon2.hash(password)
            
            # TOTP secret oluştur
            totp_secret = pyotp.random_base32()
            totp_secret_encrypted = self.master_key.encrypt_string(totp_secret)
            
            # RSA key pair oluştur
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            public_key = private_key.public_key()
            
            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Private key'i master key ile şifrele
            private_key_encrypted = self.master_key.encrypt(private_pem)
            
            # Master user oluştur
            master_user = MasterUser(
                username=username,
                email=email,
                password_hash=password_hash,
                totp_secret_encrypted=totp_secret_encrypted,
                public_key=public_pem.decode('utf-8'),
                private_key_encrypted=private_key_encrypted
            )
            
            session.add(master_user)
            session.commit()
            
            # TOTP URI oluştur
            totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
                name=email,
                issuer_name="Surveillance System - Admin"
            )
            
            # Generate QR code
            qr_dir = "totp_qr_codes/master"
            os.makedirs(qr_dir, exist_ok=True)
            qr_path = f"{qr_dir}/{username}_qr.png"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            qr.make_image(fill_color="black", back_color="white").save(qr_path)
            
            # Audit log
            self.db.log_audit(
                session=session,
                event_type='master_user_created',
                user_id=master_user.id,
                user_type='master',
                action=f'Master user created: {username}',
                details={'username': username, 'email': email}
            )
            
            print(f"✅ Master user created: {username}")
            print(f"📱 TOTP QR code saved: {qr_path}")
            
            return {
                'id': str(master_user.id),
                'username': username,
                'email': email,
                'totp_uri': totp_uri,
                'qr_path': qr_path
            }
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error creating master user: {e}")
            raise
        finally:
            session.close()
    
    def authenticate(self, username: str, password: str, totp_code: str, 
                    ip_address: str = None) -> Optional[Dict]:
        """
        Master kullanıcı girişi (2FA)
        
        Returns:
            User info if successful, None otherwise
        """
        session = self.db.get_session()
        
        try:
            # Kullanıcıyı bul
            user = session.query(MasterUser).filter(
                MasterUser.username == username
            ).first()
            
            if not user:
                self.db.log_audit(
                    session=session,
                    event_type='login_failed',
                    user_id=None,
                    user_type='master',
                    action=f'Login failed: user not found - {username}',
                    ip_address=ip_address,
                    success=False,
                    error_message='User not found'
                )
                return None
            
            # Is user locked?
            if user.locked_until and user.locked_until > datetime.utcnow():
                remaining = (user.locked_until - datetime.utcnow()).seconds // 60
                self.db.log_audit(
                    session=session,
                    event_type='login_failed',
                    user_id=user.id,
                    user_type='master',
                    action=f'Login failed: account locked - {username}',
                    ip_address=ip_address,
                    success=False,
                    error_message=f'Account locked for {remaining} minutes'
                )
                raise ValueError(f"Account locked. Try again in {remaining} minutes")
            
            # Is user active?
            if not user.is_active:
                self.db.log_audit(
                    session=session,
                    event_type='login_failed',
                    user_id=user.id,
                    user_type='master',
                    action=f'Login failed: account inactive - {username}',
                    ip_address=ip_address,
                    success=False,
                    error_message='Account inactive'
                )
                raise ValueError("Account is inactive")
            
            # Verify password
            if not argon2.verify(password, user.password_hash):
                user.failed_login_attempts += 1
                
                # Lock after 5 failed attempts
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                    session.commit()
                    
                    self.db.log_audit(
                        session=session,
                        event_type='account_locked',
                        user_id=user.id,
                        user_type='master',
                        action=f'Account locked due to failed login attempts - {username}',
                        ip_address=ip_address,
                        success=False
                    )
                    raise ValueError("Account locked due to multiple failed attempts")
                
                session.commit()
                
                self.db.log_audit(
                    session=session,
                    event_type='login_failed',
                    user_id=user.id,
                    user_type='master',
                    action=f'Login failed: invalid password - {username}',
                    ip_address=ip_address,
                    success=False,
                    error_message='Invalid password'
                )
                return None
            
            # Verify TOTP
            totp_secret = self.master_key.decrypt_string(user.totp_secret_encrypted)
            totp = pyotp.TOTP(totp_secret)
            
            if not totp.verify(totp_code):
                user.failed_login_attempts += 1
                session.commit()
                
                self.db.log_audit(
                    session=session,
                    event_type='login_failed',
                    user_id=user.id,
                    user_type='master',
                    action=f'Login failed: invalid TOTP - {username}',
                    ip_address=ip_address,
                    success=False,
                    error_message='Invalid TOTP code'
                )
                return None
            
            # Successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            session.commit()
            
            self.db.log_audit(
                session=session,
                event_type='login_success',
                user_id=user.id,
                user_type='master',
                action=f'Successful login - {username}',
                ip_address=ip_address,
                success=True
            )
            
            print(f"✅ Master user logged in: {username}")
            
            return {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'last_login': user.last_login.isoformat()
            }
            
        except Exception as e:
            session.rollback()
            print(f"❌ Authentication error: {e}")
            raise
        finally:
            session.close()
    
    def list_master_users(self) -> List[Dict]:
        """List all master users"""
        session = self.db.get_session()
        
        try:
            users = session.query(MasterUser).all()
            
            return [{
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            } for user in users]
            
        finally:
            session.close()
    
    def deactivate_master_user(self, user_id: uuid.UUID, deactivated_by: uuid.UUID):
        """Deactivate master user"""
        session = self.db.get_session()
        
        try:
            user = session.query(MasterUser).filter(MasterUser.id == user_id).first()
            
            if not user:
                raise ValueError("User not found")
            
            user.is_active = False
            session.commit()
            
            self.db.log_audit(
                session=session,
                event_type='master_user_deactivated',
                user_id=deactivated_by,
                user_type='master',
                action=f'Master user deactivated: {user.username}',
                details={'deactivated_user_id': str(user_id)}
            )
            
            print(f"✅ Master user deactivated: {user.username}")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error deactivating user: {e}")
            raise
        finally:
            session.close()


if __name__ == "__main__":
    # Create first master user
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python master_user_manager.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    manager = MasterUserManager()
    
    try:
        result = manager.create_master_user(username, email, password)
        print(f"\n🎉 Master user created successfully!")
        print(f"Username: {result['username']}")
        print(f"Email: {result['email']}")
        print(f"QR Code: {result['qr_path']}")
        print(f"\n⚠️  IMPORTANT: Scan the QR code with Google Authenticator NOW!")
    except Exception as e:
        print(f"\n❌ Failed to create master user: {e}")
        sys.exit(1)
