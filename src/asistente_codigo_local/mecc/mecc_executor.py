# Asistente de Código Local - Módulo de Ejecución de Comandos de Consola (MECC)

import subprocess
import os
import shlex

# Placeholder para futuras importaciones (ej. logger)
# from ..mlm import ModuloLogging

class ModuloEjecucionComandosConsola:
    def __init__(self, directorio_proyecto_base: str):
        # self.logger = ModuloLogging.get_logger() # Cuando MLM esté disponible
        if not os.path.isdir(directorio_proyecto_base):
            # self.logger.error(f"MECC: El directorio del proyecto base no existe: {directorio_proyecto_base}")
            raise ValueError(f"El directorio del proyecto base especificado no existe: {directorio_proyecto_base}")
        self.directorio_proyecto_base = os.path.abspath(directorio_proyecto_base)
        print(f"MECC: Inicializado con directorio base: {self.directorio_proyecto_base}")
        
        # Lista blanca de comandos permitidos (ejemplo simple, expandir según sea necesario)
        # Idealmente, esto sería configurable y más granular.
        self.comandos_permitidos = {
            "echo": [], # Permite echo con cualquier argumento
            "ls": ["-l", "-a"], # Permite ls con -l o -a
            "git": ["status", "diff", "log"], # Comandos git seguros
            "python": ["--version"], # Ejemplo de comando con argumento específico
            "python3.11": ["--version"], 
            "node": ["--version"],
            "npm": ["--version", "list"],
            # Se podrían añadir comandos de compilación o testeo específicos del proyecto si son seguros
        }

    def _validar_comando(self, comando_str: str) -> bool:
        """Valida si el comando está permitido y es seguro."""
        # self.logger.debug(f"MECC: Validando comando: {comando_str}")
        print(f"MECC: Validando comando: {comando_str}")
        try:
            partes_comando = shlex.split(comando_str) # Divide el comando de forma segura
        except ValueError as e:
            # self.logger.warning(f"MECC: Error al parsear el comando (shlex): {comando_str} - {e}")
            print(f"MECC: Error al parsear el comando (shlex): {comando_str} - {e}")
            return False

        if not partes_comando:
            # self.logger.warning("MECC: Comando vacío proporcionado.")
            return False

        comando_principal = partes_comando[0]
        argumentos_comando = partes_comando[1:]

        # Comprobación de lista blanca
        if comando_principal not in self.comandos_permitidos:
            # self.logger.error(f"MECC: ¡ALERTA DE SEGURIDAD! Comando principal no permitido: {comando_principal}")
            print(f"MECC: ¡ALERTA DE SEGURIDAD! Comando principal no permitido: {comando_principal}")
            return False
        
        # Validar argumentos si hay restricciones específicas en la lista blanca
        argumentos_permitidos_para_comando = self.comandos_permitidos[comando_principal]
        if argumentos_permitidos_para_comando: # Si la lista no está vacía, hay restricciones de args
            for arg in argumentos_comando:
                if not arg.startswith("-") and arg not in argumentos_permitidos_para_comando:
                    # Permitir argumentos que no son flags si el comando lo requiere (ej. python script.py)
                    # Esta lógica de validación de argumentos necesitaría ser más sofisticada
                    # Por ahora, si hay una lista de args permitidos y el arg no está, lo rechazamos
                    # a menos que sea un nombre de archivo o similar (lo cual es difícil de validar genéricamente aquí)
                    # Para este ejemplo simplificado, si hay lista de args, solo esos args son permitidos.
                    # Una mejora sería permitir patrones o tipos de argumentos.
                    if arg not in argumentos_permitidos_para_comando:
                        # self.logger.error(f"MECC: ¡ALERTA DE SEGURIDAD! Argumento no permitido ")
                        print(f"MECC: ¡ALERTA DE SEGURIDAD! Argumento ")
                        return False
        
        # Comprobaciones adicionales de seguridad (lista negra simple)
        comandos_peligrosos_absolutos = ["rm", "sudo", "mkfs", "dd", "shutdown", "reboot"]
        if comando_principal in comandos_peligrosos_absolutos:
             # self.logger.error(f"MECC: ¡ALERTA DE SEGURIDAD! Comando explícitamente peligroso: {comando_principal}")
             print(f"MECC: ¡ALERTA DE SEGURIDAD! Comando explícitamente peligroso: {comando_principal}")
             return False

        # self.logger.info(f"MECC: Comando validado como seguro: {comando_str}")
        return True

    def ejecutar_comando(self, comando_str: str) -> dict:
        """Ejecuta un comando de consola de forma segura y devuelve su salida."""
        # self.logger.info(f"MECC: Intentando ejecutar comando: {comando_str}")
        print(f"MECC: Intentando ejecutar comando: {comando_str}")

        if not self._validar_comando(comando_str):
            mensaje_error = f"Comando no permitido o inseguro: {comando_str}"
            # self.logger.error(f"MECC: {mensaje_error}")
            return {"exito": False, "stdout": "", "stderr": mensaje_error, "codigo_retorno": -1}

        try:
            # Usar shlex.split para manejar argumentos con espacios de forma segura
            partes_comando = shlex.split(comando_str)
            proceso = subprocess.Popen(
                partes_comando, 
                cwd=self.directorio_proyecto_base, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                encoding="utf-8"
            )
            stdout, stderr = proceso.communicate(timeout=60) # Timeout de 60 segundos
            codigo_retorno = proceso.returncode

            # self.logger.info(f"MECC: Comando ")
            print(f"MECC: Comando ")
            return {"exito": codigo_retorno == 0, "stdout": stdout, "stderr": stderr, "codigo_retorno": codigo_retorno}
        
        except FileNotFoundError:
            mensaje_error = f"Comando no encontrado: {partes_comando[0]}"
            # self.logger.error(f"MECC: {mensaje_error}")
            return {"exito": False, "stdout": "", "stderr": mensaje_error, "codigo_retorno": -1}
        except subprocess.TimeoutExpired:
            mensaje_error = f"Comando excedió el tiempo límite: {comando_str}"
            # self.logger.error(f"MECC: {mensaje_error}")
            proceso.kill()
            stdout, stderr = proceso.communicate()
            return {"exito": False, "stdout": stdout, "stderr": mensaje_error + "\n" + stderr, "codigo_retorno": -1}
        except Exception as e:
            mensaje_error = f"Error ejecutando comando {comando_str}: {e}"
            # self.logger.error(f"MECC: {mensaje_error}", exc_info=True)
            return {"exito": False, "stdout": "", "stderr": mensaje_error, "codigo_retorno": -1}

