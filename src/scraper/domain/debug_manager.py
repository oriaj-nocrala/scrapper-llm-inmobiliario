"""
Debug Manager para AssetPlan Extractor.
Maneja todas las funcionalidades de debug y visualización.
"""
import logging
import time
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)


class DebugManager:
    """Gestor de funcionalidades de debug para el extractor."""
    
    def __init__(self, driver: WebDriver):
        """Initialize debug manager.
        
        Args:
            driver: WebDriver instance
        """
        self.driver = driver
        self.debug_mode = False
        
    def enable_debug_mode(self, enabled: bool = True):
        """Habilitar/deshabilitar modo debug."""
        self.debug_mode = enabled
        
        if enabled:
            # Inject CSS for debug highlighting
            debug_css = """
            .scraper-highlight {
                border: 3px solid red !important;
                background-color: yellow !important;
                opacity: 0.8 !important;
            }
            .scraper-click {
                border: 3px solid blue !important;
                background-color: lightblue !important;
                opacity: 0.9 !important;
            }
            .scraper-extract {
                border: 3px solid green !important;
                background-color: lightgreen !important;
                opacity: 0.7 !important;
            }
            .scraper-info {
                position: fixed;
                top: 10px;
                right: 10px;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 10px;
                border-radius: 5px;
                z-index: 10000;
                font-family: monospace;
            }
            """
            
            self.driver.execute_script(f"""
                var style = document.createElement('style');
                style.textContent = `{debug_css}`;
                document.head.appendChild(style);
            """)
            
            logger.info("Debug mode enabled with visual highlighting")
        else:
            logger.info("Debug mode disabled")
    
    def highlight_element(self, element: WebElement, highlight_type: str = "highlight", duration: float = 1.5):
        """Highlight an element for debugging.
        
        Args:
            element: Element to highlight
            highlight_type: Type of highlight (highlight, click, extract)
            duration: Duration in seconds
        """
        if not self.debug_mode:
            return
            
        try:
            # Add highlight class
            self.driver.execute_script(
                f"arguments[0].classList.add('scraper-{highlight_type}');", 
                element
            )
            
            # Wait for visibility
            time.sleep(duration)
            
            # Remove highlight class
            self.driver.execute_script(
                f"arguments[0].classList.remove('scraper-{highlight_type}');", 
                element
            )
            
        except Exception as e:
            logger.debug(f"Error highlighting element: {e}")
    
    def show_debug_info(self, message: str, duration: float = 3.0):
        """Show debug information overlay.
        
        Args:
            message: Debug message to show
            duration: Duration in seconds
        """
        if not self.debug_mode:
            return
            
        try:
            # Create info overlay
            self.driver.execute_script(f"""
                var info = document.createElement('div');
                info.textContent = `{message}`;
                info.className = 'scraper-info';
                info.id = 'scraper-debug-info';
                
                // Remove existing info
                var existing = document.getElementById('scraper-debug-info');
                if (existing) existing.remove();
                
                document.body.appendChild(info);
                
                setTimeout(() => {{
                    if (info.parentNode) {{
                        info.parentNode.removeChild(info);
                    }}
                }}, {duration * 1000});
            """)
            
            logger.debug(f"Debug info: {message}")
            
        except Exception as e:
            logger.debug(f"Error showing debug info: {e}")
    
    def debug_click(self, element: WebElement, context: str = ""):
        """Debug-aware click with visual feedback.
        
        Args:
            element: Element to click
            context: Context description for debugging
        """
        if self.debug_mode:
            self.show_debug_info(f"Clicking: {context}", 2.0)
            self.highlight_element(element, "click", 1.0)
            
        try:
            element.click()
            
            if self.debug_mode:
                time.sleep(0.5)  # Brief pause for visual confirmation
                
        except Exception as e:
            if self.debug_mode:
                self.show_debug_info(f"Click failed: {e}", 3.0)
            raise