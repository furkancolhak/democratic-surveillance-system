"""
Test script to verify system is working
"""

import sys
import uuid
from database import db_manager
from master_user_manager import MasterUserManager
from secure_member_auth import SecureMemberAuth
from secure_voting_system import SecureVotingSystem

def test_database():
    """Test database connection"""
    print("\n1️⃣  Testing database connection...")
    try:
        session = db_manager.get_session()
        result = session.execute('SELECT 1').fetchone()
        session.close()
        print("   ✅ Database connection successful")
        return True
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def test_master_key():
    """Test master key"""
    print("\n2️⃣  Testing master key encryption...")
    try:
        test_data = b"test_secret_data"
        encrypted = db_manager.master_key_manager.encrypt(test_data)
        decrypted = db_manager.master_key_manager.decrypt(encrypted)
        
        if decrypted == test_data:
            print("   ✅ Master key encryption working")
            return True
        else:
            print("   ❌ Master key encryption failed")
            return False
    except Exception as e:
        print(f"   ❌ Master key test failed: {e}")
        return False

def test_master_user():
    """Test master user creation"""
    print("\n3️⃣  Testing master user system...")
    try:
        manager = MasterUserManager()
        users = manager.list_master_users()
        
        if users:
            print(f"   ✅ Found {len(users)} master user(s)")
            for user in users:
                print(f"      - {user['username']} ({user['email']})")
            return True
        else:
            print("   ⚠️  No master users found")
            print("      Create one with: python master_user_manager.py <username> <email> <password>")
            return False
    except Exception as e:
        print(f"   ❌ Master user test failed: {e}")
        return False

def test_member_auth():
    """Test member authentication system"""
    print("\n4️⃣  Testing member authentication...")
    try:
        auth = SecureMemberAuth()
        members = auth.get_active_members()
        
        if members:
            print(f"   ✅ Found {len(members)} active member(s)")
            for member in members:
                print(f"      - {member['name']} ({member['email']})")
            return True
        else:
            print("   ⚠️  No members found")
            print("      Register members through master user interface")
            return False
    except Exception as e:
        print(f"   ❌ Member auth test failed: {e}")
        return False

def test_voting_system():
    """Test voting system"""
    print("\n5️⃣  Testing voting system...")
    try:
        voting = SecureVotingSystem()
        print("   ✅ Voting system initialized")
        return True
    except Exception as e:
        print(f"   ❌ Voting system test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🔒 Secure Surveillance System - System Test")
    print("=" * 60)
    
    tests = [
        test_database,
        test_master_key,
        test_master_user,
        test_member_auth,
        test_voting_system
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"   ❌ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Test Results")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! System is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
