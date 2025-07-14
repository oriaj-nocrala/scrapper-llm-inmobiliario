#!/usr/bin/env python3
"""
Comando optimizado para ejecutar el sistema completo con aceleración GPU.
Configuración óptima para RTX 3050 8GB.
"""
import os
import sys
import argparse
from pathlib import Path

def setup_gpu_environment():
    """Configurar variables de entorno optimizadas para GPU."""
    # Configuración base
    os.environ["USE_LOCAL_MODELS"] = "true"
    os.environ["USE_GPU"] = "true"
    
    # GPU optimization for RTX 3050
    os.environ["GPU_LAYERS"] = "25"  # Conservativo para evitar OOM
    os.environ["GPU_MEMORY_LIMIT"] = "5.5"  # Deja 2.5GB para el sistema
    
    # CUDA optimizations
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"
    
    print("🚀 Configuración GPU optimizada para RTX 3050:")
    print(f"   - GPU Layers: {os.environ['GPU_LAYERS']}")
    print(f"   - Memory Limit: {os.environ['GPU_MEMORY_LIMIT']}GB")

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Ejecutor optimizado para GPU RTX 3050",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos optimizados para RTX 3050:

  # Pipeline completo con API (recomendado)
  python run_gpu_optimized.py --full-pipeline --start-api

  # Solo test de rendimiento
  python run_gpu_optimized.py --test-only

  # Pipeline rápido para pruebas
  python run_gpu_optimized.py --quick --max-properties 10

  # Configuración conservativa (si hay problemas de memoria)
  python run_gpu_optimized.py --conservative --max-properties 20
        """)
    
    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Ejecutar pipeline completo: scraping + RAG + API"
    )
    
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Solo probar sistema RAG existente"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Pipeline rápido para pruebas"
    )
    
    parser.add_argument(
        "--conservative",
        action="store_true",
        help="Configuración conservativa de memoria"
    )
    
    parser.add_argument(
        "--start-api",
        action="store_true",
        help="Iniciar servidor API después del pipeline"
    )
    
    parser.add_argument(
        "--max-properties",
        type=int,
        default=30,
        help="Máximo número de propiedades (default: 30)"
    )
    
    parser.add_argument(
        "--gpu-layers",
        type=int,
        help="Número de capas GPU (override automático)"
    )
    
    args = parser.parse_args()
    
    # Configurar GPU
    setup_gpu_environment()
    
    # Override GPU layers si se especifica
    if args.gpu_layers:
        os.environ["GPU_LAYERS"] = str(args.gpu_layers)
        print(f"   - GPU Layers (override): {args.gpu_layers}")
    
    # Configuración conservativa
    if args.conservative:
        os.environ["GPU_LAYERS"] = "20"
        os.environ["GPU_MEMORY_LIMIT"] = "4.5"
        print("🔧 Modo conservativo activado")
    
    print("")
    
    try:
        if args.test_only:
            # Solo test
            print("🧪 Ejecutando test de rendimiento...")
            os.system("python3 test_gpu_llama_only.py")
            
        elif args.full_pipeline:
            # Pipeline completo
            cmd = f"python3 run_scraper_rag.py --mode quick --max-properties {args.max_properties}"
            if args.start_api:
                cmd += " --start-api --wait-for-api"
            
            print("🚀 Ejecutando pipeline completo...")
            os.system(cmd)
            
        elif args.quick:
            # Pipeline rápido
            cmd = f"python3 run_scraper_rag.py --mode quick --max-properties {args.max_properties}"
            print("⚡ Ejecutando pipeline rápido...")
            os.system(cmd)
            
        else:
            # Default: mostrar ayuda
            parser.print_help()
            print("\n💡 Usa --full-pipeline para ejecutar todo el sistema")
            return 1
            
    except KeyboardInterrupt:
        print("\n👋 Proceso interrumpido por el usuario")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())