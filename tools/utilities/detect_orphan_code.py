#!/usr/bin/env python3
"""
Script para detectar funciones huérfanas, imports no utilizados y código muerto.
Útil para refactoring y limpieza del código.
"""
import ast
import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import re

class CodeAnalyzer(ast.NodeVisitor):
    """Analizador de AST para detectar funciones, clases e imports."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.functions_defined = set()
        self.classes_defined = set()
        self.functions_called = set()
        self.imports = set()
        self.from_imports = defaultdict(set)
        self.variables_assigned = set()
        self.variables_used = set()
        self.decorators_used = set()
        
    def visit_FunctionDef(self, node):
        """Registrar definiciones de funciones."""
        self.functions_defined.add(node.name)
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        """Registrar definiciones de funciones async."""
        self.functions_defined.add(node.name)
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        """Registrar definiciones de clases."""
        self.classes_defined.add(node.name)
        # También registrar métodos de clase
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_name = f"{node.name}.{item.name}"
                self.functions_defined.add(method_name)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Registrar llamadas a funciones."""
        if isinstance(node.func, ast.Name):
            self.functions_called.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Para métodos como obj.method()
            if isinstance(node.func.value, ast.Name):
                method_name = f"{node.func.value.id}.{node.func.attr}"
                self.functions_called.add(method_name)
            self.functions_called.add(node.func.attr)
        self.generic_visit(node)
        
    def visit_Import(self, node):
        """Registrar imports simples."""
        for alias in node.names:
            import_name = alias.asname if alias.asname else alias.name
            self.imports.add(import_name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Registrar from imports."""
        module = node.module if node.module else ""
        for alias in node.names:
            import_name = alias.asname if alias.asname else alias.name
            self.from_imports[module].add(import_name)
            self.imports.add(import_name)
        self.generic_visit(node)
        
    def visit_Assign(self, node):
        """Registrar asignaciones de variables."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables_assigned.add(target.id)
        self.generic_visit(node)
        
    def visit_Name(self, node):
        """Registrar uso de nombres/variables."""
        if isinstance(node.ctx, ast.Load):
            self.variables_used.add(node.id)
        self.generic_visit(node)

def analyze_file(filepath: Path) -> CodeAnalyzer:
    """Analizar un archivo Python específico."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        analyzer = CodeAnalyzer(str(filepath))
        analyzer.visit(tree)
        return analyzer
    except Exception as e:
        print(f"⚠️ Error analizando {filepath}: {e}")
        return None

def find_python_files(root_dir: Path) -> List[Path]:
    """Encontrar todos los archivos Python en el proyecto."""
    python_files = []
    
    # Directorios a excluir
    exclude_dirs = {
        'env', '__pycache__', '.git', '.pytest_cache', 
        'node_modules', '.venv', 'venv', 'build', 'dist'
    }
    
    for filepath in root_dir.rglob("*.py"):
        # Excluir archivos en directorios específicos
        if any(excluded in filepath.parts for excluded in exclude_dirs):
            continue
        python_files.append(filepath)
    
    return python_files

def detect_orphan_functions(analyzers: List[CodeAnalyzer]) -> Dict[str, List[str]]:
    """Detectar funciones que se definen pero nunca se llaman."""
    all_defined = set()
    all_called = set()
    function_locations = {}
    
    for analyzer in analyzers:
        if analyzer:
            for func in analyzer.functions_defined:
                all_defined.add(func)
                function_locations[func] = analyzer.filepath
            all_called.update(analyzer.functions_called)
    
    # Funciones especiales que no consideramos huérfanas
    special_functions = {
        'main', '__init__', '__str__', '__repr__', '__call__',
        'setUp', 'tearDown', 'test_*', 'setup_method', 'teardown_method',
        'run', 'start', 'stop', 'close', 'open', 'execute',
        'handle', 'process', 'validate', 'create', 'get', 'set',
        'post', 'put', 'delete', 'patch'  # FastAPI endpoints
    }
    
    orphan_functions = {}
    for func in all_defined:
        if func not in all_called:
            # Verificar si es función especial
            is_special = any(
                func.startswith(pattern.replace('*', '')) or 
                func == pattern.replace('*', '') or
                (pattern.endswith('*') and func.startswith(pattern[:-1]))
                for pattern in special_functions
            )
            
            if not is_special:
                filepath = function_locations[func]
                if filepath not in orphan_functions:
                    orphan_functions[filepath] = []
                orphan_functions[filepath].append(func)
    
    return orphan_functions

def detect_unused_imports(analyzers: List[CodeAnalyzer]) -> Dict[str, List[str]]:
    """Detectar imports que no se utilizan."""
    unused_imports = {}
    
    for analyzer in analyzers:
        if analyzer:
            unused = []
            
            # Verificar imports simples
            for imp in analyzer.imports:
                if imp not in analyzer.variables_used and imp not in analyzer.functions_called:
                    # Excepciones comunes
                    if imp not in ['typing', 'annotations', '__future__']:
                        unused.append(imp)
            
            if unused:
                unused_imports[analyzer.filepath] = unused
    
    return unused_imports

def detect_unused_variables(analyzers: List[CodeAnalyzer]) -> Dict[str, List[str]]:
    """Detectar variables asignadas pero no utilizadas."""
    unused_variables = {}
    
    for analyzer in analyzers:
        if analyzer:
            unused = []
            
            for var in analyzer.variables_assigned:
                if var not in analyzer.variables_used:
                    # Excluir variables especiales
                    if not var.startswith('_') and var not in ['self', 'cls']:
                        unused.append(var)
            
            if unused:
                unused_variables[analyzer.filepath] = unused
    
    return unused_variables

def _generate_report_header() -> List[str]:
    """Generar encabezado del reporte."""
    return [
        "🧹 REPORTE DE REFACTORING - AssetPlan Property Assistant",
        "=" * 70,
        ""
    ]

def _generate_project_stats_section(project_stats: Dict) -> List[str]:
    """Generar sección de estadísticas del proyecto."""
    return [
        "📊 ESTADÍSTICAS DEL PROYECTO",
        "-" * 40,
        f"📁 Archivos Python analizados: {project_stats['total_files']}",
        f"📝 Total líneas de código: {project_stats['total_lines']}",
        f"🔧 Funciones definidas: {project_stats['total_functions']}",
        f"📦 Imports totales: {project_stats['total_imports']}",
        ""
    ]

def _generate_orphan_functions_section(orphan_functions: Dict[str, List[str]]) -> List[str]:
    """Generar sección de funciones huérfanas."""
    section = [
        "🔍 FUNCIONES HUÉRFANAS (Definidas pero no llamadas)",
        "-" * 50
    ]
    
    if orphan_functions:
        orphan_count = sum(len(funcs) for funcs in orphan_functions.values())
        section.append(f"❌ Total funciones huérfanas: {orphan_count}")
        section.append("")
        
        for file_path, functions in orphan_functions.items():
            if functions:
                section.append(f"📄 {file_path}:")
                for func in functions:
                    section.append(f"   • {func}()")
                section.append("")
    else:
        section.extend([
            "✅ ¡Excelente! No se encontraron funciones huérfanas.",
            "   El proyecto está bien optimizado.",
            ""
        ])
    
    return section

def _generate_unused_imports_section(unused_imports: Dict[str, List[str]]) -> List[str]:
    """Generar sección de imports no utilizados."""
    section = [
        "📦 IMPORTS NO UTILIZADOS",
        "-" * 30
    ]
    
    if unused_imports:
        unused_count = sum(len(imports) for imports in unused_imports.values())
        section.append(f"⚠️ Encontrados {unused_count} imports no utilizados en {len(unused_imports)} archivos")
        section.append("")
        
        for filepath, imports in unused_imports.items():
            relative_path = os.path.relpath(filepath)
            section.append(f"📄 {relative_path}")
            for imp in imports:
                section.append(f"   📦 {imp}")
            section.append("")
    else:
        section.extend([
            "✅ Todos los imports están siendo utilizados",
            ""
        ])
    
    return section

def _generate_summary_section(orphan_functions, unused_imports, unused_variables) -> List[str]:
    """Generar sección de resumen y recomendaciones."""
    section = [
        "📋 RESUMEN Y RECOMENDACIONES",
        "-" * 35
    ]
    
    total_issues = (
        sum(len(funcs) for funcs in orphan_functions.values()) +
        sum(len(imports) for imports in unused_imports.values()) +
        sum(len(vars) for vars in unused_variables.values())
    )
    
    if total_issues == 0:
        section.extend([
            "🎉 ¡EXCELENTE! El código está completamente optimizado.",
            "   No se encontraron problemas de código no utilizado.",
            "",
            "💡 SUGERENCIAS:",
            "   • Continuar con las buenas prácticas de desarrollo",
            "   • Realizar revisiones regulares de código",
            "   • Mantener la documentación actualizada"
        ])
    else:
        section.extend([
            f"📊 Total de issues encontrados: {total_issues}",
            "",
            "🔧 ACCIONES RECOMENDADAS:",
            "   1. Eliminar funciones huérfanas que no aportan valor",
            "   2. Limpiar imports no utilizados para mejorar rendimiento",
            "   3. Revisar variables no utilizadas en cada archivo",
            "   4. Ejecutar tests después de cada limpieza",
            "",
            "⚠️ IMPORTANTE:",
            "   • Revisar cada función antes de eliminarla",
            "   • Algunas funciones pueden ser para uso futuro",
            "   • Hacer commit antes de cambios grandes"
        ])
    
    return section

def generate_refactoring_report(
    orphan_functions: Dict[str, List[str]],
    unused_imports: Dict[str, List[str]], 
    unused_variables: Dict[str, List[str]],
    project_stats: Dict
) -> str:
    """Generar reporte completo de refactoring (refactorizado)."""
    
    report = []
    report.extend(_generate_report_header())
    report.extend(_generate_project_stats_section(project_stats))
    report.extend(_generate_orphan_functions_section(orphan_functions))
    report.extend(_generate_unused_imports_section(unused_imports))
    report.extend(_generate_summary_section(orphan_functions, unused_imports, unused_variables))
    
    return "\n".join(report)

def calculate_project_stats(analyzers: List['CodeAnalyzer'], python_files: List[Path]) -> Dict:
    """Calcula estadísticas generales del proyecto."""
    total_lines = 0
    total_functions = 0
    total_imports = 0

    for analyzer in analyzers:
        if analyzer:
            with open(analyzer.filepath, 'r', encoding='utf-8') as f:
                total_lines += len(f.readlines())
            total_functions += len(analyzer.functions_defined)
            total_imports += len(analyzer.imports) + sum(len(v) for v in analyzer.from_imports.values())

    return {
        'total_files': len(python_files),
        'total_lines': total_lines,
        'total_functions': total_functions,
        'total_imports': total_imports,
    }

def main():
    """Ejecutar detección de código huérfano."""
    project_root = Path(__file__).parent.parent.parent

    print("🧠 ANÁLISIS INTELIGENTE DE CÓDIGO")
    print("=" * 50)

    print("🔍 Buscando archivos Python...")
    python_files = find_python_files(project_root)
    print(f"✅ Encontrados {len(python_files)} archivos Python.")
    print()

    print("📊 Analizando archivos...")
    analyzers = []
    for python_file in python_files:
        print(f"🔍 {os.path.relpath(python_file, project_root)}")
        analyzer = analyze_file(python_file)
        if analyzer:
            analyzers.append(analyzer)

    print(f"✅ Analizados {len(analyzers)} archivos exitosamente")
    print()

    # Detectar problemas
    print("🔍 Detectando problemas...")
    orphan_functions = detect_orphan_functions(analyzers)
    unused_imports = detect_unused_imports(analyzers)
    unused_variables = detect_unused_variables(analyzers)

    # Calcular estadísticas
    project_stats = calculate_project_stats(analyzers, python_files) # This call was unindented

    # Generar reporte
    report = generate_refactoring_report(
        orphan_functions, unused_imports, unused_variables, project_stats
    )

    # Guardar reporte
    report_file = project_root / "REFACTORING_REPORT.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"📄 Reporte guardado en: {report_file}")
    print()

    # Mostrar resumen
    total_issues = (
        sum(len(funcs) for funcs in orphan_functions.values()) +
        sum(len(imports) for imports in unused_imports.values()) +
        sum(len(vars) for vars in unused_variables.values())
    )

    if total_issues == 0:
        print("🎉 ¡Excelente! No se encontraron problemas")
    else:
        print(f"⚠️ Encontrados {total_issues} problemas:")
        print(f"   - {len(orphan_functions)} archivos con funciones huérfanas")
        print(f"   - {len(unused_imports)} archivos con imports no utilizados")
        print(f"   - {len(unused_variables)} archivos con variables no utilizadas")

    print()
    print("💡 Revisa REFACTORING_REPORT.md para detalles completos")

    return total_issues

if __name__ == "__main__":
    sys.exit(main())