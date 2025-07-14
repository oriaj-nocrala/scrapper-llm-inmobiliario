"""
Debug Manager especializado para AssetPlan Extractor.
Componente especializado generado automáticamente.
"""
import logging
import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)


class AssetPlanDebugManager:
    """Debug y monitoreo especializado."""
    
    def __init__(self, driver: WebDriver, **kwargs):
        """Initialize debug manager.
        
        Args:
            driver: WebDriver instance
            **kwargs: Additional configuration
        """
        self.driver = driver
        self.debug_mode = False
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def enable_debug_mode(self, enabled: bool = True):
        """Enable or disable debug mode with visual indicators."""
        self.debug_mode = enabled
        
    def highlight_element(self, element: WebElement, highlight_type: str = "highlight", duration: float = 1.5):
        """Highlight element for debugging."""
        if not self.debug_mode:
            return
            
        try:
            self.driver.execute_script("""
                arguments[0].style.border = '3px solid red';
                arguments[0].style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
            """, element)
            
            time.sleep(duration)
            
            self.driver.execute_script("""
                arguments[0].style.border = '';
                arguments[0].style.backgroundColor = '';
            """, element)
        except Exception:
            pass
            
    def show_debug_info(self, message: str, duration: float = 3.0):
        """Show debug information."""
        if self.debug_mode:
            logger.info(f"🔍 DEBUG: {message}")
            
    def debug_click(self, element: WebElement, context: str = ""):
        """Debug click with visual feedback."""
        if self.debug_mode:
            self.highlight_element(element, "click", 1.0)
            logger.info(f"🖱️ CLICK: {context}")
        
        element.click()
        
    def monitor_navigation(self, context: str = "", timeout: float = 10.0):
        """Monitor navigation changes with concise logging."""
        if not self.debug_mode:
            return
            
        try:
            current_url = self.driver.current_url
            logger.info(f"🌐 NAVIGATION: {context} - {current_url}")
        except Exception:
            pass
