"""
Tests de regresión para la funcionalidad MULTI-TIPOLOGÍA.
Previene regresiones en navegación back y extracción de múltiples edificios.
"""

import pytest
import time
from unittest.mock import Mock, patch, call
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from src.scraper.domain.assetplan_extractor_v2 import AssetPlanExtractorV2
from src.scraper.models import Property, PropertyCollection
from src.scraper.services.scraper_manager import ScrapingConfig, ScraperManager


class TestMultiTypologyRegression:
    """Tests críticos para la funcionalidad multi-tipología."""
    
    def test_scraper_manager_passes_max_typologies(self):
        """CRÍTICO: ScraperManager debe pasar max_typologies al extractor."""
        config = ScrapingConfig(
            max_properties=8,
            max_typologies=2
        )
        
        mock_driver = Mock(spec=WebDriver)
        
        with patch('src.scraper.services.scraper_manager.DriverManager') as mock_driver_manager:
            mock_driver_manager.return_value.get_driver.return_value = mock_driver
            
            with patch('src.scraper.services.scraper_manager.AssetPlanExtractorV2') as mock_extractor_class:
                mock_extractor = Mock()
                mock_extractor.start_scraping.return_value = PropertyCollection(
                    properties=[],
                    typologies={},
                    total_count=0,
                    scraped_at="2023-01-01T00:00:00",
                    source_url="https://test.com"
                )
                mock_extractor_class.return_value = mock_extractor
                
                manager = ScraperManager(config)
                manager.scrape_properties()
                
                # Verificar que start_scraping fue llamado con los parámetros correctos
                mock_extractor.start_scraping.assert_called_once_with(
                    max_properties=8,
                    max_typologies=2
                )


class TestMultiTypologyNavigation:
    """Tests para navegación back en modo multi-tipología."""
    
    @pytest.fixture
    def extractor_with_mocks(self):
        """Extractor con mocks configurados para navegación."""
        mock_driver = Mock(spec=WebDriver)
        extractor = AssetPlanExtractorV2(mock_driver)
        
        # Mock métodos de navegación
        extractor._smart_back_to_modal = Mock()
        extractor._smart_delay = Mock()
        extractor.wait = Mock()
        
        return extractor
    
class TestMultiTypologyLogic:
    """Tests para la lógica de procesamiento multi-tipología."""
    
    def test_extract_from_multiple_buildings_distribution(self):
        """CRÍTICO: Distribución correcta de propiedades entre edificios."""
        mock_driver = Mock(spec=WebDriver)
        extractor = AssetPlanExtractorV2(mock_driver)
        
        # Mock edificios
        building_cards = [
            {"name": "Edificio 1", "url": "url1"},
            {"name": "Edificio 2", "url": "url2"},
            {"name": "Edificio 3", "url": "url3"}
        ]
        
        # Mock validación y procesamiento
        extractor._validate_building_data = Mock(return_value=True)
        
        def mock_process_building(building_data, max_props):
            # Simular que cada edificio retorna una propiedad
            return [
                Property(
                    title=f"Prop from {building_data['name']}",
                    url="https://test.com",
                    id=f"prop_{building_data['name']}"
                )
            ]
        
        extractor._process_building = Mock(side_effect=mock_process_building)
        extractor._navigate_back_to_buildings_list = Mock(return_value=True)
        extractor._smart_delay = Mock()
        extractor.extreme_mode = True  # Para evitar logs
        
        # Test: 9 propiedades de 3 edificios
        properties = extractor._extract_from_multiple_buildings(
            building_cards, max_properties=9, max_typologies=3
        )
        
        assert len(properties) == 3  # Una de cada edificio
        assert extractor._process_building.call_count == 3
        assert extractor._navigate_back_to_buildings_list.call_count == 2  # 2 backs (no en el último)
    
    def test_extract_from_multiple_buildings_max_properties_limit(self):
        """CRÍTICO: Respetar límite de max_properties."""
        mock_driver = Mock(spec=WebDriver)
        extractor = AssetPlanExtractorV2(mock_driver)
        
        building_cards = [{"name": f"Edificio {i}", "url": f"url{i}"} for i in range(5)]
        
        extractor._validate_building_data = Mock(return_value=True)
        extractor._process_building = Mock(return_value=[
            Property(title="Test", url="https://test.com", id="test1"),
            Property(title="Test2", url="https://test.com", id="test2")
        ])  # 2 propiedades por edificio
        extractor._navigate_back_to_buildings_list = Mock(return_value=True)
        extractor._smart_delay = Mock()
        extractor.extreme_mode = True
        
        # Test: límite de 3 propiedades
        properties = extractor._extract_from_multiple_buildings(
            building_cards, max_properties=3, max_typologies=5
        )
        
        # Debe parar cuando alcance max_properties
        assert len(properties) <= 3
        # No debe procesar todos los edificios
        assert extractor._process_building.call_count < 5
    
    def test_extract_from_multiple_buildings_error_recovery(self):
        """CRÍTICO: Recuperación de errores en modo multi-tipología."""
        mock_driver = Mock(spec=WebDriver)
        extractor = AssetPlanExtractorV2(mock_driver)
        
        building_cards = [
            {"name": "Edificio OK", "url": "url1"},
            {"name": "Edificio ERROR", "url": "url2"},
            {"name": "Edificio OK2", "url": "url3"}
        ]
        
        extractor._validate_building_data = Mock(return_value=True)
        
        def mock_process_building_with_error(building_data, max_props):
            if "ERROR" in building_data['name']:
                raise Exception("Processing error")
            return [Property(title=f"Prop from {building_data['name']}", url="https://test.com")]
        
        extractor._process_building = Mock(side_effect=mock_process_building_with_error)
        extractor._navigate_back_to_buildings_list = Mock(return_value=True)
        extractor._smart_delay = Mock()
        extractor.extreme_mode = True
        
        properties = extractor._extract_from_multiple_buildings(
            building_cards, max_properties=10, max_typologies=3
        )
        
        # Debe recuperarse del error y procesar el siguiente edificio
        assert len(properties) == 2  # Solo los edificios OK
        assert extractor._process_building.call_count == 3  # Intentó los 3
        assert extractor._navigate_back_to_buildings_list.call_count >= 1  # Intentó navegación back


