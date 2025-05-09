# Asistente de Código Local - Módulo UI/CLI

import argparse
import os
import json # Para mostrar el plan de acciones de forma legible

# En asistente_codigo_local/ui_cli/main_cli.py
# ... (importaciones existentes) ...
import sys # Asegúrate de que sys esté importado si ajustas path
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "..") 
sys.path.append(SRC_DIR) 

from asistente_codigo_local.gpo.orchestrator import GestorPeticionesOrquestacion
from asistente_codigo_local.mlm.mlm_logger import ModuloLogging

logger_cli = ModuloLogging.get_logger("UI_CLI")

# ... (función solicitar_confirmacion_acciones_cli existente sin cambios necesarios por ahora) ...
def solicitar_confirmacion_acciones_cli(plan_acciones: list) -> bool:
    logger_cli.info("Mostrando plan de acciones para confirmación del usuario.")
    print("\n---------- PLAN DE ACCIONES PROPUESTO ----------")
    if not plan_acciones:
        print("No se proponen acciones.")
        print("--------------------------------------------")
        return False 

    for i, accion in enumerate(plan_acciones):
        print(f"\nAcción #{i+1}: {accion.get('type')}")
        description = accion.get('description', 'N/A')
        print(f"  Descripción: {description}")
        if accion.get("path"):
            print(f"  Ruta: {accion.get('path')}")
        if accion.get("command"):
            print(f"  Comando: {accion.get('command')}")
        if accion.get("content"):         
            content_summary = accion.get("content", "")
            if len(content_summary) > 150:
                content_summary = content_summary[:150] + "... (contenido truncado)"
            print(f"  Contenido: {content_summary}")
        # No mostramos message_to_user aquí si es REQUEST_CLARIFICATION, se maneja después
        if accion.get("message_to_user") and accion.get("type") not in ["INFO_MESSAGE", "REQUEST_CLARIFICATION"]: 
            print(f"  Mensaje de Gemini: {accion.get('message_to_user')}")

    print("--------------------------------------------")
    
    while True:
        try:
            confirmacion = input("¿Aprobar y ejecutar estas acciones? (s/N): ").strip().lower()
            if confirmacion == "s":
                logger_cli.info("Usuario aprobó las acciones.")
                return True
            elif confirmacion == "n" or confirmacion == "":
                logger_cli.info("Usuario rechazó las acciones.")
                return False
            else:
                print("Respuesta no válida. Por favor, ingrese 's' para sí o 'n' para no.")
        except KeyboardInterrupt:
            logger_cli.info("Confirmación interrumpida por el usuario.")
            print("\nConfirmación cancelada.")
            return False

