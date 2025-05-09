## 2. Flujo de Trabajo Detallado de la Aplicación

A continuación, se describe el flujo de trabajo paso a paso, desde que el usuario introduce el problema hasta que la aplicación realiza las modificaciones o ejecuta los comandos, incluyendo el manejo de errores y el ciclo de corrección.

**Paso 1: Entrada del Usuario y Recopilación de Contexto Inicial**

1.  **Interacción del Usuario:** El usuario inicia la interacción con el "Asistente de Código Local" a través de la interfaz designada (CLI o GUI). Proporciona una descripción en lenguaje natural de la tarea de programación que desea realizar o el problema que necesita resolver (por ejemplo, "Refactorizar la función 'getUserData' para que use async/await y maneje errores de red", "Crear un nuevo componente React llamado 'UserProfileCard' que muestre nombre, email y avatar", "Configurar un script de despliegue para este proyecto Node.js usando Docker").
2.  **Recepción por el GPO:** El Módulo de Interfaz de Usuario (UI/CLI) transmite esta entrada al Gestor de Peticiones y Orquestación (GPO).
3.  **Solicitud de Contexto:** El GPO identifica el directorio del proyecto activo (ya sea preconfigurado, detectado automáticamente o solicitado al usuario). Luego, instruye al Gestor de Contexto del Proyecto (GCP) para que recopile información relevante. El GCP podría, por ejemplo:
    *   Listar la estructura de archivos y directorios del proyecto.
    *   Identificar archivos abiertos o recientemente modificados.
    *   Extraer fragmentos de código de archivos que parezcan relevantes para la petición del usuario (basado en nombres de archivo, menciones en la petición, etc.).
    *   Obtener el estado actual del repositorio Git (rama actual, cambios no confirmados), si aplica.
4.  **Consolidación de Información:** El GPO recibe el contexto del GCP y lo combina con la petición original del usuario.

**Paso 2: Interacción con la API de Gemini**

1.  **Preparación del Prompt:** El GPO pasa la petición consolidada (descripción del usuario + contexto del proyecto) al Módulo de Interacción con Gemini (MIG).
2.  **Construcción del Prompt Estructurado:** El MIG formatea esta información en un prompt optimizado para la API de Gemini. Este prompt inicial no solo incluirá la tarea, sino que también podría instruir a Gemini sobre el formato de respuesta esperado (ver Sección 3) y su rol como asistente que puede proponer cambios en el código, creación/eliminación de archivos y ejecución de comandos.
3.  **Envío a Gemini:** El MIG envía la solicitud a la API de Google Gemini.
4.  **Recepción de Respuesta:** El MIG espera y recibe la respuesta de Gemini. Esta respuesta podría ser:
    *   Un plan de acción estructurado (ej. una lista de operaciones de archivo y comandos).
    *   Código fuente nuevo o modificado.
    *   Una solicitud de aclaración si la petición del usuario es ambigua.
    *   Un mensaje indicando que no puede cumplir la solicitud.

**Paso 3: Interpretación de la Respuesta de Gemini y Planificación de Acciones**

1.  **Transferencia al IAG:** El MIG pasa la respuesta de Gemini al Intérprete de Acciones de Gemini (IAG).
2.  **Análisis y Validación:** El IAG parsea la respuesta. Su principal tarea es convertir la salida de Gemini en una secuencia de operaciones ejecutables y seguras:
    *   **Identificación de Acciones:** Determina si Gemini propone crear archivos, modificar archivos existentes, eliminar archivos o ejecutar comandos de consola.
    *   **Extracción de Parámetros:** Extrae los detalles necesarios para cada acción (nombres de archivo, contenido a escribir, parches de código, comandos específicos, argumentos de comandos).
    *   **Validación de Seguridad Preliminar:** Realiza una primera revisión de las acciones propuestas. Por ejemplo, podría marcar comandos potencialmente peligrosos (ej. `rm -rf /`) o acciones que afecten archivos fuera del directorio del proyecto designado (si no está explícitamente permitido).
3.  **Generación de Plan de Ejecución:** El IAG crea un plan de ejecución interno, que es una lista ordenada de las acciones validadas.

**Paso 4: Ejecución de Acciones (con Posible Confirmación del Usuario)**

