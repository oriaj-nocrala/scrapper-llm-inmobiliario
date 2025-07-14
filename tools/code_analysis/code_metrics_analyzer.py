#!/usr/bin/env python3
"""
Sistema avanzado de métricas de código para refactoring basado en datos.
Analiza uso real, complejidad y impacto para tomar decisiones informadas.
"""
import ast
import os
import sys
import json
import time
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re

@dataclass
class FileMetrics:
    """Métricas detalladas de un archivo."""
    path: str
    lines_of_code: int
    functions_count: int
    classes_count: int
    imports_count: int
    complexity_score: float
    test_coverage_estimate: float
    last_modified: str
    usage_score: float  # Based on imports from other files
    critical_score: float  # Based on system criticality

@dataclass
class FunctionMetrics:
    """Métricas detalladas de una función."""
    name: str
    file_path: str
    lines_of_code: int
    complexity: int
    called_count: int
    is_test: bool
    is_private: bool
    is_api_endpoint: bool
    is_critical: bool  # Core system function
    usage_type: str  # 'unused', 'test_only', 'internal', 'api', 'critical'

@dataclass
class ProjectMetrics:
    """Métricas generales del proyecto."""
    total_files: int
    total_lines: int
    total_functions: int
    total_classes: int
    test_files: int
    core_files: int
    utility_files: int
    orphan_functions: int
    dead_imports: int
    complexity_average: float
    maintainability_score: float

class AdvancedCodeAnalyzer(ast.NodeVisitor):
    """Analizador avanzado con métricas de complejidad y uso."""
    
    def __init__(self, filepath: str, project_root: Path):
        self.filepath = filepath
        self.project_root = project_root
        self.functions = {}
        self.classes = {}
        self.imports = set()
        self.function_calls = defaultdict(int)
        self.complexity_score = 0
        self.current_function = None
        self.function_complexity = defaultdict(int)
        
    def visit_FunctionDef(self, node):
        """Analizar definiciones de función con métricas de complejidad."""
        func_name = node.name
        self.current_function = func_name
        
        # Calculate function complexity (simplified cyclomatic complexity)
        complexity = self._calculate_complexity(node)
        
        # Determine function characteristics
        is_test = self._is_test_function(func_name, self.filepath)
        is_private = func_name.startswith('_')
        is_api_endpoint = self._is_api_endpoint(node)
        is_critical = self._is_critical_function(func_name, self.filepath)
        
        self.functions[func_name] = {
            'name': func_name,
            'line_start': node.lineno,
            'line_end': node.end_lineno or node.lineno,
            'complexity': complexity,
            'is_test': is_test,
            'is_private': is_private,
            'is_api_endpoint': is_api_endpoint,
            'is_critical': is_critical,
            'docstring': ast.get_docstring(node),
            'decorators': [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list]
        }
        
        self.function_complexity[func_name] = complexity
        self.complexity_score += complexity
        
        self.generic_visit(node)
        self.current_function = None
        
    def visit_Call(self, node):
        """Registrar llamadas a funciones."""
        if isinstance(node.func, ast.Name):
            self.function_calls[node.func.id] += 1
        elif isinstance(node.func, ast.Attribute):
            self.function_calls[node.func.attr] += 1
        self.generic_visit(node)
    
    def _calculate_complexity(self, node) -> int:
        """Calcular complejidad ciclomática simplificada."""
        from code_utils import calculate_complexity
        return calculate_complexity(node)
    
    def _is_test_function(self, func_name: str, filepath: str) -> bool:
        """Determinar si es función de test."""
        return (func_name.startswith('test_') or 
                'test' in filepath.lower() or 
                func_name in ['setUp', 'tearDown'])
    
    def _is_api_endpoint(self, node) -> bool:
        """Determinar si es endpoint de API."""
        decorators = [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list]
        api_decorators = ['app.get', 'app.post', 'app.put', 'app.delete', 'router.get', 'router.post']
        return any(any(dec in str(decorator) for dec in api_decorators) for decorator in decorators)
    
    def _is_critical_function(self, func_name: str, filepath: str) -> bool:
        """Determinar si es función crítica del sistema."""
        critical_patterns = [
            'main', 'run', 'start', 'init', 'setup',
            'ask_question', 'create_rag_chain', 'scrape',
            'extract', 'process', 'generate'
        ]
        critical_files = ['main.py', 'property_api.py', 'property_rag_chain.py', 'assetplan_extractor']
        
        is_in_critical_file = any(cf in filepath for cf in critical_files)
        is_critical_name = any(pattern in func_name.lower() for pattern in critical_patterns)
        
        return is_in_critical_file or is_critical_name

