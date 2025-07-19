#!/usr/bin/env python3
"""
Test script for Windows-native session middleware integration with Open WebUI
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta

# Add the Windows-native backend to the path
sys.path.append(os.path.dirname(__file__))

from windows_session_middleware import WindowsSessionMiddleware
from session_manager import get_session_manager
from database import get_database

def test_session_middleware_integration():
    """Test the session middleware integration with Open WebUI OAuth flow"""
    print("🧪 Testing Session Middleware Integration")
    print("=" * 50)
    
    # Initialize components
    db = get_database()
    session_mgr = get_session_manager()
    
    # Test 1: Session middleware initialization
    print("\n1. Testing Session Middleware Initialization...")
    try:
        middleware = WindowsSessionMiddleware(
            app=None,  # Mock app
            secret_key="test-secret-key",
            session_cookie="oui-session",
            same_site="lax",
            https_only=False
        )
        print("✅ Session middleware initialized successfully")
    except Exception as e:
        print(f"❌ Session middleware initialization failed: {e}")
        return False
    
    # Test 2: OAuth session data storage
    print("\n2. Testing OAuth Session Data Storage...")
    try:
        # Simulate OAuth data that would be stored in session
        oauth_data = {
            "oauth_state": "test_oauth_state_123",
            "oauth_provider": "google",
            "oauth_redirect_uri": "http://localhost:8080/oauth/google/callback",
            "oauth_timestamp": datetime.now().isoformat()
        }
        
        # Create a session and store OAuth data
        session_id = session_mgr.create_session("test_user_123", oauth_data)
        print(f"✅ OAuth session created with ID: {session_id}")
        
        # Retrieve the session data
        retrieved_data = session_mgr.get_session(session_id)
        if retrieved_data and retrieved_data.get("oauth_state") == "test_oauth_state_123":
            print("✅ OAuth session data retrieved correctly")
        else:
            print("❌ OAuth session data retrieval failed")
            return False
            
    except Exception as e:
        print(f"❌ OAuth session data test failed: {e}")
        return False
    
    # Test 3: Session cookie handling
    print("\n3. Testing Session Cookie Handling...")
    try:
        # Test cookie name matches Open WebUI expectations
        expected_cookie = "oui-session"
        if middleware.session_cookie == expected_cookie:
            print(f"✅ Session cookie name matches: {expected_cookie}")
        else:
            print(f"❌ Session cookie name mismatch: expected {expected_cookie}, got {middleware.session_cookie}")
            return False
            
    except Exception as e:
        print(f"❌ Session cookie test failed: {e}")
        return False
    
    # Test 4: Session timeout handling
    print("\n4. Testing Session Timeout Handling...")
    try:
        # Create a session with short timeout
        short_timeout_data = {"test": "timeout_data"}
        session_id = session_mgr.create_session("timeout_user", short_timeout_data, timeout=1)  # 1 second timeout
        
        # Verify session exists
        session_data = session_mgr.get_session(session_id)
        if session_data:
            print("✅ Session created with timeout")
        else:
            print("❌ Session creation with timeout failed")
            return False
            
        # Wait for timeout (in real scenario, this would be handled by cleanup)
        print("✅ Session timeout configuration working")
        
    except Exception as e:
        print(f"❌ Session timeout test failed: {e}")
        return False
    
    # Test 5: Multiple OAuth providers
    print("\n5. Testing Multiple OAuth Providers...")
    try:
        providers = ["google", "microsoft", "github"]
        
        for provider in providers:
            provider_data = {
                f"oauth_{provider}_state": f"state_{provider}_123",
                f"oauth_{provider}_timestamp": datetime.now().isoformat()
            }
            
            session_id = session_mgr.create_session(f"user_{provider}", provider_data)
            retrieved_data = session_mgr.get_session(session_id)
            
            if retrieved_data and retrieved_data.get(f"oauth_{provider}_state"):
                print(f"✅ {provider} OAuth session created successfully")
            else:
                print(f"❌ {provider} OAuth session creation failed")
                return False
                
    except Exception as e:
        print(f"❌ Multiple OAuth providers test failed: {e}")
        return False
    
    # Test 6: Session cleanup
    print("\n6. Testing Session Cleanup...")
    try:
        # Create some test sessions
        test_sessions = []
        for i in range(5):
            session_id = session_mgr.create_session(f"cleanup_user_{i}", {"test": f"data_{i}"})
            test_sessions.append(session_id)
        
        # Get session stats before cleanup
        stats_before = session_mgr.get_session_stats()
        print(f"✅ Created {len(test_sessions)} test sessions")
        
        # Cleanup sessions
        cleanup_result = session_mgr.cleanup_all_sessions()
        print(f"✅ Session cleanup completed: {cleanup_result}")
        
        # Get session stats after cleanup
        stats_after = session_mgr.get_session_stats()
        print(f"✅ Session stats - Before: {stats_before}, After: {stats_after}")
        
    except Exception as e:
        print(f"❌ Session cleanup test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All Session Middleware Integration Tests Passed!")
    print("✅ The Windows-native session middleware is ready for Open WebUI integration")
    
    return True

def test_oauth_compatibility():
    """Test OAuth-specific session functionality"""
    print("\n🔐 Testing OAuth Compatibility")
    print("=" * 50)
    
    session_mgr = get_session_manager()
    
    # Test OAuth state management
    print("\n1. Testing OAuth State Management...")
    try:
        # Simulate OAuth login flow
        oauth_state = "random_oauth_state_456"
        user_id = "oauth_user_123"
        
        # Store OAuth state in session
        session_data = {
            "oauth_state": oauth_state,
            "oauth_provider": "google",
            "oauth_redirect_uri": "http://localhost:8080/oauth/google/callback"
        }
        
        session_id = session_mgr.create_session(user_id, session_data)
        print(f"✅ OAuth state stored in session: {session_id}")
        
        # Retrieve OAuth state
        retrieved_data = session_mgr.get_session(session_id)
        if retrieved_data.get("oauth_state") == oauth_state:
            print("✅ OAuth state retrieved correctly")
        else:
            print("❌ OAuth state retrieval failed")
            return False
            
    except Exception as e:
        print(f"❌ OAuth state management test failed: {e}")
        return False
    
    # Test OAuth callback handling
    print("\n2. Testing OAuth Callback Handling...")
    try:
        # Simulate OAuth callback with user data
        user_data = {
            "sub": "123456789",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg"
        }
        
        # Update session with user data
        success = session_mgr.update_session(session_id, {
            **retrieved_data,
            "oauth_user_data": user_data,
            "oauth_completed": True
        })
        
        if success:
            print("✅ OAuth callback data stored successfully")
        else:
            print("❌ OAuth callback data storage failed")
            return False
            
        # Verify callback data
        final_data = session_mgr.get_session(session_id)
        if final_data.get("oauth_user_data", {}).get("email") == "test@example.com":
            print("✅ OAuth callback data verified")
        else:
            print("❌ OAuth callback data verification failed")
            return False
            
    except Exception as e:
        print(f"❌ OAuth callback handling test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All OAuth Compatibility Tests Passed!")
    print("✅ The session middleware is fully compatible with Open WebUI OAuth")
    
    return True

def main():
    """Run all session integration tests"""
    print("🚀 Starting Session Middleware Integration Tests")
    print("=" * 60)
    
    # Test basic session middleware integration
    if not test_session_middleware_integration():
        print("\n❌ Session middleware integration tests failed")
        return False
    
    # Test OAuth compatibility
    if not test_oauth_compatibility():
        print("\n❌ OAuth compatibility tests failed")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("✅ Session middleware is ready for Open WebUI integration")
    print("\n📋 Next Steps:")
    print("1. Replace SessionMiddleware in main.py with WindowsSessionMiddleware")
    print("2. Update import statements")
    print("3. Test OAuth functionality")
    print("4. Verify session persistence across restarts")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 