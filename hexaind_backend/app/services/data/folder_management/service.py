import json
import logging
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from mimetypes import MimeTypes
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from bson import ObjectId
from fastapi import HTTPException
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import DirectoryPath
from pymongo import MongoClient

from app.config.env_vars import environment
from app.services.admin.authentication.schemas import User
from app.services.admin.authentication.service import AuthenticationService
from app.services.data.assets.datasets.schemas import (
    Dataset,
    DatasetLocation,
    DatasetType,
    TabularDatasetInformation,
    UploadStats,
    UploadStatus,
)
from app.services.data.assets.modules.schemas import ModuleExtenstion
from app.services.data.assets.image_datasets.dao import ImageDatasetsDao
from app.services.data.assets.image_datasets.service import ImageDatasetsService
from app.services.data.folder_management.dao import FolderManagementDao
from app.services.data.folder_management.schema import (
    CreateDatasetDuplicate,
    CreateDatasetDuplicateRespose,
    CreateFolder,
    CreateFolderResponse,
    DeleteAssets,
    DeleteAssetsResponse,
    DownloadAssets,
    MoveAssets,
    MoveAssetsResponse,
    RenameAssets,
    RenameAssetsResponse,
    dataset_extension,
    MimeTypesDownload
)

from app.services.data.assets.image_datasets.schemas import ImageDatasetSubFolders

logger = logging.getLogger(__package__)


