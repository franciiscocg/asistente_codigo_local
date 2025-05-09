# En asistente_codigo_local/gpo/orchestrator.py
import os
import json # Para logging de objetos complejos
# ... (otras importaciones que ya tengas) ...
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
        self.mig = ModuloInteraccionGemini(use_mock=False)
        self.iag = InterpreteAccionesGemini()
        self.mosa = None
        self.mecc = None
        self.ui_confirm_callback = ui_confirm_callback
        self.logger.info("GPO: Inicializado.")

    def _inicializar_modulos_de_sistema(self, directorio_proyecto: str):
        self.logger.info(f"GPO: Inicializando MOSA y MECC para el directorio: {directorio_proyecto}")
        self.mosa = ModuloOperacionesSistemaArchivos(directorio_proyecto_base=directorio_proyecto)
        self.mecc = ModuloEjecucionComandosConsola(directorio_proyecto_base=directorio_proyecto)
        self.iag.set_directorio_proyecto(directorio_proyecto)

    def procesar_peticion_usuario(self, peticion_texto: str, directorio_proyecto: str) -> dict: # CAMBIO: Tipo de retorno a dict
        self.logger.info(f"GPO: Petición recibida: Texto='{peticion_texto}', Directorio='{directorio_proyecto}'")

        if not os.path.isdir(directorio_proyecto):
            self.logger.error(f"GPO: El directorio del proyecto no existe: {directorio_proyecto}")
            return {"type": "error", "data": f"Error: El directorio del proyecto especificado no existe: {directorio_proyecto}"}
        
        self._inicializar_modulos_de_sistema(directorio_proyecto)

        try:
            self.logger.info("GPO: Obteniendo contexto del proyecto...")
            contexto = self.gcp.obtener_contexto(directorio_proyecto, peticion_texto)
            # ... (logging del contexto como antes) ...
            if contexto.get("error"):
                 self.logger.error(f"GPO: Error obteniendo contexto: {contexto.get('error')}")
                 return {"type": "error", "data": f"Error al obtener contexto del proyecto: {contexto.get('error')}"}

            self.logger.info("GPO: Enviando petición a Gemini...")
            respuesta_gemini = self.mig.enviar_a_gemini(peticion_texto, contexto)
            # ... (logging de respuesta_gemini como antes) ...
            if respuesta_gemini.get("error"):
                self.logger.error(f"GPO: Error en la respuesta de Gemini: {respuesta_gemini.get('error')}")
                return {"type": "error", "data": f"Error en la comunicación con Gemini: {respuesta_gemini.get('error')} - Detalles: {respuesta_gemini.get('details', '')}"}

            self.logger.info("GPO: Interpretando respuesta de Gemini...")
            plan_acciones = self.iag.interpretar_respuesta(respuesta_gemini)
            self.logger.info(f"GPO: Plan de acciones generado: {json.dumps(plan_acciones, indent=2)}")

            if not plan_acciones:
                self.logger.warning("GPO: No se generaron acciones válidas o el plan está vacío.")
                summary = respuesta_gemini.get("summary", "No se pudo generar un plan de acciones o la respuesta no contenía acciones.")
                # Si no hay plan, pero hay un resumen, podría ser una respuesta directa sin acciones.
                if not summary and respuesta_gemini.get("candidates"): # Intenta obtener texto directo si no hay 'summary'
                    try:
                        summary = respuesta_gemini["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError, TypeError):
                        summary = "Respuesta de Gemini no contenía un plan de acciones claro ni un resumen."
                return {"type": "results", "data": summary}

            # --- INICIO DE NUEVA LÓGICA PARA REQUEST_CLARIFICATION ---
            # Si la acción principal (o única) es una aclaración, no pedir confirmación para ejecutarla,
            # sino devolverla a la UI para que maneje la entrada del usuario.
            if len(plan_acciones) >= 1 and plan_acciones[0].get("type") == "REQUEST_CLARIFICATION":
                self.logger.info("GPO: Se requiere aclaración del usuario. Devolviendo a la UI.")
                accion_aclaracion = plan_acciones[0]
                return {
                    "type": "clarification_needed",
                    "message": accion_aclaracion.get("message_to_user", "Se necesita más información para continuar."),
                    "options": accion_aclaracion.get("options", []), # Para uso futuro si la UI maneja opciones
                    "original_request": peticion_texto, # Guardar la petición original
                    "summary_gemini": respuesta_gemini.get("summary", "") # Resumen si Gemini lo dio
                }
            # --- FIN DE NUEVA LÓGICA PARA REQUEST_CLARIFICATION ---

            if self.ui_confirm_callback:
                self.logger.info("GPO: Solicitando confirmación al usuario para el plan de acciones...")
                if not self.ui_confirm_callback(plan_acciones):
                    self.logger.info("GPO: El usuario canceló las acciones.")
                    return {"type": "results", "data": "Operación cancelada por el usuario."}
                self.logger.info("GPO: Usuario confirmó las acciones.")
            else:
                self.logger.warning("GPO: No se proporcionó callback de confirmación. Asumiendo SÍ (NO RECOMENDADO).")

            self.logger.info("GPO: Ejecutando plan de acciones...")
            resultados_ejecucion = self.ejecutar_plan_acciones(plan_acciones, directorio_proyecto) # Asumiendo que esto ya está modificado para el nuevo retorno de MOSA
            self.logger.info(f"GPO: Resultados de la ejecución: {resultados_ejecucion}")
            
            output_para_usuario = []
            summary_gemini = respuesta_gemini.get("summary", "Resumen no disponible.")
            output_para_usuario.append(f"Resumen de Gemini: {summary_gemini}")
            output_para_usuario.append("\nResultados de las acciones ejecutadas:")
            for resultado_accion_str in resultados_ejecucion: # Asumiendo que resultados_ejecucion es una lista de strings
                output_para_usuario.append(f"- {resultado_accion_str}")
            
            return {"type": "results", "data": "\n".join(output_para_usuario)}

        except Exception as e:
            self.logger.error(f"GPO: Error crítico procesando la petición: {e}", exc_info=True)
            return {"type": "error", "data": f"Error crítico en el GPO: {e}"}

    def ejecutar_plan_acciones(self, plan_acciones: list, directorio_proyecto: str) -> list:
        resultados = []
        rutas_creadas_mapeo = {} 

        if not self.mosa or not self.mecc:
            self.logger.error("GPO: MOSA o MECC no inicializados antes de ejecutar acciones.")
            resultados.append("Error interno: Módulos de sistema no inicializados.")
            return resultados

        for accion in plan_acciones:
            tipo_accion = accion.get("type")
            # Aseguramos que resultado_accion_str tenga un valor por defecto.
            resultado_accion_str = f"Acción '{tipo_accion}' no fue procesada o reconocida." 
            self.logger.info(f"GPO: Procesando acción: {tipo_accion}, Detalles: {accion}")
            
            try:
                if tipo_accion == "CREATE_FILE":
                    ruta_original = accion.get("path")
                    contenido = accion.get("content")
                    if ruta_original and contenido is not None: # Contenido puede ser string vacío
                        resultado_mosa = self.mosa.crear_archivo(ruta_original, contenido) # MOSA ahora devuelve dict
                        resultado_accion_str = resultado_mosa.get('message', 'Error desconocido en MOSA al crear archivo.')
                        if resultado_mosa.get('status') == 'éxito' and resultado_mosa.get('final_path'):
                            rutas_creadas_mapeo[ruta_original] = resultado_mosa.get('final_path')
                    else:
                        resultado_accion_str = "Error: CREATE_FILE requiere 'path' y 'content'."
                
                elif tipo_accion == "MODIFY_FILE":
                    ruta_modificar = accion.get("path")
                    contenido = accion.get("content")
                    if ruta_modificar in rutas_creadas_mapeo:
                        ruta_modificar_actualizada = rutas_creadas_mapeo[ruta_modificar]
                        self.logger.info(f"GPO: Ruta de MODIFY_FILE actualizada a: {ruta_modificar_actualizada} (desde {ruta_modificar})")
                        ruta_modificar = ruta_modificar_actualizada
                    
                    if ruta_modificar and contenido is not None:
                        resultado_accion_str = self.mosa.modificar_archivo(ruta_modificar, contenido)
                    else:
                        resultado_accion_str = "Error: MODIFY_FILE requiere 'path' y 'content'."

                elif tipo_accion == "DELETE_FILE":
                    ruta_eliminar = accion.get("path")
                    if ruta_eliminar in rutas_creadas_mapeo:
                        ruta_eliminar_actualizada = rutas_creadas_mapeo[ruta_eliminar]
                        self.logger.info(f"GPO: Ruta de DELETE_FILE actualizada a: {ruta_eliminar_actualizada} (desde {ruta_eliminar})")
                        ruta_eliminar = ruta_eliminar_actualizada
                    
                    if ruta_eliminar:
                        resultado_accion_str = self.mosa.eliminar_archivo(ruta_eliminar)
                    else:
                        resultado_accion_str = "Error: DELETE_FILE requiere 'path'."

                elif tipo_accion == "EXECUTE_COMMAND":
                    comando_original = accion.get("command")
                    comando_para_ejecutar = comando_original
                    
                    if comando_original:
                        partes_comando_orig = shlex.split(comando_original)
                        partes_comando_actualizadas = []
                        comando_modificado = False
                        for parte in partes_comando_orig:
                            if parte in rutas_creadas_mapeo:
                                parte_actualizada = rutas_creadas_mapeo[parte]
                                partes_comando_actualizadas.append(parte_actualizada)
                                self.logger.info(f"GPO: Parte del comando '{parte}' actualizada a '{parte_actualizada}'")
                                comando_modificado = True
                            else:
                                partes_comando_actualizadas.append(parte)
                        
                        if comando_modificado:
                            comando_para_ejecutar = shlex.join(partes_comando_actualizadas)
                            self.logger.info(f"GPO: Comando actualizado a: '{comando_para_ejecutar}' (desde '{comando_original}')")

                        res_cmd = self.mecc.ejecutar_comando(comando_para_ejecutar)
                        # Formatear el resultado del comando
                        stdout_msg = f"\n  Salida: {res_cmd['stdout']}" if res_cmd['stdout'] else ""
                        stderr_msg = f"\n  Error (stderr): {res_cmd['stderr']}" if res_cmd['stderr'] else ""
                        resultado_accion_str = (f"Comando: '{comando_para_ejecutar}' "
                                              f"(Original: '{comando_original if comando_modificado else 'N/A'}')\n"
                                              f"  Éxito: {res_cmd['exito']}{stdout_msg}{stderr_msg}")
                    else:
                        resultado_accion_str = "Error: EXECUTE_COMMAND requiere 'command'."
                
                elif tipo_accion == "INFO_MESSAGE":
                    resultado_accion_str = f"Mensaje informativo de Gemini: {accion.get('message_to_user', 'Sin mensaje.')}"
                
                # REQUEST_CLARIFICATION ya no debería llegar aquí si se maneja antes en procesar_peticion_usuario
                # Pero si llegara por alguna razón (ej. mezclado con otras acciones), solo registramos.
                elif tipo_accion == "REQUEST_CLARIFICATION":
                     resultado_accion_str = (f"Solicitud de aclaración de Gemini (en medio de otras acciones, no manejado interactivamente aquí): "
                                           f"{accion.get('message_to_user', 'Sin mensaje.')}")
                else:
                    self.logger.warning(f"GPO: Tipo de acción desconocido o no manejado directamente en ejecución: {tipo_accion}")
                    resultado_accion_str = f"Acción '{tipo_accion}' no procesada. Detalles: {accion.get('description', 'N/A')}"
                
                self.logger.info(f"GPO: Resultado acción {tipo_accion}: {resultado_accion_str}")
            except Exception as e:
                self.logger.error(f"GPO: Error ejecutando acción {tipo_accion} en '{accion.get('path', accion.get('command', 'N/A'))}': {e}", exc_info=True)
                resultado_accion_str = f"Error al ejecutar {tipo_accion} en '{accion.get('path', accion.get('command', 'N/A'))}': {e}"
            resultados.append(resultado_accion_str)
        return resultados

# ... (resto de la clase si hay algo más)