# Asistente de Estudio y Certificación de Google Cloud (Multi-Agent System)

Este proyecto es el trabajo final para el curso de sistemas multiagente. Se trata de un **Asistente de Estudio y Certificación de Google Cloud** inteligente y contextual, diseñado sobre el **Google ADK** (Agent Development Kit), utilizando **uv** como gestor de dependencias, **LlamaIndex con FAISS** local para el sistema RAG, y un **Servidor MCP propio** para exportar resúmenes y reportes de progreso.

---

## 🏛️ Arquitectura del Sistema

El sistema sigue un patrón de **Supervisor + Sub-agentes especializados**:

1. **Agente Supervisor (`supervisor_agent`)**: El punto de contacto con el usuario. Analiza la intención del usuario y delega las tareas al sub-agente adecuado o invoca herramientas locales.
2. **Sub-agente Experto RAG (`rag_expert_agent`)**: Especializado en responder dudas conceptuales y técnicas de Google Cloud. Utiliza **LlamaIndex** para consultar el índice de vectores local de **FAISS** con los apuntes en PDF indexados.
3. **Sub-agente Evaluador (`evaluator_agent`)**: Diseña preguntas de examen tipo test interactivas (con opciones A, B, C y D) para evaluar el conocimiento del usuario sobre un tema basándose en la información real de los apuntes.
4. **Servidor MCP Personalizado (`asistente-gcp-mcp-server`)**: Un servidor de protocolo de contexto de modelo (MCP) que expone la herramienta `exportar_resumen_y_progreso` para almacenar de forma estructurada en disco local resúmenes y reportes de fallos como archivos Markdown.

---

## 🛠️ Requisitos Previos

- **Python**: Versión `>=3.10`
- **uv**: Gestor de paquetes rápido de Python. Si no lo tienes instalado, ejecútalo en PowerShell/Consola:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Clave de API de Gemini**: Consigue una gratis en [Google AI Studio](https://aistudio.google.com/app/apikey).

---

## 🚀 Guía de Instalación y Arranque Rápido (Menos de 5 Minutos)

### 1. Clonar e Instalar Dependencias
Instala todas las dependencias requeridas (incluyendo las librerías ADK, LlamaIndex, FAISS, FastMCP):
```bash
uv sync
```

### 2. Configurar Variables de Entorno
Crea tu archivo de entorno local a partir de la plantilla y edítalo para introducir tu `GEMINI_API_KEY`:
```bash
cp .env.example .env
```
*(Abre el archivo `.env` y sustituye `tu_gemini_api_key_aqui` por tu clave de API de Gemini real)*.

### 3. Indexar tus Apuntes (RAG local)
1. Coloca tus apuntes en formato **PDF** dentro del directorio recién creado: `data/apuntes/`.
2. Ejecuta el pipeline de indexación para generar los embeddings vectoriales con Gemini y estructurar el índice FAISS:
   ```bash
   uv run notebooks/indexar_apuntes.py
   ```
   *(El índice vectorial generado se guardará de forma persistente en `data/storage/`)*.

### 4. Iniciar el Servidor MCP Local
En una ventana de terminal independiente, arranca el servidor MCP local:
```bash
uv run python src/asistente_gcp/mcp_server/server.py
```
*(El servidor se iniciará en `http://127.0.0.1:9002/sse`)*.

### 5. Iniciar la Interfaz Web del Agente (Google ADK Web UI)
En tu terminal principal, arranca la interfaz gráfica interactiva del Google ADK:
```bash
uv run adk web src/asistente_gcp
```
¡Listo! Abre en tu navegador [http://localhost:8000](http://localhost:8000), selecciona el agente **`supervisor_agent`** y comienza a estudiar.

---

## 📝 Ejemplos de Interacciones a Probar
- **Pregunta teórica**: *"¿Qué diferencia hay entre Cloud Spanner y Cloud SQL según mis apuntes?"* (El supervisor llamará al Experto RAG).
- **Auto-evaluación**: *"Hazme un test tipo examen sobre IAM en Google Cloud"* (El supervisor llamará al Evaluador).
- **Exportar información**: *"Genera un resumen sobre los servicios de almacenamiento de GCP y expórtalo como nota"* (El supervisor llamará al Experto RAG y luego guardará el resultado mediante la herramienta del servidor MCP en `data/studio_notes/resumenes/`).