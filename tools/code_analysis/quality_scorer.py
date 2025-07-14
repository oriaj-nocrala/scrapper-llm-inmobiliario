#!/usr/bin/env python3
"""
Sistema avanzado de scoring de calidad de código.
Métricas inteligentes con scoring contextual y detección de antipatrones.
"""
import ast
import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import argparse
import math

class QualitySeverity(Enum):
    """Severidades de problemas de calidad."""
    CRITICAL = "critical"    # Bloquea desarrollo
    HIGH = "high"           # Debe corregirse pronto
    MEDIUM = "medium"       # Mejora recomendada
    LOW = "low"            # Oportunidad de mejora
    INFO = "info"          # Solo informativo

@dataclass
class QualityIssue:
    """Issue de calidad de código."""
    id: str
    type: str
    severity: QualitySeverity
    title: str
    description: str
    file_path: str
    line_number: int
    column: int
    function_name: Optional[str]
    class_name: Optional[str]
    category: str  # production, test, tooling, etc.
    score_impact: float  # Impacto en score (0-10)
    technical_debt_hours: float
    recommendation: str
    rule_violated: str
    context: Dict[str, Any]

@dataclass
class QualityMetrics:
    """Métricas de calidad de un componente."""
    component_name: str
    component_type: str  # function, class, module
    file_path: str
    category: str
    lines_of_code: int
    complexity: int
    maintainability_index: float
    test_coverage_estimate: float
    coupling_score: float
    cohesion_score: float
    documentation_score: float
    naming_score: float
    overall_score: float
    grade: str  # A, B, C, D, F
    issues: List[QualityIssue]

