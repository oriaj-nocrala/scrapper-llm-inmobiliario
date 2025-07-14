#!/usr/bin/env python3
"""
Detector rápido de código duplicado sin dependencias ML pesadas.
Enfocado en eficiencia y resultados inmediatos.
"""
import ast
import hashlib
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from difflib import SequenceMatcher
import argparse

class QuickDuplicateDetector:
    """Detector rápido de código duplicado."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.min_lines = 5  # Mínimo líneas para considerar duplicado
        self.similarity_threshold = 0.85
    
    def detect_duplicates(self) -> Dict:
        """Detectar duplicados rápidamente."""
        print("🔍 DETECCIÓN RÁPIDA DE CÓDIGO DUPLICADO")
        print("=" * 50)
        
        # Obtener funciones de archivos Python
        functions = self._extract_functions()
        print(f"📊 Analizando {len(functions)} funciones...")
        
        # 1. Duplicados exactos (hash)
        exact_duplicates = self._find_exact_duplicates(functions)
        
        # 2. Duplicados similares (text similarity)
        similar_duplicates = self._find_similar_duplicates(functions)
        
        results = {
            'exact_duplicates': exact_duplicates,
            'similar_duplicates': similar_duplicates,
            'summary': {
                'total_functions': len(functions),
                'exact_duplicate_groups': len(exact_duplicates),
                'similar_duplicate_groups': len(similar_duplicates),
                'potential_savings': self._calculate_savings(exact_duplicates, similar_duplicates)
            }
        }
        
        return results
    
    def _extract_functions(self) -> List[Dict]:
        """Extraer funciones de archivos Python."""
        functions = []
        
        # Obtener archivos Python
        python_files = list(self.project_root.rglob("*.py"))
        exclude_dirs = {'env', '__pycache__', '.git', 'refactor_backup', 'code_rag_data'}
        python_files = [f for f in python_files if not any(excluded in f.parts for excluded in exclude_dirs)]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                lines = content.splitlines()
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if hasattr(node, 'end_lineno') and node.end_lineno:
                            func_lines = lines[node.lineno-1:node.end_lineno]
                            func_content = '\n'.join(func_lines)
                            
                            # Filtrar funciones muy pequeñas
                            if len(func_lines) >= self.min_lines:
                                functions.append({
                                    'name': node.name,
                                    'file': str(file_path.relative_to(self.project_root)),
                                    'line_start': node.lineno,
                                    'line_end': node.end_lineno,
                                    'content': func_content,
                                    'normalized': self._normalize_code(func_content),
                                    'lines_count': len(func_lines)
                                })
                        
            except Exception as e:
                print(f"⚠️ Error procesando {file_path}: {e}")
        
        return functions
    
    def _normalize_code(self, code: str) -> str:
        """Normalizar código para comparación."""
        # Remover comentarios y normalizar espacios
        lines = []
        for line in code.split('\n'):
            # Remover comentarios
            if '#' in line:
                line = line[:line.index('#')]
            # Normalizar espacios pero mantener indentación relativa
            stripped = line.strip()
            if stripped:
                # Contar indentación
                indent_level = (len(line) - len(line.lstrip())) // 4
                normalized_line = '    ' * indent_level + ' '.join(stripped.split())
                lines.append(normalized_line)
        
        return '\n'.join(lines)
    
    def _find_exact_duplicates(self, functions: List[Dict]) -> List[Dict]:
        """Encontrar duplicados exactos usando hash."""
        hash_groups = defaultdict(list)
        
        for func in functions:
            # Hash del código normalizado
            code_hash = hashlib.md5(func['normalized'].encode()).hexdigest()
            hash_groups[code_hash].append(func)
        
        # Filtrar grupos con al menos 2 funciones
        exact_duplicates = []
        for code_hash, group in hash_groups.items():
            if len(group) >= 2:
                duplicate_group = {
                    'type': 'exact',
                    'hash': code_hash,
                    'count': len(group),
                    'functions': group,
                    'lines_per_instance': group[0]['lines_count'],
                    'total_duplicate_lines': (len(group) - 1) * group[0]['lines_count'],
                    'recommendation': f"Extraer a función común - {len(group)} duplicados exactos"
                }
                exact_duplicates.append(duplicate_group)
        
        # Ordenar por total de líneas duplicadas
        return sorted(exact_duplicates, key=lambda x: x['total_duplicate_lines'], reverse=True)
    
    def _find_similar_duplicates(self, functions: List[Dict]) -> List[Dict]:
        """Encontrar duplicados similares usando comparación de texto."""
        similar_groups = []
        processed = set()
        
        for i, func1 in enumerate(functions):
            if i in processed:
                continue
            
            similar_funcs = [func1]
            
            for j, func2 in enumerate(functions[i+1:], i+1):
                if j in processed:
                    continue
                
                # Calcular similitud
                similarity = SequenceMatcher(None, func1['normalized'], func2['normalized']).ratio()
                
                if similarity >= self.similarity_threshold:
                    similar_funcs.append(func2)
                    processed.add(j)
            
            if len(similar_funcs) >= 2:
                processed.add(i)
                
                # Calcular similitud promedio
                avg_similarity = sum(
                    SequenceMatcher(None, func1['normalized'], func['normalized']).ratio()
                    for func in similar_funcs[1:]
                ) / (len(similar_funcs) - 1)
                
                avg_lines = sum(func['lines_count'] for func in similar_funcs) / len(similar_funcs)
                
                similar_group = {
                    'type': 'similar',
                    'similarity': avg_similarity,
                    'count': len(similar_funcs),
                    'functions': similar_funcs,
                    'avg_lines_per_instance': int(avg_lines),
                    'potential_savings': int(avg_lines * (len(similar_funcs) - 1) * 0.7),  # 70% de ahorro estimado
                    'recommendation': f"Refactorizar similitudes - {len(similar_funcs)} funciones {avg_similarity:.0%} similares"
                }
                similar_groups.append(similar_group)
        
        # Ordenar por potential savings
        return sorted(similar_groups, key=lambda x: x['potential_savings'], reverse=True)[:10]  # Top 10
    
    def _calculate_savings(self, exact_dups: List, similar_dups: List) -> Dict:
        """Calcular ahorros potenciales."""
        exact_savings = sum(dup['total_duplicate_lines'] for dup in exact_dups)
        similar_savings = sum(dup['potential_savings'] for dup in similar_dups)
        
        return {
            'exact_duplicate_lines': exact_savings,
            'similar_duplicate_lines': similar_savings,
            'total_potential_savings': exact_savings + similar_savings,
            'maintenance_hours_saved': (exact_savings + similar_savings) * 0.1  # 6 min por línea
        }
    
    def print_results(self, results: Dict, verbose: bool = False):
        """Mostrar resultados."""
        summary = results['summary']
        
        print(f"\n📊 RESUMEN DE DUPLICACIÓN")
        print("=" * 30)
        print(f"📁 Funciones analizadas: {summary['total_functions']}")
        print(f"🔄 Grupos duplicados exactos: {summary['exact_duplicate_groups']}")
        print(f"📐 Grupos similares: {summary['similar_duplicate_groups']}")
        print(f"💾 Líneas ahorradas (exactos): {summary['potential_savings']['exact_duplicate_lines']}")
        print(f"🔧 Líneas ahorradas (similares): {summary['potential_savings']['similar_duplicate_lines']}")
        print(f"⏱️ Horas de mantenimiento ahorradas: {summary['potential_savings']['maintenance_hours_saved']:.1f}")
        
        # Mostrar top duplicados exactos
        if results['exact_duplicates']:
            print(f"\n🔄 TOP DUPLICADOS EXACTOS:")
            for i, dup in enumerate(results['exact_duplicates'][:5], 1):
                print(f"   {i}. {dup['count']} instancias × {dup['lines_per_instance']} líneas")
                print(f"      💾 Ahorro: {dup['total_duplicate_lines']} líneas")
                if verbose:
                    for func in dup['functions'][:3]:  # Mostrar max 3 ejemplos
                        print(f"         📂 {func['name']} ({func['file']}:{func['line_start']})")
                else:
                    print(f"         📂 {dup['functions'][0]['name']} y {dup['count']-1} más...")
        
        # Mostrar top similares
        if results['similar_duplicates']:
            print(f"\n📐 TOP DUPLICADOS SIMILARES:")
            for i, dup in enumerate(results['similar_duplicates'][:5], 1):
                print(f"   {i}. {dup['count']} funciones {dup['similarity']:.0%} similares")
                print(f"      🔧 Ahorro potencial: {dup['potential_savings']} líneas")
                if verbose:
                    for func in dup['functions'][:3]:
                        print(f"         📂 {func['name']} ({func['file']}:{func['line_start']})")
                else:
                    print(f"         📂 {dup['functions'][0]['name']} y {dup['count']-1} más...")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        total_savings = summary['potential_savings']['total_potential_savings']
        if total_savings > 100:
            print(f"   🔴 ALTA PRIORIDAD: {total_savings} líneas duplicadas detectadas")
            print(f"   📋 Acción: Crear funciones comunes para duplicados exactos")
            print(f"   🔧 Refactorizar: Abstraer patrones similares")
        elif total_savings > 50:
            print(f"   🟡 MEDIA PRIORIDAD: {total_savings} líneas duplicadas")
            print(f"   📋 Acción: Revisar duplicados más grandes primero")
        else:
            print(f"   ✅ Duplicación bajo control: solo {total_savings} líneas")
    
    def save_results(self, results: Dict, output_file: Path):
        """Guardar resultados en JSON."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Resultados guardados en: {output_file}")

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Detector rápido de código duplicado')
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
    detector = QuickDuplicateDetector(project_root)
    
    # Configurar parámetros
    detector.min_lines = args.min_lines
    detector.similarity_threshold = args.similarity
    
    # Ejecutar detección
    results = detector.detect_duplicates()
    
    # Mostrar resultados
    detector.print_results(results, verbose=args.verbose)
    
    # Guardar si se especifica
    if args.output:
        output_file = Path(args.output)
        detector.save_results(results, output_file)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())