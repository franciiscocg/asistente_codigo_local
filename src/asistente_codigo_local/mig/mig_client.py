# Asistente de Código Local - Módulo de Interacción con Gemini (MIG)

import json
import os
import requests # Para la API real de Gemini

# Cargar la configuración que contiene la API Key
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "core", "config.json")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

class ModuloInteraccionGemini:
    def __init__(self, use_mock=False, mock_api_instance=None):
        self.use_mock = use_mock
        self.api_key = None
        # self.logger = ModuloLogging.get_logger("MIGModule") # Cuando MLM esté integrado

        if self.use_mock:
            if mock_api_instance:
                self.mock_api = mock_api_instance
                print("MIG: Inicializado con Mock API proporcionada.")
                # self.logger.info("MIG: Inicializado con Mock API proporcionada.")
            else:
                # Crear un mock por defecto si no se provee uno y use_mock es True
                self.mock_api = self._default_mock_api()
                print("MIG: Inicializado con Mock API por defecto.")
                # self.logger.info("MIG: Inicializado con Mock API por defecto.")
        else:
            try:
                with open(CONFIG_FILE_PATH, "r") as f:
                    config = json.load(f)
                    self.api_key = config.get("GEMINI_API_KEY")
                if not self.api_key:
                    print("MIG: ERROR - Clave API de Gemini no encontrada en config.json. Revirtiendo a mock.")
                    # self.logger.error("MIG: Clave API de Gemini no encontrada en config.json. Revirtiendo a mock.")
                    self.use_mock = True
                    self.mock_api = self._default_mock_api()
                else:
                    print("MIG: Inicializado para usar API Real de Gemini.")
                    # self.logger.info("MIG: Inicializado para usar API Real de Gemini.")
            except FileNotFoundError:
                print(f"MIG: ERROR - Archivo de configuración no encontrado en {CONFIG_FILE_PATH}. Revirtiendo a mock.")
                # self.logger.error(f"MIG: Archivo de configuración no encontrado en {CONFIG_FILE_PATH}. Revirtiendo a mock.")
                self.use_mock = True
                self.mock_api = self._default_mock_api()
            except json.JSONDecodeError:
                print(f"MIG: ERROR - Error decodificando config.json. Revirtiendo a mock.")
                # self.logger.error(f"MIG: Error decodificando config.json. Revirtiendo a mock.")
                self.use_mock = True
                self.mock_api = self._default_mock_api()

    def _default_mock_api(self):
        # self.logger.info("MIG: Usando mock API por defecto.")
        class DefaultMock:
            def generate_content(self, prompt, contexto):
                print(f"MIG (DefaultMock): Recibido prompt: {prompt[:50]}...")
                return {"summary": "Respuesta del Mock API por defecto. Configure la API real.", "actions": []}
        return DefaultMock()

    def set_mock_api(self, mock_api_instance):
        self.mock_api = mock_api_instance
        self.use_mock = True
        print("MIG: Instancia de Mock API establecida. Se usará el mock.")
        # self.logger.info("MIG: Instancia de Mock API establecida. Se usará el mock.")

    def enviar_a_gemini(self, prompt_usuario: str, contexto_proyecto: dict) -> dict:
        """Prepara el prompt y lo envía a la API de Gemini (real o mock)."""
        # self.logger.info(f"MIG: Enviando petición. Mock: {self.use_mock}. Prompt: {prompt_usuario[:100]}...")
        print(f"MIG: Enviando petición a Gemini (Mock: {self.use_mock}).")

        prompt_parts = [
            {"text": "Eres 'Asistente de Código Local', una IA experta en desarrollo de software. Tu propósito es ayudar a los usuarios a modificar sus proyectos de código. Puedes proponer la creación de nuevos archivos, la modificación de archivos existentes (proporcionando el contenido completo o un parche en formato diff unificado), la eliminación de archivos y la ejecución de comandos de consola dentro del directorio del proyecto."},
            {"text": "Todas tus respuestas deben estar estrictamente en formato JSON, siguiendo este esquema: {\"summary\": \"Descripción de lo que harán las acciones...\", \"actions\": [{\"type\": \"ACTION_TYPE\", ...}]}. No incluyas explicaciones o texto fuera del objeto JSON principal."},
            {"text": "Los tipos de acción válidos son: CREATE_FILE, MODIFY_FILE, DELETE_FILE, EXECUTE_COMMAND, REQUEST_CLARIFICATION, INFO_MESSAGE."},
            {"text": "Para MODIFY_FILE, proporciona el contenido completo del archivo modificado."},
            {"text": "Todas las rutas de archivo deben ser relativas al directorio raíz del proyecto. No sugieras comandos que operen fuera de este directorio o que sean inherentemente destructivos sin una justificación muy clara. Prioriza la seguridad y la reversibilidad de las acciones."},
            {"text": "Si la solicitud del usuario es ambigua o necesitas más información para proceder de manera segura y efectiva, utiliza la acción REQUEST_CLARIFICATION."},
            {"text": "--- INICIO CONTEXTO DEL PROYECTO ---"},
            {"text": json.dumps(contexto_proyecto, indent=2, ensure_ascii=False)},
            {"text": "--- FIN CONTEXTO DEL PROYECTO ---"},
            {"text": f"Usuario: {prompt_usuario}"},
            {"text": "Asistente (Respuesta JSON esperada):"}
        ]
        
        payload = {
            "contents": [{"role": "user", "parts": prompt_parts}],
            "generationConfig": {
                "temperature": 0.2, 
                "topK": 1,
                "topP": 0.95,
                "maxOutputTokens": 8192, # Aumentado para permitir respuestas más largas / código
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
        }

        respuesta_final_parseada = {}

        if self.use_mock:
            if not self.mock_api:
                # self.logger.error("MIG: Se intenta usar Mock API pero no hay instancia.")
                raise ValueError("MIG: Mock API no configurada y use_mock es True.")
            respuesta_bruta = self.mock_api.generate_content(prompt_usuario, contexto_proyecto)
            # El mock debe devolver directamente el diccionario de acciones o un string JSON
            if isinstance(respuesta_bruta, dict):
                respuesta_final_parseada = respuesta_bruta
            elif isinstance(respuesta_bruta, str):
                try:
                    respuesta_final_parseada = json.loads(respuesta_bruta)
                except json.JSONDecodeError as e:
                    # self.logger.error(f"MIG (Mock): Error decodificando JSON: {e}. Respuesta: {respuesta_bruta}")
                    return {"error": "Mock Error decodificando JSON", "details": str(e), "raw_response": respuesta_bruta}
            else:
                return {"error": "Mock Error: tipo de respuesta no esperado del mock.", "raw_response": str(respuesta_bruta)}
        else:
            if not self.api_key:
                # self.logger.error("MIG: Intento de usar API real sin clave API configurada.")
                return {"error": "API real no utilizable, clave API no configurada."}
            
            headers = {"Content-Type": "application/json"}
            params = {"key": self.api_key}
            
            try:
                # self.logger.debug(f"MIG: Enviando payload a API real: {json.dumps(payload, indent=2)[:500]}...")
                print(f"MIG: Enviando payload a API real (tamaño: {len(json.dumps(payload))} bytes)")
                response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload, timeout=120) # Timeout 120s
                response.raise_for_status()
                respuesta_api = response.json()
                # self.logger.debug(f"MIG: Respuesta cruda de API real: {json.dumps(respuesta_api, indent=2)[:500]}...")
                print(f"MIG: Respuesta cruda de API real recibida.")

                # Extraer el contenido de la respuesta de Gemini API v1beta
                if (respuesta_api.get("candidates") and 
                   isinstance(respuesta_api["candidates"], list) and 
                   len(respuesta_api["candidates"]) > 0 and 
                   respuesta_api["candidates"][0].get("content") and 
                   respuesta_api["candidates"][0]["content"].get("parts") and 
                   isinstance(respuesta_api["candidates"][0]["content"]["parts"], list) and 
                   len(respuesta_api["candidates"][0]["content"]["parts"]) > 0 and 
                   respuesta_api["candidates"][0]["content"]["parts"][0].get("text")):
                    
                    texto_respuesta_gemini = respuesta_api["candidates"][0]["content"]["parts"][0]["text"]
                    # self.logger.info("MIG: Texto extraído de la respuesta de Gemini.")
                    print("MIG: Texto extraído de la respuesta de Gemini.")
                    
                    # El texto puede estar envuelto en ```json ... ``` o ser JSON directamente
                    if texto_respuesta_gemini.strip().startswith("```json"):
                        json_str = texto_respuesta_gemini.strip()[7:-3].strip()
                    elif texto_respuesta_gemini.strip().startswith("```"):
                        json_str = texto_respuesta_gemini.strip()[3:-3].strip()
                    else:
                        json_str = texto_respuesta_gemini
                    
                    respuesta_final_parseada = json.loads(json_str)
                else:
                    # self.logger.error(f"MIG: Formato de respuesta inesperado de Gemini API: {respuesta_api}")
                    return {"error": "Formato de respuesta inesperado de Gemini API", "raw_response": respuesta_api}

            except requests.exceptions.RequestException as e:
                # self.logger.error(f"MIG: Error de conexión con API de Gemini: {e}")
                return {"error": "Error de conexión con API de Gemini", "details": str(e)}
            except json.JSONDecodeError as e:
                # self.logger.error(f"MIG: Error decodificando JSON de API real: {e}. Respuesta: {texto_respuesta_gemini if 'texto_respuesta_gemini' in locals() else 'No disponible'}")
                return {"error": "Error decodificando JSON de API real", "details": str(e), "raw_response": texto_respuesta_gemini if 'texto_respuesta_gemini' in locals() else 'Respuesta no disponible o error previo'}
            except Exception as e:
                # self.logger.error(f"MIG: Error inesperado durante llamada a API real: {e}", exc_info=True)
                return {"error": "Error inesperado durante llamada a API real", "details": str(e)}

        # self.logger.info(f"MIG: Respuesta final parseada: {str(respuesta_final_parseada)[:200]}...")
        print(f"MIG: Respuesta final parseada obtenida.")
        return respuesta_final_parseada

