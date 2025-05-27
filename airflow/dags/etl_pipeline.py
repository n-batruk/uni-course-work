from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime, timedelta

# Default arguments for all tasks
default_args = {
    'start_date': datetime(2025, 5, 25),
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='etl_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
) as dag:

    # Extract task: fetch and store raw payloads into Postgres and Push metrics
    extract = KubernetesPodOperator(
        task_id='extract',
        name='extract',
        namespace='airflow',
        image='etl_extractor:latest',
        image_pull_policy='Never',
        cmds=['python', 'main.py', 'extract'],
        env_vars={
            'PUSHGATEWAY': 'http://pushgateway.monitoring.svc.cluster.local:9091',
            'DB_HOST': 'postgres.etl-db.svc.cluster.local',
            'DB_PORT': '5432',
            'DB_NAME': 'etl_db',
            'DB_USER': 'etl_user',
            'DB_PASSWORD': 'strongPassword123',
        },
        in_cluster=True,
        get_logs=True,
        is_delete_operator_pod=False,
        service_account_name='airflow-sa',
    )

    # Transform task: read raw table, write cleaned and aggregated tables
    transform = KubernetesPodOperator(
        task_id='transform',
        name='transform',
        namespace='airflow',
        image='etl_transformer:latest',
        image_pull_policy='Never',
        cmds=['python', 'main.py', 'transform'],
        env_vars={
            'DB_HOST': 'postgres.etl-db.svc.cluster.local',
            'DB_PORT': '5432',
            'DB_NAME': 'etl_db',
            'DB_USER': 'etl_user',
            'DB_PASSWORD': 'strongPassword123',
        },
        in_cluster=True,
        get_logs=True,
        is_delete_operator_pod=False,
        service_account_name='airflow-sa',
    )

    extract >> transform
