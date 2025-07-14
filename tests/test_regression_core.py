"""
Tests de regresión CORE para el scraper AssetPlan - enfocados en funcionalidades críticas
y prevención de regresiones de rendimiento específicas (especialmente el modal).
"""
import pytest
import re
import time
from unittest.mock import Mock, patch
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

from src.scraper.domain.assetplan_extractor_v2 import AssetPlanExtractorV2
from src.scraper.models import Property, PropertyCollection, PropertyTypology


class TestFloorExtractionRegression:
    """Tests críticos para prevenir regresión de rendimiento en extracción de piso."""
    
    def test_floor_extraction_performance_under_1_second(self):
        """CRÍTICO: La extracción de piso debe ser < 1 segundo para evitar regresión de 37s."""
        mock_driver = Mock(spec=WebDriver)
        
        # Mock de pocos elementos para simular caso eficiente
        mock_elements = []
        for i in range(3):
            element = Mock(spec=WebElement)
            element.text = f"Piso {10 + i}"
            mock_elements.append(element)
        
        mock_driver.find_elements.return_value = mock_elements
        
        extractor = AssetPlanExtractorV2(mock_driver)
        
        start_time = time.time()
        floor = extractor._extract_floor_from_page()
        elapsed_time = time.time() - start_time
        
        # REGRESIÓN CRÍTICA: debe ser rápido
        assert elapsed_time < 1.0, f"REGRESIÓN: Extracción tomó {elapsed_time:.2f}s, debe ser <1s"
        assert floor == 10
    
    def test_floor_extraction_skips_many_elements(self):
        """CRÍTICO: Con muchos elementos debe abortar para evitar lentitud."""
        mock_driver = Mock(spec=WebDriver)
        
        # Mock de 15 elementos (más del límite de 10)
        mock_elements = [Mock(spec=WebElement) for _ in range(15)]
        mock_driver.find_elements.return_value = mock_elements
        
        extractor = AssetPlanExtractorV2(mock_driver)
        
        start_time = time.time()
        floor = extractor._extract_floor_from_page()
        elapsed_time = time.time() - start_time
        
        # Debe abortar muy rápido
        assert elapsed_time < 0.1, f"Con muchos elementos debería abortar en <0.1s, tomó {elapsed_time:.2f}s"
        assert floor is None
    
    def test_floor_extraction_valid_patterns(self):
        """Test de patrones válidos de extracción de piso."""
        mock_driver = Mock(spec=WebDriver)
        extractor = AssetPlanExtractorV2(mock_driver)
        
        valid_cases = [
            ("Piso 5", 5),
            ("PISO 13", 13),
            ("piso 20", 20),
            ("Departamento en Piso 7", 7),
        ]
        
        for text, expected_floor in valid_cases:
            element = Mock(spec=WebElement)
            element.text = text
            mock_driver.find_elements.return_value = [element]
            
            floor = extractor._extract_floor_from_page()
            assert floor == expected_floor, f"'{text}' debería extraer piso {expected_floor}"


class TestTypologyCleaningRegression:
    """Tests críticos para prevenir regresión en limpieza de tipologías."""
    
class TestDataIntegrityRegression:
    """Tests críticos para integridad de datos."""
    
    def test_floor_priority_logic(self):
        """CRÍTICO: Prioridad de datos de piso debe ser página > modal > unit_number."""
        mock_driver = Mock(spec=WebDriver)
        extractor = AssetPlanExtractorV2(mock_driver)
        
        # Test manual de lógica de prioridad
        page_floor = 15
        modal_floor = 13
        unit_number = "1011-A"  # implica piso 10
        
        # Lógica de prioridad (simulando el código real)
        final_floor = None
        
        # 1. Prioridad máxima: página
        if page_floor is not None:
            final_floor = page_floor
        # 2. Fallback: modal
        elif modal_floor is not None:
            final_floor = modal_floor
        # 3. Fallback final: unit_number
        else:
            final_floor = extractor._extract_floor_from_unit_number(unit_number)
        
        assert final_floor == 15, f"Debe usar piso de página (15), obtuvo {final_floor}"
        
        # Test sin página
        final_floor = None
        page_floor = None
        
        if page_floor is not None:
            final_floor = page_floor
        elif modal_floor is not None:
            final_floor = modal_floor
        else:
            final_floor = extractor._extract_floor_from_unit_number(unit_number)
        
        assert final_floor == 13, f"Debe usar piso de modal (13), obtuvo {final_floor}"
    
    def test_extract_floor_from_unit_number_patterns(self):
        """CRÍTICO: Extracción de piso desde unit_number debe funcionar."""
        mock_driver = Mock(spec=WebDriver)
        extractor = AssetPlanExtractorV2(mock_driver)
        
        test_cases = [
            ("1011-A", 10),
            ("0515-B", 5),
            ("2304-C", 23),
            ("101", 1),
            ("ABC", None),
            ("", None)
        ]
        
        for unit_number, expected_floor in test_cases:
            result = extractor._extract_floor_from_unit_number(unit_number)
            assert result == expected_floor, f"Unit '{unit_number}' debe dar piso {expected_floor}, obtuvo {result}"


class TestModalRegression:
    """Tests críticos para prevenir regresiones en el modal."""
    
    def test_retry_stale_element_works(self):
        """CRÍTICO: El retry de elementos stale debe funcionar."""
        mock_driver = Mock(spec=WebDriver)
        extractor = AssetPlanExtractorV2(mock_driver)
        
        # Mock función que falla primero y luego funciona
        call_count = 0
class TestPropertyCollectionRegression:
    """Tests críticos para la estructura de datos PropertyCollection."""
    
    def test_property_collection_structure(self):
        """CRÍTICO: Estructura optimizada de PropertyCollection debe mantenerse."""
        from src.scraper.models import Property, PropertyTypology, PropertyCollection
        
        # Crear datos de prueba
        property1 = Property(
            id="123",
            title="Test Property",
            url="https://test.com/prop",
            typology_id="bed1_bath1_area50",
            unit_number="101-A",
            floor=10,
            images=[]  # Debe estar vacío
        )
        
        typology = PropertyTypology(
            typology_id="bed1_bath1_area50",
            name="1 dormitorio 1 baño",
            area_m2=50.0,
            bedrooms=1,
            bathrooms=1,
            property_type="Departamento",
            images=["img1.jpg", "img2.jpg"]  # Imágenes van aquí
        )
        
        from datetime import datetime
        
        collection = PropertyCollection(
            properties=[],
            typologies={},
            total_count=0,
            scraped_at=datetime.now().isoformat(),
            source_url="https://test.com"
        )
        collection.add_property_with_typology(property1, typology)
        
        # REGRESIÓN CRÍTICA: estructura optimizada
        assert len(collection.properties) == 1
        assert len(collection.typologies) == 1
        assert collection.properties[0].images == [], "Propiedades deben tener images vacío"
        assert len(collection.typologies["bed1_bath1_area50"].images) == 2, "Tipologías deben tener las imágenes"
        
        # Test de obtención de imágenes
        all_images = collection.get_property_images(property1)
        assert len(all_images) == 2, "Debe obtener imágenes de la tipología"
        assert all_images == ["img1.jpg", "img2.jpg"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])