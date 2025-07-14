#!/usr/bin/env python3
"""
Herramienta de insights automáticos sobre el código usando RAG.
Genera análisis y sugerencias de mejora basados en patrones detectados.
"""
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime

try:
    from code_rag_system import CodeRAGSystem, CodeChunk
    HAS_RAG = True
except ImportError:
    HAS_RAG = False

class CodeInsights:
    """Generador de insights automáticos sobre el código."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.rag_system = None
        
    def initialize(self):
        """Inicializar sistema RAG."""
        if not HAS_RAG:
            print("❌ Sistema RAG no disponible.")
            return False
        
        self.rag_system = CodeRAGSystem(self.project_root)
        self.rag_system.index_codebase()
        return True
    
    def generate_insights(self) -> Dict[str, Any]:
        """Generar insights completos sobre el código."""
        if not self.rag_system:
            raise ValueError("Sistema no inicializado")
        
        chunks = self.rag_system.chunks
        
        insights = {
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(chunks),
            'complexity_analysis': self._analyze_complexity(chunks),
            'dependency_analysis': self._analyze_dependencies(chunks),
            'pattern_analysis': self._analyze_patterns(chunks),
            'quality_metrics': self._calculate_quality_metrics(chunks),
            'recommendations': self._generate_recommendations(chunks),
            'hotspots': self._identify_hotspots(chunks),
            'architecture_insights': self._analyze_architecture(chunks)
        }
        
        return insights
    
    def _generate_summary(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Generar resumen general del código."""
        # Contar por tipo
        type_counts = Counter(chunk.chunk_type for chunk in chunks)
        
        # Contar por archivo
        file_counts = Counter(chunk.file_path for chunk in chunks)
        
        # Complejidad total
        total_complexity = sum(chunk.complexity for chunk in chunks)
        
        # Archivos con más chunks
        top_files = file_counts.most_common(5)
        
        return {
            'total_chunks': len(chunks),
            'total_files': len(file_counts),
            'type_distribution': dict(type_counts),
            'total_complexity': total_complexity,
            'avg_complexity': total_complexity / len(chunks) if chunks else 0,
            'top_files': [{'file': Path(f).name, 'chunks': c} for f, c in top_files]
        }
    
    def _analyze_complexity(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Analizar complejidad del código."""
        function_chunks = [c for c in chunks if c.chunk_type == 'function']
        
        if not function_chunks:
            return {'error': 'No functions found'}
        
        complexities = [c.complexity for c in function_chunks]
        
        # Estadísticas
        complexities.sort()
        n = len(complexities)
        
        # Funciones más complejas
        complex_functions = sorted(function_chunks, key=lambda x: x.complexity, reverse=True)[:10]
        
        # Distribución por rangos
        ranges = {
            'simple': len([c for c in complexities if c <= 3]),
            'moderate': len([c for c in complexities if 4 <= c <= 7]),
            'complex': len([c for c in complexities if 8 <= c <= 15]),
            'very_complex': len([c for c in complexities if c > 15])
        }
        
        return {
            'total_functions': len(function_chunks),
            'min_complexity': min(complexities),
            'max_complexity': max(complexities),
            'avg_complexity': sum(complexities) / n,
            'median_complexity': complexities[n // 2],
            'complexity_ranges': ranges,
            'most_complex_functions': [
                {
                    'name': f.name,
                    'file': Path(f.file_path).name,
                    'complexity': f.complexity,
                    'lines': f.line_end - f.line_start
                }
                for f in complex_functions
            ]
        }
    
    def _analyze_dependencies(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Analizar dependencias entre componentes."""
        # Mapear dependencias
        dependency_graph = defaultdict(set)
        all_dependencies = []
        
        for chunk in chunks:
            for dep in chunk.dependencies:
                dependency_graph[chunk.name].add(dep)
                all_dependencies.append(dep)
        
        # Contar dependencias más usadas
        dep_counts = Counter(all_dependencies)
        
        # Encontrar componentes con muchas dependencias
        high_dependency_components = [
            (name, len(deps)) for name, deps in dependency_graph.items()
            if len(deps) > 5
        ]
        high_dependency_components.sort(key=lambda x: x[1], reverse=True)
        
        # Encontrar dependencias circulares simples
        circular_deps = []
        for name, deps in dependency_graph.items():
            for dep in deps:
                if name in dependency_graph.get(dep, set()):
                    circular_deps.append((name, dep))
        
        return {
            'total_unique_dependencies': len(dep_counts),
            'most_used_dependencies': dep_counts.most_common(10),
            'high_dependency_components': high_dependency_components[:10],
            'potential_circular_dependencies': circular_deps,
            'avg_dependencies_per_component': len(all_dependencies) / len(chunks) if chunks else 0
        }
    
    def _analyze_patterns(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Analizar patrones en el código."""
        patterns = {
            'naming_patterns': self._analyze_naming_patterns(chunks),
            'code_patterns': self._analyze_code_patterns(chunks),
            'architectural_patterns': self._analyze_architectural_patterns(chunks)
        }
        
        return patterns
    
    def _analyze_naming_patterns(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Analizar patrones de nombres."""
        function_names = [c.name for c in chunks if c.chunk_type == 'function']
        class_names = [c.name for c in chunks if c.chunk_type == 'class']
        
        # Convenciones de nombres
        snake_case_functions = len([n for n in function_names if '_' in n and n.islower()])
        camel_case_classes = len([n for n in class_names if n[0].isupper()])
        
        # Prefijos comunes
        function_prefixes = Counter([n.split('_')[0] for n in function_names if '_' in n])
        
        # Nombres largos
        long_names = [n for n in function_names + class_names if len(n) > 25]
        
        return {
            'total_functions': len(function_names),
            'total_classes': len(class_names),
            'snake_case_functions': snake_case_functions,
            'camel_case_classes': camel_case_classes,
            'common_prefixes': dict(function_prefixes.most_common(5)),
            'long_names': long_names[:10],
            'naming_consistency_score': (snake_case_functions + camel_case_classes) / 
                                       (len(function_names) + len(class_names)) if function_names or class_names else 0
        }
    
    def _analyze_code_patterns(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Analizar patrones en el código."""
        # Buscar patrones comunes en el contenido
        pattern_counts = {
            'try_except_blocks': 0,
            'async_functions': 0,
            'decorators': 0,
            'list_comprehensions': 0,
            'type_hints': 0,
            'docstrings': 0
        }
        
        for chunk in chunks:
            content = chunk.content.lower()
            
            if 'try:' in content and 'except' in content:
                pattern_counts['try_except_blocks'] += 1
            
            if 'async def' in content:
                pattern_counts['async_functions'] += 1
            
            if '@' in content and 'def' in content:
                pattern_counts['decorators'] += 1
            
            if '[' in content and 'for' in content and 'in' in content and ']' in content:
                pattern_counts['list_comprehensions'] += 1
            
            if '->' in content or ':' in content:
                pattern_counts['type_hints'] += 1
            
            if chunk.docstring:
                pattern_counts['docstrings'] += 1
        
        return pattern_counts
    
    def _analyze_architectural_patterns(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Analizar patrones arquitectónicos."""
        # Agrupar por directorios
        directory_structure = defaultdict(list)
        
        for chunk in chunks:
            path_parts = Path(chunk.file_path).parts
            if len(path_parts) > 1:
                directory = path_parts[-2]  # Directorio padre
                directory_structure[directory].append(chunk)
        
        # Analizar estructura por directorio
        dir_analysis = {}
        for directory, dir_chunks in directory_structure.items():
            type_dist = Counter(c.chunk_type for c in dir_chunks)
            avg_complexity = sum(c.complexity for c in dir_chunks) / len(dir_chunks)
            
            dir_analysis[directory] = {
                'chunk_count': len(dir_chunks),
                'type_distribution': dict(type_dist),
                'avg_complexity': avg_complexity
            }
        
        return {
            'directory_structure': dir_analysis,
            'separation_of_concerns_score': self._calculate_soc_score(directory_structure)
        }
    
    def _calculate_soc_score(self, directory_structure: Dict) -> float:
        """Calcular score de separación de responsabilidades."""
        if not directory_structure:
            return 0.0
        
        # Penalizar directorios con muchos tipos diferentes
        total_score = 0
        for directory, chunks in directory_structure.items():
            type_diversity = len(set(c.chunk_type for c in chunks))
            # Score más alto = mejor separación (menos tipos por directorio)
            dir_score = max(0, 1 - (type_diversity - 1) * 0.2)
            total_score += dir_score
        
        return total_score / len(directory_structure)
    
    def _calculate_quality_metrics(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Calcular métricas de calidad del código."""
        function_chunks = [c for c in chunks if c.chunk_type == 'function']
        
        if not function_chunks:
            return {'error': 'No functions found'}
        
        # Métricas básicas
        documented_functions = len([c for c in function_chunks if c.docstring])
        short_functions = len([c for c in function_chunks if c.line_end - c.line_start <= 20])
        simple_functions = len([c for c in function_chunks if c.complexity <= 5])
        
        # Scores de calidad
        documentation_score = documented_functions / len(function_chunks)
        simplicity_score = simple_functions / len(function_chunks)
        conciseness_score = short_functions / len(function_chunks)
        
        # Score general
        overall_quality = (documentation_score + simplicity_score + conciseness_score) / 3
        
        return {
            'total_functions': len(function_chunks),
            'documented_functions': documented_functions,
            'documentation_score': documentation_score,
            'simplicity_score': simplicity_score,
            'conciseness_score': conciseness_score,
            'overall_quality_score': overall_quality,
            'quality_grade': self._get_quality_grade(overall_quality)
        }
    
    def _get_quality_grade(self, score: float) -> str:
        """Convertir score a letra."""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def _generate_recommendations(self, chunks: List[CodeChunk]) -> List[Dict[str, Any]]:
        """Generar recomendaciones de mejora."""
        recommendations = []
        
        # Funciones muy complejas
        complex_functions = [c for c in chunks if c.chunk_type == 'function' and c.complexity > 10]
        if complex_functions:
            recommendations.append({
                'type': 'complexity',
                'priority': 'high',
                'title': 'Reducir complejidad de funciones',
                'description': f'{len(complex_functions)} funciones tienen complejidad > 10',
                'affected_items': [f"{c.name} ({c.complexity})" for c in complex_functions[:5]]
            })
        
        # Funciones sin documentación
        undocumented = [c for c in chunks if c.chunk_type == 'function' and not c.docstring]
        if len(undocumented) > 5:
            recommendations.append({
                'type': 'documentation',
                'priority': 'medium',
                'title': 'Agregar documentación',
                'description': f'{len(undocumented)} funciones sin docstring',
                'affected_items': [c.name for c in undocumented[:5]]
            })
        
        # Archivos con muchos chunks
        file_counts = Counter(c.file_path for c in chunks)
        large_files = [(f, c) for f, c in file_counts.items() if c > 20]
        if large_files:
            recommendations.append({
                'type': 'structure',
                'priority': 'medium',
                'title': 'Considerar dividir archivos grandes',
                'description': f'{len(large_files)} archivos con >20 componentes',
                'affected_items': [f"{Path(f).name} ({c} componentes)" for f, c in large_files[:3]]
            })
        
        return recommendations
    
    def _identify_hotspots(self, chunks: List[CodeChunk]) -> List[Dict[str, Any]]:
        """Identificar hotspots problemáticos."""
        hotspots = []
        
        # Hotspot por complejidad
        complex_chunks = sorted(
            [c for c in chunks if c.chunk_type == 'function'], 
            key=lambda x: x.complexity, reverse=True
        )[:5]
        
        for chunk in complex_chunks:
            hotspots.append({
                'type': 'complexity_hotspot',
                'name': chunk.name,
                'file': chunk.file_path,
                'score': chunk.complexity,
                'description': f'Función muy compleja (complejidad: {chunk.complexity})'
            })
        
        # Hotspot por dependencias
        dependency_counts = defaultdict(int)
        for chunk in chunks:
            for dep in chunk.dependencies:
                dependency_counts[dep] += 1
        
        for dep, count in sorted(dependency_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            if count > 5:
                hotspots.append({
                    'type': 'dependency_hotspot',
                    'name': dep,
                    'file': 'multiple',
                    'score': count,
                    'description': f'Dependencia muy usada ({count} referencias)'
                })
        
        return hotspots
    
    def _analyze_architecture(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Analizar arquitectura del proyecto."""
        # Agrupar por directorios principales
        main_dirs = defaultdict(list)
        
        for chunk in chunks:
            path_parts = Path(chunk.file_path).parts
            if len(path_parts) > 0:
                main_dir = path_parts[0]  # Directorio raíz
                main_dirs[main_dir].append(chunk)
        
        # Analizar cada directorio principal
        architecture = {}
        for directory, dir_chunks in main_dirs.items():
            if len(dir_chunks) < 5:  # Ignorar directorios pequeños
                continue
                
            type_dist = Counter(c.chunk_type for c in dir_chunks)
            avg_complexity = sum(c.complexity for c in dir_chunks) / len(dir_chunks)
            
            # Detectar patrones arquitectónicos
            patterns = []
            if directory == 'src':
                patterns.append('main_source')
            elif directory == 'tests':
                patterns.append('test_suite')
            elif directory == 'tools':
                patterns.append('utilities')
            elif directory == 'scripts':
                patterns.append('automation')
            
            architecture[directory] = {
                'chunk_count': len(dir_chunks),
                'file_count': len(set(c.file_path for c in dir_chunks)),
                'type_distribution': dict(type_dist),
                'avg_complexity': avg_complexity,
                'patterns': patterns
            }
        
        return {
            'main_directories': architecture,
            'architectural_style': self._detect_architectural_style(architecture)
        }
    
    def _detect_architectural_style(self, architecture: Dict) -> str:
        """Detectar estilo arquitectónico."""
        dirs = set(architecture.keys())
        
        if 'src' in dirs and 'tests' in dirs:
            if 'tools' in dirs and 'scripts' in dirs:
                return 'modular_with_tooling'
            else:
                return 'standard_src_test'
        elif len(dirs) == 1:
            return 'monolithic'
        else:
            return 'custom_structure'
    
    def save_insights(self, insights: Dict[str, Any], output_file: Optional[Path] = None):
        """Guardar insights en archivo JSON."""
        if output_file is None:
            output_file = self.project_root / "tools" / "code_insights.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Insights guardados en: {output_file}")
    
    def print_summary(self, insights: Dict[str, Any]):
        """Imprimir resumen de insights."""
        print("🔍 INSIGHTS DE CÓDIGO")
        print("=" * 50)
        
        summary = insights['summary']
        print(f"📊 Resumen General:")
        print(f"   📁 Archivos: {summary['total_files']}")
        print(f"   🧩 Componentes: {summary['total_chunks']}")
        print(f"   📈 Complejidad promedio: {summary['avg_complexity']:.1f}")
        
        quality = insights['quality_metrics']
        if 'overall_quality_score' in quality:
            print(f"   💯 Calidad general: {quality['quality_grade']} ({quality['overall_quality_score']:.2f})")
        
        recommendations = insights['recommendations']
        if recommendations:
            print(f"\n💡 Recomendaciones principales:")
            for rec in recommendations[:3]:
                priority_icon = "🔴" if rec['priority'] == 'high' else "🟡"
                print(f"   {priority_icon} {rec['title']}")
        
        hotspots = insights['hotspots']
        if hotspots:
            print(f"\n🔥 Hotspots detectados:")
            for hotspot in hotspots[:3]:
                print(f"   🎯 {hotspot['name']}: {hotspot['description']}")

def main():
    """Función principal."""
    if not HAS_RAG:
        print("❌ Dependencias faltantes:")
        print("   pip install sentence-transformers numpy faiss-cpu")
        return 1
    
    project_root = Path(__file__).parent.parent
    insights_generator = CodeInsights(project_root)
    
    print("🧠 GENERADOR DE INSIGHTS DE CÓDIGO")
    print("=" * 50)
    
    if not insights_generator.initialize():
        return 1
    
    # Generar insights
    print("🔄 Generando insights...")
    insights = insights_generator.generate_insights()
    
    # Mostrar resumen
    insights_generator.print_summary(insights)
    
    # Guardar insights
    insights_generator.save_insights(insights)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())