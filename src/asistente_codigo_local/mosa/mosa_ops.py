# En asistente_codigo_local/mosa/mosa_ops.py

import os
import shutil
import re # Asegúrate de que esta importación esté al inicio del archivo

class ModuloOperacionesSistemaArchivos:
    def __init__(self, directorio_proyecto_base: str):
        # self.logger = ModuloLogging.get_logger() # Cuando MLM esté disponible
        if not os.path.isdir(directorio_proyecto_base):
            # self.logger.error(f"MOSA: El directorio del proyecto base no existe: {directorio_proyecto_base}")
            raise ValueError(f"El directorio del proyecto base especificado no existe: {directorio_proyecto_base}")
        self.directorio_proyecto_base = os.path.abspath(directorio_proyecto_base)
        # Log de inicialización original, NO MODIFICAR ESTA LÍNEA DE PRINT
        print(f"MOSA: Inicializado con directorio base: {self.directorio_proyecto_base}")


    def _obtener_ruta_completa_segura(self, ruta_relativa_accion: str) -> str:
        """Construye y valida la ruta completa para una operación de archivo."""
        if os.path.isabs(ruta_relativa_accion):
            # self.logger.error(f"MOSA: ¡ALERTA DE SEGURIDAD! Se intentó usar una ruta absoluta: {ruta_relativa_accion}")
            raise PermissionError(f"Ruta absoluta no permitida: {ruta_relativa_accion}")

        ruta_completa_previa = os.path.join(self.directorio_proyecto_base, ruta_relativa_accion)
        ruta_completa = os.path.abspath(ruta_completa_previa)

        if not ruta_completa.startswith(self.directorio_proyecto_base + os.sep) and ruta_completa != self.directorio_proyecto_base:
            # self.logger.error(f"MOSA: ¡ALERTA DE SEGURIDAD! Intento de acceso fuera del directorio del proyecto: {ruta_completa}")
            raise PermissionError(f"Intento de acceso fuera del directorio del proyecto: {ruta_completa} (base: {self.directorio_proyecto_base})")
        
        return ruta_completa

    # --- ESTA ES LA NUEVA FUNCIÓN QUE DEBE ESTAR PRESENTE ---
    def _generar_ruta_con_directorio_dedicado(self, ruta_relativa_original: str) -> str:
        """
        Transforma una ruta relativa para que el archivo se cree dentro 
        de un directorio dedicado nombrado a partir del archivo.
        Ej: "mi_archivo.txt" -> "mi_archivo_txt_dir/mi_archivo.txt"
        Ej: "subdir/otro.py" -> "subdir/otro_py_dir/otro.py"
        """
        directorio_original = os.path.dirname(ruta_relativa_original)
        nombre_archivo_original = os.path.basename(ruta_relativa_original)
        
        if not nombre_archivo_original: 
             raise ValueError(f"La ruta proporcionada ('{ruta_relativa_original}') no incluye un nombre de archivo válido.")

        nombre_base, extension = os.path.splitext(nombre_archivo_original)
        
        nombre_base_limpio = re.sub(r'[^a-zA-Z0-9_]', '_', nombre_base)
        
        extension_limpia = extension.lstrip('.')
        
        if not nombre_base_limpio: 
            nombre_base_limpio = "file"

        nombre_directorio_dedicado = f"{nombre_base_limpio}_{extension_limpia}_dir" if extension_limpia else f"{nombre_base_limpio}_dir"
        
        ruta_modificada = os.path.join(directorio_original, nombre_directorio_dedicado, nombre_archivo_original)
        return ruta_modificada

    # --- ASEGÚRATE DE QUE TU MÉTODO crear_archivo SE VEA ASÍ ---
    def crear_archivo(self, ruta_relativa: str, contenido: str) -> str:
        """
        Crea un nuevo archivo con el contenido especificado, asegurándose de que
        esté dentro de un subdirectorio dedicado nombrado a partir del archivo.
        """
        # Estos logs son importantes para depurar
        print(f"MOSA: Solicitud para crear archivo en ruta relativa original: {ruta_relativa}")

        try:
            ruta_relativa_con_directorio = self._generar_ruta_con_directorio_dedicado(ruta_relativa)
            print(f"MOSA: Ruta con directorio dedicado generada: {ruta_relativa_con_directorio}")
        except ValueError as ve:
            print(f"MOSA: Error al generar ruta dedicada para '{ruta_relativa}': {ve}")
            return f"Error al generar la ruta dedicada para '{ruta_relativa}': {ve}"

        # ESTE ES EL LOG QUE NO VIMOS EN TU SALIDA, PERO DEBERÍA APARECER SI EL CÓDIGO ES CORRECTO
        # SI NO VES ESTE LOG, ALGO ANDA MAL ANTES DE LLAMAR A _obtener_ruta_completa_segura
        # O _obtener_ruta_completa_segura está siendo llamada con la ruta incorrecta.
        # La ruta que se pasa a _obtener_ruta_completa_segura DEBE ser ruta_relativa_con_directorio
        ruta_completa = self._obtener_ruta_completa_segura(ruta_relativa_con_directorio)
        
        # ESTE PRINT DEBERÍA MOSTRAR LA RUTA CON EL DIRECTORIO DEDICADO
        print(f"MOSA: Creando archivo en ruta completa segura (debería incluir dir. dedicado): {ruta_completa}")
        
        try:
            os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
            with open(ruta_completa, "w", encoding="utf-8") as f:
                f.write(contenido)
            return f"Archivo '{ruta_relativa}' creado con éxito en la ruta (con directorio dedicado): '{ruta_relativa_con_directorio}'."
        except Exception as e:
            print(f"MOSA: Error creando archivo {ruta_completa}: {e}")
            return f"Error al crear archivo en '{ruta_relativa_con_directorio}': {e}"

    # ... (resto de los métodos: modificar_archivo, eliminar_archivo, etc.
    # Asegúrate de que también estén actualizados si los cambiamos antes,
    # aunque el problema principal ahora está en crear_archivo)
    # Copio las versiones que te di antes para modificar_archivo y eliminar_archivo
    # para que tengas el bloque completo y actualizado.

    def modificar_archivo(self, ruta_relativa: str, contenido_nuevo: str) -> str:
        print(f"MOSA: Modificando archivo en ruta relativa: {ruta_relativa}")
        ruta_completa = self._obtener_ruta_completa_segura(ruta_relativa)
        
        if not os.path.exists(ruta_completa):
            print(f"MOSA: Archivo a modificar no encontrado: {ruta_completa}. Si fue creado por el asistente, verifique que la ruta incluya el directorio dedicado.")
            return f"Error: Archivo a modificar no encontrado en '{ruta_relativa}'. Verifique la ruta."

        try:
            with open(ruta_completa, "w", encoding="utf-8") as f:
                f.write(contenido_nuevo)
            return f"Archivo '{ruta_relativa}' modificado con éxito."
        except Exception as e:
            print(f"MOSA: Error modificando archivo {ruta_completa}: {e}")
            return f"Error al modificar archivo '{ruta_relativa}': {e}"

    def eliminar_archivo(self, ruta_relativa: str) -> str:
        print(f"MOSA: Eliminando archivo en ruta relativa: {ruta_relativa}")
        ruta_completa = self._obtener_ruta_completa_segura(ruta_relativa)

        if not os.path.exists(ruta_completa):
            return f"Error: Archivo a eliminar no encontrado: {ruta_relativa}"
        if os.path.isdir(ruta_completa):
            return f"Error: '{ruta_relativa}' es un directorio, no un archivo. Use una función específica para directorios."

        try:
            os.remove(ruta_completa)
            return f"Archivo '{ruta_relativa}' eliminado con éxito."
        except Exception as e:
            print(f"MOSA: Error eliminando archivo {ruta_completa}: {e}")
            return f"Error al eliminar archivo '{ruta_relativa}': {e}"

# Fin de la clase ModuloOperacionesSistemaArchivos