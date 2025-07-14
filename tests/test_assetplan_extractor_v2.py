"""
Tests de regresión para AssetPlanExtractorV2 - Modal y extracción de datos
Enfocado en prevenir regresiones de rendimiento y funcionalidad crítica.
"""
import pytest
import re
import time
from unittest.mock import Mock, patch, MagicMock, call
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By

from src.scraper.domain.assetplan_extractor_v2 import AssetPlanExtractorV2
from src.scraper.models import Property, PropertyCollection, PropertyTypology


class TestAssetPlanExtractorV2Regression:
    """Tests de regresión para funcionalidades críticas del extractor V2."""
    
    @pytest.fixture
    def mock_driver(self):
        """Mock del WebDriver con comportamientos básicos."""
        driver = Mock(spec=WebDriver)
        driver.get = Mock()
        driver.quit = Mock()
        driver.find_elements = Mock()
        driver.find_element = Mock()
        driver.execute_script = Mock()
        driver.current_url = "https://www.assetplan.cl/test"
        return driver
    
    @pytest.fixture
    def extractor(self, mock_driver):
        """Instancia del extractor con mock driver."""
        return AssetPlanExtractorV2(mock_driver)
    
    @pytest.fixture
    def mock_modal_elements(self):
        """Mock de elementos del modal con datos de muestra."""
        elements = {}
        
        # Elemento de piso en modal
        piso_element = Mock(spec=WebElement)
        piso_element.text = "Piso 10"
        elements['piso'] = piso_element
        
        # Elemento de unidad en modal  
        unit_element = Mock(spec=WebElement)
        unit_element.text = "Unidad 1011-A"
        elements['unit'] = unit_element
        
        # Elemento de precio en modal
        price_element = Mock(spec=WebElement)
        price_element.text = "$154.414"
        elements['price'] = price_element
        
        return elements


class TestFloorExtraction:
    """Tests específicos para extracción de piso - prevención de regresión de rendimiento."""
    
    @pytest.fixture
    def extractor(self):
        """Extractor con mock driver para tests de piso."""
        mock_driver = Mock(spec=WebDriver)
        mock_driver.find_elements = Mock()
        return AssetPlanExtractorV2(mock_driver)
    
    def test_extract_floor_from_page_performance_regression(self, extractor):
        """Test de regresión: _extract_floor_from_page debe ser rápido (<1 segundo)."""
        # Mock de elementos con texto "Piso"
        mock_elements = []
        for i in range(3):  # Solo pocos elementos para test rápido
            element = Mock(spec=WebElement)
            element.text = f"Piso {10 + i}"
            mock_elements.append(element)
        
        extractor.driver.find_elements.return_value = mock_elements
        
        start_time = time.time()
        floor = extractor._extract_floor_from_page()
        elapsed_time = time.time() - start_time
        
        # Regresión crítica: debe ser rápido
        assert elapsed_time < 1.0, f"Extracción de piso tomó {elapsed_time:.2f}s, debe ser <1s"
        assert floor == 10
    
    def test_extract_floor_from_page_too_many_elements(self, extractor):
        """Test: evitar lentitud con demasiados elementos 'Piso'."""
        # Mock de muchos elementos (más de 10)
        mock_elements = []
        for i in range(15):  # Más del límite
            element = Mock(spec=WebElement)
            element.text = f"Algún texto con Piso {i}"
            mock_elements.append(element)
        
        extractor.driver.find_elements.return_value = mock_elements
        
        start_time = time.time()
        floor = extractor._extract_floor_from_page()
        elapsed_time = time.time() - start_time
        
        # Debe abortar rápidamente y devolver None
        assert elapsed_time < 0.5, f"Debería abortar rápido, tomó {elapsed_time:.2f}s"
        assert floor is None
    
    def test_extract_floor_from_page_valid_patterns(self, extractor):
        """Test: patrones válidos de extracción de piso."""
        test_cases = [
            ("Piso 5", 5),
            ("PISO 13", 13),
            ("piso 20", 20),
            ("Departamento en Piso 7", 7),
            ("Piso   15  ", 15),  # Con espacios
        ]
        
        for text, expected_floor in test_cases:
            # Mock individual para cada caso
            element = Mock(spec=WebElement)
            element.text = text
            extractor.driver.find_elements.return_value = [element]
            
            floor = extractor._extract_floor_from_page()
            assert floor == expected_floor, f"Patrón '{text}' debería extraer piso {expected_floor}"
    
    def test_extract_floor_from_page_invalid_patterns(self, extractor):
        """Test: patrones que NO deben extraer piso."""
        invalid_texts = [
            "Piso de madera",  # No es número
            "Piso muy alto",
            "Edificio de 10 pisos",  # No dice "Piso X"
            "Piso 0",  # Fuera de rango
            "Piso 100",  # Fuera de rango
            "Casa con piso de cerámica",
        ]
        
        for text in invalid_texts:
            element = Mock(spec=WebElement)
            element.text = text
            extractor.driver.find_elements.return_value = [element]
            
            floor = extractor._extract_floor_from_page()
            assert floor is None, f"Texto '{text}' NO debería extraer un piso válido"
    
    def test_extract_floor_from_page_long_text_skip(self, extractor):
        """Test: saltar textos muy largos para mantener rendimiento."""
        # Texto muy largo (>100 caracteres)
        long_text = "Este es un texto muy largo que contiene la palabra Piso 12 pero es demasiado largo para procesarlo eficientemente en el scraper y debería ser saltado"
        
        element = Mock(spec=WebElement)
        element.text = long_text
        extractor.driver.find_elements.return_value = [element]
        
        floor = extractor._extract_floor_from_page()
        assert floor is None  # Debe saltar textos largos
    
    def test_extract_floor_from_page_exception_handling(self, extractor):
        """Test: manejo de excepciones en extracción de piso."""
        # Mock que arroja excepción
        extractor.driver.find_elements.side_effect = Exception("Error de conexión")
        
        floor = extractor._extract_floor_from_page()
        assert floor is None  # Debe manejar excepciones gracefully