1.  **Orquestación por el GPO:** El IAG devuelve el plan de ejecución al GPO.
2.  **Solicitud de Confirmación (Condicional):** Para acciones consideradas sensibles o destructivas (configurables por el usuario, como eliminación de archivos, modificaciones extensas, o ejecución de ciertos comandos), el GPO, a través de la UI/CLI, presentará el plan de acción al usuario y solicitará su confirmación explícita antes de proceder. El usuario podría aprobar todo, aprobar selectivamente, o cancelar.
3.  **Ejecución de Operaciones de Sistema de Archivos:**
    *   El GPO instruye al Módulo de Operaciones de Sistema de Archivos (MOSA) para cada operación de archivo aprobada.
    *   El MOSA realiza la creación, escritura (aplicando parches si es necesario), o eliminación de archivos. Se implementarán mecanismos de backup o versionado simple (ej. renombrar el archivo original antes de modificarlo) para permitir la reversión en caso de error.
    *   El MOSA reporta el éxito o fracaso de cada operación al GPO.
4.  **Ejecución de Comandos de Consola:**
    *   El GPO instruye al Módulo de Ejecución de Comandos de Consola (MECC) para cada comando aprobado.
    *   El MECC ejecuta el comando en un subproceso, dentro del directorio del proyecto.
    *   Captura `stdout` y `stderr` del comando ejecutado.
    *   Reporta el código de salida, `stdout` y `stderr` al GPO.

**Paso 5: Manejo de Resultados, Errores y Ciclo de Corrección**

1.  **Recopilación de Resultados:** El GPO centraliza los resultados de todas las operaciones ejecutadas (éxitos, fallos, salidas de comandos).
2.  **Detección de Errores:** Si alguna operación del MOSA falla o si el MECC reporta un código de salida distinto de cero o contenido en `stderr`, el GPO lo identifica como un error.
3.  **Presentación al Usuario:**
    *   **Éxito:** Si todas las acciones se completan con éxito, el GPO informa al usuario a través de la UI/CLI, mostrando un resumen de los cambios realizados y cualquier salida relevante de los comandos.
    *   **Error:** Si ocurren errores, el GPO informa al usuario del problema específico, mostrando los mensajes de error y la salida relevante.
4.  **Ciclo de Corrección (Opcional y Configurable):**
    *   **Decisión de Reintentar con Gemini:** El usuario (o automáticamente, según configuración) puede decidir enviar la información del error de vuelta a Gemini para una corrección.
    *   **Preparación del Prompt de Corrección:** El GPO, con la ayuda del MIG, construye un nuevo prompt para Gemini. Este prompt incluirá:
        *   La petición original del usuario.
        *   El contexto del proyecto (posiblemente actualizado si hubo cambios parciales exitosos).
        *   La acción o acciones que fallaron.
        *   Los mensajes de error exactos (`stderr`, errores del sistema de archivos).
        *   Una instrucción a Gemini para que analice el error y proponga una solución o un plan de acción corregido.
    *   **Re-interacción con Gemini:** Se repite el Paso 2 (Interacción con la API de Gemini) con este nuevo prompt de corrección.
    *   **Re-interpretación y Re-ejecución:** Se repiten los Pasos 3 y 4 con la nueva respuesta de Gemini. Este ciclo puede continuar varias veces, idealmente con un límite para evitar bucles infinitos.
5.  **Actualización del Contexto:** Después de cada conjunto de acciones (exitosas o no), el GPO puede instruir al GCP para que actualice su conocimiento del estado del proyecto.

**Paso 6: Finalización y Logging**

1.  **Informe Final:** Una vez que la tarea se considera completada (ya sea con éxito, con errores no resueltos después de intentos de corrección, o cancelada por el usuario), el GPO presenta un informe final al usuario.
2.  **Registro Completo:** El Módulo de Logging y Monitorización (MLM) asegura que todo el flujo, incluyendo la entrada inicial, los prompts enviados a Gemini, las respuestas recibidas, las acciones intentadas y sus resultados, y cualquier error, quede registrado para futura referencia o depuración.

Este flujo de trabajo detallado busca ser robusto, permitiendo la intervención del usuario en puntos críticos y facilitando un mecanismo de corrección iterativo con la ayuda de Gemini. La modularidad de la arquitectura soporta la implementación de cada uno de estos pasos de manera independiente y bien definida.
