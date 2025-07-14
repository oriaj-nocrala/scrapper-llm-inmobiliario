"""
AssetPlanExtractorV2 refactorizado con componentes especializados.
Generado automáticamente por God Class Refactor Tool.
"""
from .debug_manager import AssetPlanDebugManager
from .navigation_manager_enhanced import AssetPlanNavigationManager
from .extraction_manager import AssetPlanExtractionManager
from .data_parser import DataParser
from ..infrastructure.human_behavior import HumanBehaviorSimulator
from ..models import Property, PropertyCollection, PropertyTypology


class AssetPlanExtractorV2Refactored:
    """AssetPlanExtractorV2 refactorizado con arquitectura modular."""
    
    def __init__(self, driver=None, **kwargs):
        """Initialize refactored AssetPlanExtractorV2.
        
        Args:
            driver: WebDriver instance
            **kwargs: Additional configuration
        """
        self.driver = driver
        
        # Initialize specialized components
        self.debug_manager = AssetPlanDebugManager(driver, **kwargs)
        self.navigation_manager = AssetPlanNavigationManager(driver, self.debug_manager, **kwargs)
        self.data_parser = DataParser()
        self.extraction_manager = AssetPlanExtractionManager(driver, self.navigation_manager, self.data_parser, **kwargs)
        
        # Legacy compatibility
        self.behavior = HumanBehaviorSimulator(driver)
        self.base_url = kwargs.get('base_url', "https://www.assetplan.cl")
        self.search_url = f"{self.base_url}/arriendo/departamento"
    
    # Coordinator methods
    def start_scraping(self, search_params: dict = None) -> PropertyCollection:
        """Main coordinator method for scraping process."""
        try:
            self.debug_manager.show_debug_info("Starting AssetPlan scraping...", 2.0)
            
            # Navigate to search page
            self.driver.get(self.search_url)
            self.navigation_manager.wait_for_complete_navigation("", 10.0)
            
            # Extract buildings
            buildings = self.extraction_manager.extract_building_cards()
            self.debug_manager.show_debug_info(f"Found {len(buildings)} buildings", 2.0)
            
            # Process each building
            properties = PropertyCollection()
            for building in buildings:
                building_properties = self._process_building(building)
                properties.extend(building_properties)
            
            return properties
            
        except Exception as e:
            logger.error(f"Error in scraping process: {e}")
            return PropertyCollection()
    
    def _process_building(self, building_data: dict) -> List[Property]:
        """Process individual building (coordinator method)."""
        try:
            # Navigate to building
            self.driver.get(building_data['url'])
            self.navigation_manager.wait_for_complete_navigation(building_data['url'], 10.0)
            
            # Extract typologies
            typologies = self.extraction_manager.extract_building_typologies()
            
            # Process each typology
            properties = []
            for typology in typologies:
                typology_properties = self._process_typology(building_data, typology)
                properties.extend(typology_properties)
            
            return properties
            
        except Exception as e:
            logger.error(f"Error processing building {building_data.get('name')}: {e}")
            return []
    
    def _process_typology(self, building_data: dict, typology_data: dict) -> List[Property]:
        """Process individual typology (coordinator method)."""
        # Implementation would delegate to extraction_manager
        # This is a simplified version
        return []
    
    # Legacy delegate methods for backward compatibility
    def enable_debug_mode(self, enabled: bool = True):
        """Delegate to debug manager."""
        return self.debug_manager.enable_debug_mode(enabled)
    
    def configure_behavior_mode(self, human_like: bool = False, behavior_mode: str = "extreme"):
        """Configure behavior mode."""
        self.navigation_manager.configure_behavior_mode(human_like, behavior_mode)
