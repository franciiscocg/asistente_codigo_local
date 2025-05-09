# Asistente de Código Local - Intérprete de Acciones de Gemini (IAG)

import json
import os

# Placeholder para futuras importaciones (ej. logger)
# from ..mlm import ModuloLogging

class InterpreteAccionesGemini:
    def __init__(self):
        # self.logger = ModuloLogging.get_logger() # Cuando MLM esté disponible
        print("IAG: Inicializado")
        self.directorio_proyecto_base = None

    def set_directorio_proyecto(self, directorio_proyecto):
        """Establece el directorio base del proyecto para validaciones de ruta."""
        if not os.path.isdir(directorio_proyecto):
            # self.logger.error(f"IAG: El directorio del proyecto no existe: {directorio_proyecto}")
            raise ValueError(f"El directorio del proyecto especificado no existe: {directorio_proyecto}")
        self.directorio_proyecto_base = os.path.abspath(directorio_proyecto)
        print(f"IAG: Directorio de proyecto base establecido en: {self.directorio_proyecto_base}")

    def interpretar_respuesta(self, respuesta_gemini: dict) -> list:
        """Analiza la respuesta de Gemini y la valida para convertirla en un plan de acciones."""
        # self.logger.info(f"IAG: Interpretando respuesta de Gemini: {str(respuesta_gemini)[:200]}...")
        print(f"IAG: Interpretando respuesta: {respuesta_gemini}")

        if not isinstance(respuesta_gemini, dict):
            # self.logger.error(f"IAG: La respuesta de Gemini no es un diccionario: {type(respuesta_gemini)}")
            print(f"IAG: Error - La respuesta de Gemini no es un diccionario: {type(respuesta_gemini)}")
            return []

        if "error" in respuesta_gemini:
            # self.logger.error(f"IAG: La respuesta de Gemini contiene un error: {respuesta_gemini['error']}")
            print(f"IAG: Error en la respuesta de Gemini: {respuesta_gemini['error']}")
            # Podríamos querer propagar este error de alguna manera
            return []

        acciones_propuestas = respuesta_gemini.get("actions")
        if not acciones_propuestas or not isinstance(acciones_propuestas, list):
            # self.logger.warning("IAG: No se encontraron acciones válidas en la respuesta de Gemini.")
            print("IAG: No se encontraron acciones válidas o la lista de acciones está malformada.")
            return []

        plan_acciones_validado = []
        for accion in acciones_propuestas:
            if self.validar_accion(accion):
                # self.logger.info(f"IAG: Acción validada: {accion['type']}")
                plan_acciones_validado.append(accion)
            else:
                # self.logger.warning(f"IAG: Acción inválida o no permitida descartada: {accion}")
                print(f"IAG: Acción inválida descartada: {accion.get('type', 'DESCONOCIDO')}")
        
        print(f"IAG: Plan de acciones validado: {plan_acciones_validado}")
        return plan_acciones_validado

    def validar_accion(self, accion: dict) -> bool:
        """Valida una acción individual propuesta por Gemini."""
        if not isinstance(accion, dict) or "type" not in accion:
            # self.logger.warning("IAG: Acción malformada, falta tipo o no es diccionario.")
            return False

        tipo_accion = accion["type"]
        # self.logger.debug(f"IAG: Validando acción de tipo: {tipo_accion}")

        if tipo_accion in ["CREATE_FILE", "MODIFY_FILE", "DELETE_FILE"]:
            if "path" not in accion or not isinstance(accion["path"], str):
                # self.logger.warning(f"IAG: Acción de archivo {tipo_accion} sin ruta válida.")
                return False
            if not self.es_ruta_segura(accion["path"]):
                # self.logger.error(f"IAG: ¡ALERTA DE SEGURIDAD! Intento de acceso a ruta no segura: {accion['path']}")
                print(f"IAG: ¡ALERTA DE SEGURIDAD! Ruta no segura: {accion['path']}")
                return False
            if tipo_accion in ["CREATE_FILE", "MODIFY_FILE"] and "content" not in accion:
                 # self.logger.warning(f"IAG: Acción {tipo_accion} sin contenido.")
                 return False # Podría permitirse MODIFY_FILE sin content si se usa diff, pero no para este ejemplo
            return True
        
        elif tipo_accion == "EXECUTE_COMMAND":
            if "command" not in accion or not isinstance(accion["command"], str):
                # self.logger.warning("IAG: Acción EXECUTE_COMMAND sin comando válido.")
                return False
            # Aquí iría una validación más robusta del comando (lista blanca, análisis de peligrosidad)
            # Por ahora, una validación simple para evitar comandos muy obvios y peligrosos
            comando_lower = accion["command"].lower()
            comandos_peligrosos = ["rm -rf", "sudo", ":(){:|:&};:", "mkfs"]
            if any(peligroso in comando_lower for peligroso in comandos_peligrosos):
                # self.logger.error(f"IAG: ¡ALERTA DE SEGURIDAD! Intento de ejecutar comando peligroso: {accion['command']}")
                print(f"IAG: ¡ALERTA DE SEGURIDAD! Comando peligroso detectado: {accion['command']}")
                return False
            return True

        elif tipo_accion in ["REQUEST_CLARIFICATION", "INFO_MESSAGE"]:
            if "message_to_user" not in accion:
                # self.logger.warning(f"IAG: Acción {tipo_accion} sin message_to_user.")
                return False
            return True
        
        # self.logger.warning(f"IAG: Tipo de acción desconocido o no soportado: {tipo_accion}")
        return False

    def es_ruta_segura(self, ruta_relativa: str) -> bool:
        """Verifica que la ruta sea relativa y confinada al directorio del proyecto."""
        if not self.directorio_proyecto_base:
            # self.logger.error("IAG: No se ha establecido el directorio del proyecto para validar rutas.")
            raise ValueError("Directorio de proyecto base no establecido en IAG.")

        # Evitar rutas absolutas en la entrada de Gemini
        if os.path.isabs(ruta_relativa):
            # self.logger.warning(f"IAG: Ruta absoluta proporcionada por Gemini: {ruta_relativa}")
            return False

        ruta_completa_objetivo = os.path.abspath(os.path.join(self.directorio_proyecto_base, ruta_relativa))
        
        # Verificar que la ruta completa esté dentro del directorio base del proyecto
        if not ruta_completa_objetivo.startswith(self.directorio_proyecto_base):
            # self.logger.error(f"IAG: Intento de acceso fuera del directorio del proyecto: {ruta_completa_objetivo} vs {self.directorio_proyecto_base}")
            return False
        
        return True

