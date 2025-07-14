#!/usr/bin/env python3
"""
Sistema RAG local para análisis inteligente de código.
Usa embeddings locales (Qwen3) + FAISS para responder preguntas sobre el codebase.
"""
import os
import sys
import json
import ast
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib

try:
    import numpy as np
    import faiss
    from sentence_transformers import SentenceTransformer
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False

@dataclass
class CodeChunk:
    """Chunk de código con metadatos."""
    id: str
    content: str
    file_path: str
    chunk_type: str  # 'function', 'class', 'import', 'comment', 'global'
    name: str
    line_start: int
    line_end: int
    complexity: int
    dependencies: List[str]
    docstring: Optional[str] = None

class CodeAnalyzer:
    """Analizador de código Python para extraer chunks semánticos."""
    
    def __init__(self):
        self.chunks = []
        
    def analyze_file(self, file_path: Path) -> List[CodeChunk]:
        """Analizar archivo Python y extraer chunks."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            lines = content.splitlines()
            
            chunks = []
            
            # Extraer imports
            chunks.extend(self._extract_imports(tree, lines, file_path))
            
            # Extraer funciones
            chunks.extend(self._extract_functions(tree, lines, file_path))
            
            # Extraer clases
            chunks.extend(self._extract_classes(tree, lines, file_path))
            
            # Extraer comentarios y docstrings importantes
            chunks.extend(self._extract_comments(content, lines, file_path))
            
            return chunks
            
        except Exception as e:
            print(f"⚠️ Error analizando {file_path}: {e}")
            return []
    
    def _extract_imports(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeChunk]:
        """Extraer imports y from statements."""
        chunks = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                line_start = node.lineno
                line_end = node.end_lineno or line_start
                
                # Extraer contenido del import
                import_lines = lines[line_start-1:line_end]
                content = '\n'.join(import_lines)
                
                # Identificar dependencias
                deps = []
                if isinstance(node, ast.Import):
                    deps = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    deps = [f"{module}.{alias.name}" for alias in node.names]
                
                chunk_id = self._generate_id(file_path, "import", line_start)
                
                chunks.append(CodeChunk(
                    id=chunk_id,
                    content=content,
                    file_path=str(file_path),
                    chunk_type="import",
                    name=f"import_{line_start}",
                    line_start=line_start,
                    line_end=line_end,
                    complexity=1,
                    dependencies=deps
                ))
        
        return chunks
    
    def _extract_functions(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeChunk]:
        """Extraer definiciones de funciones."""
        chunks = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                line_start = node.lineno
                line_end = node.end_lineno or line_start + 10
                
                # Extraer contenido completo de la función
                func_lines = lines[line_start-1:line_end]
                content = '\n'.join(func_lines)
                
                # Calcular complejidad ciclomática básica
                complexity = self._calculate_complexity(node)
                
                # Extraer dependencias (llamadas a funciones)
                dependencies = self._extract_function_calls(node)
                
                # Extraer docstring
                docstring = ast.get_docstring(node)
                
                chunk_id = self._generate_id(file_path, "function", node.name)
                
                chunks.append(CodeChunk(
                    id=chunk_id,
                    content=content,
                    file_path=str(file_path),
                    chunk_type="function",
                    name=node.name,
                    line_start=line_start,
                    line_end=line_end,
                    complexity=complexity,
                    dependencies=dependencies,
                    docstring=docstring
                ))
        
        return chunks
    
    def _extract_classes(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeChunk]:
        """Extraer definiciones de clases."""
        chunks = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                line_start = node.lineno
                line_end = node.end_lineno or line_start + 20
                
                # Extraer contenido de la clase
                class_lines = lines[line_start-1:line_end]
                content = '\n'.join(class_lines)
                
                # Extraer métodos
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                
                # Extraer herencia
                bases = [ast.unparse(base) if hasattr(ast, 'unparse') else str(base) 
                        for base in node.bases]
                
                # Extraer docstring
                docstring = ast.get_docstring(node)
                
                chunk_id = self._generate_id(file_path, "class", node.name)
                
                chunks.append(CodeChunk(
                    id=chunk_id,
                    content=content,
                    file_path=str(file_path),
                    chunk_type="class",
                    name=node.name,
                    line_start=line_start,
                    line_end=line_end,
                    complexity=len(methods),
                    dependencies=bases + methods,
                    docstring=docstring
                ))
        
        return chunks
    
    def _extract_comments(self, content: str, lines: List[str], file_path: Path) -> List[CodeChunk]:
        """Extraer comentarios importantes y docstrings."""
        chunks = []
        
        # Extraer comentarios multilinea importantes
        comment_blocks = []
        in_comment = False
        comment_start = 0
        comment_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detectar inicio de bloque de comentarios
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_comment:
                    in_comment = True
                    comment_start = i + 1
                    comment_lines = [line]
                else:
                    # Fin del comentario
                    comment_lines.append(line)
                    comment_content = '\n'.join(comment_lines)
                    
                    if len(comment_content) > 100:  # Solo comentarios largos
                        chunk_id = self._generate_id(file_path, "comment", comment_start)
                        
                        chunks.append(CodeChunk(
                            id=chunk_id,
                            content=comment_content,
                            file_path=str(file_path),
                            chunk_type="comment",
                            name=f"comment_{comment_start}",
                            line_start=comment_start,
                            line_end=i + 1,
                            complexity=1,
                            dependencies=[]
                        ))
                    
                    in_comment = False
                    comment_lines = []
            elif in_comment:
                comment_lines.append(line)
        
        return chunks
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calcular complejidad ciclomática simplificada."""
        from code_utils import calculate_complexity
        return calculate_complexity(node)
    
    def _extract_function_calls(self, node: ast.FunctionDef) -> List[str]:
        """Extraer llamadas a funciones dentro de una función."""
        calls = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        
        return list(set(calls))  # Remover duplicados
    
    def _generate_id(self, file_path: Path, chunk_type: str, identifier: Any) -> str:
        """Generar ID único para el chunk."""
        content = f"{file_path}::{chunk_type}::{identifier}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