# Ejemplo de uso (se movería a pruebas o al GPO)
if __name__ == "__main__":
    # Para probar la API real, asegúrate de que config.json exista con tu clave
    # y cambia use_mock a False.
    # Ejemplo: Crear /home/ubuntu/asistente_codigo_local/src/asistente_codigo_local/core/config.json
    # con { "GEMINI_API_KEY": "TU_CLAVE_AQUI" }
    
    # Prueba con Mock
    print("--- Probando con Mock API ---")
    mig_client_mock = ModuloInteraccionGemini(use_mock=True)
    test_prompt_mock = "Crear archivo de prueba llamado test_file.txt con mock"
    test_contexto_mock = {"directorio_actual": "/test_mock"}
    respuesta_mock = mig_client_mock.enviar_a_gemini(test_prompt_mock, test_contexto_mock)
    print("Respuesta del MIG (Mock):")
    print(json.dumps(respuesta_mock, indent=2))

    # Prueba con API Real (requiere config.json y clave válida)
    print("\n--- Probando con API Real de Gemini (requiere config.json y clave válida) ---")
    # Asegúrate de que el path a config.json sea correcto relativo a este script si lo ejecutas directamente
    # Para que funcione como está, ejecuta desde el directorio raíz del proyecto: 
    # python -m asistente_codigo_local.mig.mig_client
    # O ajusta CONFIG_FILE_PATH para pruebas directas.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE_PATH = os.path.join(current_dir, "..", "core", "config.json") # Reajustar para ejecución directa
    
    mig_client_real = ModuloInteraccionGemini(use_mock=False)
    if not mig_client_real.use_mock: # Solo intentar si no revirtió a mock
        test_prompt_real = "Escribe un poema corto sobre la programación en Python. Solo el poema, sin explicaciones."
        test_contexto_real = {"lenguaje_favorito": "Python"}
        print(f"Enviando a API real con prompt: {test_prompt_real}")
        respuesta_real = mig_client_real.enviar_a_gemini(test_prompt_real, test_contexto_real)
        print("Respuesta del MIG (Real API):")
        print(json.dumps(respuesta_real, indent=2))
    else:
        print("No se pudo probar la API real, MIG revirtió a mock (probablemente falta config.json o API Key).")

