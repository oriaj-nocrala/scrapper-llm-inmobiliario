#!/usr/bin/env python3
"""
Debug para verificar exactamente de dónde vienen las URLs.
"""
import os
import sys
import time
from pathlib import Path

# Configuración
os.environ["USE_LOCAL_MODELS"] = "true"
os.environ["USE_GPU"] = "true"
os.environ["GPU_LAYERS"] = "25"

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_url_source():
    """Debug detallado del origen de las URLs."""
    try:
        from src.rag.property_rag_chain import create_rag_chain_from_scraped_data
        
        print("🔍 DEBUG: ¿DE DÓNDE VIENEN LAS URLs?")
        print("=" * 50)
        
        # 1. Verificar datos originales
        print("1️⃣ VERIFICANDO DATOS ORIGINALES:")
        import json
        with open("data/properties.json", "r") as f:
            data = json.load(f)
        
        sample_property = data["properties"][0]
        print(f"   Título: {sample_property['title']}")
        print(f"   URL en JSON: {sample_property['url']}")
        print()
        
        # 2. Inicializar RAG y verificar contexto
        print("2️⃣ INICIALIZANDO RAG...")
        rag_chain = create_rag_chain_from_scraped_data()
        
        # 3. Obtener documentos relevantes directamente
        print("3️⃣ OBTENIENDO DOCUMENTOS RELEVANTES:")
        relevant_docs = rag_chain.retriever.get_relevant_documents("departamento Independencia")
        
        print(f"   Documentos encontrados: {len(relevant_docs)}")
        if len(relevant_docs) > 0:
            doc = relevant_docs[0]
            print(f"   Metadata del primer doc:")
            print(f"     - Título: {doc.metadata.get('title', 'N/A')}")
            print(f"     - URL: {doc.metadata.get('url', 'N/A')}")
            print(f"     - Precio: {doc.metadata.get('price', 'N/A')}")
        print()
        
        # 4. Verificar cómo se formatea el contexto
        print("4️⃣ FORMATO DEL CONTEXTO:")
        
        # Usar la función format_docs internamente
        def format_docs_debug(docs):
            formatted_docs = []
            for i, doc in enumerate(docs[:1], 1):  # Solo el primero
                metadata = doc.metadata
                content = f"""
PROPIEDAD {i}:
- Título: {metadata.get('title', 'N/A')}
- Tipo: {metadata.get('property_type', 'N/A')}
- Ubicación: {metadata.get('location', 'N/A')}
- Precio: {metadata.get('price', 'N/A')}
- Precio UF: {metadata.get('price_uf', 'N/A')}
- Superficie: {metadata.get('area_m2', 'N/A')} m²
- Dormitorios: {metadata.get('bedrooms', 'N/A')}
- Baños: {metadata.get('bathrooms', 'N/A')}
- URL: {metadata.get('url', 'N/A')}
- Descripción: {doc.page_content}
"""
                formatted_docs.append(content)
            return "\\n".join(formatted_docs)
        
        context_text = format_docs_debug(relevant_docs)
        print("   CONTEXTO QUE VE EL MODELO:")
        print(context_text[:300] + "...")
        print()
        
        # 5. Ahora hacer la pregunta y ver el resultado
        print("5️⃣ PREGUNTA AL MODELO:")
        question = "Muestra 1 departamento"
        print(f"   Pregunta: {question}")
        
        start_time = time.time()
        answer = rag_chain.ask_question(question)
        response_time = time.time() - start_time
        
        print(f"   Respuesta del modelo:")
        print(f"   {answer.answer}")
        print()
        
        # 6. Análisis final
        print("6️⃣ ANÁLISIS:")
        if "https://" in answer.answer:
            print("   ✅ El modelo SÍ extrajo la URL del contexto")
            print("   🔍 El modelo copia la URL que está en los metadatos")
            print("   📋 Los metadatos vienen del JSON original scrapeado")
        else:
            print("   ❌ El modelo NO extrajo la URL")
        
        print(f"   ⏱️ Tiempo: {response_time:.1f}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING)
    debug_url_source()