class LocalEmbeddingModel:
    """Modelo de embeddings local usando llama.cpp o sentence-transformers."""
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path
        self.model = None
        self.embedding_dim = 384  # Dimensión por defecto
        
    def load_model(self):
        """Cargar modelo de embeddings."""
        if not HAS_DEPENDENCIES:
            raise ImportError("Instalar: pip install sentence-transformers numpy faiss-cpu")
        
        print("🤖 Cargando modelo de embeddings...")
        
        # Intentar usar modelo local si está disponible
        if self.model_path and self.model_path.exists():
            print(f"📂 Usando modelo local: {self.model_path}")
            # TODO: Implementar carga de modelo GGUF con llama-cpp-python
            # Por ahora usar sentence-transformers como fallback
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            print("📦 Usando modelo sentence-transformers...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Modelo cargado - Dimensión: {self.embedding_dim}")
    
    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """Generar embeddings para una lista de textos."""
        if self.model is None:
            self.load_model()
        
        return self.model.encode(texts, show_progress_bar=True)
    
    def encode_text(self, text: str) -> np.ndarray:
        """Generar embedding para un texto."""
        return self.encode_texts([text])[0]

class CodeRAGSystem:
    """Sistema RAG completo para análisis de código."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.analyzer = CodeAnalyzer()
        self.embedding_model = LocalEmbeddingModel(
            project_root / "ml-models" / "Qwen3-Embedding-8B-Q6_K.gguf"
        )
        
        # Directorios de datos
        self.data_dir = project_root / "tools" / "code_rag_data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.chunks_file = self.data_dir / "code_chunks.json"
        self.index_file = self.data_dir / "faiss_index.bin"
        self.metadata_file = self.data_dir / "metadata.json"
        
        # Datos en memoria
        self.chunks: List[CodeChunk] = []
        self.index: Optional[faiss.Index] = None
        self.chunk_texts: List[str] = []
        
    def index_codebase(self, force_rebuild: bool = False):
        """Indexar todo el codebase."""
        print("🔍 INDEXANDO CODEBASE PARA RAG")
        print("=" * 50)
        
        # Verificar si necesitamos reconstruir
        if not force_rebuild and self._is_index_current():
            print("📚 Cargando índice existente...")
            self._load_existing_index()
            return
        
        print("🚀 Construyendo nuevo índice...")
        
        # 1. Analizar archivos Python
        self._analyze_all_files()
        
        # 2. Generar embeddings
        self._generate_embeddings()
        
        # 3. Construir índice FAISS
        self._build_faiss_index()
        
        # 4. Guardar todo
        self._save_index()
        
        print(f"✅ Índice completo: {len(self.chunks)} chunks indexados")
    
    def _analyze_all_files(self):
        """Analizar todos los archivos Python del proyecto."""
        print("📁 Analizando archivos Python...")
        
        # Directorios a incluir
        include_dirs = ['src', 'tests', 'tools', 'scripts']
        exclude_dirs = {'env', '__pycache__', '.git', 'refactor_backup', 'code_rag_data'}
        
        all_chunks = []
        file_count = 0
        
        for include_dir in include_dirs:
            dir_path = self.project_root / include_dir
            if not dir_path.exists():
                continue
                
            for py_file in dir_path.rglob("*.py"):
                # Verificar exclusiones
                if any(excluded in py_file.parts for excluded in exclude_dirs):
                    continue
                
                print(f"   📄 {py_file.relative_to(self.project_root)}")
                chunks = self.analyzer.analyze_file(py_file)
                all_chunks.extend(chunks)
                file_count += 1
        
        self.chunks = all_chunks
        print(f"✅ {file_count} archivos analizados, {len(all_chunks)} chunks extraídos")
    
    def _generate_embeddings(self):
        """Generar embeddings para todos los chunks."""
        print("🧠 Generando embeddings...")
        
        # Preparar textos para embedding
        texts = []
        for chunk in self.chunks:
            # Combinar diferentes elementos del chunk
            text_parts = [chunk.content]
            
            if chunk.docstring:
                text_parts.append(f"Docstring: {chunk.docstring}")
            
            text_parts.append(f"Tipo: {chunk.chunk_type}")
            text_parts.append(f"Archivo: {chunk.file_path}")
            text_parts.append(f"Nombre: {chunk.name}")
            
            if chunk.dependencies:
                text_parts.append(f"Dependencias: {', '.join(chunk.dependencies)}")
            
            combined_text = '\n'.join(text_parts)
            texts.append(combined_text)
        
        self.chunk_texts = texts
        
        # Generar embeddings
        start_time = time.time()
        self.embeddings = self.embedding_model.encode_texts(texts)
        elapsed = time.time() - start_time
        
        print(f"✅ {len(texts)} embeddings generados en {elapsed:.2f}s")
    
    def _build_faiss_index(self):
        """Construir índice FAISS."""
        if not HAS_DEPENDENCIES:
            raise ImportError("Instalar: pip install faiss-cpu")
        
        print("🔗 Construyendo índice FAISS...")
        
        # Crear índice FAISS (Inner Product para similaridad coseno)
        embedding_dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(embedding_dim)
        
        # Normalizar embeddings para similaridad coseno
        faiss.normalize_L2(self.embeddings)
        
        # Agregar al índice
        self.index.add(self.embeddings.astype('float32'))
        
        print(f"✅ Índice FAISS creado con {self.index.ntotal} vectores")
    
    def _save_index(self):
        """Guardar índice y metadatos."""
        print("💾 Guardando índice...")
        
        # Guardar chunks
        chunks_data = []
        for chunk in self.chunks:
            chunks_data.append({
                'id': chunk.id,
                'content': chunk.content,
                'file_path': chunk.file_path,
                'chunk_type': chunk.chunk_type,
                'name': chunk.name,
                'line_start': chunk.line_start,
                'line_end': chunk.line_end,
                'complexity': chunk.complexity,
                'dependencies': chunk.dependencies,
                'docstring': chunk.docstring
            })
        
        with open(self.chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
        
        # Guardar índice FAISS
        faiss.write_index(self.index, str(self.index_file))
        
        # Guardar metadatos
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'total_chunks': len(self.chunks),
            'embedding_dim': self.embeddings.shape[1],
            'files_indexed': len(set(chunk.file_path for chunk in self.chunks))
        }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print("✅ Índice guardado")
    
    def _load_existing_index(self):
        """Cargar índice existente."""
        if not HAS_DEPENDENCIES:
            raise ImportError("Instalar: pip install faiss-cpu")
        
        # Cargar chunks
        with open(self.chunks_file, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        self.chunks = []
        for data in chunks_data:
            chunk = CodeChunk(
                id=data['id'],
                content=data['content'],
                file_path=data['file_path'],
                chunk_type=data['chunk_type'],
                name=data['name'],
                line_start=data['line_start'],
                line_end=data['line_end'],
                complexity=data['complexity'],
                dependencies=data['dependencies'],
                docstring=data.get('docstring')
            )
            self.chunks.append(chunk)
        
        # Cargar índice FAISS
        self.index = faiss.read_index(str(self.index_file))
        
        print(f"📚 Índice cargado: {len(self.chunks)} chunks")
    
    def _is_index_current(self) -> bool:
        """Verificar si el índice está actualizado."""
        if not all(f.exists() for f in [self.chunks_file, self.index_file, self.metadata_file]):
            return False
        
        # Verificar timestamp (reconstruir si es muy viejo)
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
        
        timestamp = datetime.fromisoformat(metadata['timestamp'])
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        
        return age_hours < 24  # Reconstruir si tiene más de 24 horas
    
    def search_code(self, query: str, k: int = 5) -> List[Tuple[CodeChunk, float]]:
        """Buscar código similar a la consulta."""
        if self.index is None:
            raise ValueError("Índice no cargado. Ejecutar index_codebase() primero.")
        
        # Generar embedding de la consulta
        query_embedding = self.embedding_model.encode_text(query)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Normalizar para similaridad coseno
        faiss.normalize_L2(query_embedding)
        
        # Buscar en el índice
        scores, indices = self.index.search(query_embedding, k)
        
        # Retornar resultados
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):
                results.append((self.chunks[idx], float(score)))
        
        return results
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Responder pregunta sobre el código con scoring mejorado."""
        print(f"❓ Pregunta: {question}")
        
        # Buscar chunks relevantes con más resultados
        results = self.search_code(question, k=15)
        
        if not results:
            return {
                'answer': "No encontré información relevante en el código.",
                'sources': [],
                'confidence': 0.0
            }
        
        # MEJORA 1: Re-scoring inteligente basado en tipo y relevancia
        enhanced_results = self._enhance_scoring(question, results)
        
        # MEJORA 2: Filtrar por relevancia mejorada y diversidad
        filtered_results = self._filter_and_diversify(enhanced_results)
        
        # Preparar contexto
        context_parts = []
        sources = []
        
        for chunk, score in filtered_results:
            context_parts.append(f"""
## {chunk.chunk_type.title()}: {chunk.name}
**Archivo:** {chunk.file_path} (líneas {chunk.line_start}-{chunk.line_end})
**Complejidad:** {chunk.complexity}

```python
{chunk.content}
```
""")
            sources.append({
                'file': chunk.file_path,
                'name': chunk.name,
                'type': chunk.chunk_type,
                'lines': f"{chunk.line_start}-{chunk.line_end}",
                'score': score
            })
        
        context = '\n'.join(context_parts)
        
        # Generar respuesta simple basada en contexto
        answer = self._generate_simple_answer(question, context, sources)
        
        return {
            'answer': answer,
            'sources': sources,
            'confidence': max(score for _, score in filtered_results) if filtered_results else 0.0,
            'context_length': len(context)
        }
    
    def _enhance_scoring(self, question: str, results: List[Tuple[CodeChunk, float]]) -> List[Tuple[CodeChunk, float]]:
        """Mejorar scoring basado en tipo de chunk y relevancia de contenido."""
        question_lower = question.lower()
        enhanced_results = []
        
        for chunk, base_score in results:
            # Calcular score mejorado
            enhanced_score = base_score
            
            # BOOST 1: Priorizar funciones sobre comentarios
            if chunk.chunk_type == 'function':
                enhanced_score *= 1.5  # +50% para funciones
            elif chunk.chunk_type == 'class':
                enhanced_score *= 1.3  # +30% para clases
            elif chunk.chunk_type == 'comment':
                enhanced_score *= 0.7  # -30% para comentarios generales
            
            # BOOST 2: Match exacto de nombres en la pregunta
            chunk_name_lower = chunk.name.lower()
            if any(word in chunk_name_lower for word in question_lower.split()):
                enhanced_score *= 1.4  # +40% para matches de nombre
            
            # BOOST 3: Match de palabras clave específicas en contenido
            content_lower = chunk.content.lower()
            for word in question_lower.split():
                if len(word) > 3 and word in content_lower:
                    # Más boost si la palabra aparece en el nombre de función
                    if word in chunk_name_lower:
                        enhanced_score *= 1.2
                    else:
                        enhanced_score *= 1.1
            
            # BOOST 4: Penalizar comentarios muy cortos o imports
            if chunk.chunk_type == 'comment' and len(chunk.content) < 50:
                enhanced_score *= 0.5
            elif chunk.chunk_type == 'import':
                enhanced_score *= 0.6
            
            # BOOST 5: Priorizar archivos específicos mencionados en la pregunta
            for word in question_lower.split():
                if word in chunk.file_path.lower():
                    enhanced_score *= 1.3
            
            enhanced_results.append((chunk, enhanced_score))
        
        # Ordenar por score mejorado
        enhanced_results.sort(key=lambda x: x[1], reverse=True)
        return enhanced_results
    
    def _filter_and_diversify(self, results: List[Tuple[CodeChunk, float]]) -> List[Tuple[CodeChunk, float]]:
        """Filtrar resultados y diversificar por tipos y archivos."""
        if not results:
            return []
        
        filtered = []
        seen_files = set()
        type_counts = {'function': 0, 'class': 0, 'comment': 0, 'import': 0}
        
        # Umbral dinámico basado en el mejor score
        best_score = results[0][1]
        min_threshold = max(0.4, best_score * 0.6)  # Al menos 60% del mejor score
        
        for chunk, score in results:
            # Filtro de threshold
            if score < min_threshold:
                continue
            
            # Diversificar tipos (limite por tipo)
            chunk_type = chunk.chunk_type
            if chunk_type == 'comment' and type_counts['comment'] >= 2:
                continue  # Máximo 2 comentarios
            if chunk_type == 'import' and type_counts['import'] >= 1:
                continue  # Máximo 1 import
            
            # Diversificar archivos (máximo 3 del mismo archivo)
            file_key = chunk.file_path.split('/')[-1]  # Solo nombre de archivo
            if file_key in seen_files:
                file_count = sum(1 for c, _ in filtered if c.file_path.split('/')[-1] == file_key)
                if file_count >= 3:
                    continue
            
            filtered.append((chunk, score))
            seen_files.add(file_key)
            type_counts[chunk_type] += 1
            
            # Límite total de resultados
            if len(filtered) >= 8:
                break
        
        return filtered
    
    def _generate_simple_answer(self, question: str, context: str, sources: List[Dict]) -> str:
        """Generar respuesta simple basada en el contexto."""
        # Análisis de patrones simples
        question_lower = question.lower()
        
        if not sources:
            return "No encontré información relevante en el código."
        
        # Tipos de preguntas
        if any(word in question_lower for word in ['qué hace', 'que hace', 'función', 'propósito']):
            return self._answer_what_does(sources, context)
        elif any(word in question_lower for word in ['cómo', 'como', 'implementa']):
            return self._answer_how(sources, context)
        elif any(word in question_lower for word in ['dónde', 'donde', 'ubicación']):
            return self._answer_where(sources)
        elif any(word in question_lower for word in ['cuántas', 'cuantas', 'cantidad']):
            return self._answer_count(sources)
        else:
            return self._answer_general(sources, context)
    
    def _answer_what_does(self, sources: List[Dict], context: str) -> str:
        """Responder qué hace algo."""
        if len(sources) == 1:
            source = sources[0]
            return f"La {source['type']} `{source['name']}` en `{source['file']}` (líneas {source['lines']}) es responsable de esta funcionalidad. Revisa el código para ver los detalles de implementación."
        else:
            names = [s['name'] for s in sources[:3]]
            return f"Encontré {len(sources)} elementos relacionados: {', '.join(names)}. Los principales están en los archivos mostrados en las fuentes."
    
    def _answer_how(self, sources: List[Dict], context: str) -> str:
        """Responder cómo funciona algo."""
        if sources:
            main_source = sources[0]
            return f"La implementación principal está en `{main_source['file']}` en la {main_source['type']} `{main_source['name']}`. Revisa el código para ver los detalles paso a paso."
        return "No encontré implementación específica."
    
    def _answer_where(self, sources: List[Dict]) -> str:
        """Responder dónde está algo."""
        if sources:
            locations = []
            for source in sources[:3]:
                locations.append(f"`{source['name']}` en `{source['file']}` (líneas {source['lines']})")
            return f"Ubicaciones encontradas:\n" + "\n".join(f"- {loc}" for loc in locations)
        return "No encontré la ubicación."
    
    def _answer_count(self, sources: List[Dict]) -> str:
        """Responder cantidades."""
        counts = {}
        for source in sources:
            type_name = source['type']
            counts[type_name] = counts.get(type_name, 0) + 1
        
        result = f"Encontré {len(sources)} elementos relacionados:\n"
        for type_name, count in counts.items():
            result += f"- {count} {type_name}(s)\n"
        
        return result
    
    def _answer_general(self, sources: List[Dict], context: str) -> str:
        """Respuesta general."""
        if sources:
            main_source = sources[0]
            return f"Información relevante encontrada en `{main_source['file']}` - {main_source['type']} `{main_source['name']}`. Revisa las fuentes para más detalles."
        return "No encontré información específica para tu consulta."

def main():
    """Función principal para testing."""
    if not HAS_DEPENDENCIES:
        print("❌ Dependencias faltantes:")
        print("   pip install sentence-transformers numpy faiss-cpu")
        return 1
    
    project_root = Path(__file__).parent.parent
    rag_system = CodeRAGSystem(project_root)
    
    print("🤖 SISTEMA RAG PARA ANÁLISIS DE CÓDIGO")
    print("=" * 50)
    
    # Indexar codebase
    rag_system.index_codebase()
    
    # Preguntas de ejemplo
    example_questions = [
        "¿Qué hace la función scrape?",
        "¿Cómo funciona el extractor de propiedades?",
        "¿Dónde está implementado el sistema RAG?",
        "¿Cuántas funciones de test hay?",
        "¿Qué archivos manejan el scraping?"
    ]
    
    print("\n🔍 PROBANDO CONSULTAS:")
    print("=" * 30)
    
    for question in example_questions:
        print(f"\n❓ {question}")
        result = rag_system.ask_question(question)
        print(f"💬 {result['answer']}")
        print(f"🎯 Confianza: {result['confidence']:.2f}")
        if result['sources']:
            print(f"📚 Fuentes: {len(result['sources'])} encontradas")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())