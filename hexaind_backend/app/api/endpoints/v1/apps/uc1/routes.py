import logging
from datetime import timezone, datetime
from typing import List
import zipfile
import shutil

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File


from app.api.rbac.end_points_v1_access_control import CheckNameRoute
import os
import json
from pathlib import Path
from app.core.db.db_utils import get_db_async
from motor.motor_asyncio import AsyncIOMotorClient

from app.services.apps.uc1.schemas import (
    UC1FilesResponse,
    UC1AggregatedData,
    UC1SetTrainConfig,
    UC1SetPredictionConfig,
    UC1ZipUploadResponse,
)
from app.config.env_vars import environment
from app.services.data.assets.modules.schemas import FileDetailsList

uc1_configurations_router = APIRouter(
    prefix="/v1/uc1", tags=["UC1Configurations"], route_class=CheckNameRoute
)

logger = logging.getLogger(__package__)


class UC1ConfigurationsAppRouter:

    def __init__(self):
        pass

    @staticmethod
    @uc1_configurations_router.get(
        "/projects/{projectId}/get_aggregated_config",
        response_model=UC1AggregatedData,
    )
    async def get_aggregated_config(
        projectId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> UC1AggregatedData:
        try:
            file_path = (
                environment.hexaind_data / f"p_{projectId}/uc1/data_aggregation.json"
            )
            if not file_path.exists():
                default_data = UC1AggregatedData(
                    all_trained_dids=[
                        "e5ca",
                        "y52p",
                        "y52k",
                        "y5cb",
                        "y62c",
                        "y62e",
                        "y62p",
                        "y72z",
                        "y72u",
                        "e5cb",
                    ],
                    unique_ids=[],  # previous_runs
                    models_map={},
                )
                file_path.parent.mkdir(
                    parents=True, exist_ok=True
                )  # Ensure directory exists
                with open(file_path, "w") as file:
                    json.dump(default_data.dict(), file, default=str)

            with open(file_path, "r") as file:
                data = json.load(file)
            return UC1AggregatedData(**data)
        except Exception as e:
            logger.exception("Exception occurred: {e}")
            raise HTTPException(status_code=500, detail=f"unexpected error: {str(e)}")

    @staticmethod
    @uc1_configurations_router.get(
        "/projects/{projectId}/get_train_config",
        response_model=UC1SetTrainConfig,
    )
    async def get_train_config(
        projectId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> UC1SetTrainConfig:
        try:
            file_path = environment.hexaind_data / f"p_{projectId}/uc1/train_config.json"
            if not file_path.exists():
                raise KeyError(f"File not exists : {file_path}")
            with open(file_path, "r") as file:
                data = json.load(file)
            return UC1SetTrainConfig(**data)
        except KeyError as e:
            logger.error(str(e))
            raise HTTPException(status_code=404, detail=f"file error: {str(e)}")
        except Exception as e:
            logger.exception("Exception occurred: {e}")
            raise HTTPException(status_code=404, detail=f"unexpected error: {str(e)}")

    @staticmethod
    @uc1_configurations_router.get(
        "/projects/{projectId}/get_prediction_config",
        response_model=UC1SetPredictionConfig,
    )
    async def get_prediction_config(
        projectId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> UC1SetPredictionConfig:

        try:
            file_path = (
                environment.hexaind_data / f"p_{projectId}/uc1/prediction_config.json"
            )
            if not file_path.exists():
                raise KeyError(f"File not exists : {file_path}")
            with open(file_path, "r") as file:
                data = json.load(file)
            return UC1SetPredictionConfig(**data)
        except KeyError as e:
            logger.error(str(e))
            raise HTTPException(status_code=404, detail=f"file error: {str(e)}")
        except Exception as e:
            logger.exception("Exception occurred: {e}")
            raise HTTPException(status_code=404, detail=f"unexpected error: {str(e)}")

    @staticmethod
    @uc1_configurations_router.post(
        "/projects/{projectId}/set_train_config",
        response_model=UC1SetTrainConfig,
    )
    async def set_train_config(
        projectId: str,
        train_config: UC1SetTrainConfig,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> UC1SetTrainConfig:
        try:
            file_path = environment.hexaind_data / f"p_{projectId}/uc1/train_config.json"
            train_config.updated_at = datetime.now(timezone.utc)
            # remove duplicates if FE send's it
            if train_config.all_dids:
                train_config.all_dids = list(set(train_config.all_dids))
            if train_config.selected_train_dids:
                train_config.selected_train_dids = list(
                    set(train_config.selected_train_dids)
                )
            if train_config.selected_test_dids:
                train_config.selected_test_dids = list(
                    set(train_config.selected_test_dids)
                )

            with open(file_path, "w") as file:
                json.dump(train_config.model_dump(), file, default=str)
            return train_config
        except Exception as e:
            logger.exception(str(e))
            raise HTTPException(status_code=500, detail=f"unexpected error: {str(e)}")

    @staticmethod
    @uc1_configurations_router.post(
        "/projects/{projectId}/set_prediction_config",
        response_model=UC1SetPredictionConfig,
    )
    async def set_prediction_config(
        projectId: str,
        prediction_config: UC1SetPredictionConfig,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> UC1SetPredictionConfig:

        try:
            file_path = (
                environment.hexaind_data / f"p_{projectId}/uc1/prediction_config.json"
            )
            # remove duplicates if FE send's it
            if prediction_config.all_dids:
                prediction_config.all_dids = list(set(prediction_config.all_dids))
            prediction_config.updated_at = datetime.now(timezone.utc)
            with open(file_path, "w") as file:
                json.dump(prediction_config.dict(), file, default=str)
            return prediction_config
        except Exception as e:
            logger.exception(str(e))
            raise HTTPException(status_code=500, detail=f"unexpected error: {str(e)}")

    # TODO: REMOVE BELOW API POST UI CHANGES BY ADDING PARAMETER
    @staticmethod
    @uc1_configurations_router.post(
        "/projects/{projectId}/upload_files", response_model=UC1ZipUploadResponse
    )
    async def upload_extract_zip(
        projectId: str, folder_path_suffix: str,  files: List[UploadFile] = File(...)
    ) -> UC1ZipUploadResponse:
        # Define the directory to save the uploaded ZIP file and extract it
        upload_dir = Path(
            environment.hexaind_data / f"p_{projectId}/uc1/{folder_path_suffix}"
        )
        upload_dir.mkdir(parents=True, exist_ok=True)
        file = files[0]
        # Save the uploaded ZIP file
        zip_path = str(upload_dir / file.filename)
        async with aiofiles.open(zip_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        # Extract the ZIP file
        filename = file.filename.strip(".zip")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(f"{upload_dir}/{filename}")

        # Look for JSON files in the extracted folder
        json_file = next(upload_dir.rglob("data_config.json"), None)
        if not json_file:
            raise HTTPException(
                status_code=404, detail="No data_config JSON file found in the ZIP"
            )

        # Read the first JSON file found
        async with aiofiles.open(json_file, "r") as json_file_data:
            json_content = await json_file_data.read()
            data = json.loads(json_content)

        design_data = list(data["design_measurement_data"].keys())
        material_designations = [
            details["material_designations"]
            for details in data["design_measurement_data"].values()
        ]
        if design_data:
            design_data = list(set(design_data))
        if material_designations:
            material_designations = list(
                map(list, set(map(tuple, material_designations)))
            )

        files_data = UC1FilesResponse(
            file_name=str(file.filename),
            file_path=str(zip_path),
            all_dids=design_data,
            all_design_measurements=material_designations,
        )
        # Clean up: Remove the extracted files
        shutil.rmtree(f"{upload_dir}/{filename}")

        return UC1ZipUploadResponse(files=[files_data])

    @staticmethod
    @uc1_configurations_router.post(
        "/projects/{projectId}/upload_files/predictions", response_model=UC1ZipUploadResponse
    )
    async def upload_extract_zip_predictions(
            projectId: str, folder_path_suffix: str, files: List[UploadFile] = File(...)
    ) -> UC1ZipUploadResponse:
        # Define the directory to save the uploaded ZIP file and extract it
        upload_dir = Path(
            environment.hexaind_data / f"p_{projectId}/uc1/{folder_path_suffix}"
        )
        upload_dir.mkdir(parents=True, exist_ok=True)
        file = files[0]
        # Save the uploaded ZIP file
        zip_path = str(upload_dir / file.filename)
        async with aiofiles.open(zip_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        # Extract the ZIP file
        filename = file.filename.strip(".zip")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(f"{upload_dir}/{filename}")

        # Look for JSON files in the extracted folder
        json_file = next(upload_dir.rglob("data_config.json"), None)
        if not json_file:
            raise HTTPException(
                status_code=404, detail="No data_config JSON file found in the ZIP"
            )

        # Read the first JSON file found
        async with aiofiles.open(json_file, "r") as json_file_data:
            json_content = await json_file_data.read()
            data = json.loads(json_content)

        design_data = list(data["design_coordinate_data"].keys())
        material_designations = [
            details["material_designations"]
            for details in data["design_measurement_data"].values()
        ]
        if design_data:
            design_data = list(set(design_data))
        if material_designations:
            material_designations = list(
                map(list, set(map(tuple, material_designations)))
            )

        files_data = UC1FilesResponse(
            file_name=str(file.filename),
            file_path=str(zip_path),
            all_dids=design_data,
            all_design_measurements=material_designations,
        )
        # Clean up: Remove the extracted files
        shutil.rmtree(f"{upload_dir}/{filename}")

        return UC1ZipUploadResponse(files=[files_data])
