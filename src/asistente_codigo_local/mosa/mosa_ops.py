# Asistente de Código Local - Módulo de Operaciones de Sistema de Archivos (MOSA)

import os
import shutil

# Placeholder para futuras importaciones (ej. logger)
# from ..mlm import ModuloLogging

class ModuloOperacionesSistemaArchivos:
    def __init__(self, directorio_proyecto_base: str):
        # self.logger = ModuloLogging.get_logger() # Cuando MLM esté disponible
        if not os.path.isdir(directorio_proyecto_base):
            # self.logger.error(f"MOSA: El directorio del proyecto base no existe: {directorio_proyecto_base}")
            raise ValueError(f"El directorio del proyecto base especificado no existe: {directorio_proyecto_base}")
        self.directorio_proyecto_base = os.path.abspath(directorio_proyecto_base)
        print(f"MOSA: Inicializado con directorio base: {self.directorio_proyecto_base}")

    def _obtener_ruta_completa_segura(self, ruta_relativa_accion: str) -> str:
        """Construye y valida la ruta completa para una operación de archivo."""
        if os.path.isabs(ruta_relativa_accion):
            # self.logger.error(f"MOSA: ¡ALERTA DE SEGURIDAD! Se intentó usar una ruta absoluta: {ruta_relativa_accion}")
            raise PermissionError(f"Ruta absoluta no permitida: {ruta_relativa_accion}")

        ruta_completa = os.path.abspath(os.path.join(self.directorio_proyecto_base, ruta_relativa_accion))

        if not ruta_completa.startswith(self.directorio_proyecto_base):
            # self.logger.error(f"MOSA: ¡ALERTA DE SEGURIDAD! Intento de acceso fuera del directorio del proyecto: {ruta_completa}")
            raise PermissionError(f"Intento de acceso fuera del directorio del proyecto: {ruta_completa}")
        
        return ruta_completa

    def crear_archivo(self, ruta_relativa: str, contenido: str) -> str:
        """Crea un nuevo archivo con el contenido especificado."""
        ruta_completa = self._obtener_ruta_completa_segura(ruta_relativa)
        # self.logger.info(f"MOSA: Creando archivo en: {ruta_completa}")
        print(f"MOSA: Creando archivo en: {ruta_completa}")
        try:
            os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
            with open(ruta_completa, "w", encoding="utf-8") as f:
                f.write(contenido)
            # self.logger.info(f"MOSA: Archivo creado con éxito: {ruta_completa}")
            return f"Archivo '{ruta_relativa}' creado con éxito."
        except Exception as e:
            # self.logger.error(f"MOSA: Error creando archivo {ruta_completa}: {e}")
            print(f"MOSA: Error creando archivo {ruta_completa}: {e}")
            return f"Error al crear archivo '{ruta_relativa}': {e}"

    def modificar_archivo(self, ruta_relativa: str, contenido_nuevo: str) -> str:
        """Modifica un archivo existente con el nuevo contenido (sobrescribe)."""
        ruta_completa = self._obtener_ruta_completa_segura(ruta_relativa)
        # self.logger.info(f"MOSA: Modificando archivo en: {ruta_completa}")
        print(f"MOSA: Modificando archivo en: {ruta_completa}")
        if not os.path.exists(ruta_completa):
            # self.logger.warning(f"MOSA: Archivo a modificar no encontrado: {ruta_completa}. Se creará uno nuevo.")
            # Opcionalmente, se podría lanzar un error si el archivo debe existir
            # return f"Error: Archivo a modificar no encontrado: {ruta_relativa}"
            print(f"MOSA: Archivo a modificar no encontrado: {ruta_completa}. Se creará.")
            # os.makedirs(os.path.dirname(ruta_completa), exist_ok=True) # Ya lo hace crear_archivo
            return self.crear_archivo(ruta_relativa, contenido_nuevo) # O manejar como error

        try:
            # Opcional: Crear un backup antes de modificar
            # shutil.copy(ruta_completa, ruta_completa + ".bak") 
            with open(ruta_completa, "w", encoding="utf-8") as f:
                f.write(contenido_nuevo)
            # self.logger.info(f"MOSA: Archivo modificado con éxito: {ruta_completa}")
            return f"Archivo '{ruta_relativa}' modificado con éxito."
        except Exception as e:
            # self.logger.error(f"MOSA: Error modificando archivo {ruta_completa}: {e}")
            print(f"MOSA: Error modificando archivo {ruta_completa}: {e}")
            return f"Error al modificar archivo '{ruta_relativa}': {e}"

    def eliminar_archivo(self, ruta_relativa: str) -> str:
        """Elimina un archivo especificado."""
        ruta_completa = self._obtener_ruta_completa_segura(ruta_relativa)
        # self.logger.info(f"MOSA: Eliminando archivo en: {ruta_completa}")
        print(f"MOSA: Eliminando archivo en: {ruta_completa}")
        if not os.path.exists(ruta_completa):
            # self.logger.warning(f"MOSA: Archivo a eliminar no encontrado: {ruta_completa}")
            return f"Error: Archivo a eliminar no encontrado: {ruta_relativa}"
        if os.path.isdir(ruta_completa):
            # self.logger.error(f"MOSA: Intento de eliminar un directorio con eliminar_archivo: {ruta_completa}")
            return f"Error: '{ruta_relativa}' es un directorio, no un archivo. Use una función específica para directorios."

        try:
            os.remove(ruta_completa)
            # self.logger.info(f"MOSA: Archivo eliminado con éxito: {ruta_completa}")
            return f"Archivo '{ruta_relativa}' eliminado con éxito."
        except Exception as e:
            # self.logger.error(f"MOSA: Error eliminando archivo {ruta_completa}: {e}")
            print(f"MOSA: Error eliminando archivo {ruta_completa}: {e}")
            return f"Error al eliminar archivo '{ruta_relativa}': {e}"

