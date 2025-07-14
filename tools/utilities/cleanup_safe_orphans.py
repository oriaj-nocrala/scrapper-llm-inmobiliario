#!/usr/bin/env python3
"""
Script para eliminar funciones huérfanas específicas que son muy seguras de eliminar.
Solo elimina funciones claramente no utilizadas y de bajo riesgo.
"""
import os
import re
from pathlib import Path

def remove_safe_unused_functions():
    """Eliminar funciones específicas que son seguras de eliminar."""
    
    print("🧹 LIMPIEZA SEGURA DE FUNCIONES HUÉRFANAS")
    print("=" * 50)
    
    safe_removals = []
    
    # 1. Eliminar imports no utilizados en archivos root
    print("1️⃣ Limpiando imports en archivos root...")
    
    # run_chat.py - eliminar import os no usado
    run_chat_path = Path("run_chat.py")
    if run_chat_path.exists():
        with open(run_chat_path, 'r') as f:
            content = f.read()
        
        if 'import os' in content and 'os.' not in content:
            content = re.sub(r'^import os\n', '', content, flags=re.MULTILINE)
            with open(run_chat_path, 'w') as f:
                f.write(content)
            print(f"   ✅ Eliminado 'import os' no usado de run_chat.py")
            safe_removals.append("run_chat.py: import os")
    
    # run_api.py - eliminar imports no usados  
    run_api_path = Path("run_api.py")
    if run_api_path.exists():
        with open(run_api_path, 'r') as f:
            content = f.read()
        
        # Eliminar imports no usados
        original_content = content
        content = re.sub(r'^import os\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'^import subprocess\n', '', content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(run_api_path, 'w') as f:
                f.write(content)
            print(f"   ✅ Eliminados imports no usados de run_api.py")
            safe_removals.append("run_api.py: import os, subprocess")
    
    # 2. Limpiar variables no utilizadas que son constantes
    print("\\n2️⃣ Limpiando constantes no utilizadas...")
    
    # human_behavior.py - eliminar constantes de velocidad no usadas
    human_behavior_path = Path("src/scraper/infrastructure/human_behavior.py")
    if human_behavior_path.exists():
        with open(human_behavior_path, 'r') as f:
            content = f.read()
        
        # Eliminar constantes no usadas
        constants_to_remove = ['FAST', 'NORMAL', 'SLOW', 'VERY_SLOW']
        original_content = content
        
        for const in constants_to_remove:
            pattern = rf'^{const}\s*=\s*[^\\n]+\\n'
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(human_behavior_path, 'w') as f:
                f.write(content)
            print(f"   ✅ Eliminadas constantes no usadas de human_behavior.py")
            safe_removals.append("human_behavior.py: FAST, NORMAL, SLOW, VERY_SLOW")
    
    # 3. Limpiar funciones standalone no utilizadas (funciones globales seguras)
    print("\\n3️⃣ Limpiando funciones globales no utilizadas...")
    
    # detect_orphan_code.py - eliminar funciones visitor no usadas
    detect_orphan_path = Path("detect_orphan_code.py")
    if detect_orphan_path.exists():
        with open(detect_orphan_path, 'r') as f:
            content = f.read()
        
        # Eliminar funciones visitor standalone que son duplicadas
        functions_to_remove = [
            'visit_FunctionDef', 'visit_Call', 'visit_Assign', 'visit_Name',
            'visit_ClassDef', 'visit_ImportFrom', 'visit_AsyncFunctionDef', 'visit_Import'
        ]
        
        original_content = content
        for func in functions_to_remove:
            # Solo eliminar si es función standalone (no método de clase)
            pattern = rf'^def {func}\\([^)]*\\):.*?(?=^def |^class |^\\Z)'
            content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
        
        if content != original_content:
            with open(detect_orphan_path, 'w') as f:
                f.write(content)
            print(f"   ✅ Eliminadas funciones visitor duplicadas de detect_orphan_code.py")
            safe_removals.append("detect_orphan_code.py: funciones visitor standalone")
    
    # 4. Eliminar funciones de demo/test que no son críticas
    print("\\n4️⃣ Limpiando archivos de demo...")
    
    # demo_system.py - limpiar variables no usadas
    demo_path = Path("demo_system.py")
    if demo_path.exists():
        with open(demo_path, 'r') as f:
            content = f.read()
        
        # Eliminar variables no usadas
        original_content = content
        content = re.sub(r'^\\s*sample_doc\\s*=.*?\\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\\s*answer\\s*=.*?\\n', '', content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(demo_path, 'w') as f:
                f.write(content)
            print(f"   ✅ Eliminadas variables no usadas de demo_system.py")
            safe_removals.append("demo_system.py: sample_doc, answer")
    
    # 5. Resumen
    print("\\n" + "=" * 50)
    print("📊 RESUMEN DE LIMPIEZA SEGURA")
    print("=" * 50)
    
    if safe_removals:
        print(f"✅ Se eliminaron {len(safe_removals)} elementos:")
        for removal in safe_removals:
            print(f"   - {removal}")
    else:
        print("ℹ️ No se encontraron elementos seguros para eliminar")
    
    print("\\n💡 Próximos pasos:")
    print("   1. Ejecutar tests: make test-status")
    print("   2. Verificar funcionamiento: make test-url-citation")
    print("   3. Re-analizar código: make analyze-code")
    
    return len(safe_removals)

if __name__ == "__main__":
    import sys
    
    removals = remove_safe_unused_functions()
    
    if removals > 0:
        print(f"\\n🎉 Limpieza exitosa: {removals} elementos eliminados")
        sys.exit(0)
    else:
        print(f"\\nℹ️ No hay elementos seguros para eliminar")
        sys.exit(1)