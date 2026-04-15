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
Machine type: e2-medium
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

