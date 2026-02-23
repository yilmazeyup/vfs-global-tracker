#!/usr/bin/env python3
"""
🎯 VFS Global Randevu Sistemi - Main Entry Point
Enterprise VFS appointment monitoring system

⚡ Manaliza Enterprise Solutions
📅 Developed: February 2026
🎯 Purpose: Automated VFS Netherlands visa appointment detection
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.main_controller import vfs_controller
from backend.config.settings import settings
from backend.utils.logger import main_logger

def print_banner():
    """🎨 System banner"""
    
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🎯 VFS GLOBAL RANDEVU TAKİP SİSTEMİ                      ║
║                                                              ║
║    ⚡ Manaliza Enterprise Solutions                          ║
║    📍 Hollanda Vize Randevuları - Otomatik Takip           ║
║                                                              ║
║    🏢 Ofisler: Ankara & İstanbul                            ║
║    📱 Telegram: Anında bildirim                             ║
║    🤖 Anti-Detection: GitHub research based                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    
    print(banner)

def print_help():
    """📖 Help information"""
    
    help_text = """
🎯 VFS GLOBAL RANDEVU SİSTEMİ - KULLANIM KILAVUZU

📋 KOMUTLAR:
  python main.py start              Monitoring sistemini başlat
  python main.py test               Sistem bileşenlerini test et
  python main.py check [city]       Manuel randevu kontrolü
  python main.py status             Sistem durum bilgisi
  python main.py config             Konfigürasyon kontrolü
  python main.py help               Bu yardım mesajını göster

🔧 KONFİGÜRASYON:
  1. config/secrets.env.example dosyasını config/secrets.env olarak kopyala
  2. Telegram bot token ve chat ID'sini ekle
  3. VFS Global giriş bilgilerini ekle
  4. İsteğe bağlı diğer ayarları yapılandır

📱 TELEGRAM BOT KURULUMU:
  1. @BotFather ile yeni bot oluştur
  2. Bot token'ı al
  3. Bot ile sohbet başlat
  4. Chat ID'sini öğren
  5. secrets.env dosyasına ekle

⚠️  ÖNEMLİ NOTLAR:
  - Bu sistem eğitim amaçlıdır
  - VFS Global ToS'a uygun kullanın
  - Aşırı istek göndermeyin
  - Yasal sorumluluğu kabul edin

📚 DAHA FAZLA BİLGİ:
  README.md dosyasını okuyun
  GitHub: https://github.com/manaliza/vfs-global-system
  
