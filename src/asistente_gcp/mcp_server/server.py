"""Servidor MCP para exportar resúmenes y reportes de progreso del Asistente de Estudio de Google Cloud."""

from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
from mcp.server import FastMCP

# Cargar variables de entorno
load_dotenv()

# Puerto y host por defecto del servidor MCP
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "9002"))

mcp = FastMCP(
    name="asistente-gcp-mcp-server",
    host=MCP_HOST,
    port=MCP_PORT,
)

# Obtener y crear directorio de estudio local persistente
DEFAULT_STUDY_DIR = Path(__file__).resolve().parents[3] / "data" / "studio_notes"

def _study_dir() -> Path:
    study_dir_env = os.getenv("STUDY_DIR")
    if study_dir_env:
        path = Path(study_dir_env).expanduser()
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[3] / path
    else:
        path = DEFAULT_STUDY_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path

def _generate_filename(title: str, tipo: str) -> Path:
    clean_title = title.strip()
    if not clean_title:
        raise ValueError("El título no puede estar vacío.")

    # Sanitizar título
    safe_title = "".join(
        ch for ch in clean_title if ch.isalnum() or ch in ("-", "_", " ", ".")
    )
    safe_title = safe_title.strip().replace(" ", "_")
    if not safe_title:
        raise ValueError("El título debe contener caracteres alfanuméricos válidos.")

    # Asegurar extensión markdown
    if not safe_title.lower().endswith(".md"):
        safe_title = f"{safe_title}.md"

    # Organizar por subcarpetas según tipo
    subfolder = "resumenes" if tipo.lower() == "resumen" else "reportes_errores"
    target_dir = _study_dir() / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    
    return target_dir / safe_title

@mcp.tool(description="Exporta un resumen de estudio o reporte de progreso/errores a un archivo Markdown local.")
def exportar_resumen_y_progreso(titulo: str, contenido: str, tipo: str = "resumen") -> str:
    """
    Guarda de forma persistente y estructurada información de estudio en formato Markdown.
    
    Args:
        titulo: Título del archivo o tema de estudio (ej: 'Cloud Spanner Overview')
        contenido: El texto completo formateado en Markdown.
        tipo: El tipo de reporte ('resumen' o 'reporte_errores'). Por defecto es 'resumen'.
        
    Returns:
        Un mensaje confirmando el éxito del guardado y la ruta del archivo.
    """
    if tipo.lower() not in ("resumen", "reporte_errores"):
        return f"Error: Tipo '{tipo}' no válido. Utiliza 'resumen' o 'reporte_errores'."

    try:
        filepath = _generate_filename(titulo, tipo)
        filepath.write_text(contenido, encoding="utf-8")
        return f"[OK] Guardado con éxito en {tipo}: {filepath.relative_to(Path(__file__).resolve().parents[3])}"
    except Exception as e:
        return f"Error al guardar el archivo: {str(e)}"

if __name__ == "__main__":
    print(f"Iniciando Servidor MCP en http://{MCP_HOST}:{MCP_PORT}/sse")
    mcp.run(transport="sse")
