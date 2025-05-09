# En asistente_codigo_local/mecc/mecc_executor.py
import subprocess
import os
import shlex

class ModuloEjecucionComandosConsola:
    def __init__(self, directorio_proyecto_base: str):
        # self.logger = ModuloLogging.get_logger() # Cuando MLM esté disponible
        if not os.path.isdir(directorio_proyecto_base):
            # self.logger.error(f"MECC: El directorio del proyecto base no existe: {directorio_proyecto_base}")
            raise ValueError(f"El directorio del proyecto base especificado no existe: {directorio_proyecto_base}")
        self.directorio_proyecto_base = os.path.abspath(directorio_proyecto_base)
        # Log de inicialización original
        print(f"MECC: Inicializado con directorio base: {self.directorio_proyecto_base}")
        
        # Modificar la lista blanca
        self.comandos_permitidos = {
            "echo": [], 
            "ls": ["-l", "-a"], 
            "git": ["status", "diff", "log"], 
            "python": [],  # Permitir 'python' con argumentos, se validarán específicamente
            "python3": [], # Permitir 'python3' con argumentos, se validarán específicamente
            "node": ["--version"],
            "npm": ["--version", "list"],
            # Puedes añadir más comandos seguros aquí si los necesitas, ej: "sh", "bash"
        }

    def _validar_comando(self, comando_str: str) -> bool:
        # Log de validación original
        print(f"MECC: Validando comando: {comando_str}")
        try:
            partes_comando = shlex.split(comando_str) 
        except ValueError as e:
            print(f"MECC: Error al parsear el comando (shlex): {comando_str} - {e}")
            return False

        if not partes_comando:
            # self.logger.warning("MECC: Comando vacío proporcionado.")
            return False

        comando_principal = partes_comando[0]
        argumentos_comando = partes_comando[1:]

        if comando_principal not in self.comandos_permitidos:
            # self.logger.error(f"MECC: ¡ALERTA DE SEGURIDAD! Comando principal no permitido: {comando_principal}")
            print(f"MECC: ¡ALERTA DE SEGURIDAD! Comando principal no permitido: {comando_principal}")
            return False
        
        # --- INICIO DE MODIFICACIÓN PARA PYTHON/PYTHON3 ---
        if comando_principal in ["python", "python3"]:
            if not argumentos_comando:
                # Permitir `python` o `python3` sin argumentos (abre el REPL), si se considera seguro.
                # O bloquearlo si no se quiere permitir. Por ahora, lo permitimos.
                # print(f"MECC: '{comando_principal}' sin argumentos se ejecutará (REPL).")
                return True # O False si no quieres permitir el REPL

            primer_argumento = argumentos_comando[0]

            if primer_argumento == "--version": # Permitir explícitamente "python --version"
                return True

            # Validar que el script .py sea el primer argumento y esté dentro del proyecto
            if primer_argumento.endswith(".py"):
                # Comprobar si la ruta del script es segura (relativa al proyecto)
                # os.path.abspath previene algunos trucos, pero la comprobación startswith es clave.
                ruta_script_propuesta = os.path.join(self.directorio_proyecto_base, primer_argumento)
                ruta_script_abs = os.path.abspath(ruta_script_propuesta)

                if not ruta_script_abs.startswith(self.directorio_proyecto_base + os.sep) and ruta_script_abs != self.directorio_proyecto_base :
                    print(f"MECC: ¡ALERTA DE SEGURIDAD! Intento de ejecutar script de Python fuera del directorio del proyecto: {ruta_script_abs}")
                    return False
                
                # Si es un script .py y está dentro del proyecto, consideramos la estructura del comando válida.
                # La existencia del archivo la comprobará el propio subprocess al intentar ejecutarlo.
                # Aquí solo validamos el formato del comando y la seguridad de la ruta.
                print(f"MECC: Comando '{comando_principal} {primer_argumento}' validado para ejecución de script .py.")
                return True
            else:
                # Si el primer argumento no es --version y no es un .py, lo consideramos inseguro
                print(f"MECC: ¡ALERTA DE SEGURIDAD! Argumento '{primer_argumento}' no permitido para '{comando_principal}'. Solo se permite --version o un script .py como primer argumento.")
                return False
        # --- FIN DE MODIFICACIÓN PARA PYTHON/PYTHON3 ---
        
        # Validación genérica de argumentos para otros comandos (si tienen restricciones)
        argumentos_permitidos_para_comando_especifico = self.comandos_permitidos[comando_principal]
        if argumentos_permitidos_para_comando_especifico: 
            for arg_idx, arg_val in enumerate(argumentos_comando):
                # Esta es una validación simple, asume que los argumentos permitidos son literales.
                # Puede necesitar ser más sofisticada para comandos con patrones de argumentos.
                if arg_val not in argumentos_permitidos_para_comando_especifico:
                    # Permitir si el comando principal está en la lista y la lista de args permitidos está vacía (permite todos los args)
                    # Esto ya está cubierto por `if argumentos_permitidos_para_comando_especifico:`
                    print(f"MECC: ¡ALERTA DE SEGURIDAD! Argumento '{arg_val}' en posición {arg_idx} no está en la lista de argumentos permitidos para '{comando_principal}': {argumentos_permitidos_para_comando_especifico}")
                    return False
        
        comandos_peligrosos_absolutos = ["rm", "sudo", "mkfs", "dd", "shutdown", "reboot"]
        if comando_principal in comandos_peligrosos_absolutos:
             # self.logger.error(f"MECC: ¡ALERTA DE SEGURIDAD! Comando explícitamente peligroso: {comando_principal}")
             print(f"MECC: ¡ALERTA DE SEGURIDAD! Comando explícitamente peligroso: {comando_principal}")
             return False
        
        # self.logger.info(f"MECC: Comando validado como seguro: {comando_str}")
        return True

    def ejecutar_comando(self, comando_str: str) -> dict:
        # Log original
        print(f"MECC: Intentando ejecutar comando: {comando_str}")

        if not self._validar_comando(comando_str):
            mensaje_error = f"Comando no permitido o inseguro: {comando_str}"
            # self.logger.error(f"MECC: {mensaje_error}")
            return {"exito": False, "stdout": "", "stderr": mensaje_error, "codigo_retorno": -1}

        try:
            partes_comando = shlex.split(comando_str)
            proceso = subprocess.Popen(
                partes_comando, 
                cwd=self.directorio_proyecto_base, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                encoding="utf-8",
                errors="replace" # Añadido para manejar posibles errores de decodificación
            )
            stdout, stderr = proceso.communicate(timeout=60) 
            codigo_retorno = proceso.returncode
            
            # Log original, puede que necesite el f-string corregido si estaba mal antes
            print(f"MECC: Comando '{comando_str}' ejecutado. Código de retorno: {codigo_retorno}")
            return {"exito": codigo_retorno == 0, "stdout": stdout, "stderr": stderr, "codigo_retorno": codigo_retorno}
        
        except FileNotFoundError:
            # Esto podría ocurrir si el script no se encuentra en la ruta especificada.
            mensaje_error = f"Comando no encontrado o archivo de script no hallado: {shlex.split(comando_str)[0]}"
            print(f"MECC: {mensaje_error}")
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

# Fin de la clase