import asyncio
import logging
import os
import re
import shutil
import zipfile
import tempfile
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Optional
from uuid import uuid4
from pymongo import MongoClient
import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    WebSocket,
    status,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import FilePath, PositiveInt
from asgi_correlation_id import correlation_id
from app.core.db.db_utils import get_db_async, get_db_sync

from app.api.endpoints.v1.data.eda.routes import Message
from app.config.env_vars import environment
from app.core.services.jwt_token_utils.jwt_token_utils import decodeJWT
from app.services.access_controls.user_projects.service import (
    UsersProjectsMappingsService,
)
from app.services.admin.authentication.service import AuthenticationService
from app.services.AI.mobo.service import MOBOService
from app.services.admin.projects.service import ProjectService
from app.services.data.assets.modules.utils import redirect_print_to_file

from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationModel,
    NotificationType,
    NotificationCategory,
    NotificationImportance,
)

from app.services.data.assets.datasets.schemas import (
    AccessMode,
    AssetsListResponse,
    Dataset,
    DatasetSource,
    DatasetType,
    DatasetDeleteType,
    DatasetRenameBody,
    DatasetRenameResponse,
    DatasetUploadResponse,
    DeleteDatasetsRequest,
    DeleteDatasetsResponse,
    DatasetFileTypes,
    DatasetType,
    UploadPlace,
    DatasetFileDataPreviewResponse,
    DatasetMetadata,
    DatasetSourceFormats,
    GetFilesListMountedRequest,
)
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.assets.modules.schemas import (
    CodeValidationRequest,
    CodeValidationResponse,
    CreateModuleRequest,
    CreateModuleResponse,
    CustomCodeMetadataResponse,
    FileContentResponse,
    FileCopyResponse,
    FileDetails,
    FilePathRequest,
    FileCopyRequest,
    VizFolderDetail,
    FileDetailsList,
    ModuleUploadResponse,
    ModulesListResponse,
    Module,
)
from app.services.data.folder_management.service import FolderManagement
from app.services.data.elastic_search.schemas import LogsResponse
from app.services.data.assets.modules.service import (
    ModuleService,
)
from app.services.data.elastic_search.service import ElasticSearchLogRetrievalService
from app.services.workflows.designer.service import WorkflowDesignerService
from app.utils.file_utils import FileUtils
from app.utils.module_utils import parse_numpy_doc_string
from app.services.data.folder_management.service import FolderManagement
from app.api.rbac.end_points_v1_access_control import CheckNameRoute, is_subfolder
from app.services.data.folder_management.schema import CreateFolder

logger = logging.getLogger(__package__)

assets_router = APIRouter(tags=["Assets"], route_class=CheckNameRoute)
active_rescale_scheduler_connections = []
CUSTOM_CODE_FUNCTION_NAME = os.environ.get(
    "CUSTOM_CODE_FUNCTION_NAME", "hexaind_custom_widget_function"
)
MIME_TYPES = {
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".parquet": "application/octet-stream",  # No specific MIME type for Parquet
    ".py": "text/x-python",
}  # TODO: need to convert to model


