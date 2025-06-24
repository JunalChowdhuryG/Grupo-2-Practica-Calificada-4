# **Grupo 2 Practica Calificada 4 Proyecto 3: "Orquestador de flujos de trabajo basado en eventos (Local)"**

## **Integrantes**
| Integrante                         | Codigo    | Repositorio Personal del Proyecto                                                 |
| ---------------------------------- | --------- | --------------------------------------------------------------------------------- |
| Chowdhury Gomez, Junal Johir       | 20200092K | [JunalChowdhuryG](https://github.com/JunalChowdhuryG/Proyecto-3-Personal-Grupo-2) |
| La Torre Vasquez, Andres Sebastian | 20212100C | [Jun1el](https://github.com/Jun1el/Proyecto-3-Personal-Grupo-2)                   |
| Zapata Inga, Janio Adolfo          | 20212636K | [Janiopi](https://github.com/Janiopi/Proyecto-3-Personal-Grupo-2)                 |

## Estructura del Proyecto

- **`src/`**: Codigo fuente principal (motor de eventos, scripts Python)
- **`scripts/`**: Scripts Bash para acciones automatizadas
- **`docs/`**: Documentacion y archivos de configuracion de workflows
- **`data/`**: Carpeta monitoreada para eventos de archivos
- **`reports/`**: Logs y reportes generados por el sistema
- **`Dockerfile` y `docker-compose.yml`**: Configuracion de contenedores y servicios
- **`requirements.txt`**: Dependencias de Python

## Sprint 1: Motor de eventos y ejecutores básicos

### Objetivo
Desarrollar un motor de eventos local capaz de detectar la creacion de archivos y ejecutar scripts asociados, ademas de sentar las bases para la integracion con colas de mensajes.

### Funcionalidades Implementadas
- **Motor de eventos (`src/event_engine.py`)**:  
  Monitorea la carpeta `/app/data` y ejecuta acciones definidas en `docs/workflows.yaml` al detectar nuevos archivos.
- **Configuracion de workflows (`docs/workflows.yaml`)**:  
  Define que accion ejecutar ante cada tipo de evento.
- **Scripts de ejemplo**:  
  - `scripts/process_data.sh`: Procesa archivos nuevos y registra logs.
  - `src/notify.py`: Registra notificaciones en logs.
- **Integracion con Redis**:  
  Configuración de Docker Compose para levantar un servicio de cola de mensajes (Redis) para futuras expansiones.

### Cómo funciona
1. El motor de eventos lee la configuracion de `docs/workflows.yaml`
2. Monitorea la carpeta `/app/data` en busca de nuevos archivos
3. Al detectar un archivo nuevo, ejecuta el script `process_data.sh` con el archivo como argumento
4. También puede ejecutar scripts Python como `notify.py` al recibir mensajes en la cola Redis
---

## Issues y Asignaciones SPRINT 1

## [1] Configuracion del Repositorio GitHub

- Historia de Usuario
   - **Como** desarrollador  
   - **Necesito** un repositorio GitHub configurado con ramas protegidas y plantillas de issues  
   - **Para que** el equipo pueda colaborar de manera organizada y mantener la calidad del codigo
- Responsable: **Junal**
## [2] Creacion de Hook para Formato de Commits

- Historia de Usuario
    - **Como** desarrollador  
    - **Necesito** un hook de Git para estandarizar el formato de los mensajes de commit  
    - **Para que** los commits sean consistentes y cumplan con las rubricas de commits atomicos
- Responsable: **Andres**
## [3] Implementacion del Motor de Eventos

- Historia de Usuario
    - **Como** desarrollador  
    - **Necesito** un motor de eventos que detecte la creacion de archivos y mensajes en Redis  
    - **Para que** el sistema pueda orquestar flujos de trabajo basados en eventos

## [4] Configuracion del Entorno Docker

- Historia de Usuario
    - **Como** desarrollador  
    - **Necesito** un entorno dockerizado reproducible  
    - **Para que** el sistema sea portatil y consistente en todos los entornos
- Responsable: **Junal**
## [5] Creacion de Scripts para Registro de Mensajes

- Historia de Usuario
    - **Como** desarrollador  
    - **Necesito** scripts para procesar archivos creados y mensajes Redis  
    - **Para que** el sistema ejecute acciones basadas en eventos de manera automatizada
- Responsable: **Andres**

## [6] Implementación de Pruebas Unitarias

- Historia de Usuario
    - **Como** desarrollador  
    - **Necesito** pruebas unitarias para el motor de eventos  
    - **Para que** el sistema sea robusto y cumpla con la cobertura requerida
- Responsable: **Junal**

## [7] Documentacion Sprint 1
- Responsable: **Andres**

## Guia de Uso

### Requisitos
- Docker y Docker Compose instalados.

### Instrucciones 
1. Clona el repositorio.
   ```bash
   git clone git@github.com:JunalChowdhuryG/Grupo-2-Practica-Calificada-4.git
   cd Grupo-2-Practica-Calificada-4
   ```
2. Aseguramos permisos de escritura en carpetas compartidas
   ```bash
   chmod -R 777 data reports
   ```
3. Construye y levanta los servicios
   ```sh
   docker-compose up --build
   ```
4. Probamos el flujo de archivos:
   ```bash
   # Creamos contenido en `data/` y observamos los logs en `reports/`.
   echo "contenido de prueba" > data/ejemplo.txt
   ```
  
5. Para probar notificaciones:
   ```bash
   docker-compose exec redis redis-cli publish notifications "Hello"
   ```
6. Ejecutar pruebas unitarias:
   ```bash
   docker-compose run event-engine pytest tests/ --cov=src --cov-report=term-missing
   ```
---
