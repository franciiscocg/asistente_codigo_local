# Asistente de Código Local - Gestor de Peticiones y Orquestación (GPO)

import os
import json # Para logging de objetos complejos

from asistente_codigo_local.mig.mig_client import ModuloInteraccionGemini
from asistente_codigo_local.iag.iag_parser import InterpreteAccionesGemini
from asistente_codigo_local.gcp.gcp_manager import GestorContextoProyecto
from asistente_codigo_local.mosa.mosa_ops import ModuloOperacionesSistemaArchivos
from asistente_codigo_local.mecc.mecc_executor import ModuloEjecucionComandosConsola
from asistente_codigo_local.mlm.mlm_logger import ModuloLogging

class GestorPeticionesOrquestacion:
    def __init__(self, ui_confirm_callback=None):
        self.logger = ModuloLogging.get_logger("GPO")
        self.gcp = GestorContextoProyecto()
        self.mig = ModuloInteraccionGemini(use_mock=False) # Por defecto, usar API real ahora
        self.iag = InterpreteAccionesGemini()
        # MOSA y MECC se inicializarán por petición, ya que dependen del directorio del proyecto
        self.mosa = None
        self.mecc = None
        self.ui_confirm_callback = ui_confirm_callback # Callback para confirmación del usuario
        self.logger.info("GPO: Inicializado y listo para usar API real (si está configurada).")

    def _inicializar_modulos_de_sistema(self, directorio_proyecto: str):
        self.logger.info(f"GPO: Inicializando MOSA y MECC para el directorio: {directorio_proyecto}")
        self.mosa = ModuloOperacionesSistemaArchivos(directorio_proyecto_base=directorio_proyecto)
        self.mecc = ModuloEjecucionComandosConsola(directorio_proyecto_base=directorio_proyecto)
        self.iag.set_directorio_proyecto(directorio_proyecto) # Asegurar que IAG conozca el dir

    def procesar_peticion_usuario(self, peticion_texto: str, directorio_proyecto: str) -> str:
        self.logger.info(f"GPO: Petición recibida: ")
        self.logger.info(f"  Texto: {peticion_texto}")
        self.logger.info(f"  Directorio Proyecto: {directorio_proyecto}")

        if not os.path.isdir(directorio_proyecto):
            self.logger.error(f"GPO: El directorio del proyecto no existe: {directorio_proyecto}")
            return f"Error: El directorio del proyecto especificado no existe: {directorio_proyecto}"
        
        self._inicializar_modulos_de_sistema(directorio_proyecto)

        try:
            # 1. Obtener contexto del proyecto (GCP)
            self.logger.info("GPO: Obteniendo contexto del proyecto...")
            contexto = self.gcp.obtener_contexto(directorio_proyecto, peticion_texto)
            # Crear un resumen del contexto para logging de forma más segura
            contexto_summary_for_log = {}
            if isinstance(contexto, dict):
                for k, v in contexto.items():
                    if isinstance(v, dict):
                        contexto_summary_for_log[k] = f"{len(v.keys())} keys"
                    elif isinstance(v, list):
                        contexto_summary_for_log[k] = f"{len(v)} items"
                    else:
                        contexto_summary_for_log[k] = str(v)[:100] # Limitar longitud de strings directos
            else:
                contexto_summary_for_log = {"error": "Contexto no es un diccionario"}
            self.logger.info(f"GPO: Contexto obtenido (resumen): {contexto_summary_for_log}")
            if contexto.get("error"):
                 self.logger.error(f"GPO: Error obteniendo contexto: {contexto.get('error')}")
                 return f"Error al obtener contexto del proyecto: {contexto.get('error')}"

            # 2. Enviar petición y contexto a Gemini (MIG)
            self.logger.info("GPO: Enviando petición a Gemini...")
            respuesta_gemini = self.mig.enviar_a_gemini(peticion_texto, contexto)
            self.logger.info(f"GPO: Respuesta de Gemini (resumen): {str(respuesta_gemini)[:500]}...")
            if respuesta_gemini.get("error"):
                self.logger.error(f"GPO: Error en la respuesta de Gemini: {respuesta_gemini.get('error')}")
                return f"Error en la comunicación con Gemini: {respuesta_gemini.get('error')} - Detalles: {respuesta_gemini.get('details', '')}"

            # 3. Interpretar respuesta y generar plan de acción (IAG)
            self.logger.info("GPO: Interpretando respuesta de Gemini...")
            plan_acciones = self.iag.interpretar_respuesta(respuesta_gemini)
            self.logger.info(f"GPO: Plan de acciones generado: {json.dumps(plan_acciones, indent=2)}")

            if not plan_acciones:
                self.logger.warning("GPO: No se generaron acciones válidas o el plan está vacío.")
                summary = respuesta_gemini.get("summary", "No se pudo generar un plan de acciones.")
                return summary # Devolver el resumen o un mensaje de error

            # 4. Solicitar confirmación al usuario
            if self.ui_confirm_callback:
                self.logger.info("GPO: Solicitando confirmación al usuario para el plan de acciones...")
                if not self.ui_confirm_callback(plan_acciones):
                    self.logger.info("GPO: El usuario canceló las acciones.")
                    return "Operación cancelada por el usuario."
                self.logger.info("GPO: Usuario confirmó las acciones.")
            else:
                self.logger.warning("GPO: No se proporcionó callback de confirmación. Asumiendo SÍ (NO RECOMENDADO PARA PRODUCCIÓN).")
                # En un entorno real, esto debería ser un error o requerir configuración explícita.

            # 5. Ejecutar acciones (MOSA, MECC)
            self.logger.info("GPO: Ejecutando plan de acciones...")
            resultados_ejecucion = self.ejecutar_plan_acciones(plan_acciones, directorio_proyecto)
            self.logger.info(f"GPO: Resultados de la ejecución: {resultados_ejecucion}")
            
            # Formatear resultados para el usuario
            output_para_usuario = []
            summary_gemini = respuesta_gemini.get("summary", "Resumen no disponible.")
            output_para_usuario.append(f"Resumen de Gemini: {summary_gemini}")
            output_para_usuario.append("\nResultados de las acciones ejecutadas:")
            for resultado_accion in resultados_ejecucion:
                output_para_usuario.append(f"- {resultado_accion}")
            return "\n".join(output_para_usuario)

        except Exception as e:
            self.logger.error(f"GPO: Error crítico procesando la petición: {e}", exc_info=True)
            return f"Error crítico en el GPO: {e}"

    def ejecutar_plan_acciones(self, plan_acciones: list, directorio_proyecto: str) -> list:
        resultados = []
        if not self.mosa or not self.mecc:
            self.logger.error("GPO: MOSA o MECC no inicializados antes de ejecutar acciones.")
            resultados.append("Error interno: Módulos de sistema no inicializados.")
            return resultados

        for accion in plan_acciones:
            tipo_accion = accion.get("type")
            resultado_accion = f"Acción {tipo_accion} no reconocida o no ejecutada."
            self.logger.info(f"GPO: Procesando acción: {tipo_accion}")
            try:
                if tipo_accion == "CREATE_FILE":
                    ruta = accion.get("path")
                    contenido = accion.get("content")
                    if ruta and contenido is not None:
                        resultado_accion = self.mosa.crear_archivo(ruta, contenido)
                    else:
                        resultado_accion = "Error: CREATE_FILE requiere 'path' y 'content'."
                elif tipo_accion == "MODIFY_FILE":
                    ruta = accion.get("path")
                    contenido = accion.get("content")
                    if ruta and contenido is not None:
                        resultado_accion = self.mosa.modificar_archivo(ruta, contenido)
                    else:
                        resultado_accion = "Error: MODIFY_FILE requiere 'path' y 'content'."
                elif tipo_accion == "DELETE_FILE":
                    ruta = accion.get("path")
                    if ruta:
                        resultado_accion = self.mosa.eliminar_archivo(ruta)
                    else:
                        resultado_accion = "Error: DELETE_FILE requiere 'path'."
                elif tipo_accion == "EXECUTE_COMMAND":
                    comando = accion.get("command")
                    if comando:
                        res_cmd = self.mecc.ejecutar_comando(comando)
                        resultado_accion = f"Comando: '{comando}'\n  Éxito: {res_cmd['exito']}\n  Salida: {res_cmd['stdout']}\n  Error: {res_cmd['stderr']}"
                    else:
                        resultado_accion = "Error: EXECUTE_COMMAND requiere 'command'."
                elif tipo_accion == "INFO_MESSAGE":
                    resultado_accion = f"Mensaje informativo: {accion.get('message_to_user', 'Sin mensaje.')}"
                elif tipo_accion == "REQUEST_CLARIFICATION":
                     resultado_accion = f"Solicitud de aclaración de Gemini: {accion.get('message_to_user', 'Sin mensaje.')} (Esta funcionalidad requiere más desarrollo en la UI)"
                else:
                    self.logger.warning(f"GPO: Tipo de acción desconocido en ejecución: {tipo_accion}")
                
                self.logger.info(f"GPO: Resultado acción {tipo_accion}: {resultado_accion}")
            except Exception as e:
                self.logger.error(f"GPO: Error ejecutando acción {tipo_accion}: {e}", exc_info=True)
                resultado_accion = f"Error al ejecutar {tipo_accion} en '{accion.get('path', accion.get('command', 'N/A'))}': {e}"
            resultados.append(resultado_accion)
        return resultados

