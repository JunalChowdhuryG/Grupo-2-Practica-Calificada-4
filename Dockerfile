FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

#instalar dependencias
RUN pip install -r requirements.txt

#crear directorios
RUN mkdir -p /app/data /app/reports

#Copiar el resto del codigo
COPY . .

#permisos escritura
RUN echo "chmod -R 777 /app/data /app/reports" > /app/init.sh
#permisos ejecucion
RUN chmod +x /app/init.sh

#ejecucion
CMD ["/bin/bash", "-c", "/app/init.sh && python src/event_engine.py"]