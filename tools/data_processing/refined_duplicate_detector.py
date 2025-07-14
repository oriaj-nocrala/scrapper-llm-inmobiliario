#!/usr/bin/env python3
"""
Detector refinado de código duplicado con filtros inteligentes.
Reduce falsos positivos y se enfoca en duplicados problemáticos.
"""
import ast
import hashlib
import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
from difflib import SequenceMatcher
from dataclasses import dataclass
import argparse

@dataclass
class IntelligentCluster:
    """Cluster de duplicados con análisis inteligente."""
    id: str
    type: str  # exact, semantic, structural
    severity: str  # critical, high, medium, low, ignore
    confidence: float  # 0-1
    functions: List[Dict]
    similarity_score: float
    lines_saved: int
    hours_saved: float
    category_analysis: Dict
    recommendation: str
    should_refactor: bool

class FunctionExtractor:
    """Extractor especializado de funciones."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root

class DuplicateFilter:
    """Filtro especializado para falsos positivos."""
    
    def __init__(self):
        # Patrones de funciones que típicamente son similares (falsos positivos)
        self.common_patterns = {
            'getters': ['get_', 'fetch_', 'retrieve_'],
            'setters': ['set_', 'update_', 'save_'],
            'validators': ['validate_', 'check_', 'verify_'],
            'converters': ['convert_', 'transform_', 'format_'],
            'test_helpers': ['setup_', 'teardown_', 'create_test_', 'mock_'],
            'property_accessors': ['@property', 'def __get__', 'def __set__']
        }
        
        # Código que es naturalmente similar
        self.acceptable_similarity_patterns = {
            'crud_operations': ['create', 'read', 'update', 'delete'],
            'error_handlers': ['except', 'try', 'raise', 'error'],
            'initialization': ['__init__', 'setup', 'configure'],
            'cleanup': ['cleanup', 'teardown', 'close', 'destroy']
        }

class ClusterAnalyzer:
    """Analizador especializado de clusters de duplicados."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

