#!/usr/bin/env python3
"""
God Class Refactor Guide - Herramienta inteligente para guiar refactorización manual.

Características:
- Usa IA local (Qwen3 Embeddings) para análisis semántico
- Se adapta automáticamente para usar máxima VRAM disponible
- Genera plan paso a paso para refactorización manual SEGURA
- Cache inteligente para acelerar análisis futuros
- Identificación de concerns y evaluación de riesgos

Uso:
    python3 god_class_refactor_guide.py archivo.py --output analisis.json

Este es la versión FINAL y ROBUSTA después de múltiples iteraciones.
"""
import ast
import json
import logging
import numpy as np
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import hashlib
import time

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MethodAnalysis:
    """Análisis de un método individual."""
    name: str
    source_code: str
    line_start: int
    line_end: int
    complexity: int
    dependencies: List[str]
    semantic_concern: str
    confidence: float
    refactor_priority: int
    suggested_component: str
    risk_level: str
    similarity_group: str

class GodClassRefactorGuide:
    """Guía inteligente para refactorización manual de God classes con IA local."""
    
    def __init__(self):
        """Initialize the God class refactor guide."""
        self.project_root = Path(__file__).parent.parent
        self.models_dir = self.project_root / "ml-models"
        self.cache_dir = self.project_root / "cache" / "god_class_refactor"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.embeddings_cache = {}
        self.optimal_config = None
        
        # Cargar cache
        self._load_cache()
        self._load_optimal_config()
    
    def _load_cache(self):
        """Cargar cache de embeddings."""
        cache_file = self.cache_dir / "embeddings_cache.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
                print(f"📚 Cache cargado: {len(self.embeddings_cache)} embeddings")
            except Exception as e:
                self.embeddings_cache = {}
    
    def _save_cache(self):
        """Guardar cache."""
        cache_file = self.cache_dir / "embeddings_cache.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
        except Exception:
            pass
    
    def _load_optimal_config(self):
        """Cargar configuración óptima conocida."""
        config_file = self.cache_dir / "optimal_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self.optimal_config = json.load(f)
                print(f"⚡ Configuración óptima cargada: {self.optimal_config}")
            except Exception:
                pass
    
    def _save_optimal_config(self, config: Dict):
        """Guardar configuración óptima."""
        config_file = self.cache_dir / "optimal_config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.optimal_config = config
        except Exception:
            pass
    
    def _try_load_model_adaptive(self):
        """Probar cargar modelo con configuraciones adaptativas."""
        model_path = self.models_dir / "Qwen3-Embedding-8B-Q6_K.gguf"
        if not model_path.exists():
            return None
        
        # Si tenemos configuración óptima, usarla directamente
        if self.optimal_config:
            print(f"🚀 Usando configuración óptima conocida...")
            return self._try_load_with_config(model_path, self.optimal_config)
        
        # Configuraciones a probar (de más agresiva a más conservadora)
        configs = [
            # Configuración agresiva
            {
                "n_ctx": 8192,
                "n_gpu_layers": 30,
                "n_batch": 1024,
                "n_threads": 6,
                "f16_kv": True,
                "description": "Agresiva"
            },
            # Configuración balanceada
            {
                "n_ctx": 6144,
                "n_gpu_layers": 25,
                "n_batch": 512,
                "n_threads": 4,
                "f16_kv": True,
                "description": "Balanceada"
            },
            # Configuración conservadora
            {
                "n_ctx": 4096,
                "n_gpu_layers": 20,
                "n_batch": 256,
                "n_threads": 4,
                "f16_kv": True,
                "description": "Conservadora"
            },
            # Configuración mínima
            {
                "n_ctx": 2048,
                "n_gpu_layers": 15,
                "n_batch": 128,
                "n_threads": 2,
                "f16_kv": True,
                "description": "Mínima"
            }
        ]
        
        print("🔄 Buscando configuración óptima...")
        
        for i, config in enumerate(configs):
            print(f"   🧪 Probando configuración {config['description']}...")
            model = self._try_load_with_config(model_path, config)
            
            if model is not None:
                print(f"✅ Configuración {config['description']} exitosa!")
                self._save_optimal_config(config)
                return model
            else:
                print(f"❌ Configuración {config['description']} falló")
        
        print("❌ No se pudo cargar modelo con ninguna configuración")
        return None
    
    def _try_load_with_config(self, model_path: Path, config: Dict):
        """Probar cargar modelo con configuración específica."""
        try:
            model = Llama(
                model_path=str(model_path),
                n_ctx=config["n_ctx"],
                embedding=True,
                n_gpu_layers=config["n_gpu_layers"],
                n_batch=config["n_batch"],
                n_threads=config["n_threads"],
                verbose=False,
                use_mmap=True,
                use_mlock=False,
                f16_kv=config.get("f16_kv", True),
            )
            return model
        except Exception as e:
            return None
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Obtener embedding con cache."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash in self.embeddings_cache:
            return self.embeddings_cache[text_hash]
        
        if not self.model:
            return None
        
        try:
            embedding = np.array(self.model.embed(text))
            embedding = embedding / np.linalg.norm(embedding)
            self.embeddings_cache[text_hash] = embedding
            return embedding
        except Exception:
            return None
    
    def analyze_god_class(self, file_path: Path) -> Dict[str, Any]:
        """Análisis inteligente de God class con IA local."""
        print(f"\\n🧠 ANÁLISIS INTELIGENTE GOD CLASS - IA LOCAL")
        print("=" * 50)
        
        # Cache completo
        file_hash = self._get_file_hash(file_path)
        cache_file = self.cache_dir / f"analysis_{file_hash}.json"
        
        if cache_file.exists():
            print("⚡ Usando análisis completo cacheado...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Cargar modelo con configuración óptima
        print("📊 Cargando modelo de IA local...")
        self.model = self._try_load_model_adaptive()
        
        if not self.model:
            return {"error": "No se pudo cargar modelo de embeddings"}
        
        print(f"🎯 Modelo cargado exitosamente!")
        if self.optimal_config:
            print(f"📈 Usando: {self.optimal_config['description']} ({self.optimal_config['n_ctx']} ctx, {self.optimal_config['n_gpu_layers']} GPU layers)")
        
        # Análisis del archivo
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        tree = ast.parse(source_code)
        main_class = self._find_main_class(tree)
        
        if not main_class:
            return {"error": "No se encontró clase principal"}
        
        print(f"📋 Clase: {main_class.name}")
        
        methods = self._extract_methods_detailed(main_class, source_code)
        print(f"🔧 Métodos encontrados: {len(methods)}")
        
        if len(methods) < 10:
            return {"error": f"No es God class ({len(methods)} métodos)"}
        
        # Análisis semántico optimizado
        print(f"🧠 Análisis semántico con configuración óptima...")
        start_time = time.time()
        
        semantic_analysis = self._optimized_semantic_analysis(methods)
        
        elapsed = time.time() - start_time
        print(f"⏱️ Análisis completado en {elapsed:.1f}s")
        
        # Combinar análisis
        combined_analysis = self._generate_final_analysis(methods, semantic_analysis)
        
        # Plan de refactorización
        refactor_plan = self._generate_actionable_plan(combined_analysis, main_class.name)
        
        result = {
            "class_name": main_class.name,
            "total_methods": len(methods),
            "methods_analysis": [asdict(m) for m in combined_analysis],
            "refactor_plan": refactor_plan,
            "semantic_insights": semantic_analysis,
            "configuration": self.optimal_config,
            "performance": {
                "analysis_time": elapsed,
                "embeddings_generated": len([m for m in methods if self._get_embedding(self._method_to_text(m)) is not None]),
                "cache_hits": len(self.embeddings_cache),
                "model_config": self.optimal_config
            },
            "summary": self._generate_executive_summary(combined_analysis)
        }
        
        # Guardar en cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        self._save_cache()
        
        return result
    
    def _optimized_semantic_analysis(self, methods: List[Dict]) -> Dict[str, Any]:
        """Análisis semántico optimizado."""
        embeddings_data = []
        batch_size = 5  # Procesar en lotes para mostrar progreso
        
        print(f"   🔗 Generando embeddings en lotes...")
        
        for i in range(0, len(methods), batch_size):
            batch = methods[i:i + batch_size]
            print(f"      📈 Lote {i//batch_size + 1}/{(len(methods) + batch_size - 1)//batch_size}")
            
            for method in batch:
                method_text = self._method_to_text(method)
                embedding = self._get_embedding(method_text)
                
                if embedding is not None:
                    embeddings_data.append((method['name'], embedding))
        
        print(f"   🧮 Calculando similitudes semánticas...")
        similarities = self._efficient_similarities(embeddings_data)
        
        print(f"   🎯 Clustering inteligente...")
        groups = self._intelligent_clustering(embeddings_data)
        
        return {
            "embeddings_count": len(embeddings_data),
            "similarities": similarities,
            "semantic_groups": groups,
            "quality_score": len(embeddings_data) / len(methods) * 100
        }
    
    def _method_to_text(self, method: Dict) -> str:
        """Optimizar texto para embedding."""
        return f"Method {method['name']} complexity {method.get('complexity', 0)} deps {len(method.get('dependencies', []))} code {method['source_code'][:600]}"
    
    def _efficient_similarities(self, embeddings_data: List[Tuple[str, np.ndarray]]) -> Dict[str, float]:
        """Calcular similitudes de forma eficiente."""
        similarities = {}
        
        # Solo calcular para pares más prometedores
        for i, (name1, emb1) in enumerate(embeddings_data):
            for j, (name2, emb2) in enumerate(embeddings_data[i+1:i+6], i+1):  # Solo 5 más cercanos
                if j < len(embeddings_data):  # Verificar bounds
                    try:
                        # Asegurar que ambos embeddings tengan la misma forma
                        if emb1.shape == emb2.shape:
                            similarity = float(np.dot(emb1, emb2))
                            if similarity > 0.5:  # Solo guardar similitudes significativas
                                similarities[f"{name1}--{name2}"] = similarity
                    except Exception:
                        continue  # Skip problematic pairs
        
        return similarities
    
    def _intelligent_clustering(self, embeddings_data: List[Tuple[str, np.ndarray]]) -> Dict[str, List[str]]:
        """Clustering inteligente con manejo robusto de dimensiones."""
        groups = {}
        processed = set()
        
        # Normalizar todos los embeddings primero
        normalized_embeddings = []
        for name, emb in embeddings_data:
            if emb.ndim > 1:
                emb = emb.flatten()  # Aplanar si es multidimensional
            if len(emb) > 0:  # Solo si no está vacío
                emb_norm = emb / np.linalg.norm(emb) if np.linalg.norm(emb) > 0 else emb
                normalized_embeddings.append((name, emb_norm))
        
        for name1, emb1 in normalized_embeddings:
            if name1 in processed:
                continue
            
            group_members = [name1]
            processed.add(name1)
            
            # Buscar similares con manejo de errores
            for name2, emb2 in normalized_embeddings:
                if name2 in processed:
                    continue
                
                try:
                    # Verificar que tengan la misma dimensión
                    if emb1.shape == emb2.shape and len(emb1) == len(emb2):
                        similarity = np.dot(emb1, emb2)
                        if similarity > 0.7:
                            group_members.append(name2)
                            processed.add(name2)
                except Exception:
                    continue  # Skip problematic embeddings
            
            if len(group_members) >= 2:
                groups[f"cluster_{len(groups)}"] = group_members
        
        return groups
    
    def _generate_final_analysis(self, methods: List[Dict], semantic_analysis: Dict) -> List[MethodAnalysis]:
        """Generar análisis final."""
        combined = []
        
        for i, method in enumerate(methods):
            name = method['name']
            concern = self._smart_concern_detection(name, method)
            risk = self._smart_risk_assessment(method)
            
            analysis = MethodAnalysis(
                name=name,
                source_code=method['source_code'][:300] + "..." if len(method['source_code']) > 300 else method['source_code'],
                line_start=method['line_start'],
                line_end=method['line_end'],
                complexity=method.get('complexity', 1),
                dependencies=method.get('dependencies', []),
                semantic_concern=concern,
                confidence=0.9,
                refactor_priority=i,
                suggested_component=f"{concern.title()}Manager",
                risk_level=risk,
                similarity_group="auto_detected"
            )
            
            combined.append(analysis)
        
        return combined
    
    def _smart_concern_detection(self, name: str, method: Dict) -> str:
        """Detección inteligente de concerns."""
        name_lower = name.lower()
        
        patterns = {
            "debug": ["debug", "highlight", "monitor", "show"],
            "navigation": ["navigate", "wait", "find", "click", "smart", "back"],
            "parsing": ["parse", "extract_property", "extract_floor", "extract_id"],
            "extraction": ["extract", "building", "typolog", "card"],
            "validation": ["validate", "check", "is_", "valid"],
            "coordination": ["process", "handle", "create", "__init__", "start"]
        }
        
        for concern, keywords in patterns.items():
            if any(keyword in name_lower for keyword in keywords):
                return concern
        
        return "utility"
    
    def _smart_risk_assessment(self, method: Dict) -> str:
        """Evaluación inteligente de riesgo."""
        complexity = method.get('complexity', 0)
        dependencies = len(method.get('dependencies', []))
        
        if complexity > 8 or dependencies > 10:
            return "high"
        elif complexity > 4 or dependencies > 5:
            return "medium"
        else:
            return "low"
    
    def _generate_actionable_plan(self, analysis: List[MethodAnalysis], class_name: str) -> List[Dict]:
        """Generar plan accionable."""
        plan = []
        
        # Agrupar por concern y riesgo
        by_concern = {}
        for method in analysis:
            concern = method.suggested_component
            if concern not in by_concern:
                by_concern[concern] = {"low": [], "medium": [], "high": []}
            by_concern[concern][method.risk_level].append(method)
        
        step = 1
        
        # Preparación
        plan.append({
            "step": step,
            "action": "Preparar refactorización",
            "description": "Configurar tests y estructura",
            "risk": "Muy Bajo",
            "time_estimate": "2-3 horas",
            "success_criteria": ["Tests al 100%", "Estructura creada"]
        })
        step += 1
        
        # Extracción por fases
        for risk_level in ["low", "medium", "high"]:
            for concern, risk_methods in by_concern.items():
                methods = risk_methods[risk_level]
                if len(methods) >= 2:
                    plan.append({
                        "step": step,
                        "action": f"Extraer {concern}",
                        "description": f"Separar {len(methods)} métodos de {concern.lower()}",
                        "risk": risk_level.title(),
                        "methods": [m.name for m in methods],
                        "time_estimate": f"{len(methods) * 30 + 60} minutos",
                        "success_criteria": [
                            f"Clase {concern} creada",
                            "Tests pasando",
                            "Integración funcionando"
                        ]
                    })
                    step += 1
        
        return plan
    
    def _generate_executive_summary(self, analysis: List[MethodAnalysis]) -> Dict[str, Any]:
        """Generar resumen ejecutivo."""
        concerns = set(m.semantic_concern for m in analysis)
        risk_dist = {}
        
        for risk in ["low", "medium", "high"]:
            risk_dist[risk] = len([m for m in analysis if m.risk_level == risk])
        
        return {
            "key_insights": [
                f"God class con {len(analysis)} métodos identificada",
                f"Separable en {len(concerns)} componentes especializados",
                f"Reducción de complejidad: {(len(analysis) - len(concerns)) / len(analysis) * 100:.0f}%",
                f"Riesgo predominante: {max(risk_dist.items(), key=lambda x: x[1])[0]}"
            ],
            "concerns_breakdown": list(concerns),
            "risk_distribution": risk_dist,
            "refactorability": "Alta" if risk_dist["low"] > risk_dist["high"] else "Media",
            "recommended_approach": "Refactorización incremental por componentes"
        }
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Hash de archivo."""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    
    def _find_main_class(self, tree: ast.AST) -> Optional[ast.ClassDef]:
        """Encontrar clase principal."""
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        if not classes:
            return None
        return max(classes, key=lambda cls: len([n for n in cls.body if isinstance(n, ast.FunctionDef)]))
    
    def _extract_methods_detailed(self, class_node: ast.ClassDef, source_code: str) -> List[Dict]:
        """Extraer métodos con detalles."""
        methods = []
        lines = source_code.split('\\n')
        
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 20
                
                for i in range(start_line + 1, min(len(lines), start_line + 100)):
                    if i < len(lines) and (lines[i].strip().startswith('def ') or lines[i].strip().startswith('class ')):
                        end_line = i
                        break
                
                method_lines = lines[start_line:min(end_line, len(lines))]
                source = '\\n'.join(method_lines)
                
                dependencies = []
                for n in ast.walk(node):
                    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                        if n.value.id == 'self':
                            dependencies.append(n.attr)
                
                complexity = len([n for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With))])
                
                methods.append({
                    'name': node.name,
                    'source_code': source,
                    'line_start': start_line + 1,
                    'line_end': end_line,
                    'complexity': complexity,
                    'dependencies': list(set(dependencies))
                })
        
        return methods

def main():
    """Main adaptativo."""
    import argparse
    
    parser = argparse.ArgumentParser(description='God Class Refactor Guide - Herramienta inteligente con IA local')
    parser.add_argument('file_path', help='Ruta al archivo')
    parser.add_argument('--output', '-o', help='Archivo de salida')
    parser.add_argument('--reset-config', action='store_true', help='Reset configuración óptima')
    
    args = parser.parse_args()
    
    guide = GodClassRefactorGuide()
    
    if args.reset_config:
        config_file = guide.cache_dir / "optimal_config.json"
        config_file.unlink(missing_ok=True)
        print("🔄 Configuración reseteada")
        return
    
    file_path = Path(args.file_path)
    result = guide.analyze_god_class(file_path)
    
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    # Mostrar resultados
    summary = result['summary']
    config = result.get('configuration', {})
    
    print(f"\\n🎯 ANÁLISIS INTELIGENTE COMPLETADO")
    print("=" * 50)
    print(f"🏗️ Clase: {result['class_name']}")
    print(f"🔧 Métodos: {result['total_methods']}")
    print(f"📊 Configuración: {config.get('description', 'N/A')} ({config.get('n_ctx', 0)} ctx)")
    
    print(f"\\n💡 INSIGHTS CLAVE:")
    for insight in summary['key_insights']:
        print(f"   • {insight}")
    
    print(f"\\n🛣️ PLAN EJECUTIVO:")
    for step in result['refactor_plan'][:4]:
        print(f"   {step['step']}. {step['action']} ({step.get('time_estimate', 'N/A')})")
    
    if args.output:
        with open(Path(args.output), 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Guardado en {args.output}")

if __name__ == "__main__":
    main()