class TestTypologyGeneration:
    """Tests para generación de typology_id y limpieza de nombres."""
    
    @pytest.fixture
    def extractor(self):
        """Extractor para tests de tipología."""
        mock_driver = Mock(spec=WebDriver)
        return AssetPlanExtractorV2(mock_driver)
    
    def test_generate_typology_id_clean_newlines(self, extractor):
        """Test: _generate_typology_id debe limpiar caracteres \
."""
        # Data con caracteres \
 problemáticos
        typology_data = {
            'bedrooms': 1,
            'bathrooms': 1, 
            'area_m2': 51.0,
            'rooms_info': '1
dormitorio
1
baño',  # Con \

            'property_type': 'Departamento'
        }
        
        typology_id = extractor._generate_typology_id(typology_data)
        
        # No debe contener \

        assert '
' not in typology_id
        assert typology_id == 'bed1_bath1_area51_1dormitori'
    
    def test_generate_typology_id_consistent_format(self, extractor):
        """Test: formato consistente de typology_id."""
        test_cases = [
            ({
                'bedrooms': 2,
                'bathrooms': 1,
                'area_m2': 65.5,
                'rooms_info': '2 dormitorios 1 baño',
                'property_type': 'Departamento'
            }, 'bed2_bath1_area65_2dormitori'),
            ({
                'bedrooms': 1,
                'bathrooms': 2,
                'area_m2': 45.0,
                'rooms_info': '1 dormitorio 2 baños',
                'property_type': 'Estudio'
            }, 'bed1_bath2_area45_1dormitori'),
        ]
        
        for typology_data, expected_id in test_cases:
            result_id = extractor._generate_typology_id(typology_data)
            assert result_id == expected_id
    
    def test_create_property_typology_clean_name(self, extractor):
        """Test: nombres de tipología sin \
 en PropertyTypology creation."""
        # Test directo de creación de PropertyTypology con datos limpios
        from src.scraper.models import PropertyTypology
        
        # Simular datos con \
 problemáticos
        rooms_info_dirty = '1
