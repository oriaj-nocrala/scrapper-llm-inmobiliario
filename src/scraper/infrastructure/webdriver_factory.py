"""
Professional WebDriver Factory with optimized configurations.
"""
import logging
import random
from typing import Any, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions

logger = logging.getLogger(__name__)


class WebDriverFactory:
    """Factory for creating optimized WebDriver instances."""
    
    # Realistic user agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
    ]
    
    # Common screen resolutions
    SCREEN_SIZES = [
        "1920,1080", "1366,768", "1536,864", "1440,900", "1280,720"
    ]
    
    @classmethod
    def create_chrome_driver(
        cls,
        headless: bool = True,
        stealth_mode: bool = True,
        performance_optimized: bool = True,
        debug_mode: bool = False,
        custom_options: Optional[Dict[str, Any]] = None
    ) -> webdriver.Chrome:
        """Create an optimized Chrome WebDriver instance.
        
        Args:
            headless: Run in headless mode
            stealth_mode: Apply anti-detection measures
            performance_optimized: Apply performance optimizations
            custom_options: Additional custom options
            
        Returns:
            Configured Chrome WebDriver
        """
        options = ChromeOptions()
        
        # Basic configuration
        if headless:
            options.add_argument("--headless=new")  # Use new headless mode
        
        # Essential stability options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        
        # Performance optimizations (disabled in debug mode)
        if performance_optimized and not debug_mode:
            options.add_argument("--disable-images")
            options.add_argument("--disable-javascript")  # We'll enable if needed
            options.add_argument("--disable-css")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-sync")
            options.add_argument("--metrics-recording-only")
            options.add_argument("--no-first-run")
        
        # Debug mode configuration
        if debug_mode:
            # Force visible mode for debugging
            headless = False
            # Enable all web technologies needed for AssetPlan
            options.add_argument("--enable-javascript")
            options.add_argument("--load-images=yes")
            # Keep session stable
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            # Keep browser open on failure for debugging
            options.add_experimental_option("detach", True)
            
        # Anti-detection measures
        if stealth_mode:
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Random user agent
            user_agent = random.choice(cls.USER_AGENTS)
            options.add_argument(f"--user-agent={user_agent}")
            
            # Random screen size
            screen_size = random.choice(cls.SCREEN_SIZES)
            options.add_argument(f"--window-size={screen_size}")
            
        # Memory optimizations
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")
        
        # Custom options
        if custom_options:
            for key, value in custom_options.items():
                if isinstance(value, bool) and value:
                    options.add_argument(f"--{key}")
                elif value:
                    options.add_argument(f"--{key}={value}")
        
        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
            
            # Additional stealth measures
            if stealth_mode:
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
            # Set timeouts (más generosos para debug y scraping)
            driver.implicitly_wait(15)  # Aumentado de 10 a 15
            driver.set_page_load_timeout(60)  # Aumentado de 30 a 60
            driver.set_script_timeout(45)  # Aumentado de 30 a 45
            
            logger.info(f"Chrome WebDriver created successfully (headless={headless}, stealth={stealth_mode})")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to create Chrome WebDriver: {e}")
            raise
    
    @classmethod
    def create_firefox_driver(
        cls,
        headless: bool = True,
        stealth_mode: bool = True,
        performance_optimized: bool = True
    ) -> webdriver.Firefox:
        """Create an optimized Firefox WebDriver instance.
        
        Args:
            headless: Run in headless mode
            stealth_mode: Apply anti-detection measures
            performance_optimized: Apply performance optimizations
            
        Returns:
            Configured Firefox WebDriver
        """
        options = FirefoxOptions()
        
        if headless:
            options.add_argument("--headless")
        
        # Performance optimizations
        if performance_optimized:
            # Disable images
            options.set_preference("permissions.default.image", 2)
            # Disable CSS
            options.set_preference("permissions.default.stylesheet", 2)
            # Disable JavaScript (if needed)
            options.set_preference("javascript.enabled", False)
            # Disable Flash
            options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", False)
            
        # Anti-detection measures
        if stealth_mode:
            # Random user agent
            user_agent = random.choice(cls.USER_AGENTS)
            options.set_preference("general.useragent.override", user_agent)
            
            # Disable automation indicators
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            
        try:
            driver = webdriver.Firefox(options=options)
            driver.implicitly_wait(10)
            driver.set_page_load_timeout(30)
            driver.set_script_timeout(30)
            
            logger.info(f"Firefox WebDriver created successfully (headless={headless}, stealth={stealth_mode})")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to create Firefox WebDriver: {e}")
            raise
    
    @classmethod
    def get_random_user_agent(cls) -> str:
        """Get a random user agent string."""
        return random.choice(cls.USER_AGENTS)
    
    @classmethod
    def get_random_screen_size(cls) -> str:
        """Get a random screen size."""
        return random.choice(cls.SCREEN_SIZES)


class DriverManager:
    """Manager for WebDriver lifecycle and health monitoring."""
    
    def __init__(self, driver_type: str = "chrome", **kwargs):
        """Initialize the driver manager.
        
        Args:
            driver_type: Type of driver to create ("chrome" or "firefox")
            **kwargs: Additional options for driver creation
        """
        self.driver_type = driver_type
        self.driver_options = kwargs
        self.driver: Optional[webdriver.Chrome | webdriver.Firefox] = None
        self.requests_count = 0
        self.max_requests = kwargs.get('max_requests', 100)  # Restart driver after N requests
        
    def get_driver(self) -> webdriver.Chrome | webdriver.Firefox:
        """Get or create a WebDriver instance."""
        if self.driver is None or self._should_restart_driver():
            self._restart_driver()
        return self.driver
    
    def _should_restart_driver(self) -> bool:
        """Check if driver should be restarted."""
        if self.requests_count >= self.max_requests:
            logger.info(f"Restarting driver after {self.requests_count} requests")
            return True
        
        # Check if driver is still alive
        try:
            self.driver.current_url
            return False
        except:
            logger.warning("Driver appears to be dead, restarting")
            return True
    
    def _restart_driver(self) -> None:
        """Restart the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        if self.driver_type == "chrome":
            self.driver = WebDriverFactory.create_chrome_driver(**self.driver_options)
        elif self.driver_type == "firefox":
            self.driver = WebDriverFactory.create_firefox_driver(**self.driver_options)
        else:
            raise ValueError(f"Unsupported driver type: {self.driver_type}")
        
        self.requests_count = 0
    
    def increment_request_count(self) -> None:
        """Increment the request counter."""
        self.requests_count += 1
    
    def close(self) -> None:
        """Close the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    