from app.services.data.assets.datasets.schemas import *
from app.services.data.assets.image_datasets.dao import ImageDatasetsDao
from app.services.data.assets.datasets.dao import DatasetsDao
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
import os
import aiofiles
from fastapi import UploadFile
import asyncio
from PIL import Image
from io import BytesIO   
import json
import logging
from datetime import datetime, timezone
import shutil
import traceback
import re
from uuid import uuid4
from bson.objectid import ObjectId
from app.services.data.assets.image_datasets.schemas import (ImageFileType, ImageMetaDataExtn,
                                                              ImageDatasetSubFolders, FileNode, 
                                                              ImagesUploadResponse, FOLDER_STRUCTURE_JSON_FILE, 
                                                              FileUploadDetails, MetaDataExtns)
from app.services.data.assets.datasets.service import DatasetsService
from app.services.admin.authentication.schemas import User
from app.services.apps.image_analysis.dao import ImageAnalysisDao
from app.services.apps.image_analysis.schema import *
from app.services.apps.image_analysis.controller.image_analysis_modules import *

logger = logging.getLogger(__package__)

class ImageDatasetsService:

    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:

        self.image_datasets_dao = ImageDatasetsDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.datasets_dao = DatasetsDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.image_analysis_dao = ImageAnalysisDao(db_sync_client=db_sync_client,db_async_client=
                                                   db_async_client)
        self.folder_struct_json_file_name = FOLDER_STRUCTURE_JSON_FILE
        self.allowed_image_extns = {item.value for item in ImageFileType}
        self.allowed_img_metadata_xtns = {item.value for item in ImageMetaDataExtn}
        self.allowed_material_metadata_xtns =  {item.value for item in MetaDataExtns}
        self.allowed_extensions = self.allowed_image_extns | self.allowed_img_metadata_xtns | self.allowed_material_metadata_xtns

    async def upload_images_in_folder_struct(self, files: List[UploadFile], upload_directory: str, user: User, sub_folder: str = "") :

        logger.info("Inside image_datasets service upload_images_in_folder_struct")

        imgs_uploads_loc = os.path.join(upload_directory, ImageDatasetSubFolders.UPLOADS)
        imgs_metadata_loc = os.path.join(upload_directory, ImageDatasetSubFolders.IMAGES_METADATA)
        imgs_base_path = imgs_uploads_loc

        if sub_folder and len(sub_folder.lstrip("/")) > 0:
            if not self.is_valid_image_dataset_location(upload_directory):
                raise ValueError(f"Provided path {upload_directory} is not a valid images dataset folder")

            if not await self.is_image_dataset_exists_with_path_async(upload_directory):
                raise ValueError(f"There is no image dataset exists with provided path {upload_directory}")

            sub_folder = sub_folder.lstrip("/")
            proposed_upload_folder = os.path.join(imgs_uploads_loc, sub_folder)
            if not os.path.exists(proposed_upload_folder) or not os.path.isdir(proposed_upload_folder):
                raise ValueError(f"There is no target folder exists with provided path {proposed_upload_folder}")
            
            imgs_uploads_loc = os.path.join(imgs_uploads_loc, sub_folder)
            imgs_metadata_loc = os.path.join(imgs_metadata_loc, sub_folder)
        
        self.raise_error_if_any_duplicates(files, imgs_metadata_loc)

        thumbnails_to_create_list = []
        uploaded_files_details = []
        for file in files:
            extension = os.path.splitext(file.filename)[1].lower()
            if extension not in self.allowed_extensions:
                continue

            if extension in (self.allowed_image_extns | self.allowed_material_metadata_xtns):
                file_path = os.path.join(imgs_uploads_loc, file.filename)
                created_folder_paths = self.makedirs_and_get_list(os.path.dirname(file_path), imgs_base_path, user)
                uploaded_files_details.extend(created_folder_paths)
                uploaded_files_details.append(FileUploadDetails(file_path=file_path, user_id=user.id, user_name=user.name, uid=f"{uuid4()}"))
                if extension in self.allowed_image_extns:
                    thumbnails_to_create_list.append(file_path)
            else:
                file_path = os.path.join(imgs_metadata_loc, file.filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(await file.read())

        for file in files:
            await file.close()

        thumbnails_loc = os.path.join(upload_directory, ImageDatasetSubFolders.THUMBNAILS)
        if sub_folder and len(sub_folder) > 0:
            thumbnails_loc = os.path.join(thumbnails_loc, sub_folder)
        
        await self.create_thumbnails(thumbnails_to_create_list, thumbnails_loc, imgs_uploads_loc)
  
        return await self.get_upload_response_for_folder_struct(upload_directory, user, uploaded_files_details)

    def makedirs_and_get_list(self, path: str, base_folder: str, user: User):
        created_dirs = []
        current_path = path[:(path.find(os.sep)+1)]
        for part in path.split(os.sep):
            if part:
                current_path = os.path.join(current_path, part)
                if not os.path.exists(current_path):
                    rel_path = os.path.relpath(current_path, base_folder)
                    if rel_path not in [".", ".."]:
                        created_dirs.append(FileUploadDetails(file_path=current_path, user_id=user.id, user_name=user.name, is_folder=True, uid=f"{uuid4()}"))
                    os.makedirs(current_path,exist_ok=True)

        return created_dirs

    def raise_error_if_any_duplicates(self, files: List[UploadFile], imgs_uploads_loc: str):
        duplicates_list = []
        found_any_duplicates = False
        try:
            for file in files:
                extension = os.path.splitext(file.filename)[1].lower()
                if extension in self.allowed_image_extns:
                    file_path = os.path.join(imgs_uploads_loc, file.filename)
                    if os.path.exists(file_path):
                        duplicates_list.append(file.filename)
                        found_any_duplicates = True
        except Exception as e:
            logger.error(f"Exception while trying to check for duplicates in Uploading local files. Reason:{e}")

        if found_any_duplicates:
            raise ValueError(f"Already files {duplicates_list} exists at {imgs_uploads_loc}")
    
    async def upload_csv_files(self, upload_directory: str, files: List[UploadFile], user: User):

        if not self.is_valid_image_dataset_location(upload_directory):
            raise ValueError(f"There is no target folder exists with provided path {upload_directory}")
        
        sub_folder = ImageDatasetSubFolders.CSV_METADATA
        allowed_extensions = {item.value for item in MetaDataExtns}
        upload_folder_loc = os.path.join(upload_directory, sub_folder)

        self.raise_error_if_any_duplicates(files, upload_folder_loc)

        uploaded_files_details = []
        for file in files:
            extension = os.path.splitext(file.filename)[1].lower()
            if extension not in allowed_extensions:
                continue

            file_path = os.path.join(upload_folder_loc, file.filename)
            created_folder_paths = self.makedirs_and_get_list(os.path.dirname(file_path), upload_folder_loc, user)
            uploaded_files_details.extend(created_folder_paths)
            uploaded_files_details.append(FileUploadDetails(file_path=file_path, user_id=user.id, user_name=user.name, uid=f"{uuid4()}"))
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(await file.read())

        for file in files:
            await file.close()
        
        return await self.get_upload_response_for_folder_struct(upload_directory, user, uploaded_files_details)

    def is_valid_image_dataset_location(self, base_folder: str):
        if not os.path.isdir(base_folder):
            return False
        json_path = os.path.join(base_folder, self.folder_struct_json_file_name)
        uploads_path = os.path.join(base_folder, ImageDatasetSubFolders.UPLOADS)
        thumbnails_path = os.path.join(base_folder, ImageDatasetSubFolders.THUMBNAILS)
        if not os.path.exists(json_path) or not os.path.exists(uploads_path) or not os.path.exists(thumbnails_path):
            return False

        return True
    
    async def save_image_dataset_async(self,
        base_folder,
        project_id: str,
        user: User,
        site_id: str,
        action_id: str = "",
        name: str = "",
        description: str = "",
        tags: List[str] = [],
        access_mode: AccessMode = AccessMode.EXTERNAL):

        if not self.is_valid_image_dataset_location(base_folder):
            raise ValueError(f"Uploads path {base_folder} does not exists or Improper uploads. Not suitable to save as image dataset")

        curr_time = datetime.now(timezone.utc)
        file_location_info = DatasetLocation(
            isfolder=True,
            size=str(self.get_folder_size(base_folder)),
            extension="N/A",
            path=base_folder,
            last_modified_by=user.name,
            last_modified_at=curr_time,
        )
    
        if await self.is_dataset_exists_with_path(base_folder):
            raise ValueError(f"Dataset already exists with the images uploading folder {base_folder}")

        dataset = Dataset(
            user_id=user.id,
            project_id=project_id,
            site_id=site_id,
            action_id=action_id,
            name=name,
            description=description,
            dataset_type=DatasetType.IMAGE_DATASET,
            dataset_information=[],
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            metadata={},
            created_at=curr_time,
            dataset_location=[file_location_info],
            access_mode=access_mode,
            tags=tags,
            custom_information=None,
            created_by=user.name
        )

        response =  await self.datasets_dao.insert_dataset_record_async(dataset)
        await self.insert_images_info_in_db(base_folder)
        return response
    
    def get_folder_size(self, folder_path: str) -> int:
        return sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(folder_path)
            for filename in filenames
        )

    async def insert_images_info_in_db(self, base_path: str):
        try:
            dataset = await self.image_datasets_dao.get_dataset_with_path_async(base_path)
            if dataset != None:
                json_path = os.path.join(base_path, self.folder_struct_json_file_name)
                json_data = self.get_json_data_from_file(json_path)
                fold_struct_json_obj = ImagesUploadResponse(**json_data)
                await self.image_datasets_dao.insert_image_records(dataset.id, fold_struct_json_obj.uploaded_file_det_list)
                uploaded_file_det_list = fold_struct_json_obj.uploaded_file_det_list

                for file_det in uploaded_file_det_list:
                    file_det.dataset_id = dataset.id

                json_path = os.path.join(base_path, self.folder_struct_json_file_name)
                self.write_json_to_file(json_path, fold_struct_json_obj)
        except Exception as e:
            logger.exception(f"Exception while trying to save images paths. Seems, there is no dataset exists with path {base_path}. Error:{e}")

    async def get_dataset_by_id(self, dataset_id: str) -> Dataset:
        return await self.datasets_dao.get_dataset_by_id_async(dataset_id=dataset_id)
    
    async def get_upload_response_for_folder_struct(self, upload_directory:str, user: User, uploaded_files_details: List[FileUploadDetails] = []):
        json_path = os.path.join(upload_directory, self.folder_struct_json_file_name)
        data = self.get_json_data_from_file(json_path)
        fold_struct_json_obj = ImagesUploadResponse(base_folder=upload_directory)
        if data != None:
            fold_struct_json_obj = ImagesUploadResponse(**data)
        
        total_uploads_list = fold_struct_json_obj.uploaded_file_det_list.copy()
        existing_uploads_list = fold_struct_json_obj.uploaded_file_det_list.copy()
        total_uploads_list.extend(uploaded_files_details)
        search_file_dict = {}
        for file_det in total_uploads_list:
            file_det: FileUploadDetails = file_det
            
            search_file_dict[file_det.file_path] = file_det

        upload_folder_struct = {"base_folder": upload_directory, "uploads": ImageDatasetSubFolders.UPLOADS.value,
                    "thumbnails": ImageDatasetSubFolders.THUMBNAILS.value,
                    "images_metadata": ImageDatasetSubFolders.IMAGES_METADATA.value,
                    "csv_metadata_folder": ImageDatasetSubFolders.CSV_METADATA.value,
                    "folder_struct": [],
                    "csv_metadata": []}
        upload_folder_struct = ImagesUploadResponse(**upload_folder_struct)
        try:
            
            uploads_folder = os.path.join(upload_directory, ImageDatasetSubFolders.UPLOADS) 
            files_tree: FileNode = self.build_file_tree(uploads_folder, uploads_folder, user=user, search_file_dict=search_file_dict)
            if files_tree:
                upload_folder_struct.folder_struct = files_tree.children
            
            upload_folder_struct.uploaded_file_det_list.extend(total_uploads_list)
            
            csv_metadata_folder  = os.path.join(upload_directory, ImageDatasetSubFolders.CSV_METADATA)
            files_tree: FileNode = self.build_file_tree(csv_metadata_folder, csv_metadata_folder, user=user, search_file_dict=search_file_dict)
            if files_tree:
                upload_folder_struct.csv_metadata = files_tree.children
            
            self.write_json_to_file(json_path, upload_folder_struct)
            try:
                dataset = await self.image_datasets_dao.get_dataset_with_path_async(upload_directory)
                if dataset:
                    await self.image_datasets_dao.insert_image_records(dataset.id, uploaded_files_details)
                    if existing_uploads_list:
                        new_folder_path = next((file.file_path for file in uploaded_files_details if file.is_folder), None)
                        new_file_paths = [file.file_path for file in uploaded_files_details if not file.is_folder]
                        image_cat_data = imageCategorizationUpdateDataset(dataset, new_folder_path, new_file_paths, self.image_analysis_dao.db_sync)
            except Exception as e:
                logger.error("Image dataset not yet saved", exc_info = True)

        except Exception as e:
            logger.exception("Uploaded the folder but, Failed to create Folder structure json file.", exc_info = True)
            file_node = FileNode(name="Exception", is_folder=False)
            upload_folder_struct.folder_struct = [file_node]

        return upload_folder_struct
    
    def build_file_tree(self, root_path: str,  relative_path: str, user: User, parent: Optional[str] = None, search_file_dict = {}) -> FileNode:
        if not os.path.exists(root_path):
            return {}

        name = os.path.basename(root_path)
        is_folder = os.path.isdir(root_path)
        extension = None
        children = []
        parent = root_path.replace(relative_path, "", 1)
        last_modified_at = ""

        if is_folder:
            for item in os.listdir(root_path):
                item_path = os.path.join(root_path, item)
                child_node = self.build_file_tree(item_path, relative_path, user=user, parent=parent, search_file_dict=search_file_dict)
                if child_node:
                    children.append(child_node)
        else:
            extension = os.path.splitext(name)[1].lower()
        
        size = os.path.getsize(root_path)
        last_modified_at = self.float_to_iso_format(os.path.getmtime(root_path))
        created_at = self.float_to_iso_format(os.path.getctime(root_path))

        parent = os.path.dirname(parent)
        
        file_type = "file"
        dataset_type =  None
        if os.path.isdir(root_path):
            file_type = "folder"
            dataset_type = DatasetType.IMAGES_FOLDER
            size = self.get_folder_size(root_path)
        elif extension == '.csv':
            dataset_type = DatasetType.TABULAR
        elif extension in self.allowed_image_extns:
            dataset_type = DatasetType.IMAGE
        else:
            dataset_type = DatasetType.TEXT
        file_uploaded_info: FileUploadDetails = search_file_dict.get(root_path)
        user_name = user.name
        user_id = user.id
        if file_uploaded_info:
            user_name = file_uploaded_info.user_name
            user_id = file_uploaded_info.user_id

        return FileNode(
            name=name,
            is_folder=is_folder,
            extension=extension[1:].upper() if not is_folder else None,
            size=size,
            parent=parent,
            created_by=user_name,
            last_modified_at = last_modified_at,
            type = file_type,
            dataset_type = dataset_type,
            user_id = user_id,
            created_at=created_at,
            children=children if children else None,
            full_path=root_path
        )
           
    def float_to_iso_format(self, time_float):
        dt = datetime.fromtimestamp(time_float)
        formatted_time = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")
        return formatted_time

    async def create_thumbnail(self, image_path, thumbnail_path, size=(128, 128)):
        """Create a thumbnail of the image and save it."""
        try:
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()
            img = Image.open(BytesIO(image_data))
            img.thumbnail(size)
            img.save(thumbnail_path)
        except Exception as e:
            logger.exception(f"Exception while trying to create thumbnail for{image_path}. Error:{e}")

    async def is_dataset_exists_with_path(self, base_path):
        return await self.image_datasets_dao.is_dataset_exists_with_path(base_path)
    
    async def is_image_dataset_exists_with_path_async(self, base_path):
        is_exists = await self.image_datasets_dao.is_image_dataset_exists_with_path_async(base_path)
        return is_exists

    async def get_image_dataset_folder_struct_json(self, dataset_id) -> dict:
        dataset = await self.datasets_dao.get_dataset_by_id_async(dataset_id)
        if not dataset:
            err_str = f"Invalid dataset id provided"
            logging.error(err_str)
            raise ValueError(err_str)
        
        if dataset.dataset_type != DatasetType.IMAGE_DATASET:
            err_str = f"Dataset type is not {DatasetType.IMAGE_DATASET}"
            logging.error(err_str)
            raise ValueError(err_str)
        
        base_path = dataset.dataset_location[0].path

        json_path = os.path.join(base_path, self.folder_struct_json_file_name)
        return self.get_json_data_from_file(json_path)
    
    def raise_error_if_duplicates_before_copying(self, source_paths: List[str], imgs_uploads_loc):
        duplicates_list = []
        found_any_duplicates = False
        try:
            for source_path in source_paths:
                file_name = os.path.basename(source_path)
                if os.path.isdir(source_path):
                    for root, dirs, files in os.walk(source_path):
                        relative_root = os.path.relpath(root, source_path)
                        image_target_subdir = os.path.join(imgs_uploads_loc, os.path.basename(source_path), relative_root)
                        for file in files:
                                file_extension = os.path.splitext(file)[1].lower()
                                file_path = os.path.join(root, file)
                                if file_extension in self.allowed_image_extns:
                                    #shutil.copy2(file_path, image_target_subdir)
                                    target_file_path = os.path.join(image_target_subdir, file)
                                    if  os.path.exists(target_file_path):
                                        found_any_duplicates = True
                                        duplicates_list.append(file_path)
                else:
                    # Copy the file
                    file_extension = os.path.splitext(file_name)[1].lower()
                    if file_extension in self.allowed_image_extns:
                        target_path = os.path.join(imgs_uploads_loc , file_name)
                        if  os.path.exists(target_path):
                            found_any_duplicates = True
                            duplicates_list.append(file_path)

        except Exception as e:
            logger.info(f"Exception while trying to check for Duplicates for mounted drive uploads. reason:{e}")
        
        if found_any_duplicates:
            raise ValueError(f"File(s) {duplicates_list} already exists at  the location {imgs_uploads_loc}")

    async def copy_images_img_metadata_create_thumbnails(self, source_paths: List[str], upload_directory: str, user: User, sub_folder:str = ""):
        imgs_uploads_loc = os.path.join(upload_directory, ImageDatasetSubFolders.UPLOADS)
        thumbnails_loc = os.path.join(upload_directory, ImageDatasetSubFolders.THUMBNAILS)
        img_metadata_loc = os.path.join(upload_directory, ImageDatasetSubFolders.IMAGES_METADATA)
        imgs_base_folder = imgs_uploads_loc

        if sub_folder and len(sub_folder.lstrip("/")) > 0:
            if not self.is_valid_image_dataset_location(upload_directory):
                raise ValueError(f"Provided path {upload_directory} is not a valid images dataset folder")
            
            sub_folder = sub_folder.lstrip("/")
            proposed_upload_folder = os.path.join(imgs_uploads_loc, sub_folder)
            if not os.path.exists(proposed_upload_folder) or not os.path.isdir(proposed_upload_folder):
                raise ValueError(f"There is no target folder exists with provided path {proposed_upload_folder}")
            
            imgs_uploads_loc = os.path.join(imgs_uploads_loc, sub_folder)
            img_metadata_loc = os.path.join(img_metadata_loc, sub_folder)
            thumbnails_loc = os.path.join(thumbnails_loc, sub_folder)

        uploaded_files_details = []
        created_folder_paths = self.makedirs_and_get_list(imgs_uploads_loc, upload_directory, user)
        uploaded_files_details.extend(created_folder_paths)
        os.makedirs(thumbnails_loc, exist_ok=True)
        os.makedirs(img_metadata_loc, exist_ok=True)

        self.raise_error_if_duplicates_before_copying(source_paths, imgs_uploads_loc)

        thumbnails_to_create_list = []
        # Copy each item to the target directory
        for source_path in source_paths:
            try:
                file_name = os.path.basename(source_path)

                if os.path.isdir(source_path):
                    
                    for root, dirs, files in os.walk(source_path):
                        relative_root = os.path.relpath(root, source_path)
                        source_path_name = os.path.basename(source_path)
                        image_target_subdir = os.path.join(imgs_uploads_loc, source_path_name)
                        metadata_target_subdir = os.path.join(img_metadata_loc, source_path_name)
                        if relative_root != ".":
                            image_target_subdir = os.path.join(image_target_subdir, relative_root)
                            metadata_target_subdir = os.path.join(metadata_target_subdir, relative_root)
                        created_folder_paths = self.makedirs_and_get_list(image_target_subdir, upload_directory, user)
                        uploaded_files_details.extend(created_folder_paths)
                        os.makedirs(metadata_target_subdir, exist_ok=True)

                        for file in files:
                            file_extension = os.path.splitext(file)[1].lower()
                            if file_extension not in self.allowed_extensions:
                                continue

                            file_path = os.path.join(root, file)

                            if file_extension in (self.allowed_image_extns | self.allowed_material_metadata_xtns):
                                shutil.copy2(file_path, image_target_subdir)
                                target_file_path = os.path.join(image_target_subdir, file)
                                if file_extension in self.allowed_image_extns:
                                    thumbnails_to_create_list.append(target_file_path)
                                uploaded_files_details.append(FileUploadDetails(file_path=target_file_path, user_id=user.id, user_name=user.name, uid=f"{uuid4()}"))
                            elif file_extension in self.allowed_img_metadata_xtns:
                                shutil.copy2(file_path, metadata_target_subdir)

                else:
                    # Copy the file
                    file_extension = os.path.splitext(file_name)[1].lower()

                    if file_extension not in self.allowed_extensions:
                        continue

                    if file_extension in (self.allowed_image_extns | self.allowed_material_metadata_xtns):
                        target_path = os.path.join(imgs_uploads_loc , file_name)
                        if file_extension in self.allowed_image_extns:
                            thumbnails_to_create_list.append(target_path)
                        uploaded_files_details.append(FileUploadDetails(file_path=target_path, user_id=user.id, user_name=user.name, uid=f"{uuid4()}"))
                    else:
                        target_path = os.path.join(img_metadata_loc , file_name)

                    shutil.copy2(source_path, target_path)

            except Exception as e:
                logger.exception("Failed to Upload. Exception")
                raise ValueError(f"Exception while trying to upload files/ folder. {e}")

        await self.create_thumbnails(thumbnails_to_create_list, thumbnails_loc, imgs_uploads_loc)

        return await self.get_upload_response_for_folder_struct(upload_directory, user, uploaded_files_details)
    
    def is_image(self, file_path):
        image_extensions = [
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp",
            ".svg", ".ico", ".heif", ".heic", ".raw", ".cr2", ".nef", ".orf", ".sr2"
        ]
        return any(file_path.lower().endswith(ext) for ext in image_extensions)


    async def create_thumbnails(self, thumbnails_to_create_list, thumbnails_loc, uploaded_loc):
        tasks = []
        for file_path in thumbnails_to_create_list:
            if self.is_image(file_path):
                relative_path = os.path.relpath(file_path, uploaded_loc)
                thumbnail_path = os.path.join(thumbnails_loc, relative_path)
                os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                tasks.append(self.create_thumbnail(file_path, thumbnail_path))

        # Wait for all thumbnail creation tasks to complete
        await asyncio.gather(*tasks)

    async def copy_csv_files(self, upload_directory: str, files: List[str], user: User):
        
        if not self.is_valid_image_dataset_location(upload_directory):
            raise ValueError(f"Provided path {upload_directory} is not a valid images dataset folder")
        
        allowed_extensions = {item.value for item in MetaDataExtns}
        sub_folder =  ImageDatasetSubFolders.CSV_METADATA

        upload_location = os.path.join(upload_directory, sub_folder)

        self.raise_error_if_duplicates_before_copying(files, upload_location)

        os.makedirs(upload_location, exist_ok=True)
        uploaded_files_details = []
        for file in files:
            file_name = os.path.basename(file)
            extension = os.path.splitext(file)[1].lower()
            if extension not in allowed_extensions:
                continue

            target_path = os.path.join(upload_location , file_name)
            uploaded_files_details.append(FileUploadDetails(file_path=target_path, user_id=user.id, user_name=user.name, uid=f"{uuid4()}"))
            shutil.copy2(file, target_path)
        
        return await self.get_upload_response_for_folder_struct(upload_directory, user, uploaded_files_details)

    async def rename(self, path: str, new_name: str, base_folder: str, dataset_id: str = "", user: User = None):
        if base_folder == "":
            dataset = await self.image_datasets_dao.get_dataset_with_simple_qry_async({'_id': ObjectId(dataset_id), 'dataset_type': DatasetType.IMAGE_DATASET})
            if dataset != None:
                base_folder = dataset['dataset_location.0.path']
        else:
            dataset = await self.image_datasets_dao.get_dataset_with_simple_qry_async({'dataset_location.0.path': base_folder, 'dataset_type': DatasetType.IMAGE_DATASET})

        if dataset == None:
            raise ValueError("There is no image dataset exists with given details.")

        if not os.path.exists(path):
            raise ValueError(f"There is no file exists woth path:{path}")

        if not self.is_valid_filename(new_name):
            raise ValueError("Invalid file name.")
        
        if not self.is_same_extension(path, new_name):
            raise ValueError("Invalid extension provided. please provide the extension same as previous.")

        proposed_path = os.path.join(os.path.dirname(path), new_name)

        if os.path.exists(proposed_path):
            raise ValueError("File/ Folder already exists with the provided name")
        
        is_file = False

        if os.path.isfile(path):
            is_file = True
        
        extension = os.path.splitext(path)[1].lower()
        is_renamed = False
        if is_file and extension not in self.allowed_image_extns:
            dir_name = os.path.dirname(path)
            os.rename(path, os.path.join(dir_name,new_name))
            is_renamed = True
        else:
            relative_path = os.path.relpath(path, start=os.path.join(base_folder, ImageDatasetSubFolders.UPLOADS))
            relative_dir = os.path.dirname(relative_path)
            old_name = os.path.basename(relative_path)
            subfolders = [ImageDatasetSubFolders.UPLOADS, ImageDatasetSubFolders.THUMBNAILS, ImageDatasetSubFolders.IMAGES_METADATA]
            for subfolder in subfolders:
                final_old_name = ""+old_name
                final_new_name = ""+new_name

                if subfolder == ImageDatasetSubFolders.IMAGES_METADATA and is_file:
                    final_old_name = self.get_hdr_name_of_filename(final_old_name)
                    final_new_name = self.get_hdr_name_of_filename(final_new_name)
                    
                old_rel_path = os.path.join(relative_dir, final_old_name)
                new_relative_path = os.path.join(relative_dir, final_new_name)
                old_path = os.path.join(base_folder, subfolder, old_rel_path)
                new_path = os.path.join(base_folder, subfolder, new_relative_path)

                if os.path.exists(old_path):
                    is_renamed = True
                    os.rename(old_path, new_path)

        if is_renamed:
            json_path = os.path.join(base_folder, self.folder_struct_json_file_name)

            json_data = self.get_json_data_from_file(json_path)

            fold_struct_obj = ImagesUploadResponse(**json_data)

            uploaded_file_det_list = fold_struct_obj.uploaded_file_det_list #json_data.get('uploaded_file_det_list', [])

            file_dir = os.path.dirname(path)
            new_path = os.path.join(file_dir, new_name)
            for file_det in uploaded_file_det_list:
                file_path = ""+file_det.file_path
                if file_path == path and is_file:
                    file_det.file_path = new_path
                    break
                elif not is_file:
                    if file_path == path:
                        file_det.file_path = new_path
                    elif file_path.startswith(path + os.sep):
                        rel_path = os.path.relpath(file_path, path)
                        new_full_path = os.path.join(new_path, rel_path)
                        file_det.file_path = new_full_path
            
            folder_struct = self.get_updated_folder_struct(uploaded_file_det_list, base_path=os.path.join(base_folder, ImageDatasetSubFolders.UPLOADS), user=user)
            
            await self.image_datasets_dao.update_images_file_info(dataset.id, uploaded_file_det_list, user.name)

            fold_struct_obj.folder_struct = folder_struct.children
            self.write_json_to_file(json_path, fold_struct_obj)

        return f"Renamed to {new_name}"

    async def delete_file_or_folder(self, path: str, base_folder: str, dataset_id: str = "", user: User = None):
        if base_folder == "":
            dataset = await self.image_datasets_dao.get_dataset_with_simple_qry_async({'_id': ObjectId(dataset_id), 'dataset_type': DatasetType.IMAGE_DATASET})
            if dataset != None:
                base_folder = dataset['dataset_location.0.path']
        else:
            dataset = await self.image_datasets_dao.get_dataset_with_simple_qry_async({'dataset_location.0.path': base_folder, 'dataset_type': DatasetType.IMAGE_DATASET})

        if dataset == None:
            raise ValueError("There is no image dataset exists with given details.")

        if not os.path.exists(path):
            raise ValueError(f"There is no file exists woth path:{path}")

        is_file = False

        if os.path.isfile(path):
            is_file = True
        
        extension = os.path.splitext(path)[1].lower()
        is_deleted = False
        if is_file and extension not in self.allowed_image_extns:
            os.remove(path)
            is_deleted = True
        else:
            relative_path = os.path.relpath(path, start=os.path.join(base_folder, ImageDatasetSubFolders.UPLOADS))
            relative_dir = os.path.dirname(relative_path)
            existing_name = os.path.basename(relative_path)
            subfolders = [ImageDatasetSubFolders.UPLOADS, ImageDatasetSubFolders.THUMBNAILS, ImageDatasetSubFolders.IMAGES_METADATA]
            for subfolder in subfolders:
                final_existing_name = ""+existing_name

                if subfolder == ImageDatasetSubFolders.IMAGES_METADATA and is_file:
                    final_existing_name = self.get_hdr_name_of_filename(final_existing_name)
                    
                existing_rel_path = os.path.join(relative_dir, final_existing_name)
                existing_path = os.path.join(base_folder, subfolder, existing_rel_path)

                if os.path.exists(existing_path):
                    is_deleted = True
                    if is_file:
                        os.remove(existing_path)
                    else:
                        shutil.rmtree(existing_path, ignore_errors=True)

        if is_deleted:
            json_path = os.path.join(base_folder, self.folder_struct_json_file_name)

            json_data = self.get_json_data_from_file(json_path)

            fold_struct_obj = ImagesUploadResponse(**json_data)

            uploaded_file_det_list = fold_struct_obj.uploaded_file_det_list

            remaining_file_det_list = []
            remove_file_det_list = []
            for file_det in uploaded_file_det_list:
                file_path = file_det.file_path
                if file_path != path and not file_path.startswith(path + os.sep):
                    remaining_file_det_list.append(file_det)
                else:
                    remove_file_det_list.append(file_det)
            
            fold_struct_obj.uploaded_file_det_list = remaining_file_det_list
            
            folder_struct = self.get_updated_folder_struct(remaining_file_det_list, base_path=os.path.join(base_folder, ImageDatasetSubFolders.UPLOADS), user=user)

            folder_size = self.get_folder_size(base_folder)
            await self.image_datasets_dao.delete_images_file_info(dataset.id, remove_file_det_list, user.name, str(folder_size))

            fold_struct_obj.folder_struct = folder_struct.children
            self.write_json_to_file(json_path, fold_struct_obj)
            

        return f"Removed File/ Folder {os.path.basename(path)}"
    
    def get_updated_folder_struct(self, uploaded_file_det_list: List[FileUploadDetails], base_path: str, user: User):
        search_file_dict = {}
        for file_det in uploaded_file_det_list:
            search_file_dict[file_det.file_path] = file_det
        
        updated_folder_struct = self.build_file_tree(base_path, base_path,user, search_file_dict=search_file_dict)
        return updated_folder_struct

    def get_hdr_name_of_filename(self, image_file_name):
        image_file_name = os.path.basename(image_file_name)
        file_parts = os.path.splitext(image_file_name)
        hdr_name = file_parts[0] + "-" + file_parts[1][1:] + ".hdr"
        return hdr_name

    def is_same_extension(self, path, new_name) -> bool:
        original_extension = os.path.splitext(path)[1].lower()
        new_extension = os.path.splitext(new_name)[1].lower()
        return original_extension == new_extension

    def is_valid_filename(self, filename):
        # Define invalid characters for Windows
        invalid_chars_windows = r'[<>:"/\\|?*]'
        
        # Check if the filename is empty
        if not filename:
            return False
        
        # Check for invalid characters on Windows
        if re.search(invalid_chars_windows, filename):
            return False
        
        # Check for control characters (ASCII 0-31)
        if any(ord(char) < 32 for char in filename):
            return False
        
        # Check for invalid Unix characters
        if '/' in filename or '\0' in filename:
            return False
        
        # Check for reserved names in Windows (con, prn, aux, nul, com1-com9, lpt1-lpt9)
        reserved_names = [
            "CON", "PRN", "AUX", "NUL",
            "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
            "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        ]
        if filename.split('.')[0].upper() in reserved_names:
            return False
        
        return True
    
    def get_json_data_from_file(self, json_file_path):
        data = None
        try:
            with open(json_file_path, "r", encoding="utf-8") as file_path:
                data = json.load(file_path)
        except:
            logger.info("Files does not exists")
        return data
    
    def write_json_to_file(self, json_file_path:str, json_obj: object):
        with open(json_file_path, "w") as fp:
            json.dump(json_obj.model_dump(), fp)

    @staticmethod
    def fill_fullpath_for_file_node(file_node_json: dict, parent_path: str, dataset_path: str, dataset_name: str = ""):
        file_node_json["full_path"] = os.path.join(parent_path, file_node_json["name"])
        file_node_json["dataset_path"] = dataset_path
        file_node_json["item_path"] = os.path.join(file_node_json["parent"], file_node_json["name"])
        file_node_json["dataset_name"] = dataset_name

        children = file_node_json.get("children")
        if children:
            for child in file_node_json["children"]:
                ImageDatasetsService.fill_fullpath_for_file_node(child, file_node_json["full_path"], dataset_path, dataset_name)
    
    @staticmethod
    def get_file_nodes(dataset: dict):
        base_path = dataset['full_path']
        json_file_path = os.path.join(base_path, FOLDER_STRUCTURE_JSON_FILE)
        try:
            data = json.load(open(json_file_path))
            if data == None:
                return None

            folder_struct = data.get('folder_struct', [])

            for item in folder_struct:
                 ImageDatasetsService.fill_fullpath_for_file_node(item, os.path.join(base_path, ImageDatasetSubFolders.UPLOADS), base_path, dataset['name'])

            csvs_struct = data.get('csv_metadata', [])

            for item in csvs_struct:
                ImageDatasetsService.fill_fullpath_for_file_node(item, os.path.join(base_path, ImageDatasetSubFolders.CSV_METADATA), base_path, dataset['name'])

            return {'folder_struct': folder_struct, 'csv_metadata': csvs_struct}
        except:
            traceback.print_exc()
            return None

    @staticmethod
    def update_json_with_new_dataset_location(new_base_path: str, dataset_name):
        json_file_path = os.path.join(new_base_path, FOLDER_STRUCTURE_JSON_FILE)
        try:
            data = json.load(open(json_file_path))
            if data == None:
                return None

            #image_dataset_resp = ImagesUploadResponse(**data)
            old_base_path = data['base_folder']
            uploaded_file_det_list = data['uploaded_file_det_list']
            for file_det in uploaded_file_det_list:
                rel_path = os.path.relpath(file_det['file_path'], old_base_path)
                file_det['file_path'] = os.path.join(new_base_path, rel_path)

            folder_struct = data.get('folder_struct', [])

            for item in folder_struct:
                 ImageDatasetsService.fill_fullpath_for_file_node(item, os.path.join(new_base_path, ImageDatasetSubFolders.UPLOADS), new_base_path, dataset_name)

            csvs_struct = data.get('csv_metadata', [])

            for item in csvs_struct:
                ImageDatasetsService.fill_fullpath_for_file_node(item, os.path.join(new_base_path, ImageDatasetSubFolders.CSV_METADATA), new_base_path, dataset_name)

            data["base_folder"] = new_base_path

            with open(json_file_path, "w") as fp:
                json.dump(data, fp)
            
            fold_struct_obj = ImagesUploadResponse(**data)

            return fold_struct_obj.uploaded_file_det_list
        except:
            traceback.print_exc()
            return None

    async def get_image_datasets(self, project_id) -> List[Dataset]:
        try:
            datasets = await self.image_datasets_dao.get_image_datasets(project_id)
            image_datasets=[]
            if  datasets:
                for dataset in datasets:
                    segmented = await self.image_datasets_dao.sampleworkflows(str(dataset["_id"]))
                    image_datasets.append({
                        "dataset_id": str(dataset["_id"]),
                        "dataset_name": dataset.get("name"),
                        "segmented": segmented,
                        "dataset_location": dataset["dataset_location"][0]["path"],
                        "defect_metadata_path": dataset["defect_metadata"] if "defect_metadata" in dataset else ""
                    })
            
            return image_datasets
        except Exception as e:
            raise Exception(f"Error fetching image datasets: {str(e)}")
        
    async def update_dataset(self, dataset_id, file_path):
        try:
            await self.image_datasets_dao.update_dataset(dataset_id,file_path)
            return
        except Exception as e:
            raise Exception(f"Error updating dataset: {str(e)}")