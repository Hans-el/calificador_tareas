#En este archivo se configura la aplicacion principal de Flask, además 
from flask import Flask, render_template, request, send_file
from evaluador import EvaluadorResumenes
import os
from datetime import datetime

app = Flask(__name__)
evaluador = EvaluadorResumenes()

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/procesar", methods=["POST"])
def procesar():
    if "archivo" not in request.files:
        return "No se subió ningún archivo", 400

    archivo = request.files["archivo"]

    if archivo.filename == "":
        return "Archivo inválido", 400

    # Guardar archivo subido temporalmente
    nombre_entrada = "archivo_subido.xlsx"
    archivo.save(nombre_entrada)

    # Nombre del archivo de salida
    nombre_salida = f"resultados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    # Ejecutar evaluación
    resultados = evaluador.procesar_excel(nombre_entrada, TEXTO_BASE, nombre_salida)

    if resultados is None:
        return render_template("resultado.html", error=True)

    return render_template("resultado.html",
                           archivo_generado=nombre_salida,
                           total=len(resultados),
                           promedio=resultados["Calificación Final"].mean())

@app.route("/descargar/<archivo>")
def descargar(archivo):
    path = os.path.join(os.getcwd(), archivo)
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
