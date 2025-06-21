FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
#instalar librerias
RUN pip install -r requirements.txt
RUN mkdir -p /app/data /app/reports
#permisos escritura
RUN chmod -R 777 /app/data /app/reports
COPY . .
#permisos escritura
RUN echo "chmod -R 777 /app/data /app/reports" > /app/init.sh
#permisos ejecucion
RUN chmod +x /app/init.sh
CMD ["/bin/bash", "-c", "/app/init.sh && python src/event_engine.py"]