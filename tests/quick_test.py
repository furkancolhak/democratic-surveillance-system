"""
Quick Smoke Test
Fast test to verify critical components are working
Run this before deployment or after changes
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'services'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'utils'))

import tempfile
import shutil

def test_secret_sharing():
    """Quick test: Secret sharing"""
    print("🧪 Secret Sharing...", end=" ")
    try:
        from secret_sharing import ShamirSecretSharing
        
        sss = ShamirSecretSharing()
        secret = os.urandom(32)
        shares = sss.split_secret(secret, n=5, k=3)
        reconstructed = sss.reconstruct_secret(shares[:3], 32)
        
        assert secret == reconstructed, "Secret mismatch"
        print("✅")
        return True
    except Exception as e:
        print(f"❌ {e}")
        return False

def test_video_crypto():
    """Quick test: Video encryption"""
    print("🧪 Video Crypto...", end=" ")
    try:
        from video_crypto import VideoCrypto
        
        temp_dir = tempfile.mkdtemp()
        try:
            crypto = VideoCrypto(encrypted_dir=temp_dir)
            
            # Create test file
            test_file = os.path.join(temp_dir, "test.mp4")
            test_data = b"test" * 1000
            with open(test_file, 'wb') as f:
                f.write(test_data)
            
            # Encrypt
            encrypted_path, key = crypto.encrypt_video(test_file)
            
            # Decrypt
            decrypted_path = crypto.decrypt_video(encrypted_path, key, temp_dir)
            
            # Verify
            with open(decrypted_path, 'rb') as f:
                decrypted_data = f.read()
            
            assert test_data == decrypted_data, "Data mismatch"
            print("✅")
            return True
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        print(f"❌ {e}")
        return False

def test_video_source():
    """Quick test: Video source creation"""
    print("🧪 Video Source...", end=" ")
    try:
        from video_source import create_video_source, WebcamSource, RTSPSource, FileSource
        
        # Test factory
        webcam = create_video_source('webcam', camera_index=0)
        assert isinstance(webcam, WebcamSource), "Webcam type mismatch"
        
        rtsp = create_video_source('rtsp', rtsp_url='rtsp://test.com/stream')
        assert isinstance(rtsp, RTSPSource), "RTSP type mismatch"
        
        file_src = create_video_source('file', file_path='test.mp4')
        assert isinstance(file_src, FileSource), "File type mismatch"
        
        print("✅")
        return True
    except Exception as e:
        print(f"❌ {e}")
        return False

def test_imports():
    """Quick test: All imports work"""
    print("🧪 Imports...", end=" ")
    try:
        # Core imports
        from secret_sharing import ShamirSecretSharing
        from video_crypto import VideoCrypto
        from video_source import create_video_source
        
        # Try database imports (may fail if DB not available)
        try:
            from database import db_manager
            from secure_member_auth import SecureMemberAuth
            from secure_voting_system import SecureVotingSystem
            db_available = True
        except:
            db_available = False
        
        print("✅" + (" (DB available)" if db_available else " (DB not available)"))
        return True
    except Exception as e:
        print(f"❌ {e}")
        return False

def test_env_config():
    """Quick test: Environment configuration"""
    print("🧪 Environment...", end=" ")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check critical env vars
        smtp_server = os.getenv('SMTP_SERVER')
        base_url = os.getenv('BASE_URL')
        video_source = os.getenv('VIDEO_SOURCE_TYPE', 'webcam')
        
        assert smtp_server is not None, "SMTP_SERVER not set"
        assert base_url is not None, "BASE_URL not set"
        
        print(f"✅ (source: {video_source})")
        return True
    except Exception as e:
        print(f"❌ {e}")
        return False

def main():
    """Run quick smoke tests"""
    print("=" * 60)
    print("⚡ QUICK SMOKE TEST")
    print("=" * 60)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Environment", test_env_config),
        ("Secret Sharing", test_secret_sharing),
        ("Video Crypto", test_video_crypto),
        ("Video Source", test_video_source),
    ]
    
    results = []
    for name, test_func in tests:
        results.append(test_func())
    
    print()
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("=" * 60)
        return 0
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
