"""
Infrastructure initialization script.
Run this to set up the database and test connections.
"""

import sys
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

print("=" * 60)
print("INFRASTRUCTURE INITIALIZATION")
print("=" * 60)
print(f"\nUsing DATABASE_URL: {os.getenv('DATABASE_URL')}")

# Step 1: Initialize database schema
print("\n[1/4] Initializing database schema...")
try:
    from quantlib_pro.data.database import init_db
    init_db()
    print(" Database schema created")
except Exception as e:
    print(f" Failed to create schema: {e}")
    sys.exit(1)

# Step 2: Test PostgreSQL connection
print("\n[2/4] Testing PostgreSQL connection...")
try:
    from quantlib_pro.data.database import get_postgres_session
    from quantlib_pro.data.models.user import User
    
    with get_postgres_session() as session:
        # Create test user
        test_user = User(
            user_id=uuid.uuid4(),
            username="demo_user",
            email="demo@quantlib.pro",
            created_at=datetime.utcnow()
        )
        session.add(test_user)
        session.commit()
        
        # Query users
        users_count = session.query(User).count()
        print(f" PostgreSQL working! Users in database: {users_count}")
        
except Exception as e:
    print(f" PostgreSQL connection failed: {e}")
    sys.exit(1)

# Step 3: Test Redis connection
print("\n[3/4] Testing Redis connection...")
try:
    import redis
    import os
    
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_password = os.getenv("REDIS_PASSWORD")
    
    if redis_password:
        r = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)
    else:
        r = redis.Redis(host=redis_host, port=redis_port, db=0)
    
    # Test connection
    r.ping()
    r.set("quantlib:test", "infrastructure_ok")
    value = r.get("quantlib:test")
    
    print(f" Redis working! Test value: {value.decode('utf-8')}")
    
except Exception as e:
    print(f" Redis connection failed: {e}")
    print("   (This is optional - system will work without caching)")

# Step 4: Display configuration
print("\n[4/4] Configuration summary:")
print(f"  • Database URL: {os.getenv('DATABASE_URL', 'Not set')}")
print(f"  • Redis Host: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}")
print(f"  • Cache Enabled: {os.getenv('CACHE_ENABLED', 'false')}")

print("\n" + "=" * 60)
print("INFRASTRUCTURE READY!")
print("=" * 60)
print("\nNext steps:")
print("  1. Start Streamlit: streamlit run streamlit_app.py --server.port 8503")
print("  2. Start FastAPI: uvicorn main_api:app --port 8000")
print("  3. View containers: docker ps")
print("  4. Stop infrastructure: docker-compose down")
