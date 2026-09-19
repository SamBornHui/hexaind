import requests
from requests.auth import HTTPBasicAuth
import os
import logging
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from typing import List
from croniter import croniter
from app.services.workflows.scheduling.schemas import WFSchedule, RepeatType

from app.config.env_vars import airflow_environment

logger = logging.getLogger(__package__)


def pause_dag(dag_id: str, is_paused: bool):
    logger.info("Inside pause_dag function")
    airflow_url = str(airflow_environment.url)
    airflow_username = airflow_environment.username
    airflow_password = airflow_environment.password
    api_endpoint = f"{airflow_url}/api/v1/dags/{dag_id}?update_mask=is_paused"

    payload = {"is_paused": is_paused}
    headers = {"Content-Type": "application/json"}
    response = requests.patch(
        api_endpoint,
        json=payload,
        headers=headers,
        auth=HTTPBasicAuth(airflow_username, airflow_password),
    )
    logger.info(f"{response.json()}")
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"failed to pause/unpause dag {response.json()}")
        raise Exception(f"failed to pause/unpause dag {response.json()}")


def fetch_dag_next_run(dag_id: str):
    logger.info("Inside fetch_dag_next_run function")
    airflow_url = str(airflow_environment.url)
    airflow_username = airflow_environment.username
    airflow_password = airflow_environment.password
    api_endpoint = f"{airflow_url}/api/v1/dags/{dag_id}"

    # Headers
    headers = {"Content-Type": "application/json"}
    logger.info(f"{api_endpoint} , {airflow_username} {airflow_password}")
    # Make the GET request
    response = requests.get(
        api_endpoint,
        headers=headers,
        auth=HTTPBasicAuth(airflow_username, airflow_password),
    )
    logger.info(f"{response.json()}")
    if response.status_code == 200:
        dag_details = response.json()
        next_dag_run = dag_details.get("next_dagrun")
        next_dag_run_create_after = dag_details.get("next_dagrun_create_after")
        return {
            "next_dagrun": next_dag_run,
            "next_dagrun_create_after": next_dag_run_create_after
        }
    else:
        logger.error(f"Failed to fetch DAG details. Status Code: {response.status_code}")
        raise Exception(f"Failed to fetch DAG details. Status Code: {response.status_code}")

def get_prev_weekday_date(start_date: datetime, cron_week_day: int) -> datetime:
    dt_week_day = cron_week_day - 1
    if dt_week_day < 0:
        dt_week_day = 6
    
    given_dt_wd = start_date.weekday()
    if given_dt_wd == dt_week_day:
        return start_date - timedelta(days=7)
    else:
        days = (dt_week_day - given_dt_wd + 7) % 7
        return start_date + timedelta(days=(days-7))

def get_job_trigger_datetimes(wf_schedule: WFSchedule) -> List[str]:
    repeat_value = wf_schedule.repeat_value
    # Convert start_date and end_date to datetime objects
    date_format = "%Y-%m-%d %H:%M:%S"
    st_dt = datetime.strptime(wf_schedule.start_date, date_format)
    end_dt = datetime.strptime(wf_schedule.end_date, date_format)

    # Prepare the cron expression using the provided scheduled interval
    cron_expr = wf_schedule.scheduled_interval

    # Adjust the start date for correct initial interval alignment
    add_days = 0
    if wf_schedule.repeat_type == RepeatType.WEEKS:
        add_days = 6
    elif wf_schedule.repeat_type == RepeatType.MONTHS:
        next_month_dt = st_dt + relativedelta(months=1)
        add_days = (next_month_dt - st_dt).days - 1
    elif wf_schedule.repeat_type == RepeatType.YEARS:
        next_yr_dt = st_dt + relativedelta(years=1)
        add_days = (next_yr_dt - st_dt).days - 1

    st_dt += timedelta(days=add_days)

    # Initialize a cron iterator starting from the adjusted start date
    cron = croniter(cron_expr, st_dt)

    # Generate the next run times until we reach the end_date
    all_runs = []
    next_run = cron.get_next(datetime)

    # Collect all valid runs within the date range
    while next_run <= end_dt:
        all_runs.append(next_run)
        next_run = cron.get_next(datetime)

    # Apply repeat_value to skip occurrences based on repeat_type
    job_trigger_dt_times = []

    if wf_schedule.repeat_type == RepeatType.DAYS or \
       wf_schedule.repeat_type == RepeatType.MONTHS or \
       wf_schedule.repeat_type == RepeatType.YEARS:
        # Skip individual days based on repeat_value
        job_trigger_dt_times = [
            run.strftime(date_format)
            for index, run in enumerate(all_runs)
            if index % repeat_value == 0
        ]

    elif wf_schedule.repeat_type == RepeatType.WEEKS:
        # Group by weeks based on the days in the cron expression
        # For instance, if we have "0,1,2" (Sun, Mon, Tue), we treat each week as a group of 3 days.
        day_count_in_week = len(cron_expr.split()[-1].split(','))

        # Create groups of `day_count_in_week`
        week_groups = [
            all_runs[i:i + day_count_in_week]
            for i in range(0, len(all_runs), day_count_in_week)
        ]

        # Apply repeat_value to take every nth group of week days
        job_trigger_dt_times = [
            run.strftime(date_format)
            for index, week_group in enumerate(week_groups)
            if index % repeat_value == 0
            for run in week_group
        ]

    return job_trigger_dt_times

def get_next_job_time(job_times: list[str]) -> str:
    # Convert the list of datetime strings into timezone-aware datetime objects
    date_format = "%Y-%m-%d %H:%M:%S"
    job_times_dt = [datetime.strptime(time_str, date_format).replace(tzinfo=timezone.utc) for time_str in job_times]

    # Get the current system time in UTC
    current_time = datetime.now(timezone.utc)

    # Filter out times that are in the past
    future_times = [job_time for job_time in job_times_dt if job_time > current_time]

    # Sort the future times and get the first one
    if future_times:
        next_time = min(future_times)
        return next_time.strftime(date_format)
    else:
        return "Unknown"