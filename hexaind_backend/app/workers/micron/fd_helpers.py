import os
import uuid
from pathlib import Path
from typing import List
from glob import glob

import pandas as pd
import polars as pl
from app.workers.micron.utils import add_suffix_to_filename

from app.services.micron.data_catalog.fd_trace.schemas import ProbeDataPullInputs


def clean_fd_context(result_path: Path,
                     columns_to_group_by: List[str] = ['TOOL_ID','RUN_ID'],
                     columns_to_keep: List[str] = ['DWH_SRCID','DESIGN_ID','RECIPE_NAME','TOOL_NAME','TOOL_ID','RUN_ID','LOT_ID','WAFER_ID','TRAVELER_STEP','START_DATE'],
                     columns_to_combine_values_on: List[str] = ['LOT_ID','WAFER_ID']) -> Path:
    '''
    Description:
    - The FD CONTEXT data needs to be cleaned in a certain way
    - Sometimes, multiple wafers are processed at the same time. This means they have the same TOOL/RUNID
    - Because these are the same data points, they need to be grouped to avoid data duplication
    - This cleaning script will perform grouping based on TOOL/RUNID and then club the WAFERIDs together
    
    Input:
    - data : a pandas dataframe object that contains the original FD CONTEXT data as freshly pulled from GCP
    - columns_to_group_by : the flow will group the data with these columns
    - columns_to_keep : this list of columns will only be considered for the data cleaning steps
    - columns_to_combine_values_on : this list of columns will be combined wherever data grouping has occurred
    
    Note:
    - The default values are pre-configured to match with the sql query used to ingest the context data
    '''
    try:
        data = pd.read_parquet(result_path)
        
        # TODO file to data conversion
        # Convert everything to string for context data
        data = data.astype(str)
        
        # Perform groupby based on required columns
        fd_context_groups = data.groupby(columns_to_group_by)
        
        cleaned_fd_context = pd.DataFrame(columns=columns_to_keep)
        for group_name,fd_context_group in fd_context_groups:
            temp_data = fd_context_group[columns_to_keep].drop_duplicates()
            for column_name in columns_to_combine_values_on:
                temp_data[column_name] = ';'.join(sorted(list(fd_context_group[column_name].drop_duplicates())))
    
            cleaned_fd_context = pd.concat([cleaned_fd_context, temp_data])
    
            del temp_data
    
        cleaned_fd_context = cleaned_fd_context[columns_to_keep].drop_duplicates().reset_index(drop=True)
        
        # # We are splitting the table and columns to make it easier for UI to interpret them
        # table = cleaned_fd_context.to_dict(orient='records')

        if os.path.isdir(result_path):
            result_path = result_path / f"clean_fd_context_{uuid.uuid4()}.parquet"
        
        cleaned_fd_context.to_parquet(result_path)
        return result_path
        
    except Exception as e:
        print("Exception occured while post processing the fd_context data")


def preprocess_traveler_steps(
    traveler_steps_files: List[Path],
    destination_path: Path,
    traveler_steps_column: str = "traveler_steps",
    module_ids_column: str = "module_ids",
):

    # contatinating dataframes
    concatenated_dataframe = pd.concat(
        map(pd.read_parquet, traveler_steps_files)
    )
    # first 4 characters are considered as module id
    concatenated_dataframe[module_ids_column] = concatenated_dataframe[traveler_steps_column].str[:4]
    concatenated_dataframe.to_parquet(destination_path)

def remove_0_byte_files(files):
    files_removed = []
    clean_files = []
    for file in files:
        if os.path.isfile(file) and os.path.getsize(file) == 0:
            os.remove(file)
            files_removed.append(file)
        else:
            clean_files.append(file)
    return clean_files, files_removed

def remove_temp_files(files):
    for file in files:
        if os.path.isfile(file):
            os.remove(file)

def clean_probe_context(result_path: str):
    
    all_probe_context_files = glob(str(result_path) + "/*")

    clean_files, files_removed = remove_0_byte_files(all_probe_context_files)

    print(f"probe context: removed {len(files_removed)} 0 size files")

    final_probe_context = pl.read_parquet(clean_files)

    if os.path.isdir(result_path):
        result_path = str(Path(result_path) / f"clean_probe_context_{uuid.uuid4()}.parquet")
    
    final_probe_context.write_parquet(result_path)

    remove_temp_files(clean_files)

    return result_path

def post_process_probe_datapull(result_path: str, inputs: ProbeDataPullInputs):

    probe_data = pd.read_parquet(result_path)

    final_probe_data = probe_data.groupby(
                                            ['piid','LOT_ID','WAFER_ID','RUN_COMPLETE_DATE','WORK_WEEK','REGION']
                                        ).agg(
                                            {'DIE_X':'count'}
                                        ).sort_values(
                                            by=['WORK_WEEK','LOT_ID','WAFER_ID','REGION']
                                        ).rename(columns = {'DIE_X': 'DIE_COUNT'}).reset_index()
    
    max_die_counts_per_region = inputs.die_counts_per_region.model_dump()
    
    final_probe_data['TOTAL_DIE_COUNT'] = final_probe_data['REGION'].map(max_die_counts_per_region)

    final_probe_data['YL'] = final_probe_data['DIE_COUNT']/final_probe_data['TOTAL_DIE_COUNT']

    final_result_path = add_suffix_to_filename(result_path, suffix="_test")

    final_probe_data.to_parquet(final_result_path)

    return final_result_path
