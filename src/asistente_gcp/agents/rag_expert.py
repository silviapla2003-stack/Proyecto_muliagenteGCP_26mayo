"""Sub-agente Experto RAG respaldado por el índice FAISS de LlamaIndex."""

import os
from pathlib import Path
from google.adk import Agent
from google.adk.tools.retrieval import LlamaIndexRetrieval
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.vector_stores.faiss import FaissVectorStore

from asistente_gcp.utils.model_config import get_model, get_embedding_model

# Rutas de almacenamiento
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STORAGE_DIR = PROJECT_ROOT / "data" / "storage"

def _load_retriever():
    storage_dir = Path(os.getenv("LOCAL_RAG_STORAGE_DIR", str(DEFAULT_STORAGE_DIR)))
    
    if not storage_dir.exists() or not (storage_dir / "default__vector_store.json").exists():
        print(f"\n[!] ADVERTENCIA: Índice FAISS no encontrado en '{storage_dir}'.")
        print("Por favor, indexa primero tus apuntes ejecutando: uv run notebooks/indexar_apuntes.py")
        return None

    embed_model = get_embedding_model()
    vector_store = FaissVectorStore.from_persist_dir(str(storage_dir))
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        persist_dir=str(storage_dir),
    )
    index = load_index_from_storage(
        storage_context=storage_context,
        embed_model=embed_model,
    )
    return index.as_retriever(similarity_top_k=3)

# Cargar retriever
retriever = _load_retriever()

tools = []
if retriever:
    local_knowledge_tool = LlamaIndexRetrieval(
        name="consultar_apuntes_gcp",
        description=(
            "Recupera fragmentos relevantes de los apuntes oficiales de Google Cloud para "
            "responder preguntas conceptuales y teóricas."
        ),
        retriever=retriever,
    )
    tools.append(local_knowledge_tool)
else:
    # Si no hay índice, creamos una función mock para evitar romper la carga
    def consultar_apuntes_gcp(query: str) -> str:
        """Consulta los apuntes de GCP."""
        return "El índice FAISS no está inicializado todavía. Por favor indexa los apuntes primero."
    tools.append(consultar_apuntes_gcp)

rag_expert_agent = Agent(
    model=get_model(),
    name="rag_expert_agent",
    description=(
        "Sub-agente experto en Google Cloud. Responde dudas conceptuales sólidas y genera "
        "resúmenes técnicos basados directamente en los apuntes indexados."
    ),
    instruction=(
        "Eres un arquitecto experto de Google Cloud y tutor de certificación.\n"
        "Tu única tarea es responder preguntas conceptuales y redactar resúmenes teóricos.\n"
        "1. Llama SIEMPRE a 'consultar_apuntes_gcp' antes de responder cualquier pregunta teórica.\n"
        "2. Responde basándote estrictamente en el contexto recuperado. No inventes datos.\n"
        "3. Si los apuntes no contienen información suficiente sobre el tema consultado, infórmalo educadamente "
        "pero aporta tu conocimiento aclarando que no procede del material oficial.\n"
        "4. Cuando generes un resumen, estructúralo de forma limpia usando Markdown (título, conceptos clave, tablas comparativas)."
    ),
    tools=tools,
)