# Ejemplo de uso (se movería a pruebas o al GPO)
if __name__ == "__main__":
    test_project_mosa_dir = "/home/ubuntu/test_mosa_project"
    if os.path.exists(test_project_mosa_dir):
        shutil.rmtree(test_project_mosa_dir) # Limpiar de ejecuciones anteriores
    os.makedirs(test_project_mosa_dir)

    mosa_instance = ModuloOperacionesSistemaArchivos(test_project_mosa_dir)

    print("--- Pruebas MOSA ---")
    # Crear archivo
    print(mosa_instance.crear_archivo("nuevo_fichero.txt", "Contenido inicial del fichero.\nSegunda línea."))
    print(mosa_instance.crear_archivo("subdir/otro_fichero.txt", "Contenido en subdirectorio."))

    # Modificar archivo
    print(mosa_instance.modificar_archivo("nuevo_fichero.txt", "Contenido modificado.\nSigue aquí."))
    print(mosa_instance.modificar_archivo("no_existe_aun.txt", "Se crea al modificar."))

    # Eliminar archivo
    print(mosa_instance.eliminar_archivo("nuevo_fichero.txt"))
    print(mosa_instance.eliminar_archivo("subdir/otro_fichero.txt"))
    print(mosa_instance.eliminar_archivo("no_existe.txt")) # Prueba de error

    # Pruebas de seguridad
    try:
        mosa_instance.crear_archivo("../archivo_fuera.txt", "ilegal")
    except PermissionError as e:
        print(f"Error de seguridad (esperado): {e}")
    try:
        mosa_instance.crear_archivo("/tmp/archivo_absoluto.txt", "ilegal")
    except PermissionError as e:
        print(f"Error de seguridad (esperado): {e}")

    # Limpiar directorio de prueba
    # shutil.rmtree(test_project_mosa_dir)

