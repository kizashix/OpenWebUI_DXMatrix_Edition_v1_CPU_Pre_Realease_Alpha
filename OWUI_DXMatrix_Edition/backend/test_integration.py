"""
Open WebUI DXMatrix Edition - Integration Test Suite
Tests the integration of Windows-native components with Open WebUI backend
"""

import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integration_manager import get_integration_manager, shutdown_integration_manager
from windows_session_middleware import (
    WindowsSessionMiddleware, 
    create_user_session, 
    get_user_from_session,
    delete_user_session,
    update_session_data,
    get_session_data
)
from windows_config_adapter import (
    WindowsPersistentConfig,
    WindowsAppConfig,
    create_persistent_config,
    create_app_config,
    get_config_value,
    set_config_value,
    save_config,
    get_config,
    reset_config,
    migrate_redis_config,
    export_config_to_redis_format
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockRequest:
    """Mock FastAPI request object for testing"""
    
    def __init__(self):
        self.state = type('State', (), {})()
        self.cookies = {}
        self.headers = {}


class MockResponse:
    """Mock FastAPI response object for testing"""
    
    def __init__(self):
        self.cookies = {}
    
    def set_cookie(self, key, value, **kwargs):
        self.cookies[key] = value
    
    def delete_cookie(self, key, **kwargs):
        if key in self.cookies:
            del self.cookies[key]


class IntegrationTestSuite:
    """Comprehensive test suite for integration components"""
    
    def __init__(self):
        self.integration_mgr = get_integration_manager()
        self.test_results = []
        
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting Open WebUI DXMatrix Edition Integration Tests")
        
        test_methods = [
            self.test_integration_manager,
            self.test_session_middleware,
            self.test_config_adapter,
            self.test_redis_compatibility,
            self.test_config_migration,
            self.test_session_management,
            self.test_config_persistence,
            self.test_error_handling,
            self.test_performance,
            self.test_windows_specific_features
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                logger.info(f"Running {test_method.__name__}...")
                test_method()
                logger.info(f"✅ {test_method.__name__} PASSED")
                passed += 1
            except Exception as e:
                logger.error(f"❌ {test_method.__name__} FAILED: {e}")
                failed += 1
                self.test_results.append({
                    "test": test_method.__name__,
                    "status": "FAILED",
                    "error": str(e)
                })
        
        logger.info(f"\n📊 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            logger.info("🎉 All integration tests passed!")
        else:
            logger.error(f"❌ {failed} tests failed. Check logs for details.")
        
        return passed, failed

    def test_integration_manager(self):
        """Test the integration manager functionality"""
        logger.info("Testing Integration Manager...")
        
        # Test basic functionality
        assert self.integration_mgr is not None
        assert hasattr(self.integration_mgr, 'db')
        assert hasattr(self.integration_mgr, 'session_mgr')
        assert hasattr(self.integration_mgr, 'config_mgr')
        
        # Test configuration migration
        test_redis_config = {
            "ENABLE_API_KEY": True,
            "ENABLE_OAUTH_SIGNUP": False,
            "OLLAMA_BASE_URLS": ["http://localhost:11434"],
            "OPENAI_API_KEYS": ["test-key"]
        }
        
        success = self.integration_mgr.migrate_config_from_redis(test_redis_config)
        assert success, "Configuration migration failed"
        
        # Test cache operations
        assert self.integration_mgr.cache_set("test_key", "test_value", 60)
        assert self.integration_mgr.cache_get("test_key") == "test_value"
        assert self.integration_mgr.cache_delete("test_key")
        
        # Test session operations
        user_data = {"user_id": "test_user", "email": "test@example.com"}
        session_id = self.integration_mgr.create_session_for_user("test_user", user_data)
        assert session_id is not None
        
        session_data = self.integration_mgr.validate_session(session_id)
        assert session_data is not None
        assert session_data.get("user_id") == "test_user"
        
        # Test system stats
        stats = self.integration_mgr.get_system_stats()
        assert isinstance(stats, dict)
        assert "windows_native" in stats
        
        logger.info("Integration Manager tests completed")

    def test_session_middleware(self):
        """Test the Windows session middleware"""
        logger.info("Testing Session Middleware...")
        
        # Create mock request and response
        request = MockRequest()
        response = MockResponse()
        
        # Test session creation
        user_data = {
            "user_id": "test_user",
            "email": "test@example.com",
            "role": "user",
            "created_at": datetime.now().isoformat()
        }
        
        session_id = create_user_session(request, "test_user", user_data)
        assert session_id is not None
        assert hasattr(request.state, 'session')
        assert hasattr(request.state, 'session_id')
        assert request.state.session_modified
        
        # Test session retrieval
        user_from_session = get_user_from_session(request)
        assert user_from_session is not None
        assert user_from_session.get("user_id") == "test_user"
        
        # Test session data operations
        update_session_data(request, "last_activity", datetime.now().isoformat())
        last_activity = get_session_data(request, "last_activity")
        assert last_activity is not None
        
        # Test session deletion
        success = delete_user_session(request)
        assert success
        assert request.state.session_deleted
        
        logger.info("Session Middleware tests completed")

    def test_config_adapter(self):
        """Test the Windows configuration adapter"""
        logger.info("Testing Configuration Adapter...")
        
        # Test persistent config
        test_config = create_persistent_config(
            "TEST_CONFIG", 
            "test.section.key", 
            "test_value"
        )
        assert test_config.value == "test_value"
        assert str(test_config) == "test_value"
        
        # Test app config
        app_config = create_app_config("test-app")
        assert app_config is not None
        assert hasattr(app_config, 'config_prefix')
        
        # Test configuration operations
        assert set_config_value("test.key", "test_value")
        assert get_config_value("test.key") == "test_value"
        
        # Test configuration save/load
        test_config_data = {
            "section1.key1": "value1",
            "section1.key2": "value2",
            "section2.key1": 123
        }
        
        assert save_config(test_config_data)
        
        all_config = get_config()
        assert "section1.key1" in all_config
        assert all_config["section1.key1"] == "value1"
        
        logger.info("Configuration Adapter tests completed")

    def test_redis_compatibility(self):
        """Test Redis-compatible interfaces"""
        logger.info("Testing Redis Compatibility...")
        
        from windows_config_adapter import (
            redis_config_get,
            redis_config_set,
            redis_config_delete,
            redis_config_exists
        )
        
        # Test Redis-compatible config operations
        assert redis_config_set("redis_test_key", "redis_test_value")
        assert redis_config_get("redis_test_key") == "redis_test_value"
        assert redis_config_exists("redis_test_key")
        assert redis_config_delete("redis_test_key")
        assert not redis_config_exists("redis_test_key")
        
        # Test cache operations through integration manager
        assert self.integration_mgr.cache_set("cache_test", {"data": "test"}, 300)
        cached_data = self.integration_mgr.cache_get("cache_test")
        assert cached_data is not None
        assert cached_data.get("data") == "test"
        
        logger.info("Redis Compatibility tests completed")

    def test_config_migration(self):
        """Test configuration migration from Redis format"""
        logger.info("Testing Configuration Migration...")
        
        # Test Redis config migration
        redis_config = {
            "auth": {
                "api_key": {
                    "enable": True,
                    "endpoint_restrictions": False
                },
                "jwt_expiry": 3600
            },
            "oauth": {
                "enable_signup": True,
                "google": {
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret"
                }
            },
            "ollama": {
                "enable_api": True,
                "base_urls": ["http://localhost:11434"]
            }
        }
        
        success = migrate_redis_config(redis_config)
        assert success, "Redis config migration failed"
        
        # Verify migrated config
        assert get_config_value("auth.api_key.enable") == True
        assert get_config_value("oauth.google.client_id") == "test_client_id"
        assert get_config_value("ollama.enable_api") == True
        
        # Test export to Redis format
        exported_config = export_config_to_redis_format()
        assert isinstance(exported_config, dict)
        assert "auth" in exported_config
        
        logger.info("Configuration Migration tests completed")

    def test_session_management(self):
        """Test comprehensive session management"""
        logger.info("Testing Session Management...")
        
        # Test multiple user sessions
        user1_data = {"user_id": "user1", "email": "user1@example.com"}
        user2_data = {"user_id": "user2", "email": "user2@example.com"}
        
        session1 = self.integration_mgr.create_session_for_user("user1", user1_data)
        session2 = self.integration_mgr.create_session_for_user("user2", user2_data)
        
        assert session1 != session2
        
        # Test session validation
        assert self.integration_mgr.validate_session(session1) is not None
        assert self.integration_mgr.validate_session(session2) is not None
        
        # Test user sessions retrieval
        user1_sessions = self.integration_mgr.get_user_sessions("user1")
        assert len(user1_sessions) > 0
        
        # Test session deletion
        assert self.integration_mgr.delete_user_session(session1)
        assert self.integration_mgr.validate_session(session1) is None
        
        logger.info("Session Management tests completed")

    def test_config_persistence(self):
        """Test configuration persistence across restarts"""
        logger.info("Testing Configuration Persistence...")
        
        # Set test configuration
        test_values = {
            "persistence.test1": "value1",
            "persistence.test2": 42,
            "persistence.test3": {"nested": "data"},
            "persistence.test4": [1, 2, 3]
        }
        
        for key, value in test_values.items():
            assert set_config_value(key, value)
        
        # Verify values are persisted
        for key, expected_value in test_values.items():
            actual_value = get_config_value(key)
            assert actual_value == expected_value, f"Persistence failed for {key}"
        
        # Test configuration reset
        assert reset_config()
        
        # Verify reset worked
        for key in test_values.keys():
            value = get_config_value(key)
            assert value is None or value == "", f"Reset failed for {key}"
        
        logger.info("Configuration Persistence tests completed")

    def test_error_handling(self):
        """Test error handling and edge cases"""
        logger.info("Testing Error Handling...")
        
        # Test invalid session ID
        invalid_session = self.integration_mgr.validate_session("invalid_session_id")
        assert invalid_session is None
        
        # Test invalid config key
        invalid_config = get_config_value("invalid.key.path")
        assert invalid_config is None
        
        # Test cache with invalid key
        assert not self.integration_mgr.cache_set("", "value")
        assert self.integration_mgr.cache_get("") is None
        
        # Test session with invalid data
        invalid_session_id = self.integration_mgr.create_session_for_user("", {})
        assert invalid_session_id is None
        
        # Test configuration with invalid data
        assert not set_config_value("", None)
        
        logger.info("Error Handling tests completed")

    def test_performance(self):
        """Test performance characteristics"""
        logger.info("Testing Performance...")
        
        import time
        
        # Test cache performance
        start_time = time.time()
        for i in range(100):
            self.integration_mgr.cache_set(f"perf_test_{i}", f"value_{i}")
        
        cache_set_time = time.time() - start_time
        logger.info(f"Cache set performance: {cache_set_time:.3f}s for 100 operations")
        
        # Test config performance
        start_time = time.time()
        for i in range(100):
            set_config_value(f"perf_config_{i}", f"value_{i}")
        
        config_set_time = time.time() - start_time
        logger.info(f"Config set performance: {config_set_time:.3f}s for 100 operations")
        
        # Test session performance
        start_time = time.time()
        for i in range(50):
            user_data = {"user_id": f"perf_user_{i}", "email": f"user{i}@example.com"}
            self.integration_mgr.create_session_for_user(f"perf_user_{i}", user_data)
        
        session_create_time = time.time() - start_time
        logger.info(f"Session creation performance: {session_create_time:.3f}s for 50 operations")
        
        # Performance assertions (adjust thresholds as needed)
        assert cache_set_time < 1.0, f"Cache set too slow: {cache_set_time}s"
        assert config_set_time < 1.0, f"Config set too slow: {config_set_time}s"
        assert session_create_time < 1.0, f"Session creation too slow: {session_create_time}s"
        
        logger.info("Performance tests completed")

    def test_windows_specific_features(self):
        """Test Windows-specific features"""
        logger.info("Testing Windows-Specific Features...")
        
        # Test Windows path handling
        from config_manager import get_config_manager
        config_mgr = get_config_manager()
        
        # Verify Windows paths are handled correctly
        config_path = config_mgr.get_config_path()
        assert "\\" in config_path or "/" in config_path
        assert os.path.exists(os.path.dirname(config_path))
        
        # Test Windows-specific configuration
        windows_config = {
            "windows.auto_start": True,
            "windows.system_tray": True,
            "windows.notifications": True,
            "windows.theme": "dark"
        }
        
        for key, value in windows_config.items():
            assert set_config_value(key, value)
            assert get_config_value(key) == value
        
        # Test Windows session cleanup
        cleanup_stats = self.integration_mgr.cleanup_expired_data()
        assert isinstance(cleanup_stats, dict)
        assert "sessions_cleaned" in cleanup_stats
        assert "cache_entries_cleaned" in cleanup_stats
        
        logger.info("Windows-Specific Features tests completed")


def main():
    """Main test runner"""
    try:
        # Create and run test suite
        test_suite = IntegrationTestSuite()
        passed, failed = test_suite.run_all_tests()
        
        # Print summary
        print("\n" + "="*60)
        print("🎯 OPEN WEBUI DXMATRIX EDITION - INTEGRATION TEST SUMMARY")
        print("="*60)
        print(f"✅ Tests Passed: {passed}")
        print(f"❌ Tests Failed: {failed}")
        print(f"📊 Total Tests: {passed + failed}")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Integration is ready for Open WebUI.")
            print("\n🚀 Next Steps:")
            print("   1. Copy integration files to Open WebUI backend")
            print("   2. Update Open WebUI imports to use Windows-native components")
            print("   3. Replace Redis dependencies with SQLite implementations")
            print("   4. Test with actual Open WebUI backend")
        else:
            print(f"\n⚠️  {failed} tests failed. Please check the logs above.")
        
        print("="*60)
        
        return failed == 0
        
    except Exception as e:
        logger.error(f"Test suite failed with error: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            shutdown_integration_manager()
        except:
            pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 