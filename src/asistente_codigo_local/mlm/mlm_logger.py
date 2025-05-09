# Asistente de Código Local - Módulo de Logging y Monitorización (MLM)

import logging
import os
from logging.handlers import RotatingFileHandler

# Configuración del Logger
LOG_FILE_PATH = os.path.join(os.path.expanduser("~"), ".asistente_codigo_local", "asistente.log")
LOG_LEVEL = logging.INFO # Configurable, podría ser DEBUG para más detalle
MAX_LOG_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# Asegurarse de que el directorio de logs exista
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

# Formato del log
log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s")

# Handler para rotar archivos de log
rotating_file_handler = RotatingFileHandler(
    LOG_FILE_PATH, 
    maxBytes=MAX_LOG_SIZE_BYTES, 
    backupCount=BACKUP_COUNT,
    encoding='utf-8'
)
rotating_file_handler.setFormatter(log_formatter)

# Handler para la consola (opcional, para desarrollo o verbosidad)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

def get_logger(name: str, level=None) -> logging.Logger:
    """Obtiene una instancia de logger configurada."""
    logger = logging.getLogger(name)
    
    # Evitar añadir handlers múltiples si el logger ya los tiene (común en algunos entornos)
    if not logger.handlers:
        logger.addHandler(rotating_file_handler)
        # Descomentar para añadir logs a la consola también:
        # logger.addHandler(console_handler) 
    
    logger.setLevel(level if level is not None else LOG_LEVEL)
    logger.propagate = False # Evitar que los logs se propaguen al logger raíz si no es deseado
    return logger

class ModuloLogging:
    # Esta clase es más un namespace para la función get_logger y la configuración
    # Podría expandirse si se necesita más lógica de gestión de logging.
    
    @staticmethod
    def inicializar_logging_global(level=None):
        """Configura el logger raíz si es necesario o ajusta niveles."""
        # Esto es opcional, usualmente se configuran loggers por módulo.
        # Pero podría ser útil para establecer un nivel global por defecto.
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            root_logger.addHandler(rotating_file_handler)
            # root_logger.addHandler(console_handler)
        root_logger.setLevel(level if level is not None else LOG_LEVEL)
        print(f"MLM: Logging global inicializado. Nivel: {root_logger.getEffectiveLevel()}. Archivo: {LOG_FILE_PATH}")

    @staticmethod
    def get_logger(name: str, level=None) -> logging.Logger:
        """Función de conveniencia para acceder al logger desde la clase."""
        return get_logger(name, level)

# Ejemplo de uso del logger
if __name__ == "__main__":
    # Inicializar logging global (opcional)
    # ModuloLogging.inicializar_logging_global(logging.DEBUG)

    # Obtener un logger para un módulo específico
    logger_gcp_test = ModuloLogging.get_logger("GCP_TestModule", logging.DEBUG)
    logger_main_test = ModuloLogging.get_logger("MainApp_TestModule") # Usará LOG_LEVEL por defecto

    logger_gcp_test.debug("Este es un mensaje de debug desde GCP_TestModule.")
    logger_gcp_test.info("Este es un mensaje informativo desde GCP_TestModule.")
    logger_gcp_test.warning("Este es un mensaje de advertencia desde GCP_TestModule.")
    logger_gcp_test.error("Este es un mensaje de error desde GCP_TestModule.")
    
    logger_main_test.info("Información desde MainApp_TestModule.")
    try:
        x = 1 / 0
    except ZeroDivisionError:
        logger_main_test.error("Error de división por cero capturado.", exc_info=True)
    
    print(f"MLM: Pruebas de logging completadas. Revisa el archivo: {LOG_FILE_PATH}")

