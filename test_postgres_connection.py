#!/usr/bin/env python3
"""
PostgreSQL Connection Test
Tests the connection to our Docker PostgreSQL instance
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def test_postgres_connection():
    """Test PostgreSQL connection and basic operations"""
    try:
        print("🔗 Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host='127.0.0.1', 
            port=5433,  # External Docker port
            user='quantlib', 
            database='quantlib_pro'
            # No password with trust method
        )
        
        print("✅ SUCCESS! PostgreSQL connection established!")
        
        # Test basic operations
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get connection info
        cur.execute("""
            SELECT 
                current_database() as database,
                current_user as user,
                version() as pg_version
        """)
        info = cur.fetchone()
        
        print(f"📊 Connection Details:")
        print(f"   Database: {info['database']}")
        print(f"   User: {info['user']}")
        print(f"   Version: {info['pg_version'][:50]}...")
        
        # Test table creation and insertion
        print("\n🧪 Testing table operations...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                test_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message TEXT
            );
        """)
        
        cur.execute("""
            INSERT INTO connection_test (message) 
            VALUES ('PostgreSQL authentication fixed!')
        """)
        
        conn.commit()
        
        # Verify insertion
        cur.execute("""
            SELECT id, test_time, message 
            FROM connection_test 
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        result = cur.fetchone()
        print(f"   Test Record: ID={result['id']}, Message='{result['message']}'")
        
        # Clean up
        cur.execute("DROP TABLE IF EXISTS connection_test")
        conn.commit()
        
        conn.close()
        
        print("\n🎉 POSTGRESQL AUTHENTICATION FIXED!")
        print("   ✓ Connection successful")
        print("   ✓ Database operations working")
        print("   ✓ Ready for full application integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nDebugging info:")
        print(f"  - Host: 127.0.0.1")
        print(f"  - Port: 5433") 
        print(f"  - User: quantlib")
        print(f"  - Database: quantlib_pro")
        return False

if __name__ == "__main__":
    test_postgres_connection()