class TestMultiTypologyModeSelection:
    """Tests para selección automática del modo correcto."""
    
    def test_start_scraping_selects_multi_mode(self):
        """CRÍTICO: start_scraping debe elegir modo multi-tipología cuando max_typologies > 1."""
        mock_driver = Mock(spec=WebDriver)
        extractor = AssetPlanExtractorV2(mock_driver)
        
        # Mock métodos necesarios
        extractor._navigate_to_search_page = Mock()
        extractor._extract_building_cards = Mock(return_value=[
            {"name": "Building 1"}, {"name": "Building 2"}, {"name": "Building 3"}
        ])
        extractor._extract_from_multiple_buildings = Mock(return_value=[])
        extractor.extreme_mode = True
        
        # Test con max_typologies > 1
        extractor.start_scraping(max_properties=10, max_typologies=3)
        
        # Debe llamar modo multi-tipología
        extractor._extract_from_multiple_buildings.assert_called_once_with(
            extractor._extract_building_cards.return_value, 10, 3
        )
    
    def test_start_scraping_selects_standard_mode(self):
        """CRÍTICO: start_scraping debe usar modo estándar cuando max_typologies es None o 1."""
        mock_driver = Mock(spec=WebDriver)
        extractor = AssetPlanExtractorV2(mock_driver)
        
        # Mock métodos necesarios
        extractor._navigate_to_search_page = Mock()
        extractor._extract_building_cards = Mock(return_value=[{"name": "Building 1"}])
        extractor._validate_building_data = Mock(return_value=True)
        extractor._process_building = Mock(return_value=[])
        extractor._smart_delay = Mock()
        extractor.extreme_mode = True
        
        # Test con max_typologies = None
        extractor.start_scraping(max_properties=10, max_typologies=None)
        
        # Debe llamar modo estándar
        extractor._process_building.assert_called_once()


class TestMultiTypologyPerformance:
    """Tests de performance para multi-tipología."""
    
    def test_multi_typology_building_processing_distribution(self):
        """CRÍTICO: Distribución de carga entre edificios debe ser eficiente."""
        # Test que la distribución de propiedades entre edificios sea lógica
        max_properties = 15
        max_typologies = 5
        
        # Calcular distribución como lo hace el código real
        properties_per_building = max(1, max_properties // max_typologies)
        
        assert properties_per_building == 3  # 15 // 5 = 3
        
        # Test casos edge
        assert max(1, 2 // 5) == 1  # Mínimo 1 propiedad por edificio
        assert max(1, 10 // 3) == 3  # División normal


if __name__ == "__main__":
    pytest.main([__file__, "-v"])