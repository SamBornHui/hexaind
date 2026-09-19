import asyncio
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.config.env_vars import environment
from app.core.db.db_utils import get_db_async, get_db_sync
from app.services.data.assets.datasets.schemas import *
from app.services.data.folder_management.schema import *
from app.services.data.folder_management.service import FolderManagement

logger = logging.getLogger(__package__)
folder_management_router = APIRouter(
    tags=["Folder Management"], prefix="/v1", route_class=CheckNameRoute
)


class FolderManagementRouter:
    def __init__(self):
        pass

    @folder_management_router.get(
        "/sites/{siteId}/projects/{projectId}/folder_structure"
    )
    async def get_folder_structure(
        siteId: str,
        projectId: str,
        folder_name: Path = None,
        file_ext: str = None,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):
        """
        Desc:
        Api to get folder structure of the hexaind-data

         Args:
            siteId (str): site id of the user.
            projectId (str): project id of the user.

        Returns:
           folder structure
        """
        try:
            logger.info("Getting the folder structure of mounted drive")
            folder_management_obj = FolderManagement(db_async_client=client)
            path_ = Path(os.path.join(environment.hexaind_data, "datasets"))

            if not folder_name:
                folder = await folder_management_obj.list_directory(
                    path=path_, file_ext=file_ext, project_id=projectId
                )
                logger.info("Returning the list of files.")
            else:
                folder = await folder_management_obj.list_directory(
                    path=folder_name, file_ext=file_ext, project_id=projectId
                )
            return folder

        except Exception as e:
            logger.error(
                f"Failed to get folder structure due to exception: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @folder_management_router.post("/sites/{siteId}/projects/{projectId}/create_folder")
    async def create_folder(
        siteId: str,
        projectId: str,
        create_folder: CreateFolder,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):
        try:
            logger.info("Inside create folder")
            folder_management_obj = FolderManagement(db_async_client=client)
            response = await folder_management_obj.create_folder(
                siteId, projectId, create_folder=create_folder
            )

            return response

        except Exception as e:
            logger.error(
                f"Failed to create folder due to exception: {str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "folder_creation_error", "message": str(e)},
            )

    @staticmethod
    @folder_management_router.post("/sites/{siteId}/projects/{projectId}/move_assets")
    async def move_assets(
        siteId: str,
        projectId: str,
        move_assets: MoveAssets,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):
        try:
            logger.info("Inside move assets")
            folder_management_obj = FolderManagement(db_async_client=client)
            response = await folder_management_obj.move_assets(
                siteId, projectId, move_assets
            )

            return response

        except Exception as e:
            logger.error(
                f"Failded to move assets due to exception: {str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "moving_assets_error", "message": str(e)},
            )

    @staticmethod
    @folder_management_router.post("/sites/{siteId}/projects/{projectId}/get_childern")
    async def get_childern(
        siteId: str,
        projectId: str,
        dataset: dict,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):
        try:
            logger.info("Inside get childern ")
            folder_management_obj = FolderManagement(db_async_client=client)
            response = await folder_management_obj.get_dataset_childern(
                projectId, dataset
            )

            return response

        except Exception as e:
            logger.error(
                f"Failded to move assets due to exception: {str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "moving_assets_error", "message": str(e)},
            )

    @staticmethod
    @folder_management_router.post("/sites/{siteId}/projects/{projectId}/rename_assets")
    async def rename_assets(
        siteId: str,
        projectId: str,
        rename_assets: RenameAssets,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):
        try:
            logger.info("Inside rename assets")
            folder_management_obj = FolderManagement(db_async_client=client)
            response = await folder_management_obj.rename_assets(
                siteId, projectId, rename_assets
            )
            return response
        except Exception as e:
            logger.error(
                f"Failed to rename asset due to exception:{str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "rename assets error", "message": str(e)},
            )

    @staticmethod
    @folder_management_router.post(
        "/sites/{siteId}/projects/{projectId}/create_dataset_duplicate"
    )
    async def create_dataset_duplicate(
        siteId: str,
        projectId: str,
        create_dataset: CreateDatasetDuplicate,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):
        try:
            logger.info("Inside create dataset duplicate")
            folder_management_obj = FolderManagement(db_async_client=client)
            response = await folder_management_obj.create_dataset_duplicate(
                siteId, projectId, create_dataset
            )
            return response

        except Exception as e:

            logger.error(
                f"Failed to duplicate datset due to exception:{str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "create dataset duplicate error", "message": str(e)},
            )

    @staticmethod
    @folder_management_router.delete(
        "/sites/{siteId}/projects/{projectId}/delete_asset"
    )
    async def delete_asset(
        siteId: str,
        projectId: str,
        delete_assets: DeleteAssets,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):
        try:
            folder_management_obj = FolderManagement(db_async_client=client)
            response = await folder_management_obj.delete_asset(
                siteId, projectId, delete_assets
            )
            return response

        except Exception as e:
            logger.error(
                f"Failed to duplicate delete assets due to exception:{str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "failed assets error", "message": str(e)},
            )

    @folder_management_router.post(
        "/sites/{siteId}/projects/{projectId}/download_asset"
    )
    def download_asset(
        siteId: str,
        projectId: str,
        download_assets: DownloadAssets,
        client: MongoClient = Depends(get_db_sync),
    ):
        try:

            folder_management_obj = FolderManagement(db_sync_client=client)
            file_response = folder_management_obj.download_asset_sync(
                siteId, projectId, download_assets
            )
            return file_response
        except Exception as e:
            logger.error(
                f"Failed to download assets due to exception:{str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "download assets error", "message": str(e)},
            )
