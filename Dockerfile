# Usa una imagen de Python ligera
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los requisitos e instálalos
COPY api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia los archivos de la API
COPY api/ /app/

# Expone el puerto donde correrá FastAPI
EXPOSE 8000

# Comando para correr la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

