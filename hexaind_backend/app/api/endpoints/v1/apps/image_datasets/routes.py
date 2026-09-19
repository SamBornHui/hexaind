import traceback
import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status, Form
from app.api.rbac.end_points_v1_access_control import CheckNameRoute, is_subfolder
import os
import time
from typing import List
from pymongo import MongoClient
from fastapi.responses import StreamingResponse
from app.services.data.assets.image_datasets.service import ImageDatasetsService
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.assets.image_datasets.schemas import ImagesUploadResponse, ImagesDatasetResponse, MEDIA_TYPES
from app.core.db.db_utils import get_db_async, get_db_sync
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image
import io
import json
from app.services.data.assets.image_datasets.service import ImageDatasetsService, ImageDatasetSubFolders
from app.services.data.assets.image_datasets.schemas import ImagesUploadResponse, MetaDataExtns
from app.services.apps.image_analysis.service import ImageAnalysisService
from app.core.services.jwt_token_utils.jwt_token_utils import decodeJWT
from app.services.admin.authentication.service import AuthenticationService
from app.config.env_vars import environment
from app.services.data.assets.datasets.schemas import DatasetUploadResponse

from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationModel,
    NotificationType,
    NotificationCategory,
    NotificationImportance,
)
from app.services.data.folder_management.service import FolderManagement
from app.services.data.folder_management.schema import CreateFolder

image_dataset_router = APIRouter(prefix="/v1/image_datasets", tags = ["ImageDatasets"], route_class=CheckNameRoute)

logger = logging.getLogger(__package__)

