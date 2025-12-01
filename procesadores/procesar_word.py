from docx import Document
from typing import Optional

def extraer_texto_word(ruta_archivo: str) -> Optional[str]:
    """
    Extrae el texto de un archivo Word (.docx).

    Args:
        ruta_archivo (str): Ruta del archivo Word.

    Returns:
        Optional[str]: Texto extraído del archivo Word o None si hay un error.
    """
    try:
        doc = Document(ruta_archivo)
        texto = "\n".join([parrafo.text for parrafo in doc.paragraphs])
        return texto.strip()  # Eliminar espacios en blanco al inicio y final
    except Exception as e:
        print(f"Error al extraer texto del archivo Word: {e}")
        return None

def procesar_word(ruta_archivo: str) -> str:
    """
    Procesa un archivo Word y devuelve el texto extraído.

    Args:
        ruta_archivo (str): Ruta del archivo Word.

    Returns:
        str: Texto extraído del archivo Word.

    Raises:
        ValueError: Si no se puede extraer el texto del archivo Word.
    """
    texto = extraer_texto_word(ruta_archivo)
    if texto is None:
        raise ValueError("No se pudo extraer texto del archivo Word.")
    return texto
