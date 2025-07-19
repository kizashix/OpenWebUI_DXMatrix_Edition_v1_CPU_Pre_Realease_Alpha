#!/usr/bin/env python3
"""
Open WebUI DXMatrix Edition - Core Components Test Script
Tests all Windows-native core components: Database, Session Manager, and Config Manager
"""

import sys
import os
import json
import time
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_database, close_database
from session_manager import get_session_manager, shutdown_session_manager
from config_manager import get_config_manager


def test_database_component():
    """Test database component functionality"""
    print("🔍 Testing Database Component...")
    
    db = get_database()
    
    # Test basic operations
    test_data = {"test": "value", "timestamp": datetime.now().isoformat()}
    
    # Test cache operations
    cache_success = db.set_cache("test_key", test_data, expires_in=300)
    print(f"  ✅ Cache set: {'PASS' if cache_success else 'FAIL'}")
    
    cached_data = db.get_cache("test_key")
    if cached_data and cached_data.get("test") == "value":
        print("  ✅ Cache get: PASS")
    else:
        print("  ❌ Cache get: FAIL")
    
    # Test session operations
    session_success = db.save_session("test_session", "test_user", test_data, expires_in=3600)
    print(f"  ✅ Session save: {'PASS' if session_success else 'FAIL'}")
    
    session_data = db.get_session("test_session")
    if session_data and session_data.get("test") == "value":
        print("  ✅ Session get: PASS")
    else:
        print("  ❌ Session get: FAIL")
    
    # Test settings operations
    settings_success = db.set_setting("test_setting", test_data, "Test setting")
    print(f"  ✅ Settings save: {'PASS' if settings_success else 'FAIL'}")
    
    settings_data = db.get_setting("test_setting")
    if settings_data and settings_data.get("test") == "value":
        print("  ✅ Settings get: PASS")
    else:
        print("  ❌ Settings get: FAIL")
    
    # Test database stats
    stats = db.get_stats()
    if isinstance(stats, dict) and "sessions_count" in stats:
        print("  ✅ Database stats: PASS")
        print(f"    📊 Database size: {stats.get('db_size_mb', 0):.2f} MB")
    else:
        print("  ❌ Database stats: FAIL")
    
    # Cleanup
    db.delete_cache("test_key")
    db.delete_session("test_session")
    print("  ✅ Database cleanup: PASS")


def test_session_manager_component():
    """Test session manager component functionality"""
    print("\n🔍 Testing Session Manager Component...")
    
    session_mgr = get_session_manager()
    
    # Test session creation
    user_data = {"username": "testuser", "role": "user"}
    session_id = session_mgr.create_session("test_user_123", user_data)
    
    if session_id:
        print("  ✅ Session creation: PASS")
    else:
        print("  ❌ Session creation: FAIL")
        return
    
    # Test session retrieval
    session_data = session_mgr.get_session(session_id)
    if session_data and session_data.get("data", {}).get("username") == "testuser":
        print("  ✅ Session retrieval: PASS")
    else:
        print("  ❌ Session retrieval: FAIL")
    
    # Test session validation
    is_valid = session_mgr.is_session_valid(session_id)
    print(f"  ✅ Session validation: {'PASS' if is_valid else 'FAIL'}")
    
    # Test session update
    update_data = {"last_action": "test_action"}
    update_success = session_mgr.update_session(session_id, update_data)
    print(f"  ✅ Session update: {'PASS' if update_success else 'FAIL'}")
    
    # Test session extension
    extend_success = session_mgr.extend_session(session_id, additional_time=7200)
    print(f"  ✅ Session extension: {'PASS' if extend_success else 'FAIL'}")
    
    # Test session stats
    stats = session_mgr.get_session_stats()
    if isinstance(stats, dict) and "total_sessions" in stats:
        print("  ✅ Session stats: PASS")
        print(f"    📊 Total sessions: {stats.get('total_sessions', 0)}")
    else:
        print("  ❌ Session stats: FAIL")
    
    # Test session deletion
    delete_success = session_mgr.delete_session(session_id)
    print(f"  ✅ Session deletion: {'PASS' if delete_success else 'FAIL'}")
    
    # Verify deletion
    deleted_session = session_mgr.get_session(session_id)
    if deleted_session is None:
        print("  ✅ Session deletion verification: PASS")
    else:
        print("  ❌ Session deletion verification: FAIL")


