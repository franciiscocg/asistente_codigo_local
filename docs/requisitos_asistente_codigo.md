# Requisitos Funcionales y No Funcionales: Asistente de Código Local

Este documento detalla los requisitos funcionales y no funcionales para el desarrollo de la aplicación "Asistente de Código Local", basados en el documento de diseño previamente generado.

## 1. Requisitos Funcionales (RF)

Los requisitos funcionales describen qué debe hacer el sistema.

-   **RF001: Entrada del Usuario:** La aplicación debe permitir al usuario introducir una descripción de un problema o una tarea de programación en lenguaje natural. Inicialmente, esto se realizará a través de una interfaz de línea de comandos (CLI), con potencial extensión a una GUI.
-   **RF002: Interacción con Gemini API:** La aplicación debe ser capaz de comunicarse con la API de Google Gemini, enviando la entrada del usuario y el contexto del proyecto para su interpretación y la generación de soluciones.
-   **RF003: Traducción de Respuestas en Acciones:** La aplicación debe interpretar las respuestas de Gemini (preferiblemente en formato JSON estructurado) y traducirlas en acciones concretas sobre el sistema de archivos local y la consola. Estas acciones incluyen:
    -   **RF003.1: Creación de Archivos:** Crear nuevos archivos con el contenido especificado por Gemini.
    -   **RF003.2: Modificación de Archivos:** Modificar archivos existentes. Esto puede implicar reemplazar el contenido completo del archivo o aplicar un parche (formato diff).
    -   **RF003.3: Eliminación de Archivos:** Eliminar archivos específicos según la indicación de Gemini.
    -   **RF003.4: Ejecución de Comandos:** Ejecutar comandos de consola dentro del directorio del proyecto (ej. compilación, instalación de dependencias, ejecución de scripts).
-   **RF004: Confirmación del Usuario:** Antes de ejecutar cualquier acción que modifique el sistema de archivos (crear, editar, eliminar) o ejecute comandos de consola, la aplicación debe solicitar una confirmación explícita al usuario.
-   **RF005: Presentación del Plan de Acción:** La aplicación debe mostrar al usuario un resumen claro y detallado del plan de acciones propuesto por Gemini antes de solicitar la confirmación. Esto incluye los comandos exactos y las rutas de los archivos afectados (con un diff de los cambios si es posible).
-   **RF006: Aprobación Selectiva de Acciones:** El usuario debe tener la opción de aprobar o rechazar las acciones propuestas de forma individual o todas en conjunto.
-   **RF007: Gestión de Contexto del Proyecto:** La aplicación debe recopilar y enviar a Gemini el contexto relevante del proyecto del usuario. Esto incluye, pero no se limita a, la estructura de directorios, el contenido de archivos específicos (mencionados por el usuario o inferidos como relevantes), y potencialmente información del control de versiones (Git).
-   **RF008: Manejo de Errores y Ciclo de Corrección:** La aplicación debe gestionar los errores que puedan ocurrir durante la ejecución de las acciones. Si una acción falla, se debe informar al usuario. Opcionalmente (y configurable), la aplicación puede iniciar un ciclo de corrección enviando la información del error de vuelta a Gemini para obtener una solución revisada.
-   **RF009: Retroalimentación al Usuario:** La aplicación debe informar al usuario sobre el resultado de cada operación (éxito, fallo) y proporcionar logs o salidas relevantes de los comandos ejecutados.
-   **RF010: Logging Detallado:** La aplicación debe mantener un registro (log) detallado de todas las operaciones importantes, incluyendo la entrada del usuario, los prompts enviados a Gemini, las respuestas recibidas, las acciones ejecutadas y cualquier error.
-   **RF011: Solicitud de Aclaraciones:** Si Gemini determina que la solicitud del usuario es ambigua o requiere más información, debe poder generar una acción de tipo `REQUEST_CLARIFICATION`. La aplicación debe presentar esta solicitud al usuario y enviar la respuesta del usuario de vuelta a Gemini.
-   **RF012: Especificación del Directorio del Proyecto:** El usuario debe poder especificar el directorio raíz del proyecto sobre el cual operará el asistente.

