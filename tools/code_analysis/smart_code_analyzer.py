#!/usr/bin/env python3
"""
Analizador inteligente de código que categoriza por importancia y contexto.
Prioriza código de producción en /src/ sobre tests y herramientas.
"""
import json
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter
from enum import Enum
import re

class CodeCategory(Enum):
    """Categorías de código por importancia."""
    PRODUCTION = "production"      # /src/ - Código de producción
    TEST = "test"                 # /tests/ - Código de testing
    TOOLING = "tooling"           # /tools/ - Herramientas de desarrollo
    SCRIPTS = "scripts"           # /scripts/ - Scripts de automatización
    CONFIG = "config"             # Archivos de configuración
    DOCS = "docs"                 # Documentación
    OTHER = "other"               # Otros archivos

@dataclass
class SmartCodeChunk:
    """Chunk de código con categorización inteligente."""
    id: str
    name: str
    file_path: str
    category: CodeCategory
    priority: int  # 1-10, donde 10 = más importante
    chunk_type: str
    content: str
    line_start: int
    line_end: int
    complexity: int
    dependencies: List[str]
    used_by: List[str]
    is_orphan: bool
    orphan_confidence: float  # 0-1, donde 1 = definitivamente huérfano
    business_value: int  # 1-10, importancia para el negocio
    docstring: Optional[str] = None

