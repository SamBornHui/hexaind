
from pathlib import Path
from pymongo import MongoClient
import os
import sys
import json
import zipfile
from typing import Mapping, Dict
import traceback
import pandas as pd
from importlib import import_module
from motor.motor_asyncio import AsyncIOMotorClient
import logging as logger

from .schemas import PostRescaleConfig, PostRescaleResponse
from .dao import PostRescaleDao
from app.services.data.assets.modules.service import *


class PostRescaleService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        self.postrescaledao = PostRescaleDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.post_rescale_dir = None

    
    def get_zip_data(self, modules_loc: Path) -> str:
        
        logger.info('zip block  ')
        modules_dir = modules_loc.parent
        py_file = 'post_rescale.py'
        py_file_path = modules_dir / py_file

        if not py_file_path.is_file():
            logger.info('going to extract zip file')
            with zipfile.ZipFile(modules_loc, 'r') as zip_ref:
                # Extract all contents to the specified directory
                zip_ref.extractall(modules_dir)
        
        sys.path.append(str(modules_dir))
        logger.info('module dir:  {}'.format(modules_dir))
        self.post_rescale_dir = modules_dir
        return str(modules_dir/py_file)

    def get_post_rescale_data(self, module_id: str, db_syc_client: MongoClient=None):
        
        logger.info('in get post rescale data')
        try:

            ms = ModuleService(db_sync_client=db_syc_client)
            modules_info = ms.get_module_record_by_id(module_id=module_id)
            logger.info('module info:  {}'.format(modules_info))
            module_path = modules_info.module_location.path
            if modules_info.module_location.extension == 'ZIP':
               module_path = self.get_zip_data(Path(modules_info.module_location.path))

            self.post_rescale_module = ms.import_module_from_path(module_name=modules_info.name, module_path=module_path)
        except:

            traceback.print_exc()
            logger.error('Error in module block:  {}'.format(module_id))

    def serialize_and_dump_to_json(self, file_path: Path):
        def convert_paths(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {key: convert_paths(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(element) for element in obj]
            return obj

        # Convert Path objects to strings recursively in the data
        serialized_data = convert_paths(self.next_observation_evaluation)

        # Write the serialized data to a JSON file
        with open(file_path, 'w') as file:
            json.dump(serialized_data, file, indent=4)

    def run_post_rescale(self, parameters: PostRescaleConfig, rescale_output: Path=None) -> PostRescaleResponse:
        try:

            self.parameters = parameters
            self.rescale_output = rescale_output
            self.get_post_rescale_data(self.parameters.post_rescale_module_id, db_syc_client=self.postrescaledao.db_sync_client)
            
            self.job_data = None
            with open (rescale_output, 'r') as file:
                self.job_data = json.load(file)
            
            post_rescale_json = rescale_output.parent / 'post_rescale_output.json'
            self.next_observation_evaluation = list()
            logger.info('post_rescale_dir:   {}'.format(self.post_rescale_dir))
            for i in self.job_data:
                kwargs = dict(rescale_output_file=Path(i['output_file_path']), trial_folder=Path(i['trial_folder']), parameters_file=Path(i['parameters_file']), additional_files_dir=self.post_rescale_dir)
                self.next_observation_evaluation.append(self.post_rescale_module.PostProcess(**kwargs))    

            self.serialize_and_dump_to_json(post_rescale_json)
            return PostRescaleResponse(json_path=post_rescale_json)
        except Exception as e:

            logger.error(f'Error during post-rescale: {e}')
            traceback.print_exc()
            return PostRescaleResponse(exception_detail=str(e))






    
    
