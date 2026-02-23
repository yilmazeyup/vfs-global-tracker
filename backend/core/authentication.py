"""
🔐 VFS Global Randevu Sistemi - Authentication & Session Management
Advanced session handling with anti-detection features
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import pickle

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc

try:
    from config.settings import settings
    from utils.logger import session_logger
except ImportError:
    from backend.config.settings import settings
    from backend.utils.logger import session_logger

class SessionManager:
    """🎯 Gelişmiş VFS Session Yöneticisi"""
    
    def __init__(self, office_config):
        self.office = office_config
        self.driver: Optional[webdriver.Chrome] = None
        self.session_file = settings.BASE_DIR / "sessions" / f"session_{office_config.name}.pkl"
        self.cookies_file = settings.BASE_DIR / "sessions" / f"cookies_{office_config.name}.json"
        
        # Session durumu
        self.is_logged_in = False
        self.login_time: Optional[datetime] = None
        self.last_activity: Optional[datetime] = None
        
        # Anti-detection ayarları
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # Dizinleri oluştur
        self.session_file.parent.mkdir(exist_ok=True)
    
    async def initialize_driver(self) -> bool:
        """Anti-detection Chrome driver başlat"""
        
        try:
            # Chrome options
            options = uc.ChromeOptions()
            
            # Headless mode
            if settings.SCRAPING.headless:
                options.add_argument("--headless=new")
            
            # Anti-detection ayarları
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")  # Hız için
            options.add_argument("--disable-javascript")  # Gerekirse kapatılabilir
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Window size randomization
            if settings.ANTI_DETECTION["window_size_randomization"]:
                width = random.randint(1200, 1920)
                height = random.randint(800, 1080)
                options.add_argument(f"--window-size={width},{height}")
            
            # User agent
            user_agent = random.choice(self.user_agents)
            options.add_argument(f"--user-agent={user_agent}")
            
            # Diğer optimizasyonlar
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Chrome prefs
            prefs = {
                "profile.default_content_setting_values": {
                    "images": 2,  # Block images
                    "plugins": 2,  # Block plugins
                    "popups": 2,  # Block popups
                    "geolocation": 2,  # Block location sharing
                    "notifications": 2,  # Block notifications  
                    "media_stream": 2,  # Block camera/microphone
                }
            }
            options.add_experimental_option("prefs", prefs)
            
            # Driver oluştur
            self.driver = uc.Chrome(options=options, version_main=120)
            
            # Anti-detection script çalıştır
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'tr'],
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)
            
            # Implicit wait
            self.driver.implicitly_wait(settings.SCRAPING.implicit_wait)
            
            session_logger.success(f"Driver initialized for {self.office.city}")
            return True
            
        except Exception as e:
            session_logger.error(f"Driver initialization failed: {e}")
            return False
    
    async def login(self, email: str, password: str) -> bool:
        """VFS Global'e giriş yap"""
        
        if not self.driver:
            if not await self.initialize_driver():
                return False
        
        try:
            session_logger.info(f"Starting login process for {self.office.city}")
            
            # Ana sayfaya git
            login_url = f"{self.office.base_url}/login"
            await self._navigate_with_retry(login_url)
            
            # Cookies yükle (varsa)
            await self._load_cookies()
            
            # Zaten giriş yapmış mıyız kontrol et
            if await self._check_login_status():
                session_logger.success("Already logged in")
                return True
            
            # Login form alanlarını bul ve doldur
            await self._human_like_delay(2, 4)
            
            # Email field
            if not await self._fill_field(settings.VFS_SELECTORS["login_email"], email):
                session_logger.error("Could not find email field")
                return False
            
            await self._human_like_delay(1, 2)
            
            # Password field
            if not await self._fill_field(settings.VFS_SELECTORS["login_password"], password):
                session_logger.error("Could not find password field")
                return False
            
            await self._human_like_delay(1, 2)
            
            # Login button click
            if not await self._click_element(settings.VFS_SELECTORS["login_button"]):
                session_logger.error("Could not find login button")
                return False
            
            # Login sonucunu bekle
            await self._human_like_delay(3, 6)
            
            # Login başarılı mı kontrol et
            if await self._check_login_status():
                self.is_logged_in = True
                self.login_time = datetime.now()
                self.last_activity = datetime.now()
                
                # Session kaydet
                await self._save_session()
                await self._save_cookies()
                
                session_logger.success(f"Login successful for {self.office.city}")
                return True
            else:
                session_logger.error("Login failed - invalid credentials or blocked")
                return False
                
        except Exception as e:
            session_logger.error(f"Login exception: {e}")
            return False
    
    async def keep_session_alive(self) -> bool:
        """Session canlı tutma - anti-timeout"""
        
        if not self.driver or not self.is_logged_in:
            return False
        
        try:
            # Human-like aktivite simüle et
            if settings.ANTI_DETECTION["mouse_movements"]:
                await self._simulate_mouse_activity()
            
            if settings.ANTI_DETECTION["scroll_simulation"]:
                await self._simulate_scroll_activity()
            
            # Sayfa yenileme (çok nadir)
            if random.random() < 0.1:  # %10 ihtimal
                await self.driver.refresh()
                await self._human_like_delay(2, 4)
            
            self.last_activity = datetime.now()
            session_logger.debug(f"Session activity simulated for {self.office.city}")
            
            return True
            
        except Exception as e:
            session_logger.error(f"Keep alive failed: {e}")
            return False
    
    async def _navigate_with_retry(self, url: str, max_retries: int = 3) -> bool:
        """Sayfa navigasyonu retry ile"""
        
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                
                # Page load bekle
                WebDriverWait(self.driver, settings.SCRAPING.page_load_timeout).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                session_logger.debug(f"Navigated to {url}")
                return True
                
            except Exception as e:
                session_logger.warning(f"Navigation attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    await self._human_like_delay(2, 5)
                
        return False
    
    async def _fill_field(self, selector: str, value: str) -> bool:
        """Form alanını human-like şekilde doldur"""
        
        try:
            # Multiple selector support
            selectors = selector.split(", ")
            element = None
            
            for sel in selectors:
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not element:
                return False
            
            # Field temizle
            element.clear()
            await self._human_like_delay(0.5, 1)
            
            # Human-like typing
            for char in value:
                element.send_keys(char)
                await self._human_like_delay(0.05, 0.15)  # Realistic typing speed
            
            return True
            
        except Exception as e:
            session_logger.error(f"Fill field failed: {e}")
            return False
    
    async def _click_element(self, selector: str) -> bool:
        """Element tıklama human-like"""
        
        try:
            # Multiple selector support
            selectors = selector.split(", ")
            element = None
            
            for sel in selectors:
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not element:
                return False
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            await self._human_like_delay(0.5, 1)
            
            # Mouse movement + click
            if settings.ANTI_DETECTION["mouse_movements"]:
                actions = ActionChains(self.driver)
                actions.move_to_element(element)
                actions.pause(random.uniform(0.1, 0.3))
                actions.click()
                actions.perform()
            else:
                element.click()
            
            return True
            
        except Exception as e:
            session_logger.error(f"Click element failed: {e}")
            return False
    
    async def _check_login_status(self) -> bool:
        """Login durumu kontrol et"""
        
        try:
            # URL-based check
            current_url = self.driver.current_url
            if "dashboard" in current_url or "appointments" in current_url:
                return True
            
            # Element-based check
            try:
                # Logout button veya dashboard elementi var mı?
                logout_selectors = [
                    "a[href*='logout']",
                    ".logout-btn",
                    ".user-menu", 
                    ".dashboard"
                ]
                
                for selector in logout_selectors:
                    if self.driver.find_elements(By.CSS_SELECTOR, selector):
                        return True
            except:
                pass
            
            return False
            
        except Exception as e:
            session_logger.error(f"Login status check failed: {e}")
            return False
    
    async def _simulate_mouse_activity(self):
        """Mouse aktivitesi simüle et"""
        
        try:
            actions = ActionChains(self.driver)
            
            # Random mouse movements
            for _ in range(random.randint(2, 5)):
                x_offset = random.randint(-100, 100)
                y_offset = random.randint(-100, 100)
                actions.move_by_offset(x_offset, y_offset)
                actions.pause(random.uniform(0.5, 2))
            
            actions.perform()
            
        except Exception as e:
            session_logger.debug(f"Mouse simulation failed: {e}")
    
    async def _simulate_scroll_activity(self):
        """Scroll aktivitesi simüle et"""
        
        try:
            # Random scroll
            scroll_amount = random.randint(-300, 300)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            
        except Exception as e:
            session_logger.debug(f"Scroll simulation failed: {e}")
    
    async def _human_like_delay(self, min_seconds: float, max_seconds: float):
        """Human-like delay"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def _save_session(self):
        """Session bilgilerini kaydet"""
        
        try:
            session_data = {
                "office": self.office.name,
                "is_logged_in": self.is_logged_in,
                "login_time": self.login_time.isoformat() if self.login_time else None,
                "last_activity": self.last_activity.isoformat() if self.last_activity else None
            }
            
            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)
                
            session_logger.debug(f"Session saved for {self.office.city}")
            
        except Exception as e:
            session_logger.error(f"Save session failed: {e}")
    
    async def _save_cookies(self):
        """Browser cookies kaydet"""
        
        try:
            if self.driver:
                cookies = self.driver.get_cookies()
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f)
                
                session_logger.debug(f"Cookies saved for {self.office.city}")
                
        except Exception as e:
            session_logger.error(f"Save cookies failed: {e}")
    
    async def _load_cookies(self):
        """Browser cookies yükle"""
        
        try:
            if self.cookies_file.exists() and self.driver:
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass  # Invalid cookies skip
                
                session_logger.debug(f"Cookies loaded for {self.office.city}")
                
        except Exception as e:
            session_logger.error(f"Load cookies failed: {e}")
    
    async def close(self):
        """Session kapat ve temizle"""
        
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            self.is_logged_in = False
            session_logger.info(f"Session closed for {self.office.city}")
            
        except Exception as e:
            session_logger.error(f"Session close failed: {e}")
    
    def __del__(self):
        """Destructor - cleanup"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

class MultiSessionManager:
    """🎯 Çoklu Session Yöneticisi"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionManager] = {}
    
    async def initialize_sessions(self) -> bool:
        """Tüm ofisler için session başlat"""
        
        success_count = 0
        
        for office in settings.VFS_OFFICES:
            session_manager = SessionManager(office)
            
            # Login credentials
            email = settings.VFS_LOGIN_CREDENTIALS["email"]
            password = settings.VFS_LOGIN_CREDENTIALS["password"]
            
            if await session_manager.login(email, password):
                self.sessions[office.name] = session_manager
                success_count += 1
            else:
                session_logger.error(f"Failed to initialize session for {office.city}")
        
        session_logger.info(f"Initialized {success_count}/{len(settings.VFS_OFFICES)} sessions")
        return success_count > 0
    
    async def keep_all_alive(self):
        """Tüm session'ları canlı tut"""
        
        for name, session in self.sessions.items():
            await session.keep_session_alive()
    
    async def close_all(self):
        """Tüm session'ları kapat"""
        
        for session in self.sessions.values():
            await session.close()
        
        self.sessions.clear()
        session_logger.info("All sessions closed")

# Global session manager
multi_session_manager = MultiSessionManager()

# Test function
async def test_authentication():
    """Authentication sistemini test et"""
    
    print("🔐 Testing Authentication System...")
    
    # Single session test
    ankara_office = settings.VFS_OFFICES[0]  # Ankara
    session = SessionManager(ankara_office)
    
    # Driver init test
    if await session.initialize_driver():
        print("✅ Driver initialization successful")
    else:
        print("❌ Driver initialization failed")
        return
    
    # Login test (test credentials)
    email = "test@example.com"  
    password = "test_password"
    
    # Note: This will fail with real VFS but tests the flow
    await session.login(email, password)
    
    # Keep alive test
    await session.keep_session_alive()
    
    # Close
    await session.close()
    
    print("✅ Authentication system test completed")

if __name__ == "__main__":
    asyncio.run(test_authentication())