# INFORME TÉCNICO Y ACADÉMICO

## Diseño e Implementación de un Sistema Multiagente de Inteligencia Artificial con Grounding y Herramientas MCP

---

**Asistente de Estudio y Certificación de Google Cloud con RAG local y Servidor MCP**

| Campo | Detalle |
|---|---|
| **Curso** | Sistemas Multiagente con Herramientas MCP y Grounding con Datos |
| **Fecha** | Mayo 2026 |
| **Autores** | David Fernández Andujar, Paola Reguera González, Silvia Plà Martínez y José Félix González. |
| **Institución** | EDEM Máster de IA |

---

## Índice

1. [Resumen Ejecutivo y Escenario del Negocio](#1-resumen-ejecutivo-y-escenario-del-negocio)
2. [Diagrama de Arquitectura Detallada](#2-diagrama-de-arquitectura-detallada)
3. [Desglose de Componentes de Software](#3-desglose-de-componentes-de-software)
4. [Marco Teórico del Pipeline de RAG e Indexación](#4-marco-teórico-del-pipeline-de-rag-e-indexación)
5. [Capturas de Conversaciones y Validación en Producción](#5-capturas-de-conversaciones-y-validación-en-producción)
6. [Plan de Pruebas y Validación Técnica](#6-plan-de-pruebas-y-validación-técnica)
7. [Limitaciones Detectadas y Trabajo Futuro](#7-limitaciones-detectadas-y-trabajo-futuro)

---

## 1. Resumen Ejecutivo y Escenario del Negocio

### 1.1 Introducción y Justificación

El ecosistema de computación en la nube de Google Cloud Platform (GCP) se compone de cientos de servicios complejos y en constante evolución (cómputo, almacenamiento, bases de datos orientadas a escala, mensajería, analítica y seguridad). La obtención de certificaciones oficiales de Google Cloud (tales como *Professional Cloud Architect*, *Professional Data Engineer* o *Associate Cloud Engineer*) requiere un profundo entendimiento de la teoría arquitectónica y una excelente capacidad para discernir soluciones óptimas en casos de estudio técnicos.

La metodología tradicional de estudio basada en la lectura lineal de diapositivas o manuales extensos presenta dos graves carencias:

1. **Carencia de interactividad**: El estudiante adopta un rol pasivo, lo que reduce drásticamente la retención a largo plazo.
2. **Falta de evaluación a medida**: Los bancos de preguntas fijos son limitados, repetitivos y no se adaptan a las debilidades conceptuales específicas del estudiante en tiempo real.

Para solventar estas limitaciones, se ha diseñado e implementado el **Asistente de Estudio y Certificación de Google Cloud**, un ecosistema de agentes inteligentes capaz de guiar al estudiante de manera interactiva. El sistema utiliza **LlamaIndex** y **FAISS** para fundamentar el conocimiento en los apuntes PDF del propio estudiante (eliminando alucinaciones) y cuenta con un **Servidor MCP independiente** que permite guardar de forma persistente y estructurada los resúmenes y registros de progreso en formato Markdown directamente en el disco duro local del usuario.

### 1.2 Justificación del Stack Tecnológico Elegido

| Tecnología | Justificación |
|---|---|
| **Google ADK** (Agent Development Kit) | Framework de orquestación de agentes. Flexibilidad en el paso de mensajes, robusta abstracción de herramientas (`AgentTool`, `McpToolset`) y soporte nativo para Vertex AI y LiteLLM. |
| **LlamaIndex & FAISS** | Pipeline RAG modular para parsing y chunking de PDFs técnicos. FAISS (`faiss-cpu`) provee base vectorial local en memoria ultrarrápida mediante distancias L2. |
| **FastMCP** (spec. Anthropic) | Implementación de servidor MCP en pocas líneas de Python. Expone funciones del sistema (escritura segura en disco) abstrayendo la complejidad del protocolo SSE. |
| **uv** (Astral) | Gestor de paquetes y dependencias en sustitución de `pip` y `virtualenv`. Instalaciones ultrarrápidas y reproducibles gracias al archivo `uv.lock`. |
| **Vertex AI** (Google Cloud) | Integración con modelos de lenguaje y embeddings de producción mediante Application Default Credentials (ADC), eliminando restricciones de cuota de AI Studio. |

---

## 2. Diagrama de Arquitectura Detallada

El siguiente diagrama detalla la arquitectura del sistema y el flujo exacto de la información desde que el usuario realiza una consulta hasta que se procesa a nivel conceptual, vectorial y físico:

```
👤 Usuario (Estudiante)
        |
        |  [1. Entrada en Lenguaje Natural]
        v
🖥️  Interfaz Web ADK  (localhost:8000)
        |
        |  [2. Sesión Activa / Eventos SSE]
        v
🤖 Agente Supervisor  (supervisor/agent.py)
        |                          |
[3a. Delegar Teoría]    [3b. Delegar Examen]
        |                          |
        v                          v
📚 Sub-Agente Experto RAG    📝 Sub-Agente Evaluador
   (rag_expert.py)               (evaluator.py)
        |                          |
        |  [4. Query Semántica]     |
        v                          v
       🗄️  Vector Store FAISS Local  (data/storage/)
                    |
        [5. Embeddings & Inferencia]
                    |
                    v
       ☁️  GCP Vertex AI
           text-embedding-004 / gemini-2.5-flash
                    |
        [6. Guardar resúmenes / progreso]
                    |
                    v
       🔌 Servidor MCP  (mcp_server/server.py)
                    |
        [7. Escritura Segura / Sanitización]
                    |
                    v
       📁 Disco local  (data/studio_notes/)
```

### 2.1 Flujo Operativo del Sistema (Paso a Paso)

1. **Entrada**: El estudiante ingresa una solicitud en la interfaz gráfica del Google ADK.
2. **Análisis Cognitivo**: El Agente Supervisor interpreta la consulta y planifica una ejecución secuencial si contiene peticiones mixtas.
3. **Búsqueda en RAG**: Se invoca al Experto RAG, pasándole la consulta técnica.
4. **Recuperación Vectorial**: El Experto RAG ejecuta `consultar_apuntes_gcp`, activando LlamaIndex para buscar los fragmentos con mayor similitud en FAISS.
5. **Generación con Vertex AI**: Vertex AI procesa el prompt enriquecido y genera el resumen técnico preciso.
6. **Llamada al Servidor MCP**: El Supervisor activa `exportar_resumen_y_progreso` del servidor MCP en segundo plano.
7. **Persistencia Física**: El Servidor MCP sanitiza el título y guarda un archivo `.md` en `data/studio_notes/resumenes/`, reportando la ruta de vuelta a la UI.

---

## 3. Desglose de Componentes de Software

### 3.1 Agente Supervisor (`supervisor_agent`)

- **Propósito**: Coordinar la navegación y distribución del trabajo en el sistema multiagente.
- **Localización**: `src/asistente_gcp/supervisor/agent.py`

#### Estrategia de Prompting

El *system instruction* define una personalidad de "Tutor Académico experto en Google Cloud" con las siguientes directrices de enrutamiento:

1. No responder preguntas técnicas directas; delegar siempre en `rag_expert_agent`.
2. No formular preguntas tipo test; delegar siempre en `evaluator_agent`.
3. Consumir `exportar_resumen_y_progreso` únicamente cuando el usuario exprese explícitamente el deseo de guardar, exportar o reportar información a disco.

#### Estructura de Datos

| Elemento | Descripción |
|---|---|
| **Inputs** | JSON con historial de conversación y mensaje actual |
| **Outputs** | Llamada de herramienta vía `AgentTool` (JSON con parámetros) o texto en lenguaje natural |

#### Modos de Fallo y Mitigación

| Modo de Fallo | Mitigación |
|---|---|
| Entrada mixta o ambigua (ej: *"Explícame IAM y hazme un examen"*) puede causar bucle o acción única. | Se instruye para actuar secuencialmente o solicitar confirmación de prioridad al estudiante. |

---

### 3.2 Sub-Agente Experto RAG (`rag_expert_agent`)

- **Propósito**: Responder consultas teóricas y conceptuales fundamentándose al 100% en los apuntes cargados en PDF.
- **Localización**: `src/asistente_gcp/agents/rag_expert.py`

#### Estrategia de Prompting

El *system instruction* define el rol de "Ingeniero Cloud Especialista en GCP". Se prohíbe de forma categórica inventar características o costes. Ante cualquier pregunta técnica, se obliga al agente a llamar primero a la herramienta `consultar_apuntes_gcp`.

#### Modos de Fallo y Mitigación

| Modo de Fallo | Mitigación |
|---|---|
| La base de datos FAISS local no está inicializada, o el PDF no contiene información del tema. | La herramienta atrapa la excepción y advierte al usuario en consola. El prompt instruye al agente a apoyarse en su conocimiento nativo, aclarando explícitamente que dicha información no proviene de los apuntes oficiales. |

---

### 3.3 Sub-Agente Evaluador (`evaluator_agent`)

- **Propósito**: Diseñar y corregir simulacros de examen realistas e interactivos.
- **Localización**: `src/asistente_gcp/agents/evaluator.py`

#### Estrategia de Prompting

El *system instruction* define el rol de "Diseñador de Exámenes de Certificación Oficial de GCP". Crea preguntas con dificultad idéntica al examen real, generando una pregunta a la vez para permitir una experiencia dinámica. Las opciones A, B, C y D se presentan sin revelar la solución hasta que el usuario responde en el siguiente turno.

#### Modos de Fallo y Mitigación

| Modo de Fallo | Mitigación |
|---|---|
| El agente lanza un test con las respuestas correctas ya visibles en el mismo mensaje. | Prompting estricto con estructura *One-Shot* para ocultar las explicaciones hasta que el usuario responde en el siguiente turno de conversación. |

---

### 3.4 Servidor MCP (`asistente-gcp-mcp-server`)

- **Propósito**: Exponer capacidades seguras de persistencia de archivos del sistema al ecosistema de agentes.
- **Localización**: `src/asistente_gcp/mcp_server/server.py`
- **Herramienta expuesta**: `exportar_resumen_y_progreso(titulo, contenido, tipo)`

#### Mecanismos de Seguridad

- Filtrado de caracteres maliciosos o inyecciones de ruta (como `../`), previniendo escrituras arbitrarias en el sistema de archivos (*Path Traversal*).
- Validación de que los tipos de archivos se limiten a carpetas autorizadas de notas de estudio.

---

## 4. Marco Teórico del Pipeline de RAG e Indexación

El diseño de un sistema RAG (*Retrieval-Augmented Generation*) robusto para documentación técnica de ingeniería cloud no puede limitarse a un procesamiento genérico de texto. El material técnico contiene configuraciones complejas, límites de cuota y nombres de servicios que no deben quedar fragmentados en diferentes chunks.

### 4.1 Estrategia de Segmentación y Análisis del Solapamiento (Chunking)

| Parámetro | Valor Configurado |
|---|---|
| **Tamaño del Chunk** | 1.024 caracteres |
| **Solapamiento (Overlap)** | 200 caracteres |

#### Justificación Técnica

Si se configura un tamaño de chunk demasiado pequeño (ej: 256 caracteres), se pierde la correlación semántica. La descripción del servicio *GCP Cloud Spanner* (que detalla consistencia transaccional y escalabilidad global) requiere varias frases para ser explicada completamente. Con un chunk de 1.024 caracteres, se garantiza que la explicación completa del servicio quepa de forma íntegra en un solo nodo.

El solapamiento de 200 caracteres asegura que si una tabla comparativa o un párrafo crítico queda justo en la frontera de separación entre dos nodos, dicha información aparezca al final de un nodo y al principio del siguiente. Esto previene que una búsqueda vectorial corte por la mitad una definición crítica, garantizando la continuidad de la información que recibe el LLM.

### 4.2 Generación de Embeddings e Indexación Vectorial

| Componente | Detalle Técnico |
|---|---|
| **Modelo de Representación** | `text-embedding-004` (Vertex AI) — vectores densos de **768 dimensiones** |
| **Base de Datos Vectorial** | FAISS (Facebook AI Similarity Search) |
| **Métrica de Distancia** | Distancia L2 (Euclídea): $D(u,v) = \sqrt{\sum_{i=1}^{n}(u_i - v_i)^2}$ |
| **Recuperación** | Top-k = 3 fragmentos con mayor similitud semántica |

Los fragmentos de texto más cercanos semánticamente a la consulta del usuario tendrán la distancia L2 más baja. LlamaIndex extrae los `top_k=3` fragmentos con mayor similitud y los inyecta en el prompt de Vertex AI como contexto seguro de verdad, eliminando el riesgo de alucinaciones.

---

## 5. Capturas de Conversaciones y Validación en Producción

### 5.1 Caso de Uso 1: Consulta Conceptual con RAG

> **[ INSERTAR CAPTURA DE PANTALLA — localhost:8000 ]**

*Análisis*: El usuario pregunta sobre un concepto técnico de sus apuntes. La traza muestra al Supervisor delegando en el Experto RAG, el cual ejecuta una consulta semántica sobre FAISS y devuelve una respuesta enriquecida sin inventar datos.

---

### 5.2 Caso de Uso 2: Examen Interactivo de Certificación

> **[ INSERTAR CAPTURA DE PANTALLA — localhost:8000 ]**

*Análisis*: El usuario solicita "Hazme un test". Se aprecia la delegación inmediata al sub-agente Evaluador, que diseña una pregunta con cuatro opciones (A, B, C, D) retando al estudiante antes de revelar la respuesta correcta.

---

### 5.3 Caso de Uso 3: Guardado a Disco vía Servidor MCP

> **[ INSERTAR CAPTURA DE PANTALLA — localhost:8000 ]**

*Análisis*: Se simula la orden de exportación física del resumen. El Agente Supervisor invoca `exportar_resumen_y_progreso`. La consola del servidor MCP registra la petición SSE y la UI reporta la ruta física del archivo `.md` generado en `data/studio_notes/resumenes/`.

---

### 5.4 Caso de Uso 4: Gestión de Consultas Fuera de Alcance

> **[ INSERTAR CAPTURA DE PANTALLA — localhost:8000 ]**

*Análisis*: Se introduce una consulta fuera de contexto (ej: *"¿Cómo cocinar una tortilla de patatas?"*). El Experto RAG o el Supervisor identifican que la pregunta no tiene relación con los apuntes técnicos y responden delimitando amablemente el alcance del asistente.

---

## 6. Plan de Pruebas y Validación Técnica

Para asegurar el correcto funcionamiento de toda la solución a nivel local e integración con el Cloud, se diseñó y ejecutó una suite de pruebas manuales y diagnósticos de consola.

### 6.1 Suite de Pruebas Ejecutadas

| # | Prueba | Comando | Resultado |
|---|---|---|---|
| 1 | Validación de Dependencias | `uv sync` | Resolución e instalación exitosa de 220 paquetes en 2,51 s. Entorno `.venv` limpio y libre de conflictos. |
| 2 | Validación del Pipeline RAG | `uv run notebooks/indexar_apuntes.py` | Indexación exitosa de los PDFs en `data/apuntes/`. Índice FAISS generado en `data/storage/` sin excepciones. Tiempo promedio: 4,5 s. |
| 3 | Conectividad con Vertex AI | `uv run python -c "from asistente_gcp.utils.model_config import get_embedding_model; get_embedding_model()"` | Verificación exitosa de autenticación ADC. Modelo `text-embedding-004` cargado en proyecto `project3grupo2`, región `us-central1`. |
| 4 | Prueba del Servidor MCP | `uv run python src/asistente_gcp/mcp_server/server.py` | Arranque exitoso del servidor HTTP SSE en el puerto `9002`, listo para recibir peticiones externas. |

```bash
# 1. Instalación de dependencias
uv sync

# 2. Indexación de apuntes PDF
uv run notebooks/indexar_apuntes.py

# 3. Verificación de conectividad con Vertex AI
uv run python -c "from asistente_gcp.utils.model_config import get_embedding_model; get_embedding_model()"

# 4. Arranque del Servidor MCP
uv run python src/asistente_gcp/mcp_server/server.py
```

---

## 7. Limitaciones Detectadas y Trabajo Futuro

### 7.1 Limitaciones Actuales del Sistema

| Limitación | Descripción |
|---|---|
| **Latencia del Ciclo de Ejecución (RTT)** | Las consultas pasan por una cadena secuencial (Supervisor → Sub-agente → RAG → Generación). El tiempo de respuesta se sitúa entre 3,5 y 5,5 segundos debido a los round-trips hacia la API de Vertex AI y el cálculo local de FAISS. |
| **Seguridad y Sanitización en MCP** | Aunque el servidor MCP sanitiza los títulos para evitar *Path Traversal*, un ataque sofisticado de *Prompt Injection* podría forzar al LLM a escribir grandes volúmenes de texto basura, saturando el disco local. |
| **Dependencia Cloud para Razonamiento** | A pesar de que la base vectorial FAISS reside localmente, la generación de lenguaje y los embeddings siguen requiriendo conectividad a Vertex AI. El sistema no puede funcionar 100% sin conexión a Internet. |

### 7.2 Líneas de Trabajo Futuro y Escalabilidad

| Mejora Propuesta | Descripción y Beneficio |
|---|---|
| **Observabilidad Completa** (Bonus t07/t08) | Integrar **Arize Phoenix** o **Langfuse** para medir con precisión la latencia de cada agente, los costes por tokens en Vertex AI e identificar cuellos de botella en la recuperación RAG. |
| **Migración a Vertex AI Vector Search** | Reemplazar el índice local FAISS por la base vectorial administrada de Vertex AI para escalar a millones de páginas de documentación. |
| **Evaluación Continua con DeepEval** | Batería de pruebas CI/CD con un *Golden Dataset* de 50 preguntas reales de certificación GCP, calculando automáticamente las métricas de **Faithfulness** y **Answer Relevancy** ante cada cambio del sistema. |

---

## Referencias

1. Google Cloud. (2025). *Google Agent Development Kit (ADK) Documentation*. https://google.github.io/adk-docs
2. Anthropic. (2024). *Model Context Protocol (MCP) Specification*. https://modelcontextprotocol.io
3. Meta AI Research. (2023). *FAISS: A Library for Efficient Similarity Search*. https://github.com/facebookresearch/faiss
4. LlamaIndex. (2025). *LlamaIndex Documentation — RAG Pipelines*. https://docs.llamaindex.ai
5. Google Cloud. (2025). *Vertex AI Text Embeddings API — text-embedding-004*. https://cloud.google.com/vertex-ai
6. Astral. (2024). *uv — An Extremely Fast Python Package Manager*. https://github.com/astral-sh/uv
7. Huang, J. et al. (2023). *A Survey on Hallucination in Large Language Models*. arXiv:2309.01219
8. Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS 2020.
