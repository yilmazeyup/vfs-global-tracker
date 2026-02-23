#!/usr/bin/env python3
"""
🧪 VFS Global Quick Test - Import & Basic Functionality
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
project_root = Path(__file__).parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

def test_imports():
    """Test critical imports"""
    
    print("🧪 TESTING VFS SYSTEM IMPORTS...")
    print("=" * 50)
    
    # Test 1: Basic Python modules
    try:
        import json
        import asyncio
        from datetime import datetime
        print("✅ Core Python modules - OK")
    except Exception as e:
        print(f"❌ Core Python modules failed: {e}")
        return False
    
    # Test 2: Settings (no external deps)
    try:
        # Try absolute import path
        import backend.config.settings as settings_module
        settings = settings_module.settings
        print("✅ Settings configuration - OK")
        print(f"   📍 Offices: {len(settings.VFS_OFFICES)}")
    except Exception as e:
        print(f"❌ Settings failed: {e}")
        # Try alternative path
        try:
            sys.path.append(str(backend_path / "config"))
            import settings as settings_module
            settings = settings_module.settings
            print("✅ Settings configuration (alt path) - OK")
        except Exception as e2:
            print(f"❌ Settings alt path failed: {e2}")
            return False
    
    # Test 3: Basic logger (minimal deps)
    try:
        # Create a simple logger test
        import logging
        logger = logging.getLogger("vfs_test")
        logger.info("Test log")
        print("✅ Basic logging - OK")
    except Exception as e:
        print(f"❌ Basic logging failed: {e}")
        return False
    
    # Test 4: Try external dependencies (if available)
    external_deps = [
        ("python-dotenv", "dotenv"),
        ("aiohttp", "aiohttp"), 
        ("selenium", "selenium"),
    ]
    
    available_deps = []
    for dep_name, import_name in external_deps:
        try:
            __import__(import_name)
            available_deps.append(dep_name)
            print(f"✅ {dep_name} - Available")
        except ImportError:
            print(f"⏳ {dep_name} - Installing...")
    
    print(f"\n📊 Dependencies available: {len(available_deps)}/{len(external_deps)}")
    
    return True

def test_configuration():
    """Test configuration validation"""
    
    print("\n🔧 TESTING CONFIGURATION...")
    print("=" * 50)
    
    try:
        import backend.config.settings as settings_module
        settings = settings_module.settings
        
        # Check VFS offices
        print(f"📍 VFS Offices: {len(settings.VFS_OFFICES)}")
        for office in settings.VFS_OFFICES:
            print(f"   • {office.city}: {office.base_url}")
        
        # Check directories
        print(f"📁 Logs dir: {settings.LOGS_DIR}")
        print(f"📸 Screenshots dir: {settings.SCREENSHOTS_DIR}")
        
        # Create directories if needed
        settings.LOGS_DIR.mkdir(exist_ok=True)
        settings.SCREENSHOTS_DIR.mkdir(exist_ok=True)
        print("✅ Directories created/verified")
        
        # Basic validation
        config_errors = settings.validate_config()
        if config_errors:
            print("⚠️ Configuration warnings:")
            for error in config_errors:
                print(f"   • {error}")
        else:
            print("✅ Configuration is valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_basic_functionality():
    """Test basic system functionality"""
    
    print("\n🎯 TESTING BASIC FUNCTIONALITY...")
    print("=" * 50)
    
    try:
        import backend.config.settings as settings_module
        settings = settings_module.settings
        import json
        from datetime import datetime
        
        # Test settings access
        office = settings.VFS_OFFICES[0]
        print(f"✅ Settings access: {office.name}")
        
        # Test JSON serialization
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "office": office.name,
            "test": True
        }
        json_str = json.dumps(test_data)
        print("✅ JSON serialization working")
        
        # Test file operations
        test_file = settings.LOGS_DIR / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
        
        test_file.unlink()  # Clean up
        print("✅ File operations working")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality failed: {e}")
        return False

def main():
    """Main test runner"""
    
    print("🎯 VFS GLOBAL RANDEVU SİSTEMİ - QUICK TEST")
    print("⚡ Manaliza Enterprise Solutions")
    print("📅 Development Phase Testing")
    print("=" * 60)
    
    # Run tests
    tests = [
        test_imports,
        test_configuration, 
        test_basic_functionality
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 30)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {len(tests) - passed}/{len(tests)}")
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 System ready for advanced testing")
        return True
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("🔧 Dependencies or configuration issues detected")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)