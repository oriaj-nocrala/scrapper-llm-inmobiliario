"""
Data Parser para AssetPlan Extractor.
Maneja el parsing y validación de todos los datos extraídos.
"""
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DataParser:
    """Parser especializado para datos de AssetPlan."""
    
    def __init__(self):
        """Initialize data parser."""
        pass
    
    def parse_price_uf(self, price_text: str) -> Optional[float]:
        """Parse UF price from text.
        
        Args:
            price_text: Raw price text
            
        Returns:
            Price in UF as float, or None if not found
        """
        if not price_text:
            return None
            
        try:
            # Clean the text
            clean_text = price_text.replace(',', '').replace('.', '').replace(' ', '').upper()
            
            # Extract UF value
            uf_patterns = [
                r'UF\s*([0-9]+)',
                r'([0-9]+)\s*UF',
                r'DESDE\s*UF\s*([0-9]+)',
                r'([0-9]+)\s*HASTA'
            ]
            
            for pattern in uf_patterns:
                match = re.search(pattern, clean_text)
                if match:
                    return float(match.group(1))
            
            # Try to extract any number if UF is mentioned
            if 'UF' in clean_text:
                numbers = re.findall(r'([0-9]+)', clean_text)
                if numbers:
                    return float(numbers[0])
                    
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error parsing UF price '{price_text}': {e}")
            
        return None
    
    def parse_area(self, area_text: str) -> Optional[float]:
        """Parse area from text.
        
        Args:
            area_text: Raw area text
            
        Returns:
            Area in m² as float, or None if not found
        """
        if not area_text:
            return None
            
        try:
            # Clean the text
            clean_text = area_text.replace(',', '.').replace(' ', '')
            
            # Extract area value
            area_patterns = [
                r'([0-9]+(?:\.[0-9]+)?)\s*m[²2]',
                r'([0-9]+(?:\.[0-9]+)?)\s*mt[²2]',
                r'([0-9]+(?:\.[0-9]+)?)\s*metros'
            ]
            
            for pattern in area_patterns:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    return float(match.group(1))
                    
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error parsing area '{area_text}': {e}")
            
        return None
    
    def parse_bedrooms(self, bedrooms_text: str) -> Optional[int]:
        """Parse number of bedrooms from text.
        
        Args:
            bedrooms_text: Raw bedrooms text
            
        Returns:
            Number of bedrooms as int, or None if not found
        """
        if not bedrooms_text:
            return None
            
        try:
            # Extract bedroom count
            bedroom_patterns = [
                r'([0-9]+)\s*dormitorios?',
                r'([0-9]+)\s*habitaciones?',
                r'([0-9]+)\s*d\b',
                r'([0-9]+)\s*hab\b'
            ]
            
            for pattern in bedroom_patterns:
                match = re.search(pattern, bedrooms_text.lower())
                if match:
                    return int(match.group(1))
                    
            # Look for just numbers if context suggests bedrooms
            if any(word in bedrooms_text.lower() for word in ['dorm', 'hab', 'bed']):
                numbers = re.findall(r'([0-9]+)', bedrooms_text)
                if numbers:
                    return int(numbers[0])
                    
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error parsing bedrooms '{bedrooms_text}': {e}")
            
        return None
    
    def parse_bathrooms(self, bathrooms_text: str) -> Optional[int]:
        """Parse number of bathrooms from text.
        
        Args:
            bathrooms_text: Raw bathrooms text
            
        Returns:
            Number of bathrooms as int, or None if not found
        """
        if not bathrooms_text:
            return None
            
        try:
            # Extract bathroom count
            bathroom_patterns = [
                r'([0-9]+)\s*baños?',
                r'([0-9]+)\s*b\b',
                r'([0-9]+)\s*bath'
            ]
            
            for pattern in bathroom_patterns:
                match = re.search(pattern, bathrooms_text.lower())
                if match:
                    return int(match.group(1))
                    
            # Look for just numbers if context suggests bathrooms
            if any(word in bathrooms_text.lower() for word in ['baño', 'bath', 'wc']):
                numbers = re.findall(r'([0-9]+)', bathrooms_text)
                if numbers:
                    return int(numbers[0])
                    
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error parsing bathrooms '{bathrooms_text}': {e}")
            
        return None
    
    def parse_units_count(self, units_text: str) -> Optional[int]:
        """Parse number of units from text.
        
        Args:
            units_text: Raw units text
            
        Returns:
            Number of units as int, or None if not found
        """
        if not units_text:
            return None
            
        try:
            # Extract units count
            units_patterns = [
                r'([0-9]+)\s*unidades?',
                r'([0-9]+)\s*departamentos?',
                r'([0-9]+)\s*disponibles?'
            ]
            
            for pattern in units_patterns:
                match = re.search(pattern, units_text.lower())
                if match:
                    return int(match.group(1))
                    
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error parsing units count '{units_text}': {e}")
            
        return None
    
    def extract_floor_from_unit_number(self, unit_number: str) -> Optional[int]:
        """Extract floor number from unit number.
        
        Args:
            unit_number: Unit number (e.g., "1011-A", "0515-B")
            
        Returns:
            Floor number as int, or None if not found
        """
        if not unit_number:
            return None
            
        try:
            # Remove any non-digit characters except for the first part
            clean_unit = re.sub(r'[^0-9-]', '', str(unit_number))
            
            # Extract the first part (before any dash)
            unit_part = clean_unit.split('-')[0]
            
            if len(unit_part) >= 3:
                # For units like "1011", "0515", extract first 1-2 digits as floor
                if unit_part.startswith('0'):
                    # Remove leading zero and take first digit(s)
                    floor_digits = unit_part[1:3]
                else:
                    # Take first 1-2 digits
                    floor_digits = unit_part[:-2] if len(unit_part) > 2 else unit_part
                
                return int(floor_digits) if floor_digits else None
                
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error extracting floor from unit '{unit_number}': {e}")
            
        return None
    
    def extract_property_id_from_url(self, url: str) -> Optional[str]:
        """Extract property ID from URL.
        
        Args:
            url: Property URL
            
        Returns:
            Property ID as string, or None if not found
        """
        if not url:
            return None
            
        try:
            # Extract ID from various URL patterns
            id_patterns = [
                r'/departamento/([^/]+)',
                r'/propiedad/([^/]+)',
                r'id=([^&]+)',
                r'/([0-9]+)/?$'
            ]
            
            for pattern in id_patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
                    
        except Exception as e:
            logger.debug(f"Error extracting property ID from URL '{url}': {e}")
            
        return None
    
    def generate_typology_id(self, bedrooms: Optional[int], bathrooms: Optional[int], 
                           area_m2: Optional[float]) -> str:
        """Generate typology ID from characteristics.
        
        Args:
            bedrooms: Number of bedrooms
            bathrooms: Number of bathrooms
            area_m2: Area in square meters
            
        Returns:
            Typology ID string
        """
        bed_str = f"bed{bedrooms}" if bedrooms is not None else "bedN"
        bath_str = f"bath{bathrooms}" if bathrooms is not None else "bathN"
        area_str = f"area{int(area_m2)}" if area_m2 is not None else "areaN"
        
        return f"{bed_str}_{bath_str}_{area_str}"
    
    def is_valid_department_url(self, url: str) -> bool:
        """Check if URL is a valid department URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if valid department URL
        """
        if not url:
            return False
            
        valid_patterns = [
            r'/departamento/',
            r'/propiedad/',
            r'AssetPlan\.cl.*departamento'
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in valid_patterns)
    
    def validate_building_data(self, building_data: Dict[str, Any]) -> bool:
        """Validate building data.
        
        Args:
            building_data: Building data dictionary
            
        Returns:
            True if data is valid
        """
        required_fields = ['name', 'url']
        
        # Check required fields
        for field in required_fields:
            if not building_data.get(field):
                return False
        
        # Validate URL
        url = building_data.get('url', '')
        if not self.is_valid_department_url(url):
            return False
        
        return True