class CodeMetricsSystem:
    """Sistema completo de métricas de código."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.file_metrics = {}
        self.function_metrics = {}
        self.project_metrics = None
        self.usage_graph = defaultdict(set)
        
    def analyze_project(self) -> ProjectMetrics:
        """Analizar todo el proyecto y generar métricas."""
        print("📊 ANALIZANDO MÉTRICAS DEL PROYECTO")
        print("=" * 50)
        
        python_files = self._find_python_files()
        print(f"📁 Encontrados {len(python_files)} archivos Python")
        
        # Analyze each file
        total_functions = 0
        total_classes = 0
        total_lines = 0
        complexity_total = 0
        orphan_count = 0
        
        for file_path in python_files:
            print(f"🔍 Analizando {file_path.relative_to(self.project_root)}")
            
            analyzer = AdvancedCodeAnalyzer(str(file_path), self.project_root)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.splitlines())
                
                tree = ast.parse(content)
                analyzer.visit(tree)
                
                # Calculate usage score
                usage_score = self._calculate_usage_score(file_path)
                critical_score = self._calculate_critical_score(file_path)
                
                # File metrics
                file_metrics = FileMetrics(
                    path=str(file_path.relative_to(self.project_root)),
                    lines_of_code=lines,
                    functions_count=len(analyzer.functions),
                    classes_count=len(analyzer.classes),
                    imports_count=len(analyzer.imports),
                    complexity_score=analyzer.complexity_score,
                    test_coverage_estimate=self._estimate_test_coverage(file_path),
                    last_modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    usage_score=usage_score,
                    critical_score=critical_score
                )
                
                self.file_metrics[str(file_path)] = file_metrics
                
                # Function metrics
                for func_name, func_data in analyzer.functions.items():
                    called_count = analyzer.function_calls.get(func_name, 0)
                    usage_type = self._determine_usage_type(func_data, called_count)
                    
                    func_metrics = FunctionMetrics(
                        name=func_name,
                        file_path=str(file_path.relative_to(self.project_root)),
                        lines_of_code=func_data['line_end'] - func_data['line_start'],
                        complexity=func_data['complexity'],
                        called_count=called_count,
                        is_test=func_data['is_test'],
                        is_private=func_data['is_private'],
                        is_api_endpoint=func_data['is_api_endpoint'],
                        is_critical=func_data['is_critical'],
                        usage_type=usage_type
                    )
                    
                    key = f"{file_path}::{func_name}"
                    self.function_metrics[key] = func_metrics
                    
                    if usage_type == 'unused':
                        orphan_count += 1
                
                total_functions += len(analyzer.functions)
                total_classes += len(analyzer.classes)
                total_lines += lines
                complexity_total += analyzer.complexity_score
                
            except Exception as e:
                print(f"⚠️ Error analizando {file_path}: {e}")
        
        # Calculate project metrics
        complexity_avg = complexity_total / max(total_functions, 1)
        maintainability = self._calculate_maintainability_score()
        
        self.project_metrics = ProjectMetrics(
            total_files=len(python_files),
            total_lines=total_lines,
            total_functions=total_functions,
            total_classes=total_classes,
            test_files=len([f for f in python_files if 'test' in str(f)]),
            core_files=len([f for f in python_files if self._is_core_file(f)]),
            utility_files=len([f for f in python_files if self._is_utility_file(f)]),
            orphan_functions=orphan_count,
            dead_imports=self._count_dead_imports(),
            complexity_average=complexity_avg,
            maintainability_score=maintainability
        )
        
        print(f"✅ Análisis completo: {total_functions} funciones, {orphan_count} huérfanas")
        return self.project_metrics
    
    def generate_refactoring_recommendations(self) -> Dict:
        """Generar recomendaciones de refactoring basadas en métricas."""
        recommendations = {
            'safe_to_delete': [],
            'review_for_deletion': [],
            'simplify_complexity': [],
            'merge_candidates': [],
            'extract_candidates': [],
            'priority_scores': {}
        }
        
        # Analyze functions for deletion
        for key, func in self.function_metrics.items():
            priority_score = self._calculate_deletion_priority(func)
            recommendations['priority_scores'][key] = priority_score
            
            if func.usage_type == 'unused' and not func.is_critical:
                if func.is_test or func.is_private:
                    recommendations['safe_to_delete'].append(key)
                else:
                    recommendations['review_for_deletion'].append(key)
            
            if func.complexity > 10:
                recommendations['simplify_complexity'].append(key)
        
        # Sort by priority
        recommendations['safe_to_delete'].sort(key=lambda x: recommendations['priority_scores'][x], reverse=True)
        recommendations['review_for_deletion'].sort(key=lambda x: recommendations['priority_scores'][x], reverse=True)
        
        return recommendations
    
    def _calculate_deletion_priority(self, func: FunctionMetrics) -> float:
        """Calcular prioridad de eliminación (mayor = más prioritario)."""
        score = 0.0
        
        # Base score for unused functions
        if func.usage_type == 'unused':
            score += 10.0
        
        # Higher priority for test functions
        if func.is_test:
            score += 5.0
        
        # Higher priority for private functions
        if func.is_private:
            score += 3.0
        
        # Lower priority for API endpoints
        if func.is_api_endpoint:
            score -= 10.0
        
        # Lower priority for critical functions
        if func.is_critical:
            score -= 15.0
        
        # Consider complexity (simpler = easier to delete)
        score += max(0, 5 - func.complexity)
        
        # Consider lines of code (smaller = easier to delete)
        score += max(0, 10 - func.lines_of_code)
        
        return score
    
    def _find_python_files(self) -> List[Path]:
        """Encontrar todos los archivos Python."""
        exclude_dirs = {'env', '__pycache__', '.git', '.pytest_cache', 'node_modules', 'refactor_backup'}
        python_files = []
        
        for file_path in self.project_root.rglob("*.py"):
            if not any(excluded in file_path.parts for excluded in exclude_dirs):
                python_files.append(file_path)
        
        return python_files
    
    def _calculate_usage_score(self, file_path: Path) -> float:
        """Calcular score de uso basado en imports."""
        # Simplified: count how many files import this one
        file_name = file_path.stem
        usage_count = 0
        
        for other_file in self._find_python_files():
            if other_file == file_path:
                continue
            try:
                with open(other_file, 'r') as f:
                    content = f.read()
                    if f"from {file_name}" in content or f"import {file_name}" in content:
                        usage_count += 1
            except:
                pass
        
        return float(usage_count)
    
    def _calculate_critical_score(self, file_path: Path) -> float:
        """Calcular score de criticidad."""
        critical_files = [
            'main.py', 'property_api.py', 'property_rag_chain.py', 
            'assetplan_extractor_v2.py', 'professional_scraper.py'
        ]
        
        file_name = file_path.name
        if any(cf in file_name for cf in critical_files):
            return 10.0
        elif 'test' in file_name:
            return 2.0
        elif file_path.suffix == '.py':
            return 5.0
        
        return 1.0
    
    def _determine_usage_type(self, func_data: Dict, called_count: int) -> str:
        """Determinar tipo de uso de función."""
        if called_count == 0:
            return 'unused'
        elif func_data['is_test']:
            return 'test_only'
        elif func_data['is_api_endpoint']:
            return 'api'
        elif func_data['is_critical']:
            return 'critical'
        else:
            return 'internal'
    
    def _estimate_test_coverage(self, file_path: Path) -> float:
        """Estimar cobertura de tests."""
        if 'test' in str(file_path):
            return 100.0
        
        # Look for corresponding test file
        test_patterns = [
            f"test_{file_path.stem}.py",
            f"test_{file_path.stem}_test.py",
            f"{file_path.stem}_test.py"
        ]
        
        for pattern in test_patterns:
            test_path = file_path.parent / pattern
            if test_path.exists():
                return 80.0
        
        # Check in tests directory
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            for pattern in test_patterns:
                test_path = tests_dir / pattern
                if test_path.exists():
                    return 70.0
        
        return 30.0  # Default low coverage
    
    def _calculate_maintainability_score(self) -> float:
        """Calcular score de mantenibilidad."""
        if not self.function_metrics:
            return 50.0
        
        total_score = 0
        count = 0
        
        for func in self.function_metrics.values():
            score = 100.0
            
            # Penalize high complexity
            if func.complexity > 15:
                score -= 30
            elif func.complexity > 10:
                score -= 15
            elif func.complexity > 5:
                score -= 5
            
            # Penalize large functions
            if func.lines_of_code > 50:
                score -= 20
            elif func.lines_of_code > 25:
                score -= 10
            
            # Reward good naming and structure
            if not func.is_private and func.called_count > 0:
                score += 10
            
            total_score += max(0, score)
            count += 1
        
        return total_score / max(count, 1)
    
    def _is_core_file(self, file_path: Path) -> bool:
        """Determinar si es archivo core."""
        core_patterns = ['main', 'api', 'rag', 'scraper', 'extractor']
        return any(pattern in str(file_path).lower() for pattern in core_patterns)
    
    def _is_utility_file(self, file_path: Path) -> bool:
        """Determinar si es archivo de utilidad."""
        utility_patterns = ['utils', 'helper', 'config', 'tools']
        return any(pattern in str(file_path).lower() for pattern in utility_patterns)
    
    def _count_dead_imports(self) -> int:
        """Contar imports no utilizados (simplificado)."""
        # This would require more sophisticated analysis
        return 0
    
    def save_metrics_report(self, output_path: Path):
        """Guardar reporte completo de métricas."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'project_metrics': asdict(self.project_metrics) if self.project_metrics else {},
            'file_metrics': {k: asdict(v) for k, v in self.file_metrics.items()},
            'function_metrics': {k: asdict(v) for k, v in self.function_metrics.items()},
            'recommendations': self.generate_refactoring_recommendations()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Reporte de métricas guardado en: {output_path}")

