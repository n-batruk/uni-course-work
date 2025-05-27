# CI/CD ELT Pipeline on Kubernetes with Airflow & Prometheus

This repository contains a modern ELT (Extract → Load → Transform) pipeline using:

* **Apache Airflow** (KubernetesPodOperator, TaskFlow ELT) for orchestration
* **PostgreSQL** as the single source of truth (raw + transformed tables)
* **Prometheus** & **Pushgateway** for metrics collection
* **Grafana** for visualization
* **Docker Desktop Kubernetes** for local cluster testing
* **GitHub Actions** for CI/CD

---

## Repository Layout

```text
├── .github/
│   └── workflows/                     # CICD pipelines
│
├── airflow/
│   └── dags/                          # Dags scripts and their requirements
│
├── docker/                            # Dockerfiles for etl and airflow scripts
│
├── etl_extractor/                     # Scripts and requirements for extraction step
│                
├── etl_transformer/                   # Scripts and requirements for transform step
│
├── k8s/
│   ├── airflow/                       # Airflow manifests
│   ├── database/                      # Postgres manifests
│   └── monitoring/
│       ├── grafana/                   # Graphana manifests
│       ├── prometheus/                # Prometheus manifests
│       └── pushgateway/               # Pushgateway manifests 
│
├── docs/                              # Documentation and architecture diagrams
│   └── ...
│
├── docker-compose.yml                 # Local dev Docker stack
├── README.md                          # Project overview and instructions

```

---

## Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop) with **Kubernetes** enabled
* [kubectl](https://kubernetes.io/docs/tasks/tools/) v1.24+
* [Airflow CLI](https://airflow.apache.org/docs/) (optional, for local triggers)
* A Docker registry account (Docker Hub, GHCR, etc.) for image pushes

---

## Local Setup with Docker Desktop Kubernetes

1. **Enable Kubernetes** in Docker Desktop settings. Ensure `kubectl` context is set to `docker-desktop`.

2. **Build & tag Docker images**

   ```bash
   docker compose build -f docker-compose.yml
   ```

3. **Apply Namespaces**

   ```bash
   kubectl apply -f k8s/airflow/namespace.yaml
   kubectl apply -f k8s/database/namespace.yaml
   kubectl apply -f k8s/monitoring/namespace.yaml
   ```

4. **Deploy Postgres**

   ```bash
   kubectl apply -R -f k8s/database/
   ```

5. **Deploy Airflow**

   ```bash
   kubectl apply -R -f k8s/airflow/
   ```

6. **Deploy Monitoring stack**

   ```bash
   kubectl apply -R -f k8s/monitoring/
   ```

---

## Verifying the Stack

* **Airflow UI:**  `kubectl port-forward -n airflow svc/airflow-web-service 8080:8080` → [http://localhost:8080](http://localhost:8080)
* **Prometheus UI:**  `kubectl port-forward -n monitoring svc/prometheus 9090:9090` → [http://localhost:9090](http://localhost:9090)
* **Pushgateway:**    `kubectl port-forward -n monitoring svc/pushgateway 9091:9091` → [http://localhost:9091/metrics](http://localhost:9091/metrics)
* **Grafana UI:**     `kubectl port-forward -n monitoring svc/grafana 3000:3000` → [http://localhost:3000](http://localhost:3000) (default `admin`/`admin`)

---

## Running the ELT Pipeline

1. **Initialize Airflow metadata DB** (scheduler initContainer does this automatically).
2. **Create admin user**

   ```bash
   kubectl apply -n airflow -f airflow/create-admin-job.yaml
   ```
3. **Trigger DAG**

   ```bash
   airflow dags trigger etl_pipeline
   ```
4. **Watch logs**

   ```bash
   kubectl -n airflow get pods -l dag_id=etl_pipeline,task_id=extract -w
   kubectl -n airflow logs <extract-pod> -f
   ```
5. **Verify data**

   ```bash
   kubectl -n etl-db exec -it svc/postgres -- psql -U etl_user -d etl_db \
     -c "\dt; SELECT COUNT(*) FROM raw_extracted; SELECT COUNT(*) FROM clean_comments;" \
     -c "SELECT COUNT(*) FROM agg_comments_by_post;"
   ```

---

## CI/CD with GitHub Actions

* Workflow: `.github/workflows/ci-cd.yaml`
* On push to `main`:

  1. Build & push images to your registry
  2. Deploy manifests via `kubectl apply` against Docker Desktop cluster

Customize environment variables and registry settings in the workflow as needed.
