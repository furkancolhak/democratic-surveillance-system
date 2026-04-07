import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import os
from datetime import datetime
import jwt
from dotenv import load_dotenv

class NotificationService:
    def __init__(self):
        load_dotenv()
        
        # Load email configuration from environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL')
        
        # JWT configuration
        self.jwt_secret = os.getenv('JWT_SECRET', os.urandom(32).hex())
        self.jwt_expire_hours = int(os.getenv('JWT_EXPIRE_HOURS', '24'))
        
        # Base URL for voting links
        self.base_url = os.getenv('BASE_URL', 'http://localhost:3333')
        
        if not all([self.smtp_username, self.smtp_password, self.from_email]):
            raise ValueError("Missing email configuration. Please check .env file.")

    def _create_voting_link(self, session_id: str, member_email: str) -> str:
        """Create a secure voting link with JWT token"""
        token = jwt.encode({
            'session_id': session_id,
            'email': member_email,
            'exp': datetime.utcnow().timestamp() + (self.jwt_expire_hours * 3600)
        }, self.jwt_secret, algorithm='HS256')
        
        return f"{self.base_url}/vote?token={token}"

    def verify_voting_token(self, token: str) -> dict:
        """Verify and decode a voting token"""
        try:
            print(f"Using JWT secret: {self.jwt_secret[:10]}...")  # İlk 10 karakteri göster
            print(f"Verifying token: {token}")
            decoded = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            print(f"Decoded token: {decoded}")
            return decoded
        except jwt.ExpiredSignatureError:
            print("Token has expired")
            raise jwt.ExpiredSignatureError("Voting token has expired")
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {str(e)}")
            raise jwt.InvalidTokenError(f"Invalid voting token: {str(e)}")
        except Exception as e:
            print(f"Error verifying token: {str(e)}")
            raise Exception(f"Error verifying token: {str(e)}")

    def send_incident_notification(self, session_id: str, members: List[Dict], 
                                 incident_time: str, encrypted_shares: Dict[str, bytes]):
        """Send incident notification emails to all members"""
        for email, member in members.items():
            # Create secure voting link
            voting_link = self._create_voting_link(session_id, email)
            
            # Get encrypted share for this member
            encrypted_share = encrypted_shares[email]
            
            # Create email content
            subject = "Güvenlik Kamerası - Şiddet Olayı Tespit Edildi"
            
            html_content = f"""
            <html>
                <body>
                    <h2>Güvenlik Uyarısı</h2>
                    <p>Sayın {member['name']},</p>
                    <p>Güvenlik kamerasında {incident_time} tarihinde şiddet içerikli bir olay tespit edildi.</p>
                    <p>Lütfen aşağıdaki linke tıklayarak oyunuzu kullanın:</p>
                    <p><a href="{voting_link}">Oylama Sayfasına Git</a></p>
                    <p>Bu link 24 saat içinde geçerliliğini yitirecektir.</p>
                    <p><strong>Önemli:</strong> Bu e-posta gizli bilgiler içermektedir. Lütfen başkalarıyla paylaşmayın.</p>
                    <hr>
                    <p><small>Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayın.</small></p>
                </body>
            </html>
            """
            
            try:
                self._send_email(email, subject, html_content)
            except Exception as e:
                print(f"Error sending email to {email}: {e}")

    def send_result_notification(self, session_id: str, members: List[Dict], 
                               status: str, decrypted_video_path: str = None):
        """Send voting result notification to all members"""
        subject = "Güvenlik Kamerası - Oylama Sonucu"
        
        for email, member in members.items():
            if status == 'approved':
                content = f"""
                <html>
                    <body>
                        <h2>Oylama Sonucu: Onaylandı</h2>
                        <p>Sayın {member['name']},</p>
                        <p>İlgili olay kaydının gösterilmesi için yeterli oy toplanmıştır.</p>
                        <p>Video kaydı güvenli sistemde görüntülenmeye hazırdır.</p>
                        <hr>
                        <p><small>Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayın.</small></p>
                    </body>
                </html>
                """
            else:
                content = f"""
                <html>
                    <body>
                        <h2>Oylama Sonucu: Reddedildi</h2>
                        <p>Sayın {member['name']},</p>
                        <p>İlgili olay kaydının gösterilmesi için yeterli oy toplanamamıştır.</p>
                        <p>Video kaydı şifreli olarak saklanmaya devam edecektir.</p>
                        <hr>
                        <p><small>Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayın.</small></p>
                    </body>
                </html>
                """
            
            try:
                self._send_email(email, subject, content)
            except Exception as e:
                print(f"Error sending result email to {email}: {e}")

    def _send_email(self, to_email: str, subject: str, html_content: str):
        """Send an email using SMTP"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
