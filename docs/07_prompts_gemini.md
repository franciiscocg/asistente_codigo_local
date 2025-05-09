## 7. Definir la Estructura de los Prompts para Gemini

La calidad y utilidad de las respuestas de Gemini dependen en gran medida de la claridad, especificidad y estructura de los prompts que la aplicación "Asistente de Código Local" le envíe. Una ingeniería de prompts efectiva es esencial para guiar a Gemini a comprender su rol, el contexto de la tarea, y el formato de respuesta esperado. Esta sección describe cómo deberían estructurarse los prompts iniciales y los de seguimiento para correcciones.

**Principios Generales para la Estructura de Prompts:**

1.  **Claridad y Concisión:** Los prompts deben ser directos y evitar ambigüedades. Aunque se puede proporcionar contexto detallado, la instrucción principal debe ser fácil de entender.
2.  **Especificidad del Rol:** Definir claramente el rol de Gemini como un asistente de desarrollo de software que puede proponer cambios en archivos, crear nuevos archivos, eliminarlos y sugerir comandos de consola.
3.  **Contexto Relevante:** Incluir el contexto del proyecto necesario (ver Sección 4) de manera estructurada dentro del prompt o como parte de la conversación si la API lo soporta (ej. historial de mensajes).
4.  **Formato de Salida Esperado:** Instruir explícitamente a Gemini sobre el formato de respuesta deseado (JSON, como se detalla en la Sección 3), incluyendo el esquema si es posible o ejemplos.
5.  **Manejo de Incertidumbre:** Animar a Gemini a solicitar aclaraciones (`REQUEST_CLARIFICATION`) si la tarea no está clara o si necesita más información, en lugar de adivinar.
6.  **Iteración:** Diseñar los prompts para que funcionen bien en un flujo conversacional, donde las respuestas de Gemini pueden llevar a prompts de seguimiento.

**1. Estructura del Prompt Inicial (Primera Interacción para una Nueva Tarea)**

El prompt inicial establece el escenario para la interacción con Gemini. Debería contener varios componentes clave:

*   **A. System Prompt o Instrucción de Rol Principal (puede ser parte del primer mensaje de usuario si la API no tiene un system prompt separado):**
    *   **Definición del Rol:** "Eres 'Asistente de Código Local', una IA experta en desarrollo de software. Tu propósito es ayudar a los usuarios a modificar sus proyectos de código. Puedes proponer la creación de nuevos archivos, la modificación de archivos existentes (proporcionando el contenido completo o un parche en formato diff unificado), la eliminación de archivos y la ejecución de comandos de consola dentro del directorio del proyecto."
    *   **Instrucción de Formato de Salida:** "Todas tus respuestas deben estar estrictamente en formato JSON, siguiendo este esquema: [Aquí se podría incluir una versión simplificada del esquema JSON o un recordatorio clave, ej: `{"summary": "...", "actions": [{"type": "ACTION_TYPE", ...}]}`]. No incluyas explicaciones o texto fuera del objeto JSON principal. Los tipos de acción válidos son: `CREATE_FILE`, `MODIFY_FILE`, `DELETE_FILE`, `EXECUTE_COMMAND`, `REQUEST_CLARIFICATION`, `INFO_MESSAGE`."
    *   **Restricciones de Seguridad (Recordatorio):** "Todas las rutas de archivo deben ser relativas al directorio raíz del proyecto. No sugieras comandos que operen fuera de este directorio o que sean inherentemente destructivos sin una justificación muy clara. Prioriza la seguridad y la reversibilidad de las acciones."
    *   **Manejo de Ambigüedad:** "Si la solicitud del usuario es ambigua o necesitas más información para proceder de manera segura y efectiva, utiliza la acción `REQUEST_CLARIFICATION`."

*   **B. Contexto del Proyecto (Proporcionado por el GCP):**
    *   Esta sección se poblará dinámicamente por el Gestor de Contexto del Proyecto.
    *   **Ejemplo de cómo podría estructurarse dentro del prompt:**
        ```
        --- INICIO CONTEXTO DEL PROYECTO ---
        Directorio Raíz: /ruta/al/proyecto/usuario
        Estructura de Archivos (resumida):
        - src/
          - main.js
          - components/
            - Button.js
        - package.json

        Contenido de Archivos Relevantes:
        ### src/main.js ###
        // Contenido de main.js...
        
        ### package.json ###
        // Contenido de package.json...

        (Otros elementos de contexto como rama git, errores previos si es una continuación, etc.)
        --- FIN CONTEXTO DEL PROYECTO ---
        ```

*   **C. Petición Específica del Usuario:**
    *   La descripción en lenguaje natural proporcionada por el usuario.
    *   **Ejemplo:** "Usuario: Necesito añadir una nueva función a `src/main.js` que se llame `calculateTotal` y que reciba un array de números y devuelva su suma. Luego, importa y usa esta función en `src/components/Button.js` para mostrar el total cuando se hace clic en un botón (puedes añadir un nuevo botón o modificar uno existente). Asegúrate de que `calculateTotal` maneje arrays vacíos devolviendo 0."

*   **D. Ejemplos (Few-Shot Learning - Opcional pero muy recomendado para el formato):**
    *   Incluir un ejemplo completo de una interacción simple (Usuario + Contexto -> Respuesta JSON de Gemini) puede mejorar drásticamente la adherencia al formato.

**Ejemplo de Prompt Inicial Consolidado (simplificado):**

