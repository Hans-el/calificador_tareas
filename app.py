from flask import Flask, render_template, request, send_file
import os
from werkzeug.utils import secure_filename
from evaluador import EvaluadorResumenes

# Procesadores externos (tú ya los tienes)
from procesadores.procesar_archivo import procesar_excel, procesar_pdf, procesar_word

# ======================================================
# CONFIGURACIÓN
# ======================================================
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["RESULTADOS_FOLDER"] = "resultados"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["RESULTADOS_FOLDER"], exist_ok=True)

evaluador = EvaluadorResumenes()


# ======================================================
# RUTA PRINCIPAL
# ======================================================
@app.route("/")
def index():
    return render_template("index.html")


# ======================================================
# PROCESAR ARCHIVO / TEXTO
# ======================================================
@app.route("/procesar", methods=["POST"])
def procesar():
    # --------------------------------------------------
    # 1. RECIBIR CRITERIOS
    # --------------------------------------------------
    criterios_nombres = request.form.getlist("criterio_nombre")
    criterios_notas   = request.form.getlist("criterio_peso")

    criterios = []
    for nombre, nota in zip(criterios_nombres, criterios_notas):
        if nombre.strip() != "":
            criterios.append({
                "nombre": nombre,
                "notaMax": int(nota)
        })

    if not criterios:
        return render_template("resultado.html", error="No se recibieron criterios.")



    # --------------------------------------------------
    # 2. ARCHIVO O TEXTO DIRECTO
    # --------------------------------------------------
    archivo = request.files.get("archivo")
    texto_manual = request.form.get("texto_manual", "").strip()

    if not archivo and texto_manual == "":
        return render_template("resultado.html", error="Debe subir un archivo o escribir texto.")

    # --------------------------------------------------
    # 3. EVALUAR TEXTO DIRECTO
    # --------------------------------------------------
    if texto_manual:
        resultado = evaluador.evaluar_texto(texto_manual, criterios)

        return render_template("resultado.html",
                               resultado=resultado,
                               archivo_generado=None)

    # --------------------------------------------------
    # 4. PROCESAR ARCHIVO SUBIDO
    # --------------------------------------------------
    nombre = secure_filename(archivo.filename)
    ruta = os.path.join(app.config["UPLOAD_FOLDER"], nombre)
    archivo.save(ruta)

    extension = nombre.lower().split(".")[-1]

    # ----- PDF -----
    if extension == "pdf":
        texto = procesar_pdf(ruta)
        resultado = evaluador.evaluar_texto(texto, criterios)
        return render_template("resultado.html", resultado=resultado)

    # ----- WORD -----
    if extension == "docx":
        texto = procesar_word(ruta)
        resultado = evaluador.evaluar_texto(texto, criterios)
        return render_template("resultado.html", resultado=resultado)

    # ----- EXCEL (múltiples resúmenes) -----
    if extension == "xlsx":
        df_resultado, nombre_archivo = procesar_excel(ruta, criterios, evaluador, app.config["RESULTADOS_FOLDER"]) #tiene 4 parametros por recibir. OJO
        return render_template("resultado.html",
                               resultado=df_resultado.to_dict(orient="records"),
                               archivo_generado=nombre_archivo)

    return render_template("resultado.html", error="Formato de archivo no soportado.")


# ======================================================
# DESCARGAR ARCHIVO RESULTANTE
# ======================================================
@app.route("/descargar/<archivo>")
def descargar(archivo):
    ruta = os.path.join(app.config["RESULTADOS_FOLDER"], archivo)
    if os.path.exists(ruta):
        return send_file(ruta, as_attachment=True)
    return "Archivo no encontrado", 404


# ======================================================
# EJECUTAR
# ======================================================
if __name__ == "__main__":
    app.run(debug=True)
