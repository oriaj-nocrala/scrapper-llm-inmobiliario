"""
Navigation Manager para AssetPlan Extractor.
Maneja toda la navegación, waits y detección de cambios de página.
"""
import logging
import time
from typing import Optional

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class NavigationManager:
    """Gestor de navegación para el extractor."""
    
    def __init__(self, driver: WebDriver, debug_manager=None):
        """Initialize navigation manager.
        
        Args:
            driver: WebDriver instance
            debug_manager: Optional debug manager for visual feedback
        """
        self.driver = driver
        self.debug_manager = debug_manager
        self.wait = WebDriverWait(driver, 15)
        self.fast_wait = WebDriverWait(driver, 2)
        self.last_url = None
        
    def configure_behavior_mode(self, human_like: bool = False, behavior_mode: str = "extreme"):
        """Configure navigation behavior.
        
        Args:
            human_like: Whether to use human-like behavior
            behavior_mode: Speed mode (extreme, fast, normal, slow)
        """
        timeout_map = {
            "extreme": 3,
            "fast": 5,
            "normal": 10,
            "slow": 15,
            "very_slow": 20
        }
        
        timeout = timeout_map.get(behavior_mode, 3)
        self.wait = WebDriverWait(self.driver, timeout)
        self.fast_wait = WebDriverWait(self.driver, min(2, timeout))
        
        logger.info(f"Navigation configured: {behavior_mode} mode, timeout: {timeout}s")
    
    def smart_delay(self, min_delay: float, max_delay: float):
        """Smart delay between operations.
        
        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        import random
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def wait_for_complete_navigation(self, initial_url: str, timeout: float = 8.0) -> bool:
        """Wait for complete page navigation.
        
        Args:
            initial_url: Initial URL before navigation
            timeout: Maximum time to wait
            
        Returns:
            True if navigation completed successfully
        """
        try:
            # Wait for URL change
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.current_url != initial_url
            )
            
            # Wait for page to be ready
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            return True
            
        except TimeoutException:
            logger.warning(f"Navigation timeout after {timeout}s")
            return False
    
    def smart_back_to_modal(self):
        """Navigate back to modal intelligently."""
        try:
            current_url = self.driver.current_url
            
            if self.debug_manager:
                self.debug_manager.show_debug_info("Navigating back to modal...", 2.0)
            
            self.driver.back()
            
            # Wait for navigation to complete
            self.wait_for_complete_navigation(current_url, 5.0)
            
            # Additional wait for modal to be ready
            time.sleep(1.0)
            
            if self.debug_manager:
                self.debug_manager.show_debug_info("Back navigation completed", 1.0)
                
        except Exception as e:
            logger.error(f"Error navigating back: {e}")
            raise
    
    def wait_for_element_quick(self, selector: str, timeout: float = 1.0) -> Optional[WebElement]:
        """Wait for element with quick timeout.
        
        Args:
            selector: CSS selector
            timeout: Timeout in seconds
            
        Returns:
            Element if found, None otherwise
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except TimeoutException:
            return None
    
    def wait_for_navigation_with_debug(self, expected_url_pattern: str = None, 
                                     timeout: float = 10.0, context: str = "") -> bool:
        """Wait for navigation with debug feedback.
        
        Args:
            expected_url_pattern: Pattern to match in URL
            timeout: Maximum time to wait
            context: Context description for debugging
            
        Returns:
            True if navigation successful
        """
        initial_url = self.driver.current_url
        
        if self.debug_manager:
            self.debug_manager.show_debug_info(f"Waiting for navigation: {context}", 2.0)
        
        try:
            # Wait for URL change or pattern match
            if expected_url_pattern:
                WebDriverWait(self.driver, timeout).until(
                    lambda driver: expected_url_pattern in driver.current_url
                )
            else:
                WebDriverWait(self.driver, timeout).until(
                    lambda driver: driver.current_url != initial_url
                )
            
            # Wait for page ready
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            if self.debug_manager:
                self.debug_manager.show_debug_info("Navigation successful", 1.0)
            
            return True
            
        except TimeoutException:
            if self.debug_manager:
                self.debug_manager.show_debug_info(f"Navigation timeout: {context}", 3.0)
            
            logger.warning(f"Navigation timeout: {context}")
            return False
    
    def find_element_robust(self, selectors: list, parent=None) -> Optional[WebElement]:
        """Find element using multiple selectors robustly.
        
        Args:
            selectors: List of CSS selectors to try
            parent: Parent element to search within
            
        Returns:
            First element found, or None
        """
        search_context = parent or self.driver
        
        for selector in selectors:
            try:
                element = search_context.find_element(By.CSS_SELECTOR, selector)
                
                if self.debug_manager:
                    self.debug_manager.highlight_element(element, "extract", 0.5)
                
                return element
                
            except NoSuchElementException:
                continue
                
        return None
    
    def find_elements_robust(self, selectors: list, parent=None) -> list:
        """Find elements using multiple selectors robustly.
        
        Args:
            selectors: List of CSS selectors to try
            parent: Parent element to search within
            
        Returns:
            List of elements found
        """
        search_context = parent or self.driver
        
        for selector in selectors:
            try:
                elements = search_context.find_elements(By.CSS_SELECTOR, selector)
                
                if elements and self.debug_manager:
                    for element in elements[:3]:  # Highlight first 3
                        self.debug_manager.highlight_element(element, "extract", 0.2)
                
                return elements
                
            except NoSuchElementException:
                continue
                
        return []
    
    def navigate_to_search_page(self):
        """Navigate to the search page."""
        try:
            if self.debug_manager:
                self.debug_manager.show_debug_info("Navigating to search page...", 2.0)
            
            self.driver.get(self.search_url)
            
            # Wait for page to load
            self.wait_for_complete_navigation("", 10.0)
            
            if self.debug_manager:
                self.debug_manager.show_debug_info("Search page loaded", 1.0)
                
        except Exception as e:
            logger.error(f"Error navigating to search page: {e}")
            raise
    
    def navigate_back_to_buildings_list(self) -> bool:
        """Navigate back to buildings list.
        
        Returns:
            True if navigation successful
        """
        try:
            current_url = self.driver.current_url
            
            if self.debug_manager:
                self.debug_manager.show_debug_info("Navigating back to buildings list...", 2.0)
            
            self.driver.back()
            
            # Wait for navigation
            success = self.wait_for_complete_navigation(current_url, 8.0)
            
            if success and self.debug_manager:
                self.debug_manager.show_debug_info("Back to buildings list", 1.0)
            
            return success
            
        except Exception as e:
            logger.error(f"Error navigating back to buildings list: {e}")
            return False