def main():
    parser = argparse.ArgumentParser(description="Asistente de Código Local potenciado por Gemini.")
    parser.add_argument("prompt", nargs="?", help="El prompt o la tarea a realizar.")
    parser.add_argument("--directorio_proyecto", "-d", default=os.getcwd(), help="Ruta al directorio del proyecto. Por defecto es el directorio actual.")
    
    args = parser.parse_args()
    
    directorio_proyecto_abs = os.path.abspath(args.directorio_proyecto)
    if not os.path.isdir(directorio_proyecto_abs):
        print(f"Error: El directorio del proyecto especificado no existe: {directorio_proyecto_abs}")
        logger_cli.error(f"Directorio de proyecto no válido: {directorio_proyecto_abs}")
        return

    logger_cli.info(f"Asistente iniciado. Directorio de proyecto: {directorio_proyecto_abs}")
    print(f"Usando directorio del proyecto: {directorio_proyecto_abs}")

    gpo = GestorPeticionesOrquestacion(ui_confirm_callback=solicitar_confirmacion_acciones_cli)

    # Variable para mantener el contexto de la petición original entre aclaraciones
    peticion_original_para_contexto = ""

    if args.prompt:
        user_input = args.prompt
        peticion_original_para_contexto = user_input # Guardar para posible aclaración
        logger_cli.info(f"Recibido prompt desde argumento: {user_input}")
        print(f"\nProcesando su solicitud: {user_input}")
        
        respuesta_gpo = gpo.procesar_peticion_usuario(user_input, directorio_proyecto_abs)
        # Procesar la respuesta (esta lógica se repite, podría ir a una función)
        if respuesta_gpo.get("type") == "clarification_needed":
            print("\n---------- ACLARACIÓN REQUERIDA ----------")
            clarification_message = respuesta_gpo.get("message")
            print(f"Gemini dice: {clarification_message}")
            print("Lamentablemente, el modo de argumento único no soporta aclaraciones interactivas en esta versión.")
            print("Por favor, intente una petición más específica o use el modo interactivo.")
        elif respuesta_gpo.get("type") == "results":
            print("\n---------- RESULTADO DEL ASISTENTE ----------")
            print(respuesta_gpo.get("data"))
            print("-------------------------------------------")
        elif respuesta_gpo.get("type") == "error":
            print("\n---------- ERROR DEL ASISTENTE ----------")
            print(respuesta_gpo.get("data"))
            print("-------------------------------------------")
        else:
            print("\n---------- RESPUESTA DESCONOCIDA DEL ASISTENTE ----------")
            print(str(respuesta_gpo))
            print("-------------------------------------------------------")
    else:
        print("\nBienvenido al Asistente de Código Local. Escriba su petición o 'salir' para terminar.")
        # Mantener la última petición original en caso de necesitar aclaración
        ultima_peticion_original_valida = ""

        while True:
            try:
                user_input = input("\nTu petición: ").strip()
                if user_input.lower() == "salir":
                    logger_cli.info("Usuario solicitó salir.")
                    print("Saliendo del Asistente de Código Local.")
                    break
                if not user_input:
                    continue
                
                ultima_peticion_original_valida = user_input # Actualizar la petición válida más reciente
                
                logger_cli.info(f"Recibida petición interactiva: {ultima_peticion_original_valida}")
                print(f"Procesando: {ultima_peticion_original_valida}")
                
                respuesta_gpo = gpo.procesar_peticion_usuario(ultima_peticion_original_valida, directorio_proyecto_abs)

                if respuesta_gpo.get("type") == "clarification_needed":
                    print("\n---------- ACLARACIÓN REQUERIDA ----------")
                    clarification_message = respuesta_gpo.get("message", "El asistente necesita más información.")
                    original_request_context = respuesta_gpo.get("original_request", ultima_peticion_original_valida)
                    summary_gemini_clarif = respuesta_gpo.get("summary_gemini","")
                    if summary_gemini_clarif:
                        print(f"Resumen de Gemini (solicitando aclaración): {summary_gemini_clarif}")

                    print(f"\nGemini dice: {clarification_message}")
                    
                    respuesta_usuario_aclaracion = input("Tu respuesta a la aclaración (o 'cancelar'): ").strip()

                    if respuesta_usuario_aclaracion.lower() == "cancelar":
                        print("Aclaración cancelada.")
                        continue
                    
                    if respuesta_usuario_aclaracion:
                        prompt_con_aclaracion = (
                            f"Referente a la petición anterior: \"{original_request_context}\".\n"
                            f"Se solicitó la siguiente aclaración: \"{clarification_message}\".\n"
                            f"El usuario ha respondido: \"{respuesta_usuario_aclaracion}\".\n"
                            f"Por favor, intenta procesar la petición original de nuevo con esta información adicional y genera un plan de acciones ejecutable."
                        )
                        logger_cli.info(f"Enviando nueva petición con aclaración: {prompt_con_aclaracion[:200]}...") # Log truncado
                        print(f"\nProcesando con tu aclaración...")
                        
                        # Actualizar ultima_peticion_original_valida para que si hay otra aclaración, el contexto sea el acumulado.
                        ultima_peticion_original_valida = prompt_con_aclaracion
                        respuesta_gpo = gpo.procesar_peticion_usuario(prompt_con_aclaracion, directorio_proyecto_abs)
                        # Volvemos al inicio del bucle de procesamiento de respuesta_gpo
                        # Esto significa que necesitamos un bucle interno o refactorizar el manejo de respuesta_gpo

                # Bucle para manejar respuestas del GPO (incluyendo aclaraciones anidadas)
                while respuesta_gpo.get("type") == "clarification_needed":
                    print("\n---------- ACLARACIÓN REQUERIDA ----------")
                    clarification_message = respuesta_gpo.get("message", "El asistente necesita más información.")
                    original_request_context = respuesta_gpo.get("original_request", ultima_peticion_original_valida)
                    summary_gemini_clarif = respuesta_gpo.get("summary_gemini","")
                    if summary_gemini_clarif:
                        print(f"Resumen de Gemini (solicitando aclaración): {summary_gemini_clarif}")
                    print(f"\nGemini dice: {clarification_message}")
                    
                    respuesta_usuario_aclaracion = input("Tu respuesta a la aclaración (o 'cancelar'): ").strip()

                    if respuesta_usuario_aclaracion.lower() == "cancelar":
                        print("Aclaración cancelada.")
                        # Romper el bucle de aclaraciones y esperar nueva petición
                        respuesta_gpo = {"type": "info", "data": "Proceso de aclaración cancelado."} 
                        break 
                    
                    if respuesta_usuario_aclaracion:
                        prompt_con_aclaracion = (
                            f"Referente a la petición anterior: \"{original_request_context}\".\n"
                            f"Se solicitó la siguiente aclaración: \"{clarification_message}\".\n"
                            f"El usuario ha respondido: \"{respuesta_usuario_aclaracion}\".\n"
                            f"Por favor, intenta procesar la petición original de nuevo con esta información adicional y genera un plan de acciones ejecutable."
                        )
                        logger_cli.info(f"Enviando nueva petición con aclaración: {prompt_con_aclaracion[:200]}...")
                        print(f"\nProcesando con tu aclaración...")
                        
                        ultima_peticion_original_valida = prompt_con_aclaracion # Acumular contexto
                        respuesta_gpo = gpo.procesar_peticion_usuario(prompt_con_aclaracion, directorio_proyecto_abs)
                    else:
                        print("No se proporcionó aclaración. Intenta la petición de nuevo siendo más específico.")
                        respuesta_gpo = {"type": "info", "data": "Aclaración vacía, no se procesó."}
                        break # Salir del bucle de aclaraciones
                
                # Mostrar el resultado final después de cualquier ciclo de aclaración
                if respuesta_gpo.get("type") == "results":
                    print("\n---------- RESULTADO DEL ASISTENTE ----------")
                    print(respuesta_gpo.get("data"))
                    print("-------------------------------------------")
                elif respuesta_gpo.get("type") == "error":
                    print("\n---------- ERROR DEL ASISTENTE ----------")
                    print(respuesta_gpo.get("data"))
                    print("-------------------------------------------")
                elif respuesta_gpo.get("type") == "info": # Para mensajes como "Aclaración cancelada"
                    print(f"\nInfo: {respuesta_gpo.get('data')}")
                # No imprimir si ya se manejó una aclaración que no resultó en error/results
                elif respuesta_gpo.get("type") != "clarification_needed": 
                    print("\n---------- RESPUESTA DESCONOCIDA DEL ASISTENTE ----------")
                    print(str(respuesta_gpo))
                    print("-------------------------------------------------------")

            except KeyboardInterrupt:
                logger_cli.info("Sesión interactiva interrumpida por el usuario.")
                print("\nSaliendo del Asistente de Código Local.")
                break
            except Exception as e:
                logger_cli.error(f"Error inesperado en el bucle principal de la UI: {e}", exc_info=True)
                print(f"Ha ocurrido un error inesperado: {e}")

if __name__ == "__main__":
    log_dir = os.path.join(os.path.expanduser("~"), ".asistente_codigo_local")
    os.makedirs(log_dir, exist_ok=True)
    # Configurar el logger principal del módulo MLM si se desea un nivel diferente para la consola
    # ModuloLogging.get_logger('').addHandler(ModuloLogging.console_handler) # Ejemplo
    logger_cli.info("--- Asistente de Código Local CLI Iniciado ---")
    main()
    logger_cli.info("--- Asistente de Código Local CLI Terminado ---")