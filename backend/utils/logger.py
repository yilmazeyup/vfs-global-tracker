"""
📝 VFS Global Randevu Sistemi - Logging System
Enterprise-grade logging with structured output
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json

try:
    from config.settings import settings
except ImportError:
    from backend.config.settings import settings

class VFSLogger:
    """🎯 Özelleştirilmiş VFS Logger"""
    
    def __init__(self, name: str = "vfs_global"):
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Logger kurulumu"""
        
        # Logger oluştur
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, settings.SYSTEM.log_level))
        
        # Handler'lar temizle (duplicate log önleme)
        logger.handlers.clear()
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File Handler
        log_file = settings.LOGS_DIR / f"vfs_global_{datetime.now().strftime('%Y_%m_%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Handler'ları ekle
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def info(self, message: str, **kwargs):
        """Info level log"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Error level log"""  
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning level log"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Debug level log"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """Success log (info level with ✅ prefix)"""
        self._log_with_context(logging.INFO, f"✅ {message}", **kwargs)
    
    def alert(self, message: str, **kwargs):
        """Alert log (error level with 🚨 prefix)"""
        self._log_with_context(logging.ERROR, f"🚨 {message}", **kwargs)
    
    def appointment_found(self, city: str, date: str, **kwargs):
        """Randevu bulundu özel log"""
        self._log_with_context(
            logging.CRITICAL, 
            f"🎯 RANDEVU BULUNDU! {city} - {date}",
            event_type="appointment_found",
            city=city,
            date=date,
            **kwargs
        )
    
    def session_event(self, event: str, **kwargs):
        """Session events için özel log"""
        self._log_with_context(
            logging.INFO,
            f"🔐 Session: {event}",
            event_type="session",
            session_event=event,
            **kwargs
        )
    
    def scraping_event(self, event: str, city: str = None, **kwargs):
        """Scraping events için özel log"""
        city_info = f" [{city}]" if city else ""
        self._log_with_context(
            logging.INFO,
            f"🔍 Scraping{city_info}: {event}",
            event_type="scraping", 
            city=city,
            scraping_event=event,
            **kwargs
        )
    
    def retry_event(self, attempt: int, max_attempts: int, error: str = None, **kwargs):
        """Retry events için özel log"""
        self._log_with_context(
            logging.WARNING,
            f"🔄 Retry {attempt}/{max_attempts}: {error or 'Unknown error'}",
            event_type="retry",
            attempt=attempt,
            max_attempts=max_attempts,
            error=error,
            **kwargs
        )
    
    def telegram_event(self, event: str, success: bool = True, **kwargs):
        """Telegram events için özel log"""
        emoji = "📱" if success else "❌"
        self._log_with_context(
            logging.INFO if success else logging.ERROR,
            f"{emoji} Telegram: {event}",
            event_type="telegram",
            success=success,
            **kwargs
        )
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Context ile log yaz"""
        
        # Extra context oluştur
        extra_context = {
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        # JSON formatında extra bilgi (debug mode'da)
        if settings.SYSTEM.debug and kwargs:
            context_str = json.dumps(extra_context, ensure_ascii=False, indent=None)
            message = f"{message} | Context: {context_str}"
        
        self.logger.log(level, message, extra=extra_context)
    
    def save_structured_log(self, event_type: str, data: dict):
        """Structured JSON log kaydet"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "logger": self.name,
            "data": data
        }
        
        # JSON log dosyası
        json_log_file = settings.LOGS_DIR / f"structured_logs_{datetime.now().strftime('%Y_%m_%d')}.jsonl"
        
        with open(json_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

# Global logger instances
main_logger = VFSLogger("vfs_main")
scraper_logger = VFSLogger("vfs_scraper")
telegram_logger = VFSLogger("vfs_telegram")
session_logger = VFSLogger("vfs_session")

def get_logger(name: str = "vfs_global") -> VFSLogger:
    """Logger instance al"""
    return VFSLogger(name)

# Test function
def test_logging():
    """Logging sistemini test et"""
    logger = get_logger("test")
    
    logger.info("Test log message")
    logger.success("Test success message")
    logger.warning("Test warning message")
    logger.error("Test error message")
    logger.appointment_found("İstanbul", "2026-05-15", time_slot="14:30")
    logger.session_event("login_success", user="test@example.com")
    logger.scraping_event("checking_calendar", city="Ankara")
    logger.retry_event(2, 5, "Connection timeout")
    logger.telegram_event("message_sent", success=True, chat_id="123456")
    
    # Structured log test
    logger.save_structured_log("appointment_check", {
        "city": "İstanbul",
        "available_dates": ["2026-05-15", "2026-05-20"],
        "check_duration": 3.5
    })
    
    print("✅ Logging system test completed")

if __name__ == "__main__":
    test_logging()