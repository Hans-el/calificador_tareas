# Sirve para extraer texto de archivos Word
from docx import Document

def extraer_texto_docx(ruta_archivo: str) -> str:
    doc = Document(ruta_archivo)
    partes = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(partes)
# Esto mandará el texto al modelo junto con los criterios.


#otra versión simple
def procesar_word(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])
