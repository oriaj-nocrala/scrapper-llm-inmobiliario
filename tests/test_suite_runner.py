#!/usr/bin/env python3
"""
Suite de tests completa y funcional para el proyecto.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, description, timeout_min=5):
    """Execute a command with timeout and capture results."""
    print(f"\n🧪 {description}")
    print("=" * 60)
    
    try:
        # Activate virtual environment and run command
        full_cmd = f"source env/bin/activate && {cmd}"
        
        start_time = time.time()
        result = subprocess.run(
            full_cmd, 
            shell=True, 
            executable="/bin/bash",
            capture_output=True, 
            text=True, 
            timeout=timeout_min * 60
        )
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ PASSED ({execution_time:.1f}s)")
            if result.stdout:
                # Only show last few lines for brevity
                lines = result.stdout.strip().split('\\n')
                if len(lines) > 5:
                    print("   ...")
                    for line in lines[-3:]:
                        print(f"   {line}")
                else:
                    print(f"   {result.stdout.strip()}")
            return True
        else:
            print(f"❌ FAILED ({execution_time:.1f}s)")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT after {timeout_min} minutes")
        return False
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

def main():
    """Run the complete test suite."""
    print("🚀 SUITE DE TESTS COMPLETA")
    print("=" * 60)
    print("Ejecutando todos los tests funcionales del proyecto")
    print()
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    test_results = []
    
    # 1. Quick URL Test (our proven working test)
    test_results.append(
        run_command(
            "python3 quick_url_test.py", 
            "Test de Citación de URLs (Rápido)",
            timeout_min=3
        )
    )
    
    # 2. Anti-overthinking test
    test_results.append(
        run_command(
            "python3 test_anti_overthinking.py", 
            "Test Anti-Overthinking",
            timeout_min=10
        )
    )
    
    # 3. Debug URL source test
    test_results.append(
        run_command(
            "python3 debug_url_source.py", 
            "Debug Origen URLs",
            timeout_min=3
        )
    )
    
    # 4. GPU performance test
    test_results.append(
        run_command(
            "python3 test_gpu_quick.py", 
            "Test GPU Performance (Rápido)",
            timeout_min=5
        )
    )
    
    # Summary
    print("\\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    test_names = [
        "Citación URLs",
        "Anti-Overthinking", 
        "Debug URLs",
        "GPU Performance"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n📈 Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ Sistema funcionando correctamente")
        print("✅ Coding challenge requirements cumplidos")
        print("✅ URLs se citan correctamente")
        print("✅ Anti-overthinking funcional")
        print("✅ GPU acceleration operativa")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests fallaron")
        print("🔧 Revisar configuración del sistema")
        return 1

if __name__ == "__main__":
    sys.exit(main())