def main():
    """Ejecutar análisis completo de métricas."""
    project_root = Path(__file__).parent.parent  # Go up one level from tools/
    metrics_system = CodeMetricsSystem(project_root)
    
    # Analyze project
    project_metrics = metrics_system.analyze_project()
    
    # Generate recommendations
    recommendations = metrics_system.generate_refactoring_recommendations()
    
    # Save detailed report
    metrics_system.save_metrics_report(project_root / "CODE_METRICS_REPORT.json")
    
    # Print summary
    print("\\n📊 RESUMEN DE MÉTRICAS")
    print("=" * 50)
    print(f"📁 Archivos totales: {project_metrics.total_files}")
    print(f"📝 Líneas de código: {project_metrics.total_lines}")
    print(f"🔧 Funciones totales: {project_metrics.total_functions}")
    print(f"❌ Funciones huérfanas: {project_metrics.orphan_functions}")
    print(f"🧪 Archivos de test: {project_metrics.test_files}")
    print(f"💯 Score mantenibilidad: {project_metrics.maintainability_score:.1f}/100")
    print(f"📈 Complejidad promedio: {project_metrics.complexity_average:.1f}")
    
    print("\\n🎯 RECOMENDACIONES")
    print("=" * 50)
    print(f"✅ Seguras para eliminar: {len(recommendations['safe_to_delete'])}")
    print(f"🔍 Revisar para eliminar: {len(recommendations['review_for_deletion'])}")
    print(f"🧮 Simplificar complejidad: {len(recommendations['simplify_complexity'])}")
    
    # Show top candidates for deletion
    print("\\n🗑️ TOP 10 CANDIDATAS PARA ELIMINACIÓN:")
    for i, key in enumerate(recommendations['safe_to_delete'][:10], 1):
        func = metrics_system.function_metrics[key]
        score = recommendations['priority_scores'][key]
        print(f"   {i}. {func.name} ({func.file_path}) - Score: {score:.1f}")
    
    return len(recommendations['safe_to_delete'])

if __name__ == "__main__":
    sys.exit(main())