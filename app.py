from flask import Flask, render_template, request, send_file, redirect, url_for
import os
from flask import send_from_directory
from werkzeug.utils import secure_filename
from evaluador import EvaluadorTareas  # Usamos la nueva clase
#from procesadores.procesar_archivo import procesar_excel, procesar_pdf, procesar_word
from procesadores.procesar_pdf import extraer_texto_pdf
from procesadores.procesar_word import extraer_texto_word
from procesadores.procesar_excel import extraer_texto_excel, procesar_excel

# ======================================================
# CONFIGURACIÓN
# ======================================================
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["RESULTADOS_FOLDER"] = "resultados"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["RESULTADOS_FOLDER"], exist_ok=True)

# Inicializar el evaluador de tareas
evaluador = EvaluadorTareas()

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
    criterios_notas = request.form.getlist("criterio_peso")

    # Validar que los criterios no estén vacíos
    if not criterios_nombres or not criterios_notas:
        return render_template("resultado.html", error="No se recibieron criterios.")

    # Crear diccionario de criterios
    criterios_dict = {}
    for nombre, nota in zip(criterios_nombres, criterios_notas):
        if nombre.strip() != "":
            criterios_dict[nombre] = float(nota)

    # Actualizar la rúbrica en el evaluador
    evaluador.actualizar_rubrica(criterios_dict)

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
        resultado = evaluador.evaluar_texto(texto_manual)
        # Generar archivo Excel con los resultados
        nombre_excel = f"rubrica_texto_manual.xlsx"
        ruta_excel = os.path.join(app.config["RESULTADOS_FOLDER"], nombre_excel)
        evaluador.generar_rubrica_excel(resultado, ruta_excel)
        return render_template("resultado.html",
                               resultado=resultado,
                               archivo_generado=nombre_excel)

    # --------------------------------------------------
    # 4. PROCESAR ARCHIVO SUBIDO
    # --------------------------------------------------
    nombre = secure_filename(archivo.filename)
    ruta = os.path.join(app.config["UPLOAD_FOLDER"], nombre)
    archivo.save(ruta)
    extension = nombre.lower().rsplit(".", 1)[-1]

    # ----- PDF -----
    if extension == "pdf":
        texto = extraer_texto_pdf(ruta)
        resultado = evaluador.evaluar_texto(texto)
        # Generar archivo Excel con los resultados
        nombre_excel = f"rubrica_{nombre}.xlsx"
        ruta_excel = os.path.join(app.config["RESULTADOS_FOLDER"], nombre_excel)
        evaluador.generar_rubrica_excel(resultado, ruta_excel)
        return render_template("resultado.html",
                               resultado=resultado,
                               archivo_generado=nombre_excel)

    # ----- WORD -----
    if extension == "docx":
        texto = extraer_texto_word(ruta)
        resultado = evaluador.evaluar_texto(texto)
        # Generar archivo Excel con los resultados
        nombre_excel = f"rubrica_{nombre}.xlsx"
        ruta_excel = os.path.join(app.config["RESULTADOS_FOLDER"], nombre_excel)
        evaluador.generar_rubrica_excel(resultado, ruta_excel)
        return render_template("resultado.html",
                               resultado=resultado,
                               archivo_generado=nombre_excel)

    # ----- EXCEL (múltiples resúmenes) -----
    if extension == "xlsx":
        df_resultado, nombre_archivo = procesar_excel(ruta, criterios_dict, evaluador, 
    app.config["RESULTADOS_FOLDER"])
        if df_resultado.empty:
            return render_template("resultado.html", error=f"Error al procesar el archivo Excel: {nombre_archivo}")
    return render_template(
        "resultado.html",
        resultado=df_resultado.to_dict(orient="records"),
        archivo_generado=nombre_archivo
    )


# ======================================================
# DESCARGAR ARCHIVO RESULTANTE
# ======================================================
@app.route("/descargar/<archivo>")
def descargar(archivo):
    ruta = os.path.join(app.config["RESULTADOS_FOLDER"], archivo)
    if os.path.exists(ruta):
        return send_file(ruta, as_attachment=True)
    return "Archivo no encontrado", 404

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ======================================================
# EJECUTAR
# ======================================================
if __name__ == "__main__":
    app.run(debug=True)
