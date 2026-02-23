"""
🎯 VFS Global Randevu Sistemi - Main Controller
Enterprise orchestration engine that coordinates all components
"""

import asyncio
import signal
import sys
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

try:
    from core.authentication import MultiSessionManager, SessionManager
    from core.scraper import VFSAppointmentScraper, ScrapingResult
    from core.telegram_bot import telegram_notifier
    from core.retry_engine import retry_engine, with_retry
    from config.settings import settings
    from utils.logger import main_logger
except ImportError:
    from backend.core.authentication import MultiSessionManager, SessionManager
    from backend.core.scraper import VFSAppointmentScraper, ScrapingResult
    from backend.core.telegram_bot import telegram_notifier
    from backend.core.retry_engine import retry_engine, with_retry
    from backend.config.settings import settings
    from backend.utils.logger import main_logger

class VFSMainController:
    """🎯 VFS Global Ana Kontrolcü"""
    
    def __init__(self):
        self.session_manager = MultiSessionManager()
        self.scrapers: Dict[str, VFSAppointmentScraper] = {}
        
        # System state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.last_check_times: Dict[str, datetime] = {}
        self.total_checks = 0
        self.appointments_found_total = 0
        
        # Statistics
        self.city_stats: Dict[str, Dict] = {}
        
        # Graceful shutdown
        self._shutdown_event = asyncio.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Graceful shutdown signal handler"""
        main_logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self._shutdown())
    
    async def _shutdown(self):
        """Graceful shutdown"""
        self._shutdown_event.set()
    
    async def initialize(self) -> bool:
        """🚀 Sistem başlatma"""
        
        main_logger.info("🚀 VFS Global Randevu Sistemi başlatılıyor...")
        
        try:
            # Telegram bot test
            main_logger.info("📱 Telegram bot test ediliyor...")
            async with telegram_notifier as notifier:
                if await notifier.test_connection():
                    main_logger.success("Telegram bot bağlantısı başarılı")
                else:
                    main_logger.warning("Telegram bot test başarısız - bildirimler çalışmayabilir")
            
            # Session initialization
            main_logger.info("🔐 VFS session'ları başlatılıyor...")
            
            if await self.session_manager.initialize_sessions():
                main_logger.success(f"Session'lar başlatıldı: {len(self.session_manager.sessions)} ofis")
                
                # Scraper'ları oluştur
                for office_name, session in self.session_manager.sessions.items():
                    scraper = VFSAppointmentScraper(session)
                    self.scrapers[office_name] = scraper
                    
                    # Initialize stats
                    self.city_stats[office_name] = {
                        'total_checks': 0,
                        'successful_checks': 0,
                        'appointments_found': 0,
                        'last_check': None,
                        'last_success': None
                    }
                
                main_logger.success(f"Scraper'lar hazırlandı: {len(self.scrapers)} şehir")
            else:
                main_logger.error("Session başlatma başarısız!")
                return False
            
            # Startup notification
            await self._send_startup_notification()
            
            self.start_time = datetime.now()
            main_logger.success("🎯 VFS Global Randevu Sistemi başarıyla başlatıldı!")
            
            return True
            
        except Exception as e:
            main_logger.error(f"Sistem başlatma hatası: {e}")
            return False
    
    async def run_monitoring_loop(self):
        """🔄 Ana monitoring döngüsü"""
        
        if not await self.initialize():
            main_logger.error("Sistem başlatılamadı!")
            return
        
        self.is_running = True
        main_logger.info("🔄 Ana monitoring döngüsü başladı")
        
        try:
            while self.is_running and not self._shutdown_event.is_set():
                
                # Paralel appointment checks
                tasks = []
                for office_name, scraper in self.scrapers.items():
                    task = asyncio.create_task(
                        self._check_office_with_retry(office_name, scraper),
                        name=f"check_{office_name}"
                    )
                    tasks.append(task)
                
                # Execute all checks concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                await self._process_check_results(results)
                
                # Session keep-alive
                await self._maintain_sessions()
                
                # Calculate next check delay
                delay = await self._calculate_next_delay()
                
                main_logger.info(f"✅ Check cycle completed, waiting {delay:.1f}s for next cycle")
                
                # Wait with shutdown check
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=delay)
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Normal delay completed
                    
        except Exception as e:
            main_logger.error(f"Monitoring loop error: {e}")
        finally:
            await self._cleanup()
    
    @with_retry("office_appointment_check", max_attempts=3)
    async def _check_office_with_retry(self, office_name: str, scraper: VFSAppointmentScraper) -> ScrapingResult:
        """🔍 Ofis kontrolü retry ile"""
        
        main_logger.info(f"🔍 {office_name} randevu kontrolü başladı")
        
        try:
            # Scraping yap
            result = await scraper.check_appointments()
            
            # Update statistics
            self.city_stats[office_name]['total_checks'] += 1
            self.last_check_times[office_name] = datetime.now()
            
            if result.success:
                self.city_stats[office_name]['successful_checks'] += 1
                self.city_stats[office_name]['last_success'] = datetime.now()
                
                if result.appointments_found:
                    self.city_stats[office_name]['appointments_found'] += len(result.appointments_found)
            
            self.total_checks += 1
            
            return result
            
        except Exception as e:
            main_logger.error(f"Office check failed: {office_name} - {e}")
            raise
    
    async def _process_check_results(self, results: List):
        """📊 Check sonuçlarını işle"""
        
        appointments_found = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                office_name = list(self.scrapers.keys())[i]
                main_logger.error(f"Check failed for {office_name}: {result}")
                continue
            
            if not isinstance(result, ScrapingResult):
                continue
            
            if result.success and result.appointments_found:
                appointments_found.extend(result.appointments_found)
                
                # APPOINTMENT ALERT!
                for appointment in result.appointments_found:
                    main_logger.appointment_found(
                        city=appointment.office,
                        date=appointment.date,
                        time=appointment.time
                    )
                    
                    # Send Telegram alert
                    await self._send_appointment_alert(appointment, result.screenshot_path)
                
                self.appointments_found_total += len(result.appointments_found)
        
        # Log cycle summary
        successful_checks = sum(1 for r in results if isinstance(r, ScrapingResult) and r.success)
        total_offices = len(self.scrapers)
        
        main_logger.info(
            f"📊 Check cycle: {successful_checks}/{total_offices} successful, "
            f"{len(appointments_found)} appointments found"
        )
        
        # Periodic status report
        if self.total_checks % 20 == 0:  # Her 20 check'te bir
            await self._send_status_report()
    
    async def _send_appointment_alert(self, appointment, screenshot_path: Optional[Path]):
        """🚨 Randevu alarm gönder"""
        
        try:
            async with telegram_notifier as notifier:
                success = await notifier.send_appointment_alert(
                    city=appointment.office,
                    date=appointment.date,
                    time_slot=appointment.time,
                    screenshot_path=screenshot_path,
                    additional_info={
                        "Slot Type": appointment.slot_type,
                        "Detection Time": datetime.now().strftime("%H:%M:%S")
                    }
                )
                
                if success:
                    main_logger.success(f"Appointment alert sent for {appointment.office}")
                    
                    # PAUSE SYSTEM - User intervention needed
                    main_logger.alert("🛑 SYSTEM PAUSED - User intervention required for booking!")
                    self.is_running = False  # Stop monitoring
                else:
                    main_logger.error("Failed to send appointment alert")
                    
        except Exception as e:
            main_logger.error(f"Alert sending failed: {e}")
    
    async def _maintain_sessions(self):
        """🔄 Session maintenance"""
        
        try:
            await self.session_manager.keep_all_alive()
            main_logger.debug("Session maintenance completed")
        except Exception as e:
            main_logger.error(f"Session maintenance failed: {e}")
    
    async def _calculate_next_delay(self) -> float:
        """⏰ Sonraki check için delay hesapla"""
        
        # Random interval between min and max
        min_delay = settings.SCRAPING.check_interval_min * 60  # Convert to seconds
        max_delay = settings.SCRAPING.check_interval_max * 60
        
        base_delay = random.uniform(min_delay, max_delay)
        
        # Adaptive delay based on success rate
        overall_success_rate = self._calculate_overall_success_rate()
        
        if overall_success_rate < 0.5:  # Low success rate
            base_delay *= 1.5  # Increase delay
        elif overall_success_rate > 0.9:  # High success rate  
            base_delay *= 0.8  # Decrease delay
        
        return base_delay
    
    def _calculate_overall_success_rate(self) -> float:
        """📊 Overall success rate hesapla"""
        
        total_checks = sum(stats['total_checks'] for stats in self.city_stats.values())
        successful_checks = sum(stats['successful_checks'] for stats in self.city_stats.values())
        
        if total_checks == 0:
            return 1.0
        
        return successful_checks / total_checks
    
    async def _send_startup_notification(self):
        """🚀 Startup bildirimi"""
        
        try:
            cities = [office.city for office in settings.VFS_OFFICES]
            
            async with telegram_notifier as notifier:
                await notifier.send_system_alert(
                    alert_type="System Startup",
                    message="VFS Global Randevu Sistemi başarıyla başlatıldı",
                    severity="success",
                    details={
                        "Version": "1.0.0",
                        "Cities": ", ".join(cities),
                        "Check Interval": f"{settings.SCRAPING.check_interval_min}-{settings.SCRAPING.check_interval_max} min",
                        "Started": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }
                )
        except Exception as e:
            main_logger.error(f"Startup notification failed: {e}")
    
    async def _send_status_report(self):
        """📊 Status raporu gönder"""
        
        try:
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            
            async with telegram_notifier as notifier:
                await notifier.send_status_report(
                    status="Running",
                    cities_checked=list(self.city_stats.keys()),
                    last_check_times=self.last_check_times,
                    total_checks=self.total_checks,
                    uptime=uptime_str
                )
        except Exception as e:
            main_logger.error(f"Status report failed: {e}")
    
    async def _cleanup(self):
        """🧹 Cleanup resources"""
        
        main_logger.info("🧹 Sistem kapatılıyor...")
        
        try:
            # Close all sessions
            await self.session_manager.close_all()
            
            # Send shutdown notification
            async with telegram_notifier as notifier:
                await notifier.send_system_alert(
                    alert_type="System Shutdown",
                    message="VFS Global Randevu Sistemi kapatıldı",
                    severity="info",
                    details={
                        "Total Checks": self.total_checks,
                        "Total Appointments Found": self.appointments_found_total,
                        "Uptime": str(datetime.now() - self.start_time).split('.')[0] if self.start_time else "N/A"
                    }
                )
            
            main_logger.success("Sistem temizliği tamamlandı")
            
        except Exception as e:
            main_logger.error(f"Cleanup error: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """📈 Sistem istatistiklerini döndür"""
        
        uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        
        return {
            "system": {
                "is_running": self.is_running,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "uptime_seconds": uptime.total_seconds(),
                "total_checks": self.total_checks,
                "appointments_found_total": self.appointments_found_total
            },
            "cities": self.city_stats.copy(),
            "sessions": len(self.session_manager.sessions),
            "scrapers": len(self.scrapers),
            "retry_engine": retry_engine.get_statistics()
        }
    
    async def manual_check(self, city: Optional[str] = None) -> Dict[str, Any]:
        """🔍 Manuel check trigger"""
        
        if city and city in self.scrapers:
            # Single city check
            scraper = self.scrapers[city]
            result = await self._check_office_with_retry(city, scraper)
            return {"city": city, "result": result}
        else:
            # All cities check
            results = {}
            for office_name, scraper in self.scrapers.items():
                result = await self._check_office_with_retry(office_name, scraper)
                results[office_name] = result
            return results
    
    async def pause_monitoring(self):
        """⏸️ Monitoring'i duraklat"""
        self.is_running = False
        main_logger.info("Monitoring paused")
    
    async def resume_monitoring(self):
        """▶️ Monitoring'i devam ettir"""
        self.is_running = True
        main_logger.info("Monitoring resumed")

