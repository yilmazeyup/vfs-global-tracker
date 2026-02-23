"""
📱 VFS Global Randevu Sistemi - Telegram Bot
Advanced notification system with rich formatting and media support
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import base64
import io

try:
    from config.settings import settings
    from utils.logger import telegram_logger
except ImportError:
    from backend.config.settings import settings
    from backend.utils.logger import telegram_logger

class TelegramNotifier:
    """🤖 Gelişmiş Telegram Bildirim Sistemi"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM.bot_token
        self.chat_id = settings.TELEGRAM.chat_id
        self.enabled = settings.TELEGRAM.enabled
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
    
    async def start(self):
        """HTTP session başlat"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            telegram_logger.info("Telegram session started")
    
    async def stop(self):
        """HTTP session kapat"""
        if self.session:
            await self.session.close()
            self.session = None
            telegram_logger.info("Telegram session stopped")
    
    async def send_appointment_alert(
        self,
        city: str,
        date: str,
        time_slot: Optional[str] = None,
        screenshot_path: Optional[Path] = None,
        additional_info: Dict[str, Any] = None
    ) -> bool:
        """🚨 Randevu bulundu alarm mesajı"""
        
        if not self.enabled:
            telegram_logger.warning("Telegram notifications disabled")
            return False
        
        # Mesaj formatı
        message = self._format_appointment_message(city, date, time_slot, additional_info)
        
        # Screenshot varsa fotoğrafla birlikte gönder
        if screenshot_path and screenshot_path.exists():
            success = await self._send_photo_with_caption(screenshot_path, message)
        else:
            success = await self._send_message(message)
        
        if success:
            telegram_logger.appointment_alert_sent(city=city, date=date, time_slot=time_slot)
        
        return success
    
    async def send_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "info",
        details: Dict[str, Any] = None
    ) -> bool:
        """⚠️ Sistem uyarı mesajları"""
        
        if not self.enabled:
            return False
        
        formatted_message = self._format_system_message(alert_type, message, severity, details)
        success = await self._send_message(formatted_message)
        
        if success:
            telegram_logger.telegram_event(f"system_alert_sent: {alert_type}", success=True)
        
        return success
    
    async def send_status_report(
        self,
        status: str,
        cities_checked: List[str],
        last_check_times: Dict[str, datetime],
        total_checks: int,
        uptime: str
    ) -> bool:
        """📊 Durum raporu mesajı"""
        
        if not self.enabled:
            return False
        
        message = self._format_status_report(status, cities_checked, last_check_times, total_checks, uptime)
        success = await self._send_message(message)
        
        return success
    
    async def send_error_report(
        self,
        error_type: str,
        error_message: str,
        city: Optional[str] = None,
        retry_count: int = 0,
        screenshot_path: Optional[Path] = None
    ) -> bool:
        """🔥 Hata raporu mesajı"""
        
        if not self.enabled:
            return False
        
        message = self._format_error_message(error_type, error_message, city, retry_count)
        
        # Screenshot varsa ekle
        if screenshot_path and screenshot_path.exists():
            success = await self._send_photo_with_caption(screenshot_path, message)
        else:
            success = await self._send_message(message)
        
        return success
    
    def _format_appointment_message(
        self,
        city: str,
        date: str,
        time_slot: Optional[str],
        additional_info: Dict[str, Any] = None
    ) -> str:
        """Randevu alarm mesajı formatla"""
        
        # Base message - Eyüp'ün istediği format
        message = f"""🚨 VFS HOLLANDA RANDEVU ALARMI! 🚨

📍 Şehir: {city}
🗓️ Tarih: {date}"""
        
        if time_slot:
            message += f"\n🕐 Saat: {time_slot}"
        
        message += f"""
🔗 Hemen Giriş Yap: https://visa.vfsglobal.com/tur/en/nld/book-appointment

⚠️ Not: Bot şu an otonom döngüyü durdurdu. 
✅ Lütfen sisteme girip randevunu onayla.
🔄 İşlemin bitince botu yeniden başlatabilirsin.

⏰ Tespit Zamanı: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"""

        # Ek bilgiler varsa ekle
        if additional_info:
            message += "\n\n📋 Ek Bilgiler:"
            for key, value in additional_info.items():
                message += f"\n• {key}: {value}"
        
        message += "\n\n⚡ Manaliza VFS Randevu Sistemi"
        
        return message
    
    def _format_system_message(
        self,
        alert_type: str,
        message: str,
        severity: str,
        details: Dict[str, Any] = None
    ) -> str:
        """Sistem mesajı formatla"""
        
        # Severity emojileri
        severity_emojis = {
            "info": "ℹ️",
            "warning": "⚠️", 
            "error": "🔥",
            "critical": "🚨",
            "success": "✅"
        }
        
        emoji = severity_emojis.get(severity, "📢")
        
        formatted = f"""{emoji} VFS SİSTEM UYARISI

🏷️ Tip: {alert_type}
📝 Mesaj: {message}
⏰ Zaman: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"""

        if details:
            formatted += "\n\n📋 Detaylar:"
            for key, value in details.items():
                formatted += f"\n• {key}: {value}"
        
        return formatted
    
    def _format_status_report(
        self,
        status: str,
        cities_checked: List[str], 
        last_check_times: Dict[str, datetime],
        total_checks: int,
        uptime: str
    ) -> str:
        """Durum raporu formatla"""
        
        message = f"""📊 VFS SİSTEM DURUM RAPORU