# El if __name__ == "__main__": se eliminará o se moverá a un script de prueba/CLI principal.
# Por ahora, lo comento para evitar ejecuciones accidentales si este archivo es importado.
"""
if __name__ == "__main__":
    # Esta sección es para pruebas rápidas y se integrará con main_cli.py
    # Necesita una función de confirmación de la UI
    def simple_confirm_callback(plan):
        print("\n--- PLAN DE ACCIONES PROPUESTO ---")
        for i, accion_prop in enumerate(plan):
            print(f"{i+1}. Tipo: {accion_prop.get('type')}")
            print(f"   Descripción: {accion_prop.get('description', 'N/A')}")
            if 'path' in accion_prop: print(f"   Ruta: {accion_prop.get('path')}")
            if 'command' in accion_prop: print(f"   Comando: {accion_prop.get('command')}")
            if 'content' in accion_prop: print(f"   Contenido (resumen): {accion_prop.get('content', '')[:50]}...")
            if 'message_to_user' in accion_prop: print(f"   Mensaje: {accion_prop.get('message_to_user')}")
        print("----------------------------------")
        confirm = input("¿Aprobar todas las acciones? (s/N): ")
        return confirm.lower() == 's'

    # Crear directorio de prueba si no existe
    directorio_test_gpo = "/home/ubuntu/test_gpo_functional_project"
    if not os.path.exists(directorio_test_gpo):
        os.makedirs(directorio_test_gpo)
    # Crear un archivo de ejemplo en el directorio de prueba
    with open(os.path.join(directorio_test_gpo, "ejemplo.py"), "w") as f:
        f.write("print(\"Hola desde ejemplo.py\")\n")

    gpo_instance = GestorPeticionesOrquestacion(ui_confirm_callback=simple_confirm_callback)
    
    # Petición de prueba
    # Asegúrate de que tu API Key de Gemini esté en src/asistente_codigo_local/core/config.json
    peticion_test_funcional = "Modifica el archivo ejemplo.py para que también imprima 'Adiós desde ejemplo.py' al final. Luego, crea un nuevo archivo llamado notas.txt con el texto 'Tarea completada.'"
    # peticion_test_funcional = "Crea un archivo llamado hola.txt con el contenido 'Hola Mundo desde Gemini'"
    # peticion_test_funcional = "Dime la capital de Francia. No realices acciones de archivo o comando."

    print(f"\nEnviando petición al GPO: {peticion_test_funcional}")
    resultado_final = gpo_instance.procesar_peticion_usuario(peticion_test_funcional, directorio_test_gpo)
    
    print("\n--- RESULTADO FINAL DEL GPO ---")
    print(resultado_final)
    print("-------------------------------")
    print(f"Revisa el directorio {directorio_test_gpo} para ver los cambios.")
"""