# Ejemplo de uso (se movería a pruebas o al GPO)
if __name__ == "__main__":
    iag_instance = InterpreteAccionesGemini()
    
    # Crear un directorio de proyecto de prueba
    test_project_dir = "/home/ubuntu/test_iag_project"
    if not os.path.exists(test_project_dir):
        os.makedirs(test_project_dir)
    iag_instance.set_directorio_proyecto(test_project_dir)

    respuesta_gemini_test = {
        "summary": "Plan de prueba para IAG.",
        "actions": [
            {"type": "CREATE_FILE", "path": "nuevo.txt", "content": "Hola"},
            {"type": "MODIFY_FILE", "path": "existente.txt", "content": "Modificado"},
            {"type": "DELETE_FILE", "path": "a_borrar.txt"},
            {"type": "EXECUTE_COMMAND", "command": "echo \"Comando seguro\""},
            {"type": "EXECUTE_COMMAND", "command": "rm -rf /home/test"}, # Debería ser rechazado
            {"type": "CREATE_FILE", "path": "../fuera_del_proyecto.txt", "content": "Oops"}, # Debería ser rechazado
            {"type": "CREATE_FILE", "path": "/etc/passwd", "content": "Oops"}, # Debería ser rechazado
            {"type": "MALFORMED_ACTION"},
            {"type": "REQUEST_CLARIFICATION", "message_to_user": "¿Estás seguro?"}
        ]
    }
    plan = iag_instance.interpretar_respuesta(respuesta_gemini_test)
    print("--- Plan de Acciones Validado por IAG ---")
    for accion_validada in plan:
        print(accion_validada)
    
    # Limpiar directorio de prueba
    # import shutil
    # shutil.rmtree(test_project_dir)

