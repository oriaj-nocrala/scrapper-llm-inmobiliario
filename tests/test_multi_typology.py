#!/usr/bin/env python3
"""
Test script para la nueva funcionalidad de multi-tipología.
Permite probar --max-typologies flag.
"""

import argparse
import logging
from src.scraper.services.scraper_manager import ScrapingConfig, ScraperManager

logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser(description="Test scraper con soporte multi-tipología")
    parser.add_argument("--max-properties", type=int, default=10, 
                       help="Máximo número de propiedades a extraer (default: 10)")
    parser.add_argument("--max-typologies", type=int, default=None,
                       help="Máximo número de tipologías/edificios a procesar (default: None)")
    parser.add_argument("--debug", action="store_true",
                       help="Activar modo debug con browser visible")
    parser.add_argument("--behavior", choices=["extreme", "fast", "normal"], default="extreme",
                       help="Modo de comportamiento (default: extreme)")
    
    args = parser.parse_args()
    
    # Configurar scraping
    config = ScrapingConfig(
        max_properties=args.max_properties,
        max_typologies=args.max_typologies,
        behavior_mode=args.behavior,
        debug_mode=args.debug,
        save_raw_data=True
    )
    
    print(f"🚀 Iniciando scraper con configuración:")
    print(f"   • Max propiedades: {args.max_properties}")
    print(f"   • Max tipologías: {args.max_typologies if args.max_typologies else 'Ilimitado'}")
    print(f"   • Modo: {args.behavior}")
    print(f"   • Debug: {args.debug}")
    
    if args.max_typologies and args.max_typologies > 1:
        print(f"🏢 MODO MULTI-TIPOLOGÍA activado: extraerá de {args.max_typologies} edificios diferentes")
    else:
        print(f"🏠 Modo estándar: extraerá de un solo edificio hasta {args.max_properties} props")
    
    try:
        with ScraperManager(config) as manager:
            collection = manager.scrape_properties(
                base_url="https://www.assetplan.cl/arriendo/departamento"
            )
        
        print(f"\n✅ Scraping completado:")
        print(f"   • Total propiedades: {collection.total_count}")
        print(f"   • Total tipologías: {len(collection.typologies)}")
        print(f"   • Fuente: {collection.source_url}")
        print(f"   • Guardado en: data/properties.json")
        
        # Mostrar estadísticas por tipología
        if collection.typologies:
            print(f"\n📊 Tipologías encontradas:")
            for typology_id, typology in collection.typologies.items():
                props_count = sum(1 for p in collection.properties if p.typology_id == typology_id)
                print(f"   • {typology.name}: {props_count} propiedades, {len(typology.images)} imágenes")
        
        return collection
        
    except Exception as e:
        print(f"❌ Error durante scraping: {e}")
        return None

if __name__ == "__main__":
    collection = main()
    if collection:
        print(f"\n🎉 ¡Proceso exitoso! {collection.total_count} propiedades extraídas")
    else:
        print(f"\n💥 Proceso falló")