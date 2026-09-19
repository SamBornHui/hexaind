import logging
import requests
import pandas as pd
import math
from app.config.env_vars import thermocalc_environment
from app.services.apps.thermocalc_web_service.schemas import ThermoCalcJob, ThermoCalcJobRegisterationRequest
from app.services.admin.connectors.schemas import Connector


logger = logging.getLogger(__package__)


def get_batches_count(csv_path: str, batch_size: int):
    df = pd.read_csv(csv_path)
    total_rows = df.shape[0]
    batch_count = math.ceil(total_rows / batch_size)
    return batch_count


def batches_data_generator(csv_path: str, batch_size: int):
    chunk_iter = pd.read_csv(csv_path, chunksize=batch_size)
    start_index = 0
    for chunk in chunk_iter:
        end_index = start_index + len(chunk)
        yield (start_index, end_index, chunk.to_dict(orient='records'))
        start_index = end_index

def create_job(run_id: str, action_id: str, file_path: str):
    url = f"http://{thermocalc_environment.thermo_calc_service_url}/v1/thermocalc/jobs"
    files = {"file": open(file_path, "rb")}
    data = {"run_id": run_id, "action_id": action_id}

    try:
        response = requests.post(url, files=files, params=data)
        response.raise_for_status()  # Raise an error for bad status codes
        job = ThermoCalcJob(**response.json())
        job_id = job.id
        logger.info(
            f"Job created successfully with ID: {job_id}, run_id: {run_id}, action_id: {action_id}"
        )
        return job_id
    except requests.HTTPError as e:
        raise ValueError(
            f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        )
    finally:
        files["file"].close()


def register_job(parent_job_id: str, payload: ThermoCalcJobRegisterationRequest):
    url = f"http://{thermocalc_environment.thermo_calc_service_url}/v1/thermocalc/jobs/{parent_job_id}/register"
    try:
        response = requests.post(url, json=payload.model_dump())
        response.raise_for_status()  # Raise an error for bad status codes
        logger.info(f"Job registered successfully with ID: {parent_job_id}")
    except requests.HTTPError as e:
        raise ValueError(
            f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        )


def receive_task(parent_job_id: str, data: dict, start_index: int, connection:Connector):
    url = f"http://{thermocalc_environment.thermo_calc_service_url}/v1/thermocalc/jobs/{parent_job_id}/receive_task"
    try:

            # Debugging logs
        logger.info(f"Connection object: {connection}")
        logger.info(f"Connection config: {connection.configuration}")
        response = requests.post(url, 
                                 params={
                                     "start_index": start_index,
                                     "TC23A_HOME": connection.configuration.path, 
                                     "TC23B_HOME": connection.configuration.path, 
                                     "LSHOST": connection.configuration.host,
                                     "connection_type":connection.type}, 
                                json=data)
        response.raise_for_status()  # Raise an error for bad status codes
        logger.info(f"Task received successfully for Job ID: {parent_job_id}")
    except requests.HTTPError as e:
        raise ValueError(
            f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        )


def complete_task(parent_job_id: str):
    url = f"http://{thermocalc_environment.thermo_calc_service_url}/v1/thermocalc/jobs/{parent_job_id}/complete_task"

    try:
        response = requests.post(url)
        response.raise_for_status()  # Raise an error for bad status codes
        logger.info(f"Task completed successfully for Job ID: {parent_job_id}")
    except requests.HTTPError as e:
        raise ValueError(
            f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        )


def get_status(parent_job_id: str) -> ThermoCalcJob:
    url = f"http://{thermocalc_environment.thermo_calc_service_url}/v1/thermocalc/jobs/{parent_job_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        return ThermoCalcJob(**response.json())
    except requests.HTTPError as e:
        raise ValueError(
            f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        )

def get_results_file(parent_job_id: str, destination_file_path: str):

    url = f"http://{thermocalc_environment.thermo_calc_service_url}/v1/thermocalc/results/{parent_job_id}"
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination_file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        logger.info(f"results file with {parent_job_id} downloaded at {destination_file_path}")
    except requests.HTTPError as e:
        raise ValueError(
            f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        )
    except IOError as e:
        raise ValueError(f"IO error occurred while saving the file: {e}")
