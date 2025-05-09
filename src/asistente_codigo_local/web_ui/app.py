from flask import Flask, render_template, request, jsonify, session
import os
import sys
import logging

# --- AJUSTE DE RUTA (COMO ANTES, VERIFICADO) ---
PATH_TO_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PATH_TO_SRC_DIR not in sys.path:
    sys.path.insert(0, PATH_TO_SRC_DIR)

from asistente_codigo_local.gpo.orchestrator import GestorPeticionesOrquestacion
from asistente_codigo_local.mlm.mlm_logger import ModuloLogging

app = Flask(__name__)
app.secret_key = os.urandom(32) 

logger_web = ModuloLogging.get_logger("WEB_UI_FLASK")

# --- CONFIGURACIÓN DEL DIRECTORIO DEL PROYECTO PARA EL GPO (USANDO ENV VAR) ---
# El Dockerfile puede establecer ASSISTANT_PROJECT_DIR.
# Para ejecución local sin Docker, usa un fallback (ej., la raíz del proyecto del asistente).
DEFAULT_PROJECT_OPERATIONS_DIR = os.environ.get(
    "ASSISTANT_PROJECT_DIR", 
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")) # 3 niveles arriba desde app.py
)
logger_web.info(f"Directorio de proyecto para operaciones del GPO: {DEFAULT_PROJECT_OPERATIONS_DIR}")
if not os.path.isdir(DEFAULT_PROJECT_OPERATIONS_DIR):
    logger_web.warning(f"El directorio de operaciones por defecto '{DEFAULT_PROJECT_OPERATIONS_DIR}' no existe. Creándolo o usando uno temporal podría ser necesario.")
    # Considera crear un directorio por defecto si no existe y es esperado,
    # o manejar el error más adelante si el GPO lo necesita obligatoriamente.
    # Por ahora, el GPO ya valida la existencia del directorio.


gpo_instance = GestorPeticionesOrquestacion(ui_confirm_callback=None)
logger_web.warning("GPO inicializado en la Web UI con auto-confirmación de acciones (ui_confirm_callback=None). Esto es para desarrollo y es INSEGURO para operaciones sensibles.")

@app.route('/', methods=['GET'])
def index():
    session.pop('original_request_context', None)
    session.pop('clarification_message_context', None)
    logger_web.debug("Sirviendo página principal, sesión limpiada.")
    # Pasar el directorio de operaciones para mostrarlo en la UI
    return render_template('index.html', project_dir_display=DEFAULT_PROJECT_OPERATIONS_DIR)

@app.route('/ask', methods=['POST'])
def ask_assistant():
    user_prompt = request.form.get('prompt')
    project_dir_for_gpo = DEFAULT_PROJECT_OPERATIONS_DIR # Usar el directorio configurado

    if not user_prompt:
        logger_web.warning("Petición recibida sin prompt.")
        return jsonify({"type": "error", "data": "La petición está vacía."}), 400

    if not os.path.isdir(project_dir_for_gpo):
        logger_web.error(f"Directorio de proyecto para GPO no válido o no encontrado: {project_dir_for_gpo}")
        return jsonify({"type": "error", "data": f"Directorio de proyecto (para GPO) configurado no es válido: {project_dir_for_gpo}"}), 500

    final_prompt_to_gpo = user_prompt
    is_clarification_response = False
    original_req_for_clarif_context = ""

    if 'original_request_context' in session and 'clarification_message_context' in session:
        original_req_for_clarif_context = session.pop('original_request_context')
        clarif_msg = session.pop('clarification_message_context')

        final_prompt_to_gpo = (
            f"Referente a la petición anterior: \"{original_req_for_clarif_context}\".\n"
            f"Se solicitó la siguiente aclaración: \"{clarif_msg}\".\n"
            f"El usuario ha respondido: \"{user_prompt}\".\n"
            f"Por favor, intenta procesar la petición original de nuevo con esta información adicional y genera un plan de acciones ejecutable."
        )
        is_clarification_response = True
        logger_web.info(f"Procesando con aclaración. Prompt combinado: {final_prompt_to_gpo[:250]}...")
    else:
        logger_web.info(f"Nueva petición web: Prompt='{user_prompt}', Dir GPO='{project_dir_for_gpo}'")

    try:
        gpo_response = gpo_instance.procesar_peticion_usuario(final_prompt_to_gpo, project_dir_for_gpo)

        if gpo_response.get("type") == "clarification_needed":
            logger_web.info(f"GPO solicita aclaración: {gpo_response.get('message')}")
            session['original_request_context'] = gpo_response.get('original_request', user_prompt if not is_clarification_response else original_req_for_clarif_context)
            session['clarification_message_context'] = gpo_response.get('message')

        return jsonify(gpo_response)

    except Exception as e:
        logger_web.error(f"Excepción no controlada en /ask: {e}", exc_info=True)
        return jsonify({"type": "error", "data": f"Error interno del servidor al procesar la petición: {str(e)}"}), 500

if __name__ == '__main__':
    log_dir_path = os.path.join(os.path.expanduser("~"), ".asistente_codigo_local")
    os.makedirs(log_dir_path, exist_ok=True) 
    logger_web.info(f"Log directory: {log_dir_path}")

    logger_web.info("--- Iniciando Web UI del Asistente de Código Local ---")

    port = int(os.environ.get("FLASK_RUN_PORT", 5001))
    # FLASK_DEBUG=1 (o cualquier valor no vacío) habilita el modo debug.
    # Para producción, esto debería ser 0 o no estar definido.
    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1"

    app.jinja_env.globals.update(project_dir_display=DEFAULT_PROJECT_OPERATIONS_DIR)

    # Ejecutar en 0.0.0.0 para ser accesible desde fuera del contenedor Docker
    app.run(debug=debug_mode, host='0.0.0.0', port=port)