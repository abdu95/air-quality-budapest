# air-quality-budapest

Problem statement (Budapest air quality context, why it matters)
Architecture diagram (simple ASCII or image)
Tech stack table with explanation of each tool
Step-by-step reproduction guide:

Clone repo
Set up .env from .env.example
Run Terraform
docker compose up
Trigger Airflow DAG
Run dbt
Open Looker dashboard link


Dashboard screenshot



1. I tested openaq API and received data
test_api_openaq_budapest.py

2. I used Airflow in Docker to check how Airflow can fetch data from API and save in parquet
get_airdata_openaq_dag.py

3. Google Cloud
Created project in Google Cloud Console
airquality-bp-dezoomcamp

Create a bucket in GCS
gs://airquality_bp_bucket