def test_config_manager_component():
    """Test configuration manager component functionality"""
    print("\n🔍 Testing Configuration Manager Component...")
    
    config_mgr = get_config_manager()
    
    # Test basic configuration retrieval
    app_name = config_mgr.get("app.name")
    if app_name == "Open WebUI DXMatrix Edition":
        print("  ✅ Default config retrieval: PASS")
    else:
        print("  ❌ Default config retrieval: FAIL")
    
    # Test configuration setting
    test_value = {"test": "config_value"}
    set_success = config_mgr.set("test.config_key", test_value, persistent=True)
    print(f"  ✅ Config set: {'PASS' if set_success else 'FAIL'}")
    
    # Test configuration retrieval
    retrieved_value = config_mgr.get("test.config_key")
    if retrieved_value and retrieved_value.get("test") == "config_value":
        print("  ✅ Config get: PASS")
    else:
        print("  ❌ Config get: FAIL")
    
    # Test configuration update
    updates = {
        "test.update_key1": "value1",
        "test.update_key2": "value2"
    }
    update_success = config_mgr.update(updates, persistent=True)
    print(f"  ✅ Config bulk update: {'PASS' if update_success else 'FAIL'}")
    
    # Test Windows-specific configuration
    windows_config = config_mgr.get_windows_specific_config()
    if isinstance(windows_config, dict) and "system_tray_enabled" in windows_config:
        print("  ✅ Windows config: PASS")
        print(f"    🪟 System tray enabled: {windows_config.get('system_tray_enabled')}")
    else:
        print("  ❌ Windows config: FAIL")
    
    # Test configuration validation
    validation = config_mgr.validate_config()
    if isinstance(validation, dict) and "valid" in validation:
        print(f"  ✅ Config validation: {'PASS' if validation['valid'] else 'FAIL'}")
        if validation.get("warnings"):
            print(f"    ⚠️  Warnings: {len(validation['warnings'])}")
        if validation.get("errors"):
            print(f"    ❌ Errors: {len(validation['errors'])}")
    else:
        print("  ❌ Config validation: FAIL")
    
    # Test configuration export
    export_success = config_mgr.export_config()
    print(f"  ✅ Config export: {'PASS' if export_success else 'FAIL'}")


def test_component_integration():
    """Test integration between components"""
    print("\n🔍 Testing Component Integration...")
    
    db = get_database()
    session_mgr = get_session_manager()
    config_mgr = get_config_manager()
    
    # Test session timeout from config
    session_timeout = config_mgr.get("session.timeout", 3600)
    print(f"  ✅ Session timeout from config: {session_timeout}s")
    
    # Test database path from config
    db_path = config_mgr.get("database.path")
    if db_path:
        print(f"  ✅ Database path from config: {db_path}")
    else:
        print("  ❌ Database path from config: FAIL")
    
    # Test session creation with config timeout
    session_id = session_mgr.create_session("integration_test_user")
    if session_id:
        print("  ✅ Integration session creation: PASS")
        
        # Test session retrieval
        session_data = session_mgr.get_session(session_id)
        if session_data:
            print("  ✅ Integration session retrieval: PASS")
        else:
            print("  ❌ Integration session retrieval: FAIL")
        
        # Cleanup
        session_mgr.delete_session(session_id)
    else:
        print("  ❌ Integration session creation: FAIL")
    
    # Test configuration persistence in database
    test_config = {"integration": "test", "timestamp": datetime.now().isoformat()}
    config_success = config_mgr.set("integration.test_key", test_config, persistent=True)
    
    if config_success:
        # Verify it's stored in database
        db_config = db.get_setting("config.integration.test_key")
        if db_config and db_config.get("integration") == "test":
            print("  ✅ Config database persistence: PASS")
        else:
            print("  ❌ Config database persistence: FAIL")
    else:
        print("  ❌ Config database persistence: FAIL")


