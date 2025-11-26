"""
Sistema de Evaluación Automática de Resúmenes usando Mistral 7B
Requisitos: pip install pandas openpyxl requests
"""

import pandas as pd
import requests
import json
from datetime import datetime

class EvaluadorResumenes:
    def __init__(self, url_api="http://localhost:11434/api/generate"):
        """
        Inicializa el evaluador con la URL de la API de Ollama (Mistral 7B)
        """
        self.url_api = url_api
        self.modelo = "mistral" # Nombre del modelo en Ollama
        # Define la rúbrica de evaluación
        self.rubrica = {
            "Estructura": {"descripcion": "Organización lógica del resumen (introducción, desarrollo, conclusión)","peso": 20 },
            "Ortografía": {"descripcion": "Corrección ortográfica y gramatical","peso": 15 },
            "Comprensión": {"descripcion": "Demuestra entendimiento del texto original","peso": 25 },
            "Redacción": {"descripcion": "Claridad, coherencia y fluidez del texto","peso": 20 },
            "Síntesis": {"descripcion": "Capacidad de condensar ideas principales sin perder información clave","peso": 20 }        
        }
    
    def crear_prompt_evaluacion(self, texto_base, resumen):
        """
        Crea un prompt estructurado para que Mistral evalúe el resumen
        """
        prompt = f"""Eres un evaluador académico experto. Tu tarea es evaluar un resumen según criterios específicos.

TEXTO BASE:
{texto_base}

RESUMEN A EVALUAR:
{resumen}

INSTRUCCIONES DE EVALUACIÓN:
Evalúa el resumen anterior según los siguientes criterios y asigna una calificación del 1 al 10 para cada uno:

1. ESTRUCTURA (20%): Organización lógica del resumen (introducción, desarrollo, conclusión)
2. ORTOGRAFÍA (15%): Corrección ortográfica y gramatical
3. COMPRENSIÓN (25%): Demuestra entendimiento del texto original
4. REDACCIÓN (20%): Claridad, coherencia y fluidez del texto
5. SÍNTESIS (20%): Capacidad de condensar ideas principales sin perder información clave

FORMATO DE RESPUESTA REQUERIDO (responde EXACTAMENTE en este formato JSON):
{{
    "Estructura": {{
        "calificacion": [número del 1 al 10],
        "justificacion": "[breve explicación]"
    }},
    "Ortografía": {{
        "calificacion": [número del 1 al 10],
        "justificacion": "[breve explicación]"
    }},
    "Comprensión": {{
        "calificacion": [número del 1 al 10],
        "justificacion": "[breve explicación]"
    }},
    "Redacción": {{
        "calificacion": [número del 1 al 10],
        "justificacion": "[breve explicación]"
    }},
    "Síntesis": {{
        "calificacion": [número del 1 al 10],
        "justificacion": "[breve explicación]"
    }},
    "comentario_general": "[retroalimentación general para el estudiante]"
}}

Responde ÚNICAMENTE con el JSON, sin texto adicional."""
        
        return prompt
    
    def llamar_mistral(self, prompt):
        """
        Realiza la llamada a la API local de Mistral 7B (Ollama)
        """
        try:
            payload = {
                "model": self.modelo,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,  
                "max_tokens": 1000
            }
            
            # Timeout extendido por si Mistral tarda en responder
            response = requests.post(self.url_api, json=payload, timeout=240) 
            response.raise_for_status()
            
            resultado = response.json()
            return resultado.get("response", "")
            
        except requests.exceptions.RequestException as e:
            print(f"Error en la llamada a la API: {e}")
            return None
    
    def extraer_json_respuesta(self, respuesta_texto):
        """
        Extrae el JSON de la respuesta del modelo
        """
        try:
            inicio = respuesta_texto.find('{')
            fin = respuesta_texto.rfind('}') + 1
            
            if inicio != -1 and fin > inicio:
                json_str = respuesta_texto[inicio:fin]
                return json.loads(json_str)
            else:
                print("No se encontró JSON válido en la respuesta")
                print(f"Respuesta recibida: {respuesta_texto[:200]}...")
                return None
                
        except json.JSONDecodeError as e:
            print(f"Error al parsear JSON: {e}")
            print(f"Respuesta recibida: {respuesta_texto[:500]}")
            return None
    
    def calcular_calificacion_final(self, evaluacion):
        """
        Calcula la calificación final ponderada según los pesos de la rúbrica
        """
        if not evaluacion:
            return 0
        
        calificacion_total = 0
        for criterio, datos in self.rubrica.items():
            if criterio in evaluacion:
                calificacion = evaluacion[criterio].get("calificacion", 0)
                peso = datos["peso"] / 100
                calificacion_total += calificacion * peso
        
        return round(calificacion_total, 2)
    
    def evaluar_resumen(self, texto_base, autor, resumen):
        """
        Evalúa un resumen completo y retorna los resultados
        """
        print(f"\nEvaluando resumen de: {autor}...")

        prompt = self.crear_prompt_evaluacion(texto_base, resumen)
        
        respuesta = self.llamar_mistral(prompt)
        
        if not respuesta:
            return None
        
        # Extraer evaluación
        evaluacion = self.extraer_json_respuesta(respuesta)
        
        if not evaluacion:
            return None
        
        # Calcular calificación final
        calificacion_final = self.calcular_calificacion_final(evaluacion)
        
        # Preparar resultado
        resultado = {
            "Autor": autor,
            "Calificación Final": calificacion_final
        }
        
        # Agregar calificaciones individuales
        for criterio in self.rubrica.keys():
            if criterio in evaluacion:
                resultado[f"{criterio} (Nota)"] = evaluacion[criterio].get("calificacion", 0)
                resultado[f"{criterio} (Retroalimentación)"] = evaluacion[criterio].get("justificacion", "")
        
        # Agregar comentario general
        resultado["Comentario General"] = evaluacion.get("comentario_general", "")
        
        return resultado
    
    def procesar_excel(self, archivo_entrada, texto_base, archivo_salida):
        """
        Procesa un archivo Excel con resúmenes y genera las evaluaciones
        
        El Excel de entrada debe tener las columnas:
        - Autor: Nombre del estudiante
        - Resumen: El texto del resumen
        """
        try:
            # Leer archivo Excel
            df = pd.read_excel(archivo_entrada)
            
            print(f"Archivo cargado: {len(df)} resúmenes encontrados")
            
            # Validar columnas requeridas
            if "Autor" not in df.columns or "Resumen" not in df.columns:
                raise ValueError("El archivo debe contener las columnas 'Autor' y 'Resumen'")
            
            # Lista para almacenar resultados
            resultados = []
            
            # Evaluar cada resumen
            for index, row in df.iterrows():
                autor = row["Autor"]
                resumen = row["Resumen"]
                
                # Asegurarse de que el resumen sea un string
                if not isinstance(resumen, str):
                    print(f"Omitiendo fila {index}: el resumen no es texto válido.")
                    continue
                
                resultado = self.evaluar_resumen(texto_base, autor, resumen)
                
                if resultado:
                    resultados.append(resultado)
                    print(f"✓ Evaluación completada - Calificación: {resultado['Calificación Final']}/10")
                else:
                    print(f"✗ Error al evaluar el resumen de {autor}")
            
            # Crear DataFrame con resultados
            df_resultados = pd.DataFrame(resultados)
            
            # Guardar resultados en el archivo especificado
            df_resultados.to_excel(archivo_salida, index=False)
            
            return df_resultados
            
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo '{archivo_entrada}'")
            return None
        except Exception as e:
            print(f"Error al procesar el archivo: {e}")
            return None


