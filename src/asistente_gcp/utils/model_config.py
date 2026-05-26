"""Configuración y carga de modelos de lenguaje y embeddings."""

import os
from google.adk.models.lite_llm import LiteLlm
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

def get_model():
    """Retorna el modelo configurado basado en las variables de entorno."""
    provider = os.getenv("MODEL_PROVIDER", "gemini").lower()
    
    # Asegurar que la clave API esté mapeada si solo está GOOGLE_API_KEY
    if not os.getenv("GEMINI_API_KEY") and os.getenv("GOOGLE_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

    if provider == "vertex":
        # El ADK de Google utiliza la clase nativa Gemini si el modelo se pasa como una cadena plana.
        # Esto enruta automáticamente las peticiones a Vertex AI usando ADC (Application Default Credentials).
        os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
        # Aseguramos que el proyecto y localización estén en variables de entorno estándar
        if not os.getenv("GOOGLE_CLOUD_PROJECT"):
            os.environ["GOOGLE_CLOUD_PROJECT"] = "project3grupo2"
        if not os.getenv("GOOGLE_CLOUD_LOCATION"):
            os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
        return os.getenv("VERTEX_MODEL", "gemini-2.5-flash")

    if provider == "gemini":
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        if not model_name.startswith("gemini/"):
            model_name = f"gemini/{model_name}"
        return LiteLlm(model=model_name)
    
    elif provider == "groq":
        return LiteLlm(model=os.getenv("GROQ_MODEL", "groq/qwen/qwen3-32b"))
        
    return LiteLlm(model="gemini/gemini-2.5-flash")

def get_embedding_model():
    """Retorna el modelo de embedding configurado para el proveedor actual (Gemini o Vertex AI)."""
    provider = os.getenv("MODEL_PROVIDER", "gemini").lower()
    model_name = os.getenv("LOCAL_RAG_EMBEDDING_MODEL", "text-embedding-004")

    if provider == "vertex":
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "").strip()
        if not project or not location:
            raise RuntimeError(
                "Los embeddings de Vertex requieren las variables de entorno "
                "GOOGLE_CLOUD_PROJECT y GOOGLE_CLOUD_LOCATION."
            )

        os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
        return GoogleGenAIEmbedding(
            model_name=model_name,
            vertexai_config={"project": project, "location": location},
        )

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Los embeddings de Gemini API requieren GEMINI_API_KEY o GOOGLE_API_KEY. "
            "Para usar Vertex AI (Google Cloud), configura MODEL_PROVIDER=vertex "
            "y define GOOGLE_CLOUD_PROJECT junto con GOOGLE_CLOUD_LOCATION."
        )
    
    return GoogleGenAIEmbedding(
        model_name=model_name,
        api_key=api_key
    )



