#!/usr/bin/env python3
"""
Analizador avanzado de código con métricas ML y detección inteligente.
Incluye detección de código duplicado, análisis de calidad y patrones.
"""
import ast
import json
import hashlib
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import argparse
import numpy as np
from difflib import SequenceMatcher

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

try:
    from smart_code_analyzer import SmartCodeAnalyzer, CodeCategory
    from code_rag_system import LocalEmbeddingModel
    HAS_SMART_ANALYSIS = True
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    HAS_SMART_ANALYSIS = False

@dataclass
class DuplicateCluster:
    """Cluster de código duplicado."""
    id: str
    similarity_score: float
    clone_type: str  # exact, near-exact, semantic
    instances: List[Dict[str, Any]]
    recommendation: str
    savings_estimate: int  # líneas que se podrían ahorrar

@dataclass
class QualityMetric:
    """Métrica de calidad de código."""
    name: str
    value: float
    category: str
    severity: str  # low, medium, high, critical
    description: str
    file_path: str
    line_number: int

@dataclass
class CodePattern:
    """Patrón detectado en el código."""
    pattern_type: str
    pattern_name: str
    confidence: float
    location: str
    description: str
    is_antipattern: bool

class DuplicateDetector:
    """Detector especializado de duplicados con ML."""
    
    def __init__(self, project_root: Path, smart_analyzer=None, embedding_model=None):
        self.project_root = project_root
        self.smart_analyzer = smart_analyzer
        self.embedding_model = embedding_model
    
    def detect_duplicates(self) -> Dict[str, Any]:
        """Detectar código duplicado usando múltiples técnicas."""
        duplicates = {
            'exact_clones': [],
            'near_exact_clones': [],
            'semantic_clones': [],
            'total_savings': 0,
            'summary': {}
        }
        
        if not self.smart_analyzer:
            return duplicates
        
        # Obtener chunks de código
        chunks = []
        for file_path in self.project_root.rglob("*.py"):
            if any(excluded in file_path.parts for excluded in ['env', '__pycache__', '.git']):
                continue
            
            try:
                analysis = self.smart_analyzer._analyze_file_advanced(file_path)
                chunks.extend(analysis.get('chunks', []))
            except Exception as e:
                print(f"⚠️ Error analizando {file_path}: {e}")
        
        if not chunks:
            return duplicates
        
        # Detección de clones exactos
        duplicates['exact_clones'] = self._find_exact_clones(chunks)
        
        # Detección de clones casi exactos
        duplicates['near_exact_clones'] = self._find_near_exact_clones(chunks)
        
        # Detección semántica si hay modelo de embeddings
        if self.embedding_model:
            duplicates['semantic_clones'] = self._find_semantic_clones(chunks)
        
        # Calcular estadísticas
        total_savings = sum(cluster.savings_estimate for cluster in 
                          duplicates['exact_clones'] + duplicates['near_exact_clones'] + duplicates['semantic_clones'])
        duplicates['total_savings'] = total_savings
        
        duplicates['summary'] = {
            'exact_clusters': len(duplicates['exact_clones']),
            'near_exact_clusters': len(duplicates['near_exact_clones']),
            'semantic_clusters': len(duplicates['semantic_clones']),
            'total_savings_lines': total_savings
        }
        
        return duplicates


class QualityAnalyzer:
    """Analizador especializado de calidad de código."""
    
    def __init__(self, project_root: Path, smart_analyzer=None):
        self.project_root = project_root
        self.smart_analyzer = smart_analyzer


class PatternDetector:
    """Detector especializado de patrones de código."""
    
    def __init__(self, project_root: Path, smart_analyzer=None):
        self.project_root = project_root
        self.smart_analyzer = smart_analyzer


