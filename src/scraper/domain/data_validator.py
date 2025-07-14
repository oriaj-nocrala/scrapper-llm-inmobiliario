"""
Data validator for property information with business rules and cleaning.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ..models import Property

logger = logging.getLogger(__name__)


class PropertyDataValidator:
    """Validator for property data with cleaning and business rules."""
    
    # Business rules for validation
    MIN_PRICE_UF = 50
    MAX_PRICE_UF = 50000
    MIN_AREA_M2 = 10
    MAX_AREA_M2 = 2000
    MIN_BEDROOMS = 0
    MAX_BEDROOMS = 10
    MIN_BATHROOMS = 0
    MAX_BATHROOMS = 10
    
    # Valid property types
    VALID_PROPERTY_TYPES = {
        'Departamento', 'Casa', 'Oficina', 'Local Comercial', 'Estacionamiento'
    }
    
    # Santiago communes for location validation
    VALID_COMMUNES = {
        'Santiago', 'Providencia', 'Las Condes', 'Ñuñoa', 'Vitacura',
        'La Reina', 'Maipú', 'San Miguel', 'La Florida', 'Puente Alto',
        'Macul', 'Peñalolén', 'Huechuraba', 'Independencia', 'Recoleta',
        'Estación Central', 'Quinta Normal', 'Lo Barnechea', 'Colina',
        'Pudahuel', 'Cerrillos', 'Pedro Aguirre Cerda', 'Lo Espejo',
        'San Joaquín', 'San Ramón', 'La Cisterna', 'El Bosque'
    }
    
    def __init__(self):
        """Initialize the validator."""
        self.validation_errors: List[str] = []
        
    def validate_and_clean_property(self, property_obj: Property) -> Tuple[Property, List[str]]:
        """Validate and clean a property object.
        
        Args:
            property_obj: Property object to validate
            
        Returns:
            Tuple of (cleaned_property, validation_errors)
        """
        self.validation_errors = []
        
        # Clean and validate each field
        cleaned_data = {
            'title': self._clean_title(property_obj.title),
            'price': self._clean_price(property_obj.price),
            'price_uf': self._validate_price_uf(property_obj.price_uf),
            'location': self._clean_location(property_obj.location),
            'area_m2': self._validate_area(property_obj.area_m2),
            'bedrooms': self._validate_bedrooms(property_obj.bedrooms),
            'bathrooms': self._validate_bathrooms(property_obj.bathrooms),
            'property_type': self._validate_property_type(property_obj.property_type),
            'url': self._validate_url(property_obj.url),
            'images': self._clean_images(property_obj.images),
            'description': self._clean_description(property_obj.description),
            'id': property_obj.id
        }
        
        # Create cleaned property
        try:
            cleaned_property = Property(**cleaned_data)
        except Exception as e:
            self.validation_errors.append(f"Failed to create property object: {e}")
            # Return original if cleaning failed
            return property_obj, self.validation_errors
        
        return cleaned_property, self.validation_errors
    
    def _clean_title(self, title: Optional[str]) -> str:
        """Clean and validate title."""
        if not title:
            self.validation_errors.append("Title is missing")
            return "Property"
        
        # Clean whitespace and normalize
        title = re.sub(r'\s+', ' ', title.strip())
        
        # Remove common noise words at the beginning
        noise_patterns = [
            r'^(ARRIENDO|VENTA|ALQUILER)\s*',
            r'^(SIN AVAL|CON AVAL)\s*',
            r'^(PET FRIENDLY)\s*'
        ]
        
        for pattern in noise_patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()
        
        # Validate length
        if len(title) < 3:
            self.validation_errors.append("Title too short")
            return "Property"
        
        if len(title) > 200:
            title = title[:200] + "..."
            self.validation_errors.append("Title truncated (too long)")
        
        return title
    
    def _clean_price(self, price: Optional[str]) -> Optional[str]:
        """Clean price string."""
        if not price:
            return None
        
        # Clean whitespace and normalize
        price = re.sub(r'\s+', ' ', price.strip())
        
        # Remove extra characters but keep essential info
        # Keep: numbers, dots, commas, $, UF, -
        price = re.sub(r'[^\d.,\$UF\-\s]', '', price, flags=re.IGNORECASE)
        
        # Validate format
        if not re.search(r'[\d\$UF]', price, re.IGNORECASE):
            self.validation_errors.append("Invalid price format")
            return None
        
        return price.strip()
    
    def _validate_price_uf(self, price_uf: Optional[float]) -> Optional[float]:
        """Validate UF price."""
        if price_uf is None:
            return None
        
        try:
            price_uf = float(price_uf)
        except (ValueError, TypeError):
            self.validation_errors.append("Invalid UF price format")
            return None
        
        if price_uf < self.MIN_PRICE_UF:
            self.validation_errors.append(f"UF price too low: {price_uf}")
            return None
        
        if price_uf > self.MAX_PRICE_UF:
            self.validation_errors.append(f"UF price too high: {price_uf}")
            return None
        
        return round(price_uf, 2)
    
    def _clean_location(self, location: Optional[str]) -> Optional[str]:
        """Clean and validate location."""
        if not location:
            return None
        
        # Clean whitespace
        location = re.sub(r'\s+', ' ', location.strip())
        
        # Extract commune name if present
        location_upper = location.upper()
        for commune in self.VALID_COMMUNES:
            if commune.upper() in location_upper:
                return commune
        
        # If no exact match, return cleaned location
        if len(location) > 3:
            return location[:100]  # Limit length
        
        return None
    
    def _validate_area(self, area_m2: Optional[float]) -> Optional[float]:
        """Validate area in square meters."""
        if area_m2 is None:
            return None
        
        try:
            area_m2 = float(area_m2)
        except (ValueError, TypeError):
            self.validation_errors.append("Invalid area format")
            return None
        
        if area_m2 < self.MIN_AREA_M2:
            self.validation_errors.append(f"Area too small: {area_m2} m²")
            return None
        
        if area_m2 > self.MAX_AREA_M2:
            self.validation_errors.append(f"Area too large: {area_m2} m²")
            return None
        
        return round(area_m2, 1)
    
    def _validate_bedrooms(self, bedrooms: Optional[int]) -> Optional[int]:
        """Validate number of bedrooms."""
        if bedrooms is None:
            return None
        
        try:
            bedrooms = int(bedrooms)
        except (ValueError, TypeError):
            self.validation_errors.append("Invalid bedrooms format")
            return None
        
        if bedrooms < self.MIN_BEDROOMS:
            self.validation_errors.append(f"Invalid bedrooms count: {bedrooms}")
            return None
        
        if bedrooms > self.MAX_BEDROOMS:
            self.validation_errors.append(f"Too many bedrooms: {bedrooms}")
            return None
        
        return bedrooms
    
    def _validate_bathrooms(self, bathrooms: Optional[int]) -> Optional[int]:
        """Validate number of bathrooms."""
        if bathrooms is None:
            return None
        
        try:
            bathrooms = int(bathrooms)
        except (ValueError, TypeError):
            self.validation_errors.append("Invalid bathrooms format")
            return None
        
        if bathrooms < self.MIN_BATHROOMS:
            self.validation_errors.append(f"Invalid bathrooms count: {bathrooms}")
            return None
        
        if bathrooms > self.MAX_BATHROOMS:
            self.validation_errors.append(f"Too many bathrooms: {bathrooms}")
            return None
        
        return bathrooms
    
    def _validate_property_type(self, property_type: Optional[str]) -> str:
        """Validate and normalize property type."""
        if not property_type:
            return "Departamento"  # Default
        
        property_type = property_type.strip()
        
        # Normalize common variations
        property_type_map = {
            'depto': 'Departamento',
            'dpto': 'Departamento',
            'apartment': 'Departamento',
            'house': 'Casa',
            'office': 'Oficina',
            'commercial': 'Local Comercial',
            'parking': 'Estacionamiento'
        }
        
        property_type_lower = property_type.lower()
        for key, value in property_type_map.items():
            if key in property_type_lower:
                return value
        
        # Check if it's in valid types
        if property_type in self.VALID_PROPERTY_TYPES:
            return property_type
        
        # Default fallback
        self.validation_errors.append(f"Unknown property type: {property_type}")
        return "Departamento"
    
    def _validate_url(self, url: str) -> str:
        """Validate property URL."""
        if not url:
            self.validation_errors.append("URL is missing")
            return ""
        
        try:
            parsed = urlparse(str(url))
            if not parsed.scheme or not parsed.netloc:
                self.validation_errors.append("Invalid URL format")
                return str(url)
        except Exception:
            self.validation_errors.append("URL parsing failed")
        
        return str(url)
    
    def _clean_images(self, images: Optional[List[str]]) -> List[str]:
        """Clean and validate image URLs."""
        if not images:
            return []
        
        cleaned_images = []
        for img_url in images:
            if self._is_valid_image_url(img_url):
                cleaned_images.append(img_url)
            else:
                self.validation_errors.append(f"Invalid image URL: {img_url}")
        
        return cleaned_images[:10]  # Limit to 10 images
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL is a valid image URL."""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Check for common image extensions
            path_lower = parsed.path.lower()
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
            
            # Either has extension or is from known image domain
            has_extension = any(path_lower.endswith(ext) for ext in image_extensions)
            is_image_domain = any(domain in parsed.netloc for domain in ['image', 'photo', 'img'])
            
            return has_extension or is_image_domain or 'image' in url.lower()
            
        except Exception:
            return False
    
    def _clean_description(self, description: Optional[str]) -> Optional[str]:
        """Clean property description."""
        if not description:
            return None
        
        # Clean whitespace
        description = re.sub(r'\s+', ' ', description.strip())
        
        # Remove excessive newlines
        description = re.sub(r'\n{3,}', '\n\n', description)
        
        # Limit length
        if len(description) > 1000:
            description = description[:1000] + "..."
            self.validation_errors.append("Description truncated (too long)")
        
        # Check minimum length
        if len(description) < 10:
            return None
        
        return description


