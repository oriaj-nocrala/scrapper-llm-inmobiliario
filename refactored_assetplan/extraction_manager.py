"""
Extraction Manager especializado para AssetPlan Extractor.
Maneja toda la extracción de datos de edificios, tipologías y propiedades.
"""
import logging
from typing import Dict, List, Optional, Any
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)


class AssetPlanExtractionManager:
    """Extracción de datos especializada."""
    
    def __init__(self, driver: WebDriver, navigation_manager=None, data_parser=None, **kwargs):
        """Initialize extraction manager.
        
        Args:
            driver: WebDriver instance
            navigation_manager: Navigation manager instance
            data_parser: Data parser instance
            **kwargs: Additional configuration
        """
        self.driver = driver
        self.navigation_manager = navigation_manager
        self.data_parser = data_parser
        
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def extract_building_cards(self) -> List[Dict[str, Any]]:
        """Extract building cards from search results."""
        buildings = []
        
        try:
            # Usar navigation_manager para encontrar elementos
            building_cards = self.navigation_manager.find_elements_robust([
                'div.card.building-card',
                '.property-card',
                '.building-item'
            ])
            
            for card in building_cards:
                building_data = self.extract_building_card_data(card)
                if building_data and self.data_parser.validate_building_data(building_data):
                    buildings.append(building_data)
                    
        except Exception as e:
            logger.error(f"Error extracting building cards: {e}")
            
        return buildings
    
    def extract_building_card_data(self, card_element) -> Optional[Dict[str, Any]]:
        """Extract data from a building card."""
        try:
            # Extraer nombre del edificio
            name_element = self.navigation_manager.find_element_robust([
                'h3.building-name',
                '.card-title',
                'h2'
            ], card_element)
            
            name = name_element.text.strip() if name_element else "Unknown Building"
            
            # Extraer URL
            link_element = self.navigation_manager.find_element_robust([
                'a[href*="departamento"]',
                'a[href*="edificio"]',
                'a'
            ], card_element)
            
            url = link_element.get_attribute('href') if link_element else None
            
            if not url or not self.data_parser.is_valid_department_url(url):
                return None
            
            return {
                'name': name,
                'url': url,
                'card_element': card_element
            }
            
        except Exception as e:
            logger.debug(f"Error extracting building card data: {e}")
            return None
    
    def extract_building_typologies(self) -> List[Dict[str, Any]]:
        """Extract typologies from building detail page."""
        typologies = []
        
        try:
            typology_cards = self.navigation_manager.find_elements_robust([
                '.typology-card',
                '.apartment-type',
                '.unit-type'
            ])
            
            for card in typology_cards:
                typology_data = self.extract_typology_card_data(card)
                if typology_data:
                    typologies.append(typology_data)
                    
        except Exception as e:
            logger.error(f"Error extracting typologies: {e}")
            
        return typologies
    
    def extract_typology_card_data(self, card_element) -> Optional[Dict[str, Any]]:
        """Extract data from a typology card."""
        try:
            # Extraer información básica
            bedrooms_element = self.navigation_manager.find_element_robust([
                '[data-bedrooms]',
                '.bedrooms',
                '.dormitorios'
            ], card_element)
            
            bathrooms_element = self.navigation_manager.find_element_robust([
                '[data-bathrooms]',
                '.bathrooms',
                '.baños'
            ], card_element)
            
            area_element = self.navigation_manager.find_element_robust([
                '[data-area]',
                '.area',
                '.superficie'
            ], card_element)
            
            price_element = self.navigation_manager.find_element_robust([
                '.price',
                '.precio',
                '[data-price]'
            ], card_element)
            
            # Parsear datos usando data_parser
            bedrooms = self.data_parser.parse_bedrooms(bedrooms_element.text) if bedrooms_element else None
            bathrooms = self.data_parser.parse_bathrooms(bathrooms_element.text) if bathrooms_element else None
            area_m2 = self.data_parser.parse_area(area_element.text) if area_element else None
            price_uf = self.data_parser.parse_price_uf(price_element.text) if price_element else None
            
            return {
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'area_m2': area_m2,
                'price_uf': price_uf,
                'typology_id': self.data_parser.generate_typology_id(bedrooms, bathrooms, area_m2)
            }
            
        except Exception as e:
            logger.debug(f"Error extracting typology data: {e}")
            return None
