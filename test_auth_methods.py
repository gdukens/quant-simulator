#!/usr/bin/env python3
"""
PostgreSQL Connection Test WITH PASSWORD
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def test_with_password():
    """Test PostgreSQL connection WITH password"""
    try:
        print("🔗 Connecting to PostgreSQL WITH password...")
        conn = psycopg2.connect(
            host='127.0.0.1', 
            port=5433,
            user='quantlib', 
            database='quantlib_pro',
            password='devpassword'  # Using the password we set
        )
        
        print("✅ SUCCESS! PostgreSQL connection with password works!")
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT current_database(), current_user, version();")
        result = cur.fetchone()
        
        print(f"📊 Database: {result['current_database']}")
        print(f"   User: {result['current_user']}")
        print(f"   Version: {result['version'][:50]}...")
        
        # Test table operations
        cur.execute("""
            CREATE TABLE IF NOT EXISTS auth_test (
                id SERIAL PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cur.execute("INSERT INTO auth_test (message) VALUES ('Authentication FIXED!');")
        conn.commit()
        
        cur.execute("SELECT * FROM auth_test ORDER BY id DESC LIMIT 1;")
        test_result = cur.fetchone()
        print(f"   Test Record: {test_result['message']}")
        
        conn.close()
        print("\n🎉 POSTGRESQL AUTHENTICATION COMPLETELY FIXED!")
        return True
        
    except Exception as e:
        print(f"❌ Still failed: {e}")
        return False

def test_without_password():
    """Test without password to see if trust method works"""
    try:
        print("\n🔗 Testing without password (trust method)...")
        conn = psycopg2.connect(
            host='127.0.0.1', 
            port=5433,
            user='quantlib', 
            database='quantlib_pro'
            # No password
        )
        
        print("✅ Trust method works!")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Trust method failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing PostgreSQL authentication methods...")
    
    # Try with password first
    password_works = test_with_password()
    
    # Try without password
    trust_works = test_without_password()
    
    if password_works:
        print("\n✅ SOLUTION: Use password authentication")
        print("   Update your connection strings to include password='devpassword'")
    elif trust_works:
        print("\n✅ SOLUTION: Trust authentication working")
    else:
        print("\n❌ Both methods failed - need different approach")