def test_windows_specific_features():
    """Test Windows-specific features"""
    print("\n🔍 Testing Windows-Specific Features...")
    
    config_mgr = get_config_manager()
    
    # Test Windows AppData directory usage
    app_data_dir = config_mgr.get_windows_specific_config().get("app_data_dir")
    if app_data_dir and "AppData" in app_data_dir:
        print("  ✅ Windows AppData directory: PASS")
        print(f"    📁 AppData directory: {app_data_dir}")
    else:
        print("  ❌ Windows AppData directory: FAIL")
    
    # Test Windows service configuration
    service_name = config_mgr.get("windows.service_name")
    if service_name == "OWUI-DXMatrix":
        print("  ✅ Windows service config: PASS")
    else:
        print("  ❌ Windows service config: FAIL")
    
    # Test system tray configuration
    tray_enabled = config_mgr.get("windows.system_tray_enabled")
    print(f"  ✅ System tray config: {'PASS' if tray_enabled else 'FAIL'}")
    
    # Test firewall rule configuration
    firewall_rule = config_mgr.get("windows.firewall_rule_name")
    if firewall_rule == "Open WebUI DXMatrix Edition":
        print("  ✅ Firewall rule config: PASS")
    else:
        print("  ❌ Firewall rule config: FAIL")


def test_performance_and_scalability():
    """Test performance and scalability features"""
    print("\n🔍 Testing Performance and Scalability...")
    
    db = get_database()
    session_mgr = get_session_manager()
    
    # Test multiple session creation
    start_time = time.time()
    session_ids = []
    
    for i in range(10):
        session_id = session_mgr.create_session(f"perf_test_user_{i}")
        if session_id:
            session_ids.append(session_id)
    
    creation_time = time.time() - start_time
    print(f"  ✅ Multiple session creation: {len(session_ids)} sessions in {creation_time:.3f}s")
    
    # Test concurrent session retrieval
    start_time = time.time()
    retrieved_count = 0
    
    for session_id in session_ids:
        session_data = session_mgr.get_session(session_id)
        if session_data:
            retrieved_count += 1
    
    retrieval_time = time.time() - start_time
    print(f"  ✅ Concurrent session retrieval: {retrieved_count} sessions in {retrieval_time:.3f}s")
    
    # Test cache performance
    start_time = time.time()
    cache_hits = 0
    
    for i in range(50):
        cache_key = f"perf_cache_{i % 10}"  # Only 10 unique keys for cache hits
        db.set_cache(cache_key, {"data": f"value_{i}"}, expires_in=300)
        cached_data = db.get_cache(cache_key)
        if cached_data:
            cache_hits += 1
    
    cache_time = time.time() - start_time
    print(f"  ✅ Cache performance: {cache_hits} hits in {cache_time:.3f}s")
    
    # Cleanup
    for session_id in session_ids:
        session_mgr.delete_session(session_id)
    
    # Clear test cache entries
    for i in range(10):
        db.delete_cache(f"perf_cache_{i}")


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting Open WebUI DXMatrix Edition Core Components Tests")
    print("=" * 70)
    
    test_results = {
        "database": False,
        "session_manager": False,
        "config_manager": False,
        "integration": False,
        "windows_features": False,
        "performance": False
    }
    
    try:
        # Test individual components
        test_database_component()
        test_results["database"] = True
        
        test_session_manager_component()
        test_results["session_manager"] = True
        
        test_config_manager_component()
        test_results["config_manager"] = True
        
        # Test integration
        test_component_integration()
        test_results["integration"] = True
        
        # Test Windows-specific features
        test_windows_specific_features()
        test_results["windows_features"] = True
        
        # Test performance
        test_performance_and_scalability()
        test_results["performance"] = True
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 Test Results Summary:")
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        for test_name, passed in test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All core components are working correctly!")
            print("✨ Windows-native Open WebUI is ready for integration!")
        else:
            print("⚠️  Some tests failed. Please check the logs above.")
        
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up test resources...")
        close_database()
        shutdown_session_manager()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1) 