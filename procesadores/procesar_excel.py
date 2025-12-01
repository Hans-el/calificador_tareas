# procesar_excel.py
import pandas as pd
import os
import time
from typing import Tuple, Dict, List
from evaluador import EvaluadorTareas

def extraer_texto_excel(ruta_archivo: str) -> str:
    """
    Extrae TODO el texto de un archivo Excel, concatenando todas las celdas.

    Args:
        ruta_archivo (str): Ruta del archivo Excel.

    Returns:
        str: Texto concatenado de todas las celdas.
    """
    try:
        df = pd.read_excel(ruta_archivo)
        texto_completo = " ".join(df.fillna("").astype(str).values.flatten())
        return texto_completo
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        return ""

def procesar_excel(
    ruta_archivo: str,
    criterios_dict: Dict[str, float],
    evaluador: EvaluadorTareas,
    carpeta_resultados: str
) -> Tuple[pd.DataFrame, str]:
    """
    Procesa un archivo Excel, extrae TODO el texto y lo evalúa como una sola tarea.
    Si el Excel tiene múltiples filas, cada fila se evalúa como una tarea independiente.

    Args:
        ruta_archivo (str): Ruta del archivo Excel.
        criterios_dict (Dict[str, float]): Criterios de evaluación.
        evaluador (EvaluadorTareas): Instancia del evaluador.
        carpeta_resultados (str): Carpeta para guardar el Excel de resultados.

    Returns:
        Tuple[pd.DataFrame, str]: DataFrame con resultados y nombre del archivo generado.
    """
    try:
        # Leer el archivo Excel
        df = pd.read_excel(ruta_archivo)

        # Si el Excel está vacío
        if df.empty:
            raise ValueError("El archivo Excel está vacío.")

        # Actualizar la rúbrica del evaluador
        evaluador.actualizar_rubrica(criterios_dict)

        # Lista para almacenar los resultados
        resultados = []

        # Evaluar CADA FILA como una tarea independiente
        for _, fila in df.iterrows():
            # Convertir toda la fila a texto
            texto_tarea = " ".join(fila.fillna("").astype(str).values)

            # Evaluar el texto
            resultado = evaluador.evaluar_texto(texto_tarea)

            # Agregar los resultados
            resultados.append({
                "Tarea": texto_tarea[:50] + "..." if len(texto_tarea) > 50 else texto_tarea,  # Mostrar solo un fragmento
                "Calificación Final": resultado["Calificación Final"],
                **{f"{criterio['nombre']} (Puntaje)": criterio["puntaje"] for criterio in resultado["criterios"]},
                **{f"{criterio['nombre']} (Justificación)": criterio["justificacion"] for criterio in resultado["criterios"]}
            })

        # Crear DataFrame con los resultados
        df_resultados = pd.DataFrame(resultados)

        # Generar nombre del archivo de resultados
        nombre_archivo = f"rubrica_excel_{int(time.time())}.xlsx"
        ruta_resultado = os.path.join(carpeta_resultados, nombre_archivo)

        # Guardar resultados en Excel
        df_resultados.to_excel(ruta_resultado, index=False)

        return df_resultados, nombre_archivo

    except Exception as e:
        print(f"Error al procesar el archivo Excel: {e}")
        return pd.DataFrame(), f"error_{int(time.time())}.txt"
