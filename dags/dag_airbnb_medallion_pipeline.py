from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
}

with DAG(
    dag_id='dag_airbnb_medallion_pipeline',
    default_args=default_args,
    description='Pipeline nạp và chuyển đổi Medallion BigQuery + Train ML',
    schedule_interval=None,
    catchup=False,
    tags=['airbnb', 'dbt', 'bigquery', 'medallion', 'ml'],
) as dag:

    task_ingest_bronze = BashOperator(
        task_id='ingest_bronze_layer',
        bash_command='python /opt/airflow/dags/scripts/ingest_bronze.py',
    )

    task_dbt_run = BashOperator(
        task_id='dbt_run_models',
        bash_command='cd /opt/airflow/dbt_project && dbt run',
    )

    task_dbt_test = BashOperator(
        task_id='dbt_test_models',
        bash_command='cd /opt/airflow/dbt_project && dbt test',
    )

    task_train_ml_model = BashOperator(
        task_id='train_pricing_ml_model',
        bash_command='python /opt/airflow/dags/scripts/train_pricing_model.py',
    )

    task_ingest_bronze >> task_dbt_run >> task_dbt_test >> task_train_ml_model