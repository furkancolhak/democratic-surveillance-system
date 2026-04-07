"""
Secure Member Authentication System
Database-backed with encryption
"""

from database import db_manager, Member, MasterUser
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import pyotp
import qrcode
import uuid
from typing import Optional, Dict, List
import os


class SecureMemberAuth:
    """Güvenli üye kimlik doğrulama sistemi"""
    
    def __init__(self):
        self.db = db_manager
        self.master_key = db_manager.master_key_manager
    
    def register_member(self, email: str, name: str, created_by_id: uuid.UUID) -> Dict:
        """
        Register new member (only master user can do this)
        
        Args:
            email: Member email
            name: Member name
            created_by_id: Master user ID who is creating this member
            
        Returns:
            Dict with member info and TOTP QR code URI
        """
        session = self.db.get_session()
        
        try:
            # Check master user
            master_user = session.query(MasterUser).filter(
                MasterUser.id == created_by_id,
                MasterUser.is_active == True
            ).first()
            
            if not master_user:
                raise ValueError("Invalid or inactive master user")
            
            # Check if member already exists
            existing = session.query(Member).filter(Member.email == email).first()
            if existing:
                raise ValueError("Member already exists")
            
            # Generate RSA key pair
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
            
            # Encrypt private key with master key
            private_key_encrypted = self.master_key.encrypt(private_pem)
            
            # Generate and encrypt TOTP secret
            totp_secret = pyotp.random_base32()
            totp_secret_encrypted = self.master_key.encrypt_string(totp_secret)
            
            # Create member
            member = Member(
                email=email,
                name=name,
                public_key=public_pem.decode('utf-8'),
                private_key_encrypted=private_key_encrypted,
                totp_secret_encrypted=totp_secret_encrypted,
                created_by=created_by_id
            )
            
            session.add(member)
            session.commit()
            
            # Generate TOTP URI
            totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
                name=email,
                issuer_name="Surveillance System"
            )
            
            # Generate QR code
            qr_dir = "totp_qr_codes/members"
            os.makedirs(qr_dir, exist_ok=True)
            qr_path = f"{qr_dir}/{email.replace('@', '_').replace('.', '_')}_qr.png"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            qr.make_image(fill_color="black", back_color="white").save(qr_path)
            
            # Audit log
            self.db.log_audit(
                session=session,
                event_type='member_created',
                user_id=created_by_id,
                user_type='master',
                action=f'Member registered: {email}',
                details={'member_id': str(member.id), 'member_email': email, 'member_name': name}
            )
            
            print(f"✅ Member registered: {name} ({email})")
            print(f"📱 TOTP QR code saved: {qr_path}")
            
            return {
                'id': str(member.id),
                'email': email,
                'name': name,
                'totp_uri': totp_uri,
                'qr_path': qr_path
            }
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error registering member: {e}")
            raise
        finally:
            session.close()
    
    def verify_totp(self, member_id: uuid.UUID, totp_code: str) -> bool:
        """Verify TOTP code"""
        session = self.db.get_session()
        
        try:
            member = session.query(Member).filter(
                Member.id == member_id,
                Member.is_active == True
            ).first()
            
            if not member:
                return False
            
            # Decrypt TOTP secret
            totp_secret = self.master_key.decrypt_string(member.totp_secret_encrypted)
            totp = pyotp.TOTP(totp_secret)
            
            return totp.verify(totp_code)
            
        finally:
            session.close()
    
    def get_member_by_email(self, email: str) -> Optional[Dict]:
        """Find member by email"""
        session = self.db.get_session()
        
        try:
            member = session.query(Member).filter(
                Member.email == email,
                Member.is_active == True
            ).first()
            
            if not member:
                return None
            
            return {
                'id': str(member.id),
                'email': member.email,
                'name': member.name,
                'public_key': member.public_key,
                'created_at': member.created_at.isoformat()
            }
            
        finally:
            session.close()
    
    def get_member_by_id(self, member_id: uuid.UUID) -> Optional[Dict]:
        """Find member by ID"""
        session = self.db.get_session()
        
        try:
            member = session.query(Member).filter(
                Member.id == member_id,
                Member.is_active == True
            ).first()
            
            if not member:
                return None
            
            return {
                'id': str(member.id),
                'email': member.email,
                'name': member.name,
                'public_key': member.public_key,
                'created_at': member.created_at.isoformat()
            }
            
        finally:
            session.close()
    
    def get_active_members(self) -> List[Dict]:
        """Get all active members"""
        session = self.db.get_session()
        
        try:
            members = session.query(Member).filter(Member.is_active == True).all()
            
            return [{
                'id': str(member.id),
                'email': member.email,
                'name': member.name,
                'public_key': member.public_key,
                'created_at': member.created_at.isoformat()
            } for member in members]
            
        finally:
            session.close()
    
    def get_public_key(self, member_id: uuid.UUID) -> Optional[bytes]:
        """Get member's public key"""
        session = self.db.get_session()
        
        try:
            member = session.query(Member).filter(Member.id == member_id).first()
            
            if not member:
                return None
            
            return member.public_key.encode('utf-8')
            
        finally:
            session.close()
    
    def get_private_key(self, member_id: uuid.UUID) -> Optional[bytes]:
        """Get member's private key (decrypted)"""
        session = self.db.get_session()
        
        try:
            member = session.query(Member).filter(Member.id == member_id).first()
            
            if not member:
                return None
            
            # Decrypt private key
            return self.master_key.decrypt(member.private_key_encrypted)
            
        finally:
            session.close()
    
    def encrypt_for_member(self, member_id: uuid.UUID, data: bytes) -> Optional[bytes]:
        """Encrypt data with member's public key"""
        public_key_pem = self.get_public_key(member_id)
        
        if not public_key_pem:
            return None
        
        public_key = serialization.load_pem_public_key(public_key_pem)
        
        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return encrypted
    
    def decrypt_for_member(self, member_id: uuid.UUID, encrypted_data: bytes) -> Optional[bytes]:
        """Decrypt data with member's private key"""
        private_key_pem = self.get_private_key(member_id)
        
        if not private_key_pem:
            return None
        
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None
        )
        
        decrypted = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted
    
    def sign_data(self, member_id: uuid.UUID, data: bytes) -> Optional[bytes]:
        """Sign data with member's private key"""
        private_key_pem = self.get_private_key(member_id)
        
        if not private_key_pem:
            return None
        
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None
        )
        
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return signature
    
    def verify_signature(self, member_id: uuid.UUID, data: bytes, signature: bytes) -> bool:
        """Verify signature with member's public key"""
        public_key_pem = self.get_public_key(member_id)
        
        if not public_key_pem:
            return False
        
        public_key = serialization.load_pem_public_key(public_key_pem)
        
        try:
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def deactivate_member(self, member_id: uuid.UUID, deactivated_by: uuid.UUID):
        """Deactivate member"""
        session = self.db.get_session()
        
        try:
            member = session.query(Member).filter(Member.id == member_id).first()
            
            if not member:
                raise ValueError("Member not found")
            
            member.is_active = False
            member.deactivated_at = datetime.utcnow()
            member.deactivated_by = deactivated_by
            session.commit()
            
            self.db.log_audit(
                session=session,
                event_type='member_deactivated',
                user_id=deactivated_by,
                user_type='master',
                action=f'Member deactivated: {member.email}',
                details={'member_id': str(member_id)}
            )
            
            print(f"✅ Member deactivated: {member.email}")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error deactivating member: {e}")
            raise
        finally:
            session.close()
