"""
🔍 VFS Global Randevu Sistemi - Advanced Scraper Engine
Intelligent appointment detection with anti-bot measures
"""

import asyncio
import random
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from PIL import Image

try:
    from core.authentication import SessionManager
    from core.telegram_bot import telegram_notifier
    from config.settings import settings
    from utils.logger import scraper_logger
except ImportError:
    from backend.core.authentication import SessionManager
    from backend.core.telegram_bot import telegram_notifier
    from backend.config.settings import settings
    from backend.utils.logger import scraper_logger

@dataclass
class AppointmentSlot:
    """📅 Randevu slot bilgisi"""
    date: str
    time: str
    available: bool
    office: str
    slot_type: str = "standard"  # standard, premium, urgent
    additional_info: Dict[str, Any] = None

@dataclass
class ScrapingResult:
    """📊 Scraping sonucu"""
    office: str
    success: bool
    appointments_found: List[AppointmentSlot]
    error_message: Optional[str] = None
    screenshot_path: Optional[Path] = None
    scraping_duration: float = 0.0
    timestamp: datetime = None

class VFSAppointmentScraper:
    """🎯 VFS Randevu Scraper Engine"""
    
    def __init__(self, session_manager: SessionManager):
        self.session = session_manager
        self.office = session_manager.office
        self.driver = session_manager.driver
        
        # Scraping statistics
        self.total_checks = 0
        self.successful_checks = 0
        self.appointments_found_count = 0
        self.last_check_time: Optional[datetime] = None
    
    async def check_appointments(self) -> ScrapingResult:
        """📅 Randevu kontrolü ana fonksiyonu"""
        
        start_time = datetime.now()
        self.total_checks += 1
        self.last_check_time = start_time
        
        scraper_logger.scraping_event("check_started", self.office.city)
        
        try:
            # Session kontrolü
            if not await self._ensure_session():
                return ScrapingResult(
                    office=self.office.city,
                    success=False,
                    appointments_found=[],
                    error_message="Session initialization failed",
                    timestamp=start_time
                )
            
            # Appointment sayfasına git
            if not await self._navigate_to_appointments():
                return ScrapingResult(
                    office=self.office.city,
                    success=False,
                    appointments_found=[],
                    error_message="Failed to navigate to appointments page",
                    timestamp=start_time
                )
            
            # Calendar yüklemesini bekle
            await self._wait_for_calendar_load()
            
            # Available appointments ara
            appointments = await self._scan_available_appointments()
            
            # Screenshot al
            screenshot_path = None
            if settings.SYSTEM.screenshot_enabled:
                screenshot_path = await self._take_screenshot("appointment_check")
            
            # Duration hesapla
            duration = (datetime.now() - start_time).total_seconds()
            
            # Success update
            self.successful_checks += 1
            if appointments:
                self.appointments_found_count += len(appointments)
            
            scraper_logger.scraping_event(
                f"check_completed: {len(appointments)} slots found",
                self.office.city,
                duration=duration
            )
            
            return ScrapingResult(
                office=self.office.city,
                success=True,
                appointments_found=appointments,
                screenshot_path=screenshot_path,
                scraping_duration=duration,
                timestamp=start_time
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            
            scraper_logger.error(
                f"Scraping failed for {self.office.city}: {e}",
                duration=duration
            )
            
            return ScrapingResult(
                office=self.office.city,
                success=False,
                appointments_found=[],
                error_message=str(e),
                scraping_duration=duration,
                timestamp=start_time
            )
    
    async def _ensure_session(self) -> bool:
        """Session geçerlilik kontrolü"""
        
        try:
            if not self.session.is_logged_in:
                scraper_logger.warning("Session not logged in, attempting login")
                
                email = settings.VFS_LOGIN_CREDENTIALS["email"]
                password = settings.VFS_LOGIN_CREDENTIALS["password"]
                
                return await self.session.login(email, password)
            
            # Session timeout kontrolü
            if self.session.last_activity:
                time_since_activity = datetime.now() - self.session.last_activity
                if time_since_activity > timedelta(minutes=30):  # 30 dakika timeout
                    scraper_logger.warning("Session timeout, re-authenticating")
                    
                    email = settings.VFS_LOGIN_CREDENTIALS["email"]
                    password = settings.VFS_LOGIN_CREDENTIALS["password"]
                    
                    return await self.session.login(email, password)
            
            return True
            
        except Exception as e:
            scraper_logger.error(f"Session check failed: {e}")
            return False
    
    async def _navigate_to_appointments(self) -> bool:
        """Appointment sayfasına git"""
        
        try:
            appointment_url = f"{self.office.base_url}{self.office.appointment_path}"
            
            # Navigate with retry
            if not await self.session._navigate_with_retry(appointment_url):
                return False
            
            # Appointment page load kontrolü
            await self._human_like_delay(2, 4)
            
            # Page loaded kontrolü - specific to VFS
            page_indicators = [
                ".appointment-calendar",
                "#appointment-dates", 
                ".calendar-container",
                ".date-picker"
            ]
            
            for indicator in page_indicators:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, indicator))
                    )
                    scraper_logger.debug(f"Found appointment page indicator: {indicator}")
                    return True
                except TimeoutException:
                    continue
            
            scraper_logger.warning("Appointment page indicators not found, proceeding anyway")
            return True
            
        except Exception as e:
            scraper_logger.error(f"Navigation to appointments failed: {e}")
            return False
    
    async def _wait_for_calendar_load(self):
        """Calendar yüklemesini bekle"""
        
        try:
            # JavaScript calendar loading bekle
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script(
                    "return document.readyState === 'complete' && "
                    "(document.querySelector('.calendar') !== null || "
                    "document.querySelector('[data-calendar]') !== null)"
                )
            )
            
            # Extra delay for AJAX calls
            await self._human_like_delay(2, 3)
            
            scraper_logger.debug(f"Calendar loaded for {self.office.city}")
            
        except TimeoutException:
            scraper_logger.warning("Calendar load timeout, proceeding with scan")
        except Exception as e:
            scraper_logger.error(f"Calendar wait failed: {e}")
    
    async def _scan_available_appointments(self) -> List[AppointmentSlot]:
        """Available appointments tara"""
        
        appointments = []
        
        try:
            # Multiple scanning strategies
            appointments.extend(await self._scan_calendar_grid())
            appointments.extend(await self._scan_date_list())
            appointments.extend(await self._scan_dropdown_dates())
            
            # Duplicate temizleme
            appointments = self._deduplicate_appointments(appointments)
            
            # Future dates only
            appointments = [apt for apt in appointments if self._is_future_date(apt.date)]
            
            scraper_logger.info(
                f"Scan completed for {self.office.city}: {len(appointments)} appointments found"
            )
            
            return appointments
            
        except Exception as e:
            scraper_logger.error(f"Appointment scan failed: {e}")
            return []
    
    async def _scan_calendar_grid(self) -> List[AppointmentSlot]:
        """Calendar grid formatını tara"""
        
        appointments = []
        
        try:
            # Calendar grid selectors
            calendar_selectors = [
                ".calendar-grid .available-date",
                ".appointment-calendar .date-available",
                ".datepicker-days .available",
                "[data-available='true']",
                ".calendar-date:not(.disabled):not(.unavailable)"
            ]
            
            for selector in calendar_selectors:
                try:
                    available_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in available_elements:
                        # Date extraction
                        date_text = await self._extract_date_from_element(element)
                        if not date_text:
                            continue
                        
                        # Time slots check
                        time_slots = await self._find_time_slots_for_date(element, date_text)
                        
                        if time_slots:
                            for time_slot in time_slots:
                                appointments.append(AppointmentSlot(
                                    date=date_text,
                                    time=time_slot,
                                    available=True,
                                    office=self.office.city
                                ))
                        else:
                            # No specific time, assume full day available
                            appointments.append(AppointmentSlot(
                                date=date_text,
                                time="available",
                                available=True,
                                office=self.office.city
                            ))
                    
                    if appointments:
                        scraper_logger.debug(f"Found {len(appointments)} appointments via calendar grid")
                        break  # Success with this selector
                        
                except Exception as e:
                    scraper_logger.debug(f"Calendar grid selector '{selector}' failed: {e}")
                    continue
            
            return appointments
            
        except Exception as e:
            scraper_logger.error(f"Calendar grid scan failed: {e}")
            return []
    
    async def _scan_date_list(self) -> List[AppointmentSlot]:
        """Date list formatını tara"""
        
        appointments = []
        
        try:
            # List-based date selectors
            list_selectors = [
                ".appointment-list .available-slot",
                ".date-list .available-date",  
                ".appointment-options .selectable",
                "ul.dates li:not(.disabled)",
                ".available-appointments li"
            ]
            
            for selector in list_selectors:
                try:
                    available_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in available_elements:
                        # Extract full appointment info
                        appointment_info = await self._extract_appointment_info(element)
                        
                        if appointment_info:
                            appointments.append(AppointmentSlot(**appointment_info))
                    
                    if appointments:
                        scraper_logger.debug(f"Found {len(appointments)} appointments via date list")
                        break
                        
                except Exception as e:
                    scraper_logger.debug(f"Date list selector '{selector}' failed: {e}")
                    continue
            
            return appointments
            
        except Exception as e:
            scraper_logger.error(f"Date list scan failed: {e}")
            return []
    
    async def _scan_dropdown_dates(self) -> List[AppointmentSlot]:
        """Dropdown date selectors tara"""
        
        appointments = []
        
        try:
            # Dropdown selectors
            dropdown_selectors = [
                "select[name='appointment_date'] option:not([disabled])",
                ".date-dropdown option[value]:not([disabled])",
                "select.appointment-dates option[data-available='true']"
            ]
            
            for selector in dropdown_selectors:
                try:
                    options = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for option in options:
                        if option.get_attribute("value") and option.text.strip():
                            date_text = option.text.strip()
                            
                            appointments.append(AppointmentSlot(
                                date=date_text,
                                time="dropdown_available",
                                available=True,
                                office=self.office.city,
                                additional_info={"source": "dropdown", "value": option.get_attribute("value")}
                            ))
                    
                    if appointments:
                        scraper_logger.debug(f"Found {len(appointments)} appointments via dropdown")
                        break
                        
                except Exception as e:
                    scraper_logger.debug(f"Dropdown selector '{selector}' failed: {e}")
                    continue
            
            return appointments
            
        except Exception as e:
            scraper_logger.error(f"Dropdown scan failed: {e}")
            return []
    
    async def _extract_date_from_element(self, element) -> Optional[str]:
        """Element'ten date bilgisi çıkar"""
        
        try:
            # Attribute-based extraction
            date_attrs = ["data-date", "data-day", "data-value", "title", "aria-label"]
            
            for attr in date_attrs:
                date_value = element.get_attribute(attr)
                if date_value and self._looks_like_date(date_value):
                    return self._normalize_date_string(date_value)
            
            # Text-based extraction
            element_text = element.text.strip()
            if element_text and self._looks_like_date(element_text):
                return self._normalize_date_string(element_text)
            
            # Parent element check
            parent = element.find_element(By.XPATH, "..")
            parent_text = parent.text.strip()
            if parent_text and self._looks_like_date(parent_text):
                return self._normalize_date_string(parent_text)
            
            return None
            
        except Exception as e:
            scraper_logger.debug(f"Date extraction failed: {e}")
            return None
    
    async def _find_time_slots_for_date(self, date_element, date_text: str) -> List[str]:
        """Belirli bir tarih için time slot'ları bul"""
        
        try:
            time_slots = []
            
            # Time slot selectors near date element
            time_selectors = [
                ".time-slot",
                ".appointment-time", 
                ".available-time",
                "[data-time]",
                ".time-option"
            ]
            
            # Parent container'da time slot ara
            parent_container = date_element.find_element(By.XPATH, "../..")
            
            for selector in time_selectors:
                try:
                    time_elements = parent_container.find_elements(By.CSS_SELECTOR, selector)
                    
                    for time_elem in time_elements:
                        time_text = time_elem.text.strip()
                        time_value = time_elem.get_attribute("data-time")
                        
                        time_slot = time_value or time_text
                        if time_slot and self._looks_like_time(time_slot):
                            time_slots.append(self._normalize_time_string(time_slot))
                    
                    if time_slots:
                        break
                        
                except NoSuchElementException:
                    continue
            
            return time_slots
            
        except Exception as e:
            scraper_logger.debug(f"Time slot extraction failed: {e}")
            return []
    
    async def _extract_appointment_info(self, element) -> Optional[Dict[str, Any]]:
        """Element'ten tam appointment bilgisi çıkar"""
        
        try:
            info = {
                "office": self.office.city,
                "available": True
            }
            
            # Text content analysis
            full_text = element.text.strip()
            
            # Date extraction
            date_match = re.search(r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})', full_text)
            if date_match:
                info["date"] = self._normalize_date_string(date_match.group(1))
            else:
                # Alternative date patterns
                date_patterns = [
                    r'(\d{1,2}\s+\w+\s+\d{4})',  # "15 May 2026"
                    r'(\w+\s+\d{1,2},?\s+\d{4})'  # "May 15, 2026"
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, full_text, re.IGNORECASE)
                    if match:
                        info["date"] = self._normalize_date_string(match.group(1))
                        break
            
            # Time extraction
            time_match = re.search(r'(\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?)', full_text)
            if time_match:
                info["time"] = self._normalize_time_string(time_match.group(1))
            else:
                info["time"] = "available"
            
            # Appointment type detection
            if "premium" in full_text.lower():
                info["slot_type"] = "premium"
            elif "urgent" in full_text.lower():
                info["slot_type"] = "urgent"
            else:
                info["slot_type"] = "standard"
            
            # Additional info
            info["additional_info"] = {"raw_text": full_text}
            
            # Validate required fields
            if "date" not in info:
                return None
            
            return info
            
        except Exception as e:
            scraper_logger.debug(f"Appointment info extraction failed: {e}")
            return None
    
    def _looks_like_date(self, text: str) -> bool:
        """String date benzeri mi kontrol et"""
        
        date_patterns = [
            r'\d{1,2}[/.-]\d{1,2}[/.-]\d{4}',
            r'\d{4}[/.-]\d{1,2}[/.-]\d{1,2}',
            r'\d{1,2}\s+\w+\s+\d{4}',
            r'\w+\s+\d{1,2},?\s+\d{4}'
        ]
        
        return any(re.search(pattern, text) for pattern in date_patterns)
    
    def _looks_like_time(self, text: str) -> bool:
        """String time benzeri mi kontrol et"""
        
        time_patterns = [
            r'\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?',
            r'\d{1,2}[:.]\d{2}',
            r'(?:morning|afternoon|evening)'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in time_patterns)
    
    def _normalize_date_string(self, date_str: str) -> str:
        """Date string normalize et"""
        
        # Basic normalization - can be improved
        date_str = date_str.strip()
        
        # Replace separators with standard format
        date_str = re.sub(r'[/.-]', '/', date_str)
        
        return date_str
    
    def _normalize_time_string(self, time_str: str) -> str:
        """Time string normalize et"""
        
        time_str = time_str.strip()
        
        # Standard format: HH:MM
        time_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
        if time_match:
            hours, minutes = time_match.groups()
            return f"{hours.zfill(2)}:{minutes}"
        
        return time_str
    
    def _is_future_date(self, date_str: str) -> bool:
        """Date gelecekte mi kontrol et"""
        
        try:
            # Simple future check - can be improved with proper date parsing
            today = datetime.now()
            
            # Basic patterns
            if re.search(r'\d{1,2}/\d{1,2}/\d{4}', date_str):
                # MM/DD/YYYY or DD/MM/YYYY
                parts = date_str.split('/')
                if len(parts) == 3:
                    year = int(parts[2])
                    month = int(parts[0])  # Assuming MM/DD/YYYY
                    day = int(parts[1])
                    
                    try:
                        check_date = datetime(year, month, day)
                        return check_date >= today
                    except:
                        # Try DD/MM/YYYY
                        try:
                            check_date = datetime(year, int(parts[1]), int(parts[0]))
                            return check_date >= today
                        except:
                            return True  # Assume future if parsing fails
            
            # Default to True for complex date formats
            return True
            
        except Exception as e:
            scraper_logger.debug(f"Future date check failed: {e}")
            return True
    
    def _deduplicate_appointments(self, appointments: List[AppointmentSlot]) -> List[AppointmentSlot]:
        """Duplicate appointment'ları temizle"""
        
        seen = set()
        unique_appointments = []
        
        for appointment in appointments:
            # Create unique key
            key = f"{appointment.date}_{appointment.time}_{appointment.office}"
            
            if key not in seen:
                seen.add(key)
                unique_appointments.append(appointment)
        
        return unique_appointments
    
    async def _take_screenshot(self, filename_prefix: str) -> Optional[Path]:
        """Screenshot al"""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{self.office.name}_{timestamp}.png"
            screenshot_path = settings.SCREENSHOTS_DIR / filename
            
            # Full page screenshot
            self.driver.save_screenshot(str(screenshot_path))
            
            # Optimize image size
            try:
                with Image.open(screenshot_path) as img:
                    # Resize if too large
                    if img.width > 1920:
                        ratio = 1920 / img.width
                        new_size = (1920, int(img.height * ratio))
                        img.resize(new_size, Image.LANCZOS).save(screenshot_path, optimize=True, quality=85)
            except Exception as e:
                scraper_logger.debug(f"Screenshot optimization failed: {e}")
            
            scraper_logger.debug(f"Screenshot saved: {filename}")
            return screenshot_path
            
        except Exception as e:
            scraper_logger.error(f"Screenshot failed: {e}")
            return None
    
    async def _human_like_delay(self, min_seconds: float, max_seconds: float):
        """Human-like delay"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Scraping istatistiklerini döndür"""
        
        return {
            "office": self.office.city,
            "total_checks": self.total_checks,
            "successful_checks": self.successful_checks,
            "appointments_found_count": self.appointments_found_count,
            "success_rate": self.successful_checks / self.total_checks if self.total_checks > 0 else 0,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None
        }

# Test function
async def test_scraper():
    """Scraper sistemini test et"""
    
    print("🔍 Testing Scraper Engine...")
    
    from .authentication import SessionManager
    
    # Create session for Ankara
    ankara_office = settings.VFS_OFFICES[0]
    session = SessionManager(ankara_office)
    
    # Initialize driver (required for scraper)
    if await session.initialize_driver():
        scraper = VFSAppointmentScraper(session)
        
        # Test appointment check (will fail without real VFS but tests structure)
        result = await scraper.check_appointments()
        
        print(f"✅ Scraper test completed for {result.office}")
        print(f"   Success: {result.success}")
        print(f"   Appointments found: {len(result.appointments_found)}")
        print(f"   Duration: {result.scraping_duration:.2f}s")
        
        # Statistics
        stats = scraper.get_statistics()
        print(f"   Statistics: {stats}")
        
        await session.close()
    else:
        print("❌ Session initialization failed")

if __name__ == "__main__":
    asyncio.run(test_scraper())