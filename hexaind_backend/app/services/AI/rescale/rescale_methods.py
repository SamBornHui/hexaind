import os
import json
import shutil
import string
import random
import logging
import pandas as pd
from ast import literal_eval
from pathlib import Path
from time import sleep
from typing import Any, Generator, List, Mapping, Dict
import requests
import traceback
import inspect
from moviepy.editor import VideoFileClip
from app.services.admin.connectors.schemas import *
from .schemas import RescaleConnTemplate
from app.services.data.assets.datasets.schemas import RescaleWidgetCustomInformation, RescaleMediaFiles, DatasetLocation
from app.utils.file_utils import FileUtils

logger = logging.getLogger(__package__)
logger.setLevel(logging.INFO)

def upload_file(
    token: str,
    path: Path,
    type_id: int = 1
) -> str:
    try:
        logger.info(f'Path:  {path}')
        with path.open('rb') as path_io:
            response = requests.post(
                'https://platform.rescale.com/api/v2/files/contents/',
                headers={'Authorization': f'Token {token}'},
                files={'file': (path.name, path_io, {'type_id': type_id})}
            )
            return json.loads(response.text)['id']
    except Exception as e:
        raise Exception(f'Unable to upload file {path}') from e


def create_job(
    token: str,
    name: str,
    license_envVars: Dict,
    input_files: List[Mapping[str, str]],
    analysis: Mapping[str, Any],
    hardware: Mapping[str, Any],
    command: str
) -> str:
    try:
        response = requests.post(
            'https://platform.rescale.com/api/v2/jobs/',
            headers={'Authorization': f'Token {token}'},
            json={
                'name': name,
                'jobanalyses': [
                    {
                        'envVars': license_envVars,
                        'useMpi': False,
                        'command': command,
                        'analysis': analysis,
                        'hardware': hardware,
                        'inputFiles': input_files,
                        "onDemandLicenseSeller": None,
                    }
                ]
            }
        )
        logger.info(f'create job response: {response.content}')
        return response.json()['id']
    except Exception as e:
        traceback.print_exc()
        raise Exception('Unable to create job') from e


def submit_job(token: str, job_id: str):
    requests.post(
        f'https://platform.rescale.com/api/v2/jobs/{job_id}/submit/',
        headers={'Authorization': f'Token {token}'}
    )


def stop_job(token: str, job_id: str):
    requests.post(
        f'https://platform.rescale.com/api/v2/jobs/{job_id}/force_stop/',
        headers={'Content-Type': 'application/json',
            'Authorization': f'Token {token}'}
    )


def monitor_job(token: str, job_id: str, time_interval: float = 60):
    while True:
        response = requests.get(
            f'https://platform.rescale.com/api/v2/jobs/{job_id}/statuses/',
            headers={'Authorization': f'Token {token}'},
        )
        if parse_job_content(response, job_id): break
        sleep(time_interval)

def parse_job_content(response: Any, job_id: str):
    if response.content and 'results' in response.json():
        results = response.json()['results']
        logger.info(f'job_id: {job_id} results: {results} ')
        if not results or results[0]['status'] == 'Completed' or results[0]['status'] == 'Failed':
            return (1, results[0])
        else:
            return (0, results[0])
    else:
        logger.info(f'job_id: {job_id} status code: {response.status_code} job_id content: {response.content} ')
    return (0, 0)

def ignore_extra_kwargs(func):
    """Decorator to ignore extra arguments from a dictionary of arguments while function calling."""

    def wrapper(**kwargs):
        """Wrapper function to ignore extra arguments from a dictionary of arguments."""

        # Get the expected keyword arguments for the function.
        expected_kwargs = set(inspect.getfullargspec(func).args)

        # Ignore any extra keyword arguments.
        kwargs = {k: v for k, v in kwargs.items() if k in expected_kwargs}

        # Call the function with the remaining keyword arguments.
        return func(**kwargs)

    return wrapper

def make_request_with_retry(url, headers, retries=1, delay=120): # delay in seconds (300 seconds = 5 minutes)
    try:
        # Attempt to make the request
        response = requests.get(url, headers=headers)
        if response.raise_for_status(): # This will raise an HTTPError for bad responses (4xx or 5xx)
            raise
        return response
    except requests.exceptions.HTTPError as e:
        # Check if we have retries left
        if retries > 0:
            logger.info("Request failed: {}. Waiting {} seconds before retrying...".format(e, delay))
            sleep(delay) # Wait for 5 minutes before retrying
            return make_request_with_retry(url, headers, retries - 1, delay) # Retry with one less retry left
        else:
            # No retries left, re-raise the last error
            raise

@ignore_extra_kwargs
def get_completed_job_rescale(token: str, job_id: str):

    url = f'https://platform.rescale.com/api/v2/jobs/{job_id}/statuses/'
    headers = {'Authorization': f'Token {token}'}
    response = make_request_with_retry(url=url, headers=headers, retries=4)
    parse_result = parse_job_content(response, job_id)
    if parse_result[0]: return (1, response)
    return (0 ,response)

