import requests
import json

class EvaluadorResumenes:
    def __init__(self, url_api="http://localhost:11434/api/generate", modelo="mistral"):
        self.url_api = url_api
        self.modelo = modelo
        self.rubrica = {}  # criterios dinámicos

    # =====================================================
    # ACTUALIZAR RÚBRICA (recibe {"Coherencia": 5, "Claridad": 7})
    # =====================================================
    def actualizar_rubrica(self, criterios_dict):
        self.rubrica = [
            {"nombre": nombre, "notaMax": float(peso)}
            for nombre, peso in criterios_dict.items()
        ]

    # =====================================================
    # GENERAR PROMPT DINÁMICO
    # =====================================================
    def crear_prompt(self, texto, criterios):
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
    def llamar_mistral(self, prompt):
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
            print("Error al llamar modelo:", e)
            return None

    # =====================================================
    # EXTRAER JSON DEL MODELO
    # =====================================================
    def extraer_json(self, texto):
        try:
            inicio = texto.find("{")
            fin = texto.rfind("}") + 1
            return json.loads(texto[inicio:fin])
        except:
            return None

    # =====================================================
    # EVALUAR TEXTO SIN TEXTO BASE (PDF / WORD)
    # =====================================================
    def evaluar_resumen_texto_unico(self, texto):
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
    # EVALUAR RESUMEN CON TEXTO BASE (para Excel)
    # =====================================================
    def evaluar_resumen(self, texto_base, autor, resumen):
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
