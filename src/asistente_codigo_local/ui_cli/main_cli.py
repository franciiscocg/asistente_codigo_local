# Asistente de Código Local - Módulo UI/CLI

import argparse
import os
import json # Para mostrar el plan de acciones de forma legible

# Ajustar la ruta para importar desde el directorio raíz del proyecto src
import sys
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "..") # Sube dos niveles desde ui_cli/main_cli.py a src/
sys.path.append(SRC_DIR) # Añade el directorio src, que contiene el paquete asistente_codigo_local

from asistente_codigo_local.gpo.orchestrator import GestorPeticionesOrquestacion
from asistente_codigo_local.mlm.mlm_logger import ModuloLogging # Para inicializar logging si es necesario

# Inicializar logger para la UI
logger_cli = ModuloLogging.get_logger("UI_CLI")

def solicitar_confirmacion_acciones_cli(plan_acciones: list) -> bool:
    """Muestra el plan de acciones al usuario y solicita confirmación."""
    logger_cli.info("Mostrando plan de acciones para confirmación del usuario.")
    print("\n---------- PLAN DE ACCIONES PROPUESTO ----------")
    if not plan_acciones:
        print("No se proponen acciones.")
        print("--------------------------------------------")
        return False # No hay nada que confirmar

    for i, accion in enumerate(plan_acciones):
        print(f"\nAcción #{i+1}: {accion.get('type')}")
        description = accion.get('description', 'N/A')
        print(f"  Descripción: {description}")
        if accion.get("path"):
            print(f"  Ruta: {accion.get('path')}")
        if accion.get("command"):
            print(f"  Comando: {accion.get('command')}")
        if accion.get("content"):         # Mostrar solo un resumen del contenido si es muy largo
            content_summary = accion.get("content", "")
            if len(content_summary) > 150:
                content_summary = content_summary[:150] + "... (contenido truncado)"
            print(f"  Contenido: {content_summary}")
        if accion.get("message_to_user") and accion.get("type") != "INFO_MESSAGE": # Los INFO_MESSAGE se mostrarán después
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

    # Inicializar el GPO con el callback de confirmación de la UI
    gpo = GestorPeticionesOrquestacion(ui_confirm_callback=solicitar_confirmacion_acciones_cli)

    if args.prompt:
        user_input = args.prompt
        logger_cli.info(f"Recibido prompt desde argumento: {user_input}")
        print(f"\nProcesando su solicitud: {user_input}")
        resultado = gpo.procesar_peticion_usuario(user_input, directorio_proyecto_abs)
        print("\n---------- RESULTADO DEL ASISTENTE ----------")
        print(resultado)
        print("-------------------------------------------")
    else:
        print("\nBienvenido al Asistente de Código Local. Escriba su petición o 'salir' para terminar.")
        while True:
            try:
                user_input = input("\nTu petición: ").strip()
                if user_input.lower() == "salir":
                    logger_cli.info("Usuario solicitó salir.")
                    print("Saliendo del Asistente de Código Local.")
                    break
                if not user_input:
                    continue
                
                logger_cli.info(f"Recibida petición interactiva: {user_input}")
                print(f"Procesando: {user_input}")
                resultado = gpo.procesar_peticion_usuario(user_input, directorio_proyecto_abs)
                print("\n---------- RESULTADO DEL ASISTENTE ----------")
                print(resultado)
                print("-------------------------------------------")

            except KeyboardInterrupt:
                logger_cli.info("Sesión interactiva interrumpida por el usuario.")
                print("\nSaliendo del Asistente de Código Local.")
                break
            except Exception as e:
                logger_cli.error(f"Error inesperado en el bucle principal de la UI: {e}", exc_info=True)
                print(f"Ha ocurrido un error inesperado: {e}")

if __name__ == "__main__":
    # Crear directorio de logs si no existe, basado en la configuración de MLM
    log_dir = os.path.join(os.path.expanduser("~"), ".asistente_codigo_local")
    os.makedirs(log_dir, exist_ok=True)
    logger_cli.info("--- Asistente de Código Local CLI Iniciado ---")
    main()
    logger_cli.info("--- Asistente de Código Local CLI Terminado ---")

