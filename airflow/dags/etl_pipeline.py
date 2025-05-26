# etl_pipeline.py
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime, timedelta
from kubernetes.client import models as k8s

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

    raw_vol = k8s.V1Volume(
        name='raw',
        persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
            claim_name='data-pvc'
        ),
    )
    transformed_vol = k8s.V1Volume(
        name='transformed',
        persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
            claim_name='transformed-pvc'
        ),
    )

    raw_mount = k8s.V1VolumeMount(name='raw', mount_path='/data')
    transformed_mount = k8s.V1VolumeMount(name='transformed', mount_path='/transformed')

    extract = KubernetesPodOperator(
        task_id='extract',
        name='extract',
        namespace='airflow',
        image='etl_extractor:latest',
        image_pull_policy='Never',
        cmds=['python', 'main.py', 'extract'],
        env_vars={
            "PUSHGATEWAY": "http://pushgateway.monitoring.svc.cluster.local:9091"
        },
        volumes=[raw_vol, transformed_vol],
        volume_mounts=[raw_mount, transformed_mount],
        in_cluster=True,
        get_logs=True,
        service_account_name='airflow-sa',
    )

    transform = KubernetesPodOperator(
        task_id='transform',
        name='transform',
        namespace='airflow',
        image='etl_transformer:latest',
        image_pull_policy='Never',
        env_vars={
            "PUSHGATEWAY": "http://pushgateway.monitoring.svc.cluster.local:9091"
        },
        cmds=['python', 'main.py', 'transform'],
        volumes=[raw_vol, transformed_vol],
        volume_mounts=[raw_mount, transformed_mount],
        in_cluster=True,
        get_logs=True,
        service_account_name='airflow-sa',
    )

    load = KubernetesPodOperator(
        task_id='load',
        name='load',
        namespace='airflow',
        image='etl_loader:latest',
        image_pull_policy='Never',
        env_vars={
            "PUSHGATEWAY": "http://pushgateway.monitoring.svc.cluster.local:9091"
        },
        cmds=['python', 'main.py', 'load'],
        volumes=[raw_vol, transformed_vol],
        volume_mounts=[raw_mount, transformed_mount],
        in_cluster=True,
        get_logs=True,
        is_delete_operator_pod=False,
        service_account_name='airflow-sa',
    )

    extract >> transform >> load
