import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Asegurar que las variables de entorno cruciales estén disponibles
if not os.getenv("GEMINI_API_KEY"):
    print("WARNING: GEMINI_API_KEY no encontrada en las variables de entorno.")
    print("Por favor, asegúrate de configurar tu archivo .env antes de ejecutar.")

# Agregar el directorio raíz al path de Python por si acaso
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Crear directorios necesarios para el proyecto
apuntes_dir = root_dir / "data" / "apuntes"
storage_dir = root_dir / "data" / "storage"
apuntes_dir.mkdir(parents=True, exist_ok=True)
storage_dir.mkdir(parents=True, exist_ok=True)

print(f"Directorios de datos creados/verificados en:")
print(f" - Apuntes: {apuntes_dir}")
print(f" - Almacenamiento RAG: {storage_dir}")

# Importaciones de LlamaIndex
try:
    from llama_index.core import (
        SimpleDirectoryReader,
        VectorStoreIndex,
        StorageContext,
        Settings
    )
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
    import faiss
    from llama_index.vector_stores.faiss import FaissVectorStore
    from asistente_gcp.utils.model_config import get_embedding_model
except ImportError as e:
    print("\nError al importar dependencias de LlamaIndex/FAISS.")
    print("Asegúrate de ejecutar primero: uv sync")
    print(f"Detalle del error: {e}")
    sys.exit(1)


def indexar_documentos():
    """
    Lee los PDFs de data/apuntes, realiza el chunking,
    genera los embeddings con Gemini y crea el índice FAISS persistente.
    """
    # 1. Configurar Modelos en LlamaIndex Settings
    print("Configurando el modelo de Embeddings...")
    embed_model = get_embedding_model()
    Settings.embed_model = embed_model
    # Desactivamos el LLM por defecto en Settings para la indexación pura
    Settings.llm = None

    # 2. Cargar documentos PDF
    print(f"Cargando PDFs desde: {apuntes_dir}...")
    reader = SimpleDirectoryReader(
        input_dir=str(apuntes_dir),
        required_exts=[".pdf"],
        recursive=True
    )
    documents = reader.load_data()

    if not documents:
        print("\n[!] No se encontraron archivos PDF en el directorio 'data/apuntes/'.")
        print("Por favor, copia tus apuntes en formato PDF a esa carpeta y vuelve a ejecutar este script.")
        return

    # Limitar para propósitos de prueba rápida y evitar saturación de API
    documents = documents[:15]
    print(f"Cargados con éxito {len(documents)} páginas/documentos (limitado a las primeras 15 para pruebas rápidas).")


    # 3. Definir estrategia de Chunking para material técnico
    # Usamos chunks de 1024 caracteres con un overlap de 200 para mantener el contexto
    print("Aplicando segmentación de texto (Chunking)...")
    node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
    nodes = node_parser.get_nodes_from_documents(documents)
    print(f"Creados {len(nodes)} nodos de conocimiento a partir de los documentos.")

    # 4. Inicializar FAISS Vector Store
    # Usamos 768 dimensiones que es la dimensión por defecto de text-embedding-004
    dimension = 768
    faiss_index = faiss.IndexFlatL2(dimension)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 5. Indexar y Persistir
    print("Generando embeddings e indexando en FAISS local (esto puede tomar unos momentos)...")
    index = VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        show_progress=True
    )

    print(f"Guardando índice persistente en: {storage_dir}...")
    index.storage_context.persist(persist_dir=str(storage_dir))
    print("\n[OK] ¡Indexacion completada con exito!")
    print(f"El índice FAISS está listo para ser utilizado por el Sub-agente Experto RAG.")


if __name__ == "__main__":
    indexar_documentos()
