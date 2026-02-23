"""
⚙️ VFS Global Randevu Sistemi - Ana Konfigürasyon
Enterprise-grade configuration management
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path

# Proje kök dizini
BASE_DIR = Path(__file__).parent.parent

@dataclass
class VFSOfficeConfig:
    """VFS ofis konfigürasyonu"""
    name: str
    city: str
    country_code: str
    base_url: str
    appointment_path: str
    timezone: str

@dataclass
class TelegramConfig:
    """Telegram bot konfigürasyonu"""
    bot_token: str
    chat_id: str
    enabled: bool = True

@dataclass
class DatabaseConfig:
    """Veritabanı konfigürasyonu"""
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017/"
    mongodb_db: str = "vfs_appointments"
    
    # PostgreSQL
    postgres_url: str = "postgresql://manaliza:manaliza2024@localhost:5432/manaliza_test"
    postgres_db: str = "vfs_global"

@dataclass
class ScrapingConfig:
    """Web scraping konfigürasyonu"""
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    headless: bool = True
    implicit_wait: int = 10
    page_load_timeout: int = 30
    check_interval_min: int = 1  # Dakika
    check_interval_max: int = 3  # Dakika
    max_retries: int = 5
    retry_delay: int = 30  # Saniye

@dataclass
class SystemConfig:
    """Sistem genel konfigürasyonu"""
    debug: bool = False
    log_level: str = "INFO"
    screenshot_enabled: bool = True
    max_sessions: int = 2  # Aynı anda maksimum tarama session'u

class VFSGlobalSettings:
    """🎯 VFS Global Sistem Ayarları"""
    
    def __init__(self):
        self.load_environment()
        
    def load_environment(self):
        """Environment variables yükle"""
        from dotenv import load_dotenv
        
        env_file = BASE_DIR / "config" / "secrets.env"
        if env_file.exists():
            load_dotenv(env_file)
    
    # VFS Offices Configuration
    VFS_OFFICES = [
        VFSOfficeConfig(
            name="ankara",
            city="Ankara", 
            country_code="tr",
            base_url="https://visa.vfsglobal.com/tur/en/nld",
            appointment_path="/book-appointment",
            timezone="Europe/Istanbul"
        ),
        VFSOfficeConfig(
            name="istanbul",
            city="İstanbul",
            country_code="tr", 
            base_url="https://visa.vfsglobal.com/tur/en/nld",
            appointment_path="/book-appointment",
            timezone="Europe/Istanbul"
        )
    ]
    
    # Telegram Configuration
    TELEGRAM = TelegramConfig(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        enabled=os.getenv("TELEGRAM_ENABLED", "true").lower() == "true"
    )
    
    # Database Configuration  
    DATABASE = DatabaseConfig(
        mongodb_url=os.getenv("MONGODB_URL", "mongodb://localhost:27017/"),
        mongodb_db=os.getenv("MONGODB_DB", "vfs_appointments"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://manaliza:manaliza2024@localhost:5432/manaliza_test"),
        postgres_db=os.getenv("POSTGRES_DB", "vfs_global")
    )
    
    # Scraping Configuration
    SCRAPING = ScrapingConfig(
        headless=os.getenv("HEADLESS", "true").lower() == "true",
        check_interval_min=int(os.getenv("CHECK_INTERVAL_MIN", "1")),
        check_interval_max=int(os.getenv("CHECK_INTERVAL_MAX", "3")),
        max_retries=int(os.getenv("MAX_RETRIES", "5"))
    )
    
    # System Configuration
    SYSTEM = SystemConfig(
        debug=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        screenshot_enabled=os.getenv("SCREENSHOT_ENABLED", "true").lower() == "true"
    )
    
    # Directories
    LOGS_DIR = BASE_DIR / "logs"
    SCREENSHOTS_DIR = BASE_DIR / "screenshots"
    
    # VFS Global Specific Settings
    VFS_LOGIN_CREDENTIALS = {
        "email": os.getenv("VFS_EMAIL", ""),
        "password": os.getenv("VFS_PASSWORD", "")
    }
    
    # Anti-Detection Settings
    ANTI_DETECTION = {
        "random_delays": True,
        "mouse_movements": True,
        "scroll_simulation": True,
        "window_size_randomization": True,
        "user_agent_rotation": False,  # Static for consistency
        "proxy_rotation": False  # Disable for now
    }
    
    # Element Selectors (Dynamic - will be updated from GitHub research)
    VFS_SELECTORS = {
        "login_email": "input[type='email'], input[name='email'], #email",
        "login_password": "input[type='password'], input[name='password'], #password",
        "login_button": "button[type='submit'], .login-btn, #login",
        "calendar_container": ".calendar, .appointment-calendar, #appointment-dates",
        "available_dates": ".available, .date-available, .calendar-available",
        "time_slots": ".time-slot, .appointment-time, .available-time",
        "book_button": ".book-appointment, .confirm-appointment, button[data-action='book']",
        "error_message": ".error, .alert-error, .validation-error"
    }
    
    # GitHub Research Integration
    GITHUB_PROJECTS = {
        "vfs_bot": {
            "repo": "iamx-ariful-islam/VFS-Bot",
            "last_updated": "2026-02-17",
            "key_features": ["selenium_optimization", "chrome_settings", "session_management"]
        },
        "vfs_auto": {
            "repo": "barrriwa/vfsauto", 
            "last_updated": "2026-02-17",
            "key_features": ["anti_detection", "telegram_notifications", "fingerprint_switching"]
        }
    }
    
    @classmethod
    def ensure_directories(cls):
        """Gerekli dizinleri oluştur"""
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.SCREENSHOTS_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Konfigürasyon doğrulama"""
        errors = []
        
        if not cls.TELEGRAM.bot_token:
            errors.append("TELEGRAM_BOT_TOKEN is required")
            
        if not cls.TELEGRAM.chat_id:
            errors.append("TELEGRAM_CHAT_ID is required")
            
        if not cls.VFS_LOGIN_CREDENTIALS["email"]:
            errors.append("VFS_EMAIL is required")
            
        if not cls.VFS_LOGIN_CREDENTIALS["password"]:
            errors.append("VFS_PASSWORD is required")
            
        return errors

# Global settings instance
settings = VFSGlobalSettings()

# Dizinleri oluştur
settings.ensure_directories()

# Konfigürasyon doğrulama (sadece debug modda)
if os.getenv("DEBUG", "false").lower() == "true":
    config_errors = settings.validate_config()
    if config_errors:
        print("⚠️ Configuration errors:")
        for error in config_errors:
            print(f"  - {error}")
        print("\nLütfen config/secrets.env dosyasını kontrol edin!")