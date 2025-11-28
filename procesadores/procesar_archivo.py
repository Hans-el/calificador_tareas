import os
import uuid
import pandas as pd
from evaluador import EvaluadorResumenes
from .procesar_pdf import extraer_texto_pdf
from .procesar_word import extraer_texto_docx

evaluador = EvaluadorResumenes()

# ======================================================
#  PROCESAR ARCHIVO EXCEL
# ======================================================
def procesar_excel(ruta, criterios):
    # Actualizar rúbrica según criterios dinámicos
    evaluador.actualizar_rubrica(criterios)

    df = pd.read_excel(ruta)
    resultados = []

    # El Excel debe tener: TextoBase, Autor, Resumen
    for i, row in df.iterrows():
        texto_base = row.get("TextoBase", "")
        autor = row.get("Autor", f"Autor_{i+1}")
        resumen = row.get("Resumen", "")

        r = evaluador.evaluar_resumen(texto_base, autor, resumen)

        if r:
            resultados.append(r)

    df_res = pd.DataFrame(resultados)

    nombre_archivo = f"resultados_excel_{uuid.uuid4().hex}.xlsx"
    ruta_salida = os.path.join("resultados", nombre_archivo)

    df_res.to_excel(ruta_salida, index=False)

    total = len(resultados)
    promedio = df_res["Calificación Final"].mean() if total > 0 else 0

    return {"total": total, "promedio": float(promedio)}, nombre_archivo


# ======================================================
#  PROCESAR PDF
# ======================================================
def procesar_pdf(ruta, criterios):
    evaluador.actualizar_rubrica(criterios)

    texto = extraer_texto_pdf(ruta).strip()
    if not texto:
        return {"total": 0, "promedio": 0}, None

    # Evaluación para un solo texto (sin texto base)
    r = evaluador.evaluar_resumen_texto_unico(texto)

    df = pd.DataFrame([r])

    nombre_archivo = f"resultado_pdf_{uuid.uuid4().hex}.xlsx"
    ruta_salida = os.path.join("resultados", nombre_archivo)

    df.to_excel(ruta_salida, index=False)

    return {"total": 1, "promedio": r["Calificación Final"]}, nombre_archivo


# ======================================================
#  PROCESAR WORD (DOCX)
# ======================================================
def procesar_word(ruta, criterios):
    evaluador.actualizar_rubrica(criterios)

    texto = extraer_texto_docx(ruta).strip()
    if not texto:
        return {"total": 0, "promedio": 0}, None

    r = evaluador.evaluar_resumen_texto_unico(texto)

    df = pd.DataFrame([r])

    nombre_archivo = f"resultado_word_{uuid.uuid4().hex}.xlsx"
    ruta_salida = os.path.join("resultados", nombre_archivo)

    df.to_excel(ruta_salida, index=False)

    return {"total": 1, "promedio": r["Calificación Final"]}, nombre_archivo