def get_output_files(token: str, job_id: str) -> Mapping[str, str]:
    try:
        next_page = f'https://platform.rescale.com/api/v2/jobs/{job_id}/files'
        result = {}
        while next_page:
            response = requests.get(
                url=next_page,
                headers={'Authorization': f'Token {token}'}
            )
            data = response.json()
            next_page = data.get('next')
            files = data['results']
            for file_ in files:
                result[file_['name']] = file_['id']
        return result
    except Exception as e:
        logger.info('Unable to get output files ')

def convert_avi_to_mp4(input_file: str, output_file: str):
    # Load the AVI video using moviepy
    video = VideoFileClip(input_file)

    # Write the video to MP4 format
    video.write_videofile(output_file, codec='libx264')

    # Close the video object
    video.close()


def download_file(token: str, file_id: str, path: Path):
    try:
        response = requests.get(
            f'https://platform.rescale.com/api/v2/files/{file_id}/contents/',
            headers={'Authorization': f'Token {token}'}
        )
        
        chunk_size = 10_000
        with path.open('wb') as fd:
            for chunk in response.iter_content(chunk_size):
                fd.write(chunk)
        str_path = str(path)
        if '.avi' in str_path:
            convert_avi_to_mp4(str_path, os.path.splitext(str_path)[0] + '.mp4')
    except Exception as e:
        logger.info(f'Unable to download file {file_id}')


def shareJob(job_id: str, token: str) -> None:
        requests.post(
        f'https://platform.rescale.com/api/v2/jobs/{job_id}/share/',
        headers={'Content-Type': 'application/json',
                'Authorization': f'Token {token}'},
        json={
            "email": "almambet.iskakov@novelis.adityabirla.com",
            "message": "This job is not converging as quickly as I was expecting"
        }
            )



def create_trigger_rescale_job(
    workflow_name: str,
    workflow_iteration: int,
    parameters_file: str,
    conn_doc: RescaleConnectorConfiguration,
    **kwargs: dict,
) -> Dict:

    # verifying the parameters file
    parameters_file = Path(parameters_file)
    if not parameters_file.exists():
        raise FileNotFoundError(parameters_file)
    elif not parameters_file.is_file():
        raise IsADirectoryError(parameters_file)

    # getting workflow folder
    workflow_folder = parameters_file.parent
    
    token = conn_doc.token
    rescale_settings: RescaleConnTemplate = kwargs['rescale_config']
    test_mode: bool = rescale_settings.test_mode
    run_job: bool = rescale_settings.run_job
    software = rescale_settings.software.model_dump()
    analysis = software['analysis']
    hardware = software['hardware']
    filt_hard = {key: value for key, value in hardware.items() if value is not None}
    hardware = filt_hard
    command = software['command']
    visualize_files: list = software.get("visualize_files", None)
    output_file = software['output_file']
    file_ids = [
        {'id': file_.rescale_id}
        for file_ in rescale_settings.files_detail if file_.rescale_id
                ]
    logger.info(f'file_ids:   {file_ids}')
    envVars = software['envVars']
    rescale_files = kwargs['rescale_files']
    
    # creating a job
    logger.info('creating job')
    if test_mode:
        # Generating a random jobid string 
        all_characters = string.ascii_letters + string.digits  # Includes uppercase and lowercase letters and digits
        job_id = ''.join(random.choices(all_characters, k=5))
    else:
        if rescale_files:
            for f in rescale_files:
                file_ids.append({'id':  upload_file(token, Path(f))})
        else:
            logger.info(f'uploading file {parameters_file}')
            parameters_file_id = upload_file(token, Path(parameters_file))
            file_ids.append({'id': parameters_file_id})
            logger.info(f'uploaded parameters file {parameters_file_id}')

        job_id = create_job(
            token=token,
            name=f'{workflow_name}_{workflow_iteration}',
            license_envVars=envVars,
            input_files=file_ids,
            analysis=analysis,
            hardware=hardware,
            command=command
        )

    logger.info(f'created job {job_id}')

    # creating job output folder
    logger.info('creating job output folder')
    output_directory = workflow_folder / job_id
    output_directory.mkdir(exist_ok=True, parents=True)
    logger.info(f'created job output folder {output_directory}')

    output_file_path = output_directory / output_file
    # parameters_file = parameters_file.rename(output_directory / parameters_file.name)
    ### copying file into job id folder
    shutil.copy(parameters_file, output_directory / parameters_file.name)

    if run_job:
        logger.info('sharing job with Al')
        shareJob(job_id, token)
        # submitting job
        logger.info('submitting job')
        submit_job(token, job_id)
        logger.info('submitted job')
    
    job_data = dict(job_id=job_id, token=token, output_file_path=output_file_path, trial_folder=workflow_folder, test_mode=test_mode, run_job=run_job,
                     visualize_files=visualize_files, idx=workflow_iteration, parameters_file=parameters_file)
    
    return job_data

