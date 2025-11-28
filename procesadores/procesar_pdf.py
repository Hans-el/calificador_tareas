# Sirve para extraer texto de archivos PDF
import PyPDF2

def extraer_texto_pdf(ruta_archivo: str) -> str:
    texto = []
    with open(ruta_archivo, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                texto.append(page_text)
    return "\n".join(texto)
# Esto mandará el texto al modelo junto con los criterios.


#otra versión simple
def procesar_pdf(path):
    texto = ""
    with open(path, "rb") as f:
        pdf = PyPDF2.PdfReader(f)
        for page in pdf.pages:
            texto += page.extract_text() + "\n"
    return texto
