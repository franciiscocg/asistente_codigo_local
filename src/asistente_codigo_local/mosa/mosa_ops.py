# En asistente_codigo_local/mosa/mosa_ops.py
import os
import shutil
# La importación 're' ya no es estrictamente necesaria si eliminamos _generar_ruta_con_directorio_dedicado

class ModuloOperacionesSistemaArchivos:
    def __init__(self, directorio_proyecto_base: str):
        if not os.path.isdir(directorio_proyecto_base):
            raise ValueError(f"El directorio del proyecto base especificado no existe: {directorio_proyecto_base}")
        self.directorio_proyecto_base = os.path.abspath(directorio_proyecto_base)
        # Log de inicialización original
        print(f"MOSA: Inicializado con directorio base: {self.directorio_proyecto_base}")

    def _obtener_ruta_completa_segura(self, ruta_relativa_accion: str) -> str:
        if os.path.isabs(ruta_relativa_accion):
            raise PermissionError(f"Ruta absoluta no permitida: {ruta_relativa_accion}")

        # Normalizar la ruta para resolver '..' etc., de forma segura dentro del contexto del join
        ruta_completa_previa = os.path.join(self.directorio_proyecto_base, ruta_relativa_accion)
        ruta_completa = os.path.abspath(ruta_completa_previa)

        # La validación crucial: la ruta final debe estar DENTRO del directorio base del proyecto.
        if not ruta_completa.startswith(self.directorio_proyecto_base + os.sep) and ruta_completa != self.directorio_proyecto_base:
            raise PermissionError(f"Intento de acceso fuera del directorio del proyecto: {ruta_completa} (base: {self.directorio_proyecto_base})")
        
        return ruta_completa

    # La función _generar_ruta_con_directorio_dedicado ya no se debe usar desde crear_archivo.
    # Puedes eliminarla o comentarla.
    # def _generar_ruta_con_directorio_dedicado(self, ruta_relativa_original: str) -> str:
    #     # ... (código anterior de esta función) ...

    def crear_archivo(self, ruta_relativa: str, contenido: str) -> dict:
        """
        Crea un nuevo archivo con el contenido especificado en la ruta_relativa dada.
        Los directorios intermedios en ruta_relativa se crearán si no existen.
        Devuelve un diccionario: {'status': 'éxito'/'error', 'message': str, 'final_path': str or None}
        """
        # Log de solicitud
        print(f"MOSA: Solicitud para crear archivo en ruta relativa: {ruta_relativa}")

        # IMPORTANTE: Ya NO se llama a _generar_ruta_con_directorio_dedicado aquí.
        # La ruta_relativa se usa tal cual la envía Gemini.

        try:
            # _obtener_ruta_completa_segura valida la ruta y la confina al proyecto base.
            ruta_completa = self._obtener_ruta_completa_segura(ruta_relativa)
        except PermissionError as pe:
            msg = f"Error de permisos o ruta insegura para '{ruta_relativa}': {pe}"
            print(f"MOSA: {msg}")
            return {'status': 'error', 'message': msg, 'final_path': None}
        except Exception as e_ruta: # Captura otras excepciones de _obtener_ruta_completa_segura
            msg = f"Error obteniendo ruta segura para '{ruta_relativa}': {e_ruta}"
            print(f"MOSA: {msg}")
            return {'status': 'error', 'message': msg, 'final_path': None}
        
        # Log para mostrar la ruta que se usará para crear.
        print(f"MOSA: Creando archivo en ruta completa segura: {ruta_completa}")
        
        try:
            # Esta línea crea los directorios intermedios necesarios (ej. "canciones/")
            # si no existen, gracias a os.path.dirname() y exist_ok=True.
            directorio_contenedor = os.path.dirname(ruta_completa)
            if directorio_contenedor: # Solo crear directorios si la ruta no es la raíz del proyecto base
                os.makedirs(directorio_contenedor, exist_ok=True)
            
            with open(ruta_completa, "w", encoding="utf-8") as f:
                f.write(contenido)
            
            msg = f"Archivo '{ruta_relativa}' creado con éxito."
            # final_path es la misma ruta_relativa que entró, ya que no hay transformación.
            return {'status': 'éxito', 'message': msg, 'final_path': ruta_relativa}
        except Exception as e:
            msg = f"Error al crear archivo '{ruta_relativa}': {e}"
            print(f"MOSA: {msg}")
            return {'status': 'error', 'message': msg, 'final_path': ruta_relativa}


    def modificar_archivo(self, ruta_relativa: str, contenido_nuevo: str) -> str:
        print(f"MOSA: Modificando archivo en ruta relativa: {ruta_relativa}")
        try:
            ruta_completa = self._obtener_ruta_completa_segura(ruta_relativa)
        except PermissionError as pe:
            return f"Error de permisos o ruta insegura para modificar '{ruta_relativa}': {pe}"
        except Exception as e_ruta:
            return f"Error obteniendo ruta segura para modificar '{ruta_relativa}': {e_ruta}"

        if not os.path.exists(ruta_completa):
            print(f"MOSA: Archivo a modificar no encontrado: {ruta_completa}.")
            return f"Error: Archivo a modificar no encontrado en '{ruta_relativa}'."

        try:
            with open(ruta_completa, "w", encoding="utf-8") as f:
                f.write(contenido_nuevo)
            return f"Archivo '{ruta_relativa}' modificado con éxito."
        except Exception as e:
            print(f"MOSA: Error modificando archivo {ruta_completa}: {e}")
            return f"Error al modificar archivo '{ruta_relativa}': {e}"

    def eliminar_archivo(self, ruta_relativa: str) -> str:
        print(f"MOSA: Eliminando archivo en ruta relativa: {ruta_relativa}")
        try:
            ruta_completa = self._obtener_ruta_completa_segura(ruta_relativa)
        except PermissionError as pe:
            return f"Error de permisos o ruta insegura para eliminar '{ruta_relativa}': {pe}"
        except Exception as e_ruta:
            return f"Error obteniendo ruta segura para eliminar '{ruta_relativa}': {e_ruta}"

        if not os.path.exists(ruta_completa):
            return f"Error: Archivo a eliminar no encontrado: {ruta_relativa}"
        if os.path.isdir(ruta_completa):
            return f"Error: '{ruta_relativa}' es un directorio, no un archivo."

        try:
            os.remove(ruta_completa)
            return f"Archivo '{ruta_relativa}' eliminado con éxito."
        except Exception as e:
            print(f"MOSA: Error eliminando archivo {ruta_completa}: {e}")
            return f"Error al eliminar archivo '{ruta_relativa}': {e}"

# Fin de la clase ModuloOperacionesSistemaArchivos