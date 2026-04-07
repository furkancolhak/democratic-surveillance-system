"""
Initialize database tables
Run this once after first setup
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'core'))

from database import db_manager

if __name__ == "__main__":
    print("🗄️  Initializing database...")
    
    try:
        db_manager.create_tables()
        print("✅ Database initialized successfully!")
        print("\n📋 Next steps:")
        print("   1. Create master user:")
        print("      python master_user_manager.py <username> <email> <password>")
        print("\n   2. Start the application:")
        print("      docker-compose up -d")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