dormitorio
1
baño'
        rooms_info_clean = rooms_info_dirty.replace('
', ' ').strip()
        
        # Crear tipología directamente
        typology = PropertyTypology(
            typology_id='test_id',
            name=rooms_info_clean,
            area_m2=51.0,
            bedrooms=1,
            bathrooms=1,
            property_type='Departamento'
        )
        
        # El nombre debe estar limpio
        assert '
' not in typology.name
        assert typology.name == '1 dormitorio 1 baño'
        assert typology.typology_id == 'test_id'


class TestModalInteraction:
    """Tests para interacción con modal - prevención de regresiones de navegación."""
    
    @pytest.fixture
    def extractor_with_behavior(self):
        """Extractor con simulación de comportamiento."""
        mock_driver = Mock(spec=WebDriver)
        mock_behavior = Mock()
        
        extractor = AssetPlanExtractorV2(mock_driver)
        extractor.behavior = mock_behavior
        extractor.wait = Mock()
        extractor.fast_wait = Mock()
        
        return extractor
    
    def test_smart_back_to_modal_performance(self, extractor_with_behavior):
        """Test: navegación de vuelta al modal debe ser rápida."""
        # Mock del método _smart_delay y navegación
        extractor_with_behavior._smart_delay = Mock()
        extractor_with_behavior.driver.back = Mock()
        extractor_with_behavior.wait.until = Mock(return_value=True)
        
        start_time = time.time()
        
        # Simular navegación de vuelta
        extractor_with_behavior._smart_back_to_modal()
        
        elapsed_time = time.time() - start_time
        
        # Debe ser rápido (mock, pero estructura debe ser eficiente)
        assert elapsed_time < 0.1
        
        # Verificar que se llamaron los métodos correctos
        extractor_with_behavior.driver.back.assert_called_once()
    
    def test_extract_unit_from_modal_performance(self, extractor_with_behavior):
        """Test: extracción de unidad desde modal debe ser rápida."""
        # Mock de datos de unidad
        unit_data = {
            'id': '12345',
            'unit_number': '101-A',
            'price': '$150000'
        }
        
        # Mock del método de extracción de página de departamento
        extractor_with_behavior._extract_department_detail_page = Mock(return_value=unit_data)
        extractor_with_behavior._create_property_from_data = Mock(return_value=Mock())
        
        start_time = time.time()
        result = extractor_with_behavior._extract_unit_from_modal(unit_data, {}, {})
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 0.1
        assert result is not None
    
    def test_retry_stale_element_functionality(self, extractor_with_behavior):
        """Test: funcionalidad de retry para elementos stale."""
        # Mock de función que falla con StaleElementReferenceException primero
        def mock_function():
            if not hasattr(mock_function, 'called'):
                mock_function.called = True
                raise StaleElementReferenceException()
            return "success"
        
        # Mock del delay para que no espere
        extractor_with_behavior._smart_delay = Mock()
        
        result = extractor_with_behavior._retry_stale_element(mock_function, max_retries=2, delay=0.01)
        
        assert result == "success"
        # Debe haber llamado _smart_delay una vez por el retry
        extractor_with_behavior._smart_delay.assert_called_once()


class TestDataExtraction:
    """Tests para extracción de datos de páginas de departamento."""
    
    @pytest.fixture
    def extractor_with_page_data(self):
        """Extractor con datos de página mockeados."""
        mock_driver = Mock(spec=WebDriver)
        extractor = AssetPlanExtractorV2(mock_driver)
        
        # Mock de elementos de la página de departamento
        def mock_find_element(by, selector):
            if 'piso' in selector.lower():
                element = Mock(spec=WebElement)
                element.text = "Piso 13"
                return element
            elif 'precio' in selector.lower() or 'price' in selector.lower():
                element = Mock(spec=WebElement)
                element.text = "$155.654"
                return element
            else:
                raise NoSuchElementException()
        
        extractor.driver.find_element.side_effect = mock_find_element
        return extractor
    
    def test_extract_department_detail_page_data(self, extractor_with_page_data):
        """Test: extracción correcta de datos desde página de departamento."""
        # Mock del URL actual
        extractor_with_page_data.driver.current_url = "https://test.com?selectedUnit=12345"
        
        # Simular extracción de datos de la página
        unit_data = extractor_with_page_data._extract_department_detail_page()
        
        # Debe extraer datos básicos
        assert isinstance(unit_data, dict)
        assert 'id' in unit_data
        assert unit_data['id'] == "12345"
    
    def test_extract_property_id_from_url(self, extractor_with_page_data):
        """Test: extracción correcta de ID desde URL."""
        test_urls = [
            ("https://test.com?selectedUnit=12345", "12345"),
            ("https://test.com?other=123&selectedUnit=67890", "67890"),
            ("https://test.com?selectedUnit=", None),
            ("https://test.com", None)
        ]
        
        for url, expected_id in test_urls:
            result_id = extractor_with_page_data._extract_property_id_from_url(url)
            assert result_id == expected_id
    
    def test_extract_floor_from_unit_number(self, extractor_with_page_data):
        """Test: extracción de piso desde número de unidad."""
        test_cases = [
            ("1011-A", 10),
            ("0515-B", 5),
            ("2304-C", 23),
            ("101", 1),
            ("ABC", None),
            ("", None)
        ]
        
        for unit_number, expected_floor in test_cases:
            result_floor = extractor_with_page_data._extract_floor_from_unit_number(unit_number)
            assert result_floor == expected_floor


class TestPropertyCreation:
    """Tests para creación de objetos Property con datos completos."""
    
    @pytest.fixture
    def extractor(self):
        """Extractor básico para tests de creación."""
        mock_driver = Mock(spec=WebDriver)
        return AssetPlanExtractorV2(mock_driver)
    
    def test_create_property_from_data_floor_priority(self, extractor):
        """Test: prioridad correcta de datos de piso (página > modal > unit_number)."""
        unit_data = {
            'id': '495857',
            'title': 'Test Property',
            'unit_number': '1011-A',  # Piso 10 del unit_number
            'url': 'https://test.com/prop'
        }
        
        modal_data = {
            'floor': 13  # Piso del modal
        }
        
        building_data = {
            'building_name': 'Test Building',
            'location': 'Test Location'
        }
        
        page_floor = 15  # Piso de la página (máxima prioridad)
        
        # Mock de _extract_floor_from_page para devolver piso de página
        with patch.object(extractor, '_extract_floor_from_page', return_value=page_floor):
            property_obj = extractor._create_property_from_data(unit_data, modal_data, {}, building_data)
        
        # Debe usar el piso de la página (máxima prioridad)
        assert property_obj.floor == 15
    
    def test_create_property_from_data_floor_fallback(self, extractor):
        """Test: fallback a datos de modal cuando no hay datos de página."""
        unit_data = {
            'id': '495857',
            'title': 'Test Property',
            'unit_number': '1011-A',  # Piso 10 del unit_number
            'url': 'https://test.com/prop'
        }
        
        modal_data = {
            'floor': 13  # Piso del modal
        }
        
        building_data = {
            'building_name': 'Test Building',
            'location': 'Test Location'
        }
        
        # Mock sin piso de página
        with patch.object(extractor, '_extract_floor_from_page', return_value=None):
            property_obj = extractor._create_property_from_data(unit_data, modal_data, {}, building_data)
        
        # Debe usar el piso del modal
        assert property_obj.floor == 13
    
    def test_create_property_from_data_floor_final_fallback(self, extractor):
        """Test: fallback final a unit_number cuando no hay otros datos."""
        unit_data = {
            'id': '495857',
            'title': 'Test Property',
            'unit_number': '1011-A',  # Piso 10 del unit_number
            'url': 'https://test.com/prop'
        }
        
        modal_data = {}  # Sin datos de modal
        
        building_data = {
            'building_name': 'Test Building',
            'location': 'Test Location'
        }
        
        # Mock sin piso de página
        with patch.object(extractor, '_extract_floor_from_page', return_value=None):
            property_obj = extractor._create_property_from_data(unit_data, modal_data, {}, building_data)
        
        # Debe usar el piso parseado del unit_number
        assert property_obj.floor == 10