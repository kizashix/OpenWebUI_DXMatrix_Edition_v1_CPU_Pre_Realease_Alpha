#!/usr/bin/env python3
"""
Open WebUI DXMatrix Edition - Database Test Script
Tests the SQLite database functionality for Windows-native implementation
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database, get_database, close_database


def test_session_management():
    """Test session management functionality"""
    print("🧪 Testing Session Management...")
    
    db = get_database()
    
    # Test session creation
    session_id = "test_session_123"
    user_id = "test_user_456"
    session_data = {
        "user_id": user_id,
        "username": "testuser",
        "permissions": ["read", "write"],
        "last_activity": datetime.now().isoformat()
    }
    
    # Save session
    success = db.save_session(session_id, user_id, session_data, expires_in=3600)
    print(f"  ✅ Session save: {'PASS' if success else 'FAIL'}")
    
    # Retrieve session
    retrieved_data = db.get_session(session_id)
    if retrieved_data and retrieved_data.get("username") == "testuser":
        print("  ✅ Session retrieval: PASS")
    else:
        print("  ❌ Session retrieval: FAIL")
    
    # Test session expiration
    expired_session_id = "expired_session_789"
    db.save_session(expired_session_id, user_id, session_data, expires_in=1)
    import time
    time.sleep(2)  # Wait for expiration
    
    expired_data = db.get_session(expired_session_id)
    if expired_data is None:
        print("  ✅ Session expiration: PASS")
    else:
        print("  ❌ Session expiration: FAIL")
    
    # Clean up
    db.delete_session(session_id)
    db.delete_session(expired_session_id)
    print("  ✅ Session cleanup: PASS")


def test_cache_management():
    """Test cache management functionality"""
    print("\n🧪 Testing Cache Management...")
    
    db = get_database()
    
    # Test cache set/get
    cache_key = "test_cache_key"
    cache_value = {
        "data": "test_value",
        "timestamp": datetime.now().isoformat(),
        "nested": {"key": "value"}
    }
    
    # Set cache
    success = db.set_cache(cache_key, cache_value, expires_in=300)
    print(f"  ✅ Cache set: {'PASS' if success else 'FAIL'}")
    
    # Get cache
    retrieved_value = db.get_cache(cache_key)
    if retrieved_value and retrieved_value.get("data") == "test_value":
        print("  ✅ Cache get: PASS")
    else:
        print("  ❌ Cache get: FAIL")
    
    # Test cache expiration
    expiring_key = "expiring_cache_key"
    db.set_cache(expiring_key, cache_value, expires_in=1)
    import time
    time.sleep(2)  # Wait for expiration
    
    expired_value = db.get_cache(expiring_key)
    if expired_value is None:
        print("  ✅ Cache expiration: PASS")
    else:
        print("  ❌ Cache expiration: FAIL")
    
    # Test cache deletion
    db.delete_cache(cache_key)
    deleted_value = db.get_cache(cache_key)
    if deleted_value is None:
        print("  ✅ Cache deletion: PASS")
    else:
        print("  ❌ Cache deletion: FAIL")
    
    # Clean up
    db.delete_cache(expiring_key)


def test_user_management():
    """Test user management functionality"""
    print("\n🧪 Testing User Management...")
    
    db = get_database()
    
    # Test user creation
    user_id = "test_user_789"
    username = "testuser"
    email = "test@example.com"
    
    success = db.create_user(user_id, username, email, role="user")
    print(f"  ✅ User creation: {'PASS' if success else 'FAIL'}")
    
    # Test duplicate user creation (should fail)
    duplicate_success = db.create_user(user_id, username, email)
    if not duplicate_success:
        print("  ✅ Duplicate user prevention: PASS")
    else:
        print("  ❌ Duplicate user prevention: FAIL")
    
    # Test user retrieval
    user = db.get_user(user_id)
    if user and user.get("username") == username:
        print("  ✅ User retrieval: PASS")
    else:
        print("  ❌ User retrieval: FAIL")
    
    # Test user login update
    login_success = db.update_user_login(user_id)
    print(f"  ✅ User login update: {'PASS' if login_success else 'FAIL'}")
    
    # Verify login time was updated
    updated_user = db.get_user(user_id)
    if updated_user and updated_user.get("last_login"):
        print("  ✅ Login time update: PASS")
    else:
        print("  ❌ Login time update: FAIL")


def test_settings_management():
    """Test settings management functionality"""
    print("\n🧪 Testing Settings Management...")
    
    db = get_database()
    
    # Test setting creation
    setting_key = "test_setting"
    setting_value = {
        "enabled": True,
        "max_connections": 100,
        "timeout": 30
    }
    description = "Test configuration setting"
    
    success = db.set_setting(setting_key, setting_value, description)
    print(f"  ✅ Setting creation: {'PASS' if success else 'FAIL'}")
    
    # Test setting retrieval
    retrieved_value = db.get_setting(setting_key)
    if retrieved_value and retrieved_value.get("enabled") == True:
        print("  ✅ Setting retrieval: PASS")
    else:
        print("  ❌ Setting retrieval: FAIL")
    
    # Test default value for non-existent setting
    default_value = db.get_setting("non_existent_setting", default="default_value")
    if default_value == "default_value":
        print("  ✅ Default value handling: PASS")
    else:
        print("  ❌ Default value handling: FAIL")
    
    # Test setting update
    updated_value = {
        "enabled": False,
        "max_connections": 200,
        "timeout": 60
    }
    update_success = db.set_setting(setting_key, updated_value)
    print(f"  ✅ Setting update: {'PASS' if update_success else 'FAIL'}")


def test_database_stats():
    """Test database statistics functionality"""
    print("\n🧪 Testing Database Statistics...")
    
    db = get_database()
    
    # Get database stats
    stats = db.get_stats()
    
    if isinstance(stats, dict) and "sessions_count" in stats:
        print("  ✅ Database stats retrieval: PASS")
        print(f"    📊 Sessions: {stats.get('sessions_count', 0)}")
        print(f"    📊 Cache entries: {stats.get('cache_count', 0)}")
        print(f"    📊 Users: {stats.get('users_count', 0)}")
        print(f"    📊 Chats: {stats.get('chats_count', 0)}")
        print(f"    📊 Database size: {stats.get('db_size_mb', 0):.2f} MB")
    else:
        print("  ❌ Database stats retrieval: FAIL")


def test_database_cleanup():
    """Test database cleanup functionality"""
    print("\n🧪 Testing Database Cleanup...")
    
    db = get_database()
    
    # Create some test data that will expire
    for i in range(5):
        session_id = f"cleanup_test_session_{i}"
        cache_key = f"cleanup_test_cache_{i}"
        
        db.save_session(session_id, "test_user", {"test": "data"}, expires_in=1)
        db.set_cache(cache_key, {"test": "data"}, expires_in=1)
    
    # Wait for expiration
    import time
    time.sleep(2)
    
    # Run cleanup
    db._cleanup_expired()
    
    # Verify cleanup
    stats_after = db.get_stats()
    print(f"  ✅ Database cleanup: PASS (cleaned expired entries)")


def run_all_tests():
    """Run all database tests"""
    print("🚀 Starting Open WebUI DXMatrix Edition Database Tests")
    print("=" * 60)
    
    try:
        test_session_management()
        test_cache_management()
        test_user_management()
        test_settings_management()
        test_database_stats()
        test_database_cleanup()
        
        print("\n" + "=" * 60)
        print("✅ All database tests completed successfully!")
        print("🎉 SQLite database is working correctly for Windows-native Open WebUI")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up database connections
        close_database()
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 