class FolderManagement:
    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,  # type: ignore
    ):
        self.folder_management_dao = FolderManagementDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.image_dataset_dao = ImageDatasetsDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    def get_folder_size(self, path: DirectoryPath) -> str:
        # total_size = 0
        # processed_dirs = set()

        # for dirpath, dirnames, filenames in os.walk(path, topdown=False):
        #     if dirpath not in processed_dirs:
        #         dir_size = sum(os.path.getsize(os.path.join(dirpath, f)) for f in filenames if os.path.exists(os.path.join(dirpath, f)))
        #         total_size += dir_size
        #         processed_dirs.add(dirpath)
                
        # return str(total_size)
        root_directory = Path(path)
        total_bytes = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())
        return str(total_bytes)

    async def get_dataset_childern(self, projectId, dataset:dict):
        try:
            if dataset["dataset_type"] == DatasetType.IMAGE_DATASET:
                dataset_path = dataset["full_path"]
                if dataset_path:
                    folder_struct_dict = ImageDatasetsService.get_file_nodes(
                        dataset
                    )
                    if folder_struct_dict != None:
                        dataset["children"] = folder_struct_dict.get(
                            "folder_struct", []
                        )
                        dataset["metadata"] = folder_struct_dict.get(
                            "csv_metadata", []
                        )
                return dataset
        except Exception:
            logger.error(
                "Failed to fetch and attach folder_struct.json for the {} typedataset"
            )

    # @staticmethod
    async def list_directory(
        self, path: DirectoryPath, file_ext: str = None, project_id: str = None
    ) -> Dict:
        """
        This service is used for the getting the list of files and folders in the drive

        Args:
            path (DirectoryPath): path (provided as environment variable)

        Returns:
            dict: Nested folder structure
        """
        logger.info("Inside list directory function")

        def extract_specific_keys(
            dataset_array: List[Dict[str, Any]], modules: List[Dict[str, Any]]
        ) -> List[Dict[str, Any]]:
            def create_item(
                item: Dict[str, Any], is_module: bool = False
            ) -> Dict[str, Any]:
                if is_module:
                    location = item["module_location"]
                    item_type = item["module_type"]
                else:
                    location = item["dataset_location"][0]
                    item_type = item["dataset_type"]

                # currently corrputed => file missing for some reason, we can add more in feature
                is_corrupted = Path(location["path"]).exists()


                return {
                    "_id": str(item["_id"]),
                    "user_id": item["user_id"],
                    "created_by": item["created_by"],
                    "name": item["name"],
                    "description": item["description"],
                    "project_id": item["project_id"],
                    "site_id": item["site_id"],
                    "dataset_type": item_type,
                    "created_at": item["created_at"],
                    "children": [],
                    "parent_id": "",
                    "full_path": location["path"],
                    "location": location,
                    "is_corrupted": is_corrupted,
                    "last_modified_at": location["last_modified_at"],
                    "size": self.get_folder_size(location["path"]) if location["size"] == "" or location["size"] == "0"  else location["size"],
                    "type": (
                        "folder"
                        if item_type in [DatasetType.FOLDER, DatasetType.IMAGE_DATASET]
                        else "file"
                    ),
                }

            dataset_data = [create_item(item) for item in dataset_array]
            modules_data = [create_item(item, is_module=True) for item in modules]

            return dataset_data + modules_data

        def get_parent_id(data_array: List[Dict[str, Any]], path: str) -> str:
            for item in data_array:
                if (
                    item["dataset_type"] == DatasetType.FOLDER
                    and item["full_path"] == path
                ):
                    return item["_id"]
            return ""

        def convert_to_nested(data_array: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            id_dict = {item["_id"]: item for item in data_array}
            nested_dict = {}

            for item in data_array:
                parent_id = item["parent_id"]
                if parent_id:
                    parent_item = id_dict[parent_id]
                    parent_item.setdefault("children", []).append(item)
                else:
                    nested_dict[item["_id"]] = item

            return list(nested_dict.values())

        datasets_data = await self.folder_management_dao.get_all_document(
            {"project_id": project_id}, "datasets"
        )
        modules_data = await self.folder_management_dao.get_all_document(
            {"project_id": project_id, "module_location.extension": ModuleExtenstion.PY}, "modules"
        )

        data_array = extract_specific_keys(datasets_data, modules_data)

        for item in data_array:
            parent_id = get_parent_id(data_array, os.path.dirname(item["full_path"]))
            if parent_id:
                item["parent_id"] = parent_id

        nested_data = convert_to_nested(data_array)

        return nested_data

    async def create_folder(
        self,
        siteId,
        projectId,
        create_folder: CreateFolder,
        dataset_record_name: str = "",
    ):
        logger.info("Inside create folder function")
        if not create_folder.destination_folder:
            # base_path = os.path.join(environment.hexaind_data, "datasets")
            full_path = os.path.join(
                environment.datasets_folder,f"p_{projectId}", create_folder.folder_name)
        else:
            full_path = os.path.join(
                create_folder.destination_folder, create_folder.folder_name
            )
        logger.info(f"full path:{full_path}")
        os.makedirs(full_path, exist_ok=True, mode=0o777)
        user = await self.folder_management_dao.get_document(
            {"_id": ObjectId(create_folder.user_id)}, "users"
        )

        all_datasets = await self.folder_management_dao.get_all_document(
            filter_document={"dataset_type": "FOLDER"}, collection="datasets"
        )
        existing_paths = [x["dataset_location"][0]["path"] for x in all_datasets]
        if full_path in existing_paths:
            return CreateFolderResponse(
                status="Path already exists", folder_creation_path=full_path
            )

        dataset_location = DatasetLocation(
            isfolder=True,
            size=str(self.get_folder_size(full_path)),
            extension="",
            path=full_path,
            last_modified_by=user["name"],
            last_modified_at=datetime.now(timezone.utc),
        )
        dataset = Dataset(
            user_id=str(user["_id"]),
            project_id=projectId,
            action_id="",
            site_id=siteId,
            name=(
                create_folder.folder_name
                if not dataset_record_name
                else dataset_record_name
            ),
            description=create_folder.description,
            dataset_type=DatasetType.FOLDER,
            dataset_information=[
                TabularDatasetInformation(
                    preview=None,
                    statistics=None,
                    visualize=None,
                    dataset_schema=None,
                )
            ],
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            metadata={},  # Placeholder for metadata
            created_at=datetime.now(timezone.utc),
            created_by=user["name"],
            dataset_location=[dataset_location],  # Placeholder for dataset location
            access_mode=create_folder.access_mode,
            tags=[],
            custom_information=None,
        )
        await self.folder_management_dao.insert_document(
            dataset.model_dump(), "datasets"
        )

        return CreateFolderResponse(status="success", folder_creation_path=full_path)
    
    def create_folder_sync(
        self,
        siteId,
        projectId,
        create_folder: CreateFolder,
        dataset_record_name: str = "",
    ):
        logger.info("Inside create folder function")
        if not create_folder.destination_folder:
            # base_path = os.path.join(environment.hexaind_data, "datasets")
            full_path = os.path.join(
                environment.datasets_folder,f"p_{projectId}", create_folder.folder_name)
        else:
            full_path = os.path.join(
                create_folder.destination_folder, create_folder.folder_name
            )
        logger.info(f"full path:{full_path}")
        os.makedirs(full_path, exist_ok=True, mode=0o777)
        user = self.folder_management_dao.get_document_sync(
            {"_id": ObjectId(create_folder.user_id)}, "users"
        )

        all_datasets = self.folder_management_dao.get_all_document_sync(
            filter_document={"dataset_type": "FOLDER"}, collection="datasets"
        )
        existing_paths = [x["dataset_location"][0]["path"] for x in all_datasets]
        if full_path in existing_paths:
            return CreateFolderResponse(
                status="Path already exists", folder_creation_path=full_path
            )

        dataset_location = DatasetLocation(
            isfolder=True,
            size=str(self.get_folder_size(full_path)),
            extension="",
            path=full_path,
            last_modified_by=user["name"],
            last_modified_at=datetime.now(timezone.utc),
        )
        dataset = Dataset(
            user_id=str(user["_id"]),
            project_id=projectId,
            action_id="",
            site_id=siteId,
            name=(
                create_folder.folder_name
                if not dataset_record_name
                else dataset_record_name
            ),
            description=create_folder.description,
            dataset_type=DatasetType.FOLDER,
            dataset_information=[
                TabularDatasetInformation(
                    preview=None,
                    statistics=None,
                    visualize=None,
                    dataset_schema=None,
                )
            ],
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            metadata={},  # Placeholder for metadata
            created_at=datetime.now(timezone.utc),
            created_by=user["name"],
            dataset_location=[dataset_location],  # Placeholder for dataset location
            access_mode=create_folder.access_mode,
            tags=[],
            custom_information=None,
        )
        self.folder_management_dao.insert_document_sync(
            dataset.model_dump(), "datasets"
        )

        return CreateFolderResponse(status="success", folder_creation_path=full_path)

    async def create_subfolders(
        self,
        siteId: str,
        projectId: str,
        user_id: str,
        folder_names: dict,
        full_path,
        destination_path: Path = environment.datasets_folder,
    ):

        destination_path = os.path.abspath(str(destination_path))
        path_components = full_path.strip("/").split("/")
        dest_components = destination_path.strip("/").split("/")

        for i in range(len(dest_components), len(path_components)):
            if "." in path_components[i]:
                continue

            destination = "/" + "/".join(path_components[:i])
            folder_name = path_components[i]
            create_folder_obj = CreateFolder(
                destination_folder=destination,
                folder_name=folder_name,
                user_id=user_id,
            )
            await self.create_folder(
                siteId=siteId,
                projectId=projectId,
                create_folder=create_folder_obj,
                dataset_record_name=folder_names[path_components[i]],
            )

        result = await self.folder_management_dao.delete_document(
            filter_document={"dataset_location.0.path": str(destination_path)},
            collection="datasets",
        )

    def create_subfolders_sync(
        self,
        siteId: str,
        projectId: str,
        user_id: str,
        folder_names: dict,
        full_path,
        destination_path: Path = environment.datasets_folder,
    ):

        destination_path = os.path.abspath(str(destination_path))
        path_components = full_path.strip("/").split("/")
        dest_components = destination_path.strip("/").split("/")

        for i in range(len(dest_components), len(path_components)):
            if "." in path_components[i]:
                continue

            destination = "/" + "/".join(path_components[:i])
            folder_name = path_components[i]
            create_folder_obj = CreateFolder(
                destination_folder=destination,
                folder_name=folder_name,
                user_id=user_id,
            )
            self.create_folder_sync(
                siteId=siteId,
                projectId=projectId,
                create_folder=create_folder_obj,
                dataset_record_name=folder_names[path_components[i]],
            )

        result = self.folder_management_dao.delete_document_sync(
            filter_document={"dataset_location.0.path": str(destination_path)},
            collection="datasets",
        )

    async def update_datasets_module(
        self, source: str, new_name: str, dataset_type: str = "", description: str = ""
    ):
        logger.info("Inside update_dataset_module function")
        if dataset_type == DatasetType.IMAGE_DATASET:
            await self.folder_management_dao.update_document(
                filter_document={"dataset_location.0.path": source},
                new_value={"$set": {"name": new_name, "description": description}},
            )

        elif source.endswith(dataset_extension.get_all_dataset_extension()):
            await self.folder_management_dao.update_document(
                filter_document={"dataset_location.0.path": source},
                new_value={
                    "name": new_name,
                    "dataset_location.0.last_modified_at": datetime.now(timezone.utc),
                },
                collection="datasets",
            )

        elif source.endswith(".py") or source.endswith(".zip"):
            logger.info("in modules section")
            await self.folder_management_dao.update_document(
                filter_document={"module_location.path": source},
                new_value={
                    "name": new_name,
                    "module_location.last_modified_at": datetime.now(timezone.utc),
                },
                collection="modules",
            )

    async def add_size(self, file_size, old_size_of_destination_folder):
        new_size_of_destination_folder = int(file_size) + int(
            old_size_of_destination_folder
        )
        return new_size_of_destination_folder

    async def reduce_size(self, file_size, old_size_of_destination_folder):
        new_size_of_destination_folder = int(old_size_of_destination_folder) - int(
            file_size
        )
        return new_size_of_destination_folder

    async def update_destination_size(
        self, path_to_update: str, file_size: str, update_destination: bool = True
    ):
        while True:
            if update_destination:
                logger.info("Inside update destination")

                if os.path.basename(path_to_update) == "datasets":
                    break

                source_list = os.path.split(path_to_update)
                next_path_to_update = source_list[0]

                new_size = self.add_size
            else:
                logger.info("Inside update source")

                source_list = os.path.split(path_to_update)
                if (
                    os.path.basename(source_list[0]) == "datasets"
                    or os.path.basename(source_list[0]) == "modules"
                ):
                    break
                path_to_update = source_list[0]
                next_path_to_update = path_to_update
                new_size = self.reduce_size

            # extracting old size of destination folder
            destination_folder_document = await self.folder_management_dao.get_document(
                {"dataset_location.0.path": path_to_update}, "datasets"
            )
            old_size_of_destination_folder = destination_folder_document[
                "dataset_location"
            ][0]["size"]

            if old_size_of_destination_folder and file_size:
                new_size_of_destination_folder = await new_size(
                    file_size, old_size_of_destination_folder
                )
            elif not old_size_of_destination_folder and not file_size:
                new_size_of_destination_folder = ""
            elif not file_size and old_size_of_destination_folder:
                new_size_of_destination_folder = old_size_of_destination_folder
            elif not old_size_of_destination_folder and file_size:
                new_size_of_destination_folder = file_size
            await self.folder_management_dao.update_document(
                filter_document={"dataset_location.0.path": path_to_update},
                new_value={
                    "dataset_location.0.last_modified_at": datetime.now(timezone.utc),
                    "dataset_location.0.size": str(new_size_of_destination_folder),
                },
                collection="datasets",
            )

            path_to_update = next_path_to_update

    async def move_assets_operation(self, source, old_location, destination):
        base = os.path.basename(source)
        old_loc_list = old_location.split(os.path.basename(source))
        if len(old_loc_list) > 1:
            last_path = old_location.split(os.path.basename(source))[-1]
        else:
            last_path = ""
        first_half = os.path.join(destination, base)
        new_dataset_location = first_half + last_path
        return new_dataset_location
        pass

    async def move_assets(self, siteId: str, projectId: str, move_assets: MoveAssets):

        logger.info("Inside move_assets funciton")

        if move_assets.type == "dataset":
            # extracting file size
            file_document = await self.folder_management_dao.get_document(
                {"_id": ObjectId(move_assets.id)}, "datasets"
            )
            file_size = file_document["dataset_location"][0]["size"]

        else:
            file_document = await self.folder_management_dao.get_document(
                {"_id": ObjectId(move_assets.id)}, "modules"
            )
            file_size = file_document["module_location"]["size"]

        await self.update_destination_size(
            path_to_update=move_assets.destination,
            file_size=file_size,
            update_destination=True,
        )

        await self.update_destination_size(
            path_to_update=move_assets.source,
            file_size=file_size,
            update_destination=False,
        )

        if os.path.isfile(move_assets.source):
            logger.info("File movement")
            shutil.move(move_assets.source, move_assets.destination)
            new_file_location = os.path.join(
                move_assets.destination, os.path.basename(move_assets.source)
            )
            if move_assets.source.endswith(
                dataset_extension.get_all_dataset_extension()
            ):
                result = await self.folder_management_dao.update_document(
                    {"dataset_location.0.path": move_assets.source},
                    {
                        "dataset_location.0.path": new_file_location,
                        "dataset_location.0.last_modified_at": datetime.now(
                            timezone.utc
                        ),
                    },
                    collection="datasets",
                )

            elif move_assets.source.endswith(".py"):
                result = await self.folder_management_dao.update_document(
                    filter_document={"module_location.path": move_assets.source},
                    new_value={
                        "module_location.path": new_file_location,
                        "module_location.last_modified_at": datetime.now(timezone.utc),
                    },
                    collection="modules",
                )

        else:

            shutil.move(move_assets.source, move_assets.destination)
            childrens = await self.folder_management_dao.get_all_document(
                filter_document={
                    "dataset_location.0.path": {
                        "$regex": move_assets.source,
                        "$options": "i",
                    }
                },
                collection="datasets",
            )
            childrens_modules = await self.folder_management_dao.get_all_document(
                filter_document={
                    "module_location.path": {
                        "$regex": move_assets.source,
                        "$options": "i",
                    }
                },
                collection="modules",
            )

            all_childrens = childrens + childrens_modules
            source = move_assets.source
            destination = move_assets.destination
            for x in all_childrens:
                if "dataset_type" in x.keys():
                    old_location = x["dataset_location"][0]["path"]
                    new_dataset_location = await self.move_assets_operation(
                        source=source,
                        old_location=old_location,
                        destination=destination,
                    )
                    await self.folder_management_dao.update_document(
                        filter_document={"_id": ObjectId(x["_id"])},
                        new_value={
                            "dataset_location.0.path": new_dataset_location,
                            "dataset_location.0.last_modified_at": datetime.now(
                                timezone.utc
                            ),
                        },
                        collection="datasets",
                    )
                    dataset = (
                        await self.image_dataset_dao.get_dataset_with_simple_qry_async(
                            {
                                "_id": ObjectId(x["_id"]),
                                "dataset_type": DatasetType.IMAGE_DATASET,
                            }
                        )
                    )
                    if dataset != None:
                        uploaded_file_det_list = (
                            ImageDatasetsService.update_json_with_new_dataset_location(
                                new_dataset_location, x["name"]
                            )
                        )
                        await self.image_dataset_dao.update_images_file_info(
                            x["_id"], uploaded_file_det_list
                        )
                else:
                    old_location = x["module_location"]["path"]
                    new_dataset_location = await self.move_assets_operation(
                        source=source,
                        old_location=old_location,
                        destination=destination,
                    )
                    await self.folder_management_dao.update_document(
                        filter_document={"_id": ObjectId(x["_id"])},
                        new_value={
                            "module_location.path": new_dataset_location,
                            "module_location.last_modified_at": datetime.now(
                                timezone.utc
                            ),
                        },
                        collection="modules",
                    )

        return MoveAssetsResponse(
            status="success",
            message=f"Assets moved from {move_assets.source} to {move_assets.destination}",
        )

    # Function to update paths

    async def update_path(self, path, prefix, replace_val):
        common_path = os.path.commonpath([path, prefix])
        updated_path = path.replace(
            common_path, os.path.join(os.path.dirname(common_path), replace_val)
        )
        return updated_path

    async def rename_assets(
        self, siteId: str, projectId: str, rename_assets: RenameAssets
    ):
        logger.info("Inside rename_assets function")

        if (
            os.path.isfile(rename_assets.source)
            or rename_assets.dataset_type == DatasetType.IMAGE_DATASET
        ):
            logger.info("File movement")
            await self.update_datasets_module(
                rename_assets.source,
                rename_assets.new_name,
                rename_assets.dataset_type,
                rename_assets.description,
            )
        else:
            childrens = await self.folder_management_dao.get_all_document(
                filter_document={
                    "dataset_location.0.path": {
                        "$regex": rename_assets.source,
                        "$options": "i",
                    }
                },
                collection="datasets",
            )
            childrens_modules = await self.folder_management_dao.get_all_document(
                filter_document={
                    "module_location.path": {
                        "$regex": rename_assets.source,
                        "$options": "i",
                    }
                },
                collection="modules",
            )
            all_childrens = childrens + childrens_modules

            source = rename_assets.source
            new_name = rename_assets.new_name
            await self.folder_management_dao.update_document(
                filter_document={"dataset_location.0.path": source},
                new_value={
                    "name": new_name,
                    "dataset_location.0.last_modified_at": datetime.now(timezone.utc),
                },
                collection="datasets",
            )
            for x in all_childrens:
                if "dataset_type" in x.keys():
                    old_location = x["dataset_location"][0]["path"]
                    old_name = os.path.basename(source)
                    new_dataset_location = await self.update_path(
                        old_location, rename_assets.source, new_name
                    )

                    await self.folder_management_dao.update_document(
                        filter_document={"_id": ObjectId(x["_id"])},
                        new_value={
                            "dataset_location.0.path": new_dataset_location,
                            "dataset_location.0.last_modified_at": datetime.now(
                                timezone.utc
                            ),
                        },
                        collection="datasets",
                    )
                else:
                    old_location = x["module_location"]["path"]
                    old_name = os.path.basename(source)
                    new_dataset_location = await self.update_path(
                        old_location, rename_assets.source, new_name
                    )
                    await self.folder_management_dao.update_document(
                        filter_document={"_id": ObjectId(x["_id"])},
                        new_value={
                            "module_location.path": new_dataset_location,
                            "module_location.last_modified_at": datetime.now(
                                timezone.utc
                            ),
                        },
                        collection="modules",
                    )

            new_full_name = os.path.join(
                os.path.dirname(rename_assets.source), rename_assets.new_name
            )
            os.rename(rename_assets.source, new_full_name)

        return RenameAssetsResponse(
            status="success",
            message=f"Rename assets {rename_assets.source} to {rename_assets.new_name}",
        )

    async def create_duplicate(
        self,
        file_document: dict,
        create_dataset: CreateDatasetDuplicate,
        file_location: str,
        file_size: str,
    ):

        logger.info("Inside create_duplicate function")

        _, extension = os.path.splitext(file_location)
        unique_filename = f"{uuid4()}{extension}"
        if create_dataset.folderPath:
            full_file_path = os.path.join(create_dataset.folderPath, unique_filename)
            await self.update_destination_size(
                path_to_update=create_dataset.folderPath,
                file_size=file_size,
                update_destination=True,
            )
        else:
            dirPath = os.path.split(file_location)[0]
            full_file_path = os.path.join(dirPath, unique_filename)

        user_info = await self.folder_management_dao.get_document(
            filter_document={"_id": ObjectId(create_dataset.user_id)},
            collection="users",
        )
        file_document.update(
            {
                "user_id": create_dataset.user_id,
                "name": create_dataset.datasetName,
                "created_at": datetime.now(timezone.utc),
                "created_by": user_info["name"],
            }
        )
        file_document.pop("_id")
        if create_dataset.type == "dataset":
            file_document["dataset_location"][0]["path"] = full_file_path
            file_document["dataset_location"][0]["last_modified_at"] = datetime.now(
                timezone.utc
            )
            await self.folder_management_dao.insert_document(
                value=file_document, collection="datasets"
            )

            shutil.copy(file_location, full_file_path)

        else:
            file_document["module_location"]["path"] = full_file_path
            file_document["module_location"]["last_modified_at"] = datetime.now(
                timezone.utc
            )
            await self.folder_management_dao.insert_document(
                value=file_document, collection="modules"
            )

            shutil.copy(file_location, full_file_path)

        return full_file_path

    async def create_dataset_duplicate(
        self,
        siteId: str,
        projectId: str,
        create_dataset: CreateDatasetDuplicate,
    ):
        logger.info("Inside create_dataset_duplicate function")

        if create_dataset.type == "dataset":
            document = await self.folder_management_dao.get_document(
                {"_id": ObjectId(create_dataset.datasetId)}, "datasets"
            )
            file_location = document["dataset_location"][0]["path"]
            file_size = document["dataset_location"][0]["size"]
            full_file_path = await self.create_duplicate(
                file_document=document,
                create_dataset=create_dataset,
                file_location=file_location,
                file_size=file_size,
            )
        else:
            document = await self.folder_management_dao.get_document(
                {"_id": ObjectId(create_dataset.datasetId)}, "modules"
            )
            file_location = document["module_location"]["path"]
            file_size = document["module_location"]["size"]
            full_file_path = await self.create_duplicate(
                file_document=document,
                create_dataset=create_dataset,
                file_location=file_location,
                file_size=file_size,
            )

        return CreateDatasetDuplicateRespose(
            status="success", message=f"Dataset duplicated at {full_file_path}"
        )

    async def delete_asset(
        self, siteId: str, projectId: str, delete_assets: DeleteAssets
    ):
        logger.info("Inside delete_asset function")

        if os.path.exists(delete_assets.source):
            if (
                delete_assets.dataset_type != None
                and delete_assets.dataset_type == DatasetType.IMAGE_DATASET
            ):

                dataset = await self.folder_management_dao.get_document(
                    filter_document={
                        "dataset_location.0.path": delete_assets.source,
                        "dataset_type": DatasetType.IMAGE_DATASET
                    },
                    collection="datasets",
                )
                if dataset == None:
                    raise KeyError("There is no image dataset with the path provided")
                if not os.path.isdir(delete_assets.source):
                    raise KeyError("Invalid image dataset. Not pointing to a folder")

                shutil.rmtree(delete_assets.source)
                result = await self.image_dataset_dao.delete_image_dataset(
                    dataset["_id"]
                )
                if result.deleted_count == 1:
                    logger.info(f"Location updated for in MongoDB")
                else:
                    logger.warning(f"Failed to update location for in MongoDB")
            elif os.path.isdir(delete_assets.source):
                shutil.rmtree(delete_assets.source)
            else:
                os.remove(delete_assets.source)

                if delete_assets.source.endswith(
                    dataset_extension.get_all_dataset_extension()
                ):
                    file_document = await self.folder_management_dao.get_document(
                        {"dataset_location.0.path": delete_assets.source}, "datasets"
                    )
                    file_size = file_document["dataset_location"][0]["size"]
                    await self.update_destination_size(
                        delete_assets.source, file_size, False
                    )
                    await self.folder_management_dao.delete_document(
                        filter_document={
                            "dataset_location.0.path": delete_assets.source
                        },
                        collection="datasets",
                    )

                elif delete_assets.source.endswith(".py"):
                    logger.info("inside py module")
                    file_document = await self.folder_management_dao.get_document(
                        {"module_location.path": delete_assets.source}, "modules"
                    )
                    file_size = file_document["module_location"]["size"]
                    await self.update_destination_size(
                        delete_assets.source, file_size, False
                    )
                    await self.folder_management_dao.delete_document(
                        filter_document={"module_location.path": delete_assets.source},
                        collection="modules",
                    )

        return DeleteAssetsResponse(
            status="success", message=f"Asset deleted successfully"
        )

    def send_file_download_response(self, file_path: Path):
        file_extension = file_path.suffix
        media_type = MimeTypesDownload.get_mime_type(file_extension)
        return FileResponse(
        path=file_path, filename=file_path.name, media_type=media_type
        )
    
    async def download_asset(
        self, siteId: str, projectId: str, download_assets: DownloadAssets
    ):
        logger.info("Inside download_asset function")
        datsets_document = await self.folder_management_dao.get_all_document(
            filter_document={
                "project_id": projectId,
                "dataset_location.0.path": {
                    "$regex": download_assets.source,
                    "$options": "i",
                },
            },
            collection="datasets",
        )
        modules_document = await self.folder_management_dao.get_all_document(
            filter_document={
                "project_id": projectId,
                "module_location.path": {
                    "$regex": download_assets.source,
                    "$options": "i",
                },
            },
            collection="modules",
        )
        documents = datsets_document + modules_document
        if not documents:
            raise HTTPException(
                status_code=404,
                detail="No documents found for the given site and project ID.",
            )

        # If there's only one document and it's a file, return it directly
        if len(documents) == 1:
            if "dataset_type" in documents[0].keys():
                
                if documents[0]["dataset_type"] == DatasetType.IMAGE_DATASET:
                    img_ds_path = documents[0]["dataset_location"][0]["path"]
                    uploads_folder = os.path.join(img_ds_path, ImageDatasetSubFolders.UPLOADS.value)
                    metadata_path = None
                    if os.path.exists(uploads_folder) and os.path.isdir(uploads_folder):
                        folder_path = Path(uploads_folder)
                        metadata_path =os.path.join(img_ds_path, ImageDatasetSubFolders.IMAGES_METADATA.value)
                        if os.path.exists(metadata_path) and os.path.isdir(metadata_path):
                            metadata_path = Path(metadata_path)
                        else:
                            metadata_path = None

                    else:
                        folder_path = Path(img_ds_path)

                    temp_dir = tempfile.mkdtemp()
                    zip_path = os.path.join(temp_dir, f"download_file.zip")
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                        files_list = await self.folder_management_dao.get_all_document({"dataset_id": str(documents[0]['_id']), "is_folder": False}, 
                                                                                       "image_datasets_files")
                        for file_det in files_list:
                            file_path = Path(file_det["file_path"])
                            zipf.write(file_path, arcname=file_path.relative_to(folder_path))
                      
                        if metadata_path != None:
                            for root, dirs, files in os.walk(metadata_path):
                                for file in files:
                                    file_path = Path(root) / file
                                    zipf.write(file_path, arcname=file_path.relative_to(metadata_path))
                                    print(file_path)

                    # Return the zip file as a response after it is created
                    return FileResponse(
                        zip_path,
                        media_type="application/octet-stream",
                        filename=f"{folder_path.name}.zip"
                    )
                    
                if documents[0]["dataset_type"] != DatasetType.FOLDER:
                    file_path = Path(documents[0]["dataset_location"][0]["path"])
                    if file_path.is_file():
                        return self.send_file_download_response(
                            file_path=file_path
                        )
                else:
                    temp_dir = tempfile.mkdtemp()
                    zip_path = os.path.join(temp_dir, "download_file.zip")
                    file_path = Path(documents[0]["dataset_location"][0]["path"])
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                        return FileResponse(
                            zip_path,
                            media_type="application/octet-stream",
                            filename="download_file.zip",
                        )
            else:
                file_path = Path(documents[0]["module_location"]["path"])
                if file_path.is_file():
                    return self.send_file_download_response(file_path=file_path)

        # Otherwise, create a zip file with all the documents
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "download_file.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for document in documents:
                if "dataset_type" in document.keys():
                    file_path = document["dataset_location"][0]["path"]
                else:
                    file_path = document["module_location"]["path"]
                relative_path = os.path.relpath(file_path, download_assets.source)
                if os.path.isfile(file_path):
                    arcname = os.path.join(
                        os.path.split(relative_path)[0],
                        document["name"] + os.path.splitext(file_path)[1],
                    )
                    zipf.write(file_path, arcname=arcname)

        return FileResponse(
            zip_path,
            media_type="application/octet-stream",
            filename="download_file.zip",
        )
    
    
    def download_asset_sync(
        self, siteId: str, projectId: str, download_assets: DownloadAssets
    ):
        logger.info("Inside download_asset function")
        datsets_document = self.folder_management_dao.get_all_document_sync(
            filter_document={
                "project_id": projectId,
                "dataset_location.0.path": {
                    "$regex": download_assets.source,
                    "$options": "i",
                },
            },
            collection="datasets",
        )
        modules_document = self.folder_management_dao.get_all_document_sync(
            filter_document={
                "project_id": projectId,
                "module_location.path": {
                    "$regex": download_assets.source,
                    "$options": "i",
                },
            },
            collection="modules",
        )
        if not modules_document and download_assets.source.endswith('.zip'):
            return self.send_file_download_response(Path(download_assets.source) )
        documents = datsets_document + modules_document
        if not documents:
            raise HTTPException(
                status_code=404,
                detail="No documents found for the given site and project ID.",
            )

        # If there's only one document and it's a file, return it directly
        if len(documents) == 1:
            if "dataset_type" in documents[0].keys():
                if documents[0]["dataset_type"] == DatasetType.IMAGE_DATASET:
                    img_ds_path = documents[0]["dataset_location"][0]["path"]
                    uploads_folder = os.path.join(img_ds_path, ImageDatasetSubFolders.UPLOADS.value)
                    metadata_path = None
                    if os.path.exists(uploads_folder) and os.path.isdir(uploads_folder):
                        folder_path = Path(uploads_folder)
                        metadata_path =os.path.join(img_ds_path, ImageDatasetSubFolders.IMAGES_METADATA.value)
                        if os.path.exists(metadata_path) and os.path.isdir(metadata_path):
                            metadata_path = Path(metadata_path)
                        else:
                            metadata_path = None
                    else:
                        folder_path = Path(img_ds_path)
                    temp_dir = tempfile.mkdtemp()
                    zip_path = os.path.join(temp_dir, f"download_file.zip")
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                        files_list = self.folder_management_dao.get_all_document_sync({"dataset_id": str(documents[0]['_id']), "is_folder": False}, 
                                                                                       "image_datasets_files")
                        for file_det in files_list:
                            try:
                                file_path = Path(file_det["file_path"])
                                if os.path.exists(file_path):
                                    zipf.write(file_path, arcname=file_path.relative_to(folder_path))
                            except:
                                continue
                      
                        if metadata_path != None:
                            for root, dirs, files in os.walk(metadata_path):
                                for file in files:
                                    try:
                                        file_path = Path(root) / file
                                        if os.path.exists(file_path):                               
                                            zipf.write(file_path, arcname=file_path.relative_to(metadata_path))
                                    except:
                                        continue
                    # Return the zip file as a response after it is created
                    return FileResponse(
                        zip_path,
                        media_type="application/octet-stream",
                        filename=f"{folder_path.name}.zip"
                    )

                if documents[0]["dataset_type"] != "FOLDER":
                    file_path = Path(documents[0]["dataset_location"][0]["path"])
                    if file_path.is_file():
                        return self.send_file_download_response(
                            file_path=file_path
                        )
                else:
                    temp_dir = tempfile.mkdtemp()
                    zip_path = os.path.join(temp_dir, "download_file.zip")
                    file_path = Path(documents[0]["dataset_location"][0]["path"])
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                        return FileResponse(
                            zip_path,
                            media_type="application/octet-stream",
                            filename="download_file.zip",
                        )
            else:
                file_path = Path(documents[0]["module_location"]["path"])
                if file_path.is_file():
                    return self.send_file_download_response(file_path=file_path)

        # Otherwise, create a zip file with all the documents
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "download_file.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for document in documents:
                if "dataset_type" in document.keys():
                    file_path = document["dataset_location"][0]["path"]
                else:
                    file_path = document["module_location"]["path"]
                relative_path = os.path.relpath(file_path, download_assets.source)
                if os.path.isfile(file_path):
                    arcname = os.path.join(
                        os.path.split(relative_path)[0],
                        document["name"] + os.path.splitext(file_path)[1],
                    )
                    zipf.write(file_path, arcname=arcname)

        return FileResponse(
            zip_path,
            media_type="application/octet-stream",
            filename="download_file.zip",
        )