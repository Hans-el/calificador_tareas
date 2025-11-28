import pandas as pd

def procesar_excel(path):
    """
    Extrae el texto del Excel.
    Se espera un archivo donde haya una columna llamada 'resumen' 
    o simplemente toma todas las celdas como texto concatenado.
    """
    df = pd.read_excel(pcath) #Lee el archivo Excel y lo carga en un DataFrame de pandas

 # Caso 1: Si existe una columna llamada "resumen"
    if "resumen" in df.columns:
        textos = df["resumen"].astype(str).tolist()
        return "\n\n".join(textos)

    # Caso 2: Si no existe, convierte todo el archivo a texto plano
    return df.astype(str).to_string()
#Esto mandará el texto al modelo junto con los criterios.