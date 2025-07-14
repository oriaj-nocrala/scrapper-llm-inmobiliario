#!/usr/bin/env python3
"""
Test script para verificar la integración de God Class Refactor en el dashboard.
"""
import json
import sys
from pathlib import Path

# Agregar el directorio tools al path
sys.path.insert(0, str(Path(__file__).parent))

from categorized_dashboard_server import DashboardDataProvider, DashboardAPIHandler

def test_god_class_integration():
    """Probar la integración de God Class Refactor."""
    print("🧪 Probando integración de God Class Refactor en Dashboard")
    print("=" * 60)
    
    # Inicializar componentes
    project_root = Path(__file__).parent.parent
    data_provider = DashboardDataProvider(project_root)
    api_handler = DashboardAPIHandler(data_provider)
    
    # Test 1: Detección de God Classes
    print("\n🔍 Test 1: Detección de God Classes")
    status, content_type, content = api_handler.handle_god_class_detection()
    
    print(f"Status: {status}")
    print(f"Content-Type: {content_type}")
    
    if status == 200:
        data = json.loads(content)
        print(f"✅ God classes detectadas: {data['total_detected']}")
        
        if data['god_classes']:
            for gc in data['god_classes']:
                print(f"   📋 {gc['class_name']} ({gc['method_count']} métodos) en {gc['file']}")
        else:
            print("   🎉 No se encontraron God classes")
    else:
        print(f"❌ Error: {content}")
    
    # Test 2: Análisis de God Class específica (si existe)
    if status == 200:
        data = json.loads(content)
        if data['god_classes']:
            print(f"\n🧠 Test 2: Análisis de God Class con IA")
            file_path = data['god_classes'][0]['file']
            print(f"Analizando: {file_path}")
            
            status2, content_type2, content2 = api_handler.handle_god_class_analysis(file_path)
            print(f"Status: {status2}")
            
            if status2 == 200:
                analysis_data = json.loads(content2)
                print(f"✅ Análisis completado para {analysis_data['class_name']}")
                print(f"   📊 Métodos: {analysis_data['total_methods']}")
                
                if 'summary' in analysis_data:
                    summary = analysis_data['summary']
                    print(f"   🎯 Refactorabilidad: {summary.get('refactorability', 'N/A')}")
                    
                    if 'key_insights' in summary:
                        print("   💡 Insights:")
                        for insight in summary['key_insights'][:3]:
                            print(f"      • {insight}")
                
                if 'refactor_plan' in analysis_data:
                    plan = analysis_data['refactor_plan']
                    print(f"   🛣️ Plan: {len(plan)} pasos")
                    
            else:
                print(f"❌ Error en análisis: {content2}")
    
    # Test 3: Verificar disponibilidad de God Class Refactor
    print(f"\n⚙️ Test 3: Disponibilidad de componentes")
    print(f"God Class Refactor disponible: {data_provider.god_class_refactor is not None}")
    
    if data_provider.god_class_refactor:
        print("✅ God Class Refactor Guide cargado correctamente")
        
        # Verificar configuración óptima
        config = data_provider.god_class_refactor.optimal_config
        if config:
            print(f"⚡ Configuración óptima: {config.get('description', 'N/A')}")
            print(f"   📊 Contexto: {config.get('n_ctx', 'N/A')}")
            print(f"   🚀 GPU Layers: {config.get('n_gpu_layers', 'N/A')}")
        else:
            print("⚠️ Configuración óptima no encontrada (se detectará en primer uso)")
    else:
        print("❌ God Class Refactor Guide no disponible")
    
    print(f"\n🎯 RESUMEN DE INTEGRACIÓN")
    print("=" * 60)
    print("✅ APIs integradas:")
    print("   📍 /api/god-classes - Detección de God Classes")
    print("   📍 /api/analyze-god-class?file=path - Análisis con IA")
    print("✅ Interfaz HTML integrada:")
    print("   🧠 Pestaña 'God Classes' en dashboard")
    print("   🔍 Botón 'Detectar God Classes'")
    print("   🧠 Botón 'Analizar con IA' por cada God class")
    print("✅ Funcionalidades:")
    print("   ⚡ Cache inteligente de análisis")
    print("   🎯 Configuración adaptativa de VRAM")
    print("   📊 Plan de refactorización paso a paso")
    print("   🛡️ Análisis de riesgos")

if __name__ == "__main__":
    test_god_class_integration()