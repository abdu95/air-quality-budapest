from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime, timezone, timedelta
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from openaq import OpenAQ
import os

LOCATION_ID = 783927


def fetch_openaq(**context):
    date_from = (context["data_interval_start"] - timedelta(hours=2)).isoformat()
    date_to   = (context["data_interval_end"] - timedelta(hours=2)).isoformat()

    api_key = Variable.get("openaq_api_key")
    client  = OpenAQ(api_key=api_key)

    response = client.locations.get(LOCATION_ID)
    location = response.results[0]

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
                "location_id":  location.id,
                "sensor_id":    sensor.id,
                "parameter":    sensor.parameter.name,
                "display_name": sensor.parameter.display_name,
                "value":        m.value,
                "unit":         sensor.parameter.units,
                "datetime_from": m.period.datetime_from.utc,
                "datetime_to":   m.period.datetime_to.utc,
            })

    client.close()
    context["ti"].xcom_push(key="records", value=records)


def save_parquet(**context):
    records = context["ti"].xcom_pull(key="records", task_ids="fetch_openaq")

    if not records:
        print("No records returned, skipping write.")
        return

    df = pd.DataFrame(records)
    df["datetime_from"] = df["datetime_from"].astype("datetime64[us, UTC]")
    df["datetime_to"]   = df["datetime_to"].astype("datetime64[us, UTC]")
    df["_ingested_at"]  = datetime.now(timezone.utc)

    window_start = context["data_interval_start"]
    path = (
        f"/opt/airflow/data/"
        f"date={window_start.strftime('%Y-%m-%d')}/"
        f"hour={window_start.strftime('%H')}/"
    )
    os.makedirs(path, exist_ok=True)

    table = pa.Table.from_pandas(df)
    pq.write_table(table, path + "measurements.parquet")
    print(f"Saved {len(df)} rows to {path}")


with DAG(
    dag_id="openaq_budapest_ingestion",
    schedule_interval="0 * * * *",   # every hour
    start_date=datetime(2026, 4, 14),
    catchup=False,
    default_args={"retries": 1},
) as dag:

    fetch = PythonOperator(task_id="fetch_openaq",  python_callable=fetch_openaq)
    save  = PythonOperator(task_id="save_parquet",  python_callable=save_parquet)

    fetch >> save