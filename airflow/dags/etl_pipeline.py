from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

default_args = {
    'owner': 'etl_team',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='etl_pipeline',
    default_args=default_args,
    description='ETL pipeline using DockerOperator',
    schedule_interval='@hourly',
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    extract = DockerOperator(
        task_id='extract',
        image='etl_extractor:latest',
        api_version='auto',
        network_mode='bridge',
        mounts=['/tmp/etl/data:/data'],
    )

    transform = DockerOperator(
        task_id='transform',
        image='etl_transformer:latest',
        api_version='auto',
        network_mode='bridge',
        mounts=[
            '/tmp/etl/data:/data',
            '/tmp/etl/transformed:/transformed',
        ],
    )

    load = DockerOperator(
        task_id='load',
        image='etl_loader:latest',
        api_version='auto',
        network_mode='bridge',
        mounts=['/tmp/etl/transformed:/transformed'],
        environment={
            'DB_HOST': 'postgres',
            'DB_PORT': '5432',
            'DB_NAME': 'etl_db',
            'DB_USER': 'etl_user',
            'DB_PASSWORD': 'password',
        }
    )

    extract >> transform >> load