🟢 Durum: {status}
🏙️ Kontrol Edilen Şehirler: {', '.join(cities_checked)}
📊 Toplam Kontrol: {total_checks}
⏱️ Çalışma Süresi: {uptime}

📅 Son Kontrol Zamanları:"""
        
        for city, check_time in last_check_times.items():
            message += f"\n• {city}: {check_time.strftime('%d/%m/%Y %H:%M:%S')}"
        
        message += f"\n\n⏰ Rapor Zamanı: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        message += "\n⚡ Manaliza VFS Monitor"
        
        return message
    
    def _format_error_message(
        self,
        error_type: str,
        error_message: str,
        city: Optional[str],
        retry_count: int
    ) -> str:
        """Hata mesajı formatla"""
        
        message = f"""🔥 VFS SİSTEM HATASI

🚫 Hata Tipi: {error_type}
📝 Hata Mesajı: {error_message}"""

        if city:
            message += f"\n📍 Şehir: {city}"
        
        if retry_count > 0:
            message += f"\n🔄 Deneme Sayısı: {retry_count}"
        
        message += f"\n⏰ Hata Zamanı: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        message += "\n\n🤖 Sistem otomatik düzelmeye çalışacak..."
        
        return message
    
    async def _send_message(self, text: str) -> bool:
        """Telegram mesaj gönder"""
        
        if not self.session:
            await self.start()
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    telegram_logger.telegram_event("message_sent", success=True)
                    return True
                else:
                    error_text = await response.text()
                    telegram_logger.telegram_event(
                        f"message_failed: {response.status}",
                        success=False,
                        error=error_text
                    )
                    return False
                    
        except Exception as e:
            telegram_logger.telegram_event(f"message_exception: {str(e)}", success=False)
            return False
    
    async def _send_photo_with_caption(self, photo_path: Path, caption: str) -> bool:
        """Fotoğraflı mesaj gönder"""
        
        if not self.session:
            await self.start()
        
        url = f"{self.base_url}/sendPhoto"
        
        try:
            data = aiohttp.FormData()
            data.add_field('chat_id', self.chat_id)
            data.add_field('caption', caption)
            data.add_field('parse_mode', 'HTML')
            
            # Fotoğrafı ekle
            with open(photo_path, 'rb') as photo:
                data.add_field('photo', photo, filename=photo_path.name)
                
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        telegram_logger.telegram_event("photo_sent", success=True)
                        return True
                    else:
                        error_text = await response.text()
                        telegram_logger.telegram_event(
                            f"photo_failed: {response.status}",
                            success=False,
                            error=error_text
                        )
                        return False
                        
        except Exception as e:
            telegram_logger.telegram_event(f"photo_exception: {str(e)}", success=False)
            return False
    
    async def test_connection(self) -> bool:
        """Telegram bot bağlantısını test et"""
        
        if not self.enabled:
            telegram_logger.warning("Telegram disabled, skipping test")
            return False
        
        test_message = f"""🧪 VFS Telegram Bot Test

✅ Bot bağlantısı çalışıyor!
⏰ Test Zamanı: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

⚡ Manaliza VFS Randevu Sistemi"""
        
        success = await self._send_message(test_message)
        
        if success:
            telegram_logger.success("Telegram bot test successful")
        else:
            telegram_logger.error("Telegram bot test failed")
        
        return success

# Global Telegram notifier instance
telegram_notifier = TelegramNotifier()

# Utility functions
async def send_appointment_alert(city: str, date: str, **kwargs) -> bool:
    """Randevu alarm gönder (utility function)"""
    async with telegram_notifier as notifier:
        return await notifier.send_appointment_alert(city, date, **kwargs)

async def send_system_alert(alert_type: str, message: str, **kwargs) -> bool:
    """Sistem uyarı gönder (utility function)"""
    async with telegram_notifier as notifier:
        return await notifier.send_system_alert(alert_type, message, **kwargs)

async def test_telegram_bot() -> bool:
    """Telegram bot test (utility function)"""
    async with telegram_notifier as notifier:
        return await notifier.test_connection()

# Test function
async def main():
    """Test Telegram bot functionality"""
    
    print("🧪 Testing Telegram Bot...")
    
    async with telegram_notifier as notifier:
        # Connection test
        await notifier.test_connection()
        
        # Appointment alert test
        await notifier.send_appointment_alert(
            city="İstanbul",
            date="15 Mayıs 2026",
            time_slot="14:30",
            additional_info={
                "Randevu Tipi": "Schengen Vize",
                "Süre": "30 dakika"
            }
        )
        
        # System alert test
        await notifier.send_system_alert(
            alert_type="System Startup",
            message="VFS Randevu sistemi başlatıldı",
            severity="success",
            details={
                "Version": "1.0.0",
                "Cities": "Ankara, İstanbul"
            }
        )
    
    print("✅ Telegram bot test completed")

if __name__ == "__main__":
    asyncio.run(main())