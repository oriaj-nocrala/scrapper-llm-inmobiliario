#!/usr/bin/env python3
"""
Refactoring agresivo basado en métricas de código.
Elimina funciones y archivos usando datos científicos del análisis de métricas.
"""
import json
import re
import ast
import os
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class AggressiveRefactor:
    """Refactoring agresivo basado en métricas."""
    
    def __init__(self, metrics_file: Path):
        """Inicializar con archivo de métricas."""
        with open(metrics_file, 'r') as f:
            self.metrics_data = json.load(f)
        
        self.project_root = Path(__file__).parent.parent  # Go up one level from tools/
        self.removed_functions = []
        self.removed_files = []
        self.backup_dir = self.project_root / "refactor_backup"
        
    def create_backup(self):
        """Crear backup antes del refactoring."""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        print("💾 Creando backup del proyecto...")
        shutil.copytree(
            self.project_root, 
            self.backup_dir,
            ignore=shutil.ignore_patterns('env', '__pycache__', '.git', '*.pyc', 'refactor_backup')
        )
        print(f"✅ Backup creado en: {self.backup_dir}")
    
    def execute_aggressive_refactoring(self) -> Dict:
        """Ejecutar refactoring agresivo."""
        print("🔥 REFACTORING AGRESIVO BASADO EN MÉTRICAS")
        print("=" * 60)
        
        results = {
            'functions_removed': 0,
            'files_removed': 0,
            'lines_saved': 0,
            'complexity_reduced': 0
        }
        
        # 1. Eliminar funciones seguras (score alto)
        print("1️⃣ Eliminando funciones seguras para eliminar...")
        safe_functions = self._get_safe_deletion_candidates()
        results['functions_removed'] = self._remove_functions_safely(safe_functions)
        
        # 2. Eliminar archivos completamente no utilizados
        print("\\n2️⃣ Eliminando archivos no utilizados...")
        unused_files = self._identify_unused_files()
        results['files_removed'] = self._remove_unused_files(unused_files)
        
        # 3. Limpiar imports masivamente
        print("\\n3️⃣ Limpieza masiva de imports...")
        self._aggressive_import_cleanup()
        
        # 4. Eliminar variables y constantes no utilizadas
        print("\\n4️⃣ Eliminando variables y constantes no utilizadas...")
        self._remove_unused_variables()
        
        # 5. Consolidar archivos pequeños
        print("\\n5️⃣ Consolidando archivos pequeños...")
        self._consolidate_small_files()
        
        return results
    
    def _get_safe_deletion_candidates(self) -> List[Dict]:
        """Obtener candidatos seguros para eliminación."""
        recommendations = self.metrics_data.get('recommendations', {})
        safe_candidates = []
        
        # Top 50 funciones más seguras para eliminar
        safe_keys = recommendations.get('safe_to_delete', [])[:50]
        
        for key in safe_keys:
            if key in self.metrics_data['function_metrics']:
                func_data = self.metrics_data['function_metrics'][key]
                priority_score = recommendations['priority_scores'].get(key, 0)
                
                # Solo eliminar funciones con score muy alto (>15)
                if priority_score > 15:
                    safe_candidates.append({
                        'key': key,
                        'function_name': func_data['name'],
                        'file_path': func_data['file_path'],
                        'score': priority_score,
                        'is_test': func_data['is_test'],
                        'lines': func_data['lines_of_code']
                    })
        
        return safe_candidates
    
    def _remove_functions_safely(self, candidates: List[Dict]) -> int:
        """Eliminar funciones de forma segura."""
        removed_count = 0
        
        # Group by file for efficient processing
        by_file = defaultdict(list)
        for candidate in candidates:
            by_file[candidate['file_path']].append(candidate)
        
        for file_path, funcs in by_file.items():
            full_path = self.project_root / file_path
            if not full_path.exists():
                continue
            
            print(f"   🗑️ Procesando {file_path}")
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST to find function boundaries accurately
                tree = ast.parse(content)
                functions_to_remove = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        # Check if this function should be removed
                        for func in funcs:
                            if func['function_name'] == func_name:
                                functions_to_remove.append({
                                    'name': func_name,
                                    'lineno': node.lineno,
                                    'end_lineno': getattr(node, 'end_lineno', node.lineno + 10),
                                    'score': func['score']
                                })
                                break
                
                # Remove functions (from bottom to top to preserve line numbers)
                functions_to_remove.sort(key=lambda x: x['lineno'], reverse=True)
                
                lines = content.splitlines()
                for func_info in functions_to_remove:
                    start_line = func_info['lineno'] - 1  # Convert to 0-based
                    end_line = func_info['end_lineno']
                    
                    # Find actual end of function (including docstring and body)
                    actual_end = self._find_function_end(lines, start_line)
                    
                    # Remove function
                    del lines[start_line:actual_end + 1]
                    
                    print(f"      ❌ Eliminada {func_info['name']} (score: {func_info['score']:.1f})")
                    removed_count += 1
                    self.removed_functions.append(f"{file_path}::{func_info['name']}")
                
                # Write back the modified content
                if functions_to_remove:
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write('\\n'.join(lines))
                
            except Exception as e:
                print(f"⚠️ Error procesando {file_path}: {e}")
        
        print(f"✅ Eliminadas {removed_count} funciones seguras")
        return removed_count
    
    def _find_function_end(self, lines: List[str], start_line: int) -> int:
        """Encontrar el final real de una función."""
        i = start_line + 1
        in_function = True
        base_indent = None
        
        while i < len(lines) and in_function:
            line = lines[i]
            
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                i += 1
                continue
            
            # Detect indentation
            indent = len(line) - len(line.lstrip())
            
            if base_indent is None and line.strip():
                base_indent = indent
            
            # If we find a line with same or less indentation than function def, we're done
            if base_indent is not None and indent <= base_indent and line.strip():
                # Check if it's a decorator or another function/class
                if (line.strip().startswith('@') or 
                    line.strip().startswith('def ') or 
                    line.strip().startswith('class ') or
                    not line.startswith(' ')):
                    in_function = False
                    i -= 1  # Don't include this line
                    break
            
            i += 1
        
        return min(i, len(lines) - 1)
    
    def _identify_unused_files(self) -> List[str]:
        """Identificar archivos completamente no utilizados."""
        unused_files = []
        
        # Criterios para archivos no utilizados
        for file_path, file_metrics in self.metrics_data['file_metrics'].items():
            file_path_obj = Path(file_path)
            
            # Skip critical files
            if any(critical in file_path.lower() for critical in [
                'main.py', 'property_api.py', 'property_rag_chain.py', 
                'assetplan_extractor_v2.py', 'professional_scraper.py',
                '__init__.py'
            ]):
                continue
            
            # Files with very low usage and no critical functions
            if (file_metrics['usage_score'] == 0 and 
                file_metrics['functions_count'] > 0 and
                file_metrics['critical_score'] < 5):
                
                # Double check: are any functions from this file used?
                file_functions = [
                    k for k, v in self.metrics_data['function_metrics'].items() 
                    if v['file_path'] == file_path
                ]
                
                # If all functions are unused, mark file for deletion
                all_unused = all(
                    self.metrics_data['function_metrics'][k]['usage_type'] == 'unused'
                    for k in file_functions
                )
                
                if all_unused and len(file_functions) > 0:
                    unused_files.append(file_path)
        
        # Also check for demo and diagnostic files
        demo_patterns = ['demo_', 'test_end_to_end', 'diagnose_', 'fix_']
        for file_path in self.metrics_data['file_metrics']:
            if any(pattern in Path(file_path).name for pattern in demo_patterns):
                if file_path not in unused_files:
                    unused_files.append(file_path)
        
        return unused_files
    
    def _remove_unused_files(self, unused_files: List[str]) -> int:
        """Eliminar archivos no utilizados."""
        removed_count = 0
        
        for file_path in unused_files:
            full_path = self.project_root / file_path
            
            if full_path.exists():
                # Double check: is this file imported anywhere?
                file_stem = full_path.stem
                is_imported = self._check_if_imported(file_stem)
                
                if not is_imported:
                    print(f"   🗑️ Eliminando archivo: {file_path}")
                    full_path.unlink()
                    removed_count += 1
                    self.removed_files.append(file_path)
                else:
                    print(f"   ⚠️ Archivo {file_path} está importado, conservando")
        
        print(f"✅ Eliminados {removed_count} archivos no utilizados")
        return removed_count
    
    def _check_if_imported(self, file_stem: str) -> bool:
        """Verificar si un archivo es importado en algún lugar."""
        import_patterns = [
            f"from {file_stem}",
            f"import {file_stem}",
            f"from .{file_stem}",
            f"import .{file_stem}"
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if any(pattern in content for pattern in import_patterns):
                    return True
            except:
                pass
        
        return False
    
    def _aggressive_import_cleanup(self):
        """Limpieza masiva de imports."""
        print("   🧹 Ejecutando autoflake agresivo...")
        
        import subprocess
        
        # More aggressive autoflake
        cmd = [
            "python", "-m", "autoflake",
            "--remove-all-unused-imports",
            "--remove-unused-variables", 
            "--remove-duplicate-keys",
            "--recursive",
            "--in-place",
            "src/", "tests/"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                print("   ✅ Autoflake ejecutado exitosamente")
            else:
                print(f"   ⚠️ Autoflake warning: {result.stderr}")
        except Exception as e:
            print(f"   ⚠️ Error ejecutando autoflake: {e}")
    
    def _remove_unused_variables(self):
        """Eliminar variables y constantes no utilizadas."""
        # Remove specific constant files that are clearly unused
        constants_to_remove = [
            ("src/scraper/infrastructure/smart_locator.py", [
                "PROPERTY_CONTAINERS", "PRICE_SELECTORS", "IMAGE_SELECTORS",
                "TITLE_SELECTORS", "LINK_SELECTORS", "LOCATION_SELECTORS",
                "BEDROOM_SELECTORS", "BATHROOM_SELECTORS", "AREA_SELECTORS"
            ]),
            ("src/scraper/infrastructure/webdriver_factory.py", [
                "USER_AGENTS", "SCREEN_SIZES"
            ]),
            ("src/scraper/domain/retry_manager.py", [
                "EXPONENTIAL", "LINEAR", "FIXED", "FIBONACCI",
                "FAST", "STANDARD", "AGGRESSIVE", "PATIENT",
                "OPEN", "HALF_OPEN", "CLOSED", "TOLERANT", "SENSITIVE"
            ])
        ]
        
        removed_vars = 0
        for file_path, variables in constants_to_remove:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"   🗑️ Limpiando constantes en {file_path}")
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                for var in variables:
                    # Remove variable definitions
                    pattern = rf'^{var}\\s*=.*?(?=\\n[A-Z_]|\\nclass|\\ndef|\\n\\n|$)'
                    content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
                
                if content != original_content:
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    removed_vars += len(variables)
                    print(f"      ❌ Eliminadas {len(variables)} constantes")
        
        print(f"   ✅ Eliminadas {removed_vars} variables/constantes")
    
    def _consolidate_small_files(self):
        """Consolidar archivos muy pequeños."""
        # Find files with very few functions that could be merged
        small_files = []
        
        for file_path, file_metrics in self.metrics_data['file_metrics'].items():
            if (file_metrics['lines_of_code'] < 50 and 
                file_metrics['functions_count'] < 3 and
                not any(pattern in file_path for pattern in ['__init__.py', 'main.py', 'test_'])):
                small_files.append(file_path)
        
        print(f"   📋 Identificados {len(small_files)} archivos pequeños para revisión")
        # Note: Actual consolidation would require more complex logic
        # For now, just report them for manual review
    
    def generate_refactor_report(self, results: Dict) -> str:
        """Generar reporte de refactoring."""
        report = f"""
# 🔥 REPORTE DE REFACTORING AGRESIVO

## 📊 Resultados

- **Funciones eliminadas**: {results['functions_removed']}
- **Archivos eliminados**: {results['files_removed']}
- **Funciones procesadas**: {len(self.removed_functions)}

## 🗑️ Funciones Eliminadas

"""
        for func in self.removed_functions[:20]:  # Top 20
            report += f"- {func}\\n"
        
        if len(self.removed_functions) > 20:
            report += f"... y {len(self.removed_functions) - 20} más\\n"
        
        report += f"""
## 📁 Archivos Eliminados

"""
        for file_path in self.removed_files:
            report += f"- {file_path}\\n"
        
        report += f"""
## 💾 Backup

Backup completo disponible en: `{self.backup_dir}`

## ⚠️ Próximos Pasos

1. Ejecutar tests: `make test-status`
2. Verificar funcionamiento: `make test-url-citation`
3. Re-analizar métricas: `python3 code_metrics_analyzer.py`
4. Si hay problemas, restaurar: `cp -r {self.backup_dir}/* .`
"""
        return report

def main():
    """Ejecutar refactoring agresivo."""
    metrics_file = Path(__file__).parent / "CODE_METRICS_REPORT.json"
    
    if not metrics_file.exists():
        print("❌ Archivo de métricas no encontrado. Ejecutar: python3 code_metrics_analyzer.py")
        return 1
    
    refactor = AggressiveRefactor(metrics_file)
    
    # Create backup
    refactor.create_backup()
    
    # Execute refactoring
    results = refactor.execute_aggressive_refactoring()
    
    # Generate report
    report = refactor.generate_refactor_report(results)
    
    # Save report
    with open("AGGRESSIVE_REFACTOR_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\\n" + "=" * 60)
    print("📊 REFACTORING COMPLETADO")
    print("=" * 60)
    print(f"✅ Funciones eliminadas: {results['functions_removed']}")
    print(f"✅ Archivos eliminados: {results['files_removed']}")
    print(f"📄 Reporte guardado en: AGGRESSIVE_REFACTOR_REPORT.md")
    print(f"💾 Backup disponible en: {refactor.backup_dir}")
    
    print("\\n🧪 VERIFICACIÓN REQUERIDA:")
    print("   1. make test-status")
    print("   2. make test-url-citation")
    print("   3. python3 code_metrics_analyzer.py")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())