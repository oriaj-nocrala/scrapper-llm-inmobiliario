"""
Navigation Manager especializado para AssetPlan Extractor.
Maneja toda la navegación, waits y detección de cambios de página.
"""
import logging
import time
import random
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class AssetPlanNavigationManager:
    """Navegación y interacción con elementos especializada."""
    
    def __init__(self, driver: WebDriver, debug_manager=None, **kwargs):
        """Initialize navigation manager.
        
        Args:
            driver: WebDriver instance
            debug_manager: Optional debug manager for visual feedback
            **kwargs: Additional configuration
        """
        self.driver = driver
        self.debug_manager = debug_manager
        self.wait = WebDriverWait(driver, 15)
        self.fast_wait = WebDriverWait(driver, 2)
        
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def smart_delay(self, min_delay: float, max_delay: float):
        """Smart delay between operations."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def wait_for_complete_navigation(self, initial_url: str, timeout: float = 8.0) -> bool:
        """Wait for complete page navigation."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.current_url != initial_url
            )
            
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            return True
            
        except TimeoutException:
            logger.warning(f"Navigation timeout after {timeout}s")
            return False
    
    def find_element_robust(self, selectors: list, parent=None):
        """Find element using multiple selectors robustly."""
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
    
    def find_elements_robust(self, selectors: list, parent=None):
        """Find elements using multiple selectors robustly."""
        search_context = parent or self.driver
        
        for selector in selectors:
            try:
                elements = search_context.find_elements(By.CSS_SELECTOR, selector)
                
                if elements and self.debug_manager:
                    for element in elements[:3]:
                        self.debug_manager.highlight_element(element, "extract", 0.2)
                
                return elements
                
            except NoSuchElementException:
                continue
                
        return []
    
    def smart_back_to_modal(self):
        """Navigate back to modal intelligently."""
        try:
            current_url = self.driver.current_url
            
            if self.debug_manager:
                self.debug_manager.show_debug_info("Navigating back to modal...", 2.0)
            
            self.driver.back()
            self.wait_for_complete_navigation(current_url, 5.0)
            time.sleep(1.0)
            
            if self.debug_manager:
                self.debug_manager.show_debug_info("Back navigation completed", 1.0)
                
        except Exception as e:
            logger.error(f"Error navigating back: {e}")
            raise