class RefinedDuplicateDetector:
    """Detector refinado con filtros inteligentes (refactorizado)."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.min_lines = 5
        self.similarity_threshold = 0.85
        
        # Inicializar componentes especializados
        self.function_extractor = FunctionExtractor(project_root)
        self.duplicate_filter = DuplicateFilter()
        self.cluster_analyzer = ClusterAnalyzer(self.similarity_threshold)
    
    def detect_intelligent_duplicates(self) -> Dict:
        """Detectar duplicados con análisis inteligente."""
        print("🧠 DETECCIÓN INTELIGENTE DE CÓDIGO DUPLICADO")
        print("=" * 50)
        
        # Extraer funciones con metadata enriquecida
        functions = self._extract_enriched_functions()
        print(f"📊 Analizando {len(functions)} funciones con contexto...")
        
        # Filtrar candidatos problemáticos
        candidates = self._filter_problematic_candidates(functions)
        print(f"🎯 {len(candidates)} candidatos problemáticos identificados...")
        
        # Detectar clusters inteligentes
        clusters = self._detect_intelligent_clusters(candidates)
        
        # Analizar y clasificar clusters
        analyzed_clusters = self._analyze_clusters(clusters)
        
        # Generar recomendaciones específicas
        recommendations = self._generate_smart_recommendations(analyzed_clusters)
        
        results = {
            'intelligent_clusters': analyzed_clusters,
            'recommendations': recommendations,
            'summary': self._generate_intelligent_summary(analyzed_clusters),
            'false_positives_filtered': len(functions) - len(candidates),
            'analysis_metadata': {
                'total_functions': len(functions),
                'problematic_candidates': len(candidates),
                'clusters_found': len(analyzed_clusters)
            }
        }
        
        return results
    
    def _extract_enriched_functions(self) -> List[Dict]:
        """Extraer funciones con metadata enriquecida."""
        functions = []
        
        python_files = self._get_python_files()
        
        for file_path in python_files:
            try:
                category = self._categorize_file(file_path)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                lines = content.splitlines()
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if hasattr(node, 'end_lineno') and node.end_lineno:
                            func_info = self._extract_function_info(node, lines, file_path, category)
                            if func_info and func_info['lines_count'] >= self.min_lines:
                                functions.append(func_info)
                        
            except Exception as e:
                print(f"⚠️ Error procesando {file_path}: {e}")
        
        return functions
    
    def _extract_function_info(self, node: ast.FunctionDef, lines: List[str], 
                              file_path: Path, category: str) -> Optional[Dict]:
        """Extraer información enriquecida de función."""
        func_lines = lines[node.lineno-1:node.end_lineno]
        func_content = '\n'.join(func_lines)
        
        # Análisis de patrones
        patterns = self._analyze_function_patterns(node, func_content)
        
        # Complejidad y métricas
        complexity = self._calculate_complexity(node)
        
        # Contexto del archivo
        file_context = self._analyze_file_context(file_path)
        
        return {
            'name': node.name,
            'file': str(file_path.relative_to(self.project_root)),
            'category': category,
            'line_start': node.lineno,
            'line_end': node.end_lineno,
            'content': func_content,
            'normalized': self._normalize_code(func_content),
            'lines_count': len(func_lines),
            'complexity': complexity,
            'patterns': patterns,
            'file_context': file_context,
            'docstring': ast.get_docstring(node) or '',
            'is_private': node.name.startswith('_'),
            'is_test': self._is_test_function(node.name, str(file_path)),
            'function_type': self._classify_function_type(node, func_content)
        }
    
    def _analyze_function_patterns(self, node: ast.FunctionDef, content: str) -> Dict:
        """Analizar patrones en la función."""
        patterns = {
            'is_getter': any(pattern in node.name.lower() for pattern in self.common_patterns['getters']),
            'is_setter': any(pattern in node.name.lower() for pattern in self.common_patterns['setters']),
            'is_validator': any(pattern in node.name.lower() for pattern in self.common_patterns['validators']),
            'is_converter': any(pattern in node.name.lower() for pattern in self.common_patterns['converters']),
            'is_test_helper': any(pattern in node.name.lower() for pattern in self.common_patterns['test_helpers']),
            'has_property_decorator': '@property' in content,
            'has_try_except': 'try:' in content and 'except' in content,
            'has_loops': any(isinstance(child, (ast.For, ast.While)) for child in ast.walk(node)),
            'return_count': len([n for n in ast.walk(node) if isinstance(n, ast.Return)]),
            'parameter_count': len(node.args.args)
        }
        
        # Detectar CRUD operations
        crud_keywords = ['create', 'read', 'update', 'delete', 'insert', 'select', 'modify']
        patterns['is_crud'] = any(keyword in node.name.lower() for keyword in crud_keywords)
        
        return patterns
    
    def _classify_function_type(self, node: ast.FunctionDef, content: str) -> str:
        """Clasificar tipo de función."""
        if node.name.startswith('test_'):
            return 'test'
        elif node.name.startswith('_') and not node.name.startswith('__'):
            return 'private'
        elif node.name.startswith('__') and node.name.endswith('__'):
            return 'magic'
        elif '@property' in content:
            return 'property'
        elif any(keyword in content.lower() for keyword in ['yield', 'generator']):
            return 'generator'
        elif 'async def' in content:
            return 'async'
        else:
            return 'regular'
    
    def _filter_problematic_candidates(self, functions: List[Dict]) -> List[Dict]:
        """Filtrar candidatos que son problemáticos para duplicación."""
        candidates = []
        
        for func in functions:
            # Filtrar funciones que naturalmente son similares
            if self._is_acceptable_similarity(func):
                continue
            
            # Filtrar funciones muy simples
            if func['lines_count'] < 8 and func['complexity'] <= 2:
                continue
            
            # Priorizar funciones de producción
            if func['category'] == 'production' or func['category'] == 'tooling':
                candidates.append(func)
            elif func['category'] == 'test' and func['lines_count'] > 15:
                # Solo tests complejos
                candidates.append(func)
        
        return candidates
    
    def _is_acceptable_similarity(self, func: Dict) -> bool:
        """Determinar si la similitud es aceptable (no problemática)."""
        patterns = func['patterns']
        
        # Getters/setters simples son aceptablemente similares
        if (patterns['is_getter'] or patterns['is_setter']) and func['lines_count'] < 10:
            return True
        
        # Validadores simples
        if patterns['is_validator'] and func['complexity'] <= 3:
            return True
        
        # Test helpers
        if patterns['is_test_helper']:
            return True
        
        # Properties simples
        if patterns['has_property_decorator'] and func['lines_count'] < 8:
            return True
        
        # Magic methods simples
        if func['function_type'] == 'magic' and func['lines_count'] < 12:
            return True
        
        return False
    
    def _detect_intelligent_clusters(self, candidates: List[Dict]) -> List[IntelligentCluster]:
        """Detectar clusters con análisis inteligente."""
        clusters = []
        
        # 1. Duplicados exactos (más críticos)
        exact_clusters = self._find_exact_clusters(candidates)
        clusters.extend(exact_clusters)
        
        # 2. Duplicados semánticos (estructura similar)
        semantic_clusters = self._find_semantic_clusters(candidates)
        clusters.extend(semantic_clusters)
        
        # 3. Duplicados estructurales (lógica similar)
        structural_clusters = self._find_structural_clusters(candidates)
        clusters.extend(structural_clusters)
        
        return clusters
    
    def _find_exact_clusters(self, candidates: List[Dict]) -> List[IntelligentCluster]:
        """Encontrar clusters exactos con análisis inteligente."""
        hash_groups = defaultdict(list)
        
        for func in candidates:
            code_hash = hashlib.md5(func['normalized'].encode()).hexdigest()
            hash_groups[code_hash].append(func)
        
        clusters = []
        for code_hash, group in hash_groups.items():
            if len(group) >= 2:
                cluster = IntelligentCluster(
                    id=f"exact_{code_hash[:8]}",
                    type="exact",
                    severity="critical",  # Duplicados exactos son siempre críticos
                    confidence=1.0,
                    functions=group,
                    similarity_score=1.0,
                    lines_saved=(len(group) - 1) * group[0]['lines_count'],
                    hours_saved=(len(group) - 1) * group[0]['lines_count'] * 0.1,
                    category_analysis=self._analyze_cluster_categories(group),
                    recommendation=self._generate_exact_recommendation(group),
                    should_refactor=True
                )
                clusters.append(cluster)
        
        return sorted(clusters, key=lambda x: x.lines_saved, reverse=True)
    
    def _find_semantic_clusters(self, candidates: List[Dict]) -> List[IntelligentCluster]:
        """Encontrar clusters semánticamente similares."""
        clusters = []
        processed = set()
        
        for i, func1 in enumerate(candidates):
            if i in processed:
                continue
            
            similar_funcs = [func1]
            
            for j, func2 in enumerate(candidates[i+1:], i+1):
                if j in processed:
                    continue
                
                if self._are_semantically_similar(func1, func2):
                    similar_funcs.append(func2)
                    processed.add(j)
            
            if len(similar_funcs) >= 2:
                processed.add(i)
                
                severity = self._calculate_cluster_severity(similar_funcs)
                confidence = self._calculate_cluster_confidence(similar_funcs)
                
                cluster = IntelligentCluster(
                    id=f"semantic_{i}_{len(similar_funcs)}",
                    type="semantic",
                    severity=severity,
                    confidence=confidence,
                    functions=similar_funcs,
                    similarity_score=self._calculate_avg_similarity(similar_funcs),
                    lines_saved=self._calculate_semantic_savings(similar_funcs),
                    hours_saved=self._calculate_semantic_savings(similar_funcs) * 0.1,
                    category_analysis=self._analyze_cluster_categories(similar_funcs),
                    recommendation=self._generate_semantic_recommendation(similar_funcs),
                    should_refactor=severity in ['critical', 'high'] and confidence > 0.7
                )
                clusters.append(cluster)
        
        return sorted(clusters, key=lambda x: x.confidence * x.lines_saved, reverse=True)[:8]
    
    def _are_semantically_similar(self, func1: Dict, func2: Dict) -> bool:
        """Determinar si dos funciones son semánticamente similares."""
        # Similitud textual base
        text_similarity = SequenceMatcher(None, func1['normalized'], func2['normalized']).ratio()
        
        if text_similarity < self.similarity_threshold:
            return False
        
        # Análisis de patrones
        pattern_similarity = self._calculate_pattern_similarity(func1, func2)
        
        # Análisis estructural
        structural_similarity = self._calculate_structural_similarity(func1, func2)
        
        # Score combinado
        combined_score = (text_similarity * 0.4 + pattern_similarity * 0.3 + structural_similarity * 0.3)
        
        return combined_score >= 0.8
    
    def _calculate_pattern_similarity(self, func1: Dict, func2: Dict) -> float:
        """Calcular similitud de patrones entre funciones."""
        patterns1 = func1['patterns']
        patterns2 = func2['patterns']
        
        # Comparar patrones booleanos
        bool_patterns = ['is_getter', 'is_setter', 'is_validator', 'is_converter', 'is_crud']
        matching_patterns = sum(1 for p in bool_patterns if patterns1[p] == patterns2[p])
        
        # Comparar métricas numéricas
        numeric_similarity = 0
        if patterns1['return_count'] == patterns2['return_count']:
            numeric_similarity += 0.2
        if abs(patterns1['parameter_count'] - patterns2['parameter_count']) <= 1:
            numeric_similarity += 0.2
        
        return (matching_patterns / len(bool_patterns)) * 0.8 + numeric_similarity
    
    def _calculate_structural_similarity(self, func1: Dict, func2: Dict) -> float:
        """Calcular similitud estructural."""
        # Similitud de complejidad
        complexity_diff = abs(func1['complexity'] - func2['complexity'])
        complexity_similarity = max(0, 1 - complexity_diff / 10)
        
        # Similitud de longitud
        length_diff = abs(func1['lines_count'] - func2['lines_count'])
        length_similarity = max(0, 1 - length_diff / 20)
        
        # Mismo tipo de función
        type_similarity = 1.0 if func1['function_type'] == func2['function_type'] else 0.5
        
        return (complexity_similarity + length_similarity + type_similarity) / 3
    
    def _find_structural_clusters(self, candidates: List[Dict]) -> List[IntelligentCluster]:
        """Encontrar clusters con estructura similar."""
        # Agrupar por patrones estructurales
        structural_groups = defaultdict(list)
        
        for func in candidates:
            # Crear clave estructural
            structural_key = (
                func['function_type'],
                func['patterns']['is_crud'],
                func['patterns']['has_try_except'],
                func['patterns']['has_loops'],
                min(func['complexity'] // 3, 5)  # Agrupar por rangos de complejidad
            )
            structural_groups[structural_key].append(func)
        
        clusters = []
        for structural_key, group in structural_groups.items():
            if len(group) >= 3:  # Al menos 3 funciones con estructura similar
                # Verificar que realmente sean problemáticamente similares
                text_similarities = []
                for i in range(len(group)):
                    for j in range(i+1, len(group)):
                        sim = SequenceMatcher(None, group[i]['normalized'], group[j]['normalized']).ratio()
                        text_similarities.append(sim)
                
                avg_similarity = sum(text_similarities) / len(text_similarities)
                
                if avg_similarity >= 0.7:  # Estructuralmente Y textualmente similares
                    cluster = IntelligentCluster(
                        id=f"structural_{hash(structural_key) % 10000}",
                        type="structural",
                        severity=self._calculate_cluster_severity(group),
                        confidence=avg_similarity,
                        functions=group,
                        similarity_score=avg_similarity,
                        lines_saved=sum(func['lines_count'] for func in group[1:]) // 2,
                        hours_saved=sum(func['lines_count'] for func in group[1:]) * 0.05,
                        category_analysis=self._analyze_cluster_categories(group),
                        recommendation=self._generate_structural_recommendation(group, structural_key),
                        should_refactor=avg_similarity > 0.8 and len(group) >= 4
                    )
                    clusters.append(cluster)
        
        return sorted(clusters, key=lambda x: len(x.functions) * x.confidence, reverse=True)[:5]
    
    def _analyze_clusters(self, clusters: List[IntelligentCluster]) -> List[IntelligentCluster]:
        """Analizar y enriquecer clusters."""
        for cluster in clusters:
            # Análisis de categorías
            cluster.category_analysis = self._analyze_cluster_categories(cluster.functions)
            
            # Recalcular severidad si es necesario
            if cluster.type != 'exact':
                cluster.severity = self._calculate_cluster_severity(cluster.functions)
            
            # Verificar si debe refactorizarse
            cluster.should_refactor = self._should_refactor_cluster(cluster)
        
        return clusters
    
    def _calculate_cluster_severity(self, functions: List[Dict]) -> str:
        """Calcular severidad del cluster."""
        # Funciones de producción tienen mayor severidad
        production_count = sum(1 for f in functions if f['category'] == 'production')
        
        avg_complexity = sum(f['complexity'] for f in functions) / len(functions)
        avg_lines = sum(f['lines_count'] for f in functions) / len(functions)
        
        if production_count >= 2 and avg_lines > 20:
            return 'critical'
        elif production_count >= 1 and avg_complexity > 8:
            return 'high'
        elif len(functions) >= 4 or avg_lines > 15:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_cluster_confidence(self, functions: List[Dict]) -> float:
        """Calcular confianza del cluster."""
        # Factores que aumentan confianza
        confidence = 0.5  # Base
        
        # Mismo archivo/categoría
        categories = set(f['category'] for f in functions)
        if len(categories) == 1:
            confidence += 0.2
        
        # Funciones grandes
        avg_lines = sum(f['lines_count'] for f in functions) / len(functions)
        if avg_lines > 20:
            confidence += 0.2
        
        # Alta complejidad
        avg_complexity = sum(f['complexity'] for f in functions) / len(functions)
        if avg_complexity > 10:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _should_refactor_cluster(self, cluster: IntelligentCluster) -> bool:
        """Determinar si un cluster debe refactorizarse."""
        # Siempre refactorizar duplicados exactos
        if cluster.type == 'exact':
            return True
        
        # Criterios para refactoring
        criteria = [
            cluster.severity in ['critical', 'high'],
            cluster.confidence > 0.7,
            cluster.lines_saved > 15,
            len(cluster.functions) >= 3
        ]
        
        return sum(criteria) >= 2
    
    # Métodos auxiliares (continuación en siguientes partes)
    def _analyze_cluster_categories(self, functions: List[Dict]) -> Dict:
        """Analizar categorías del cluster."""
        categories = defaultdict(int)
        for func in functions:
            categories[func['category']] += 1
        
        return {
            'categories': dict(categories),
            'is_cross_category': len(categories) > 1,
            'dominant_category': max(categories.items(), key=lambda x: x[1])[0]
        }
    
    def _generate_exact_recommendation(self, functions: List[Dict]) -> str:
        """Generar recomendación para duplicados exactos."""
        category_analysis = self._analyze_cluster_categories(functions)
        dominant_cat = category_analysis['dominant_category']
        
        if dominant_cat == 'production':
            return f"🔴 CRÍTICO: Extraer a función común en src/utils - {len(functions)} duplicados exactos en producción"
        elif dominant_cat == 'test':
            return f"🟡 Crear test helper común - {len(functions)} tests duplicados"
        else:
            return f"📋 Extraer a utilidad común - {len(functions)} duplicados en {dominant_cat}"
    
    def _generate_semantic_recommendation(self, functions: List[Dict]) -> str:
        """Generar recomendación para duplicados semánticos."""
        category_analysis = self._analyze_cluster_categories(functions)
        avg_lines = sum(f['lines_count'] for f in functions) / len(functions)
        
        if category_analysis['is_cross_category']:
            return f"🔧 Crear abstracción común cross-module - {len(functions)} funciones similares ({avg_lines:.0f} líneas promedio)"
        else:
            return f"🔄 Refactorizar similitudes en {category_analysis['dominant_category']} - {len(functions)} funciones"
    
    def _generate_structural_recommendation(self, functions: List[Dict], structural_key: tuple) -> str:
        """Generar recomendación para duplicados estructurales."""
        func_type, is_crud, has_try_except, has_loops, complexity_range = structural_key
        
        if is_crud:
            return f"🗂️ Considerar patrón Repository/DAO - {len(functions)} operaciones CRUD similares"
        elif has_try_except:
            return f"⚠️ Extraer manejo de errores común - {len(functions)} funciones con try/except similar"
        elif has_loops:
            return f"🔄 Abstraer lógica de iteración - {len(functions)} funciones con loops similares"
        else:
            return f"🏗️ Considerar patrón común - {len(functions)} funciones {func_type} estructuralmente similares"
    
    def _calculate_avg_similarity(self, functions: List[Dict]) -> float:
        """Calcular similitud promedio entre funciones."""
        similarities = []
        for i in range(len(functions)):
            for j in range(i+1, len(functions)):
                sim = SequenceMatcher(None, functions[i]['normalized'], functions[j]['normalized']).ratio()
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _calculate_semantic_savings(self, functions: List[Dict]) -> int:
        """Calcular ahorros semánticos."""
        avg_lines = sum(f['lines_count'] for f in functions) / len(functions)
        return int(avg_lines * (len(functions) - 1) * 0.7)  # 70% de ahorro estimado
    
    def _generate_smart_recommendations(self, clusters: List[IntelligentCluster]) -> List[Dict]:
        """Generar recomendaciones inteligentes priorizadas."""
        recommendations = []
        
        # Ordenar clusters por impacto
        sorted_clusters = sorted(clusters, key=lambda x: (
            {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[x.severity],
            x.confidence,
            x.lines_saved
        ), reverse=True)
        
        for i, cluster in enumerate(sorted_clusters[:10], 1):
            if cluster.should_refactor:
                recommendations.append({
                    'priority': i,
                    'severity': cluster.severity,
                    'type': f'duplicate_{cluster.type}',
                    'title': f"{cluster.recommendation}",
                    'description': f"{len(cluster.functions)} funciones {cluster.similarity_score:.0%} similares",
                    'impact': f"{cluster.lines_saved} líneas, {cluster.hours_saved:.1f} horas",
                    'confidence': f"{cluster.confidence:.0%}",
                    'categories': list(cluster.category_analysis['categories'].keys()),
                    'should_refactor': cluster.should_refactor,
                    'cluster_id': cluster.id
                })
        
        return recommendations
    
    def _generate_intelligent_summary(self, clusters: List[IntelligentCluster]) -> Dict:
        """Generar resumen inteligente."""
        total_lines_saved = sum(c.lines_saved for c in clusters)
        total_hours_saved = sum(c.hours_saved for c in clusters)
        
        severity_counts = defaultdict(int)
        for cluster in clusters:
            severity_counts[cluster.severity] += 1
        
        refactorable_clusters = [c for c in clusters if c.should_refactor]
        
        return {
            'total_clusters': len(clusters),
            'refactorable_clusters': len(refactorable_clusters),
            'total_lines_saved': total_lines_saved,
            'total_hours_saved': total_hours_saved,
            'severity_distribution': dict(severity_counts),
            'top_priority_savings': sum(c.lines_saved for c in refactorable_clusters[:5]),
            'avg_confidence': sum(c.confidence for c in clusters) / len(clusters) if clusters else 0,
            'cross_category_issues': len([c for c in clusters if c.category_analysis['is_cross_category']])
        }
    
    # Métodos auxiliares básicos
    def _get_python_files(self) -> List[Path]:
        """Obtener archivos Python del proyecto."""
        python_files = list(self.project_root.rglob("*.py"))
        exclude_dirs = {'env', '__pycache__', '.git', 'refactor_backup', 'code_rag_data'}
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
        elif first_dir == 'scripts':
            return 'scripts'
        else:
            return 'other'
    
    def _analyze_file_context(self, file_path: Path) -> Dict:
        """Analizar contexto del archivo."""
        return {
            'is_test_file': 'test' in str(file_path).lower(),
            'is_main_file': file_path.name == 'main.py',
            'is_init_file': file_path.name == '__init__.py',
            'directory_depth': len(file_path.relative_to(self.project_root).parts)
        }
    
    def _normalize_code(self, code: str) -> str:
        """Normalizar código para comparación."""
        from code_utils import normalize_code_for_comparison
        return normalize_code_for_comparison(code)
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calcular complejidad."""
        from code_utils import calculate_complexity
        return calculate_complexity(node)
    
    def _is_test_function(self, name: str, filepath: str) -> bool:
        """Determinar si es función de test."""
        return name.startswith('test_') or 'test' in filepath.lower()
    
    def print_intelligent_results(self, results: Dict, verbose: bool = False):
        """Mostrar resultados inteligentes."""
        summary = results['summary']
        
        print(f"\n🧠 ANÁLISIS INTELIGENTE DE DUPLICADOS")
        print("=" * 45)
        print(f"📊 Clusters encontrados: {summary['total_clusters']}")
        print(f"🎯 Requieren refactoring: {summary['refactorable_clusters']}")
        print(f"💾 Líneas ahorradas: {summary['total_lines_saved']}")
        print(f"⏱️ Horas ahorradas: {summary['total_hours_saved']:.1f}")
        print(f"🎲 Confianza promedio: {summary['avg_confidence']:.0%}")
        print(f"🔗 Issues cross-categoría: {summary['cross_category_issues']}")
        print(f"🚫 Falsos positivos filtrados: {results['false_positives_filtered']}")
        
        # Distribución por severidad
        if summary['severity_distribution']:
            print(f"\n📈 DISTRIBUCIÓN POR SEVERIDAD:")
            for severity, count in summary['severity_distribution'].items():
                icon = {'critical': '🔴', 'high': '🟡', 'medium': '🟠', 'low': '🟢'}[severity]
                print(f"   {icon} {severity.capitalize()}: {count} clusters")
        
        # Top recomendaciones
        if results['recommendations']:
            print(f"\n💡 TOP RECOMENDACIONES PRIORIZADAS:")
            for rec in results['recommendations'][:5]:
                severity_icon = {'critical': '🔴', 'high': '🟡', 'medium': '🟠', 'low': '🟢'}[rec['severity']]
                print(f"   {rec['priority']}. {severity_icon} {rec['title']}")
                print(f"      📊 {rec['description']} | 💾 {rec['impact']} | 🎯 {rec['confidence']} confianza")
                if verbose:
                    print(f"      📂 Categorías: {', '.join(rec['categories'])}")
                    print(f"      🔧 Refactorizar: {'✅' if rec['should_refactor'] else '❌'}")
        
        # Clusters inteligentes detallados
        if verbose and results['intelligent_clusters']:
            print(f"\n🔍 CLUSTERS DETALLADOS:")
            for cluster in results['intelligent_clusters'][:3]:
                print(f"\n   🆔 {cluster.id} ({cluster.type.upper()})")
                print(f"   📊 {len(cluster.functions)} funciones, {cluster.similarity_score:.0%} similitud")
                print(f"   ⚡ Severidad: {cluster.severity} | 🎯 Confianza: {cluster.confidence:.0%}")
                print(f"   💾 Ahorro: {cluster.lines_saved} líneas ({cluster.hours_saved:.1f}h)")
                
                for func in cluster.functions[:2]:  # Mostrar primeras 2
                    print(f"      📄 {func['name']} ({func['file']}:{func['line_start']})")
                
                if len(cluster.functions) > 2:
                    print(f"      ... y {len(cluster.functions) - 2} más")
    
    def save_intelligent_results(self, results: Dict, output_file: Path):
        """Guardar resultados inteligentes."""
        # Preparar datos para serialización
        serializable_results = {
            'intelligent_clusters': [],
            'recommendations': results['recommendations'],
            'summary': results['summary'],
            'false_positives_filtered': results['false_positives_filtered'],
            'analysis_metadata': results['analysis_metadata']
        }
        
        # Convertir clusters a diccionarios
        for cluster in results['intelligent_clusters']:
            cluster_dict = {
                'id': cluster.id,
                'type': cluster.type,
                'severity': cluster.severity,
                'confidence': cluster.confidence,
                'similarity_score': cluster.similarity_score,
                'lines_saved': cluster.lines_saved,
                'hours_saved': cluster.hours_saved,
                'should_refactor': cluster.should_refactor,
                'recommendation': cluster.recommendation,
                'category_analysis': cluster.category_analysis,
                'functions': cluster.functions
            }
            serializable_results['intelligent_clusters'].append(cluster_dict)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Análisis inteligente guardado en: {output_file}")

def main():
    """Función principal del detector refinado."""
    parser = argparse.ArgumentParser(description='Detector refinado de código duplicado')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostrar información detallada')
    parser.add_argument('--output', '-o', type=str,
                       help='Archivo de salida JSON')
    parser.add_argument('--min-lines', type=int, default=5,
                       help='Mínimo líneas para considerar duplicado')
    parser.add_argument('--similarity', type=float, default=0.85,
                       help='Umbral de similitud (0.0-1.0)')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    detector = RefinedDuplicateDetector(project_root)
    
    # Configurar parámetros
    detector.min_lines = args.min_lines
    detector.similarity_threshold = args.similarity
    
    # Ejecutar detección inteligente
    results = detector.detect_intelligent_duplicates()
    
    # Mostrar resultados
    detector.print_intelligent_results(results, verbose=args.verbose)
    
    # Guardar si se especifica
    if args.output:
        output_file = Path(args.output)
        detector.save_intelligent_results(results, output_file)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())