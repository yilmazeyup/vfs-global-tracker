#!/usr/bin/env python3
"""
🎯 VFS Global Randevu Sistemi - Demo Test
Gerçek giriş yapmadan sistem testi
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.core.telegram_bot import telegram_notifier
from backend.config.settings import settings
from datetime import datetime

def demo_test():
    print("🎯 VFS GLOBAL RANDEVU SİSTEMİ - DEMO TEST")
    print("=" * 60)
    
    # 1. Konfigürasyon kontrolü
    print("\n📋 KONFİGÜRASYON KONTROLÜ:")
    print(f"   • VFS Email: {settings.VFS_EMAIL}")
    print(f"   • Telegram Bot Token: {'✅ Ayarlandı' if settings.TELEGRAM_BOT_TOKEN else '❌ Eksik'}")
    print(f"   • Telegram Chat ID: {settings.TELEGRAM_CHAT_ID}")
    print(f"   • Tarama Aralığı: {settings.CHECK_INTERVAL} saniye")
    print(f"   • Ofisler: {', '.join(settings.VFS_OFFICES.keys())}")
    
    # 2. Telegram test mesajı
    print("\n📱 TELEGRAM TEST MESAJI GÖNDERİLİYOR...")
    try:
        test_message = f"""
🎯 VFS Global Randevu Sistemi - Test

✅ Sistem başarıyla kuruldu!
⏰ Zaman: {datetime.now().strftime('%d.%m.%Y %H:%M')}

📍 Desteklenen Ofisler:
• Ankara
• İstanbul

🔍 Özellikler:
• Anti-detection bypass
• Otomatik retry
• Screenshot capture
• 11 ülke desteği

🚀 Sistem hazır!
        """
        
        # Demo modda Telegram yerine konsola yazdır
        print("\n📬 TELEGRAM MESAJI (Demo Mode):")
        print(test_message)
        
        # Randevu bulundu simülasyonu
        print("\n🎬 RANDEVU BULUNDU SİMÜLASYONU:")
        alarm_message = """
🚨 VFS HOLLANDA RANDEVU ALARMI! 🚨

📍 Şehir: İstanbul
🗓️ Tarih: 15 Mayıs 2026
⏰ Saat: 10:30
📋 Tip: Standard Appointment

🔗 Hemen Giriş Yap: https://visa.vfsglobal.com

⚡ Bot otomatik döngüyü durdurdu
✅ Randevunu onayla ve botu yeniden başlat
        """
        print(alarm_message)
        
    except Exception as e:
        print(f"❌ Telegram test hatası: {e}")
    
    print("\n✅ DEMO TEST TAMAMLANDI!")
    print("🚀 Gerçek tarama için: python main.py --country netherlands --office ankara")

if __name__ == "__main__":
    demo_test()