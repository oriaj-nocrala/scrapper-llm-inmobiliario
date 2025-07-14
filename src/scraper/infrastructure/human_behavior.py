"""
Human Behavior Simulator for natural web scraping interactions.
"""
import logging
import math
import random
import time
from typing import List, Tuple

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)


class HumanBehaviorSimulator:
    """Simulates human-like behavior during web scraping."""
    
    def __init__(self, driver: WebDriver, speed_factor: float = 1.0):
        """Initialize the behavior simulator.
        
        Args:
            driver: WebDriver instance
            speed_factor: Multiplier for timing (1.0 = normal, 0.5 = faster, 2.0 = slower)
        """
        self.driver = driver
        self.speed_factor = speed_factor
        self.actions = ActionChains(driver)
        
    def random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
        """Add a random delay to simulate human thinking time.
        
        Args:
            min_seconds: Minimum delay
            max_seconds: Maximum delay
        """
        delay = random.uniform(min_seconds, max_seconds) * self.speed_factor
        logger.debug(f"Human delay: {delay:.2f}s")
        time.sleep(delay)
    
    def smooth_scroll_to_element(self, element: WebElement, speed: int = 300) -> None:
        """Scroll smoothly to an element like a human would.
        
        Args:
            element: Target element to scroll to
            speed: Scroll speed in pixels per second
        """
        try:
            # Get element position
            element_location = element.location_once_scrolled_into_view
            current_scroll = self.driver.execute_script("return window.pageYOffset;")
            target_scroll = element_location.get('y', 0) - 100  # Offset for better visibility
            
            # Calculate scroll distance and steps
            scroll_distance = abs(target_scroll - current_scroll)
            steps = max(5, int(scroll_distance / 50))  # At least 5 steps
            step_size = (target_scroll - current_scroll) / steps
            
            logger.debug(f"Smooth scrolling from {current_scroll} to {target_scroll} in {steps} steps")
            
            # Perform smooth scrolling
            for i in range(steps):
                current_position = current_scroll + (step_size * (i + 1))
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                
                # Variable delay between scroll steps
                step_delay = random.uniform(0.05, 0.15) * self.speed_factor
                time.sleep(step_delay)
            
            # Final positioning
            self.driver.execute_script(f"window.scrollTo(0, {target_scroll});")
            time.sleep(0.2 * self.speed_factor)
            
        except Exception as e:
            logger.warning(f"Smooth scroll failed, using fallback: {e}")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth'});", element)
            time.sleep(1.0 * self.speed_factor)
    
    def progressive_page_scroll(self, scroll_pause_time: float = 1.0, num_scrolls: int = 3) -> None:
        """Progressively scroll through the page to load dynamic content.
        
        Args:
            scroll_pause_time: Time to pause between scrolls
            num_scrolls: Number of scroll steps
        """
        logger.debug(f"Progressive page scroll with {num_scrolls} steps")
        
        # Get page height
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for i in range(num_scrolls):
            # Calculate scroll position (progressively down the page)
            scroll_position = (i + 1) * (last_height / num_scrolls)
            
            # Scroll to position with some randomness
            random_offset = random.randint(-50, 50)
            final_position = max(0, scroll_position + random_offset)
            
            self.driver.execute_script(f"window.scrollTo(0, {final_position});")
            
            # Variable pause time
            pause = scroll_pause_time * random.uniform(0.8, 1.2) * self.speed_factor
            time.sleep(pause)
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height > last_height:
                logger.debug(f"New content loaded, page height: {last_height} -> {new_height}")
                last_height = new_height
    
    def natural_mouse_movement(self, element: WebElement) -> None:
        """Move mouse to element in a natural way.
        
        Args:
            element: Target element
        """
        try:
            # Get current mouse position (approximate)
            current_pos = self.driver.execute_script("""
                return {
                    x: window.screenX + window.outerWidth / 2,
                    y: window.screenY + window.outerHeight / 2
                };
            """)
            
            # Get element position
            element_rect = self.driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                return {
                    x: rect.left + rect.width / 2,
                    y: rect.top + rect.height / 2
                };
            """, element)
            
            # Create natural movement path (simplified Bézier curve)
            self._move_mouse_naturally(
                (current_pos['x'], current_pos['y']),
                (element_rect['x'], element_rect['y'])
            )
            
        except Exception as e:
            logger.debug(f"Natural mouse movement failed, using simple hover: {e}")
            self.actions.move_to_element(element).perform()
    
    def _move_mouse_naturally(self, start: Tuple[int, int], end: Tuple[int, int]) -> None:
        """Move mouse along a natural path.
        
        Args:
            start: Starting position (x, y)
            end: Ending position (x, y)
        """
        steps = random.randint(8, 15)
        
        for i in range(steps + 1):
            t = i / steps
            
            # Add some randomness to the path
            noise_x = random.uniform(-5, 5) * math.sin(t * math.pi)
            noise_y = random.uniform(-5, 5) * math.cos(t * math.pi)
            
            # Linear interpolation with noise
            x = start[0] + (end[0] - start[0]) * t + noise_x
            y = start[1] + (end[1] - start[1]) * t + noise_y
            
            # Move mouse (this is approximate since we can't control system cursor)
            self.actions.move_by_offset(x - start[0], y - start[1])
            
            # Small delay between movements
            time.sleep(random.uniform(0.01, 0.03) * self.speed_factor)
        
        self.actions.perform()
        self.actions.reset_actions()
    
    def simulate_reading_time(self, text_length: int) -> None:
        """Simulate time a human would take to read text.
        
        Args:
            text_length: Length of text in characters
        """
        # Average reading speed: 200-300 words per minute
        # Average word length: 5 characters
        words = max(1, text_length / 5)
        reading_speed = random.uniform(200, 300)  # words per minute
        reading_time = (words / reading_speed) * 60  # convert to seconds
        
        # Add some randomness and apply speed factor
        actual_time = reading_time * random.uniform(0.3, 0.8) * self.speed_factor
        
        logger.debug(f"Simulating reading time: {actual_time:.2f}s for {text_length} characters")
        time.sleep(max(0.5, actual_time))  # Minimum 0.5 seconds
    
    def human_like_click(self, element: WebElement) -> None:
        """Perform a human-like click on an element.
        
        Args:
            element: Element to click
        """
        try:
            # Move to element naturally
            self.natural_mouse_movement(element)
            
            # Small pause before clicking
            time.sleep(random.uniform(0.1, 0.3) * self.speed_factor)
            
            # Click with slight randomness in timing
            click_delay = random.uniform(0.05, 0.15) * self.speed_factor
            time.sleep(click_delay)
            
            element.click()
            
            # Small pause after clicking
            time.sleep(random.uniform(0.2, 0.5) * self.speed_factor)
            
        except Exception as e:
            logger.warning(f"Human-like click failed, using simple click: {e}")
            element.click()
    
    def simulate_typing(self, element: WebElement, text: str) -> None:
        """Simulate human-like typing.
        
        Args:
            element: Input element
            text: Text to type
        """
        element.clear()
        
        for char in text:
            element.send_keys(char)
            
            # Variable typing speed
            typing_delay = random.uniform(0.05, 0.2) * self.speed_factor
            time.sleep(typing_delay)
            
            # Occasional longer pauses (thinking)
            if random.random() < 0.1:  # 10% chance
                time.sleep(random.uniform(0.5, 1.0) * self.speed_factor)
    
    def simulate_tab_browsing(self) -> None:
        """Simulate natural tab browsing behavior."""
        # Randomly press Tab to navigate (simulates looking around)
        if random.random() < 0.3:  # 30% chance
            self.actions.send_keys(Keys.TAB).perform()
            time.sleep(random.uniform(0.2, 0.5) * self.speed_factor)
    
    def simulate_page_interaction(self, elements: List[WebElement]) -> None:
        """Simulate natural page interaction by hovering over random elements.
        
        Args:
            elements: List of elements to potentially interact with
        """
        if not elements:
            return
            
        # Randomly hover over 1-3 elements
        num_interactions = random.randint(1, min(3, len(elements)))
        selected_elements = random.sample(elements, num_interactions)
        
        for element in selected_elements:
            try:
                # Move to element
                self.actions.move_to_element(element).perform()
                
                # Pause as if reading/considering
                pause_time = random.uniform(0.5, 1.5) * self.speed_factor
                time.sleep(pause_time)
                
            except Exception as e:
                logger.debug(f"Failed to interact with element: {e}")
                continue
    
    def anti_detection_pause(self) -> None:
        """Add a longer pause to avoid detection patterns."""
        pause_time = random.uniform(2.0, 5.0) * self.speed_factor
        logger.debug(f"Anti-detection pause: {pause_time:.2f}s")
        time.sleep(pause_time)


class BehaviorConfig:
    """Configuration for human behavior patterns."""
    
    # Timing configurations
    FAST = {"speed_factor": 0.5, "scroll_pause": 0.5, "read_speed": 400}
    NORMAL = {"speed_factor": 1.0, "scroll_pause": 1.0, "read_speed": 250}
    SLOW = {"speed_factor": 2.0, "scroll_pause": 2.0, "read_speed": 150}
    VERY_SLOW = {"speed_factor": 3.0, "scroll_pause": 3.0, "read_speed": 100}
    
    @classmethod
    def get_config(cls, mode: str = "normal") -> dict:
        """Get behavior configuration by mode.
        
        Args:
            mode: Behavior mode ("fast", "normal", "slow", "very_slow")
            
        Returns:
            Configuration dictionary
        """
        configs = {
            "fast": cls.FAST,
            "normal": cls.NORMAL,
            "slow": cls.SLOW,
            "very_slow": cls.VERY_SLOW
        }
        return configs.get(mode, cls.NORMAL)