#### for rescale dummpy job 
def cccreate_trigger_rescale_job(
    workflow_name: str,
    workflow_iteration: int,
    parameters_file: str,
    conn_doc: RescaleConnectorConfiguration,
    **kwargs: dict,
) -> Dict:

    # verifying the parameters file
    parameters_file = Path(parameters_file)
    if not parameters_file.exists():
        raise FileNotFoundError(parameters_file)
    elif not parameters_file.is_file():
        raise IsADirectoryError(parameters_file)

    # getting workflow folder
    workflow_folder = parameters_file.parent
    
    token = conn_doc.token
    rescale_settings: RescaleConnTemplate = kwargs['rescale_config']
    test_mode: bool = rescale_settings.test_mode
    run_job: bool = rescale_settings.run_job
    software = rescale_settings.software.model_dump()
    analysis = software['analysis']
    hardware = software['hardware']
    filt_hard = {key: value for key, value in hardware.items() if value is not None}
    hardware = filt_hard
    command = software['command']
    visualize_files: list = software.get("visualize_files", None)
    output_file = software['output_file']
    file_ids = [
        {'id': file_.rescale_id}
        for file_ in rescale_settings.files_detail if file_.rescale_id
                ]
    logger.info(f'file_ids:   {file_ids}')
    envVars = software['envVars']
    rescale_files = kwargs['rescale_files']
    
    # creating a job
    logger.info('creating job')
    if test_mode:
        # Generating a random jobid string 
        all_characters = string.ascii_letters + string.digits  # Includes uppercase and lowercase letters and digits
        job_id = ''.join(random.choices(all_characters, k=5))
    else:
        job_id = 'XErQJc'#'nmxWNb'

    logger.info(f'created job {job_id}')

    # creating job output folder
    logger.info('creating job output folder')
    output_directory = workflow_folder / job_id
    output_directory.mkdir(exist_ok=True, parents=True)
    logger.info(f'created job output folder {output_directory}')

    output_file_path = output_directory / output_file
    # parameters_file = parameters_file.rename(output_directory / parameters_file.name)
    ### copying file into job id folder
    shutil.copy(parameters_file, output_directory / parameters_file.name)
    
    job_data = dict(job_id=job_id, token=token, output_file_path=output_file_path, trial_folder=workflow_folder, test_mode=test_mode, run_job=run_job,
                     visualize_files=visualize_files, idx=workflow_iteration, parameters_file=parameters_file)
    
    return job_data

def complete_rescale_job_flow(job_id: str, token: str, output_file_path: Path, visualize_files: List, **_) -> str:
    
    visual_dir = None
    try:  
        # getting output files
        logger.info('getting output files')
        output_files = get_output_files(token, job_id)
        logger.info(f'got output files {list(output_files.keys())}')
        download_files = [output_file_path]
        if output_file_path.name not in output_files:
            logger.info('output file {} not found in job output files'.format(output_file_path.name))
            download_files = list()
        
        download_viz_files = False
        if visualize_files:
            visual_dir = output_file_path.parent / 'visualization'
            visual_dir.mkdir(exist_ok=True, parents=True)
            for v_f in visualize_files:
                if v_f in output_files:
                    download_viz_files = True
                    download_files.append(visual_dir / v_f)
                else:
                    logger.info(f'visualization file {v_f} does not exists')

        if not download_viz_files:
            visual_dir = None
            
        for d_f in download_files:
            f_id = output_files[d_f.name]
            # downloading output file
            logger.info('downloading output file')
            download_file(token, f_id, d_f)
            logger.info(f'downloaded file to {d_f}')
    except:
        logger.info('Unable to download output files')

        return visual_dir

def form_rescale_custom_information(rescale_output_file: Path) -> RescaleWidgetCustomInformation:

    try:
        df = pd.read_csv(rescale_output_file, converters={'visualize_files': literal_eval})

        custom_info: RescaleWidgetCustomInformation = RescaleWidgetCustomInformation(trail_data=[])
        for _, row in df.iterrows():
            visualize_files = row['visualize_files']
            visual_dir = Path(row['visual_dir'])
            idx = 'idx' if 'idx' in row else 'trial_index'
            trail_number = str(row[idx])

            visualize_files_full_path = [visual_dir / file for file in visualize_files]

            file_locations: List[DatasetLocation] = []
            for file_path in visualize_files_full_path:

                file_path = str(file_path)
                if '.avi' in file_path:
                    file_path = file_path.replace('.avi', '.mp4')

                if not FileUtils.is_file_exist(file_path=file_path):
                    logger.error(f'visualization file not exists: {file_path}')
                    continue

                file_path = Path(file_path)

                file_loc = DatasetLocation(
                    isfolder = file_path.is_dir(),
                    size = str(file_path.stat().st_size) if file_path.is_file() else 0,
                    extension = file_path.suffix if file_path.is_file() else "",
                    path = str(file_path)
                )

                file_locations.append(file_loc)    

            trail_data = RescaleMediaFiles(
                trail_number=trail_number,
                media_files=file_locations
            )

            custom_info.trail_data.append(trail_data)
        
        return custom_info

    except Exception as e:
        traceback.print_exc()
        logger.error(f'failed to find visualizations from rescale output: {str(rescale_output_file)}, {e}')
        return

