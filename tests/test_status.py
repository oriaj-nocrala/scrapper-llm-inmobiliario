#!/usr/bin/env python3
"""
Test de estado rápido para verificar funcionalidades clave.
"""
import os
import json
import sys
from pathlib import Path

def test_data_availability():
    """Test que los datos scrapeados estén disponibles."""
    data_file = Path("data/properties.json")
    if not data_file.exists():
        print("❌ Datos no encontrados")
        return False
    
    with open(data_file) as f:
        data = json.load(f)
    
    properties = data.get("properties", [])
    print(f"✅ Datos disponibles: {len(properties)} propiedades")
    
    if len(properties) > 0:
        sample = properties[0]
        has_url = bool(sample.get("url"))
        has_price = bool(sample.get("price"))
        has_location = bool(sample.get("location"))
        
        print(f"   - URLs: {'✅' if has_url else '❌'}")
        print(f"   - Precios: {'✅' if has_price else '❌'}")
        print(f"   - Ubicaciones: {'✅' if has_location else '❌'}")
        
        return has_url and has_price and has_location
    
    return False

def main():
    """Ejecutar todos los tests de estado."""
    print("🔍 TEST DE ESTADO DEL SISTEMA")
    print("=" * 50)
    
    tests = [
        ("Datos scrapeados", test_data_availability)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 {name}:")
        results.append(test_func())
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE ESTADO")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (name, result) in enumerate(zip([t[0] for t in tests], results)):
        status = "✅ OK" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n📈 Estado: {passed}/{total} componentes OK")
    
    if passed == total:
        print("\n🎉 ¡SISTEMA LISTO!")
        print("✅ Todos los componentes disponibles")
        print("✅ Listo para ejecutar tests funcionales")
        return 0
    else:
        print(f"\n⚠️ {total - passed} componentes con problemas")
        print("🔧 Revisar configuración antes de ejecutar tests")
        return 1

if __name__ == "__main__":
    sys.exit(main())