from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class PropertyTypology(BaseModel):
    """Data model for a property typology (conjunto de unidades con mismas características)."""
    
    typology_id: str = Field(..., description="Unique identifier for the typology")
    name: str = Field(..., description="Typology name (e.g., 'Estudio', 'Departamento 1D+1B')")
    area_m2: Optional[float] = Field(None, description="Area in square meters")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, description="Number of bathrooms")
    property_type: Optional[str] = Field(None, description="Type of property (apartment, house, etc.)")
    images: List[str] = Field(default_factory=list, description="List of image URLs for this typology")
    description: Optional[str] = Field(None, description="Typology description")
    building_name: Optional[str] = Field(None, description="Building name")
    building_location: Optional[str] = Field(None, description="Building location/address")
    

class Property(BaseModel):
    """Data model for a real estate property."""
    
    id: Optional[str] = Field(None, description="Unique identifier for the property")
    title: str = Field(..., description="Property title/name")
    price: Optional[str] = Field(None, description="Property price")
    price_uf: Optional[float] = Field(None, description="Price in UF (if available)")
    location: Optional[str] = Field(None, description="Property location/address")
    area_m2: Optional[float] = Field(None, description="Area in square meters")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, description="Number of bathrooms")
    property_type: Optional[str] = Field(None, description="Type of property (apartment, house, etc.)")
    url: HttpUrl = Field(..., description="Original property URL")
    typology_id: Optional[str] = Field(None, description="Reference to PropertyTypology ID")
    unit_number: Optional[str] = Field(None, description="Specific unit number/identifier")
    floor: Optional[int] = Field(None, description="Floor number")
    images: List[str] = Field(default_factory=list, description="Unit-specific images (if any)")
    description: Optional[str] = Field(None, description="Property description")
    
    model_config = {
        "json_encoders": {HttpUrl: str}
    }


class PropertyCollection(BaseModel):
    """Collection of properties with metadata and optimized typology storage."""
    
    properties: List[Property] = Field(default_factory=list)
    typologies: Dict[str, PropertyTypology] = Field(default_factory=dict, description="Typologies indexed by ID")
    total_count: int = Field(0, description="Total number of properties")
    scraped_at: str = Field(..., description="Timestamp when data was scraped")
    source_url: str = Field("https://www.assetplan.cl/", description="Source website")
    
    def add_property_with_typology(self, property_obj: Property, typology: PropertyTypology) -> None:
        """Add a property and its typology, avoiding image duplication."""
        # Store typology if not already present
        if typology.typology_id not in self.typologies:
            self.typologies[typology.typology_id] = typology
        
        # Link property to typology
        property_obj.typology_id = typology.typology_id
        
        # Clear property images to avoid duplication (all images go to typology)
        images_before = len(property_obj.images)
        property_obj.images = []
        
        # Debug log
        if images_before > 0:
            print(f"🗑️ Limpiadas {images_before} imágenes duplicadas de propiedad {property_obj.title}")
        
        self.properties.append(property_obj)
        self.total_count = len(self.properties)
    
    def get_property_images(self, property_obj: Property) -> List[str]:
        """Get all images for a property (typology + unit-specific)."""
        images = []
        
        # Add typology images
        if property_obj.typology_id and property_obj.typology_id in self.typologies:
            images.extend(self.typologies[property_obj.typology_id].images)
        
        # Add unit-specific images
        images.extend(property_obj.images)
        
        return images