class AdvancedCodeAnalyzer:
    """Coordinador de análisis avanzado (refactorizado)."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.smart_analyzer = None
        self.embedding_model = None
        
        if HAS_SMART_ANALYSIS:
            self.smart_analyzer = SmartCodeAnalyzer(project_root)
            try:
                self.embedding_model = LocalEmbeddingModel(project_root / "ml-models")
            except Exception as e:
                print(f"⚠️ Error cargando modelo de embeddings: {e}")
        
        # Inicializar componentes especializados
        self.duplicate_detector = DuplicateDetector(project_root, self.smart_analyzer, self.embedding_model)
        self.quality_analyzer = QualityAnalyzer(project_root, self.smart_analyzer)
        self.pattern_detector = PatternDetector(project_root, self.smart_analyzer)
    
    def analyze_project_advanced(self) -> Dict[str, Any]:
        """Ejecutar análisis avanzado completo."""
        print("🤖 ANÁLISIS AVANZADO CON ML")
        print("=" * 50)
        
        results = {
            'duplicate_detection': {},
            'quality_metrics': {},
            'pattern_analysis': {},
            'maintainability_score': 0.0,
            'technical_debt_hours': 0.0,
            'recommendations': []
        }
        
        if not self.smart_analyzer:
            print("⚠️ Análisis básico - instalar dependencias para funcionalidad completa")
            return results
        
        # 1. Análisis de código duplicado
        print("🔍 Detectando código duplicado...")
        results['duplicate_detection'] = self.duplicate_detector.detect_duplicates()
        
        # 2. Métricas de calidad avanzadas
        print("📊 Analizando calidad de código...")
        results['quality_metrics'] = self._analyze_quality_metrics()
        
        # 3. Detección de patrones y antipatrones
        print("🎯 Detectando patrones de código...")
        results['pattern_analysis'] = self._detect_patterns()
        
        # 4. Calcular puntuaciones agregadas
        results['maintainability_score'] = self._calculate_maintainability_score(results)
        results['technical_debt_hours'] = self._estimate_technical_debt(results)
        
        # 5. Generar recomendaciones ML
        results['recommendations'] = self._generate_ml_recommendations(results)
        
        return results
    
    def _detect_duplicates(self) -> Dict[str, Any]:
        """Detectar código duplicado usando múltiples técnicas."""
        duplicates = {
            'exact_clones': [],
            'near_exact_clones': [],
            'semantic_clones': [],
            'summary': {
                'total_duplicates': 0,
                'potential_savings_lines': 0,
                'duplication_ratio': 0.0
            }
        }
        
        # Obtener chunks de código
        categorized_chunks = self.smart_analyzer.analyze_project()
        all_chunks = []
        for category_chunks in categorized_chunks.values():
            all_chunks.extend(category_chunks)
        
        # 1. Detección de clones exactos (hash-based)
        exact_clones = self._find_exact_clones(all_chunks)
        duplicates['exact_clones'] = exact_clones
        
        # 2. Detección de clones casi exactos (text similarity)
        near_exact_clones = self._find_near_exact_clones(all_chunks)
        duplicates['near_exact_clones'] = near_exact_clones
        
        # 3. Detección de clones semánticos (embedding-based)
        if self.embedding_model:
            semantic_clones = self._find_semantic_clones(all_chunks)
            duplicates['semantic_clones'] = semantic_clones
        
        # Calcular estadísticas
        total_duplicates = len(exact_clones) + len(near_exact_clones) + len(duplicates['semantic_clones'])
        total_lines = sum(chunk.line_end - chunk.line_start for chunk in all_chunks)
        duplicate_lines = sum(self._calculate_duplicate_lines(cluster) for cluster in 
                            exact_clones + near_exact_clones + duplicates['semantic_clones'])
        
        duplicates['summary'] = {
            'total_duplicates': total_duplicates,
            'potential_savings_lines': duplicate_lines,
            'duplication_ratio': duplicate_lines / total_lines if total_lines > 0 else 0.0
        }
        
        return duplicates
    
    def _find_exact_clones(self, chunks: List) -> List[DuplicateCluster]:
        """Encontrar clones exactos usando hashes."""
        hash_to_chunks = defaultdict(list)
        
        for chunk in chunks:
            # Normalizar código (remover espacios, comentarios básicos)
            normalized = self._normalize_code(chunk.content)
            if len(normalized.strip()) < 20:  # Ignorar código muy pequeño
                continue
                
            code_hash = hashlib.md5(normalized.encode()).hexdigest()
            hash_to_chunks[code_hash].append(chunk)
        
        clusters = []
        for code_hash, chunk_list in hash_to_chunks.items():
            if len(chunk_list) >= 2:  # Al menos 2 instancias
                cluster = DuplicateCluster(
                    id=f"exact_{code_hash[:8]}",
                    similarity_score=1.0,
                    clone_type="exact",
                    instances=[{
                        'file': chunk.file_path,
                        'name': chunk.name,
                        'line_start': chunk.line_start,
                        'line_end': chunk.line_end,
                        'category': chunk.category.value
                    } for chunk in chunk_list],
                    recommendation=f"Extraer a función común - {len(chunk_list)} duplicados exactos",
                    savings_estimate=(len(chunk_list) - 1) * (chunk_list[0].line_end - chunk_list[0].line_start)
                )
                clusters.append(cluster)
        
        return sorted(clusters, key=lambda x: x.savings_estimate, reverse=True)
    
    def _find_near_exact_clones(self, chunks: List, threshold: float = 0.85) -> List[DuplicateCluster]:
        """Encontrar clones casi exactos usando similitud de texto."""
        clusters = []
        processed = set()
        
        for i, chunk1 in enumerate(chunks):
            if i in processed:
                continue
                
            similar_chunks = [chunk1]
            normalized1 = self._normalize_code(chunk1.content)
            
            if len(normalized1.strip()) < 30:  # Ignorar código muy pequeño
                continue
            
            for j, chunk2 in enumerate(chunks[i+1:], i+1):
                if j in processed:
                    continue
                    
                normalized2 = self._normalize_code(chunk2.content)
                
                # Calcular similitud usando SequenceMatcher
                similarity = SequenceMatcher(None, normalized1, normalized2).ratio()
                
                if similarity >= threshold:
                    similar_chunks.append(chunk2)
                    processed.add(j)
            
            if len(similar_chunks) >= 2:
                processed.add(i)
                
                avg_similarity = sum(
                    SequenceMatcher(None, normalized1, self._normalize_code(chunk.content)).ratio()
                    for chunk in similar_chunks[1:]
                ) / (len(similar_chunks) - 1)
                
                cluster = DuplicateCluster(
                    id=f"near_{i}_{len(similar_chunks)}",
                    similarity_score=avg_similarity,
                    clone_type="near-exact",
                    instances=[{
                        'file': chunk.file_path,
                        'name': chunk.name,
                        'line_start': chunk.line_start,
                        'line_end': chunk.line_end,
                        'category': chunk.category.value
                    } for chunk in similar_chunks],
                    recommendation=f"Refactorizar similitudes - {len(similar_chunks)} instancias {avg_similarity:.1%} similares",
                    savings_estimate=(len(similar_chunks) - 1) * (similar_chunks[0].line_end - similar_chunks[0].line_start) // 2
                )
                clusters.append(cluster)
        
        return sorted(clusters, key=lambda x: x.similarity_score, reverse=True)[:10]  # Top 10
    
    def _find_semantic_clones(self, chunks: List, threshold: float = 0.75) -> List[DuplicateCluster]:
        """Encontrar clones semánticos usando embeddings."""
        if not self.embedding_model:
            return []
        
        print("🤖 Generando embeddings para detección semántica...")
        
        # Filtrar chunks relevantes (funciones principalmente)
        function_chunks = [chunk for chunk in chunks if chunk.chunk_type == "function" and 
                          len(chunk.content.strip()) > 50]
        
        if len(function_chunks) < 2:
            return []
        
        # Generar embeddings
        try:
            embeddings = []
            for chunk in function_chunks:
                # Usar nombre + docstring + estructura como texto para embedding
                text_for_embedding = f"{chunk.name}\n{chunk.docstring or ''}\n{self._extract_structure(chunk.content)}"
                embedding = self.embedding_model.encode([text_for_embedding])[0]
                embeddings.append(embedding)
            
            embeddings = np.array(embeddings)
            
            # Calcular similitudes coseno
            similarities = np.dot(embeddings, embeddings.T) / (
                np.linalg.norm(embeddings, axis=1)[:, None] * np.linalg.norm(embeddings, axis=1)
            )
            
            # Encontrar clusters semánticos
            clusters = []
            processed = set()
            
            for i in range(len(function_chunks)):
                if i in processed:
                    continue
                
                similar_indices = np.where(similarities[i] >= threshold)[0]
                similar_indices = [idx for idx in similar_indices if idx != i and idx not in processed]
                
                if len(similar_indices) >= 1:  # Al menos 1 similar + el original
                    cluster_chunks = [function_chunks[i]] + [function_chunks[idx] for idx in similar_indices]
                    avg_similarity = similarities[i][similar_indices].mean()
                    
                    processed.add(i)
                    processed.update(similar_indices)
                    
                    cluster = DuplicateCluster(
                        id=f"semantic_{i}_{len(cluster_chunks)}",
                        similarity_score=float(avg_similarity),
                        clone_type="semantic",
                        instances=[{
                            'file': chunk.file_path,
                            'name': chunk.name,
                            'line_start': chunk.line_start,
                            'line_end': chunk.line_end,
                            'category': chunk.category.value
                        } for chunk in cluster_chunks],
                        recommendation=f"Considerar abstracción común - {len(cluster_chunks)} funciones semánticamente similares",
                        savings_estimate=sum(chunk.line_end - chunk.line_start for chunk in cluster_chunks[1:]) // 3
                    )
                    clusters.append(cluster)
            
            return sorted(clusters, key=lambda x: x.similarity_score, reverse=True)[:5]  # Top 5
            
        except Exception as e:
            print(f"⚠️ Error en detección semántica: {e}")
            return []
    
    def _analyze_quality_metrics(self) -> Dict[str, Any]:
        """Analizar métricas de calidad avanzadas."""
        metrics = {
            'code_smells': [],
            'maintainability_issues': [],
            'performance_warnings': [],
            'security_concerns': [],
            'summary': {
                'total_issues': 0,
                'critical_issues': 0,
                'quality_score': 0.0
            }
        }
        
        # Obtener archivos Python para análisis
        python_files = list(self.project_root.rglob("*.py"))
        exclude_dirs = {'env', '__pycache__', '.git', 'refactor_backup'}
        python_files = [f for f in python_files if not any(excluded in f.parts for excluded in exclude_dirs)]
        
        for file_path in python_files:
            file_metrics = self._analyze_file_quality(file_path)
            
            metrics['code_smells'].extend(file_metrics['code_smells'])
            metrics['maintainability_issues'].extend(file_metrics['maintainability_issues'])
            metrics['performance_warnings'].extend(file_metrics['performance_warnings'])
            metrics['security_concerns'].extend(file_metrics['security_concerns'])
        
        # Calcular estadísticas
        all_issues = (metrics['code_smells'] + metrics['maintainability_issues'] + 
                     metrics['performance_warnings'] + metrics['security_concerns'])
        
        metrics['summary'] = {
            'total_issues': len(all_issues),
            'critical_issues': len([issue for issue in all_issues if issue.severity == 'critical']),
            'quality_score': max(0.0, 10.0 - len(all_issues) * 0.1)  # Score de 0-10
        }
        
        return metrics
    
    def _analyze_file_quality(self, file_path: Path) -> Dict[str, List[QualityMetric]]:
        """Analizar calidad de un archivo específico."""
        metrics = {
            'code_smells': [],
            'maintainability_issues': [],
            'performance_warnings': [],
            'security_concerns': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            tree = ast.parse(content)
            
            # Detectar code smells
            metrics['code_smells'].extend(self._detect_code_smells(tree, file_path, lines))
            
            # Detectar problemas de mantenibilidad
            metrics['maintainability_issues'].extend(self._detect_maintainability_issues(tree, file_path, lines))
            
            # Detectar warnings de performance
            metrics['performance_warnings'].extend(self._detect_performance_issues(tree, file_path, lines))
            
            # Detectar concerns de seguridad
            metrics['security_concerns'].extend(self._detect_security_issues(tree, file_path, lines))
            
        except Exception as e:
            print(f"⚠️ Error analizando {file_path}: {e}")
        
        return metrics
    
    def _detect_code_smells(self, tree: ast.AST, file_path: Path, lines: List[str]) -> List[QualityMetric]:
        """Detectar code smells comunes."""
        smells = []
        
        for node in ast.walk(tree):
            # Long method
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    method_length = node.end_lineno - node.lineno
                    if method_length > 50:
                        smells.append(QualityMetric(
                            name="Long Method",
                            value=method_length,
                            category="code_smell",
                            severity="medium" if method_length < 100 else "high",
                            description=f"Método {node.name} tiene {method_length} líneas (recomendado: <50)",
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=node.lineno
                        ))
            
            # Large class
            elif isinstance(node, ast.ClassDef):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    class_length = node.end_lineno - node.lineno
                    if class_length > 200:
                        smells.append(QualityMetric(
                            name="Large Class",
                            value=class_length,
                            category="code_smell",
                            severity="medium" if class_length < 400 else "high",
                            description=f"Clase {node.name} tiene {class_length} líneas (recomendado: <200)",
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=node.lineno
                        ))
        
        return smells
    
    def _detect_maintainability_issues(self, tree: ast.AST, file_path: Path, lines: List[str]) -> List[QualityMetric]:
        """Detectar problemas de mantenibilidad."""
        issues = []
        
        # Funciones sin docstring
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not ast.get_docstring(node) and not node.name.startswith('_'):
                    issues.append(QualityMetric(
                        name="Missing Docstring",
                        value=1.0,
                        category="maintainability",
                        severity="low",
                        description=f"Función pública {node.name} sin documentación",
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=node.lineno
                    ))
        
        return issues
    
    def _detect_performance_issues(self, tree: ast.AST, file_path: Path, lines: List[str]) -> List[QualityMetric]:
        """Detectar potenciales problemas de performance."""
        warnings = []
        
        for node in ast.walk(tree):
            # Loops anidados
            if isinstance(node, (ast.For, ast.While)):
                nested_loops = [n for n in ast.walk(node) if isinstance(n, (ast.For, ast.While)) and n != node]
                if len(nested_loops) >= 2:
                    warnings.append(QualityMetric(
                        name="Nested Loops",
                        value=len(nested_loops) + 1,
                        category="performance",
                        severity="medium",
                        description=f"Loops anidados detectados (nivel {len(nested_loops) + 1})",
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=node.lineno
                    ))
        
        return warnings
    
    def _detect_security_issues(self, tree: ast.AST, file_path: Path, lines: List[str]) -> List[QualityMetric]:
        """Detectar potenciales problemas de seguridad."""
        concerns = []
        
        for node in ast.walk(tree):
            # Uso de eval()
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'eval':
                concerns.append(QualityMetric(
                    name="Dangerous eval() usage",
                    value=1.0,
                    category="security",
                    severity="critical",
                    description="Uso de eval() puede ser peligroso",
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=node.lineno
                ))
        
        return concerns
    
    def _detect_patterns(self) -> Dict[str, Any]:
        """Detectar patrones de diseño y antipatrones."""
        patterns = {
            'design_patterns': [],
            'antipatterns': [],
            'architectural_insights': []
        }
        
        # Implementación básica - se puede expandir con ML
        patterns['architectural_insights'].append({
            'pattern': 'Layered Architecture',
            'confidence': 0.7,
            'description': 'Estructura en capas detectada: src/api, src/scraper, src/rag',
            'recommendation': 'Mantener separación clara entre capas'
        })
        
        return patterns
    
    def _calculate_maintainability_score(self, results: Dict) -> float:
        """Calcular índice de mantenibilidad."""
        quality_score = results['quality_metrics']['summary']['quality_score']
        duplication_penalty = results['duplicate_detection']['summary']['duplication_ratio'] * 2
        
        return max(0.0, min(10.0, quality_score - duplication_penalty))
    
    def _estimate_technical_debt(self, results: Dict) -> float:
        """Estimar deuda técnica en horas."""
        # Estimaciones basadas en industry standards
        debt_hours = 0.0
        
        # Código duplicado
        duplicate_lines = results['duplicate_detection']['summary']['potential_savings_lines']
        debt_hours += duplicate_lines * 0.1  # 6 minutos por línea duplicada
        
        # Issues de calidad
        critical_issues = results['quality_metrics']['summary']['critical_issues']
        total_issues = results['quality_metrics']['summary']['total_issues']
        
        debt_hours += critical_issues * 2.0  # 2 horas por issue crítico
        debt_hours += (total_issues - critical_issues) * 0.5  # 30 min por issue normal
        
        return debt_hours
    
    def _generate_ml_recommendations(self, results: Dict) -> List[Dict]:
        """Generar recomendaciones inteligentes."""
        recommendations = []
        
        # Recomendaciones de duplicación
        if results['duplicate_detection']['summary']['duplication_ratio'] > 0.1:
            recommendations.append({
                'type': 'duplication',
                'priority': 'HIGH',
                'title': 'Reducir código duplicado',
                'description': f"Duplicación del {results['duplicate_detection']['summary']['duplication_ratio']:.1%} detectada",
                'action': 'Revisar clusters de duplicación y extraer funciones comunes',
                'estimated_savings': f"{results['duplicate_detection']['summary']['potential_savings_lines']} líneas"
            })
        
        # Recomendaciones de calidad
        if results['quality_metrics']['summary']['critical_issues'] > 0:
            recommendations.append({
                'type': 'quality',
                'priority': 'CRITICAL',
                'title': 'Resolver issues críticos',
                'description': f"{results['quality_metrics']['summary']['critical_issues']} problemas críticos encontrados",
                'action': 'Priorizar corrección de issues de seguridad y performance',
                'estimated_time': f"{results['quality_metrics']['summary']['critical_issues'] * 2} horas"
            })
        
        return recommendations
    
    def _normalize_code(self, code: str) -> str:
        """Normalizar código para comparación."""
        # Remover comentarios y espacios extra
        lines = []
        for line in code.split('\n'):
            # Remover comentarios
            if '#' in line:
                line = line[:line.index('#')]
            # Normalizar espacios
            line = ' '.join(line.split())
            if line.strip():
                lines.append(line)
        return '\n'.join(lines)
    
    def _extract_structure(self, code: str) -> str:
        """Extraer estructura del código para análisis semántico."""
        try:
            tree = ast.parse(code)
            structure_parts = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        structure_parts.append(f"call:{node.func.id}")
                elif isinstance(node, ast.If):
                    structure_parts.append("if")
                elif isinstance(node, ast.For):
                    structure_parts.append("for")
                elif isinstance(node, ast.While):
                    structure_parts.append("while")
            
            return ' '.join(structure_parts)
        except:
            return ""
    
    def _calculate_duplicate_lines(self, cluster: DuplicateCluster) -> int:
        """Calcular líneas duplicadas en un cluster."""
        if not cluster.instances:
            return 0
        
        # Asumir que todas las instancias tienen el mismo tamaño aproximado
        avg_lines = sum(inst.get('line_end', 0) - inst.get('line_start', 0) 
                       for inst in cluster.instances) / len(cluster.instances)
        
        return int(avg_lines * (len(cluster.instances) - 1))  # Excluir la instancia original
    
    def print_advanced_results(self, results: Dict, verbose: bool = False):
        """Mostrar resultados del análisis avanzado."""
        print(f"\n🤖 RESULTADOS DEL ANÁLISIS AVANZADO")
        print("=" * 50)
        
        # Métricas principales
        print(f"📊 Puntuación de mantenibilidad: {results['maintainability_score']:.1f}/10")
        print(f"⏱️ Deuda técnica estimada: {results['technical_debt_hours']:.1f} horas")
        
        # Código duplicado
        dup_summary = results['duplicate_detection']['summary']
        print(f"\n🔄 CÓDIGO DUPLICADO:")
        print(f"   📈 Ratio duplicación: {dup_summary['duplication_ratio']:.1%}")
        print(f"   💾 Líneas potencialmente ahorradas: {dup_summary['potential_savings_lines']}")
        print(f"   🔢 Total clusters: {dup_summary['total_duplicates']}")
        
        if verbose:
            # Mostrar top clusters
            all_clusters = (results['duplicate_detection']['exact_clones'] + 
                          results['duplicate_detection']['near_exact_clones'] + 
                          results['duplicate_detection']['semantic_clones'])
            
            if all_clusters:
                print(f"\n   🔥 Top clusters de duplicación:")
                for i, cluster in enumerate(all_clusters[:5], 1):
                    print(f"      {i}. {cluster.clone_type} - {cluster.similarity_score:.1%} similar")
                    print(f"         💾 Ahorro: {cluster.savings_estimate} líneas")
                    print(f"         📍 {len(cluster.instances)} instancias")
        
        # Calidad
        quality_summary = results['quality_metrics']['summary']
        print(f"\n🎯 CALIDAD DE CÓDIGO:")
        print(f"   📊 Score calidad: {quality_summary['quality_score']:.1f}/10")
        print(f"   ⚠️ Issues totales: {quality_summary['total_issues']}")
        print(f"   🔴 Issues críticos: {quality_summary['critical_issues']}")
        
        # Recomendaciones
        if results['recommendations']:
            print(f"\n💡 RECOMENDACIONES PRIORITARIAS:")
            for i, rec in enumerate(results['recommendations'][:5], 1):
                priority_icon = "🔴" if rec['priority'] == 'CRITICAL' else "🟡" if rec['priority'] == 'HIGH' else "🟢"
                print(f"   {priority_icon} {rec['title']}")
                if verbose:
                    print(f"      {rec['description']}")
                    print(f"      Acción: {rec['action']}")
    
    def save_advanced_results(self, results: Dict, output_file: Path):
        """Guardar resultados avanzados."""
        # Convertir dataclasses a dict para serialización
        serializable_results = {}
        
        for key, value in results.items():
            if key == 'duplicate_detection':
                serializable_results[key] = {}
                for dup_type, clusters in value.items():
                    if isinstance(clusters, list) and clusters and hasattr(clusters[0], '__dict__'):
                        serializable_results[key][dup_type] = [asdict(cluster) for cluster in clusters]
                    else:
                        serializable_results[key][dup_type] = clusters
            else:
                serializable_results[key] = value
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Análisis avanzado guardado en: {output_file}")

def main():
    """Función principal del analizador avanzado."""
    parser = argparse.ArgumentParser(description='Análisis avanzado de código con ML')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostrar información detallada')
    parser.add_argument('--output', '-o', type=str, default='tools/advanced_analysis.json',
                       help='Archivo de salida para resultados')
    parser.add_argument('--duplicates-only', action='store_true',
                       help='Solo análisis de duplicación')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    analyzer = AdvancedCodeAnalyzer(project_root)
    
    # Ejecutar análisis
    results = analyzer.analyze_project_advanced()
    
    # Mostrar resultados
    analyzer.print_advanced_results(results, verbose=args.verbose)
    
    # Guardar si se especifica
    output_file = Path(args.output)
    analyzer.save_advanced_results(results, output_file)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())