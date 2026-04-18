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


Enabled Google Cloud Services
Enabled BigQuery
Enabled APIs and Services
Enabled Compute Engine API
Enabled Cloud Storage API
Created a service account


Create the VM.

In the search bar type "Compute Engine" and click it
Click Create Instance
Configure it like this:

    Name: airflow-vm
    Region: europe-west3 (Frankfurt — close to Budapest)
    Machine type: e2-standard
    Boot disk: click Change → select Ubuntu 22.04 LTS → Select
    Boot disk size: change to 20 GB
    Firewall: check both Allow HTTP traffic and Allow HTTPS traffic


Click Create

SSH into the VM


    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg

    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    sudo groupadd docker
    sudo usermod -aG docker $USER
    newgrp docker
    docker --version

    sudo apt-get install -y git
    git clone https://github.com/abdu95/air-quality-budapest.git
    cd air-quality-budapest

    sudo apt-get install -y nano
    nano gcp-key.json

Copy paste json file content
Ctrl + X => Y => Enter

    echo "AIRFLOW_UID=50000" > .env
    nano docker-compose.yaml


Find the volumes: section (it already has dags, logs, plugins) and add two lines:
yamlvolumes:
    - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
    - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
    - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
    - ${AIRFLOW_PROJ_DIR:-.}/data:/opt/airflow/data
    - ${AIRFLOW_PROJ_DIR:-.}/gcp-key.json:/opt/airflow/gcp-key.json  # ← add this


Also add the environment variable so Google libraries can find the key. Find the environment: section and add:
yamlenvironment:
    GOOGLE_APPLICATION_CREDENTIALS: /opt/airflow/gcp-key.json

    docker compose up airflow-init

    docker compose up -d


Google console => Activate Shell > _

    gcloud config set project airquality-bp-dezoomcamp

    gcloud compute firewall-rules create allow-airflow \
        --allow tcp:8080 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow Airflow UI"


Then get your VM's external IP — in Compute Engine page you can see it next to airflow-vm.
Open in your browser:
http://YOUR_VM_EXTERNAL_IP:8080
Login with airflow / airflow as before.



mart_aqi_daily (dbt) — partition by date, cluster by aqi_category
    This is the table your dashboard queries. Dashboard will always filter by date range (temporal chart) and often by AQI category (categorical chart). 

Raw measurements table (Airflow) — add clustering_fields=["parameter"]
    This makes sense because every dbt query downstream will filter or group by parameter (you need to isolate pm25, no2, o3, pm10 separately to calculate sub-indices). One line change in your existing code:


The raw measurements table is partitioned by datetime_from (day) and clustered by parameter. All downstream dbt queries filter on a date range and isolate individual pollutants — partitioning eliminates full table scans across time, clustering reduces data scanned when filtering by pollutant type.

The mart_aqi_daily table is partitioned by measurement_date and clustered by aqi_category. The dashboard's temporal chart always queries a date range (partition pruning applies), and the categorical chart filters by AQI category (Good / Moderate / Poor etc.), which aligns directly with the cluster key.

Place your GCP service account key at gcp-key.json in the project root (not committed for security reasons)




Step: dbt 
    uv pip install dbt-bigquery
    uv pip freeze > requirements.txt
    dbt init air_quality_dbt

```
Db: bigquery
authentication: Service Account
keyfile: path
project id: airquality-bp-dezoomcamp
dataset: air_quality_dataset 
threads: 4
location: EU
```

profiles.yml 

```
air_quality_dbt:
  outputs:
    dev:
      dataset: air_quality_dataset
      job_execution_timeout_seconds: 300
      job_retries: 1
      keyfile: path\gcp-key.json
      location: EU
      method: service-account
      priority: interactive
      project: project_id
      threads: 4
      type: bigquery
  target: dev
```

add to gitignore: 
    # dbt
    air_quality_dbt/target/
    air_quality_dbt/dbt_packages/
    air_quality_dbt/logs/

    cd air_quality_dbt

Test the connection
    dbt debug 



```yaml
version: 2

sources:
  - name: openaq
    database: airquality-bp-dezoomcamp
    schema: air_quality_dataset
    tables:
      - name: measurements
        description: "Raw hourly measurements ingested by Airflow from OpenAQ API"
```

Add packages.yml 
    => dbt deps

Create these models in these order: 
    models/staging/stg_openaq__measurements.sql
    models/intermediate/int_aqi_sub_indices.sql
    models/mart/mart_aqi_daily.sql


dbt_project.yml 

```
models:
  air_quality_dbt:
    staging:
      +materialized: view
    intermediate:
      +materialized: view
    mart:
      +materialized: table

```




LayerMaterialization Why
stgviewIt's just a cleanup layer — no heavy logic, no aggregations. Keeping it as a view means no storage cost and it always reflects the latest raw data.

intview Intermediate logic, not consumed directly by end users. View keeps it inspectable for debugging 

marttableThis is what Power BI or any BI tool queries. You want it fast and pre-computed, not recalculated on every dashboard load.


    dbt run --select staging
    dbt run
    dbt test