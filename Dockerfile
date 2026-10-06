FROM python:3.11-slim

WORKDIR /app

# Copiar archivos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Ejecutar la inyección en el núcleo de Streamlit
RUN python inject_pwa.py

# Exponer el puerto
EXPOSE 8501

# Iniciar la aplicación
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
