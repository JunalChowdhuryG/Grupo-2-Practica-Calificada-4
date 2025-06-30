# **Grupo 2 Practica Calificada 4 Proyecto 3: "Orquestador de flujos de trabajo basado en eventos (Local)"**

## **Integrantes**
| Integrante                         | Codigo    | Repositorio Personal del Proyecto                                                 |
| ---------------------------------- | --------- | --------------------------------------------------------------------------------- |
| Chowdhury Gomez, Junal Johir       | 20200092K | [JunalChowdhuryG](https://github.com/JunalChowdhuryG/PC4-Chowdhury-Proyecto-3-Grupo-2) |
| La Torre Vasquez, Andres Sebastian | 20212100C | [Jun1el](https://github.com/Jun1el/Repo-personal-Proyecto3-Grupo2-PC4)                   |
| Zapata Inga, Janio Adolfo          | 20212636K | [Janiopi](https://github.com/Janiopi/Orquestador-de-flujos-basado-en-eventos)                 |

## **Videos**

- **Sprint 1:** [https://youtu.be/Z1AAJkgW170](https://youtu.be/Z1AAJkgW170)
- **Sprint 2:** [https://www.youtube.com/watch?v=DnACQzOHIfs](https://www.youtube.com/watch?v=DnACQzOHIfs)
- **Sprint 3:** [https://www.youtube.com/watch?v=dUviqheerLo](https://www.youtube.com/watch?v=dUviqheerLo)


## Prerrequisitos para el funcionamiento del proyecto

1. **Docker Desktop**:
   - Descarga e instala desde [docker.com](https://www.docker.com/products/docker-desktop).
   - Verifica:
     ```bash
     docker --version
     docker-compose --version
     ```

2. **Kind**:
   - Descarga: `curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.23.0/kind-windows-amd64.exe`.
   - Mueve a `~/kind` y añade al PATH.
   - Verifica:
     ```bash
     kind --version
     ```

3. **kubectl**:
   - Descarga: `curl -LO "https://dl.k8s.io/release/v1.30.0/bin/windows/amd64/kubectl.exe"`.
   - Mueve a `~/kubectl` y añade al PATH.
   - Verifica:
     ```bash
     kubectl version --client
     ```
(La instalación puede variar según el sistema operativo, seguir las instrucciones de la documentación oficial en caso de errores)


## Configuración del entorno

1. **Otorgar permisos de ejecución al script**:
   - Asegúrate de que `scripts/process_data.sh` tenga permisos de ejecución:
     ```bash
     chmod +x scripts/process_data.sh
     ```

2. **Otorgar permisos a directorios**:
   - Configura permisos de escritura para los directorios `data` y `reports`:
     ```bash
     chmod -R 777 data reports
     ```

3. **Configurar el clúster Kind**:
   - Crea un clúster Kind:
     ```bash
     kind create cluster --name my-cluster
     ```
   - Exporta el archivo de configuración:
     ```bash
     kind get kubeconfig --name my-cluster > kubeconfig.yaml
     ```
   - Obtén la IP del nodo de control:
     ```bash
     docker inspect my-cluster-control-plane | grep IPAddress
     ```
     - Ejemplo de salida:
       ```
       "IPAddress": "172.18.0.2",
       ```
   - Edita `kubeconfig.yaml` y actualiza el campo `server` con la IP correcta:
     ```yaml
     server: https://172.18.0.2:6443
     ```
     **Nota:** Ten encuenta que tambien se debe colocar el puerto `6443` a pesar de que el archivo `kubeconfig.yaml` mencione otro puerto.


## **¿Cómo ejecutar el proyecto?**

1. **Construir y ejecutar los servicios**:
   - Usa `docker-compose` para construir y levantar los contenedores:
     ```bash
     docker-compose up --build
     ```
    (Nota: En algunas versiones, el comando funcionaría con "docker compose")

2. **(Opcional) Verificar contenedores**:
   - Comprueba que los contenedores `event-engine` y `redis` estén corriendo:
     ```bash
     docker ps
     ```

## Probar los flujos de trabajo

El proyecto incluye tres flujos definidos en `docs/workflows.yaml`: `process_file`, `k8s_nginx`, y `notify_message`. Sigue estos pasos para probarlos.

1. **Flujo `process_file`**:
   - Crea un archivo en el directorio `data`:
     ```bash
     echo "contenido de prueba" > data/ejemplo.txt
     ```
   - Verifica el resultado:
     ```bash
     cat reports/processed_files.log
     ```
     - Salida esperada:
       ```
       2025-06-28 20:10:00 - Procesando: /app/data/ejemplo.txt
       contenido de prueba
       ```

2. **Flujo `k8s_nginx`** (depende de `process_file`):
   - Asegúrate de que `process_file` se haya ejecutado primero (ver paso anterior).
   - Crea un archivo en el directorio `data/k8s`:
     ```bash
     mkdir -p data/k8s
     touch data/k8s/trigger.txt
     ```
   - Verifica los logs:
     ```bash
     cat reports/k8s_deploy.log
     ```
     - Salida esperada:
       ```
       2025-06-28 20:10:00,123 - INFO - Aplicando deployment/nginx-deployment en namespace default
       2025-06-28 20:10:00,456 - INFO - Despliegue nginx-deployment creado en namespace default
       2025-06-28 20:10:00,789 - INFO - Aplicando service/nginx-service en namespace default
       2025-06-28 20:10:00,912 - INFO - Servicio nginx-service creado en namespace default
       2025-06-28 20:10:04,012 - INFO - Despliegue nginx-deployment listo: 1/1
       ```
   - Verifica el estado del flujo:
     ```bash
     cat data/workflow_state.json
     ```
     - Salida esperada:
       ```json
       {
         "process_file": "success",
         "k8s_nginx": "success"
       }
       ```
   - Verifica los recursos en Kubernetes:
     ```bash
     kubectl get pods
     kubectl get services
     ```
     - Salida esperada para `kubectl get pods`:
       ```
       NAME                              READY   STATUS    RESTARTS   AGE
       nginx-deployment-...              1/1     Running   0          1m
       ```
     - Salida esperada para `kubectl get services`:
       ```
       NAME                TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
       kubernetes          ClusterIP   10.96.0.1      <none>        443/TCP   81m
       nginx-service       ClusterIP   10.96.x.x      <none>        80/TCP    1m
       ```

3. **Flujo `notify_message`**:
   - Publica un mensaje en la cola de Redis:
     ```bash
     docker-compose exec redis redis-cli publish notifications "Hello"
     ```
   - Verifica el resultado:
     ```bash
     cat reports/notify.log
     ```
     - Salida esperada:
       ```
       2025-06-28 20:10:00 - INFO - Received message: Hello
       ```

4. **Probar dependencias**:
   - Intenta ejecutar `k8s_nginx` sin haber ejecutado `process_file`:

   Borrando el workflow_state
    ```bash
     rm -f data/workflow_state.json
    ```

    Creando un nuevo directorio k8s en data
    ```bash
    mkdir -p data/k8s
    ```
    
    Modificando el trigger.txt dentro de data/k8s
    ```bash
    touch data/k8s/trigger.txt
    ```

    Imprimiendo los reportes de event_engine
    ```bash
    cat reports/event_engine.log
    ```
  
    - Salida esperada (en los logs):
       ```
       2025-06-28 20:10:00,123 - WARNING - Dependencias no cumplidas para workflow k8s_nginx
       ```
   - Ejecuta `process_file` primero y repite:
    ```bash
     echo "contenido de prueba" > data/ejemplo.txt
    ```
     
    ```bash
     touch data/k8s/trigger.txt
    ```

    ```bash
      cat data/workflow_state.json
    ```

     - Salida esperada:
       ```json
       {
         "process_file": "success",
         "k8s_nginx": "success"
       }
       ```
## Ejecutar pruebas unitarias

1. **Ejecutar pruebas**:
   - Corre las pruebas unitarias con cobertura:
     ```bash
     docker-compose run event-engine pytest tests/ --cov=src --cov-report=term-missing
     ```
   - Verifica que todas las pruebas pasen y que la cobertura sea superior al 90%.
   