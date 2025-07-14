#!/usr/bin/env python3
"""
Asistente interactivo de código usando RAG local.
Interfaz de línea de comandos para hacer preguntas sobre el codebase.
"""
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from code_rag_system import CodeRAGSystem
    HAS_RAG = True
except ImportError:
    HAS_RAG = False

class CodeAssistant:
    """Asistente interactivo para consultas sobre código."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.rag_system = None
        self.session_questions = 0
        
    def initialize(self, force_rebuild: bool = False):
        """Inicializar sistema RAG."""
        if not HAS_RAG:
            print("❌ Sistema RAG no disponible.")
            print("💡 Instalar dependencias: pip install sentence-transformers numpy faiss-cpu")
            return False
        
        print("🤖 ASISTENTE DE CÓDIGO - RAG LOCAL")
        print("=" * 50)
        
        try:
            self.rag_system = CodeRAGSystem(self.project_root)
            
            print("📚 Inicializando índice de código...")
            start_time = time.time()
            self.rag_system.index_codebase(force_rebuild=force_rebuild)
            elapsed = time.time() - start_time
            
            print(f"✅ Sistema listo en {elapsed:.2f}s")
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando: {e}")
            return False
    
    def interactive_session(self):
        """Sesión interactiva de preguntas."""
        print("\n💬 SESIÓN INTERACTIVA")
        print("=" * 30)
        print("Haz preguntas sobre el código. Comandos especiales:")
        print("  - 'exit' o 'quit': Salir")
        print("  - 'rebuild': Reconstruir índice")
        print("  - 'stats': Estadísticas del sistema")
        print("  - 'help': Mostrar ayuda")
        print()
        
        while True:
            try:
                # Prompt
                question = input(f"[{self.session_questions + 1}] 🔍 Tu pregunta: ").strip()
                
                if not question:
                    continue
                
                # Comandos especiales
                if question.lower() in ['exit', 'quit', 'salir']:
                    print("👋 ¡Hasta luego!")
                    break
                elif question.lower() == 'rebuild':
                    self._rebuild_index()
                    continue
                elif question.lower() == 'stats':
                    self._show_stats()
                    continue
                elif question.lower() == 'help':
                    self._show_help()
                    continue
                
                # Procesar pregunta
                self._process_question(question)
                self.session_questions += 1
                
            except KeyboardInterrupt:
                print("\n👋 Sesión interrumpida")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _process_question(self, question: str):
        """Procesar una pregunta."""
        print(f"\n🔍 Buscando: '{question}'")
        
        start_time = time.time()
        result = self.rag_system.ask_question(question)
        elapsed = time.time() - start_time
        
        # Mostrar respuesta
        print(f"\n💬 Respuesta:")
        print("-" * 40)
        print(result['answer'])
        
        # Mostrar fuentes si hay
        if result['sources']:
            print(f"\n📚 Fuentes encontradas ({len(result['sources'])}):")
            for i, source in enumerate(result['sources'][:5], 1):
                confidence_bar = "🟢" if source['score'] > 0.7 else "🟡" if source['score'] > 0.4 else "🔴"
                print(f"  {i}. {confidence_bar} {source['type']}: `{source['name']}`")
                print(f"     📂 {source['file']} (líneas {source['lines']})")
                print(f"     🎯 Relevancia: {source['score']:.2f}")
        
        # Mostrar métricas
        print(f"\n📊 Métricas:")
        print(f"   ⏱️ Tiempo: {elapsed:.3f}s")
        print(f"   🎯 Confianza: {result['confidence']:.2f}")
        print(f"   📝 Contexto: {result['context_length']} caracteres")
        print()
    
    def _rebuild_index(self):
        """Reconstruir índice."""
        print("\n🔄 Reconstruyendo índice...")
        self.rag_system.index_codebase(force_rebuild=True)
        print("✅ Índice reconstruido")
    
    def _show_stats(self):
        """Mostrar estadísticas del sistema."""
        if not self.rag_system or not self.rag_system.chunks:
            print("❌ Sistema no inicializado")
            return
        
        chunks = self.rag_system.chunks
        
        # Estadísticas por tipo
        type_counts = {}
        file_counts = {}
        complexity_total = 0
        
        for chunk in chunks:
            type_counts[chunk.chunk_type] = type_counts.get(chunk.chunk_type, 0) + 1
            file_counts[chunk.file_path] = file_counts.get(chunk.file_path, 0) + 1
            complexity_total += chunk.complexity
        
        print(f"\n📊 ESTADÍSTICAS DEL SISTEMA")
        print("=" * 40)
        print(f"📁 Archivos indexados: {len(file_counts)}")
        print(f"🧩 Chunks totales: {len(chunks)}")
        print(f"📈 Complejidad promedio: {complexity_total / len(chunks):.1f}")
        
        print(f"\n🔧 Distribución por tipo:")
        for chunk_type, count in sorted(type_counts.items()):
            percentage = (count / len(chunks)) * 100
            print(f"   {chunk_type}: {count} ({percentage:.1f}%)")
        
        print(f"\n📂 Top archivos:")
        sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
        for file_path, count in sorted_files[:5]:
            file_name = Path(file_path).name
            print(f"   {file_name}: {count} chunks")
        
        print(f"\n🎯 Preguntas en esta sesión: {self.session_questions}")
    
    def _show_help(self):
        """Mostrar ayuda."""
        print(f"\n💡 AYUDA DEL ASISTENTE")
        print("=" * 30)
        print("Ejemplos de preguntas:")
        print("  • ¿Qué hace la función extract_property_data?")
        print("  • ¿Cómo funciona el scraper profesional?")
        print("  • ¿Dónde está implementado el sistema RAG?")
        print("  • ¿Cuántas clases hay en el proyecto?")
        print("  • ¿Qué archivos manejan la base de datos vectorial?")
        print("  • ¿Cómo se conecta el API con el scraper?")
        
        print(f"\nComandos especiales:")
        print("  • 'stats' - Ver estadísticas del sistema")
        print("  • 'rebuild' - Reconstruir índice de código")
        print("  • 'help' - Mostrar esta ayuda")
        print("  • 'exit' - Salir del asistente")

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Asistente de código con RAG local")
    parser.add_argument("--rebuild", action="store_true", help="Reconstruir índice")
    parser.add_argument("--question", "-q", help="Hacer una pregunta directa")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    
    args = parser.parse_args()
    
    # Inicializar asistente
    project_root = Path(__file__).parent.parent
    assistant = CodeAssistant(project_root)
    
    if not assistant.initialize(force_rebuild=args.rebuild):
        return 1
    
    # Modo de operación
    if args.question:
        # Pregunta directa
        assistant._process_question(args.question)
    elif args.stats:
        # Solo estadísticas
        assistant._show_stats()
    else:
        # Modo interactivo
        assistant.interactive_session()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())