class ImageDatasetRouter:
    
    def __init__(self):
        pass

    @staticmethod
    @image_dataset_router.post(
        "/projects/{projectId}/images/upload_images_data",
        response_model=ImagesUploadResponse,
    )
    async def upload_images(
        projectId: str,
        files: List[UploadFile] = File(...),
        token: str = "",
        base_folder: str = "",
        upload_type: ImageDatasetSubFolders = None,
        sub_folder: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> ImagesUploadResponse:
        logger.info("Inside upload images method from assets.")

        token = decodeJWT(token)
        auth_service = AuthenticationService(db_async_client=client)
        logger.info(token)
        user = await auth_service.get_user_with_id (token['user_id'])
        if base_folder != "":
            logger.info(f"Got Request  to add more files to the existing location{base_folder}")
            upload_directory = base_folder

            if not is_subfolder(environment.datasets_folder, upload_directory):
                raise ValueError("Not authorized to access the location.")

        else:
            logger.info("Got Fresh request upload ")
            time_in_millis = str(round(time.time() * 1000))
            user_id = token['user_id']
            #upload_directory = environment.image_datasets_folder_format_string.format(user_id, projectId, time_in_millis)

            if not is_subfolder(environment.datasets_folder, os.path.join(environment.datasets_folder, f"p_{projectId})")):
                raise ValueError("Not authorized to access the location.")

            folder_mngmnt_service = FolderManagement(db_async_client=client)
            create_folder = CreateFolder(destination_folder=str(environment.datasets_folder),
                                     folder_name=f"p_{projectId}",
                                     user_id=user.id)
            await folder_mngmnt_service.create_folder(siteId="1",
                                                  projectId=projectId,
                                                  create_folder=create_folder
                                                  )

            upload_directory = os.path.join(environment.datasets_folder,f"p_{projectId}", time_in_millis)
        
        try:
            img_ds_service = ImageDatasetsService(db_async_client=client)
            if base_folder == "":
                images_upld_resp = await img_ds_service.upload_images_in_folder_struct(files, upload_directory, user)
            else:
                images_upld_resp = None
                if upload_type  == ImageDatasetSubFolders.UPLOADS:
                    logger.info(f"Got Request to upload images or images metadata, type {upload_type}")
                    images_upld_resp = await img_ds_service.upload_images_in_folder_struct(files, upload_directory, user, sub_folder)
                elif upload_type  == ImageDatasetSubFolders.CSV_METADATA:
                    logger.info(f"Got Request to upload material metadata, type {upload_type}")
                    images_upld_resp = await img_ds_service.upload_csv_files(upload_directory, files, user)
                    
            return images_upld_resp
        except Exception as e:
            err_str = f"Exception while tring to upload files/ folders. Error:{e}"
            logger.exception(err_str)
            raise HTTPException(status_code=500, detail=err_str)

    @staticmethod
    @image_dataset_router.post("/sites/{siteId}/projects/{projectId}/assets/create_dataset", response_model=DatasetUploadResponse)
    async def save_image_dataset(siteId: str, 
                                 projectId: str, name: str, 
                                 base_folder: str, token: str = "", 
                                 description: str = "", 
                                 client: AsyncIOMotorClient = Depends(get_db_async), 
                                 sync_client: MongoClient= Depends(get_db_sync)) -> DatasetUploadResponse:
        try:
            imgs_datasets_service = ImageDatasetsService(db_async_client=client)
            imgs_analysis_service = ImageAnalysisService(db_sync_client=sync_client)
            token = decodeJWT(token)
            auth_service = AuthenticationService(db_async_client=client)
            user = await auth_service.get_user_with_id (token['user_id'])
            dataset_id = await imgs_datasets_service.save_image_dataset_async(
                base_folder = base_folder,
                project_id = projectId,
                user = user,
                site_id = siteId,
                name = name,
                description = description)
            
            logger.info(f"Dataset created id:{dataset_id}")

            # creating notification
            dataset = await imgs_datasets_service.get_dataset_by_id(dataset_id)
    
            img_cat_data = await imgs_analysis_service.image_categorization(dataset)
            img_save_data = await imgs_analysis_service.image_save_dataset(dataset)
            message = f"Dataset {dataset.name} has been created"
            notification_obj = {
                "message": message,
                "category_id": dataset_id,
                "project_id": projectId,
                "notification_type": NotificationType.SUCCESS,
                "importance": NotificationImportance.MEDIUM,
                "notification_category": NotificationCategory.DATA,
            }
            verified_notfication_obj = NotificationModel(**notification_obj)
            notification_service_obj = Notification(db_async_client=client)
            try:
                await notification_service_obj.create_notification(verified_notfication_obj)
            except Exception as e:
                traceback.print_exc()
                logger.error("Exception to send notification")

            return DatasetUploadResponse(dataset_id=dataset_id)
        except Exception as e:
            err_str = f"Exception while trying to create Image type Dataset. Error:{e}"
            logger.exception(err_str)
            raise HTTPException(status_code=500, detail=err_str)

    @staticmethod 
    @image_dataset_router.get('/get_files_list_of_folder')
    async def get_files_list_of_folder(base_path: str,
                                folder: str,
                                token: str ="") :
        logger.info("Inside get_images_list_of_folder of image_dataset_router")
        try:
            folder = folder.lstrip("/")
            folder_path = os.path.join(base_path, folder)

            if not is_subfolder(environment.hexaind_data, folder_path):
                raise ValueError("Not authorized to access the location.")

            if not os.path.isdir(folder_path):
                err_str = f"No folder exists with name {folder_path}"
                logger.error(err_str)
                raise ValueError(err_str)
            images = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            return images
        except Exception as e:
            err_str = f"Exception while trying to get files list from {base_path}/{folder}. Error:{e}"
            logger.exception(err_str)
            raise HTTPException(status_code=500, detail=err_str)
   
    @staticmethod 
    @image_dataset_router.get('/get_file')
    async def get_file(base_path: str, folder: str, image_file_name: str) :
        logger.info("Inside get_image of image_dataset_router")
        try:
            
            folder = folder.lstrip("/")
            image_file_name = image_file_name.lstrip("/")
            folder_path = os.path.join(base_path, folder)

            if not is_subfolder(environment.hexaind_data, folder_path):
                raise ValueError("Not authorized to access the file specified.")
            
            if not os.path.isdir(folder_path):
                err_str = f"No folder exists with name {folder_path}"
                logger.error(err_str)
                raise ValueError(err_str)
            
            file_path = os.path.join(folder_path, image_file_name)
            
            if not os.path.isfile(file_path):
                err_str = f"No File exists with path {file_path}"
                logger.error(err_str)
                raise ValueError(err_str)
            
            file_extension = os.path.splitext(image_file_name)[1].lower()
            if file_extension in [".tif", ".tiff"]:
                with Image.open(file_path) as img:
                    # Convert the image to JPEG format
                    img = img.convert("RGB")
                    jpeg_image_io = io.BytesIO()
                    img.save(jpeg_image_io, format="JPEG")
                    jpeg_image_io.seek(0)
                
                headers = {'Content-Disposition': f'attachment; filename="{image_file_name}.jpg"'}
                return StreamingResponse(jpeg_image_io, headers=headers, media_type="image/jpeg")
            else:
                media_type = MEDIA_TYPES.get(file_extension, "application/octet-stream")
                
                def iterfile():
                    with open(file_path, "rb") as file:
                        yield from file

                headers = {'Content-Disposition': f'attachment; filename="{image_file_name}"'}
                return StreamingResponse(iterfile(), headers=headers, media_type=media_type)           
        except Exception as e:
            err_str = f"Exception while trying to get file. Error:{e}"
            logger.exception(err_str)
            raise HTTPException(status_code=500, detail=err_str)
        
    @staticmethod
    @image_dataset_router.get('/get_image_contnet_by_path')
    async def get_image_file(file_path: str, file_name: str) :
        logger.info("Inside get_image of image_dataset_router")
        try:
            file_extension = os.path.splitext(file_name)[1].lower()
            media_type = MEDIA_TYPES.get(file_extension, "application/octet-stream")
            def iterfile():
                with open(file_path, "rb") as file:
                    yield from file
 
            headers = {'Content-Disposition': f'attachment; filename="{file_name}"'}
            return StreamingResponse(iterfile(), headers=headers, media_type=media_type)        
        except Exception as e:
            err_str = f"Exception while trying to get file. Error:{e}"
            logger.exception(err_str)
            raise HTTPException(status_code=500, detail=err_str)
    
    @staticmethod 
    @image_dataset_router.get('/get_folder_struct_json')
    async def get_folder_struct_json(dataset_id: str, client: AsyncIOMotorClient = Depends(get_db_async) ) -> ImagesUploadResponse:

        logger.info("Inside get_folder_struct of image_dataset_router")
        try:
            image_ds_service = ImageDatasetsService(db_async_client=client)
            fold_struct_json = await image_ds_service.get_image_dataset_folder_struct_json(dataset_id=dataset_id)
            return ImagesUploadResponse(**fold_struct_json)
        except Exception as e:
            err_str = f"Exception to get folder_struct.json for dataset id. Error:{e}"
            logger.exception(err_str)
            raise HTTPException(status_code=500, detail=err_str)

    @staticmethod
    @image_dataset_router.post(
        "/projects/{projectId}/images/upload_images_data_from_mounted_drive",
        response_model=ImagesUploadResponse,
    )
    async def upload_images_data_from_mounted_drive(
        projectId: str,
        paths: List[str],
        token: str = "",
        base_folder: str = "",
        upload_type: ImageDatasetSubFolders = None,
        sub_folder: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> ImagesUploadResponse:

        logger.info("Inside upload_images_data_from_mounted_drive from image dataset.")
        try:
            token = decodeJWT(token)
            auth_service = AuthenticationService(db_async_client=client)
            user = await auth_service.get_user_with_id (token['user_id'])

            if base_folder != "":
                logger.info(f"Got Request  to add more files to the existing location{base_folder}/{sub_folder}")
                upload_directory = base_folder
            else:
                logger.info("Got Fresh request to upload from mounted drive")
                time_in_millis = str(round(time.time() * 1000))
                user_id = token['user_id']
                upload_directory = os.path.join(environment.datasets_folder, time_in_millis)
            img_ds_service = ImageDatasetsService(db_async_client=client)
            if base_folder == "":
                images_upld_resp = await img_ds_service.copy_images_img_metadata_create_thumbnails(paths, upload_directory, user)
            else:
                images_upld_resp = None
                if upload_type  == ImageDatasetSubFolders.UPLOADS:
                    logger.info("Got Request to upload images or images metadata ")
                    images_upld_resp = await img_ds_service.copy_images_img_metadata_create_thumbnails(paths, upload_directory, user, sub_folder)
                elif upload_type  == ImageDatasetSubFolders.CSV_METADATA:
                    logger.info("Got Request to upload CSV metadata ")
                    images_upld_resp = await img_ds_service.copy_csv_files(upload_directory, paths,  user)
                    
            return images_upld_resp
        except Exception as e:
            err_str = f"Exception while trying to upload files/ folders from mounted drive. Error:{e}"
            logger.exception(err_str)
            raise HTTPException(status_code=500, detail=err_str)

    @staticmethod
    @image_dataset_router.post(
        "/projects/{projectId}/images/rename",
        response_model=str,
    )
    async def rename(path: str,
                    new_name: str = "",
                    base_folder: str = "",
                    dataset_id: str = "",
                    token: str = "",
                    client: AsyncIOMotorClient = Depends(get_db_async)) -> str:
        try:
            parent_path = os.path.dirname(path)
            if not is_subfolder(parent_path, os.path.join(parent_path, new_name)):
                raise ValueError("Invalid name provided")

            imgs_datasets_service = ImageDatasetsService(db_async_client=client)
            token = decodeJWT(token)
            auth_service = AuthenticationService(db_async_client=client)
            user = await auth_service.get_user_with_id (token['user_id'])
            response = await imgs_datasets_service.rename(path, new_name, base_folder, dataset_id, user)
            return response
        except Exception as e:
            err_str = f"Exception while trying to rename a folder/ file. Error:{e}"
            logger.exception(err_str)
            raise HTTPException(status_code=500, detail=err_str)

    @staticmethod
    @image_dataset_router.post(
        "/projects/{projectId}/images/delete",
        response_model=str,
    )
    async def delete_file_or_folder(path: str,
                    base_folder: str = "",
                    dataset_id: str = "",
                    token: str = "",
                    client: AsyncIOMotorClient = Depends(get_db_async)) -> str:
        try:
            if not is_subfolder(environment.datasets_folder, path):
                raise ValueError("Not authorized to remove provided file/folder.")

            imgs_datasets_service = ImageDatasetsService(db_async_client=client)
            token = decodeJWT(token)
            auth_service = AuthenticationService(db_async_client=client)
            user = await auth_service.get_user_with_id (token['user_id'])
            response = await imgs_datasets_service.delete_file_or_folder(path, base_folder, dataset_id, user)
            return response
        except Exception as e:
            err_str = f"Exception while trying to delete the folder/ file. Error:{e}"
            logger.exception(err_str)
            raise HTTPException(status_code=500, detail=err_str)

    @staticmethod
    @image_dataset_router.get("/sites/{siteId}/projects/{projectId}/image_datasets", response_model=ImagesDatasetResponse)
    async def fetch_image_datasets(
        siteId: str,
        projectId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> ImagesDatasetResponse:
        try:
            imgs_datasets_service = ImageDatasetsService(db_async_client=client)
            image_datasets = await imgs_datasets_service.get_image_datasets(projectId)
            return ImagesDatasetResponse(image_datasets=image_datasets)
        
        except Exception as e:
            logger.error(
                f"Failed to fetch image datasets due to: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    @staticmethod
    @image_dataset_router.post("/sites/{siteId}/projects/{projectId}/datasets/upload_defect_images_metadata")
    async def upload_defect_metadata(
        siteId: str,
        projectId: str,
        files: List[UploadFile] = File(...),
        metadata: str = Form(...),
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):
        try:
            metadata_list = json.loads(metadata)
            saved_file_paths = []
            imgs_datasets_service = ImageDatasetsService(db_async_client=client)
            for i, file in enumerate(files):
                dataset_id = metadata_list[i]['dataset_id']
                target_directory = f"{metadata_list[i]['dataset_location']}/custom_metadata"
                os.makedirs(target_directory, exist_ok=True)
                file_path = os.path.join(target_directory, file.filename)
                with open(file_path, "wb") as f:
                    f.write(file.file.read())
                saved_file_paths.append({'file_path':file_path,'dataset_id':dataset_id})
                image_datasets = await imgs_datasets_service.update_dataset(dataset_id, file_path)
 
            return {
                "status": "success",
                "message": "Files uploaded and metadata updated successfully.",
                "defect_metadata": saved_file_paths,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to upload files: {str(e)}"
            )