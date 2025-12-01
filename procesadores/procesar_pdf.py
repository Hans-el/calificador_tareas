import PyPDF2
from typing import Optional


#1. Primero extraemos el texto del PDF.
def extraer_texto_pdf(ruta_archivo: str) -> Optional[str]:
    """
    Extrae el texto de un archivo PDF.

    Args:
        ruta_archivo (str): Ruta del archivo PDF.

    Returns:
        Optional[str]: Texto extraído del PDF o None si hay un error.
    """
    try:
        texto = ""
        with open(ruta_archivo, "rb") as archivo:
            lector = PyPDF2.PdfReader(archivo)
            for pagina in lector.pages:
                texto += pagina.extract_text() + "\n"  # Añadir salto de línea entre páginas
        return texto.strip()  # Eliminar espacios en blanco al inicio y final
    except Exception as e:
        print(f"Error al extraer texto del PDF: {e}")
        return None

#2. Luego procesamos el PDF usando la función anterior, ya con el texto extraído.
def procesar_pdf(ruta_archivo: str) -> str:
    """
    Procesa un archivo PDF y devuelve el texto extraído.

    Args:
        ruta_archivo (str): Ruta del archivo PDF.

    Returns:
        str: Texto extraído del PDF.

    Raises:
        ValueError: Si no se puede extraer el texto del PDF.
    """
    texto = extraer_texto_pdf(ruta_archivo)
    if texto is None:
        raise ValueError("No se pudo extraer texto del PDF.")
    return texto