def main():
    """
    Función principal simplificada para ejecutar la evaluación.
    """
    TEXTO_BASE = """
    La inteligencia artificial (IA) ha transformado radicalmente múltiples sectores de la sociedad 
    en las últimas décadas. Desde sus inicios en la década de 1950, cuando Alan Turing propuso 
    el famoso "Test de Turing", la IA ha evolucionado de sistemas basados en reglas simples a 
    redes neuronales profundas capaces de aprender de grandes volúmenes de datos.
    
    En la actualidad, la IA se aplica en campos tan diversos como la medicina, donde ayuda en 
    el diagnóstico de enfermedades; la educación, personalizando el aprendizaje para cada estudiante; 
    y el transporte, con el desarrollo de vehículos autónomos. Sin embargo, también plantea 
    desafíos éticos importantes, como la privacidad de los datos, el sesgo algorítmico y el 
    impacto en el empleo.
    
    El futuro de la IA promete avances aún más significativos, pero requiere una regulación 
    adecuada y un debate social sobre sus implicaciones. Es fundamental que la sociedad participe 
    en la discusión sobre cómo queremos que la IA moldee nuestro futuro, asegurando que su 
    desarrollo beneficie a toda la humanidad de manera equitativa y sostenible.
    """
    
    print("=" * 70)
    print("SISTEMA DE EVALUACIÓN AUTOMÁTICA DE RESÚMENES")
    print("Modelo: Mistral 7B (Ollama)")
    print("=" * 70)
    
    evaluador = EvaluadorResumenes()
    
    # Archivos definidos (como solicitaste)
    archivo_entrada = "ejemplos.xlsx"
    archivo_salida = "resultados_evaluacion.xlsx"
    
    print(f"Cargando resúmenes desde: {archivo_entrada}...")
    
    # Procesar evaluaciones y guardar en el archivo de salida
    resultados = evaluador.procesar_excel(
        archivo_entrada, 
        TEXTO_BASE, 
        archivo_salida  # Pasa el nombre del archivo de salida
    )
    
    if resultados is not None and not resultados.empty:
        print("\n" + "=" * 70)
        print("RESUMEN DE EVALUACIONES")
        print("=" * 70)
        print(f"✓ Evaluaciones guardadas en: {archivo_salida}")
        print(f"\nCalificación promedio: {resultados['Calificación Final'].mean():.2f}/10")
        print(f"Calificación más alta: {resultados['Calificación Final'].max():.2f}/10")
        print(f"Calificación más baja: {resultados['Calificación Final'].min():.2f}/10")
    elif resultados is not None and resultados.empty:
        print("\n✗ No se encontraron resúmenes válidos para evaluar.")
    else:
        print(f"\n✗ No se pudieron procesar las evaluaciones.")


if __name__ == "__main__":
    main()