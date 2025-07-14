import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from src.scraper.assetplan_scraper import AssetplanScraper
from src.scraper.models import Property, PropertyCollection


class TestAssetplanScraper:
    """Test suite for AssetplanScraper class."""
    
    @pytest.fixture
    def scraper(self):
        """Create a scraper instance for testing."""
        return AssetplanScraper(headless=True)
    
    @pytest.fixture
    @pytest.fixture
    def mock_property_element(self):
        """Create a mock property element with sample data."""
        element = Mock(spec=WebElement)
        
        # Mock link element
        link_element = Mock()
        link_element.get_attribute.return_value = "https://www.assetplan.cl/propiedad/123"
        
        # Mock title element
        title_element = Mock()
        title_element.text = "Departamento 2D/2B en Providencia"
        
        # Mock price element
        price_element = Mock()
        price_element.text = "UF 2.500"
        
        # Mock location element
        location_element = Mock()
        location_element.text = "Providencia, Santiago"
        
        # Mock area element
        area_element = Mock()
        area_element.text = "85 m²"
        
        # Mock bedroom element
        bed_element = Mock()
        bed_element.text = "2 dormitorios"
        
        # Mock bathroom element
        bath_element = Mock()
        bath_element.text = "2 baños"
        
        # Mock type element
        type_element = Mock()
        type_element.text = "Departamento"
        
        # Mock image elements
        img_element = Mock()
        img_element.get_attribute.return_value = "/images/property123.jpg"
        
        # Configure find_element behavior
    def test_scraper_initialization(self, scraper):
        """Test scraper initialization."""
        assert scraper.headless is True
        assert scraper.driver is None
        assert scraper.base_url == "https://www.assetplan.cl"
        assert scraper.properties_url == "https://www.assetplan.cl/propiedades"
    
    @patch('src.scraper.assetplan_scraper.webdriver.Chrome')
    def test_setup_driver(self, mock_chrome, scraper):
        """Test WebDriver setup."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        driver = scraper._setup_driver()
        
        assert driver == mock_driver
        mock_chrome.assert_called_once()
        mock_driver.implicitly_wait.assert_called_once_with(10)
    
    @patch('src.scraper.assetplan_scraper.webdriver.Chrome')
    def test_start_stop_driver(self, mock_chrome, scraper):
        """Test starting and stopping the driver."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Test start driver
        scraper.start_driver()
        assert scraper.driver == mock_driver
        
        # Test stop driver
        scraper.stop_driver()
        mock_driver.quit.assert_called_once()
        assert scraper.driver is None
    
    def test_extract_property_details_success(self, scraper, mock_property_element):
        """Test successful property extraction."""
        property_obj = scraper._extract_property_details(mock_property_element)
        
        assert property_obj is not None
        assert isinstance(property_obj, Property)
        assert property_obj.title == "Departamento 2D/2B en Providencia"
        assert property_obj.price == "UF 2.500"
        assert property_obj.price_uf == 2500.0
        assert property_obj.location == "Providencia, Santiago"
        assert property_obj.area_m2 == 85.0
        assert property_obj.bedrooms == 2
        assert property_obj.bathrooms == 2
        assert property_obj.property_type == "Departamento"
        assert str(property_obj.url) == "https://www.assetplan.cl/propiedad/123"
        assert len(property_obj.images) == 1
    
    def test_extract_property_details_missing_link(self, scraper):
        """Test property extraction with missing link."""
        element = Mock()
        element.find_element.side_effect = NoSuchElementException()
        
        property_obj = scraper._extract_property_details(element)
        assert property_obj is None
    
    def test_extract_property_details_partial_data(self, scraper):
        """Test property extraction with partial data."""
        element = Mock()
        
        # Mock only required elements (link and title)
        link_element = Mock()
        link_element.get_attribute.return_value = "https://example.com/property"
        
        title_element = Mock()
        title_element.text = "Test Property"
        
    @patch('src.scraper.assetplan_scraper.WebDriverWait')
    def test_scrape_properties_success(self, mock_wait, scraper, mock_driver, mock_property_element):
        """Test successful property scraping."""
        scraper.driver = mock_driver
        
        # Mock WebDriverWait
        mock_wait.return_value.until.return_value = True
        
        # Mock finding property elements
        mock_driver.find_elements.return_value = [mock_property_element, mock_property_element]
        
        # Mock the property extraction
        with patch.object(scraper, '_extract_property_details') as mock_extract:
            mock_property = Property(
                title="Test Property",
                url="https://example.com/property"
            )
            mock_extract.return_value = mock_property
            
            collection = scraper.scrape_properties(max_properties=2)
            
            assert isinstance(collection, PropertyCollection)
            assert collection.total_count == 2
            assert len(collection.properties) == 2
            assert collection.source_url == "https://www.assetplan.cl"
    
    @patch('src.scraper.assetplan_scraper.WebDriverWait')
    def test_scrape_properties_timeout(self, mock_wait, scraper, mock_driver):
        """Test scraping with timeout exception."""
        scraper.driver = mock_driver
        mock_wait.return_value.until.side_effect = TimeoutException()
        
        collection = scraper.scrape_properties(max_properties=10)
        
        assert isinstance(collection, PropertyCollection)
        assert collection.total_count == 0
        assert len(collection.properties) == 0
    
    @patch('src.scraper.assetplan_scraper.WebDriverWait')
    def test_scrape_properties_no_elements_found(self, mock_wait, scraper, mock_driver):
        """Test scraping when no property elements are found."""
        scraper.driver = mock_driver
        mock_wait.return_value.until.return_value = True
        mock_driver.find_elements.return_value = []
        
        collection = scraper.scrape_properties(max_properties=10)
        
        assert isinstance(collection, PropertyCollection)
        assert collection.total_count == 0
        assert len(collection.properties) == 0
    
    def test_save_to_json(self, scraper):
        """Test saving properties to JSON file."""
        # Create test collection
        properties = [
            Property(title="Property 1", url="https://example.com/1"),
            Property(title="Property 2", url="https://example.com/2")
        ]
        collection = PropertyCollection(
            properties=properties,
            total_count=2,
            scraped_at="2024-01-01T12:00:00",
            source_url="https://test.com"
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        saved_path = scraper.save_to_json(collection, filepath)
        
        assert saved_path == filepath
        
        # Verify file contents
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['total_count'] == 2
        assert len(data['properties']) == 2
        assert data['properties'][0]['title'] == "Property 1"
    
    @patch('src.scraper.assetplan_scraper.webdriver.Chrome')
    def test_property_validation(self):
        """Test property model validation."""
        # Test valid property
        property_obj = Property(
            title="Test Property",
            url="https://example.com/property"
        )
        assert property_obj.title == "Test Property"
        assert str(property_obj.url) == "https://example.com/property"
        
        # Test property with all fields
        property_full = Property(
            title="Full Property",
            price="UF 3000",
            price_uf=3000.0,
            location="Las Condes",
            area_m2=120.5,
            bedrooms=3,
            bathrooms=2,
            property_type="Casa",
            url="https://example.com/full",
            images=["img1.jpg", "img2.jpg"],
            description="Beautiful property"
        )
        assert property_full.bedrooms == 3
        assert property_full.area_m2 == 120.5
        assert len(property_full.images) == 2
    
class TestScraperIntegration:
    """Integration tests for the scraper."""
    
    @pytest.mark.integration
    def test_scraper_minimum_properties(self):
        """Test that scraper can extract minimum required properties."""
        with AssetplanScraper(headless=True) as scraper:
            collection = scraper.scrape_properties(max_properties=5)
            
            # Assert we got some properties (at least 1)
            assert collection.total_count >= 1
            assert len(collection.properties) >= 1
            
            # Check that each property has required fields
            for prop in collection.properties:
                assert prop.title is not None
                assert prop.url is not None
                assert str(prop.url).startswith("http")
    
    @pytest.mark.integration
    def test_scraper_data_quality(self):
        """Test the quality of scraped data."""
        with AssetplanScraper(headless=True) as scraper:
            collection = scraper.scrape_properties(max_properties=3)
            
            if collection.total_count > 0:
                prop = collection.properties[0]
                
                # Check URL format
                assert str(prop.url).startswith("http")
                
                # Check title is not empty
                assert len(prop.title.strip()) > 0
                
                # If price exists, check format
                if prop.price:
                    assert len(prop.price.strip()) > 0
                
                # If numeric fields exist, check they're positive
                if prop.price_uf:
                    assert prop.price_uf > 0
                if prop.area_m2:
                    assert prop.area_m2 > 0
                if prop.bedrooms:
                    assert prop.bedrooms > 0
                if prop.bathrooms:
                    assert prop.bathrooms > 0