class PropertyCollectionValidator:
    """Validator for collections of properties."""
    
    def __init__(self):
        """Initialize the collection validator."""
        self.property_validator = PropertyDataValidator()
    
    def validate_collection(self, properties: List[Property]) -> Tuple[List[Property], Dict[str, Any]]:
        """Validate a collection of properties.
        
        Args:
            properties: List of Property objects
            
        Returns:
            Tuple of (cleaned_properties, validation_summary)
        """
        cleaned_properties = []
        all_errors = []
        duplicate_urls = set()
        seen_urls = set()
        
        for i, prop in enumerate(properties):
            # Check for duplicates
            url_str = str(prop.url)
            if url_str in seen_urls:
                duplicate_urls.add(url_str)
                continue
            seen_urls.add(url_str)
            
            # Validate individual property
            cleaned_prop, errors = self.property_validator.validate_and_clean_property(prop)
            
            if errors:
                all_errors.extend([f"Property {i+1}: {error}" for error in errors])
            
            cleaned_properties.append(cleaned_prop)
        
        # Generate summary
        summary = {
            'total_properties': len(properties),
            'cleaned_properties': len(cleaned_properties),
            'duplicates_removed': len(duplicate_urls),
            'total_errors': len(all_errors),
            'error_details': all_errors[:20],  # Limit to first 20 errors
            'data_quality_score': self._calculate_quality_score(cleaned_properties)
        }
        
        return cleaned_properties, summary
    
    def _calculate_quality_score(self, properties: List[Property]) -> float:
        """Calculate data quality score (0-100).
        
        Args:
            properties: List of cleaned properties
            
        Returns:
            Quality score percentage
        """
        if not properties:
            return 0.0
        
        total_score = 0
        for prop in properties:
            score = 0
            max_score = 10
            
            # Title quality (2 points)
            if prop.title and len(prop.title) > 10:
                score += 2
            elif prop.title:
                score += 1
            
            # Price information (2 points)
            if prop.price_uf:
                score += 2
            elif prop.price:
                score += 1
            
            # Location (1 point)
            if prop.location:
                score += 1
            
            # Area (1 point)
            if prop.area_m2:
                score += 1
            
            # Room information (2 points)
            if prop.bedrooms is not None:
                score += 1
            if prop.bathrooms is not None:
                score += 1
            
            # Images (1 point)
            if prop.images:
                score += 1
            
            # Description (1 point)
            if prop.description and len(prop.description) > 20:
                score += 1
            
            total_score += (score / max_score) * 100
        
        return round(total_score / len(properties), 2)