class SmartCodeAnalyzer:
    """Analizador inteligente con categorización automática."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.chunks: List[SmartCodeChunk] = []
        self.usage_graph = defaultdict(set)
        self.reverse_usage = defaultdict(set)
        
        # Patrones para detectar importancia de negocio
        self.business_patterns = {
            'api': ['endpoint', 'route', 'api', 'handler', 'controller'],
            'core': ['scrape', 'extract', 'process', 'pipeline', 'main'],
            'data': ['model', 'schema', 'entity', 'dto'],
            'integration': ['client', 'service', 'adapter', 'connector'],
            'config': ['config', 'settings', 'constants', 'env']
        }
        
        # Directorios críticos en /src/
        self.critical_src_dirs = {
            'api': 10,          # APIs son críticas
            'scraper': 9,       # Core del negocio
            'rag': 8,           # Sistema RAG
            'integration': 7,   # Integraciones
            'vectorstore': 6,   # Almacenamiento
            'cli': 5,           # Interface de usuario
            'utils': 4,         # Utilidades
            'agent': 3          # Agentes
        }
    
    def analyze_project(self) -> Dict[str, List[SmartCodeChunk]]:
        """Analizar proyecto completo con categorización inteligente."""
        print("🧠 ANÁLISIS INTELIGENTE DE CÓDIGO")
        print("=" * 50)
        
        # 1. Encontrar y categorizar archivos
        python_files = self._find_and_categorize_files()
        
        # 2. Analizar cada archivo
        for file_path, category in python_files:
            print(f"🔍 {category.value}: {file_path.relative_to(self.project_root)}")
            chunks = self._analyze_file(file_path, category)
            self.chunks.extend(chunks)
        
        # 3. Construir grafo de dependencias
        self._build_dependency_graph()
        
        # 4. Detectar código huérfano con inteligencia
        self._smart_orphan_detection()
        
        # 5. Categorizar por tipo
        categorized = self._categorize_chunks()
        
        print(f"\n✅ Análisis completo:")
        for category, chunks in categorized.items():
            print(f"   {category}: {len(chunks)} chunks")
        
        return categorized
    
    def _find_and_categorize_files(self) -> List[Tuple[Path, CodeCategory]]:
        """Encontrar archivos Python y categorizarlos por importancia."""
        files_with_categories = []
        exclude_dirs = {'env', '__pycache__', '.git', 'refactor_backup', 'code_rag_data'}
        
        for py_file in self.project_root.rglob("*.py"):
            if any(excluded in py_file.parts for excluded in exclude_dirs):
                continue
            
            category = self._categorize_file(py_file)
            files_with_categories.append((py_file, category))
        
        # Ordenar por importancia (producción primero)
        category_priority = {
            CodeCategory.PRODUCTION: 1,
            CodeCategory.SCRIPTS: 2,
            CodeCategory.TOOLING: 3,
            CodeCategory.TEST: 4,
            CodeCategory.CONFIG: 5,
            CodeCategory.DOCS: 6,
            CodeCategory.OTHER: 7
        }
        
        files_with_categories.sort(key=lambda x: category_priority[x[1]])
        return files_with_categories
    
    def _categorize_file(self, file_path: Path) -> CodeCategory:
        """Categorizar archivo según su ubicación y propósito."""
        parts = file_path.relative_to(self.project_root).parts
        
        if not parts:
            return CodeCategory.OTHER
        
        first_dir = parts[0].lower()
        file_name = file_path.name.lower()
        
        # Categorización por directorio
        if first_dir == 'src':
            return CodeCategory.PRODUCTION
        elif first_dir == 'tests':
            return CodeCategory.TEST
        elif first_dir == 'tools':
            return CodeCategory.TOOLING
        elif first_dir == 'scripts':
            return CodeCategory.SCRIPTS
        elif first_dir == 'docs':
            return CodeCategory.DOCS
        
        # Categorización por nombre de archivo
        if any(pattern in file_name for pattern in ['test_', '_test', 'conftest']):
            return CodeCategory.TEST
        elif any(pattern in file_name for pattern in ['config', 'settings', 'setup']):
            return CodeCategory.CONFIG
        elif file_name in ['main.py', '__init__.py']:
            # Si está en raíz, podría ser importante
            if len(parts) == 1:
                return CodeCategory.PRODUCTION
        
        return CodeCategory.OTHER
    
    def _analyze_file(self, file_path: Path, category: CodeCategory) -> List[SmartCodeChunk]:
        """Analizar archivo individual con contexto de categoría."""
        chunks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.splitlines()
            
            # Analizar funciones
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    chunk = self._create_function_chunk(node, lines, file_path, category)
                    chunks.append(chunk)
                elif isinstance(node, ast.ClassDef):
                    chunk = self._create_class_chunk(node, lines, file_path, category)
                    chunks.append(chunk)
        
        except Exception as e:
            print(f"⚠️ Error analizando {file_path}: {e}")
        
        return chunks
    
    def _create_function_chunk(self, node: ast.FunctionDef, lines: List[str], 
                              file_path: Path, category: CodeCategory) -> SmartCodeChunk:
        """Crear chunk para función con análisis inteligente."""
        # Calcular complejidad específica de función
        complexity = self._calculate_complexity(node)
        dependencies = self._extract_dependencies(node)
        
        return self._create_code_chunk(
            node, lines, file_path, category, "function", 
            complexity, dependencies, node.name, 10
        )
    
    def _create_class_chunk(self, node: ast.ClassDef, lines: List[str], 
                           file_path: Path, category: CodeCategory) -> SmartCodeChunk:
        """Crear chunk para clase."""
        # Contar métodos como complejidad
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        complexity = len(methods)
        dependencies = []  # Las clases no tienen dependencias directas como las funciones
        
        return self._create_code_chunk(
            node, lines, file_path, category, "class", 
            complexity, dependencies, node.name, 20
        )
    
    def _calculate_priority(self, name: str, file_path: Path, 
                           category: CodeCategory, content: str) -> int:
        """Calcular prioridad inteligente (1-10)."""
        priority = 5  # Base
        
        # Ajuste por categoría
        if category == CodeCategory.PRODUCTION:
            priority += 3
            
            # Bonus por directorio específico en /src/
            parts = file_path.parts
            if len(parts) > 1 and parts[0] == 'src' and len(parts) > 2:
                src_subdir = parts[1]
                priority += self.critical_src_dirs.get(src_subdir, 0) // 2
                
        elif category == CodeCategory.SCRIPTS:
            priority += 1
        elif category == CodeCategory.TEST:
            priority -= 2
        elif category == CodeCategory.TOOLING:
            priority -= 1
        
        # Bonus por patrones importantes
        name_lower = name.lower()
        content_lower = content.lower()
        
        # Funciones críticas del negocio
        if any(pattern in name_lower for pattern in ['main', 'run', 'start', 'init']):
            priority += 2
        
        if any(pattern in name_lower for pattern in ['scrape', 'extract', 'process']):
            priority += 2
        
        if any(pattern in name_lower for pattern in ['api', 'endpoint', 'handler']):
            priority += 2
        
        # Penalizar funciones privadas y de test
        if name.startswith('_'):
            priority -= 1
        
        if name.startswith('test_') or 'test' in file_path.name:
            priority -= 2
        
        return max(1, min(10, priority))
    
    def _calculate_business_value(self, name: str, file_path: Path, content: str) -> int:
        """Calcular valor de negocio (1-10)."""
        value = 5  # Base
        
        name_lower = name.lower()
        file_lower = str(file_path).lower()
        content_lower = content.lower()
        
        # Alto valor: funcionalidad core del negocio
        high_value_patterns = [
            'scrape', 'extract', 'property', 'rag', 'api', 'main', 'pipeline',
            'process', 'generate', 'create', 'run', 'start'
        ]
        
        if any(pattern in name_lower for pattern in high_value_patterns):
            value += 3
        
        # Valor medio: utilidades importantes
        medium_value_patterns = [
            'config', 'validate', 'parse', 'format', 'convert', 'transform'
        ]
        
        if any(pattern in name_lower for pattern in medium_value_patterns):
            value += 1
        
        # Bajo valor: tests, helpers, debug
        low_value_patterns = [
            'test_', 'debug', 'print', 'log', 'helper', '_internal'
        ]
        
        if any(pattern in name_lower for pattern in low_value_patterns):
            value -= 2
        
        # Bonus por estar en directorios importantes
        if 'src/api' in file_lower or 'src/scraper' in file_lower:
            value += 2
        elif 'src/rag' in file_lower:
            value += 2
        elif 'test' in file_lower or 'tools' in file_lower:
            value -= 1
        
        return max(1, min(10, value))
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calcular complejidad ciclomática."""
        from code_utils import calculate_complexity
        return calculate_complexity(node)
    
    def _extract_dependencies(self, node: ast.FunctionDef) -> List[str]:
        """Extraer dependencias de la función."""
        dependencies = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    dependencies.append(child.func.attr)
        
        return list(set(dependencies))
    
    def _build_dependency_graph(self):
        """Construir grafo de dependencias entre chunks."""
        print("🔗 Construyendo grafo de dependencias...")
        
        # Mapear nombres a chunks
        name_to_chunks = defaultdict(list)
        for chunk in self.chunks:
            name_to_chunks[chunk.name].append(chunk)
        
        # Construir conexiones
        for chunk in self.chunks:
            for dep_name in chunk.dependencies:
                if dep_name in name_to_chunks:
                    for dep_chunk in name_to_chunks[dep_name]:
                        if dep_chunk.id != chunk.id:
                            self.usage_graph[chunk.id].add(dep_chunk.id)
                            self.reverse_usage[dep_chunk.id].add(chunk.id)
                            dep_chunk.used_by.append(chunk.id)
    
    def _smart_orphan_detection(self):
        """Detección inteligente de código huérfano."""
        print("🔍 Detectando código huérfano con inteligencia...")
        
        for chunk in self.chunks:
            orphan_score = self._calculate_orphan_score(chunk)
            chunk.orphan_confidence = orphan_score
            chunk.is_orphan = orphan_score > 0.7  # Umbral ajustable
    
    def _calculate_orphan_score(self, chunk: SmartCodeChunk) -> float:
        """Calcular score de probabilidad de ser huérfano (0-1)."""
        score = 0.0
        
        # Base: si no tiene usos directos
        if not chunk.used_by and chunk.id not in self.reverse_usage:
            score += 0.5
        
        # Ajustes por categoría
        if chunk.category == CodeCategory.TEST:
            # Tests pueden parecer huérfanos pero son válidos
            score -= 0.3
        elif chunk.category == CodeCategory.PRODUCTION:
            # Código de producción huérfano es más problemático
            score += 0.2
        elif chunk.category == CodeCategory.TOOLING:
            # Tools pueden ser standalone
            score -= 0.1
        
        # Ajustes por tipo de función
        name_lower = chunk.name.lower()
        
        # Funciones especiales que pueden parecer huérfanas
        special_functions = ['main', '__init__', 'setup', 'teardown', 'run']
        if any(special in name_lower for special in special_functions):
            score -= 0.4
        
        # Funciones de test
        if name_lower.startswith('test_'):
            score -= 0.5
        
        # Funciones privadas tienen más probabilidad de ser huérfanas
        if chunk.name.startswith('_') and not chunk.name.startswith('__'):
            score += 0.2
        
        # Funciones con alta complejidad pero sin uso son sospechosas
        if chunk.complexity > 10 and not chunk.used_by:
            score += 0.3
        
        # Funciones con bajo valor de negocio
        if chunk.business_value <= 3:
            score += 0.1
        
        # Funciones con alto valor de negocio es improbable que sean huérfanas
        if chunk.business_value >= 8:
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _create_code_chunk(self, node, lines: List[str], file_path: Path, 
                          category: CodeCategory, chunk_type: str, complexity: int,
                          dependencies: List[str], name: str, default_length: int) -> SmartCodeChunk:
        """Crear chunk de código común para funciones y clases."""
        line_start = node.lineno
        line_end = node.end_lineno or line_start + default_length
        
        # Contenido del chunk
        chunk_lines = lines[line_start-1:line_end]
        content = '\n'.join(chunk_lines)
        
        # Calcular métricas
        priority = self._calculate_priority(name, file_path, category, content)
        business_value = self._calculate_business_value(name, file_path, content)
        
        # ID único
        chunk_id = f"{file_path}::{name}"
        
        return SmartCodeChunk(
            id=chunk_id,
            name=name,
            file_path=str(file_path.relative_to(self.project_root)),
            category=category,
            priority=priority,
            chunk_type=chunk_type,
            content=content,
            line_start=line_start,
            line_end=line_end,
            complexity=complexity,
            dependencies=dependencies,
            used_by=[],  # Se llena después
            is_orphan=False,  # Se determina después
            orphan_confidence=0.0,
            business_value=business_value,
            docstring=ast.get_docstring(node)
        )
    
    def _categorize_chunks(self) -> Dict[str, List[SmartCodeChunk]]:
        """Categorizar chunks por tipo de código."""
        categorized = {
            'production': [],
            'test': [],
            'tooling': [],
            'scripts': [],
            'other': []
        }
        
        for chunk in self.chunks:
            if chunk.category == CodeCategory.PRODUCTION:
                categorized['production'].append(chunk)
            elif chunk.category == CodeCategory.TEST:
                categorized['test'].append(chunk)
            elif chunk.category == CodeCategory.TOOLING:
                categorized['tooling'].append(chunk)
            elif chunk.category == CodeCategory.SCRIPTS:
                categorized['scripts'].append(chunk)
            else:
                categorized['other'].append(chunk)
        
        return categorized
    
    def get_orphan_summary(self) -> Dict[str, any]:
        """Obtener resumen inteligente de código huérfano."""
        production_orphans = [
            c for c in self.chunks 
            if c.category == CodeCategory.PRODUCTION and c.is_orphan
        ]
        
        high_confidence_orphans = [
            c for c in production_orphans 
            if c.orphan_confidence > 0.8
        ]
        
        # Ordenar por prioridad e impacto
        production_orphans.sort(key=lambda x: (x.priority, x.business_value), reverse=True)
        
        return {
            'total_production_chunks': len([c for c in self.chunks if c.category == CodeCategory.PRODUCTION]),
            'production_orphans': len(production_orphans),
            'high_confidence_orphans': len(high_confidence_orphans),
            'orphan_rate': len(production_orphans) / len([c for c in self.chunks if c.category == CodeCategory.PRODUCTION]) * 100,
            'top_orphan_candidates': [
                {
                    'name': c.name,
                    'file': c.file_path,
                    'confidence': c.orphan_confidence,
                    'priority': c.priority,
                    'business_value': c.business_value,
                    'complexity': c.complexity
                }
                for c in production_orphans[:10]
            ]
        }
    
    def save_analysis(self, output_file: Path):
        """Guardar análisis completo."""
        data = {
            'timestamp': str(Path().resolve()),
            'summary': self.get_orphan_summary(),
            'chunks_by_category': {},
            'detailed_chunks': []
        }
        
        # Agrupar por categoría
        for chunk in self.chunks:
            category = chunk.category.value
            if category not in data['chunks_by_category']:
                data['chunks_by_category'][category] = []
            
            chunk_data = {
                'id': chunk.id,
                'name': chunk.name,
                'file_path': chunk.file_path,
                'priority': chunk.priority,
                'business_value': chunk.business_value,
                'complexity': chunk.complexity,
                'is_orphan': chunk.is_orphan,
                'orphan_confidence': chunk.orphan_confidence,
                'used_by_count': len(chunk.used_by)
            }
            
            data['chunks_by_category'][category].append(chunk_data)
            data['detailed_chunks'].append(chunk_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Análisis guardado en: {output_file}")

def main():
    """Ejecutar análisis inteligente."""
    project_root = Path(__file__).parent.parent
    analyzer = SmartCodeAnalyzer(project_root)
    
    # Analizar proyecto
    categorized = analyzer.analyze_project()
    
    # Mostrar resumen
    summary = analyzer.get_orphan_summary()
    
    print(f"\n📊 RESUMEN INTELIGENTE")
    print("=" * 50)
    print(f"📁 Código de producción: {summary['total_production_chunks']} chunks")
    print(f"❌ Huérfanos en producción: {summary['production_orphans']} ({summary['orphan_rate']:.1f}%)")
    print(f"🎯 Alta confianza: {summary['high_confidence_orphans']} candidatos")
    
    print(f"\n🔥 TOP CANDIDATOS PARA REVISIÓN:")
    for i, candidate in enumerate(summary['top_orphan_candidates'][:5], 1):
        print(f"   {i}. {candidate['name']} ({candidate['file']})")
        print(f"      🎯 Confianza: {candidate['confidence']:.2f} | Valor: {candidate['business_value']}/10")
    
    # Guardar análisis
    output_file = project_root / "tools" / "smart_analysis.json"
    analyzer.save_analysis(output_file)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())