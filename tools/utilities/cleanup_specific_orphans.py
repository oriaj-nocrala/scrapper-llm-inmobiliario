#!/usr/bin/env python3
"""
Script para eliminar funciones huérfanas específicas identificadas como seguras.
"""
import re
from pathlib import Path

def remove_orphan_function(file_path: Path, function_name: str, is_method: bool = False):
    """Eliminar una función específica de un archivo."""
    if not file_path.exists():
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    if is_method:
        # Para métodos de clase (con indentación)
        pattern = rf'^    def {function_name}\\(.*?\\):.*?(?=^    def |^class |^def |^\\Z)'
    else:
        # Para funciones globales
        pattern = rf'^def {function_name}\\(.*?\\):.*?(?=^def |^class |^\\Z)'
    
    new_content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    """Eliminar funciones huérfanas específicas seguras."""
    print("🎯 ELIMINACIÓN ESPECÍFICA DE FUNCIONES HUÉRFANAS SEGURAS")
    print("=" * 60)
    
    removals = []
    
    # 1. Eliminar funciones de utilidad no utilizadas que son obvias
    print("1️⃣ Eliminando funciones de utilidad no utilizadas...")
    
    # run_scraper_rag.py - eliminar handler de señal no usado
    run_scraper_rag = Path("run_scraper_rag.py")
    if remove_orphan_function(run_scraper_rag, "signal_handler"):
        print("   ✅ signal_handler() eliminada de run_scraper_rag.py")
        removals.append("run_scraper_rag.py: signal_handler()")
    
    # 2. Eliminar métodos obvios no utilizados en archivos específicos  
    print("\\n2️⃣ Eliminando métodos específicos no utilizados...")
    
    # fix_scraping.py - eliminar funciones no utilizadas
    fix_scraping = Path("fix_scraping.py")
    functions_to_remove = ["update_makefile", "install_dependencies", "analyze_assetplan_structure"]
    
    for func in functions_to_remove:
        if remove_orphan_function(fix_scraping, func):
            print(f"   ✅ {func}() eliminada de fix_scraping.py")
            removals.append(f"fix_scraping.py: {func}()")
    
    # 3. Eliminar funciones de test que claramente no se usan
    print("\\n3️⃣ Eliminando funciones de test no utilizadas...")
    
    # test_end_to_end.py - variables no usadas
    test_e2e = Path("test_end_to_end.py")
    if test_e2e.exists():
        with open(test_e2e, 'r') as f:
            content = f.read()
        
        # Eliminar líneas de variables no usadas
        original_content = content
        content = re.sub(r'^\\s*client\\s*=.*?\\n', '', content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(test_e2e, 'w') as f:
                f.write(content)
            print("   ✅ Variable 'client' eliminada de test_end_to_end.py")
            removals.append("test_end_to_end.py: variable client")
    
    # 4. Limpiar imports específicos no utilizados que quedaron
    print("\\n4️⃣ Limpiando imports específicos restantes...")
    
    # detect_orphan_code.py - imports no usados
    detect_orphan = Path("detect_orphan_code.py")
    if detect_orphan.exists():
        with open(detect_orphan, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Eliminar imports específicos no usados
        content = re.sub(r'^import re\\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'^from typing import.*?Set.*?\\n', '', content, flags=re.MULTILINE)
        content = re.sub(r', Set', '', content)
        content = re.sub(r', Counter', '', content)
        content = re.sub(r', Tuple', '', content)
        
        if content != original_content:
            with open(detect_orphan, 'w') as f:
                f.write(content)
            print("   ✅ Imports no usados eliminados de detect_orphan_code.py")
            removals.append("detect_orphan_code.py: imports no usados")
    
    # 5. Eliminar algunas funciones debug muy específicas que sabemos que no se usan
    print("\\n5️⃣ Eliminando funciones debug específicas...")
    
    # Eliminar timeout_handler standalone si existe
    assetplan_extractor = Path("src/scraper/domain/assetplan_extractor_v2.py")
    if assetplan_extractor.exists():
        with open(assetplan_extractor, 'r') as f:
            content = f.read()
        
        # Solo eliminar si es función standalone (no método)
        pattern = r'^def timeout_handler\\(.*?\\):.*?(?=^def |^class |^\\Z)'
        new_content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
        
        if new_content != content:
            with open(assetplan_extractor, 'w') as f:
                f.write(new_content)
            print("   ✅ timeout_handler() standalone eliminada")
            removals.append("assetplan_extractor_v2.py: timeout_handler() standalone")
    
    # Resumen
    print("\\n" + "=" * 60)
    print("📊 RESUMEN DE ELIMINACIÓN ESPECÍFICA")
    print("=" * 60)
    
    if removals:
        print(f"✅ Eliminadas {len(removals)} funciones específicas:")
        for removal in removals:
            print(f"   - {removal}")
        
        print("\\n🧪 VERIFICACIÓN NECESARIA:")
        print("   1. make test-status")
        print("   2. make test-url-citation") 
        print("   3. make analyze-code")
    else:
        print("ℹ️ No se encontraron funciones específicas para eliminar")
    
    return len(removals)

if __name__ == "__main__":
    import sys
    
    removals = main()
    
    if removals > 0:
        print(f"\\n🎉 Eliminación exitosa: {removals} funciones específicas eliminadas")
        sys.exit(0)
    else:
        print(f"\\nℹ️ No hay funciones específicas para eliminar")
        sys.exit(1)