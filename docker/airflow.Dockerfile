FROM apache/airflow:2.5.1

USER airflow
COPY airflow/requirements.txt .  
RUN pip install --no-cache-dir -r requirements.txt

COPY airflow/dags/ /opt/airflow/dags/