class AssetsRouter:

    def __init__(self):
        """
        Class Initialization
        """
        pass

    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/read_file_content",
        response_model=None,
    )
    async def read_file(siteId: str, projectId: str, file_detail: FileDetails):

        file_path = file_detail.file_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        try:
            images_ext = [
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".bmp",
                ".tiff",
            ]  # Add other image formats as needed
            video_ext = [
                ".mp4",
                ".avi",
                ".mov",
                ".mkv",
                ".flv",
                ".wmv",
            ]  # Add other video formats as needed

            if file_path.suffix in images_ext + video_ext:
                return FileResponse(path=file_path, filename=file_path.name)
            elif file_path.suffix == ".html":
                return FileResponse(
                    path=file_path,
                    filename=os.path.basename(file_path),
                    media_type="text/html",
                )
            else:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                return FileContentResponse(content=content)

        except UnicodeDecodeError:
            # If UTF-8 decoding fails, read as binary
            return FileResponse(
                path=str(file_path), media_type="image/jpeg", filename=file_path.name
            )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to read the file: {str(e)}"
            )

    @assets_router.websocket("/v1/assets/rescale_status")
    async def rescale_socket_endpoint(websocket: WebSocket):
        await websocket.accept()
        active_rescale_scheduler_connections.append(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                logger.info(f"Received data: {data}")
                # Broadcast the message to all connected clients
                for connection in active_rescale_scheduler_connections:
                    if connection != websocket:
                        try:
                            await connection.send_text(data)
                        except RuntimeError as e:
                            logger.error(f"Error sending message: {e}")
                            # Remove connection if it's closed
                            active_rescale_scheduler_connections.remove(connection)
        except WebSocketDisconnect:
            active_rescale_scheduler_connections.remove(websocket)
            logger.info("WebSocket disconnected")

    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/dataset/tabular/upload",
        response_model=DatasetUploadResponse,
    )
    def upload_dataset(
        siteId: str,
        projectId: str,
        name: str,
        description: str,
        file_type: DatasetFileTypes,
        upload_type: UploadPlace = UploadPlace.DATASETS,
        file: UploadFile = File(...),
        token: str = "",
        destination_folder: str = "",
        workflow_id: Optional[str] = "",
        access_mode: AccessMode = AccessMode.EXTERNAL,
        dataset_type: DatasetType = DatasetType.TABULAR,
        tags: Optional[
            str
        ] = [],  # comma separated tags string and default is empty list
        client: MongoClient = Depends(get_db_sync),
    ) -> DatasetUploadResponse:
        logger.info("Inside upload dataset method from assets.")

        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid4()}.{file_extension}"

        # Get the user
        auth_serv = AuthenticationService(db_sync_client=client)
        user = auth_serv.get_user_by_token_or_id_sync(token=token)
        if tags:
            tags = tags.split(",")
        # # Define the directory to save files and ensure it exists
        upload_folder = environment.datasets_folder / f"p_{projectId}"
        if destination_folder != "":
            upload_folder = upload_folder / destination_folder

        folder_mngmnt_service = FolderManagement(db_sync_client=client)
        if upload_type == UploadPlace.WORKFLOWS:
            # workflow_id = "6667fc3b7f1cc76cbfbb6284"
            upload_folder = Path(
                environment.wf_inputs_folder.format(
                    projectId,
                    workflow_id,
                )
            )
            proj_service = ProjectService(db_sync_client=client)
            project = proj_service.get_project_by_id(project_id=projectId)

            workflow_service = WorkflowDesignerService(db_sync_client=client)
            workflow = workflow_service.get_workflow_by_id(workflow_id=workflow_id)
            folder_names = {
                f"p_{projectId}": project.name,
                "Workflow_Inputs": "WorkflowInputs",
                f"wf_{workflow_id}": workflow.name,
            }
            description = f"Uploaded as part CSV Widget of the workflow {workflow.name} in project {project.name}"
            folder_mngmnt_service.create_subfolders_sync(
                siteId=siteId,
                projectId=projectId,
                user_id=user.id,
                folder_names=folder_names,
                full_path=str(upload_folder),
            )
            name = file.filename.split(".")[-2]

        # os.makedirs(upload_folder, exist_ok=True)
        create_folder = CreateFolder(
            destination_folder=str(environment.datasets_folder),
            folder_name=f"p_{projectId}",
            user_id=user.id,
        )
        folder_mngmnt_service.create_folder_sync(
            siteId=siteId, projectId=projectId, create_folder=create_folder
        )
        # Define the full file path
        file_path = os.path.join(upload_folder, unique_filename)
        logger.info(f"uploading file to {file_path} location.")

        # Save the file
        try:
            datasets_service = DatasetsService(db_sync_client=client)
            # await datasets_service.validate_new_dataset_properties(name, projectId)
            file_cont = file.file.read()
            with open(file_path, "wb") as out_file:
                if file_cont:
                    out_file.write(file_cont)  # Write the content

            dataset_id = datasets_service.upload_dataset(
                siteId,
                projectId,
                name,
                description,
                dataset_type,
                user,
                file_path,
                file_extension,
                access_mode=access_mode,
                tags=tags,
            )

            logger.info(
                f"uploaded the file and added dataset to the db. dataset_id: {dataset_id}"
            )

            dataset = datasets_service.get_dataset_by_id_sync(dataset_id)
            # file_size = dataset.dataset_location[0].size
            # folder_datasets_obj= FolderManagement(db_async_client=client)
            # await folder_datasets_obj.update_destination_size(path_to_update=file_path,
            #                                             file_size=file_size,
            #                                             update_destination=True)
            try:
                # creating notification
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
                notification_service_obj = Notification(db_sync_client=client)
                notification_service_obj.create_notification_sync(
                    verified_notfication_obj
                )
            except Exception as e:
                logger.error(
                    f"Unable to create notificication due to exception: {str(e)}"
                )

            return DatasetUploadResponse(dataset_id=dataset_id)

        except Exception as e:
            logger.exception(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @assets_router.get(
        "/v1/sites/{site_id}/projects/{project_id}/assets/dataset/tabular/download/{dataset_id}"
    )
    def download_dataset(
        site_id: str,
        project_id: str,
        dataset_id: str,
        dataset_type: str = "TABULAR",
        client: MongoClient = Depends(get_db_sync),  # type: ignore
    ):
        try:
            if dataset_type == "TABULAR":
                logger.info("Downloading the dataset.")
                dataset_service = DatasetsService(db_sync_client=client)
                record = dataset_service.get_dataset_by_id_sync(dataset_id=dataset_id)
                file_path = Path(record.dataset_location[0].path)

                if len(record.dataset_location) != 1:
                    logger.error("Multiple file locations found.")
                    raise NotImplementedError(
                        status_code=400,
                        detail="Multiple file locations not supported at this moment.",
                    )

            elif dataset_type == "PYTHON":
                logger.info("Downloading the module.")
                module_service = ModuleService(db_sync_client=client)
                record = module_service.get_module_record_by_id(module_id=dataset_id)
                file_path = Path(record.module_location.path)

            logger.info(f"Fetched the {str(dataset_type)} dataset for downloading.")

            if not file_path.exists() or not file_path.is_file():
                logger.error(
                    f"File not found for the id {dataset_id}, name: {record.name} & filepath {file_path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="File not found"
                )

            file_extension = file_path.suffix
            media_type = MIME_TYPES.get(
                file_extension, "application/octet-stream"
            )  # Fallback to binary type
            logger.info(f"Downloaded the {str(dataset_type)} dataset")

            return FileResponse(
                path=file_path, filename=file_path.name, media_type=media_type
            )

        except Exception as e:
            logger.exception(f"Download failed with exception: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to download the dataset, Exception: {str(e)}",
            )

    @staticmethod
    @assets_router.get(
        "/v1/sites/{site_id}/projects/{project_id}/assets/dataset/file_preview/{dataset_id}"
    )
    async def preview_dataset_file(
        site_id: str,
        project_id: str,
        dataset_id: str,
        page_number: PositiveInt = 1,
        length: int = 1024,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> DatasetFileDataPreviewResponse:
        """
        Streams a segment of the file identified by dataset_id from the given offset and of the given length.
        Parameters:
        - dataset_id: str - Identifier for the dataset
        - offset: int - Byte offset to start reading from
        - length: int - Number of bytes to read
        - token: str
        - client
        """
        try:
            # TODO: check if decoded token user id can be used for logging purposes/
            dataset_service = DatasetsService(db_async_client=client)
            dataset = await dataset_service.get_dataset_by_id(dataset_id=dataset_id)
            if len(dataset.dataset_location) != 1:
                raise NotImplementedError(f"Not handling multi-location datasets")
            logger.info(
                f"returning file data for {dataset_id} , {page_number}, {length}"
            )
            data = FileUtils.read_file_segment(
                dataset.dataset_location[0].path, (page_number - 1) * length, length
            )
            next_page_number = page_number + 1 if data != "" else page_number
            return DatasetFileDataPreviewResponse(
                file_data=data, next_page_number=next_page_number
            )
        except Exception as e:
            # TODO : handle exceptions like FILE_NOT_FOUND, NOT HAVING EXPECTED ENCODING GRACEFULLY
            logger.exception(
                f"Exception occurred while previewing {dataset_id}, {page_number} , {length} : {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )

    @assets_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/assets/dataset/{dataset_id}",
        response_model=Dataset,
    )
    async def get_dataset(
        siteId: str,
        projectId: str,
        dataset_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> Dataset:

        try:
            datasets_handler = DatasetsService(db_async_client=client)
            return await datasets_handler.datasets_dao.get_dataset_by_id_async(
                dataset_id=dataset_id
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @assets_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/assets/datasets",
        response_model=AssetsListResponse,
    )
    async def get_datasets(
        siteId: str,
        projectId: str,
        dataset_type: str = Query(default=""),
        search_term: str = Query(default=None),
        page_limit: int = Query(default=10),
        page_number: int = Query(default=1),
        file_ext: str = None,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> AssetsListResponse:

        try:
            logger.info("inside get datasets method.")
            datasets_handler = DatasetsService(db_async_client=client)
            datasets, count = await datasets_handler.get_datasets_async(
                site_id=siteId,
                project_id=projectId,
                dataset_type=dataset_type,
                search_term=search_term,
                page_number=page_number,
                page_limit=page_limit,
                file_ext=file_ext,
            )
            logger.info(f"retrieved data and total datasets count is {count}")
            # fetch user names
            fetched_user_ids = []
            for dataset in datasets:
                fetched_user_ids.append(dataset.user_id)

            user_access_controls_service = UsersProjectsMappingsService(
                db_async_client=client
            )
            users_dict = await user_access_controls_service.get_users_dict(
                fetched_user_ids
            )
            users_names_dict = {key: users_dict[key].name for key in users_dict}
            for dataset in datasets:
                dataset.created_by = users_names_dict.get(dataset.user_id, "Not Found")
            return AssetsListResponse(datasets=datasets, total_count=count)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @assets_router.delete(
        "/v1/sites/{site_id}/projects/{project_id}/assets/datasets/delete",
        response_model=DeleteDatasetsResponse,
    )
    async def delete_datasets(
        site_id: str,
        project_id: str,
        delete_dataset_payload: DeleteDatasetsRequest,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> DeleteDatasetsResponse:
        logger.info("Starting to delete datasets.")

        try:
            datasets_handler = DatasetsService(db_async_client=client)
            logger.info("constructed datasets handler")
            response = await datasets_handler.delete_datasets_async(
                delete_dataset_payload.dataset_ids,
                delete_dataset_payload.dataset_type,
                DatasetDeleteType.SOFT,
            )
            logger.info("Deleted dataset/module.")

            return response

        except Exception as e:
            logger.exception(f"Failed with Exception: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e} for inputs",
            )

    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/multiple_file_uploads",
        response_model=FileDetailsList,
    )
    async def multiple_file_uploads_and_save(
        siteId: str,
        projectId: str,
        folder_name: str = Form(...),
        connectorId: str = Form(...),
        workflowId: str = Form(...),
        post_python: str = Form(...),
        files: List[UploadFile] = File(...),
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> FileDetailsList:

        try:
            mobo_obj = MOBOService(db_async_client=client)
            await mobo_obj.get_exp_file_path_async(
                workflow_id=connectorId,
                workflow_name=projectId,
                folder_name=folder_name,
            )
            record_detail = await mobo_obj.mobodao.get_rescale_record_id(
                connector_id=connectorId
            )
            if post_python:
                post_python = post_python.replace(" ", "").split(",")

            files_data = list()
            result_data = list()
            rescale_files = {"rescale_files": []}
            if record_detail:
                files_data = record_detail.get("platform_files", [])
                rescale_files = record_detail.get(
                    "rescale_files", {"rescale_files": []}
                )

            for file in files:
                rescale_files["rescale_files"] = [
                    d
                    for d in rescale_files["rescale_files"]
                    if d.get("file_name") != file.filename
                ]
                files_data = [
                    d for d in files_data if d.get("file_name") != file.filename
                ]
                folder_path = mobo_obj.folder_dir
                if file.filename in post_python:
                    # Validate workflowId before using it in path construction
                    if not re.match(r"^[a-zA-Z0-9_-]+$", workflowId):
                        raise ValueError("Invalid characters in workflowId")
                    folder_path = os.path.join(folder_path, workflowId)
                    os.makedirs(folder_path, exist_ok=True)

                file_path = f"{folder_path}/{file.filename}"
                if not re.match(r"^[a-zA-Z0-9_/\.]+$", file.filename):
                    raise ValueError("Invalid characters in path")

                clean_path = Path(file_path).resolve()
                with open(clean_path, "wb") as f:
                    f.write(file.file.read())

                temp = {"file_name": file.filename, "file_path": str(clean_path)}
                files_data.append(temp)
                result_data.append(temp)
            record_detail = dict(
                connector_id=connectorId,
                platform_files=files_data,
                rescale_files=rescale_files,
            )
            await mobo_obj.mobodao.insert_rescale_record(record_detail)
            return FileDetailsList(files=result_data)
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed multiple_file_uploads_and_save with exception: {str(e)}",
            )

    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/download_viz_data",
        response_model=None,
    )
    async def download_visualization(
        siteId: str, projectId: str, viz_detail: List[VizFolderDetail]
    ) -> FileResponse:
        try:
            # Ensure all folders exist
            for viz in viz_detail:
                if (
                    not os.path.isdir(viz.folder_path)
                    or "visualization" not in viz.folder_path.parts
                ):
                    traceback.print_exc()
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Error in Folder path: {viz.folder_path}",
                    )
            # Create a temporary file to store the zip
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "viz_folders.zip")

            # Create a zip file with all the folders, each prefixed with a unique identifier
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for viz in viz_detail:
                    folder_name = os.path.basename(viz.folder_path)
                    unique_id = str(viz.trial_index)
                    folder_base_path = os.path.dirname(viz.folder_path)

                    for dirname, subdirs, files in os.walk(viz.folder_path):
                        for filename in files:
                            # Path of the file in the filesystem
                            file_path = os.path.join(dirname, filename)
                            # Path in the zip file, adding a unique identifier to the folder name
                            arcname = file_path.replace(
                                folder_base_path, unique_id + "_" + folder_name
                            )
                            zipf.write(file_path, arcname=arcname)

            return FileResponse(
                zip_path,
                media_type="application/octet-stream",
                filename="viz_folders.zip",
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to download visualization with exception: {e}",
            )

    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/module/upload",
        response_model=ModuleUploadResponse,
    )
    async def upload_module(
        siteId: str,
        projectId: str,
        name: str,
        description: str,
        destination_folder: str = "",
        token: str = "",
        access_mode: AccessMode = AccessMode.EXTERNAL,
        file: UploadFile = File(...),
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> DatasetUploadResponse:
        logger.info("Inside upload module method from assets.")

        # file_extension = file.filename.split('.')[-1]
        # unique_filename = f"{uuid4()}.{file_extension}"

        file_extension = os.path.splitext(file.filename)[-1]

        unique_name = uuid4()
        unique_filename = f"{unique_name}{file_extension}"

        # Define the directory to save files and ensure it exists
        if destination_folder != "":
            upload_folder = destination_folder
        else:
            upload_folder = environment.modules_folder
        # hexaind_home = os.environ.get('HEXAIND_HOME', '/hexaind-data')
        # upload_folder = f"{hexaind_home}/modules/{unique_name}"

        os.makedirs(upload_folder, exist_ok=True)

        # Define the full file path
        file_path = os.path.join(upload_folder, unique_filename)
        logger.info(f"uploading file to {file_path} location.")

        # Save the file
        try:
            async with aiofiles.open(file_path, "wb") as out_file:
                while content := await file.read(1024):  # Read in chunks
                    await out_file.write(content)

            module_service = ModuleService(db_async_client=client)
            auth_serv = AuthenticationService(db_async_client=client)

            user = await auth_serv.get_user_by_token_or_id(token=token)
            module_id = await module_service.save_python_module_helper_async(
                module_path=file_path,
                project_id=projectId,
                site_id=siteId,
                user_id=user.id,
                action_id="",
                run_id="",
                workflow_id="",
                name=name,
                description=description,
                access_mode=access_mode,
                created_by=user.name,
            )
            logger.info(
                f"uploaded the file and added module to the db. dataset_id: {module_id}"
            )

            return ModuleUploadResponse(module_id=module_id)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @assets_router.get(
        "/v1/sites/{site_id}/projects/{project_id}/assets/modules/{module_id}",
        response_model=Module,
    )
    async def get_module(
        site_id: str,
        project_id: str,
        module_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> Module:
        try:
            module_service = ModuleService(db_async_client=client)
            return await module_service.get_module_record_by_id_async(
                module_id=module_id
            )
        except KeyError as e:
            logger.error(f"Failed with exception {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        except Exception as e:
            logger.exception(f"Failed with exception {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )

    @assets_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/assets/modules",
        response_model=ModulesListResponse,
    )
    async def get_modules(
        siteId: str,
        projectId: str,
        search_term: str = Query(default=None),
        page_limit: int = Query(default=10),
        page_number: int = Query(default=1),
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> ModulesListResponse:

        try:
            logger.info("inside get modules method.")
            module_service = ModuleService(db_async_client=client)
            modules, count = await module_service.get_all_modules_async(
                projectId=projectId,
                search_term=search_term,
                page_number=page_number,
                page_limit=page_limit,
                access_mode=AccessMode.EXTERNAL,
            )
            logger.info(f"retrieved data and total modules count is {count}")
            fetched_user_ids = []
            for module in modules:
                fetched_user_ids.append(module.user_id)

            user_access_controls_service = UsersProjectsMappingsService(
                db_async_client=client
            )
            users_dict = await user_access_controls_service.get_users_dict(
                fetched_user_ids
            )
            users_names_dict = {key: users_dict[key].name for key in users_dict}
            for module in modules:
                module.created_by = users_names_dict.get(module.user_id, "Not Found")

            return ModulesListResponse(modules=modules, total_count=count)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/datasets/mounted_files_list"
    )
    async def get_files_list_mounted(
        siteId: str,
        projectId: str,
        get_files_list_mounted_body: GetFilesListMountedRequest,
        file_ext: str = None,
    ):  # -> MountedResponseModel:
        """
        API to get the list of folders and files from the mounted drive

        Args:
            siteId (str): site id of the user.
            projectId (str): project id of the user.

        Returns:
            MountedResponseModel: Object with folders and files.
        """
        try:
            logger.info("Getting list of the files in the mounted drive.")
            if get_files_list_mounted_body.folder_path == "":
                folder_path = environment.hexaind_drive
                folder = {
                    "name": os.path.basename(folder_path),
                    "full_path": folder_path,
                    "type": "folder",
                }
            else:
                folder = DatasetsService.list_directory(
                    path=Path(get_files_list_mounted_body.folder_path),
                    file_ext=file_ext,
                )
            logger.info("Returning the list of files.")

            return folder

        except Exception as e:
            logger.exception(f"Failed with exception: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/dataset/tabular/mounted_upload",
        response_model=DatasetUploadResponse,
    )
    def file_from_mounted_dataset(
        siteId: str,
        projectId: str,
        name: str,
        description: str,
        dataset_type: DatasetType = DatasetType.TABULAR,
        destination_folder: str = "",
        upload_type: UploadPlace = UploadPlace.DATASETS,  # "DATASETS" #TODO UI Change as well
        workflow_id: Optional[str] = "",  # "DATASETS" #TODO UI Change as well
        file: FilePath = File(...),
        token: str = "",
        client: MongoClient = Depends(get_db_sync),
    ) -> DatasetUploadResponse:
        """
        This API is used to read a file from the mounted drive and create a dataset from it.

        Args:
            siteId (str): site id of the user.
            projectId (str): project id of the user.
            name (str): name of the dataset
            description (str): description of the dataset.
            file_type (TabularDatasetFileTypes): Type of file that is being uploaded
            file (FilePath, optional): _description_. Defaults to File(...).
            client (AsyncIOMotorClient, optional): _description_. Defaults to Depends(get_db_async).

        Raises:
            HTTPException: _description_

        Returns:
            DatasetUploadResponse: returns dataset id after successfull creation of dataset
        """
        logger.info("inside get file from mounted drive of DatasetsService")

        if not is_subfolder(
            environment.datasets_folder,
            os.path.join(environment.datasets_folder, f"p_{projectId}"),
        ):
            raise ValueError("Not Allowed to access the project details provided")

        file_extension = file.suffix.lstrip(".")
        unique_filename = f"{uuid4()}.{file_extension}"
        logger.info(f"Generated unique file name - {unique_filename}")

        # Define the directory to save files and ensure it exists
        if destination_folder != "":
            upload_folder = destination_folder
        else:
            upload_folder = environment.datasets_folder

        # upload_folder = environment.datasets_folder
        # if destination_folder != "":
        #     upload_folder = upload_folder / destination_folder

        # Define the full file path
        file_path = os.path.join(upload_folder, unique_filename)
        logger.info(f"Full file path {file_path}")

        auth_serv = AuthenticationService(db_async_client=client)
        user = auth_serv.get_user_by_token_or_id_sync(token=token)
        if upload_type == UploadPlace.WORKFLOWS:
            workflow_id = "6667fc3b7f1cc76cbfbb6284"
            upload_folder = Path(
                environment.wf_inputs_folder.format(
                    projectId,
                    workflow_id,
                )
            )
            proj_service = ProjectService(db_async_client=client)
            project = proj_service.get_project_by_id(project_id=projectId)

            workflow_service = WorkflowDesignerService(db_async_client=client)
            workflow = workflow_service.get_workflow_by_id(workflow_id=workflow_id)
            folder_names = {
                f"p_{projectId}": project.name,
                "Workflow_Inputs": "WorkflowInputs",
                f"wf_{workflow_id}": workflow.name,
            }
            folder_mngmnt_service = FolderManagement(db_async_client=client)
            folder_mngmnt_service.create_subfolders_sync(
                siteId=siteId,
                projectId=projectId,
                user_id=user.id,
                folder_names=folder_names,
                full_path=str(upload_folder),
            )

        # Save the file
        try:
            expected_ext = [file_extension.lower()]
            if dataset_type == DatasetType.PYTHON:
                expected_ext = ["py"]
            elif dataset_type == DatasetType.TEXT:
                expected_ext = ["txt", "text"]
            elif dataset_type == DatasetType.TABULAR:
                expected_ext = ["csv", "parquet"]

            if file_extension.lower() not in expected_ext:
                raise ValueError(
                    f"Un expected file type for {dataset_type}. Please upload the compatible file"
                )

            os.makedirs(upload_folder, exist_ok=True)

            shutil.copy(file, file_path)

            datasets_service = DatasetsService(db_async_client=client)

            if dataset_type == DatasetType.PYTHON:
                module_service = ModuleService(db_async_client=client)
                dataset_id = module_service.save_python_module_helper_sync(
                    module_path=file_path,
                    project_id=projectId,
                    site_id=siteId,
                    user_id=user.id,
                    action_id="",
                    run_id="",
                    workflow_id="",
                    name=name,
                    description=description,
                    access_mode=AccessMode.EXTERNAL,
                    created_by=user.name,
                )
            else:
                dataset_id = datasets_service.upload_dataset(
                    siteId,
                    projectId,
                    name,
                    description,
                    dataset_type,
                    user,
                    file_path,
                    file_extension,
                    DatasetSource.MOUNTED_DRIVE,
                )

            logger.info(f"Created dataset id: {dataset_id}")

            return DatasetUploadResponse(dataset_id=dataset_id)

        except Exception as e:
            logger.exception(f"Failed with exception: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/custom_python_code_builder/get_file_names",
        responses={
            status.HTTP_200_OK: {"model": List[str]},
            status.HTTP_404_NOT_FOUND: {"model": Message},
            status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
        },
        tags=["Custom Python Widget Builder"],
    )
    async def get_file_names_from_zip_file(
        request: Request, siteId: str, projectId: str, body: FilePathRequest
    ):
        """
        Endpoint for fetching filenames in zip file

        Parameters:
        - siteId (str): The ID of the site.
        - projectId (str): The ID of the project.
        - file_path (str): The uploaded zip file containing custom Python code.

        Returns:
        - List[str]: A response model containing list of file_names.
        """
        try:
            return ModuleService.get_files_in_zip(body.file_path)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Message(message=str(e)).model_dump(),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=Message(message=str(e)).model_dump(),
            )

    @staticmethod
    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/custom_python_code_builder/get_metadata",
        response_model=CustomCodeMetadataResponse,
        tags=["Custom Python Widget Builder"],
    )
    async def get_metadata_for_files(
        request: Request, siteId: str, projectId: str, body: FilePathRequest
    ):
        try:
            assets_router_process_pool: ProcessPoolExecutor = (
                request.state.assets_router_process_pool
            )
            loop = asyncio.get_event_loop()
            try:
                metadata = await loop.run_in_executor(
                    assets_router_process_pool,
                    ModuleService.get_metadata,
                    body.file_path,
                    CUSTOM_CODE_FUNCTION_NAME,
                    correlation_id.get(),
                )

                try:
                    help_details = parse_numpy_doc_string(
                        metadata.pydoc_string,
                        [x.name for x in metadata.function_inputs],
                    )
                except Exception as e:
                    help_details = {x.name: "" for x in metadata.function_inputs}
                    logger.exception(f"unable to parse docstring {e} : {metadata}")

                return CustomCodeMetadataResponse(
                    metadata=metadata,
                    succeeded=True,
                    help_details=help_details,
                    message="Metadata fetch success.",
                )
            except Exception as e:
                logger.exception(f"Exception: {str(e)}")
                return CustomCodeMetadataResponse(
                    succeeded=False,
                    metadata=None,
                    message=f"Failed with Exception {str(e)}",
                )
        except Exception as e:
            logger.exception(f"Exception: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with expression {e}",
            )

    @staticmethod
    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/custom_python_code_builder/create_module",
        response_model=CreateModuleResponse,
        tags=["Custom Python Widget Builder"],
    )
    async def create_new_module_using_file_path(
        request: Request,
        siteId: str,
        projectId: str,
        create_module_request: CreateModuleRequest,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> CreateModuleResponse:
        try:
            logger.info(f"creating module for file {create_module_request.file_path}")
            file_path = Path(create_module_request.file_path)
            module_service = ModuleService(db_async_client=client)
            decoded_token = decodeJWT(token=token)
            authentication_service = AuthenticationService()
            user = authentication_service.get_user_sync(
                user_id=decoded_token["user_id"]
            )

            try:
                dataset_name = file_name = Path(file_path).stem

                module_id = await module_service.save_python_module_helper_async(
                    module_path=create_module_request.file_path,
                    project_id=projectId,
                    site_id=siteId,
                    user_id=decoded_token["user_id"],
                    action_id="",
                    run_id="",
                    workflow_id="",
                    name=dataset_name,  # create_module_request.name,
                    description="Imported as part of CustomPythonWidgetRecipe browse",
                    access_mode=AccessMode.INTERNAL,
                    custom_code_metadata=create_module_request.metadata,
                    created_by=user.name,
                )

                logger.info(f"{file_path.name} got loaded to module {module_id}")
                message = f"created module from {file_path.name}"
                return CreateModuleResponse(
                    succeeded=True, message=message, module_id=module_id
                )

            except Exception as e:
                return CreateModuleResponse(
                    succeeded=False,
                    message=f"Unable to create module : {e}",
                    module_id=None,
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with expression {e}",
            )

    @staticmethod
    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/custom_python_code_builder/validate_custom_code",
        response_model=CodeValidationResponse,
        tags=["Custom Python Widget Builder"],
    )
    async def validate_custom_code(
        request: Request,
        siteId: str,
        projectId: str,
        validation_request: CodeValidationRequest,
    ) -> CodeValidationResponse:
        try:
            if not Path(validation_request.file_path).exists():
                raise ValueError("File not exists.")

            x_correlation_id = request.headers.get("X-Correlation-Id")
            logs_file_path = (
                environment.validation_logs_folder / f"{x_correlation_id}.log"
            )
            with redirect_print_to_file(logs_file_path):
                logger.info(f"entered validate custom code with.. {x_correlation_id}")
                print(f"entered validate custom code with.. {x_correlation_id}")
                # Optionally, you can add a check to ensure the header is present
                if not x_correlation_id:
                    raise HTTPException(
                        status_code=400, detail="x-correlation-id header is missing"
                    )

                assets_router_process_pool: ProcessPoolExecutor = (
                    request.state.assets_router_process_pool
                )
                loop = asyncio.get_event_loop()
                try:
                    # TODO: create constants class for keys in additional_params dict or pydantic class
                    await loop.run_in_executor(
                        assets_router_process_pool,
                        ModuleService.validate_custom_code,
                        validation_request.file_path,
                        validation_request.metadata,
                        validation_request.validation_inputs,
                        validation_request.validation_outputs,
                        x_correlation_id,
                        {"RESULTS_DIR": "", "CURRENT_PROJECT_ID": projectId},
                    )
                    return CodeValidationResponse(
                        succeeded=True, message="Validated Succesfully"
                    )

                except Exception as e:
                    logger.exception(f"Validation Failed {e}")
                    print(traceback.format_exc())
                    return CodeValidationResponse(
                        succeeded=False, message=f"Validation Failed {str(e)}"
                    )

        except Exception as e:
            logger.exception(str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/custom_python_code_builder/multiple_file_uploads",
        response_model=FileDetailsList,
    )
    async def multiple_file_uploads(
        siteId: str,
        projectId: str,
        files: List[UploadFile] = File(...),
        prefered_path: str = None,
    ) -> FileDetailsList:
        try:
            logger.info("multiple file uploads [mount drive]")
            if prefered_path:
                folder_path = f"{environment.data_folder}/cpw_widgets/{prefered_path}/{uuid4().hex}"
            else:
                folder_path = f"{environment.modules_folder}/{uuid4().hex}"
            folder_path = Path(folder_path).expanduser().resolve()
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info("created folder path")

            files_data = []
            for file in files:
                file_path = folder_path / file.filename
                async with aiofiles.open(file_path, "wb") as out_file:
                    while content := await file.read(1024):  # Read in chunks
                        await out_file.write(content)

                files_data.append(
                    {"file_name": file.filename, "file_path": str(file_path)}
                )
                logger.info("Returning the file data")
            return FileDetailsList(files=files_data)
        except Exception as e:
            logger.exception(f"Failed with exception: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed multiple_file_uploads_and_save with exception: {str(e)}",
            )

    @staticmethod
    @assets_router.websocket("/custom_python/validation_logs/{execution_id}")
    async def websocket_endpoint(websocket: WebSocket, execution_id: str):
        """
        WebSocket to send the activity logs of custom python code widget

        Args:
            websocket (WebSocket): _description_
            module_id (str): module id of the uploaded file
        """
        await websocket.accept()
        logs_file_path = environment.validation_logs_folder / f"{execution_id}.log"
        try:
            async with aiofiles.open(logs_file_path.absolute().as_posix(), "r") as file:
                while asyncio.sleep(0.1, True):
                    line = await file.readline()
                    if line:
                        await websocket.send_text(line)
        except Exception as e:
            pass

    @staticmethod
    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/dataset/rename/{dataset_id}",
        response_model=DatasetRenameResponse,
    )
    async def rename_existing_dataset(
        siteId: str,
        projectId: str,
        config: DatasetRenameBody,
        client: AsyncIOMotorClient = Depends(get_db_async),
        token: str = "",
    ) -> DatasetRenameResponse:

        try:
            logger.info("initializing service for rename.")
            datasets_handler = DatasetsService(db_async_client=client)
            auth_service = AuthenticationService(db_async_client=client)

            user = await auth_service.get_user_by_token_or_id(token=token)
            logger.info("fetched user from token.")
            await datasets_handler.datasets_dao.update_dataset_name_async(
                dataset_id=config.dataset_id,
                last_modified_by=user.name,
                name=config.name,
            )
            logger.info(f"Updated the dataset with new dataset name {config.name}.")

            # creating notification
            dataset = await datasets_handler.get_dataset_by_id(config.dataset_id)
            message = f"Dataset has been renamed to {dataset.name}"
            notification_obj = {
                "message": message,
                "category_id": config.dataset_id,
                "project_id": projectId,
                "notification_type": NotificationType.INFO,
                "importance": NotificationImportance.MEDIUM,
                "notification_category": NotificationCategory.DATA,
            }
            verified_notfication_obj = NotificationModel(**notification_obj)
            notification_service_obj = Notification(db_async_client=client)
            await notification_service_obj.create_notification(verified_notfication_obj)

            return DatasetRenameResponse(
                status=True, message=f"The dataset is modified to {config.name}"
            )

        except Exception as e:
            logger.exception(f"Faile with Exception: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @assets_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/sessions/{sessionId}/workflow/widget/{widgetURN}/activity_log"
    )
    async def widget_activity_log_in_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        widgetURN: str,
        size: int = Query(10, description="Number of logs per page"),
        next_cursor_timestamp: str = Query(
            None, description="Cursor for the next result timestamp"
        ),
        next_cursor_record_id: str = Query(
            None, description="Cursor for the next result id"
        ),
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> LogsResponse:

        try:
            """
            This API is reponsible for fetching the activity log from the elastic search server using session id and widget urn
            """

            elastic_service = ElasticSearchLogRetrievalService(db_async_client=client)
            return await elastic_service.get_widget_activity_log_in_session(
                session_id=sessionId,
                widget_urn=widgetURN,
                size=size,
                cursor_timestamp=next_cursor_timestamp,
                cursor_record_id=next_cursor_record_id,
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "widget_activity_log_in_session_error",
                    "message": str(e),
                },
            )

    @staticmethod
    @assets_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/workflow/runs/{runId}/widget/{widgetURN}/activity_log"
    )
    async def widget_activity_log_in_workflow_run(
        siteId: str,
        projectId: str,
        runId: str,
        widgetURN: str,
        size: int = Query(10, description="Number of logs per page"),
        next_cursor_timestamp: str = Query(
            None, description="Cursor for the next result timestamp"
        ),
        next_cursor_record_id: str = Query(
            None, description="Cursor for the next result id"
        ),
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> LogsResponse:

        try:
            """
            This API is reponsible for fetching the activity log from the elastic search server using run id and widget urn
            """

            elastic_service = ElasticSearchLogRetrievalService(db_async_client=client)
            return await elastic_service.widget_activity_log_in_workflow_run(
                run_id=runId,
                widget_urn=widgetURN,
                size=size,
                cursor_timestamp=next_cursor_timestamp,
                cursor_record_id=next_cursor_record_id,
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "widget_activity_log_in_session_error",
                    "message": str(e),
                },
            )

    @assets_router.post("/v1/sites/{siteId}/projects/{projectId}/assets/download_file")
    async def download_file(
        siteId: str,
        projectId: str,
        paths: List[FilePathRequest],
        download_json: bool = True,
    ):
        try:
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "download_file.zip")
            # Create a zip file with all the folders, each prefixed with a unique identifier
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for path in paths:
                    # Path of the file in the filesystem
                    file_path = path.file_path
                    # Path in the zip file, adding a unique identifier to the folder name
                    if os.path.isfile(file_path):
                        # Add the file to the zip
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname=arcname)
                    elif os.path.isdir(file_path):  # <-- Added this block
                        # Recursively add all files in the directory to the zip
                        for root, _, files in os.walk(file_path):
                            for file in files:
                                # Skip JSON files if download_json is False
                                if not download_json and file.lower().endswith(".json"):
                                    continue
                                full_path = os.path.join(root, file)
                                arcname = os.path.relpath(
                                    full_path, os.path.dirname(file_path)
                                )
                                zipf.write(full_path, arcname=arcname)
                    else:  # <-- Added this block
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Path {file_path} is neither a file nor a directory",
                        )

            return FileResponse(
                zip_path,
                media_type="application/octet-stream",
                filename="download_file.zip",
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to download file with exception: {e}",
            )

    @staticmethod
    @assets_router.post("/v1/sites/{site_id}/projects/{project_id}/assets/copy_file")
    async def copy_file(site_id: str, project_id: str, config: FileCopyRequest):
        logger.info(f"inside copy file api config: {config}")
        source = Path(config.source_path)
        destination = Path(config.destination_path)

        # Check if the source file exists
        if not source.is_file():
            logger.error(f"Source file not found: {source}")
            raise HTTPException(status_code=404, detail="Source file not found")

        # Create destination directory if it doesn't exist
        if not destination.exists():
            logger.error(f"destination path {destination} doesnt exist")
            folder_path = f"{environment.modules_folder}/{uuid4().hex}"
            destination = Path(folder_path).expanduser().resolve()
            destination.mkdir(parents=True, exist_ok=True)
            logger.info(f"created new destination path: {destination}")

        try:
            # Copy the file
            shutil.copy2(source, destination)
            logger.info("File copied successfully")
            return FileCopyResponse(
                status=True, message=f"File copied from {source} to {destination}"
            )
        except Exception as e:
            logger.exception(f"Copying failed with exception: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error copying file: {e}")

    @assets_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/assets/dataset/upload/multiple_text_file",
        response_model=List[DatasetUploadResponse],
    )
    def multiple_text_file(
        siteId: str,
        projectId: str,
        name: str,
        description: str,
        file_type: DatasetFileTypes = DatasetFileTypes.TEXT,
        upload_type: UploadPlace = UploadPlace.WORKFLOWS,
        file: List[UploadFile] = File(...),
        token: str = "",
        destination_folder: str = "",
        workflow_id: Optional[str] = "",
        access_mode: AccessMode = AccessMode.EXTERNAL,
        dataset_type: DatasetType = DatasetType.TEXT,
        client: MongoClient = Depends(get_db_sync),
    ) -> List[DatasetUploadResponse]:
        logger.info("Inside upload dataset method from assets.")

        # This API is seperatly upload multiple text files to cater the VPSC Simulation
        #

        # Get the user
        auth_serv = AuthenticationService(db_sync_client=client)
        user = auth_serv.get_user_by_token_or_id_sync(token=token)
        # # Define the directory to save files and ensure it exists
        upload_folder = environment.datasets_folder / f"p_{projectId}"
        if destination_folder != "":
            upload_folder = upload_folder / destination_folder

        folder_mngmnt_service = FolderManagement(db_sync_client=client)
        if upload_type == UploadPlace.WORKFLOWS:
            # workflow_id = "6667fc3b7f1cc76cbfbb6284"
            upload_folder = Path(
                environment.wf_inputs_folder.format(
                    projectId,
                    workflow_id,
                )
            )
            proj_service = ProjectService(db_sync_client=client)
            project = proj_service.get_project_by_id(project_id=projectId)

            workflow_service = WorkflowDesignerService(db_sync_client=client)
            workflow = workflow_service.get_workflow_by_id(workflow_id=workflow_id)
            folder_names = {
                f"p_{projectId}": project.name,
                "Workflow_Inputs": "WorkflowInputs",
                f"wf_{workflow_id}": workflow.name,
            }
            description = f"Uploaded as part CSV Widget of the workflow {workflow.name} in project {project.name}"
            folder_mngmnt_service.create_subfolders_sync(
                siteId=siteId,
                projectId=projectId,
                user_id=user.id,
                folder_names=folder_names,
                full_path=str(upload_folder),
            )
            # name = file.filename.split(".")[-2]

        # os.makedirs(upload_folder, exist_ok=True)
        create_folder = CreateFolder(
            destination_folder=str(environment.datasets_folder),
            folder_name=f"p_{projectId}",
            user_id=user.id,
        )
        folder_mngmnt_service.create_folder_sync(
            siteId=siteId, projectId=projectId, create_folder=create_folder
        )
        # Define the full file path

        # Save the file

        try:
            dataset_ids = []
            datasets_service = DatasetsService(db_sync_client=client)

            for one_file in file:
                if upload_type == UploadPlace.WORKFLOWS:
                    name = one_file.filename.split(".")[-2]
                file_extension = one_file.filename.split(".")[-1]
                unique_filename = f"{uuid4()}.{file_extension}"
                file_path = os.path.join(upload_folder, f"{name}.{file_extension}")
                if dataset_type == DatasetType.TEXT:
                    file_path = os.path.join(upload_folder, f"{name}.{file_extension}")

                logger.info(f"uploading file to {file_path} location.")
                # await datasets_service.validate_new_dataset_properties(name, projectId)
                file_cont = one_file.file.read()
                with open(file_path, "wb") as out_file:
                    if file_cont:
                        out_file.write(file_cont)  # Write the content

                dataset_id = datasets_service.upload_dataset(
                    siteId,
                    projectId,
                    name,
                    description,
                    dataset_type,
                    user,
                    file_path,
                    file_extension,
                )
                dataset_ids.append(dataset_id)
                logger.info(
                    f"uploaded the file and added dataset to the db. dataset_id: {dataset_id}"
                )

                dataset = datasets_service.get_dataset_by_id_sync(dataset_id)
                # file_size = dataset.dataset_location[0].size
                # folder_datasets_obj= FolderManagement(db_async_client=client)
                # await folder_datasets_obj.update_destination_size(path_to_update=file_path,
                #                                             file_size=file_size,
                #                                             update_destination=True)
                try:
                    # creating notification
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
                    notification_service_obj = Notification(db_sync_client=client)
                    notification_service_obj.create_notification_sync(
                        verified_notfication_obj
                    )
                except Exception as e:
                    logger.error(
                        f"Unable to create notificication due to exception: {str(e)}"
                    )

            return [DatasetUploadResponse(dataset_id=i) for i in dataset_ids]

        except Exception as e:

            logger.exception(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )


assets_router_obj = AssetsRouter()
