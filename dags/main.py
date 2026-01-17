from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import requests
from datetime import datetime
import pytz
import os
from pathlib import Path
import sys
from datetime import datetime, timedelta
import pendulum

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.models import Variable


#initialise path
sys.path.append(os.path.dirname(os.getcwd()))
sys.path.append(os.getcwd())

#allow timezone aware DAG
local_tz = pendulum.timezone("Asia/Singapore")


#################################
##---AirFlow DAG Definitions---##
#################################

with DAG(
    "main_dag",

    default_args={
        "depends_on_past": False,
        "email": ["airflow@example.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    description="Main ETL DAG",
    start_date=datetime(2021, 1, 1, tzinfo=local_tz),
    schedule_interval='*/15 7-21 * * *', 
    catchup=False,
    tags=["scrape"]
) as dag:

    t_scrape = DockerOperator(
        task_id="run_activesg_scrape",
        image="poewun/activesg-scrape:latest",
        command="python main.py",
        docker_url="unix://var/run/docker.sock",
        auto_remove=True,
        network_mode="bridge"
    )

    t_scrape