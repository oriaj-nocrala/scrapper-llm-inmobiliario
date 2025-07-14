"""
Smart Element Locator with fallbacks and intelligent waiting strategies.
"""
import logging
import time
from typing import List, Optional, Tuple, Union

from selenium.common.exceptions import (ElementClickInterceptedException,
                                        NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class SmartElementLocator:
    """Intelligent element locator with fallback strategies and retry logic."""
    
    def __init__(self, driver: WebDriver, default_timeout: int = 10):
        """Initialize the smart locator.
        
        Args:
            driver: WebDriver instance
            default_timeout: Default timeout for element operations
        """
        self.driver = driver
        self.default_timeout = default_timeout
        self.wait = WebDriverWait(driver, default_timeout)
        
    
    def find_elements_smart(
        self,
        selectors: Union[str, List[str]],
        by: By = By.CSS_SELECTOR,
        timeout: Optional[int] = None,
        min_elements: int = 1
    ) -> List[WebElement]:
        """Find multiple elements using smart locating.
        
        Args:
            selectors: Single selector or list of fallback selectors
            by: Selenium By strategy
            timeout: Custom timeout
            min_elements: Minimum number of elements required
            
        Returns:
            List of WebElements (empty if none found)
        """
        if isinstance(selectors, str):
            selectors = [selectors]
        
        timeout = timeout or self.default_timeout
        
        for selector in selectors:
            try:
                logger.debug(f"Looking for elements with selector: {selector}")
                
                # Wait for at least min_elements to be present
                wait = WebDriverWait(self.driver, timeout)
                wait.until(lambda d: len(d.find_elements(by, selector)) >= min_elements)
                
                elements = self.driver.find_elements(by, selector)
                if len(elements) >= min_elements:
                    logger.debug(f"Found {len(elements)} elements with selector: {selector}")
                    return elements
                    
            except TimeoutException:
                logger.debug(f"Timeout waiting for {min_elements} elements with selector: {selector}")
                continue
            except Exception as e:
                logger.debug(f"Error finding elements with selector '{selector}': {e}")
                continue
        
        logger.warning(f"Could not find {min_elements}+ elements with any selector")
        return []
    
    
    def wait_for_any_element(
        self,
        selectors: List[str],
        by: By = By.CSS_SELECTOR,
        timeout: Optional[int] = None
    ) -> Tuple[Optional[WebElement], Optional[str]]:
        """Wait for any of the provided selectors to find an element.
        
        Args:
            selectors: List of selectors to try
            by: Locator strategy
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (element, successful_selector) or (None, None)
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            for selector in selectors:
                try:
                    element = self.driver.find_element(by, selector)
                    if element.is_displayed():
                        return element, selector
                except (NoSuchElementException, StaleElementReferenceException):
                    continue
            
            time.sleep(0.5)  # Short pause before retrying
        
        return None, None
    
    
    def safe_get_text(self, element: WebElement, retry_count: int = 3) -> str:
        """Safely get text from element with retry logic.
        
        Args:
            element: Element to get text from
            retry_count: Number of retries
            
        Returns:
            Element text or empty string if failed
        """
        for attempt in range(retry_count):
            try:
                return element.text.strip()
            except StaleElementReferenceException:
                logger.warning(f"Stale element reference during text extraction (attempt {attempt + 1})")
                if attempt < retry_count - 1:
                    time.sleep(0.5)
                    continue
                return ""
            except Exception as e:
                logger.warning(f"Failed to get text: {e} (attempt {attempt + 1})")
                if attempt < retry_count - 1:
                    time.sleep(0.5)
                    continue
        
        return ""
    
    def safe_get_attribute(
        self,
        element: WebElement,
        attribute: str,
        retry_count: int = 3
    ) -> Optional[str]:
        """Safely get attribute from element with retry logic.
        
        Args:
            element: Element to get attribute from
            attribute: Attribute name
            retry_count: Number of retries
            
        Returns:
            Attribute value or None if failed
        """
        for attempt in range(retry_count):
            try:
                return element.get_attribute(attribute)
            except StaleElementReferenceException:
                logger.warning(f"Stale element reference during attribute extraction (attempt {attempt + 1})")
                if attempt < retry_count - 1:
                    time.sleep(0.5)
                    continue
                return None
            except Exception as e:
                logger.warning(f"Failed to get attribute '{attribute}': {e} (attempt {attempt + 1})")
                if attempt < retry_count - 1:
                    time.sleep(0.5)
                    continue
        
        return None
    
    def wait_for_page_load(self, timeout: Optional[int] = None) -> bool:
        """Wait for page to fully load.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if page loaded, False if timeout
        """
        timeout = timeout or self.default_timeout
        
        try:
            # Wait for document ready state
            wait = WebDriverWait(self.driver, timeout)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            # Additional wait for any AJAX calls
            time.sleep(1)
            
            # Wait for jQuery if it exists
            try:
                wait.until(lambda driver: driver.execute_script("return jQuery.active == 0") if driver.execute_script("return typeof jQuery !== 'undefined'") else True)
            except:
                pass  # jQuery might not be present
            
            return True
            
        except TimeoutException:
            logger.warning("Page load timeout")
            return False
    
    def is_element_stale(self, element: WebElement) -> bool:
        """Check if element is stale.
        
        Args:
            element: Element to check
            
        Returns:
            True if element is stale
        """
        try:
            element.tag_name  # This will raise StaleElementReferenceException if stale
            return False
        except StaleElementReferenceException:
            return True
        except Exception:
            return True  # Consider any other exception as stale for safety


class PropertySelectors:
    """Predefined selectors for common property elements."""
    
    # Property container selectors (in order of preference)
    PROPERTY_CONTAINERS = [
        "article",
        ".property-card",
        ".property",
        ".listing",
        "[class*='property']",
        "[class*='listing']",
        "[data-property]",
        ".card",
        "[class*='apartment']",
        "[class*='house']"
    ]
    
    # Title selectors
    TITLE_SELECTORS = [
        "h1", "h2", "h3", "h4",
        ".title", ".property-title", ".listing-title",
        "[class*='title']", "[class*='name']",
        ".property-name", ".listing-name"
    ]
    
    # Price selectors
    PRICE_SELECTORS = [
        ".price", ".precio", ".cost", ".rent",
        "[class*='price']", "[class*='precio']",
        "[class*='cost']", "[class*='rent']",
        "[data-price]", ".property-price"
    ]
    
    # Location selectors
    LOCATION_SELECTORS = [
        ".location", ".address", ".ubicacion", ".direccion",
        "[class*='location']", "[class*='address']",
        "[class*='ubicacion']", "[class*='direccion']",
        ".property-location", ".listing-location"
    ]
    
    # Area selectors
    AREA_SELECTORS = [
        "[class*='area']", "[class*='size']", "[class*='superficie']",
        ".area", ".size", ".superficie", ".m2", ".sqft",
        "[class*='m2']", "[class*='sqft']"
    ]
    
    # Room selectors
    BEDROOM_SELECTORS = [
        "[class*='bedroom']", "[class*='dormitorio']", "[class*='habitacion']",
        ".bedrooms", ".dormitorios", ".habitaciones",
        "[class*='bed']", "[class*='room']"
    ]
    
    BATHROOM_SELECTORS = [
        "[class*='bathroom']", "[class*='baño']", "[class*='bath']",
        ".bathrooms", ".baños", ".baths"
    ]
    
    # Image selectors
    IMAGE_SELECTORS = [
        "img", ".image", ".photo", ".picture",
        "[class*='image']", "[class*='photo']", "[class*='picture']"
    ]
    
    # Link selectors
    LINK_SELECTORS = [
        "a[href]", "a"
    ]