# Global controller instance
vfs_controller = VFSMainController()

# CLI Functions
async def start_monitoring():
    """🚀 Start VFS monitoring"""
    
    print("🚀 Starting VFS Global Randevu Sistemi...")
    print("Press Ctrl+C to stop gracefully")
    
    try:
        await vfs_controller.run_monitoring_loop()
    except KeyboardInterrupt:
        print("\n⏸️ Shutdown requested by user")
    except Exception as e:
        print(f"❌ System error: {e}")
    finally:
        print("👋 VFS Global Randevu Sistemi stopped")

async def test_system():
    """🧪 Test system components"""
    
    print("🧪 Testing VFS System Components...")
    
    # Initialize
    if await vfs_controller.initialize():
        print("✅ System initialization successful")
        
        # Manual check
        results = await vfs_controller.manual_check()
        print(f"📊 Manual check completed: {len(results)} cities")
        
        # Statistics
        stats = vfs_controller.get_system_stats()
        print(f"📈 System stats: {json.dumps(stats, indent=2, default=str)}")
        
        # Cleanup
        await vfs_controller._cleanup()
        print("✅ Test completed successfully")
    else:
        print("❌ System initialization failed")

def main():
    """Main entry point"""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            asyncio.run(test_system())
        elif sys.argv[1] == "start":
            asyncio.run(start_monitoring())
        else:
            print("Usage: python main_controller.py [start|test]")
    else:
        # Default: start monitoring
        asyncio.run(start_monitoring())

if __name__ == "__main__":
    main()