from flask import Flask, render_template, request, jsonify, session
import os
import sys
import logging # Import logging

# --- INICIO DE SECCIÓN CORREGIDA ---
# Ajustar la ruta para importar los módulos de tu asistente
# app.py está en: .../src/asistente_codigo_local/web_ui/app.py
# El paquete 'asistente_codigo_local' está en: .../src/asistente_codigo_local/
# Necesitamos añadir el directorio '.../src/' a sys.path
# para que Python pueda encontrar 'asistente_codigo_local' como un paquete de primer nivel.

# Sube dos niveles desde la ubicación de app.py (web_ui/) para llegar a la carpeta 'src/'
PATH_TO_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

if PATH_TO_SRC_DIR not in sys.path:
    sys.path.insert(0, PATH_TO_SRC_DIR)
# --- FIN DE SECCIÓN CORREGIDA ---

from asistente_codigo_local.gpo.orchestrator import GestorPeticionesOrquestacion
from asistente_codigo_local.mlm.mlm_logger import ModuloLogging

app = Flask(__name__)
app.secret_key = os.urandom(32) 

logger_web = ModuloLogging.get_logger("WEB_UI_FLASK")

# --- Configuración del Directorio del Proyecto para el GPO ---
# El GPO necesita saber sobre qué directorio de proyecto va a operar.
# DEFAULT_PROJECT_DIRECTORY debería ser la raíz de la estructura que el asistente analizará.
# Si quieres que opere sobre el propio código del asistente (como en las pruebas anteriores),
# sería tres niveles arriba desde app.py
DEFAULT_PROJECT_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
logger_web.info(f"Directorio de proyecto por defecto para la Web UI (operaciones GPO): {DEFAULT_PROJECT_DIRECTORY}")

# ... (el resto de tu archivo app.py como te lo proporcioné antes) ...
# Por ejemplo, la inicialización del GPO:
gpo_instance = GestorPeticionesOrquestacion(ui_confirm_callback=None)
logger_web.warning("GPO inicializado en la Web UI con auto-confirmación de acciones (ui_confirm_callback=None). Esto es para desarrollo y es INSEGURO para operaciones sensibles.")

@app.route('/', methods=['GET'])
def index():
    session.pop('original_request_context', None)
    session.pop('clarification_message_context', None)
    logger_web.debug("Sirviendo página principal, sesión limpiada.")
    # Pasar el DEFAULT_PROJECT_DIRECTORY al template para mostrarlo
    return render_template('index.html', project_dir_display=DEFAULT_PROJECT_DIRECTORY)

@app.route('/ask', methods=['POST'])
def ask_assistant():
    user_prompt = request.form.get('prompt')
    # Usar el directorio fijo para las operaciones del GPO
    project_dir_for_gpo = DEFAULT_PROJECT_DIRECTORY 
    # ... (el resto de la función /ask como antes, asegurándose de que `project_dir_for_gpo` 
    # se pase a `gpo_instance.procesar_peticion_usuario`) ...
    # Ejemplo:
    # final_prompt_to_gpo = user_prompt
    # ... (lógica de aclaración) ...
    # gpo_response = gpo_instance.procesar_peticion_usuario(final_prompt_to_gpo, project_dir_for_gpo)


    if not user_prompt:
        logger_web.warning("Petición recibida sin prompt.")
        return jsonify({"type": "error", "data": "La petición está vacía."}), 400
    
    # Usar DEFAULT_PROJECT_DIRECTORY para las operaciones del GPO
    if not os.path.isdir(DEFAULT_PROJECT_DIRECTORY): # Validar el directorio que usará el GPO
        logger_web.error(f"Directorio de proyecto (para GPO) no válido o no encontrado: {DEFAULT_PROJECT_DIRECTORY}")
        return jsonify({"type": "error", "data": f"Directorio de proyecto (para GPO) configurado no es válido: {DEFAULT_PROJECT_DIRECTORY}"}), 500

    final_prompt_to_gpo = user_prompt
    is_clarification_response = False
    original_req_for_clarif_context = "" # Para guardar el request original si hay aclaración

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
        logger_web.info(f"Nueva petición web: Prompt='{user_prompt}', Dir GPO='{DEFAULT_PROJECT_DIRECTORY}'")

    try:
        # Pasar DEFAULT_PROJECT_DIRECTORY al GPO
        gpo_response = gpo_instance.procesar_peticion_usuario(final_prompt_to_gpo, DEFAULT_PROJECT_DIRECTORY)

        if gpo_response.get("type") == "clarification_needed":
            logger_web.info(f"GPO solicita aclaración: {gpo_response.get('message')}")
            session['original_request_context'] = gpo_response.get('original_request', user_prompt if not is_clarification_response else original_req_for_clarif_context)
            session['clarification_message_context'] = gpo_response.get('message')
        
        return jsonify(gpo_response)

    except Exception as e:
        logger_web.error(f"Excepción no controlada en /ask: {e}", exc_info=True)
        return jsonify({"type": "error", "data": f"Error interno del servidor al procesar la petición: {str(e)}"}), 500

if __name__ == '__main__':
    log_dir = os.path.join(os.path.expanduser("~"), ".asistente_codigo_local")
    os.makedirs(log_dir, exist_ok=True)
    
    logger_web.info("--- Iniciando Web UI del Asistente de Código Local ---")
    # Pasa el project_dir_display al contexto global para que esté disponible en index() sin error la primera vez
    app.jinja_env.globals.update(project_dir_display=DEFAULT_PROJECT_DIRECTORY)
    app.run(debug=True, port=5001)