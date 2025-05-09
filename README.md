# Asistente de Código Local - README

## Introducción

Este proyecto es una implementación de un "Asistente de Código Local" que utiliza la API de Google Gemini (actualmente a través de un mock) para interpretar descripciones de problemas o tareas de programación en lenguaje natural y proponer acciones sobre el sistema de archivos y la consola del usuario. El desarrollo se ha centrado en una arquitectura modular, la seguridad en la ejecución de acciones y un flujo de trabajo detallado.

## Estructura del Proyecto

El proyecto está organizado en los siguientes directorios y módulos principales dentro de `/home/ubuntu/asistente_codigo_local/`:

-   `src/asistente_codigo_local/`:
    -   `ui_cli/`: Módulo de Interfaz de Usuario por Línea de Comandos (entrada/salida del usuario).
        -   `main_cli.py`: Punto de entrada principal de la aplicación CLI.
    -   `gpo/`: Gestor de Peticiones y Orquestación (cerebro de la aplicación).
        -   `orchestrator.py`: Lógica de coordinación entre módulos.
    -   `mig/`: Módulo de Interacción con Gemini.
        -   `mig_client.py`: Cliente para comunicarse con la API de Gemini (real o mock).
    -   `iag/`: Intérprete de Acciones de Gemini.
        -   `iag_parser.py`: Analiza y valida las respuestas de Gemini.
    -   `gcp/`: Gestor de Contexto del Proyecto.
        -   `gcp_manager.py`: Recopila y filtra el contexto del proyecto.
    -   `mosa/`: Módulo de Operaciones de Sistema de Archivos.
        -   `mosa_ops.py`: Ejecuta operaciones de creación, edición y eliminación de archivos.
    -   `mecc/`: Módulo de Ejecución de Comandos de Consola.
        -   `mecc_executor.py`: Ejecuta comandos de consola de forma segura.
    -   `mlm/`: Módulo de Logging y Monitorización.
        -   `mlm_logger.py`: Configuración y gestión de logs.
    -   `core/`: (Placeholder para lógica central compartida si es necesario).
    -   `__init__.py`: Archivos para definir los paquetes Python.
-   `tests/`: Contiene las pruebas unitarias (actualmente placeholders) para cada módulo.
    -   `test_gpo.py`, `test_mig.py`, `test_iag.py`, `test_mosa.py`, `test_mecc.py`, `test_gcp.py`
-   `docs/`: (Previsto para documentación más detallada).
-   `scripts/`: (Previsto para scripts auxiliares).
-   `venv/`: Entorno virtual de Python con las dependencias.

## Configuración del Entorno

El entorno ya ha sido configurado con Python 3.11 y las dependencias necesarias (`pylint`, `black`) en un entorno virtual ubicado en `/home/ubuntu/asistente_codigo_local/venv/`.

Para activar el entorno virtual (si se trabaja directamente en la terminal del sandbox):
```bash
source /home/ubuntu/asistente_codigo_local/venv/bin/activate
```

## Ejecución

El punto de entrada principal es `src/asistente_codigo_local/ui_cli/main_cli.py`.

Para ejecutar la aplicación en modo interactivo:
```bash
/home/ubuntu/asistente_codigo_local/venv/bin/python /home/ubuntu/asistente_codigo_local/src/asistente_codigo_local/ui_cli/main_cli.py
```

Para pasar un prompt como argumento:
```bash
/home/ubuntu/asistente_codigo_local/venv/bin/python /home/ubuntu/asistente_codigo_local/src/asistente_codigo_local/ui_cli/main_cli.py "describe tu tarea aquí"
```

**Nota:** Actualmente, la lógica de procesamiento en el GPO y la interacción con Gemini son placeholders o utilizan mocks. Las acciones no se ejecutan realmente sobre el sistema de archivos más allá de los ejemplos internos de cada módulo si se ejecutan directamente.

## Ejecución de Pruebas (Placeholders)

Las pruebas unitarias se encuentran en el directorio `tests/`. Actualmente son placeholders y necesitarían ser completadas para conectar con la lógica real de los módulos.

Para ejecutar las pruebas (una vez completadas y si se usa el framework `unittest`):
```bash
cd /home/ubuntu/asistente_codigo_local
/home/ubuntu/asistente_codigo_local/venv/bin/python -m unittest discover tests
```
O ejecutando cada archivo de prueba individualmente:
```bash
/home/ubuntu/asistente_codigo_local/venv/bin/python /home/ubuntu/asistente_codigo_local/tests/test_gpo.py
# y así para los demás archivos de prueba.
```

## Próximos Pasos (Desarrollo Futuro)

1.  **Completar la lógica de los módulos:** Reemplazar los placeholders con la implementación funcional completa.
2.  **Integración real con la API de Gemini:** Configurar la clave API y la lógica de comunicación con el servicio real.
3.  **Desarrollo exhaustivo de pruebas:** Crear casos de prueba detallados para cada módulo y para el flujo de integración.
4.  **Mejorar la interfaz de usuario:** Añadir más funcionalidades y refinamiento a la CLI.
5.  **Implementar la confirmación de acciones:** Desarrollar el flujo interactivo para que el usuario apruebe/rechace acciones.
6.  **Refinar la gestión de contexto y seguridad.**

Este README proporciona una visión general del estado actual del proyecto.

