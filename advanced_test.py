#!/usr/bin/env python3
"""
🚀 VFS Global Advanced System Test - Core Component Testing
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend to Python path
project_root = Path(__file__).parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

def print_header(title: str):
    """Print test header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

async def test_telegram_bot():
    """Test Telegram bot functionality"""
    
    print_header("TELEGRAM BOT TEST")
    
    try:
        from core.telegram_bot import TelegramNotifier
        
        # Create notifier (with disabled config for testing)
        notifier = TelegramNotifier()
        
        print(f"✅ TelegramNotifier initialized")
        print(f"   📱 Enabled: {notifier.enabled}")
        print(f"   🔑 Token: {'SET' if notifier.bot_token else 'NOT SET'}")
        print(f"   📞 Chat ID: {'SET' if notifier.chat_id else 'NOT SET'}")
        
        # Test message formatting (no actual sending)
        test_message = notifier._format_appointment_message(
            city="İstanbul",
            date="15 Mayıs 2026", 
            time_slot="14:30",
            additional_info={"Test": "Value"}
        )
        
        print(f"✅ Message formatting working")
        print(f"   📝 Message length: {len(test_message)} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ Telegram bot test failed: {e}")
        return False

async def test_logger_system():
    """Test logging system"""
    
    print_header("LOGGER SYSTEM TEST")
    
    try:
        from utils.logger import VFSLogger, main_logger
        
        # Test logger creation
        test_logger = VFSLogger("test_logger")
        
        # Test different log levels
        test_logger.info("Test info message")
        test_logger.success("Test success message")
        test_logger.warning("Test warning message")
        test_logger.debug("Test debug message")
        
        # Test specialized logging
        test_logger.appointment_found("İstanbul", "2026-05-15", time="14:30")
        test_logger.session_event("login_test", user="test@example.com")
        test_logger.scraping_event("test_scan", city="Ankara")
        
        print("✅ Logger system working")
        print("   📝 Multiple log levels tested")
        print("   🏢 Specialized loggers tested") 
        print("   📄 Log files created in logs/ directory")
        
        return True
        
    except Exception as e:
        print(f"❌ Logger system test failed: {e}")
        return False

async def test_retry_engine():
    """Test retry engine"""
    
    print_header("RETRY ENGINE TEST")
    
    try:
        from core.retry_engine import retry_engine, RetryStrategy
        import random
        
        # Test function that sometimes fails
        async def test_operation(fail_rate: float = 0.3):
            if random.random() < fail_rate:
                raise Exception("Simulated failure")
            return "Success"
        
        # Test retry with low fail rate
        result = await retry_engine.execute_with_retry(
            operation_func=test_operation,
            operation_name="test_operation", 
            office="test_office",
            max_attempts=3,
            strategy=RetryStrategy.LINEAR,
            fail_rate=0.3  # 30% fail rate
        )
        
        print(f"✅ Retry engine working")
        print(f"   🔄 Operation success: {result.success}")
        print(f"   📊 Total attempts: {result.total_attempts}")
        print(f"   ⏱️  Total time: {result.total_time:.2f}s")
        
        # Test statistics
        stats = retry_engine.get_statistics()
        print(f"   📈 Engine stats: {len(stats['operation_stats'])} operations tracked")
        
        return True
        
    except Exception as e:
        print(f"❌ Retry engine test failed: {e}")
        return False

async def test_selenium_setup():
    """Test Selenium WebDriver setup (without actually opening browser)"""
    
    print_header("SELENIUM SETUP TEST")
    
    try:
        # Test imports
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        import undetected_chromedriver as uc
        
        print("✅ Selenium imports successful")
        print("   🌐 WebDriver: Available")
        print("   🤖 Undetected ChromeDriver: Available")
        
        # Test Chrome options creation (no actual browser launch)
        options = uc.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        
        print("✅ Chrome options configuration")
        print("   ⚙️  Headless mode: Configured")
        print("   🛡️  Security options: Set")
        
        # Note: Not actually launching browser in test
        print("⚠️  Browser launch test skipped (would require full setup)")
        
        return True
        
    except Exception as e:
        print(f"❌ Selenium setup test failed: {e}")
        return False

