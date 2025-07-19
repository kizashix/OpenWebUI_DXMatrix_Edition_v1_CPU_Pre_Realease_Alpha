"""
Test Windows-native configuration integration
"""

import os
import sys
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_windows_config():
    """Test the Windows-native configuration system"""
    try:
        logger.info("Testing Windows-native configuration integration...")
        
        # Test basic config operations
        from windows_config_adapter import get_config_value, set_config_value
        
        # Set a test value
        test_key = "test.integration.key"
        test_value = "test_value_123"
        
        success = set_config_value(test_key, test_value)
        assert success, "Failed to set config value"
        
        # Get the value back
        retrieved_value = get_config_value(test_key)
        assert retrieved_value == test_value, f"Config value mismatch: {retrieved_value} != {test_value}"
        
        # Test nested config
        nested_key = "test.nested.config"
        nested_value = {"key1": "value1", "key2": 42}
        
        success = set_config_value(nested_key, nested_value)
        assert success, "Failed to set nested config value"
        
        retrieved_nested = get_config_value(nested_key)
        assert retrieved_nested == nested_value, f"Nested config value mismatch"
        
        logger.info("✅ Windows-native configuration test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Windows-native configuration test FAILED: {e}")
        return False

def test_persistent_config():
    """Test PersistentConfig class"""
    try:
        logger.info("Testing PersistentConfig class...")
        
        from windows_config_adapter import WindowsPersistentConfig
        
        # Create a persistent config
        test_config = WindowsPersistentConfig(
            "TEST_CONFIG", 
            "test.persistent.key", 
            "default_value"
        )
        
        # Test value access
        assert test_config.value == "default_value", "Default value not set correctly"
        
        # Test string representation
        assert str(test_config) == "default_value", "String representation incorrect"
        
        # Test value update
        test_config.value = "updated_value"
        assert test_config.value == "updated_value", "Value update failed"
        
        logger.info("✅ PersistentConfig test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ PersistentConfig test FAILED: {e}")
        return False

def test_app_config():
    """Test AppConfig class"""
    try:
        logger.info("Testing AppConfig class...")
        
        from windows_config_adapter import WindowsAppConfig, WindowsPersistentConfig
        
        # Create app config
        app_config = WindowsAppConfig("test-app")
        
        # Add a persistent config
        test_persistent = WindowsPersistentConfig("TEST_APP_CONFIG", "app.test.key", "app_value")
        app_config.test_config = test_persistent
        
        # Test config access
        assert app_config.test_config == "app_value", "App config access failed"
        
        # Test config update
        app_config.test_config = "updated_app_value"
        assert app_config.test_config == "updated_app_value", "App config update failed"
        
        logger.info("✅ AppConfig test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ AppConfig test FAILED: {e}")
        return False

def main():
    """Run all configuration tests"""
    logger.info("🚀 Starting Windows-native Configuration Integration Tests")
    
    tests = [
        test_windows_config,
        test_persistent_config,
        test_app_config
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test.__name__} FAILED with exception: {e}")
            failed += 1
    
    logger.info(f"\n📊 Configuration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All configuration tests passed!")
        logger.info("✅ Step 1 (Configuration Management) is ready for Open WebUI integration!")
    else:
        logger.error(f"❌ {failed} configuration tests failed.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 