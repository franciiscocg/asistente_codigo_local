# Asistente de Código Local - Gestor de Contexto del Proyecto (GCP)

import os
import fnmatch
import re

# Placeholder para futuras importaciones (ej. logger)
# from ..mlm import ModuloLogging

# Patrones para excluir archivos/directorios comunes y potencialmente sensibles
# Esto debería ser configurable por el usuario
PATRONES_EXCLUSION_DEFAULT = [
    ".git", "__pycache__", "*.pyc", "*.pyo", "*.so", "*.o",
    "node_modules", ".DS_Store", "build", "dist", "venv", ".venv",
    "*.log", "*.tmp", "*.swp", "*.swo",
    # Archivos que comúnmente contienen secretos (se necesita un escaneo de contenido también)
    ".env*", "*credentials*", "*secret*", "*key*", "*.pem", "*.key"
]

# Expresiones regulares para detectar posibles secretos en el contenido de los archivos
# Estos son ejemplos básicos y necesitarían ser mucho más robustos y configurables
PATRONES_SECRETOS_CONTENIDO = [
    re.compile(r"(api_key|secret_key|password|token)\s*[:=]\s*["']?[A-Za-z0-9\-_\.~+/=]{16,}["']?", re.IGNORECASE),
    re.compile(r"-----BEGIN (RSA|OPENSSH|PGP|EC) PRIVATE KEY-----.*?-----END \1 PRIVATE KEY-----", re.DOTALL | re.IGNORECASE)
]

MAX_FILE_SIZE_CONTEXT = 1024 * 100 # No incluir archivos mayores a 100KB en el contexto (configurable)
MAX_TOTAL_CONTEXT_SIZE = 1024 * 500 # Límite total aproximado para el contexto enviado (configurable)
MAX_CONTEXT_FILES = 20 # Máximo número de archivos a incluir en el contexto

