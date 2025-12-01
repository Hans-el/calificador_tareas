import requests
import json
import pandas as pd
from typing import Dict, List, Optional, Union

class EvaluadorTareas:
    def __init__(self, url_api: str = "http://localhost:11434/api/generate", modelo: str = "mistral"):
        """
        Inicializa el evaluador con la URL de la API de Ollama y el modelo a usar.
        Args:
            url_api (str): URL de la API de Ollama.
            modelo (str): Nombre del modelo (ej: "mistral").
        """
        self.url_api = url_api
        self.modelo = modelo
        self.rubrica = []  # Lista de criterios dinámicos

    # =====================================================
    # ACTUALIZAR RÚBRICA (recibe {"Coherencia": 5, "Claridad": 7})
    # =====================================================
    def actualizar_rubrica(self, criterios_dict: Dict[str, float]) -> None:
        """
        Actualiza la rúbrica con los criterios y sus notas máximas.
        Args:
            criterios_dict (Dict[str, float]): Diccionario con los criterios y sus notas máximas.
        """
        self.rubrica = [
            {"nombre": nombre, "notaMax": float(peso)}
            for nombre, peso in criterios_dict.items()
        ]

    # =====================================================
    # GENERAR PROMPT DINÁMICO
    # =====================================================
    def crear_prompt(self, texto: str, criterios: List[Dict[str, float]]) -> str:
        """
        Crea un prompt dinámico para evaluar el texto según los criterios.
        Args:
            texto (str): Texto a evaluar.
            criterios (List[Dict[str, float]]): Lista de criterios con sus notas máximas.
        Returns:
            str: Prompt formateado para el modelo.
        """
        criterios_json = json.dumps(criterios, indent=2)
        prompt = f"""
        Eres un evaluador académico experto.
        Evalúa el siguiente texto según los criterios definidos por el usuario.
        TEXTO A EVALUAR:
        \"\"\"{texto}\"\"\"
        CRITERIOS (cada criterio tiene una nota máxima):
        {criterios_json}
        Reglas estrictas:
        - Evalúa cada criterio con un puntaje entre 0 y su "notaMax".
        - Explica brevemente por qué asignaste ese puntaje.
        - Calcula "notaFinal" como el promedio de (puntaje / notaMax) * 10.
        - NO incluyas nada fuera del JSON.
        FORMATO EXACTO DE RESPUESTA:
        {{
          "criterios": [
            {{
              "nombre": "NombreCriterio",
              "notaMax": 0,
              "puntaje": 0,
              "justificacion": "Explicación breve"
            }}
          ],
          "notaFinal": 0
        }}
        Responde únicamente con el JSON.
        """
        return prompt

    # =====================================================
    # LLAMAR A OLLAMA / MISTRAL
    # =====================================================
    def llamar_mistral(self, prompt: str) -> Optional[str]:
        """
        Llama a la API de Ollama para generar una respuesta.
        Args:
            prompt (str): Prompt a enviar al modelo.
        Returns:
            Optional[str]: Respuesta del modelo o None si hay error.
        """
        try:
            payload = {
                "model": self.modelo,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2
            }
            response = requests.post(self.url_api, json=payload, timeout=180)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            print("Error al llamar al modelo:", e)
            return None

    # =====================================================
    # EXTRAER JSON DEL MODELO
    # =====================================================
    def extraer_json(self, texto: str) -> Optional[Dict]:
        """
        Extrae el JSON de la respuesta del modelo.
        Args:
            texto (str): Respuesta del modelo.
        Returns:
            Optional[Dict]: Diccionario con los resultados o None si hay error.
        """
        try:
            inicio = texto.find("{")
            fin = texto.rfind("}") + 1
            return json.loads(texto[inicio:fin])
        except:
            return None

    # =====================================================
    # EVALUAR TEXTO (PDF / WORD / TEXTO PLANO)
    # =====================================================
    def evaluar_texto(self, texto: str) -> Dict:
        """
        Evalúa un texto único (ej: PDF, WORD).
        Args:
            texto (str): Texto a evaluar.
        Returns:
            Dict: Resultados de la evaluación.
        """
        prompt = self.crear_prompt(texto, self.rubrica)
        raw = self.llamar_mistral(prompt)
        datos = self.extraer_json(raw)
        if not datos:
            return {
                "error": "JSON inválido",
                "respuesta": raw
            }
        datos["Calificación Final"] = datos["notaFinal"]
        return datos

    # =====================================================
    # EVALUAR TEXTO CON TEXTO BASE (para Excel)
    # =====================================================
    def evaluar_con_texto_base(self, texto_base: str, autor: str, resumen: str) -> Dict:
        """
        Evalúa un resumen en comparación con un texto base (ej: Excel).
        Args:
            texto_base (str): Texto original.
            autor (str): Autor del resumen.
            resumen (str): Resumen a evaluar.
        Returns:
            Dict: Resultados de la evaluación.
        """
        texto_total = f"""
        Autor del resumen: {autor}
        TEXTO BASE:
        \"\"\"{texto_base}\"\"\"
        RESUMEN PROPUESTO:
        \"\"\"{resumen}\"\"\"
        """
        prompt = self.crear_prompt(texto_total, self.rubrica)
        raw = self.llamar_mistral(prompt)
        datos = self.extraer_json(raw)
        if not datos:
            return {
                "error": "JSON inválido",
                "respuesta": raw
            }
        datos["Autor"] = autor
        datos["Resumen"] = resumen
        datos["Calificación Final"] = datos["notaFinal"]
        return datos

    # =====================================================
    # GENERAR RÚBRICA EN EXCEL
    # =====================================================
    def generar_rubrica_excel(self, resultados: Dict, ruta_salida: str) -> str:
        """
        Genera un archivo Excel con los resultados de la evaluación.
        Args:
            resultados (Dict): Resultados de la evaluación.
            ruta_salida (str): Ruta donde guardar el archivo Excel.
        Returns:
            str: Ruta del archivo Excel generado.
        """
        # Crear DataFrame con los criterios
        criterios_df = pd.DataFrame(resultados["criterios"])
        criterios_df["Criterio"] = criterios_df["nombre"]
        criterios_df["Nota Máxima"] = criterios_df["notaMax"]
        criterios_df["Puntaje"] = criterios_df["puntaje"]
        criterios_df["Justificación"] = criterios_df["justificacion"]
        criterios_df = criterios_df[["Criterio", "Nota Máxima", "Puntaje", "Justificación"]]

        # Crear DataFrame con la calificación final
        final_df = pd.DataFrame({
            "Calificación Final": [resultados["Calificación Final"]],
            "Autor": resultados.get("Autor", "N/A"),
            "Resumen": resultados.get("Resumen", "N/A")
        })

        # Guardar en Excel
        with pd.ExcelWriter(ruta_salida) as writer:
            criterios_df.to_excel(writer, sheet_name="Criterios", index=False)
            final_df.to_excel(writer, sheet_name="Calificación Final", index=False)

        return ruta_salida
