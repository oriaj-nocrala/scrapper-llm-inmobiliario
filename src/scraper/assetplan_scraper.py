import json
import logging
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from ..utils.config import settings
from .models import Property, PropertyCollection

logger = logging.getLogger(__name__)


class AssetplanScraper:
    """Web scraper for assetplan.cl real estate properties."""
    
    def __init__(self, headless: bool = True):
        """Initialize the scraper with Chrome WebDriver.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.comunas_rm = [
            "Colina", "Lampa", "Til Til", "Pirque", "Puente Alto", "San José de Maipo",
            "Buin", "Calera de Tango", "Paine", "San Bernardo", "Alhué", "Curacaví",
            "María Pinto", "Melipilla", "San Pedro", "Cerrillos", "Cerro Navia",
            "Conchalí", "El Bosque", "Estación Central", "Huechuraba", "Independencia",
            "La Cisterna", "La Granja", "La Florida", "La Pintana", "La Reina",
            "Las Condes", "Lo Barnechea", "Lo Espejo", "Lo Prado", "Macul", "Maipú",
            "Ñuñoa", "Pedro Aguirre Cerda", "Peñalolén", "Providencia", "Pudahuel",
            "Quilicura", "Quinta Normal", "Recoleta", "Renca", "San Miguel",
            "San Joaquín", "San Ramón", "Santiago", "Vitacura", "El Monte",
            "Isla de Maipo", "Padre Hurtado", "Peñaflor", "Talagante"
        ] 
        # FIXME
        # En assetplan_extractor.py ya existe este listado, pero para comunas de santiago.
        # Revisar unificacion.

        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.base_url = "https://www.assetplan.cl"
        self.properties_url = f"{self.base_url}/arriendo/departamento"
        
    def _setup_driver(self) -> webdriver.Chrome:
        """Set up and configure Chrome WebDriver."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        
        return driver
    
    def start_driver(self) -> None:
        """Start the WebDriver."""
        if self.driver is None:
            self.driver = self._setup_driver()
            logger.info("Chrome WebDriver started successfully")
    
    def stop_driver(self) -> None:
        """Stop and quit the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Chrome WebDriver stopped")
    
    def _extract_property_from_link(self, property_url: str, element) -> Optional[Property]:
        """Extract property details from a property link and its parent element.
        
        Args:
            property_url: URL of the property
            element: Parent element containing property info
            
        Returns:
            Property object or None if extraction fails
        """
        try:
            # Extract basic info from the parent element
            text_content = element.text.strip()
            
            # Extract title (first line usually contains the building/property name)
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            title = lines[0] if lines else "Property"
            
            # Look for price information
            price = None
            price_uf = None
            for line in lines:
                if '$' in line or 'UF' in line.upper():
                    price = line
                    # Try to extract UF value
                    if "UF" in line.upper():
                        import re
                        uf_match = re.search(r'UF\s*([0-9.,]+)', line.upper())
                        if uf_match:
                            try:
                                price_uf = float(uf_match.group(1).replace(',', '').replace('.', ''))
                            except:
                                pass
                    break
            
            # Look for location (usually contains commune names)
            location = None
            for line in lines:
                if any(comuna in line for comuna in self.comunas_rm):
                    location = line
                    break
            
            # Look for room info
            bedrooms = None
            bathrooms = None
            for line in lines:
                if 'dormitorio' in line.lower() or 'habitacion' in line.lower():
                    import re
                    bed_match = re.search(r'([0-9]+)', line)
                    if bed_match:
                        bedrooms = int(bed_match.group(1))
                if 'baño' in line.lower():
                    import re
                    bath_match = re.search(r'([0-9]+)', line)
                    if bath_match:
                        bathrooms = int(bath_match.group(1))
            
            # Look for area
            area_m2 = None
            for line in lines:
                if 'm²' in line or 'm2' in line:
                    import re
                    area_match = re.search(r'([0-9.,]+)\s*m', line.lower())
                    if area_match:
                        try:
                            area_m2 = float(area_match.group(1).replace(',', '.'))
                        except:
                            pass
                    break
            
            # Determine property type
            property_type = "Departamento"  # Default for assetplan.cl
            if 'casa' in property_url.lower():
                property_type = "Casa"
            
            # Look for images in the element
            images = []
            try:
                img_elements = element.find_elements(By.TAG_NAME, "img")
                for img in img_elements:
                    img_src = img.get_attribute("src")
                    if img_src and "placeholder" not in img_src.lower():
                        full_img_url = urljoin(self.base_url, img_src)
                        images.append(full_img_url)
            except:
                pass
            
            # Create property object
            property_obj = Property(
                title=title,
                price=price,
                price_uf=price_uf,
                location=location,
                area_m2=area_m2,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                property_type=property_type,
                url=property_url,
                images=images[:5],  # Limit to first 5 images
                description=text_content[:500]  # First 500 chars as description
            )
            
            return property_obj
            
        except Exception as e:
            logger.error(f"Error extracting property from link {property_url}: {e}")
            return None
    
    def _extract_property_details(self, property_element) -> Optional[Property]:
        """Extract property details from a property card element.
        
        Args:
            property_element: Selenium WebElement representing a property card
            
        Returns:
            Property object or None if extraction fails
        """
        try:
            # Extract property URL
            link_element = property_element.find_element(By.TAG_NAME, "a")
            property_url = link_element.get_attribute("href")
            
            if not property_url:
                return None
                
            # Extract title
            title_element = property_element.find_element(By.CSS_SELECTOR, "h3, .property-title, .title")
            title = title_element.text.strip()
            
            # Extract price
            price = None
            price_uf = None
            try:
                price_element = property_element.find_element(By.CSS_SELECTOR, ".price, .precio, [class*='price']")
                price_text = price_element.text.strip()
                price = price_text
                
                # Try to extract UF value
                if "UF" in price_text.upper():
                    import re
                    uf_match = re.search(r'UF\s*([0-9.,]+)', price_text.upper())
                    if uf_match:
                        price_uf = float(uf_match.group(1).replace(',', '').replace('.', ''))
            except NoSuchElementException:
                pass
            
            # Extract location
            location = None
            try:
                location_element = property_element.find_element(By.CSS_SELECTOR, ".location, .ubicacion, [class*='location']")
                location = location_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract area
            area_m2 = None
            try:
                area_element = property_element.find_element(By.CSS_SELECTOR, "[class*='area'], [class*='superficie'], .m2")
                area_text = area_element.text.strip()
                import re
                area_match = re.search(r'([0-9.,]+)\s*m', area_text.lower())
                if area_match:
                    area_m2 = float(area_match.group(1).replace(',', '.'))
            except NoSuchElementException:
                pass
            
            # Extract bedrooms
            bedrooms = None
            try:
                bed_element = property_element.find_element(By.CSS_SELECTOR, "[class*='bedroom'], [class*='dormitorio'], .bed")
                bed_text = bed_element.text.strip()
                import re
                bed_match = re.search(r'([0-9]+)', bed_text)
                if bed_match:
                    bedrooms = int(bed_match.group(1))
            except NoSuchElementException:
                pass
            
            # Extract bathrooms
            bathrooms = None
            try:
                bath_element = property_element.find_element(By.CSS_SELECTOR, "[class*='bathroom'], [class*='baño'], .bath")
                bath_text = bath_element.text.strip()
                import re
                bath_match = re.search(r'([0-9]+)', bath_text)
                if bath_match:
                    bathrooms = int(bath_match.group(1))
            except NoSuchElementException:
                pass
            
            # Extract property type
            property_type = None
            try:
                type_element = property_element.find_element(By.CSS_SELECTOR, ".type, .tipo, [class*='type']")
                property_type = type_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract images
            images = []
            try:
                img_elements = property_element.find_elements(By.TAG_NAME, "img")
                for img in img_elements:
                    img_src = img.get_attribute("src")
                    if img_src and "placeholder" not in img_src.lower():
                        full_img_url = urljoin(self.base_url, img_src)
                        images.append(full_img_url)
            except NoSuchElementException:
                pass
            
            # Create property object
            property_obj = Property(
                title=title,
                price=price,
                price_uf=price_uf,
                location=location,
                area_m2=area_m2,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                property_type=property_type,
                url=property_url,
                images=images[:5]  # Limit to first 5 images
            )
            
            return property_obj
            
        except Exception as e:
            logger.error(f"Error extracting property details: {e}")
            return None
    
    def scrape_properties(self, max_properties: int = None) -> PropertyCollection:
        """Scrape properties from assetplan.cl.
        
        Args:
            max_properties: Maximum number of properties to scrape
            
        Returns:
            PropertyCollection with scraped properties
        """
        if max_properties is None:
            max_properties = settings.max_properties
            
        if not self.driver:
            self.start_driver()
        
        properties = []
        scraped_count = 0
        page = 1
        
        logger.info(f"Starting to scrape properties from {self.properties_url}")
        
        while scraped_count < max_properties:
            try:
                # Navigate to properties page
                url = f"{self.properties_url}?page={page}" if page > 1 else self.properties_url
                self.driver.get(url)
                
                # Wait for page to load
                time.sleep(2)
                
                # Look for property links instead of cards
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                property_links = []
                
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and any(keyword in href.lower() for keyword in ['departamento', 'casa', 'propiedad']):
                        # Avoid duplicate links and filter out non-property links
                        if href not in [pl[0] for pl in property_links] and any(coord in href for coord in ['-70.', '-33.']):
                            parent_element = link.find_element(By.XPATH, "./..")
                            property_links.append((href, parent_element))
                
                logger.info(f"Found {len(property_links)} property links")
                
                if not property_links:
                    logger.warning(f"No property links found on page {page}")
                    break
                
                
                # Extract properties from current page
                page_properties = []
                for property_url, element in property_links:
                    if scraped_count >= max_properties:
                        break
                        
                    property_obj = self._extract_property_from_link(property_url, element)
                    if property_obj:
                        page_properties.append(property_obj)
                        scraped_count += 1
                        
                        if scraped_count % 10 == 0:
                            logger.info(f"Scraped {scraped_count} properties so far...")
                
                properties.extend(page_properties)
                
                # Check if we have more pages
                if len(page_properties) == 0:
                    logger.info("No more properties found, stopping")
                    break
                
                # Add delay between requests
                time.sleep(settings.scraping_delay)
                page += 1
                
            except TimeoutException:
                logger.error(f"Timeout loading page {page}")
                break
            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}")
                break
        
        # Create property collection
        collection = PropertyCollection(
            properties=properties,
            total_count=len(properties),
            scraped_at=datetime.now().isoformat(),
            source_url=self.base_url
        )
        
        logger.info(f"Scraping completed. Total properties: {len(properties)}")
        return collection
    
    def save_to_json(self, collection: PropertyCollection, filepath: str = None) -> str:
        """Save property collection to JSON file.
        
        Args:
            collection: PropertyCollection to save
            filepath: Path to save file (optional)
            
        Returns:
            Path to saved file
        """
        if filepath is None:
            filepath = settings.properties_json_path
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(collection.model_dump(mode='json'), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Properties saved to {filepath}")
        return filepath
    
def main():
    """Main function to run the scraper."""
    logging.basicConfig(level=logging.INFO)
    
    with AssetplanScraper(headless=settings.headless_browser) as scraper:
        collection = scraper.scrape_properties(max_properties=settings.max_properties)
        scraper.save_to_json(collection)
        
        print(f"✅ Scraping completed!")
        print(f"📊 Total properties scraped: {collection.total_count}")
        print(f"💾 Data saved to: {settings.properties_json_path}")


if __name__ == "__main__":
    main()