class GestorContextoProyecto:
    def __init__(self, patrones_exclusion=None, patrones_secretos_contenido=None):
        # self.logger = ModuloLogging.get_logger() # Cuando MLM esté disponible
        self.patrones_exclusion = patrones_exclusion if patrones_exclusion is not None else PATRONES_EXCLUSION_DEFAULT
        self.patrones_secretos_contenido = patrones_secretos_contenido if patrones_secretos_contenido is not None else PATRONES_SECRETOS_CONTENIDO
        print("GCP: Inicializado")

    def _es_excluido(self, nombre_archivo_o_dir: str, ruta_completa_dir: str) -> bool:
        """Verifica si un archivo o directorio debe ser excluido basado en patrones."""
        for patron in self.patrones_exclusion:
            if fnmatch.fnmatch(nombre_archivo_o_dir, patron):
                # self.logger.debug(f"GCP: Excluyendo \'{nombre_archivo_o_dir}\' debido al patrón \'{patron}\' en \'{ruta_completa_dir}\'")
                return True
        return False

    def _contiene_secretos(self, contenido_archivo: str, nombre_archivo: str) -> bool:
        """Verifica si el contenido de un archivo parece contener secretos."""
        for patron_secreto in self.patrones_secretos_contenido:
            if patron_secreto.search(contenido_archivo):
                # self.logger.warning(f"GCP: Potencial secreto detectado en \'{nombre_archivo}\' por el patrón \'{patron_secreto.pattern}\'. Excluyendo contenido.")
                print(f"GCP: Potencial secreto detectado en {nombre_archivo}") # Corregido el f-string
                return True
        return False

    def obtener_contexto(self, directorio_proyecto: str, peticion_usuario: str = "") -> dict:
        """Recopila el contexto del proyecto, incluyendo estructura de archivos y contenido relevante."""
        # self.logger.info(f"GCP: Obteniendo contexto para el proyecto en \'{directorio_proyecto}\' y petición: \'{peticion_usuario[:50]}...")
        print(f"GCP: Obteniendo contexto para: {directorio_proyecto}")
        if not os.path.isdir(directorio_proyecto):
            # self.logger.error(f"GCP: Directorio de proyecto no válido: {directorio_proyecto}")
            return {"error": "Directorio de proyecto no válido"}

        directorio_proyecto_abs = os.path.abspath(directorio_proyecto)
        contexto = {
            "directorio_raiz": directorio_proyecto_abs,
            "estructura_archivos": [],
            "contenido_archivos_relevantes": {},
            "archivos_excluidos_por_secreto": []
        }
        tamaño_contexto_actual = 0
        archivos_contexto_contador = 0

        for raiz, dirs, archivos in os.walk(directorio_proyecto_abs, topdown=True):
            # Excluir directorios
            dirs[:] = [d for d in dirs if not self._es_excluido(d, raiz)]

            for nombre_archivo in archivos:
                if self._es_excluido(nombre_archivo, raiz):
                    continue

                ruta_completa_archivo = os.path.join(raiz, nombre_archivo)
                ruta_relativa_archivo = os.path.relpath(ruta_completa_archivo, directorio_proyecto_abs)
                contexto["estructura_archivos"].append(ruta_relativa_archivo)

                if archivos_contexto_contador < MAX_CONTEXT_FILES and nombre_archivo.endswith(('.py', '.js', '.txt', '.md', '.json', '.html', '.css')):
                    try:
                        tamaño_archivo = os.path.getsize(ruta_completa_archivo)
                        if tamaño_archivo > MAX_FILE_SIZE_CONTEXT:
                            contexto["contenido_archivos_relevantes"][ruta_relativa_archivo] = f"<Contenido omitido: Archivo demasiado grande ({tamaño_archivo} bytes)>"
                            continue
                        
                        if tamaño_contexto_actual + tamaño_archivo > MAX_TOTAL_CONTEXT_SIZE:
                            break 

                        with open(ruta_completa_archivo, "r", encoding="utf-8", errors="ignore") as f:
                            contenido = f.read()
                        
                        if self._contiene_secretos(contenido, ruta_relativa_archivo):
                            contexto["contenido_archivos_relevantes"][ruta_relativa_archivo] = "<Contenido omitido: Potencial secreto detectado>"
                            contexto["archivos_excluidos_por_secreto"].append(ruta_relativa_archivo)
                        else:
                            contexto["contenido_archivos_relevantes"][ruta_relativa_archivo] = contenido
                            tamaño_contexto_actual += tamaño_archivo
                            archivos_contexto_contador += 1

                    except Exception as e:
                        contexto["contenido_archivos_relevantes"][ruta_relativa_archivo] = f"<Error al leer archivo: {e}>"
            
            if tamaño_contexto_actual > MAX_TOTAL_CONTEXT_SIZE or archivos_contexto_contador >= MAX_CONTEXT_FILES:
                break 
        
        print(f"GCP: Contexto recopilado. {len(contexto['estructura_archivos'])} archivos/dirs, {len(contexto['contenido_archivos_relevantes'])} contenidos.")
        return contexto

# Ejemplo de uso
if __name__ == "__main__":
    gcp_instance = GestorContextoProyecto()
    
    test_dir = "/home/ubuntu/test_gcp_project"
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)
    os.makedirs(os.path.join(test_dir, "src"))
    os.makedirs(os.path.join(test_dir, ".git")) 
    os.makedirs(os.path.join(test_dir, "node_modules/some_lib"))

    with open(os.path.join(test_dir, "main.py"), "w") as f:
        f.write("print(\"Hola Mundo\")\napi_key = \"fake_api_key_12345678901234567890\"")
    with open(os.path.join(test_dir, "src", "utils.js"), "w") as f:
        f.write("function helper() { return 'ayuda'; }")
    with open(os.path.join(test_dir, "README.md"), "w") as f:
        f.write("# Mi Proyecto de Prueba\nEste es un proyecto para probar GCP.")
    with open(os.path.join(test_dir, "config.json"), "w") as f:
        f.write("{\"setting\": \"value\", \"password\": \"supersecretpassword123\"}")
    with open(os.path.join(test_dir, "big_file.txt"), "w") as f:
        f.write("A" * (MAX_FILE_SIZE_CONTEXT + 100) )
    with open(os.path.join(test_dir, ".env"), "w") as f:
        f.write("DATABASE_URL=test_db_url")

    contexto_obtenido = gcp_instance.obtener_contexto(test_dir, "Necesito ayuda con main.py")
    print("--- Contexto Obtenido por GCP ---")
    import json
    print(json.dumps(contexto_obtenido, indent=2))

