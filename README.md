# 🏛️ Asistente de Estudio y Certificación de Google Cloud (Multi-Agent System)

Este proyecto es una solución de **Sistema Multiagente** diseñada con el **Google ADK** (Agent Development Kit), gestionada con **uv** y fundamentada en datos mediante un pipeline de **RAG local (LlamaIndex + FAISS)**. 

La solución está completamente optimizada para conectarse a **Vertex AI en Google Cloud (GCP)** a través de tu cuenta de facturación y credenciales predeterminadas (ADC), eliminando las limitaciones de cuotas de las claves de API de AI Studio.

---

## 📘 Documentación Oficial del Proyecto

> [!IMPORTANT]
> Toda la justificación teórica, el desglose arquitectónico minucioso, el análisis de componentes, el marco de pruebas y **las capturas de conversaciones reales en producción** se encuentran completamente documentadas y detalladas en el archivo:
> 🔗 **[Informe.md](file:///c:/Users/JOSE/Desktop/App%20conchita/Proyecto_mulagenteGCP/Informe.md)**

---

## 🛠️ Guía de Configuración y Despliegue Local (Arranque Rápido)

Sigue estos pasos para levantar e interactuar con el proyecto en tu máquina en menos de 5 minutos:

### 1. Requisitos e Instalación
Asegúrate de contar con Python `>=3.10` y `uv` instalado. Ejecuta el comando de sincronización de dependencias para crear y configurar el entorno virtual:
```bash
uv sync
```

### 2. Configurar Autenticación con Google Cloud (Vertex AI)
Para facturar el consumo de inferencia y embeddings a tu cuenta de Google Cloud (GCP) utilizando las credenciales predeterminadas de tu terminal:
```bash
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com
```

### 3. Configurar tu Archivo `.env`
Crea tu archivo `.env` en la raíz a partir de la plantilla y configúrala de la siguiente manera:
```env
MODEL_PROVIDER=vertex
GOOGLE_CLOUD_PROJECT=project3grupo2
GOOGLE_CLOUD_LOCATION=us-central1
STUDY_DIR=./data/studio_notes
```

### 4. Cargar e Indexar tus PDFs de Apuntes
1. **Borra** cualquier archivo de prueba en `data/apuntes/`.
2. **Pega tus apuntes reales** de Google Cloud en formato PDF dentro del directorio `data/apuntes/`.
3. Ejecuta el script indexador en tu consola:
   ```bash
   uv run notebooks/indexar_apuntes.py
   ```
   *Este script utilizará el modelo `text-embedding-004` de Vertex AI para vectorizar tus PDFs y guardará la base de datos FAISS en `data/storage/`.*

---

## 🚀 Cómo Iniciar los Servicios de la Aplicación

Para iniciar tu ecosistema multiagente, requerirás abrir dos terminales:

### Paso A: Arrancar el Servidor MCP (Terminal 1)
Inicia el microservicio de persistencia en disco:
```bash
uv run python src/asistente_gcp/mcp_server/server.py
```
*(Se mantendrá a la escucha en http://127.0.0.1:9002/sse)*

### Paso B: Lanzar la Interfaz Gráfica ADK Web (Terminal 2)
Arranca el portal web interactivo para comunicarte con tus agentes:
```bash
uv run adk web src/asistente_gcp
```
Una vez iniciado, abre tu navegador y dirígete a:
👉 **[http://localhost:8000](http://localhost:8000)** (selecciona el agente **`supervisor_agent`** en el selector superior izquierdo).