## 2. Requisitos No Funcionales (RNF)

Los requisitos no funcionales describen cómo debe ser el sistema.

-   **RNF001: Seguridad:** La seguridad es una prioridad máxima.
    -   **RNF001.1: Confinamiento de Operaciones:** Todas las operaciones de archivo deben estar estrictamente confinadas al directorio del proyecto especificado por el usuario. Se deben prevenir los ataques de traversía de directorio.
    -   **RNF001.2: Validación de Comandos:** Los comandos de consola propuestos por Gemini deben ser validados rigurosamente antes de su ejecución. Se considerará una lista blanca de comandos seguros y/o un análisis de patrones peligrosos.
    -   **RNF001.3: Ejecución Segura de Comandos:** Evitar la ejecución directa de comandos en un shell para prevenir vulnerabilidades de inyección. Usar APIs de ejecución de procesos que manejen argumentos de forma segura.
    -   **RNF001.4: Principio de Menor Privilegio:** La aplicación debe operar con los mínimos privilegios necesarios.
    -   **RNF001.5: Exclusión de Secretos:** El sistema debe intentar identificar y excluir información sensible (claves API, contraseñas) del contexto enviado a Gemini. El usuario podrá configurar exclusiones adicionales.
    -   **RNF001.6: Comunicación Segura:** Toda comunicación con la API de Gemini debe realizarse a través de HTTPS.
    -   **RNF001.7: Ejecución en Seco (Dry Run):** Ofrecer una opción para simular las acciones propuestas sin realizar cambios reales en el sistema.
-   **RNF002: Modularidad:** La arquitectura de la aplicación debe ser altamente modular, como se describe en el documento de diseño (UI/CLI, GPO, MIG, IAG, GCP, MOSA, MECC, MLM). Esto facilitará el desarrollo, las pruebas, el mantenimiento y la escalabilidad.
-   **RNF003: Usabilidad:** La interfaz de usuario (inicialmente CLI) debe ser intuitiva, proporcionando información clara y facilitando la interacción del usuario, especialmente durante el proceso de confirmación de acciones.
-   **RNF004: Rendimiento:** La aplicación debe ser razonablemente responsiva. Se debe prestar atención a la eficiencia en la recopilación y envío del contexto del proyecto para no exceder los límites de tokens de la API de Gemini y para minimizar la latencia.
-   **RNF005: Fiabilidad:** La interpretación de las respuestas de Gemini debe ser robusta. Se debe priorizar el uso de formatos de respuesta estructurados (JSON) y validar estos formatos.
-   **RNF006: Mantenibilidad:** El código fuente debe ser limpio, bien organizado, comentado adecuadamente y seguir las mejores prácticas de desarrollo para facilitar su mantenimiento y futuras actualizaciones.
-   **RNF007: Portabilidad:** La aplicación debe ser compatible con los principales sistemas operativos de escritorio: Windows, macOS y Linux.
-   **RNF008: Configurabilidad:** El usuario debe poder configurar ciertos aspectos del comportamiento de la aplicación, como las rutas a excluir del contexto, el nivel de detalle del logging, o si se activa el ciclo de corrección automática de errores.
-   **RNF009: Privacidad:** Se debe informar claramente al usuario que partes de su código fuente y la descripción de sus tareas se enviarán a una API externa (Google Gemini). El manejo de datos debe ser transparente.

## 3. Tecnologías y Arquitectura

-   **Lenguaje de Programación Principal:** Python (versión 3.9 o superior).
-   **Bibliotecas Clave (Python):**
    -   Interacción HTTP: `requests` (sincrónico) o `httpx` (asincrónico).
    -   Sistema de Archivos: `os`, `pathlib`, `shutil`.
    -   Ejecución de Procesos: `subprocess`.
    -   Manejo de JSON: `json`.
    -   Interfaz CLI: `argparse` (estándar), `Click`, o `Typer` (para una CLI más rica).
-   **Formato de Intercambio con Gemini:** JSON, siguiendo el esquema definido en el documento de diseño.
-   **Control de Versiones:** Git.
-   **Entorno de Desarrollo:** Se utilizará un entorno virtual de Python (ej. `venv`).

