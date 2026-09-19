import asyncio
import io
import json
import logging
import os
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

import aiofiles
import pytz
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.api.endpoints.v1.data.assets.routes import AssetsRouter
from app.services.data.assets.custom_python_widget_recipes.dao import (
    CustomPythonWidgetRecipeDao,
)
from app.services.data.assets.custom_python_widget_recipes.schemas import (
    CustomPythonWidgetRecipe,
    CustomPythonWidgetRecipeStatus,
)
from app.services.data.assets.modules.schemas import AccessMode, FileDetailsList
from app.services.impex.schemas import (
    CustomWidgets,
    WorkflowImportRequest,
    WorkflowModel,
)
from app.services.impex.service import ImpExService
from app.services.workflows.sessions.schemas import CreateWorkflowSessionRequest

logger = logging.getLogger(__name__)


class ImportService(ImpExService):
    def __init__(
        self,
        db_sync_client: Optional[MongoClient] = None,
        db_async_client: Optional[AsyncIOMotorClient] = None,  # type: ignore
    ):
        super().__init__(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.custom_python_widget_recipe_dao = CustomPythonWidgetRecipeDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    async def import_workflow_artifact(
        self,
        site_id: str,
        project_id: str,
        import_request: WorkflowImportRequest,
    ) -> Dict[str, Any]:
        """
        Imports a workflow artifact from the extracted files.

        Args:
            site_id (str): The site ID.
            project_id (str): The project ID.
            import_request (WorkflowImportRequest): The import request data.

        Returns:
            Dict[str, Any]: A dictionary containing 'save_object' and 'new_session_id'.
        """
        logger.info("Starting workflow artifact import")
        new_session_id = ""
        try:
            workflow_model = self._get_workflow_model(
                os.path.join(self.temp_dir, "workflow.json")
            )

            module_id_mapping = {}
            if workflow_model.custom_widgets:
                module_id_mapping = await self._process_custom_widgets(
                    workflow_model.custom_widgets, site_id, project_id, import_request
                )

            new_session_id = await self.session_service.create_workflow_session_async(
                user_id=import_request.user_id,
                user_name=import_request.user_name,
                site_id=site_id,
                project_id=project_id,
                create_session_req_obj=CreateWorkflowSessionRequest(
                    name=import_request.workflow_name,
                    description=import_request.workflow_description,
                ),
            )

            workflow_data = workflow_model.workflow_data
            save_object = {
                "widgets": workflow_data.widgets,
                "start": workflow_data.start,
                "end": workflow_data.end,
                "client_tags": workflow_data.client_tags,
                "user_id": import_request.user_id,
                "user_name": import_request.user_name,
            }

            urn_mapping = self.generate_new_urns(workflow_data.widgets)
            mappings = {**module_id_mapping, **urn_mapping}
            save_object = self.update_workflow_data(save_object, mappings)

            logger.info("Workflow artifact import completed successfully")
            return {"save_object": save_object, "new_session_id": new_session_id}
        except Exception as e:
            logger.exception(f"Error importing workflow artifact: {e}")
            self.cleanup()
            if new_session_id:
                await self.session_service.delete_workflow_session_async(
                    session_id=new_session_id,
                )
                logger.info(
                    f"Deleted newly created session {new_session_id} due to import failure"
                )
            raise

    def process_zip_file(self, zip_file: UploadFile):
        """
        Processes the uploaded ZIP file.

        Args:
            zip_file (UploadFile): The uploaded ZIP file.

        Raises:
            Exception: If HMAC verification fails or processing fails.
        """
        logger.info("Processing uploaded ZIP file")
        try:
            zip_file.file.seek(0)
            zip_content = zip_file.file.read()
            bzip_content = io.BytesIO(zip_content)
            with zipfile.ZipFile(bzip_content, "r") as zipf:
                zipf.extractall(self.temp_dir)

            workflow_zip_path = os.path.join(self.temp_dir, "workflow.zip")
            hmac_file_path = os.path.join(self.temp_dir, "hmac.txt")

            computed_hmac = self.compute_hmac(workflow_zip_path)
            with open(hmac_file_path, "r") as f:
                stored_hmac = f.read().strip()

            if not self.compare_hmac(computed_hmac, stored_hmac):
                raise ValueError("HMAC verification failed")

            with zipfile.ZipFile(workflow_zip_path, "r") as zip_ref:
                zip_ref.extractall(self.temp_dir)

            logger.info("Uploaded ZIP file processed successfully")
        except Exception as e:
            logger.exception(f"Error processing ZIP file: {e}")
            self.cleanup()
            raise

    async def _process_custom_widgets(
        self,
        custom_widgets: CustomWidgets,
        site_id: str,
        project_id: str,
        import_request: WorkflowImportRequest,
    ) -> Dict[str, str]:
        """
        Processes custom widgets from the workflow import.

        Args:
            custom_widgets (CustomWidgets): The custom widgets to process.
            site_id (str): The site ID.
            project_id (str): The project ID.
            import_request (WorkflowImportRequest): The import request data.

        Returns:
            Dict[str, str]: Mapping from old module IDs to new module IDs and old Widget IDs to new Widget IDs.
        """
        logger.info("Processing custom widgets")
        module_widget_id_mapping = {}
        old_widget_ids = custom_widgets.widget_ids
        try:
            for module_id, widget_info in custom_widgets.widget_info.items():
                file_path = (
                    self.temp_dir + widget_info.path
                )  # os.path.join(self.temp_dir, widget_info.path)
                file_name = file_path.split("/")[-1]
                if not os.path.exists(file_path):
                    logger.error(f"Module file not found: {file_path}")
                    recipe_data = widget_info.recipe.dict()
                    original_recipe_name = recipe_data['name']
                    recipe_data['name'], existing_recipe_id, existing_module_id = await self._generate_unique_recipe_name(
                        base_name=original_recipe_name
                    )
                    if existing_recipe_id:
                        logger.info(f"Recipe name '{original_recipe_name}' already exists. Using existing recipe ID and module ID.")
                        module_widget_id_mapping[module_id] = existing_module_id
                        module_widget_id_mapping[old_widget_ids[module_id]] = existing_recipe_id
                        continue
                    logger.error(f"Unable to process module '{module_id}' as the file is missing and no existing record was found.")
                    raise FileNotFoundError(f"Module file not found: {file_path}")

                async with aiofiles.open(file_path, "rb") as file_:
                    file_content = await file_.read()
                    upload_file = UploadFile(
                        file=io.BytesIO(file_content), filename=file_name
                    )
                    file_upload_res: FileDetailsList = (
                        await AssetsRouter.multiple_file_uploads(
                            siteId=site_id, projectId=project_id, files=[upload_file]
                        )
                    )
                uploaded_file_path = str(file_upload_res.files[0].file_path)

                metadata = await asyncio.to_thread(
                    self.module_service.get_metadata, uploaded_file_path
                )

                new_module_id = await self.module_service.save_python_module_helper_async(
                    module_path=uploaded_file_path,
                    name=file_name,
                    project_id=project_id,
                    site_id=site_id,
                    description="Imported as part of CustomPythonWidgetRecipe import",
                    access_mode=AccessMode.EXTERNAL,
                    user_id=import_request.user_id,
                    created_by=import_request.user_id,
                    custom_code_metadata=metadata,
                )

                recipe_data = widget_info.recipe.dict()
                recipe_data.update(
                    {
                        "module_id": new_module_id,
                        "site_id": site_id,
                        "project_id": project_id,
                        "created_by": import_request.user_id,
                        "created_at": datetime.now(pytz.utc),
                        "last_modified_by": import_request.user_id,
                        "last_modified_at": datetime.now(pytz.utc),
                        "version": "1.0",
                        "recipe_status": CustomPythonWidgetRecipeStatus.PUBLISHED,
                    }
                )
                original_recipe_name = recipe_data['name']
                recipe_data['name'], existing_recipe_id, _ = await self._generate_unique_recipe_name(
                    base_name=original_recipe_name
                )
                if existing_recipe_id:
                    logger.info(f"Recipe name '{original_recipe_name}' already exists. Using existing recipe ID.")
                    recipe_id = existing_recipe_id
                else:
                    recipe = CustomPythonWidgetRecipe(**recipe_data)
                    recipe_id = await self.custom_python_widget_recipe_dao.insert_custom_python_widget_recipe_async(
                        recipe
                    )

                    new_widget_id = (
                        await self.custom_python_widget_service.publish_as_widget(
                            custom_python_widget_recipe=recipe,
                            project_id=project_id,
                            site_id=site_id,
                            user_id=import_request.user_id,
                            widget_id=None,
                            widget_version=None,
                        )
                    )

                    logger.info(f"Processed custom widget id: {new_widget_id}")

                    module_widget_id_mapping[module_id] = str(new_module_id)
                    module_widget_id_mapping[old_widget_ids[module_id]] = str(new_widget_id)
                    logger.info(f"Processed custom widget module_id: {module_id}")
        except Exception as e:
            logger.exception(
                f"Error processing custom widget module_id {module_id}: {e}"
            )
            raise

        return module_widget_id_mapping

    async def _generate_unique_recipe_name(self, base_name: str) -> (str, Optional[str], Optional[str]):
        try:
            existing_record = await self.custom_python_widget_recipe_dao.db_async.custom_python_widget_recipes.find_one(
                {"name": base_name}
            )
            if existing_record:
                logger.info(f"Recipe name '{base_name}' already exists. Using the existing record.")
                return existing_record["name"], str(existing_record.get("_id")), str(existing_record.get("module_id"))
            return base_name, None, None
        except Exception as e:
            logger.error(f"Error generating unique recipe name for '{base_name}': {e}")
            raise
    def _get_workflow_model(self, workflow_json_file: str) -> WorkflowModel:
        """
        Reads the workflow model from the JSON file.

        Args:
            workflow_json_file (str): Path to the workflow JSON file.

        Returns:
            WorkflowModel: The workflow model object.
        """
        logger.debug(f"Loading workflow model from {workflow_json_file}")
        try:
            with open(workflow_json_file, "r") as f:
                workflow_data = json.load(f)
            return WorkflowModel(**workflow_data)
        except Exception as e:
            logger.exception(f"Error loading workflow model: {e}")
            raise

    @staticmethod
    def update_workflow_data(workflow_data: Any, mapping: Dict[str, str]) -> Any:
        """
        Updates workflow data by replacing old IDs with new IDs based on the provided mapping.

        Args:
            workflow_data (Any): The workflow data to update.
            mapping (Dict[str, str]): Mapping from old IDs to new IDs.

        Returns:
            Any: The updated workflow data.
        """
        logger.debug("Updating workflow data with new IDs")
        try:
            workflow_str = json.dumps(workflow_data, default=str)
            for old_value, new_value in mapping.items():
                workflow_str = workflow_str.replace(old_value, new_value)
            return json.loads(workflow_str)
        except Exception as e:
            logger.exception(f"Error updating workflow data: {e}")
            raise

    @staticmethod
    def generate_new_urns(widgets: Any) -> Dict[str, str]:
        """
        Generates new URNs for the widgets.

        Args:
            widgets (Any): The list of widgets.

        Returns:
            Dict[str, str]: Mapping from old URNs to new URNs.
        """
        logger.debug("Generating new URNs for widgets")
        urn_mapping = {}
        for widget in widgets:
            old_urn = widget.get("urn")
            if old_urn:
                new_urn = str(uuid4())
                urn_mapping[old_urn] = new_urn
                widget["urn"] = new_urn
        return urn_mapping
