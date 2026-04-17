import logging
import os
from datetime import datetime, timezone, timedelta

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from google.cloud import bigquery, storage

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from openaq import OpenAQ

log = logging.getLogger(__name__)

LOCATION_ID = 783927
BUCKET_NAME  = "airquality-bp-bucket-raw"
GCS_PREFIX   = "raw/openaq"
PROJECT_ID   = "airquality-bp-dezoomcamp"
BQ_DATASET   = "air_quality_dataset"
BQ_TABLE     = "measurements"


def fetch_openaq(**context):
    log.info("[fetch_openaq] Starting")
    date_from = (context["data_interval_start"] - timedelta(hours=2)).isoformat()
    date_to   = (context["data_interval_end"]   - timedelta(hours=2)).isoformat()
    log.info(f"[fetch_openaq] Window: {date_from} → {date_to}")

    client   = OpenAQ(api_key=Variable.get("openaq_api_key"))
    location = client.locations.get(LOCATION_ID).results[0]
    log.info(f"[fetch_openaq] Location: {location.name} (id={location.id})")

    records = []
    for sensor in location.sensors:
        measurements = client.measurements.list(
            sensors_id=sensor.id,
            data="hours",
            datetime_from=date_from,
            datetime_to=date_to,
            limit=24,
        )
        for m in measurements.results:
            records.append({
                "location_id":   location.id,
                "sensor_id":     sensor.id,
                "parameter":     sensor.parameter.name,
                "display_name":  sensor.parameter.display_name,
                "value":         m.value,
                "unit":          sensor.parameter.units,
                "datetime_from": m.period.datetime_from.utc,
                "datetime_to":   m.period.datetime_to.utc,
            })

    client.close()
    log.info(f"[fetch_openaq] Fetched {len(records)} records. Done")
    context["ti"].xcom_push(key="records", value=records)


def save_to_gcs(**context):
    log.info("[save_to_gcs] Starting")
    records = context["ti"].xcom_pull(key="records", task_ids="fetch_openaq")

    if not records:
        log.warning("[save_to_gcs] No records returned, skipping")
        return

    df = pd.DataFrame(records)
    df["datetime_from"] = df["datetime_from"].astype("datetime64[us, UTC]")
    df["datetime_to"]   = df["datetime_to"].astype("datetime64[us, UTC]")
    df["_ingested_at"]  = datetime.now(timezone.utc)

    window_start = context["data_interval_start"] - timedelta(hours=2)
    gcs_path = (
        f"{GCS_PREFIX}/"
        f"date={window_start.strftime('%Y-%m-%d')}/"
        f"hour={window_start.strftime('%H')}/"
        f"measurements.parquet"
    )

    local_path = "/tmp/measurements.parquet"
    pq.write_table(pa.Table.from_pandas(df), local_path)
    log.info(f"[save_to_gcs] Written local parquet: {len(df)} rows")

    gcs_client = storage.Client()

    # Create bucket if not exists
    try:
        gcs_client.get_bucket(BUCKET_NAME)
        log.info(f"[save_to_gcs] Bucket {BUCKET_NAME} already exists")
    except Exception:
        gcs_client.create_bucket(BUCKET_NAME, location="EU")
        log.info(f"[save_to_gcs] Created bucket {BUCKET_NAME}")

    gcs_client.bucket(BUCKET_NAME).blob(gcs_path).upload_from_filename(local_path)
    log.info(f"[save_to_gcs] Uploaded to gs://{BUCKET_NAME}/{gcs_path}. Done")
    context["ti"].xcom_push(key="gcs_path", value=gcs_path)


def load_to_bigquery(**context):
    log.info("[load_to_bigquery] Starting")
    gcs_path = context["ti"].xcom_pull(key="gcs_path", task_ids="save_to_gcs")

    if not gcs_path:
        log.warning("[load_to_bigquery] No GCS path, skipping")
        return

    uri = f"gs://{BUCKET_NAME}/{gcs_path}"
    log.info(f"[load_to_bigquery] Loading from {uri}")

    bq_client = bigquery.Client(project=PROJECT_ID)

    # Create dataset if not exists
    dataset_ref = bigquery.DatasetReference(PROJECT_ID, BQ_DATASET)
    try:
        bq_client.get_dataset(dataset_ref)
        log.info(f"[load_to_bigquery] Dataset {BQ_DATASET} already exists")
    except Exception:
        bq_client.create_dataset(dataset_ref)
        log.info(f"[load_to_bigquery] Created dataset {BQ_DATASET}")

    # Load parquet → BigQuery (creates table if not exists, appends if it does)
    # Partitioned by datetime_from (day), schema autodetected from parquet
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="datetime_from",
        ),
        clustering_fields=["parameter"],  # ← add this

    )

    table_ref = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
    load_job  = bq_client.load_table_from_uri(uri, table_ref, job_config=job_config)
    load_job.result()
    log.info(f"[load_to_bigquery] Loaded {load_job.output_rows} rows to {table_ref}. Done")


with DAG(
    dag_id="openaq_budapest_ingestion",
    schedule_interval="0 * * * *",
    start_date=datetime(2026, 4, 14),
    catchup=False,
    default_args={"retries": 1},
) as dag:

    fetch = PythonOperator(task_id="fetch_openaq",     python_callable=fetch_openaq)
    save  = PythonOperator(task_id="save_to_gcs",      python_callable=save_to_gcs)
    load  = PythonOperator(task_id="load_to_bigquery", python_callable=load_to_bigquery)

    fetch >> save >> load