class QualityScorer:
    """Sistema avanzado de scoring de calidad."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = []
        self.metrics = []
        
        # Configuración de scoring por categoría
        self.category_weights = {
            'production': {
                'complexity': 0.25,
                'maintainability': 0.20,
                'documentation': 0.15,
                'naming': 0.15,
                'coupling': 0.15,
                'cohesion': 0.10
            },
            'test': {
                'complexity': 0.15,  # Menos importante en tests
                'maintainability': 0.25,
                'documentation': 0.10,  # Menos doc en tests
                'naming': 0.20,  # Naming muy importante en tests
                'coupling': 0.15,
                'cohesion': 0.15
            },
            'tooling': {
                'complexity': 0.20,
                'maintainability': 0.25,
                'documentation': 0.20,  # Tools deben estar documentados
                'naming': 0.15,
                'coupling': 0.10,
                'cohesion': 0.10
            }
        }
        
        # Antipatrones específicos
        self.antipatterns = {
            'god_class': {
                'description': 'Clase con demasiadas responsabilidades',
                'severity': QualitySeverity.HIGH,
                'thresholds': {'methods': 20, 'lines': 500}
            },
            'long_method': {
                'description': 'Método demasiado largo',
                'severity': QualitySeverity.MEDIUM,
                'thresholds': {'lines': 50, 'complexity': 15}
            },
            'feature_envy': {
                'description': 'Método que usa mucho otra clase',
                'severity': QualitySeverity.MEDIUM,
                'thresholds': {'external_calls': 5}
            },
            'shotgun_surgery': {
                'description': 'Cambio requiere tocar muchos archivos',
                'severity': QualitySeverity.HIGH,
                'thresholds': {'coupling': 8}
            },
            'dead_code': {
                'description': 'Código no utilizado',
                'severity': QualitySeverity.LOW,
                'thresholds': {}
            }
        }
    
    def analyze_project_quality(self) -> Dict[str, Any]:
        """Analizar calidad completa del proyecto."""
        print("🎯 ANÁLISIS AVANZADO DE CALIDAD DE CÓDIGO")
        print("=" * 50)
        
        # 1. Analizar componentes individuales
        print("📊 Analizando componentes individuales...")
        component_metrics = self._analyze_components()
        
        # 2. Detectar antipatrones
        print("🔍 Detectando antipatrones...")
        antipattern_issues = self._detect_antipatterns()
        
        # 3. Análisis de dependencias
        print("🔗 Analizando dependencias...")
        dependency_metrics = self._analyze_dependencies()
        
        # 4. Scoring global
        print("📈 Calculando scores globales...")
        global_scores = self._calculate_global_scores(component_metrics)
        
        # 5. Generar recomendaciones
        print("💡 Generando recomendaciones...")
        recommendations = self._generate_quality_recommendations()
        
        results = {
            'global_scores': global_scores,
            'component_metrics': [asdict(m) for m in component_metrics],
            'quality_issues': [asdict(issue) for issue in self.issues],
            'antipatterns': antipattern_issues,
            'dependency_metrics': dependency_metrics,
            'recommendations': recommendations,
            'summary': self._generate_quality_summary(global_scores, component_metrics)
        }
        
        return results
    
    def _analyze_components(self) -> List[QualityMetrics]:
        """Analizar calidad de componentes individuales."""
        metrics = []
        
        python_files = self._get_python_files()
        
        for file_path in python_files:
            try:
                category = self._categorize_file(file_path)
                file_metrics = self._analyze_file_quality(file_path, category)
                metrics.extend(file_metrics)
                
            except Exception as e:
                print(f"⚠️ Error analizando {file_path}: {e}")
        
        return metrics
    
    def _analyze_file_quality(self, file_path: Path, category: str) -> List[QualityMetrics]:
        """Analizar calidad de un archivo."""
        metrics = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        
        tree = ast.parse(content)
        
        # Analizar clases
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_metrics = self._analyze_class_quality(node, lines, file_path, category)
                metrics.append(class_metrics)
            
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Solo funciones de nivel de módulo (no métodos)
                if self._is_module_level_function(node, tree):
                    func_metrics = self._analyze_function_quality(node, lines, file_path, category)
                    metrics.append(func_metrics)
        
        return metrics
    
    def _analyze_class_quality(self, node: ast.ClassDef, lines: List[str], 
                              file_path: Path, category: str) -> QualityMetrics:
        """Analizar calidad de una clase."""
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        
        # Métricas específicas de clase
        metrics = {
            'complexity': self._calculate_complexity_for_mi(node),
            'coupling': self._calculate_coupling_score(node),
            'cohesion': self._calculate_cohesion_score(node),
            'documentation': self._calculate_documentation_score(node, methods),
            'naming': self._calculate_naming_score(node.name, [m.name for m in methods])
        }
        
        # Issues específicos
        issues = self._detect_class_issues(node, file_path, category)
        
        return self._create_quality_metrics(
            node, lines, file_path, category, "class", metrics, issues
        )
    
    def _analyze_function_quality(self, node: ast.FunctionDef, lines: List[str], 
                                 file_path: Path, category: str) -> QualityMetrics:
        """Analizar calidad de una función."""
        # Métricas específicas de función
        metrics = {
            'complexity': self._calculate_function_complexity(node),
            'coupling': self._calculate_function_coupling(node),
            'cohesion': self._calculate_function_cohesion(node),
            'documentation': self._calculate_function_documentation(node),
            'naming': self._calculate_function_naming(node)
        }
        
        # Issues específicos
        issues = self._detect_function_issues(node, file_path, category)
        
        return self._create_quality_metrics(
            node, lines, file_path, category, "function", metrics, issues
        )
    
    def _calculate_maintainability_index(self, node: ast.AST, loc: int) -> float:
        """Calcular índice de mantenibilidad."""
        # Implementación simplificada del Maintainability Index
        
        # Halstead Volume (simplificado)
        operators = set()
        operands = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.BinOp):
                operators.add(type(child.op).__name__)
            elif isinstance(child, ast.Name):
                operands.add(child.id)
        
        vocabulary = len(operators) + len(operands)
        volume = max(1, vocabulary * math.log2(vocabulary) if vocabulary > 0 else 1)
        
        # Complexity
        complexity = self._calculate_complexity_for_mi(node)
        
        # MI formula (simplificada)
        mi = max(0, 171 - 5.2 * math.log(volume) - 0.23 * complexity - 16.2 * math.log(loc))
        
        # Normalizar a 0-10
        return min(10, max(0, mi / 17.1))
    
    def _calculate_complexity_for_mi(self, node: ast.AST) -> int:
        """Calcular complejidad para MI."""
        from code_utils import calculate_complexity
        return calculate_complexity(node)
    
    def _calculate_coupling_score(self, node: ast.ClassDef) -> float:
        """Calcular score de acoplamiento de clase."""
        external_dependencies = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name):
                        external_dependencies.add(child.func.value.id)
        
        # Score inversamente proporcional al acoplamiento
        coupling_count = len(external_dependencies)
        return max(0, 10 - coupling_count)  # 0-10, donde 10 es bajo acoplamiento
    
    def _calculate_cohesion_score(self, node: ast.ClassDef) -> float:
        """Calcular score de cohesión de clase."""
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if len(methods) <= 1:
            return 10.0
        
        # Analizar variables de instancia compartidas
        instance_vars = set()
        method_var_usage = defaultdict(set)
        
        for method in methods:
            for child in ast.walk(method):
                if isinstance(child, ast.Attribute):
                    if isinstance(child.value, ast.Name) and child.value.id == 'self':
                        var_name = child.attr
                        instance_vars.add(var_name)
                        method_var_usage[method.name].add(var_name)
        
        if not instance_vars:
            return 5.0  # Sin variables de instancia
        
        # Calcular cohesión basada en variables compartidas
        shared_usage = 0
        total_pairs = 0
        
        for var in instance_vars:
            using_methods = [m for m, vars in method_var_usage.items() if var in vars]
            if len(using_methods) > 1:
                shared_usage += len(using_methods) - 1
            total_pairs += len(methods) - 1
        
        cohesion_ratio = shared_usage / total_pairs if total_pairs > 0 else 0
        return min(10, cohesion_ratio * 10)
    
    def _calculate_documentation_score(self, node: ast.ClassDef, methods: List[ast.FunctionDef]) -> float:
        """Calcular score de documentación."""
        total_components = 1 + len(methods)  # Clase + métodos
        documented_components = 0
        
        # Documentación de clase
        if ast.get_docstring(node):
            documented_components += 1
        
        # Documentación de métodos públicos
        for method in methods:
            if not method.name.startswith('_'):  # Método público
                if ast.get_docstring(method):
                    documented_components += 1
        
        return (documented_components / total_components) * 10
    
    def _calculate_naming_score(self, class_name: str, method_names: List[str]) -> float:
        """Calcular score de naming."""
        score = 0
        total_checks = 0
        
        # Naming de clase (PascalCase)
        if class_name[0].isupper() and '_' not in class_name:
            score += 1
        total_checks += 1
        
        # Naming de métodos (snake_case)
        for method_name in method_names:
            if method_name.islower() and not method_name.startswith('__'):
                score += 1
            total_checks += 1
        
        return (score / total_checks) * 10 if total_checks > 0 else 10
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> float:
        """Calcular complejidad de función (0-10)."""
        complexity = self._calculate_complexity_for_mi(node)
        # Normalizar: 1-5 = 10, 6-10 = 8, 11-15 = 6, etc.
        return max(0, 12 - complexity)
    
    def _calculate_function_coupling(self, node: ast.FunctionDef) -> float:
        """Calcular acoplamiento de función."""
        external_calls = 0
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                external_calls += 1
        
        # Score inversamente proporcional
        return max(0, 10 - external_calls / 2)
    
    def _calculate_function_cohesion(self, node: ast.FunctionDef) -> float:
        """Calcular cohesión de función."""
        # Para funciones, cohesión = qué tan enfocada está en una tarea
        
        # Contar diferentes tipos de operaciones
        operation_types = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                operation_types.add('call')
            elif isinstance(child, ast.Assign):
                operation_types.add('assign')
            elif isinstance(child, ast.If):
                operation_types.add('conditional')
            elif isinstance(child, (ast.For, ast.While)):
                operation_types.add('loop')
            elif isinstance(child, ast.Return):
                operation_types.add('return')
        
        # Menos tipos de operación = más cohesión
        diversity = len(operation_types)
        return max(0, 10 - diversity)
    
    def _calculate_function_documentation(self, node: ast.FunctionDef) -> float:
        """Calcular documentación de función."""
        score = 0
        
        # Tiene docstring
        if ast.get_docstring(node):
            score += 5
        
        # Tiene type hints
        if node.returns or any(arg.annotation for arg in node.args.args):
            score += 3
        
        # Nombre descriptivo
        if len(node.name) > 3 and not node.name.startswith('_'):
            score += 2
        
        return min(10, score)
    
    def _calculate_function_naming(self, node: ast.FunctionDef) -> float:
        """Calcular calidad del naming de función."""
        score = 0
        name = node.name
        
        # snake_case
        if name.islower() and ('_' in name or len(name) <= 8):
            score += 3
        
        # Descriptivo
        if len(name) >= 4:
            score += 2
        
        # No abreviaciones
        common_abbrevs = ['calc', 'proc', 'mgr', 'util']
        if not any(abbrev in name for abbrev in common_abbrevs):
            score += 2
        
        # Verbo para funciones
        action_words = ['get', 'set', 'create', 'update', 'delete', 'process', 'handle', 'validate']
        if any(action in name for action in action_words):
            score += 3
        
        return min(10, score)
    
    def _detect_antipatterns(self) -> Dict[str, List[Dict]]:
        """Detectar antipatrones específicos."""
        antipatterns_found = defaultdict(list)
        
        python_files = self._get_python_files()
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Detectar God Class
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        god_class = self._check_god_class(node, file_path)
                        if god_class:
                            antipatterns_found['god_class'].append(god_class)
                
                # Detectar Long Method
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        long_method = self._check_long_method(node, file_path)
                        if long_method:
                            antipatterns_found['long_method'].append(long_method)
                
            except Exception as e:
                print(f"⚠️ Error detectando antipatrones en {file_path}: {e}")
        
        return dict(antipatterns_found)
    
    def _check_god_class(self, node: ast.ClassDef, file_path: Path) -> Optional[Dict]:
        """Verificar si es God Class."""
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        lines = node.end_lineno - node.lineno if node.end_lineno else 0
        
        thresholds = self.antipatterns['god_class']['thresholds']
        
        if len(methods) > thresholds['methods'] or lines > thresholds['lines']:
            return {
                'type': 'god_class',
                'name': node.name,
                'file': str(file_path.relative_to(self.project_root)),
                'line': node.lineno,
                'metrics': {
                    'methods': len(methods),
                    'lines': lines
                },
                'severity': self.antipatterns['god_class']['severity'].value,
                'description': f"Clase {node.name} tiene {len(methods)} métodos y {lines} líneas"
            }
        return None
    
    def _check_long_method(self, node: ast.FunctionDef, file_path: Path) -> Optional[Dict]:
        """Verificar si es Long Method."""
        lines = node.end_lineno - node.lineno if node.end_lineno else 0
        complexity = self._calculate_complexity_for_mi(node)
        
        thresholds = self.antipatterns['long_method']['thresholds']
        
        if lines > thresholds['lines'] or complexity > thresholds['complexity']:
            return {
                'type': 'long_method',
                'name': node.name,
                'file': str(file_path.relative_to(self.project_root)),
                'line': node.lineno,
                'metrics': {
                    'lines': lines,
                    'complexity': complexity
                },
                'severity': self.antipatterns['long_method']['severity'].value,
                'description': f"Método {node.name} tiene {lines} líneas y complejidad {complexity}"
            }
        return None
    
    def _detect_class_issues(self, node: ast.ClassDef, file_path: Path, category: str) -> List[QualityIssue]:
        """Detectar issues específicos de clase."""
        issues = []
        
        # Issue: Missing docstring
        if not ast.get_docstring(node) and category == 'production':
            issues.append(QualityIssue(
                id=f"missing_class_doc_{node.name}",
                type="documentation",
                severity=QualitySeverity.MEDIUM,
                title="Missing class documentation",
                description=f"Class {node.name} lacks documentation",
                file_path=str(file_path.relative_to(self.project_root)),
                line_number=node.lineno,
                column=0,
                function_name=None,
                class_name=node.name,
                category=category,
                score_impact=1.0,
                technical_debt_hours=0.5,
                recommendation="Add comprehensive docstring describing class purpose and usage",
                rule_violated="PEP257 - Docstring Conventions",
                context={'class_name': node.name}
            ))
        
        return issues
    
    def _detect_function_issues(self, node: ast.FunctionDef, file_path: Path, category: str) -> List[QualityIssue]:
        """Detectar issues específicos de función."""
        issues = []
        
        # Issue: High complexity
        complexity = self._calculate_complexity_for_mi(node)
        if complexity > 15:
            issues.append(QualityIssue(
                id=f"high_complexity_{node.name}",
                type="complexity",
                severity=QualitySeverity.HIGH if complexity > 20 else QualitySeverity.MEDIUM,
                title="High cyclomatic complexity",
                description=f"Function {node.name} has complexity {complexity}",
                file_path=str(file_path.relative_to(self.project_root)),
                line_number=node.lineno,
                column=0,
                function_name=node.name,
                class_name=None,
                category=category,
                score_impact=complexity / 5,
                technical_debt_hours=complexity * 0.1,
                recommendation="Break down into smaller functions or simplify logic",
                rule_violated="Cyclomatic Complexity > 15",
                context={'complexity': complexity}
            ))
        
        return issues
    
    def _create_quality_metrics(self, node: ast.AST, lines: List[str], 
                               file_path: Path, category: str, component_type: str,
                               metrics: Dict[str, float], issues: List) -> QualityMetrics:
        """Crear métricas de calidad común para clases y funciones."""
        component_name = node.name
        start_line = node.lineno
        end_line = node.end_lineno or len(lines)
        loc = end_line - start_line
        
        # Calcular maintainability
        maintainability = self._calculate_maintainability_index(node, loc)
        
        # Score overall ponderado por categoría
        weights = self.category_weights.get(category, self.category_weights['production'])
        overall_score = (
            metrics['complexity'] * weights['complexity'] +
            maintainability * weights['maintainability'] +
            metrics['documentation'] * weights['documentation'] +
            metrics['naming'] * weights['naming'] +
            metrics['coupling'] * weights['coupling'] +
            metrics['cohesion'] * weights['cohesion']
        )
        
        # Agregar issues al tracking global
        self.issues.extend(issues)
        
        return QualityMetrics(
            component_name=component_name,
            component_type=component_type,
            file_path=str(file_path.relative_to(self.project_root)),
            category=category,
            lines_of_code=loc,
            complexity=metrics['complexity'],
            maintainability_index=maintainability,
            test_coverage_estimate=self._estimate_test_coverage(component_name),
            coupling_score=metrics['coupling'],
            cohesion_score=metrics['cohesion'],
            documentation_score=metrics['documentation'],
            naming_score=metrics['naming'],
            overall_score=overall_score,
            grade=self._score_to_grade(overall_score),
            issues=issues
        )
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analizar métricas de dependencias."""
        # Implementación básica
        return {
            'circular_dependencies': [],
            'high_coupling_modules': [],
            'instability_metrics': {}
        }
    
    def _calculate_global_scores(self, metrics: List[QualityMetrics]) -> Dict[str, float]:
        """Calcular scores globales del proyecto."""
        if not metrics:
            return {}
        
        # Agrupar por categoría
        by_category = defaultdict(list)
        for metric in metrics:
            by_category[metric.category].append(metric)
        
        global_scores = {}
        
        for category, cat_metrics in by_category.items():
            scores = {
                'overall': sum(m.overall_score for m in cat_metrics) / len(cat_metrics),
                'maintainability': sum(m.maintainability_index for m in cat_metrics) / len(cat_metrics),
                'complexity': sum(m.complexity for m in cat_metrics) / len(cat_metrics),
                'documentation': sum(m.documentation_score for m in cat_metrics) / len(cat_metrics),
                'coupling': sum(m.coupling_score for m in cat_metrics) / len(cat_metrics),
                'component_count': len(cat_metrics)
            }
            global_scores[category] = scores
        
        # Score total del proyecto
        all_scores = [m.overall_score for m in metrics]
        global_scores['project_overall'] = sum(all_scores) / len(all_scores) if all_scores else 0
        
        return global_scores
    
    def _generate_quality_recommendations(self) -> List[Dict]:
        """Generar recomendaciones de calidad."""
        recommendations = []
        
        # Agrupar issues por severidad
        critical_issues = [i for i in self.issues if i.severity == QualitySeverity.CRITICAL]
        high_issues = [i for i in self.issues if i.severity == QualitySeverity.HIGH]
        
        if critical_issues:
            recommendations.append({
                'priority': 1,
                'type': 'critical_quality',
                'title': f"Resolver {len(critical_issues)} issues críticos",
                'description': "Issues que bloquean el desarrollo",
                'impact': f"{sum(i.technical_debt_hours for i in critical_issues):.1f} horas",
                'action': "Refactorizar componentes críticos inmediatamente"
            })
        
        if high_issues:
            recommendations.append({
                'priority': 2,
                'type': 'high_quality', 
                'title': f"Abordar {len(high_issues)} issues de alta prioridad",
                'description': "Mejoras importantes de calidad",
                'impact': f"{sum(i.technical_debt_hours for i in high_issues):.1f} horas",
                'action': "Planificar refactoring en próximo sprint"
            })
        
        return recommendations
    
    def _generate_quality_summary(self, global_scores: Dict, metrics: List[QualityMetrics]) -> Dict:
        """Generar resumen de calidad."""
        return {
            'project_grade': self._score_to_grade(global_scores.get('project_overall', 0)),
            'total_components': len(metrics),
            'total_issues': len(self.issues),
            'technical_debt_hours': sum(i.technical_debt_hours for i in self.issues),
            'categories_analyzed': list(global_scores.keys()),
            'best_category': max(global_scores.items(), key=lambda x: x[1].get('overall', 0) if isinstance(x[1], dict) else 0)[0] if global_scores else None,
            'worst_category': min(global_scores.items(), key=lambda x: x[1].get('overall', 0) if isinstance(x[1], dict) else 0)[0] if global_scores else None
        }
    
    # Métodos auxiliares
    def _get_python_files(self) -> List[Path]:
        """Obtener archivos Python."""
        python_files = list(self.project_root.rglob("*.py"))
        exclude_dirs = {'env', '__pycache__', '.git', 'refactor_backup'}
        return [f for f in python_files if not any(excluded in f.parts for excluded in exclude_dirs)]
    
    def _categorize_file(self, file_path: Path) -> str:
        """Categorizar archivo."""
        parts = file_path.relative_to(self.project_root).parts
        
        if not parts:
            return 'other'
        
        first_dir = parts[0].lower()
        
        if first_dir == 'src':
            return 'production'
        elif first_dir == 'tests':
            return 'test'
        elif first_dir == 'tools':
            return 'tooling'
        else:
            return 'other'
    
    def _is_module_level_function(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Verificar si es función de nivel de módulo."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return False
        return True
    
    def _estimate_test_coverage(self, component_name: str) -> float:
        """Estimar cobertura de tests (placeholder)."""
        # Implementación básica - en producción usaría herramientas reales
        return 70.0 if not component_name.startswith('_') else 40.0
    
    def _score_to_grade(self, score: float) -> str:
        """Convertir score numérico a letra."""
        if score >= 9:
            return 'A'
        elif score >= 7:
            return 'B'
        elif score >= 5:
            return 'C'
        elif score >= 3:
            return 'D'
        else:
            return 'F'
    
    def print_quality_results(self, results: Dict, verbose: bool = False):
        """Mostrar resultados de calidad."""
        summary = results['summary']
        global_scores = results['global_scores']
        
        print(f"\n🎯 ANÁLISIS DE CALIDAD DE CÓDIGO")
        print("=" * 40)
        print(f"📊 Grade del proyecto: {summary['project_grade']}")
        print(f"🔧 Componentes analizados: {summary['total_components']}")
        print(f"⚠️ Issues encontrados: {summary['total_issues']}")
        print(f"⏱️ Deuda técnica: {summary['technical_debt_hours']:.1f} horas")
        
        # Scores por categoría
        if global_scores:
            print(f"\n📈 SCORES POR CATEGORÍA:")
            for category, scores in global_scores.items():
                if isinstance(scores, dict) and 'overall' in scores:
                    grade = self._score_to_grade(scores['overall'])
                    print(f"   {category.capitalize()}: {scores['overall']:.1f}/10 ({grade}) - {scores['component_count']} componentes")
        
        # Top issues
        if results['quality_issues']:
            print(f"\n⚠️ TOP ISSUES DE CALIDAD:")
            critical_and_high = [i for i in results['quality_issues'] 
                               if i['severity'] in ['critical', 'high']]
            
            for i, issue in enumerate(critical_and_high[:5], 1):
                severity_icon = {'critical': '🔴', 'high': '🟡', 'medium': '🟠', 'low': '🟢'}[issue['severity']]
                print(f"   {i}. {severity_icon} {issue['title']}")
                print(f"      📂 {issue['file_path']}:{issue['line_number']}")
                if verbose:
                    print(f"      💡 {issue['recommendation']}")
        
        # Antipatrones
        if results['antipatterns']:
            print(f"\n🚨 ANTIPATRONES DETECTADOS:")
            for pattern_type, instances in results['antipatterns'].items():
                if instances:
                    print(f"   {pattern_type.replace('_', ' ').title()}: {len(instances)} instancias")
                    if verbose:
                        for instance in instances[:2]:
                            print(f"      📄 {instance['name']} en {instance['file']}:{instance['line']}")
        
        # Recomendaciones
        if results['recommendations']:
            print(f"\n💡 RECOMENDACIONES DE CALIDAD:")
            for rec in results['recommendations']:
                print(f"   {rec['priority']}. {rec['title']}")
                print(f"      📊 {rec['description']} | ⏱️ {rec['impact']}")
                if verbose:
                    print(f"      🔧 {rec['action']}")

def main():
    """Función principal del quality scorer."""
    parser = argparse.ArgumentParser(description='Análisis avanzado de calidad de código')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostrar información detallada')
    parser.add_argument('--output', '-o', type=str,
                       help='Archivo de salida JSON')
    parser.add_argument('--category', type=str,
                       help='Analizar solo una categoría específica')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    scorer = QualityScorer(project_root)
    
    # Ejecutar análisis
    results = scorer.analyze_project_quality()
    
    # Mostrar resultados
    scorer.print_quality_results(results, verbose=args.verbose)
    
    # Guardar si se especifica
    if args.output:
        output_file = Path(args.output)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"💾 Resultados guardados en: {output_file}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())