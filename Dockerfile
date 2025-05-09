# 1. Usar una imagen base de Python
FROM python:3.11-slim

# 2. Establecer variables de entorno útiles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_RUN_PORT 5001
ENV FLASK_DEBUG 1 
# Directorio por defecto dentro del contenedor donde el asistente operará
# Puede ser un punto de montaje para volúmenes.
ENV ASSISTANT_PROJECT_DIR /data_for_assistant 
# Opcional: para pasar la API Key de Gemini (ver mig_client.py modificado)
# ENV GEMINI_API_KEY="" 

# 3. Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# 4. (Opcional) Instalar dependencias del sistema si alguna librería Python las necesita
# RUN apt-get update && apt-get install -y --no-install-recommends gcc git \
#     && rm -rf /var/lib/apt/lists/*

# 5. Copiar el archivo de requerimientos e instalar dependencias de Python
# Esto se hace primero para aprovechar el caché de capas de Docker si no cambian.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar todo el contenido de la carpeta 'src' de tu proyecto al directorio '/app/src' en la imagen
# Esto incluye tu paquete 'asistente_codigo_local'
COPY ./src ./src

# 7. Crear directorios que la aplicación podría necesitar
RUN mkdir -p ${ASSISTANT_PROJECT_DIR}
# El logger escribe en /root/.asistente_codigo_local por defecto
RUN mkdir -p /root/.asistente_codigo_local 

# 8. Exponer el puerto en el que Flask se ejecutará dentro del contenedor
EXPOSE ${FLASK_RUN_PORT}

# 9. Comando para ejecutar la aplicación web
# app.py está en src/asistente_codigo_local/web_ui/app.py
# La modificación de sys.path en app.py se encarga de las importaciones.
CMD ["python", "src/asistente_codigo_local/web_ui/app.py"]

# --- Alternativa para producción con Gunicorn (ejemplo) ---
# Si usas Gunicorn, añádelo a requirements.txt
# WORKDIR /app/src/asistente_codigo_local/web_ui 
# CMD ["gunicorn", "--bind", "0.0.0.0:${FLASK_RUN_PORT}", "app:app"]