```
Eres 'Asistente de Código Local', una IA experta en desarrollo de software. Tu propósito es ayudar a los usuarios a modificar sus proyectos de código. Puedes proponer la creación de nuevos archivos, la modificación de archivos existentes (proporcionando el contenido completo), la eliminación de archivos y la ejecución de comandos de consola. Todas tus respuestas deben estar estrictamente en formato JSON. No incluyas explicaciones fuera del objeto JSON. Tipos de acción: CREATE_FILE, MODIFY_FILE, DELETE_FILE, EXECUTE_COMMAND, REQUEST_CLARIFICATION, INFO_MESSAGE. Si la solicitud es ambigua, usa REQUEST_CLARIFICATION.

--- INICIO CONTEXTO DEL PROYECTO ---
Directorio Raíz: /project
Estructura de Archivos:
- main.py
Contenido de Archivos Relevantes:
### main.py ###
def hello():
  print("Hola")
--- FIN CONTEXTO DEL PROYECTO ---

Usuario: Modifica la función hello en main.py para que imprima "Hola, Mundo" en lugar de "Hola".

Asistente (Respuesta JSON esperada):
```
(La aplicación esperaría que Gemini complete a partir de aquí con el JSON)

**2. Estructura de los Prompts de Seguimiento (para Correcciones o Aclaraciones)**

Cuando la aplicación necesita interactuar nuevamente con Gemini después de una respuesta inicial (por ejemplo, si un comando falló o si Gemini solicitó una aclaración), el prompt de seguimiento debe construirse sobre la conversación anterior.

*   **A. Referencia a la Conversación Anterior:**
    *   La mayoría de las APIs de LLM permiten enviar un historial de mensajes (usuario, asistente, usuario, etc.). Esto es crucial para que Gemini entienda el contexto de la nueva solicitud.

*   **B. Información Nueva o Problemática:**
    *   **Para Corrección de Errores:**
        *   La acción que falló.
        *   El comando exacto que se ejecutó (si aplica).
        *   La salida estándar (`stdout`) y el error estándar (`stderr`) completos del comando.
        *   El estado actual de los archivos relevantes si fueron modificados parcialmente.
        *   **Ejemplo de instrucción:** "Usuario: La acción `EXECUTE_COMMAND` que propusiste anteriormente (`python script.py`) falló. Aquí está la salida:
            STDOUT:
            (ninguna)
            STDERR:
            Traceback (most recent call last):
              File "script.py", line 5, in <module>
                non_existent_function()
            NameError: name 'non_existent_function' is not defined
            Por favor, analiza este error y proporciona un nuevo plan de acciones en formato JSON para corregirlo. El archivo `script.py` actualmente contiene:
            ```python
            # contenido actual de script.py
            ```
            "

    *   **Para Responder a una `REQUEST_CLARIFICATION`:**
        *   La respuesta del usuario a la pregunta de Gemini.
        *   **Ejemplo de instrucción:** "Usuario: En respuesta a tu pregunta anterior ('¿Prefieres el enfoque A o B?'), elijo el 'Enfoque A (priorizar velocidad)'. Por favor, procede con el plan de acciones en formato JSON basado en esta elección."

*   **C. Reiteración de Expectativas (Opcional, si es necesario):**
    *   Si Gemini se desvió del formato en interacciones previas, se puede recordar sutilmente el formato de respuesta JSON esperado.

**Ejemplo de Prompt de Seguimiento para Corrección (simplificado, asumiendo historial de chat):**

*Mensaje Anterior del Asistente (Gemini):*
```json
{
  "summary": "Ejecuta el script principal.",
  "actions": [
    {
      "type": "EXECUTE_COMMAND",
      "command": "python main.py",
      "description": "Ejecuta el script principal."
    }
  ]
}
```

*Nuevo Mensaje del Usuario (Aplicación):*
```
La ejecución del comando "python main.py" falló con el siguiente error:
STDERR: ImportError: No module named 'requests'

Contexto Adicional:
### main.py ###
import requests
def main():
  print(requests.get('https://www.google.com').status_code)
if __name__ == "__main__":
  main()

Por favor, proporciona un plan JSON actualizado para solucionar este error de importación y luego ejecutar el script.
```

**Consideraciones Adicionales para Prompts:**

*   **Tokenización y Límites:** Ser consciente de los límites de tokens de la API de Gemini. Los prompts, especialmente con contexto extenso, pueden volverse grandes. Las estrategias de la Sección 4 para manejar el contexto son vitales aquí.
*   **Experimentación y Refinamiento:** La ingeniería de prompts es un proceso iterativo. Será necesario experimentar con diferentes formulaciones y estructuras para encontrar lo que funciona mejor con la versión específica de la API de Gemini que se esté utilizando.
*   **Temperatura y Otros Parámetros de la API:** Ajustar parámetros como la `temperatura` de la API de Gemini puede influir en la creatividad vs. la previsibilidad de las respuestas. Para tareas que requieren precisión y adherencia a formatos, una temperatura más baja (ej. 0.2 - 0.5) suele ser preferible.
*   **Evitar la Sobrecarga de Instrucciones:** Aunque es importante ser claro, un exceso de instrucciones contradictorias o demasiado complejas en un solo prompt puede confundir a la IA.

Al diseñar cuidadosamente estos prompts, el "Asistente de Código Local" puede maximizar la probabilidad de obtener respuestas útiles, estructuradas y seguras de Gemini, lo que es fundamental para el éxito del proyecto.