# Ejemplo de uso (se movería a pruebas o al GPO)
if __name__ == "__main__":
    test_project_mecc_dir = "/home/ubuntu/test_mecc_project"
    if not os.path.exists(test_project_mecc_dir):
        os.makedirs(test_project_mecc_dir)
    # Crear un archivo de prueba para ls
    with open(os.path.join(test_project_mecc_dir, "testfile.txt"), "w") as f:
        f.write("test content")

    mecc_instance = ModuloEjecucionComandosConsola(test_project_mecc_dir)

    print("--- Pruebas MECC ---")
    comandos_prueba = [
        "echo \"Hola desde MECC\"",
        "ls -l",
        "git status", # Asumiendo que git está instalado y es seguro para status
        "python --version",
        "comando_inexistente_xyz",
        "rm -rf /", # Debería ser bloqueado por validación
        "echo \"prueba de argumento no listado para echo\"", # Debería pasar si echo permite args arbitrarios
        "ls /etc" # Debería ser bloqueado si ls no permite args arbitrarios o si se detecta /etc como sensible
    ]

    for cmd in comandos_prueba:
        print(f"\nEjecutando: {cmd}")
        resultado = mecc_instance.ejecutar_comando(cmd)
        print(f"  Éxito: {resultado["exito"]}")
        print(f"  Código Retorno: {resultado["codigo_retorno"]}")
        if resultado["stdout"]:
            print(f"  STDOUT:\n{resultado["stdout"]}")
        if resultado["stderr"]:
            print(f"  STDERR:\n{resultado["stderr"]}")

    # Limpiar directorio de prueba
    # import shutil
    # shutil.rmtree(test_project_mecc_dir)