class DataQualityReporter:
    """Generate data quality reports."""
    
    @staticmethod
    def generate_report(properties: List[Property], validation_summary: Dict[str, Any]) -> str:
        """Generate a comprehensive data quality report.
        
        Args:
            properties: List of properties
            validation_summary: Validation summary
            
        Returns:
            Formatted report string
        """
        if not properties:
            return "No properties to analyze."
        
        # Calculate field completion rates
        total = len(properties)
        completion_rates = {
            'title': sum(1 for p in properties if p.title and len(p.title) > 3) / total * 100,
            'price': sum(1 for p in properties if p.price) / total * 100,
            'price_uf': sum(1 for p in properties if p.price_uf) / total * 100,
            'location': sum(1 for p in properties if p.location) / total * 100,
            'area_m2': sum(1 for p in properties if p.area_m2) / total * 100,
            'bedrooms': sum(1 for p in properties if p.bedrooms is not None) / total * 100,
            'bathrooms': sum(1 for p in properties if p.bathrooms is not None) / total * 100,
            'images': sum(1 for p in properties if p.images) / total * 100,
            'description': sum(1 for p in properties if p.description and len(p.description) > 20) / total * 100
        }
        
        report = f"""
=== DATA QUALITY REPORT ===

Total Properties: {total}
Data Quality Score: {validation_summary.get('data_quality_score', 0):.1f}/100

FIELD COMPLETION RATES:
{'Field':<15} {'Rate':<8} {'Bar':<20}
{'-'*45}
"""
        
        for field, rate in completion_rates.items():
            bar_length = int(rate / 5)  # Scale to 20 chars
            bar = '█' * bar_length + '░' * (20 - bar_length)
            report += f"{field:<15} {rate:>6.1f}% {bar}\n"
        
        report += f"""
VALIDATION SUMMARY:
- Total Errors: {validation_summary.get('total_errors', 0)}
- Duplicates Removed: {validation_summary.get('duplicates_removed', 0)}
- Success Rate: {(1 - validation_summary.get('total_errors', 0) / max(1, total)) * 100:.1f}%
"""
        
        if validation_summary.get('error_details'):
            report += "\nSAMPLE ERRORS:\n"
            for error in validation_summary['error_details'][:5]:
                report += f"- {error}\n"
        
        return report