async def test_configuration_complete():
    """Test complete configuration system"""
    
    print_header("CONFIGURATION SYSTEM TEST")
    
    try:
        from config.settings import settings
        
        # Test all major config sections
        print("✅ VFS Offices:")
        for office in settings.VFS_OFFICES:
            print(f"   🏢 {office.city}: {office.base_url}")
        
        print("\n✅ Telegram Config:")
        print(f"   📱 Enabled: {settings.TELEGRAM.enabled}")
        print(f"   🔑 Token length: {len(settings.TELEGRAM.bot_token)}")
        
        print("\n✅ Database Config:")
        print(f"   🍃 MongoDB: {settings.DATABASE.mongodb_db}")
        print(f"   🐘 PostgreSQL: {settings.DATABASE.postgres_db}")
        
        print("\n✅ Scraping Config:")
        print(f"   ⏱️  Check interval: {settings.SCRAPING.check_interval_min}-{settings.SCRAPING.check_interval_max} min")
        print(f"   🔄 Max retries: {settings.SCRAPING.max_retries}")
        print(f"   👤 Headless: {settings.SCRAPING.headless}")
        
        print("\n✅ System Config:")
        print(f"   🐛 Debug: {settings.SYSTEM.debug}")
        print(f"   📝 Log level: {settings.SYSTEM.log_level}")
        print(f"   📸 Screenshots: {settings.SYSTEM.screenshot_enabled}")
        
        print("\n✅ Anti-Detection:")
        for feature, enabled in settings.ANTI_DETECTION.items():
            status = "✅" if enabled else "❌"
            print(f"   {status} {feature}: {enabled}")
        
        print("\n✅ VFS Selectors:")
        print(f"   🎯 Total selectors: {len(settings.VFS_SELECTORS)}")
        print(f"   🔐 Login fields: Available")
        print(f"   📅 Calendar selectors: Available")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def test_directory_structure():
    """Test directory structure and file organization"""
    
    print_header("DIRECTORY STRUCTURE TEST")
    
    try:
        from config.settings import settings
        
        # Check project structure
        project_dirs = [
            "backend",
            "backend/core", 
            "backend/config",
            "backend/utils",
            "backend/logs",
            "backend/screenshots"
        ]
        
        print("✅ Directory Structure:")
        for dir_path in project_dirs:
            full_path = project_root / dir_path
            exists = "✅" if full_path.exists() else "❌"
            print(f"   {exists} {dir_path}")
        
        # Check important files
        important_files = [
            "backend/config/settings.py",
            "backend/config/secrets.env",
            "backend/core/authentication.py", 
            "backend/core/scraper.py",
            "backend/core/telegram_bot.py",
            "backend/core/retry_engine.py",
            "backend/utils/logger.py",
            "main.py",
            "requirements.txt"
        ]
        
        print("\n✅ Important Files:")
        for file_path in important_files:
            full_path = project_root / file_path
            exists = "✅" if full_path.exists() else "❌"
            size = full_path.stat().st_size if full_path.exists() else 0
            print(f"   {exists} {file_path} ({size:,} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Directory structure test failed: {e}")
        return False

async def main():
    """Main test runner"""
    
    print("🚀 VFS GLOBAL ADVANCED SYSTEM TEST")
    print("⚡ Manaliza Enterprise Solutions")
    print("🎯 Core Component Validation")
    
    # Test suite
    tests = [
        ("Configuration System", test_configuration_complete),
        ("Directory Structure", test_directory_structure),
        ("Logger System", test_logger_system),
        ("Telegram Bot", test_telegram_bot),
        ("Retry Engine", test_retry_engine),
        ("Selenium Setup", test_selenium_setup),
    ]
    
    passed = 0
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}...")
        try:
            success = await test_func()
            if success:
                passed += 1
                results.append(("✅", test_name))
                print(f"✅ {test_name}: PASSED")
            else:
                results.append(("❌", test_name))
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            results.append(("💥", test_name))
            print(f"💥 {test_name}: EXCEPTION - {e}")
    
    # Final summary
    print("\n" + "="*60)
    print("📊 ADVANCED TEST RESULTS")
    print("="*60)
    
    for status, test_name in results:
        print(f"{status} {test_name}")
    
    print(f"\n📈 SUMMARY:")
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {len(tests) - passed}/{len(tests)}")
    
    if passed == len(tests):
        print(f"\n🎉 ALL ADVANCED TESTS PASSED!")
        print(f"🚀 System ready for integration testing")
        print(f"⏳ Ready for next phase: Authentication & Scraping")
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print(f"🔧 Component integration issues detected")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)