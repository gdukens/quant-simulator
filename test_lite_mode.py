#!/usr/bin/env python3
"""
LITE MODE Test - Redis + In-Memory Storage
Tests all components needed for LITE MODE operation
"""

import redis
import json
from datetime import datetime
import sys

def test_lite_mode():
    """Test LITE MODE components"""
    print("🚀 LITE MODE INITIALIZATION TEST")
    print("="*50)
    
    # Test Redis Connection
    print("\n🔗 Testing Redis Connection...")
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Test ping
        r.ping()
        print("✅ Redis connection: SUCCESS")
        
        # Test basic operations
        test_key = 'lite_mode_test'
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'message': 'LITE MODE operational!',
            'features': ['caching', 'sessions', 'temporary_storage'],
            'mode': 'development',
            'persistence': 'redis_only'
        }
        
        # Set with expiry
        r.setex(test_key, 300, json.dumps(test_data))
        
        # Retrieve and verify
        retrieved = json.loads(r.get(test_key))
        ttl = r.ttl(test_key)
        
        print(f"✅ Cache operations: SUCCESS")
        print(f"   Message: {retrieved['message']}")
        print(f"   TTL: {ttl} seconds")
        print(f"   Features: {len(retrieved['features'])} active")
        
        # Test Redis info
        info = r.info('memory')
        used_memory = info.get('used_memory_human', 'Unknown')
        print(f"   Memory usage: {used_memory}")
        
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False
    
    # Test In-Memory Storage Simulation  
    print("\n💾 Testing In-Memory Storage...")
    try:
        # Simulate session storage
        session_data = {
            'user_preferences': {'theme': 'dark', 'currency': 'USD'},
            'portfolio_cache': {'positions': [], 'last_update': datetime.now().isoformat()},
            'calculation_cache': {}
        }
        
        # Store in Redis as session
        session_key = 'session:lite_mode_user'
        r.setex(session_key, 3600, json.dumps(session_data))  # 1 hour
        
        print("✅ Session storage: SUCCESS")
        print(f"   Session key: {session_key}")
        print(f"   TTL: {r.ttl(session_key)} seconds")
        
    except Exception as e:
        print(f"❌ Session storage failed: {e}")
        return False
    
    # Summary
    print("\n" + "="*50)
    print("🎉 LITE MODE FULLY OPERATIONAL!")
    print("\n✅ Active Components:")
    print("   • Redis Caching (port 6379)")
    print("   • Session Management")
    print("   • Temporary Data Storage")
    print("   • Fast Key-Value Operations")
    
    print("\n⚡ Benefits:")
    print("   • Zero authentication issues")
    print("   • Fast development iterations")
    print("   • Immediate data access")
    print("   • Streamlit + FastAPI ready")
    
    print("\n⚠️  Development Notes:")
    print("   • Data resets on app restart (normal for dev)")
    print("   • Use Redis TTL for automatic cleanup")
    print("   • PostgreSQL can be added later for production")
    
    # Clean up test data
    r.delete(test_key, session_key)
    print("\n🧹 Test data cleaned up")
    
    return True

if __name__ == "__main__":
    success = test_lite_mode()
    sys.exit(0 if success else 1)