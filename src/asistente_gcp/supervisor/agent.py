"""Agente Supervisor principal que orquesta a los sub-agentes RAG y Evaluador, expuesto como root_agent."""

import os
from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

from asistente_gcp.utils.model_config import get_model
from asistente_gcp.agents.rag_expert import rag_expert_agent
from asistente_gcp.agents.evaluator import evaluator_agent

# URL del servidor MCP
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = os.getenv("MCP_PORT", "9002")
MCP_SERVER_URL = f"http://{MCP_HOST}:{MCP_PORT}/sse"

# Definir herramientas MCP para el Supervisor
mcp_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url=MCP_SERVER_URL,
        timeout=30,
    ),
    tool_filter=["exportar_resumen_y_progreso"],
)

root_agent = Agent(
    model=get_model(),
    name="supervisor_agent",
    description=(
        "Supervisor principal del Asistente de Estudio y Certificación de Google Cloud. "
        "Orquesta las consultas, evaluaciones y exportaciones de resúmenes de estudio."
    ),
    instruction=(
        "Eres el 'Asistente de Certificación de Google Cloud', un supervisor inteligente y empático.\n"
        "Tu objetivo es guiar al usuario en su camino de aprendizaje utilizando tus sub-agentes y herramientas disponibles.\n\n"
        "REGLAS DE ORQUESTACIÓN:\n"
        "1. Para dudas conceptuales, explicaciones de servicios o elaboración de resúmenes de GCP:\n"
        "   - Delega la tarea al 'rag_expert_agent'.\n"
        "2. Para evaluar al usuario con tests de opción múltiple o preguntas tipo examen:\n"
        "   - Delega la tarea al 'evaluator_agent'.\n"
        "3. Cuando el usuario solicite explícitamente GUARDAR o EXPORTAR un resumen de estudio, o reportar un error:\n"
        "   - Utiliza la herramienta del servidor MCP 'exportar_resumen_y_progreso'. Puedes pasarle el texto del "
        "     resumen y un título descriptivo.\n"
        "4. Sé siempre profesional, estructurado, motivador y claro en tus interacciones."
    ),
    tools=[
        AgentTool(agent=rag_expert_agent),
        AgentTool(agent=evaluator_agent),
        mcp_toolset,
    ],
)
