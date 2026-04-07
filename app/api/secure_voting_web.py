"""
Secure Voting Web Interface with Database Backend
Production-ready Flask application
"""

from flask import Flask, request, jsonify, render_template_string
from secure_voting_system import SecureVotingSystem
from secure_member_auth import SecureMemberAuth
from notification_service import NotificationService
from master_user_manager import MasterUserManager
from database import db_manager
import jwt
import uuid
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

# Initialize services
voting_system = SecureVotingSystem()
member_auth = SecureMemberAuth()
notification_service = NotificationService()
master_user_manager = MasterUserManager()


@app.route('/')
def index():
    """Home page"""
    return jsonify({
        'service': 'Secure Surveillance System',
        'version': '2.0',
        'status': 'operational',
        'endpoints': {
            'voting': '/vote?token=<jwt_token>',
            'admin_login': '/api/admin/login',
            'health': '/health'
        }
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        session = db_manager.get_session()
        session.execute('SELECT 1')
        session.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/vote', methods=['GET', 'POST'])
def vote():
    """Voting interface"""
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Missing voting token'}), 400
    
    try:
        # Verify JWT token
        token_data = notification_service.verify_voting_token(token)
        session_uuid = uuid.UUID(token_data.get('session_id'))
        member_email = token_data.get('email')
        
        # Get member
        member = member_auth.get_member_by_email(member_email)
        if not member:
            return jsonify({'error': 'Member not found'}), 404
        
        member_id = uuid.UUID(member['id'])
        
        # Get session
        session_data = voting_system.get_session_by_id(session_uuid)
        if not session_data:
            return jsonify({'error': 'Voting session not found'}), 404
        
        if session_data['status'] != 'active':
            return jsonify({'error': f'Session is {session_data["status"]}'}), 400
        
        # Handle POST (vote submission)
        if request.method == 'POST':
            data = request.get_json() if request.is_json else request.form
            
            vote_value = data.get('vote')
            if vote_value is None:
                return jsonify({'error': 'Missing vote value'}), 400
            
            # Convert to boolean
            if isinstance(vote_value, str):
                vote_value = vote_value.lower() == 'true'
            
            totp_code = data.get('totp_code')
            if not totp_code:
                return jsonify({'error': 'Missing TOTP code'}), 400
            
            # Get client info
            ip_address = request.headers.get('X-Real-IP') or request.remote_addr
            user_agent = request.headers.get('User-Agent')
            
            # Submit vote
            success = voting_system.submit_vote(
                session_uuid=session_uuid,
                member_id=member_id,
                vote=vote_value,
                totp_code=totp_code,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if success:
                # Check updated status
                status = voting_system.get_session_status(session_uuid)
                
                if status['status'] == 'approved':
                    return jsonify({
                        'success': True,
                        'message': 'Vote submitted and video decrypted',
                        'status': 'approved',
                        'decrypted_path': status.get('decrypted_video_path')
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': 'Vote submitted successfully',
                        'status': status['status'],
                        'votes': f"{status['positive_votes']}/{status['threshold']}"
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to submit vote'
                }), 400
        
        # Handle GET (show voting form)
        # Check if already voted
        status = voting_system.get_session_status(session_uuid)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Vote on Security Incident</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .container {{
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    max-width: 500px;
                    width: 100%;
                    padding: 40px;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 10px;
                    font-size: 28px;
                }}
                .subtitle {{
                    color: #666;
                    margin-bottom: 30px;
                    font-size: 14px;
                }}
                .info-box {{
                    background: #f8f9fa;
                    border-left: 4px solid #667eea;
                    padding: 15px;
                    margin-bottom: 25px;
                    border-radius: 5px;
                }}
                .info-box p {{
                    margin: 5px 0;
                    color: #555;
                    font-size: 14px;
                }}
                .form-group {{
                    margin-bottom: 25px;
                }}
                label {{
                    display: block;
                    margin-bottom: 8px;
                    color: #333;
                    font-weight: 600;
                    font-size: 14px;
                }}
                input, select {{
                    width: 100%;
                    padding: 12px 15px;
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                    font-size: 16px;
                    transition: border-color 0.3s;
                }}
                input:focus, select:focus {{
                    outline: none;
                    border-color: #667eea;
                }}
                input:read-only {{
                    background: #f5f5f5;
                    color: #666;
                }}
                select {{
                    cursor: pointer;
                }}
                button {{
                    width: 100%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px;
                    border: none;
                    border-radius: 10px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
                }}
                button:active {{
                    transform: translateY(0);
                }}
                button:disabled {{
                    background: #ccc;
                    cursor: not-allowed;
                    transform: none;
                }}
                .status {{
                    text-align: center;
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    font-weight: 600;
                }}
                .status.active {{
                    background: #d4edda;
                    color: #155724;
                }}
                .error {{
                    background: #f8d7da;
                    color: #721c24;
                    padding: 15px;
                    border-radius: 10px;
                    margin-top: 15px;
                    display: none;
                }}
                .success {{
                    background: #d4edda;
                    color: #155724;
                    padding: 15px;
                    border-radius: 10px;
                    margin-top: 15px;
                    display: none;
                }}
                .loading {{
                    display: none;
                    text-align: center;
                    margin-top: 15px;
                }}
                .spinner {{
                    border: 3px solid #f3f3f3;
                    border-top: 3px solid #667eea;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔒 Security Incident Vote</h1>
                <p class="subtitle">Secure voting system with 2FA authentication</p>
                
                <div class="status active">
                    Session Active - {status['positive_votes']}/{status['threshold']} votes received
                </div>
                
                <div class="info-box">
                    <p><strong>Voting as:</strong> {member_email}</p>
                    <p><strong>Session:</strong> {session_data['session_id']}</p>
                    <p><strong>Timestamp:</strong> {session_data['timestamp']}</p>
                </div>
                
                <form id="voteForm">
                    <div class="form-group">
                        <label for="member_id">Member Email</label>
                        <input type="text" id="member_id" value="{member_email}" readonly>
                    </div>
                    
                    <div class="form-group">
                        <label for="vote">Your Decision</label>
                        <select id="vote" name="vote" required>
                            <option value="">-- Select your vote --</option>
                            <option value="true">✅ Approve - Decrypt and view video</option>
                            <option value="false">❌ Reject - Keep video encrypted</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="totp_code">Authentication Code (Google Authenticator)</label>
                        <input type="text" id="totp_code" name="totp_code" required 
                               placeholder="Enter 6-digit code" maxlength="6" pattern="[0-9]{{6}}">
                    </div>
                    
                    <button type="submit" id="submitBtn">Submit Vote</button>
                </form>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Submitting vote...</p>
                </div>
                
                <div class="error" id="error"></div>
                <div class="success" id="success"></div>
            </div>
            
            <script>
                document.getElementById('voteForm').addEventListener('submit', async (e) => {{
                    e.preventDefault();
                    
                    const submitBtn = document.getElementById('submitBtn');
                    const loading = document.getElementById('loading');
                    const errorDiv = document.getElementById('error');
                    const successDiv = document.getElementById('success');
                    
                    // Hide previous messages
                    errorDiv.style.display = 'none';
                    successDiv.style.display = 'none';
                    
                    // Show loading
                    submitBtn.disabled = true;
                    loading.style.display = 'block';
                    
                    const formData = new FormData(e.target);
                    const data = Object.fromEntries(formData);
                    
                    try {{
                        const response = await fetch(window.location.href, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify(data)
                        }});
                        
                        const result = await response.json();
                        
                        loading.style.display = 'none';
                        
                        if (result.success) {{
                            successDiv.textContent = result.message;
                            successDiv.style.display = 'block';
                            
                            // Redirect after 3 seconds
                            setTimeout(() => {{
                                window.location.href = '/';
                            }}, 3000);
                        }} else {{
                            errorDiv.textContent = result.message || 'Failed to submit vote';
                            errorDiv.style.display = 'block';
                            submitBtn.disabled = false;
                        }}
                    }} catch (error) {{
                        loading.style.display = 'none';
                        errorDiv.textContent = 'Network error: ' + error.message;
                        errorDiv.style.display = 'block';
                        submitBtn.disabled = false;
                    }}
                }});
                
                // Auto-focus TOTP input
                document.getElementById('totp_code').focus();
            </script>
        </body>
        </html>
        """
        
        return html
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Voting link expired'}), 400
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid voting token'}), 400
    except Exception as e:
        print(f"❌ Error in vote route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Master user login endpoint"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    totp_code = data.get('totp_code')
    
    if not all([username, password, totp_code]):
        return jsonify({'error': 'Missing credentials'}), 400
    
    try:
        ip_address = request.headers.get('X-Real-IP') or request.remote_addr
        
        user = master_user_manager.authenticate(
            username=username,
            password=password,
            totp_code=totp_code,
            ip_address=ip_address
        )
        
        if user:
            # Generate session token
            token = jwt.encode({
                'user_id': user['id'],
                'username': user['username'],
                'type': 'master'
            }, os.getenv('JWT_SECRET'), algorithm='HS256')
            
            return jsonify({
                'success': True,
                'user': user,
                'token': token
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Development only - use gunicorn in production
    app.run(host='0.0.0.0', port=3333, debug=False)
