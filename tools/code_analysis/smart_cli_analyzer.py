#!/usr/bin/env python3
"""
Analizador CLI inteligente con categorización por importancia.
Mejora el análisis de código diferenciando entre producción, tests y herramientas.
"""
import ast
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import argparse
from dataclasses import dataclass

try:
    from smart_code_analyzer import SmartCodeAnalyzer, CodeCategory
    HAS_SMART_ANALYSIS = True
except ImportError:
    HAS_SMART_ANALYSIS = False

@dataclass
class OrphanFunction:
    """Función huérfana con metadata inteligente."""
    name: str
    file_path: str
    category: str
    confidence: float
    business_value: int
    priority: int
    complexity: int
    line_number: int

class SmartCLIAnalyzer:
    """Analizador CLI con categorización inteligente."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.smart_analyzer = None
        
        if HAS_SMART_ANALYSIS:
            self.smart_analyzer = SmartCodeAnalyzer(project_root)
    
    def analyze_project(self, category_filter: str = None) -> Dict:
        """Analizar proyecto con filtros de categoría."""
        print("🧠 ANÁLISIS INTELIGENTE DE CÓDIGO POR CLI")
        print("=" * 50)
        
        if not self.smart_analyzer:
            return self._fallback_analysis()
        
        # Analizar con categorización
        categorized_chunks = self.smart_analyzer.analyze_project()
        
        # Filtrar por categoría si se especifica
        if category_filter:
            categorized_chunks = {
                k: v for k, v in categorized_chunks.items() 
                if k == category_filter
            }
        
        return self._process_results(categorized_chunks)
    
    def _process_results(self, categorized_chunks: Dict) -> Dict:
        """Procesar resultados del análisis inteligente."""
        results = {
            'orphan_functions': [],
            'category_summary': {},
            'recommendations': [],
            'production_focus': []
        }
        
        total_chunks = 0
        total_orphans = 0
        
        for category, chunks in categorized_chunks.items():
            category_orphans = []
            
            for chunk in chunks:
                total_chunks += 1
                
                if chunk.is_orphan:
                    total_orphans += 1
                    orphan = OrphanFunction(
                        name=chunk.name,
                        file_path=chunk.file_path,
                        category=category,
                        confidence=chunk.orphan_confidence,
                        business_value=chunk.business_value,
                        priority=chunk.priority,
                        complexity=chunk.complexity,
                        line_number=chunk.line_start
                    )
                    category_orphans.append(orphan)
                    results['orphan_functions'].append(orphan)
            
            results['category_summary'][category] = {
                'total_chunks': len(chunks),
                'orphan_count': len(category_orphans),
                'orphan_rate': len(category_orphans) / len(chunks) * 100 if chunks else 0
            }
        
        # Separar funciones de producción para análisis prioritario
        production_orphans = [
            f for f in results['orphan_functions'] 
            if f.category == 'production'
        ]
        
        # Ordenar por importancia (prioridad + valor de negocio)
        production_orphans.sort(
            key=lambda x: (x.confidence, x.business_value, x.priority), 
            reverse=True
        )
        
        results['production_focus'] = production_orphans
        results['total_stats'] = {
            'total_chunks': total_chunks,
            'total_orphans': total_orphans,
            'orphan_rate': total_orphans / total_chunks * 100 if total_chunks else 0
        }
        
        # Generar recomendaciones inteligentes
        results['recommendations'] = self._generate_smart_recommendations(results)
        
        return results
    
    def _generate_smart_recommendations(self, results: Dict) -> List[Dict]:
        """Generar recomendaciones basadas en análisis inteligente."""
        recommendations = []
        
        production_orphans = results['production_focus']
        
        if production_orphans:
            high_confidence = [f for f in production_orphans if f.confidence > 0.8]
            
            if high_confidence:
                recommendations.append({
                    'type': 'high_priority_cleanup',
                    'priority': 'HIGH',
                    'title': f'Limpiar {len(high_confidence)} funciones huérfanas en producción',
                    'description': 'Funciones con alta confianza de ser huérfanas en código de producción',
                    'action': 'Revisar y eliminar si no son necesarias',
                    'functions': [f.name for f in high_confidence[:5]]
                })
            
            complex_orphans = [f for f in production_orphans if f.complexity > 10]
            if complex_orphans:
                recommendations.append({
                    'type': 'complex_orphan_review',
                    'priority': 'MEDIUM',
                    'title': f'Revisar {len(complex_orphans)} funciones complejas huérfanas',
                    'description': 'Funciones con alta complejidad que parecen no usarse',
                    'action': 'Analizar si deberían refactorizarse o eliminarse',
                    'functions': [f.name for f in complex_orphans[:3]]
                })
        
        # Análisis por categoría
        category_summary = results['category_summary']
        
        for category, stats in category_summary.items():
            if stats['orphan_rate'] > 50 and category != 'test':
                recommendations.append({
                    'type': 'category_cleanup',
                    'priority': 'MEDIUM',
                    'title': f'Alto porcentaje de huérfanos en {category}',
                    'description': f'{stats["orphan_rate"]:.1f}% de funciones huérfanas',
                    'action': f'Revisar estructura y organización de {category}',
                    'category': category
                })
        
        return recommendations
    
    def _fallback_analysis(self) -> Dict:
        """Análisis básico sin categorización inteligente."""
        print("⚠️ Análisis básico (sin categorización inteligente)")
        
        # Implementar análisis básico similar al detect_orphan_code.py original
        return {
            'orphan_functions': [],
            'category_summary': {},
            'recommendations': [{
                'type': 'upgrade_needed',
                'priority': 'HIGH',
                'title': 'Instalar dependencias para análisis inteligente',
                'description': 'Para análisis completo, instalar smart_code_analyzer',
                'action': 'pip install sentence-transformers faiss-cpu'
            }],
            'production_focus': []
        }
    
    def print_results(self, results: Dict, verbose: bool = False, category_filter: str = None):
        """Imprimir resultados del análisis."""
        print(f"\n📊 RESULTADOS DEL ANÁLISIS")
        print("=" * 50)
        
        # Estadísticas generales
        stats = results['total_stats']
        print(f"📁 Total componentes: {stats['total_chunks']}")
        print(f"❌ Total huérfanos: {stats['total_orphans']} ({stats['orphan_rate']:.1f}%)")
        
        # Resumen por categoría
        print(f"\n📂 RESUMEN POR CATEGORÍA:")
        for category, data in results['category_summary'].items():
            icon = self._get_category_icon(category)
            print(f"   {icon} {category.capitalize()}: {data['orphan_count']}/{data['total_chunks']} huérfanos ({data['orphan_rate']:.1f}%)")
        
        # Foco en producción
        production_focus = results['production_focus']
        if production_focus:
            print(f"\n🎯 FOCO EN CÓDIGO DE PRODUCCIÓN:")
            print(f"   {len(production_focus)} funciones huérfanas detectadas")
            
            if verbose:
                print(f"\n   Top candidatos:")
                for i, func in enumerate(production_focus[:10], 1):
                    print(f"      {i}. {func.name} ({func.file_path}:{func.line_number})")
                    print(f"         🎯 Confianza: {func.confidence:.2f} | 💼 Valor: {func.business_value}/10 | 📈 Complejidad: {func.complexity}")
            else:
                for i, func in enumerate(production_focus[:5], 1):
                    print(f"   {i}. {func.name} ({func.file_path})")
        
        # Recomendaciones
        if results['recommendations']:
            print(f"\n💡 RECOMENDACIONES:")
            for rec in results['recommendations']:
                priority_icon = "🔴" if rec['priority'] == 'HIGH' else "🟡"
                print(f"   {priority_icon} {rec['title']}")
                if verbose:
                    print(f"      {rec['description']}")
                    print(f"      Acción: {rec['action']}")
    
    def _get_category_icon(self, category: str) -> str:
        """Obtener icono para categoría."""
        icons = {
            'production': '🏭',
            'test': '🧪',
            'tooling': '🔧',
            'scripts': '📜',
            'other': '📦'
        }
        return icons.get(category, '📄')
    
    def save_results(self, results: Dict, output_file: Path):
        """Guardar resultados en archivo JSON."""
        # Convertir orphan functions a dict para serialización
        serializable_results = {
            'orphan_functions': [
                {
                    'name': f.name,
                    'file_path': f.file_path,
                    'category': f.category,
                    'confidence': f.confidence,
                    'business_value': f.business_value,
                    'priority': f.priority,
                    'complexity': f.complexity,
                    'line_number': f.line_number
                }
                for f in results['orphan_functions']
            ],
            'category_summary': results['category_summary'],
            'recommendations': results['recommendations'],
            'total_stats': results['total_stats']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Resultados guardados en: {output_file}")

def main():
    """Función principal del CLI."""
    parser = argparse.ArgumentParser(description='Análisis inteligente de código por CLI')
    parser.add_argument('--category', choices=['production', 'test', 'tooling', 'scripts', 'other'],
                       help='Filtrar por categoría específica')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostrar información detallada')
    parser.add_argument('--output', '-o', type=str,
                       help='Archivo de salida para resultados JSON')
    parser.add_argument('--production-only', action='store_true',
                       help='Mostrar solo análisis de código de producción')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    analyzer = SmartCLIAnalyzer(project_root)
    
    # Ejecutar análisis
    category_filter = args.category
    if args.production_only:
        category_filter = 'production'
    
    results = analyzer.analyze_project(category_filter)
    
    # Mostrar resultados
    analyzer.print_results(results, verbose=args.verbose, category_filter=category_filter)
    
    # Guardar si se especifica
    if args.output:
        output_file = Path(args.output)
        analyzer.save_results(results, output_file)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())