#!/usr/bin/env python3
"""
Motor de análisis por chunks con cache inteligente.
Estrategia divide y vencerás para proyectos grandes.
"""
import json
import hashlib
import pickle
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import concurrent.futures
import threading
from collections import defaultdict

@dataclass
class FileMetadata:
    """Metadata de archivo para cache."""
    path: str
    size: int
    mtime: float
    hash: str
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'FileMetadata':
        """Crear metadata de archivo."""
        stat = file_path.stat()
        with open(file_path, 'rb') as f:
            content_hash = hashlib.md5(f.read()).hexdigest()
        
        return cls(
            path=str(file_path),
            size=stat.st_size,
            mtime=stat.st_mtime,
            hash=content_hash
        )

@dataclass
class AnalysisChunk:
    """Chunk de análisis."""
    id: str
    files: List[Path]
    category: str
    priority: int
    estimated_time: float
    dependencies: List[str] = None

class ChunkedAnalysisEngine:
    """Motor de análisis por chunks con cache inteligente."""
    
    def __init__(self, project_root: Path, cache_dir: Optional[Path] = None):
        self.project_root = project_root
        self.cache_dir = cache_dir or (project_root / "tools" / "analysis_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache management
        self.file_cache = {}
        self.analysis_cache = {}
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.metadata_file = self.cache_dir / "file_metadata.json"
        
        # Performance tracking
        self.stats = {
            'total_files': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'chunks_processed': 0,
            'total_analysis_time': 0,
            'chunks_from_cache': 0
        }
        
        # Load existing cache
        self._load_cache_index()
        
    def _load_cache_index(self):
        """Cargar índice de cache existente."""
        try:
            if self.cache_index_file.exists():
                with open(self.cache_index_file, 'r') as f:
                    cache_data = json.load(f)
                    self.file_cache = cache_data.get('file_cache', {})
                    print(f"📚 Cache cargado: {len(self.file_cache)} archivos")
        except Exception as e:
            print(f"⚠️ Error cargando cache: {e}")
            self.file_cache = {}
    
    def _save_cache_index(self):
        """Guardar índice de cache."""
        try:
            cache_data = {
                'file_cache': self.file_cache,
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats
            }
            
            with open(self.cache_index_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error guardando cache: {e}")
    
    def _get_file_cache_key(self, file_path: Path) -> str:
        """Generar clave de cache para archivo."""
        metadata = FileMetadata.from_file(file_path)
        return f"{metadata.hash}_{metadata.mtime}_{metadata.size}"
    
    def _is_file_cached(self, file_path: Path) -> bool:
        """Verificar si archivo está en cache y es válido."""
        try:
            cache_key = self._get_file_cache_key(file_path)
            return cache_key in self.file_cache
        except:
            return False
    
    def analyze_project_chunked(self, 
                               chunk_size: int = 50,
                               max_workers: int = 3,
                               enable_parallel: bool = True) -> Dict[str, Any]:
        """Analizar proyecto completo por chunks."""
        
        print(f"🚀 ANÁLISIS CHUNKED DEL PROYECTO COMPLETO")
        print(f"📊 Chunk size: {chunk_size} archivos | Workers: {max_workers}")
        print("=" * 60)
        
        start_time = time.time()
        
        # 1. Dividir archivos en chunks inteligentes
        chunks = self._create_intelligent_chunks(chunk_size)
        print(f"📦 Creados {len(chunks)} chunks para análisis")
        
        # 2. Procesar chunks (paralelo o secuencial)
        if enable_parallel and len(chunks) > 1:
            results = self._process_chunks_parallel(chunks, max_workers)
        else:
            results = self._process_chunks_sequential(chunks)
        
        # 3. Consolidar resultados
        consolidated = self._consolidate_results(results)
        
        # 4. Generar análisis de duplicados cross-chunk
        cross_chunk_duplicates = self._find_cross_chunk_duplicates(results)
        consolidated['cross_chunk_duplicates'] = cross_chunk_duplicates
        
        # 5. Estadísticas finales
        total_time = time.time() - start_time
        self.stats['total_analysis_time'] = total_time
        
        consolidated['performance_stats'] = {
            **self.stats,
            'chunks_analyzed': len(chunks),
            'parallel_processing': enable_parallel,
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['cache_hits'] + self.stats['cache_misses']) * 100,
            'analysis_speed': self.stats['total_files'] / total_time if total_time > 0 else 0
        }
        
        # 6. Guardar cache
        self._save_cache_index()
        
        print(f"\n✅ Análisis completo en {total_time:.2f}s")
        print(f"📊 Cache hit rate: {consolidated['performance_stats']['cache_hit_rate']:.1f}%")
        print(f"⚡ Velocidad: {consolidated['performance_stats']['analysis_speed']:.1f} archivos/segundo")
        
        return consolidated
    
    def _create_intelligent_chunks(self, chunk_size: int) -> List[AnalysisChunk]:
        """Crear chunks inteligentes basados en categoría y dependencias."""
        
        # Obtener todos los archivos Python
        all_files = list(self.project_root.rglob("*.py"))
        exclude_dirs = {'env', '__pycache__', '.git', 'refactor_backup', 'analysis_cache'}
        
        files_by_category = defaultdict(list)
        
        for file_path in all_files:
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
                
            category = self._categorize_file(file_path)
            files_by_category[category].append(file_path)
            self.stats['total_files'] += 1
        
        chunks = []
        chunk_id = 0
        
        # Crear chunks por categoría (mantiene cohesión)
        category_priority = {
            'production': 1,    # Más importante
            'test': 2,
            'tooling': 3,
            'scripts': 4,
            'other': 5
        }
        
        for category, files in files_by_category.items():
            priority = category_priority.get(category, 5)
            
            # Dividir archivos grandes en sub-chunks
            for i in range(0, len(files), chunk_size):
                chunk_files = files[i:i + chunk_size]
                
                chunk = AnalysisChunk(
                    id=f"chunk_{chunk_id:03d}_{category}",
                    files=chunk_files,
                    category=category,
                    priority=priority,
                    estimated_time=self._estimate_chunk_time(chunk_files)
                )
                
                chunks.append(chunk)
                chunk_id += 1
        
        # Ordenar por prioridad (producción primero)
        chunks.sort(key=lambda x: (x.priority, -len(x.files)))
        
        print(f"📋 Chunks por categoría:")
        category_counts = defaultdict(int)
        for chunk in chunks:
            category_counts[chunk.category] += 1
        
        for category, count in category_counts.items():
            file_count = sum(len(chunk.files) for chunk in chunks if chunk.category == category)
            print(f"   {category}: {count} chunks ({file_count} archivos)")
        
        return chunks
    
    def _estimate_chunk_time(self, files: List[Path]) -> float:
        """Estimar tiempo de procesamiento del chunk."""
        total_size = sum(f.stat().st_size for f in files if f.exists())
        # Estimación: ~1MB por segundo + overhead por archivo
        return (total_size / (1024 * 1024)) + (len(files) * 0.1)
    
    def _process_chunks_parallel(self, chunks: List[AnalysisChunk], max_workers: int) -> List[Dict]:
        """Procesar chunks en paralelo."""
        print(f"⚡ Procesando {len(chunks)} chunks en paralelo ({max_workers} workers)")
        
        results = []
        lock = threading.Lock()
        
        def process_chunk_safe(chunk):
            """Wrapper thread-safe para procesar chunk."""
            try:
                result = self._process_single_chunk(chunk)
                with lock:
                    self.stats['chunks_processed'] += 1
                    progress = (self.stats['chunks_processed'] / len(chunks)) * 100
                    print(f"   ✅ {chunk.id} completado ({progress:.1f}%)")
                return result
            except Exception as e:
                print(f"   ❌ Error en {chunk.id}: {e}")
                return {'chunk_id': chunk.id, 'error': str(e), 'functions': [], 'duplicates': []}
        
        # Usar ThreadPoolExecutor para análisis I/O bound
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {executor.submit(process_chunk_safe, chunk): chunk for chunk in chunks}
            
            for future in concurrent.futures.as_completed(future_to_chunk):
                result = future.result()
                results.append(result)
        
        return results
    
    def _process_chunks_sequential(self, chunks: List[AnalysisChunk]) -> List[Dict]:
        """Procesar chunks secuencialmente."""
        print(f"🔄 Procesando {len(chunks)} chunks secuencialmente")
        
        results = []
        for i, chunk in enumerate(chunks, 1):
            try:
                result = self._process_single_chunk(chunk)
                results.append(result)
                
                progress = (i / len(chunks)) * 100
                print(f"   ✅ {chunk.id} completado ({progress:.1f}%)")
                
            except Exception as e:
                print(f"   ❌ Error en {chunk.id}: {e}")
                results.append({
                    'chunk_id': chunk.id, 
                    'error': str(e), 
                    'functions': [], 
                    'duplicates': []
                })
        
        return results
    
    def _process_single_chunk(self, chunk: AnalysisChunk) -> Dict:
        """Procesar un chunk individual."""
        chunk_start = time.time()
        
        # Verificar cache
        cached_results = self._get_chunk_from_cache(chunk)
        if cached_results:
            self.stats['chunks_from_cache'] += 1
            return cached_results
        
        # Procesar chunk
        from refined_duplicate_detector import RefinedDuplicateDetector
        from smart_code_analyzer import SmartCodeAnalyzer
        
        # Análisis de duplicados en el chunk
        detector = RefinedDuplicateDetector(self.project_root)
        
        # Filtrar solo archivos del chunk
        chunk_functions = []
        for file_path in chunk.files:
            if self._is_file_cached(file_path):
                self.stats['cache_hits'] += 1
                # TODO: Cargar funciones del cache
                continue
            else:
                self.stats['cache_misses'] += 1
            
            try:
                # Use simplified function extraction for now
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    import ast
                    tree = ast.parse(content, filename=str(file_path))
                    
                    functions = []
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            functions.append({
                                'name': node.name,
                                'file_path': str(file_path),
                                'category': chunk.category,
                                'lineno': node.lineno,
                                'normalized': ast.get_source_segment(content, node) or ''
                            })
                except:
                    functions = []
                chunk_functions.extend(functions)
                
                # Guardar en cache
                self._cache_file_functions(file_path, functions)
                
            except Exception as e:
                print(f"     ⚠️ Error en {file_path}: {e}")
        
        # Buscar duplicados dentro del chunk
        chunk_duplicates = []
        if len(chunk_functions) > 1:
            candidates = detector._filter_problematic_candidates(chunk_functions)
            if candidates:
                clusters = detector._detect_intelligent_clusters(candidates)
                chunk_duplicates = clusters
        
        result = {
            'chunk_id': chunk.id,
            'category': chunk.category,
            'files_count': len(chunk.files),
            'functions_count': len(chunk_functions),
            'functions': chunk_functions,
            'duplicates': chunk_duplicates,
            'processing_time': time.time() - chunk_start
        }
        
        # Guardar en cache
        self._cache_chunk_result(chunk, result)
        
        return result
    
    def _get_chunk_from_cache(self, chunk: AnalysisChunk) -> Optional[Dict]:
        """Obtener resultado de chunk desde cache."""
        # Verificar si todos los archivos del chunk están en cache y son válidos
        cache_key = self._get_chunk_cache_key(chunk)
        cache_file = self.cache_dir / f"chunk_{cache_key}.pkl"
        
        if not cache_file.exists():
            return None
        
        # Verificar que ningún archivo haya cambiado
        for file_path in chunk.files:
            if not self._is_file_cached(file_path):
                return None
        
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except:
            return None
    
    def _cache_chunk_result(self, chunk: AnalysisChunk, result: Dict):
        """Guardar resultado de chunk en cache."""
        try:
            cache_key = self._get_chunk_cache_key(chunk)
            cache_file = self.cache_dir / f"chunk_{cache_key}.pkl"
            
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
                
        except Exception as e:
            print(f"⚠️ Error guardando chunk en cache: {e}")
    
    def _get_chunk_cache_key(self, chunk: AnalysisChunk) -> str:
        """Generar clave de cache para chunk."""
        file_hashes = []
        for file_path in chunk.files:
            try:
                file_hashes.append(self._get_file_cache_key(file_path))
            except:
                file_hashes.append(str(file_path))
        
        chunk_content = f"{chunk.category}_{len(chunk.files)}_{'_'.join(sorted(file_hashes))}"
        return hashlib.md5(chunk_content.encode()).hexdigest()[:12]
    
    def _cache_file_functions(self, file_path: Path, functions: List[Dict]):
        """Guardar funciones de archivo en cache."""
        try:
            cache_key = self._get_file_cache_key(file_path)
            self.file_cache[cache_key] = {
                'file_path': str(file_path),
                'functions': functions,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"⚠️ Error cacheando archivo {file_path}: {e}")
    
    def _consolidate_results(self, chunk_results: List[Dict]) -> Dict[str, Any]:
        """Consolidar resultados de todos los chunks."""
        
        consolidated = {
            'total_chunks': len(chunk_results),
            'successful_chunks': len([r for r in chunk_results if 'error' not in r]),
            'failed_chunks': len([r for r in chunk_results if 'error' in r]),
            'categories': defaultdict(lambda: {'chunks': 0, 'files': 0, 'functions': 0, 'duplicates': 0}),
            'all_functions': [],
            'all_duplicates': [],
            'processing_times': []
        }
        
        for result in chunk_results:
            if 'error' in result:
                continue
                
            category = result['category']
            consolidated['categories'][category]['chunks'] += 1
            consolidated['categories'][category]['files'] += result['files_count']
            consolidated['categories'][category]['functions'] += result['functions_count']
            consolidated['categories'][category]['duplicates'] += len(result['duplicates'])
            
            consolidated['all_functions'].extend(result['functions'])
            consolidated['all_duplicates'].extend(result['duplicates'])
            consolidated['processing_times'].append(result['processing_time'])
        
        return consolidated
    
    def _find_cross_chunk_duplicates(self, chunk_results: List[Dict]) -> List[Dict]:
        """Encontrar duplicados entre chunks diferentes."""
        print("🔍 Buscando duplicados cross-chunk...")
        
        # Agrupar funciones por categoría
        from collections import defaultdict
        functions_by_category = defaultdict(list)
        for result in chunk_results:
            if 'error' not in result:
                for func in result['functions']:
                    functions_by_category[result['category']].append(func)
        
        cross_duplicates = []
        
        # Buscar duplicados entre producción principalmente
        if 'production' in functions_by_category:
            production_functions = functions_by_category['production']
            
            # Implementar búsqueda eficiente de duplicados
            by_normalized = defaultdict(list)
            
            for func in production_functions:
                normalized = func.get('normalized', '')
                if len(normalized) > 100:  # Solo funciones significativas
                    by_normalized[normalized].append(func)
            
            # Encontrar grupos duplicados
            for normalized, funcs in by_normalized.items():
                if len(funcs) > 1:
                    cross_duplicates.append({
                        'type': 'cross_chunk_exact',
                        'functions': funcs,
                        'similarity': 1.0,
                        'category': 'production'
                    })
        
        print(f"   ✅ Encontrados {len(cross_duplicates)} duplicados cross-chunk")
        return cross_duplicates
    
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

def main():
    """Ejecutar análisis chunked completo."""
    project_root = Path(__file__).parent.parent
    
    print("🚀 MOTOR DE ANÁLISIS CHUNKED CON CACHE")
    print("=" * 50)
    
    engine = ChunkedAnalysisEngine(project_root)
    
    # Configuración optimizada
    results = engine.analyze_project_chunked(
        chunk_size=30,           # 30 archivos por chunk
        max_workers=4,           # 4 workers paralelos
        enable_parallel=True     # Habilitar paralelización
    )
    
    # Mostrar resumen
    print(f"\n📊 RESUMEN COMPLETO DEL PROYECTO:")
    print(f"✅ Chunks procesados: {results['successful_chunks']}/{results['total_chunks']}")
    print(f"📁 Archivos analizados: {sum(cat['files'] for cat in results['categories'].values())}")
    print(f"🔧 Funciones encontradas: {sum(cat['functions'] for cat in results['categories'].values())}")
    print(f"🔄 Duplicados encontrados: {sum(cat['duplicates'] for cat in results['categories'].values())}")
    print(f"🌐 Duplicados cross-chunk: {len(results['cross_chunk_duplicates'])}")
    
    print(f"\n📈 Por categoría:")
    for category, stats in results['categories'].items():
        print(f"   {category}: {stats['files']} archivos, {stats['functions']} funciones, {stats['duplicates']} duplicados")
    
    # Guardar resultados completos
    output_file = project_root / "tools" / "chunked_analysis_complete.json"
    
    # Preparar datos serializables
    serializable_results = dict(results)
    serializable_results['categories'] = dict(results['categories'])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n💾 Resultados completos guardados en: {output_file}")
    
    return results

if __name__ == "__main__":
    main()