⚡ Manaliza Enterprise Solutions - 2026
"""
    
    print(help_text)

def check_configuration() -> bool:
    """✅ Configuration check"""
    
    print("🔧 Konfigürasyon kontrol ediliyor...")
    
    config_errors = settings.validate_config()
    
    if config_errors:
        print("\n❌ Konfigürasyon hataları bulundu:")
        for error in config_errors:
            print(f"  • {error}")
        print("\n📝 config/secrets.env dosyasını kontrol edin!")
        print("💡 config/secrets.env.example dosyasından kopyalayabilirsiniz")
        return False
    else:
        print("✅ Konfigürasyon başarıyla doğrulandı")
        return True

async def start_monitoring():
    """🚀 Start monitoring"""
    
    print_banner()
    
    if not check_configuration():
        return
    
    print("\n🚀 VFS Global Randevu Sistemi başlatılıyor...")
    print("📱 Telegram bildirimleri aktif")
    print("🔍 Monitoring başlıyor: Ankara & İstanbul")
    print("\n⏸️  Durdurmak için: Ctrl+C")
    print("═" * 60)
    
    try:
        await vfs_controller.run_monitoring_loop()
    except KeyboardInterrupt:
        print("\n\n⏸️ Kullanıcı tarafından durduruldu")
        main_logger.info("System stopped by user")
    except Exception as e:
        print(f"\n❌ Sistem hatası: {e}")
        main_logger.error(f"System error: {e}")
    finally:
        print("\n👋 VFS Global Randevu Sistemi kapatıldı")

async def test_system():
    """🧪 Test system"""
    
    print_banner()
    print("\n🧪 Sistem bileşenleri test ediliyor...\n")
    
    if not check_configuration():
        return
    
    # Component tests
    try:
        # Initialize system
        print("1️⃣ Sistem başlatması test ediliyor...")
        if await vfs_controller.initialize():
            print("   ✅ Sistem başarıyla başlatıldı")
            
            # Manual check test
            print("\n2️⃣ Manuel kontrol test ediliyor...")
            results = await vfs_controller.manual_check()
            print(f"   ✅ {len(results)} şehir kontrol edildi")
            
            # Statistics
            print("\n3️⃣ İstatistikler alınıyor...")
            stats = vfs_controller.get_system_stats()
            print(f"   ✅ Sistem istatistikleri: {stats['system']['total_checks']} kontrol")
            
            # Cleanup
            print("\n4️⃣ Sistem temizliği...")
            await vfs_controller._cleanup()
            print("   ✅ Temizlik tamamlandı")
            
            print("\n🎉 TÜM TESTLER BAŞARILI!")
            
        else:
            print("   ❌ Sistem başlatılamadı")
            
    except Exception as e:
        print(f"❌ Test hatası: {e}")

async def manual_check(city: str = None):
    """🔍 Manual check"""
    
    print_banner()
    
    if not check_configuration():
        return
    
    target = city or "tüm şehirler"
    print(f"\n🔍 Manuel randevu kontrolü: {target}")
    print("═" * 50)
    
    try:
        # Initialize  
        if await vfs_controller.initialize():
            # Run check
            results = await vfs_controller.manual_check(city)
            
            print(f"\n📊 KONTROL SONUÇLARI:")
            
            if isinstance(results, dict) and "result" in results:
                # Single city result
                result = results["result"]
                print(f"\n🏢 {results['city']}:")
                print(f"   Başarılı: {'✅' if result.success else '❌'}")
                if result.appointments_found:
                    print(f"   🎯 {len(result.appointments_found)} randevu bulundu!")
                    for apt in result.appointments_found:
                        print(f"      📅 {apt.date} - {apt.time}")
                else:
                    print("   📭 Randevu bulunamadı")
            else:
                # Multiple cities
                for office, result in results.items():
                    print(f"\n🏢 {office}:")
                    print(f"   Başarılı: {'✅' if result.success else '❌'}")
                    if result.appointments_found:
                        print(f"   🎯 {len(result.appointments_found)} randevu bulundu!")
                        for apt in result.appointments_found:
                            print(f"      📅 {apt.date} - {apt.time}")
                    else:
                        print("   📭 Randevu bulunamadı")
            
            # Cleanup
            await vfs_controller._cleanup()
            
        else:
            print("❌ Sistem başlatılamadı")
            
    except Exception as e:
        print(f"❌ Manuel kontrol hatası: {e}")

def show_status():
    """📊 Show system status"""
    
    print_banner()
    print("\n📊 SİSTEM DURUM BİLGİSİ")
    print("═" * 50)
    
    # Configuration status
    print("\n🔧 KONFİGÜRASYON:")
    config_errors = settings.validate_config()
    if config_errors:
        print("   ❌ Hatalı konfigürasyon")
        for error in config_errors:
            print(f"      • {error}")
    else:
        print("   ✅ Konfigürasyon geçerli")
    
    # Settings overview
    print(f"\n⚙️  AYARLAR:")
    print(f"   📍 Ofisler: {len(settings.VFS_OFFICES)} ({', '.join([o.city for o in settings.VFS_OFFICES])})")
    print(f"   ⏱️  Kontrol Aralığı: {settings.SCRAPING.check_interval_min}-{settings.SCRAPING.check_interval_max} dk")
    print(f"   🔄 Max Retry: {settings.SCRAPING.max_retries}")
    print(f"   📱 Telegram: {'✅' if settings.TELEGRAM.enabled else '❌'}")
    print(f"   📸 Screenshot: {'✅' if settings.SYSTEM.screenshot_enabled else '❌'}")
    
    # Directories
    print(f"\n📁 DİZİNLER:")
    print(f"   📝 Logs: {settings.LOGS_DIR}")
    print(f"   📸 Screenshots: {settings.SCREENSHOTS_DIR}")
    print(f"   ✅ Dizinler {'mevcut' if settings.LOGS_DIR.exists() else 'eksik'}")
    
    print(f"\n⚡ Hazırlık durumu: {'🟢 HAZIR' if not config_errors else '🔴 HAZIR DEĞİL'}")

def main():
    """🎯 Main entry point"""
    
    if len(sys.argv) < 2:
        command = "help"
    else:
        command = sys.argv[1].lower()
    
    if command == "start":
        asyncio.run(start_monitoring())
    elif command == "test":
        asyncio.run(test_system())
    elif command == "check":
        city = sys.argv[2] if len(sys.argv) > 2 else None
        asyncio.run(manual_check(city))
    elif command == "status":
        show_status()
    elif command == "config":
        check_configuration()
    elif command == "help":
        print_help()
    else:
        print(f"❌ Bilinmeyen komut: {command}")
        print("💡 Yardım için: python main.py help")

if __name__ == "__main__":
    main()