import asyncio
import logging
import os
import zipfile
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.services.impex.schemas import (
    CustomWidgets,
    WidgetInfo,
    WorkflowData,
    WorkflowModel,
)
from app.services.impex.service import ImpExService
from app.services.workflows.designer.base_schemas import WidgetType

logger = logging.getLogger(__name__)


class ExportService(ImpExService):
    def __init__(
        self,
        db_sync_client: Optional[MongoClient] = None,
        db_async_client: Optional[AsyncIOMotorClient] = None,  # type: ignore
    ):
        super().__init__(db_sync_client=db_sync_client, db_async_client=db_async_client)

    async def export_workflow_artifact(
        self, workflow_id: str, gen_hmac: bool = False
    ) -> str:
        """
        Retrieves and exports the workflow artifact for a given workflow ID.

        Args:
            workflow_id (str): The unique identifier of the workflow to export.
            gen_hmac (bool, optional): Whether to generate an HMAC file. Defaults to False.

        Returns:
            str: The path to the created ZIP file containing the exported workflow artifact.
        """
        logger.info(f"Starting export for workflow_id: {workflow_id}")
        try:
            workflow_data = await self.get_workflow_data(workflow_id)
            # In some cases workflow data contain's widgets with old module id's, as part of export design we are trying to modify the code to use differnt recipe
            for widget in workflow_data.widgets:
                if widget['type'] in "CUSTOM_CODE":                            
                    cpw = await self.custom_python_widget_service.get_widget_by_id(widget["config"]["widget_id"])
                    cpw_recipe = await self.custom_python_widget_recipe_service.get_recipe(cpw.recipe_id)
                    if widget['config']['module_id'] != cpw_recipe.module_id: 
                        logger.info(f"For {workflow_id}, while exporting modifying {widget['config']['module_id']} to {cpw_recipe.module_id} for {widget['urn']}::{widget['config']['widget_id']}")
                        widget['config']['module_id'] = cpw_recipe.module_id

            custom_widgets = await self.get_custom_widgets(workflow_data.widgets)
            workflow_model = WorkflowModel(
                workflow_data=workflow_data, custom_widgets=custom_widgets
            )
            zip_file_path = await asyncio.to_thread(
                self.create_zip_file, workflow_model
            )
            logger.info(f"Export completed for workflow_id: {workflow_id}")

            if gen_hmac:
                # Generate HMAC file
                hmac = self.compute_hmac(zip_file_path)
                zip_file_path = self._add_hmac_to_zip(zip_file_path, hmac)

            return zip_file_path
        except Exception as e:
            logger.exception(f"Error exporting workflow_id {workflow_id}: {e}")
            self.cleanup()
            raise

    async def get_workflow_data(self, workflow_id: str) -> WorkflowData:
        """
        Retrieves workflow data for a given workflow ID.

        Args:
            workflow_id (str): The ID of the workflow to retrieve.

        Returns:
            WorkflowData: An object containing the workflow data.
        """
        logger.debug(f"Fetching workflow data for workflow_id: {workflow_id}")
        workflow = await self.workflow_designer_service.get_workflow_by_id_without_schema_check_async(
            workflow_id=workflow_id
        )
        workflow_data = WorkflowData(
            widgets=workflow.get("widgets", []),
            start=workflow.get("start", []),
            end=workflow.get("end", []),
            client_tags=workflow.get("client_tags", None),
        )
        logger.debug(f"Retrieved workflow data for workflow_id: {workflow_id}")
        return workflow_data

    async def get_custom_widgets(self, widgets: List[Dict]) -> CustomWidgets:
        """
        Retrieves custom widgets based on the provided list of widget configurations.

        Args:
            widgets (List[Dict]): A list of widget configurations.

        Returns:
            CustomWidgets: An object containing Widget IDs and module information for the custom widgets.
        """
        logger.debug("Collecting custom widgets from workflow data")
        widget_ids, module_ids = self._collect_widget_ids_and_module_ids(widgets)
        if not module_ids:
            logger.debug("No custom widgets found in workflow data")
            return None
        module_records = await self._fetch_module_records(module_ids)
        recipes = await self._fetch_recipes(module_ids)
        modules = self._build_modules_dict(module_ids, module_records, recipes)
        return CustomWidgets(widget_ids=widget_ids, widget_info=modules)

    async def _fetch_module_records(self, module_ids: List[str]) -> Dict[str, Any]:
        try:
            module_records = await self.module_service.get_module_records_by_ids_async(
                module_ids
            )
            module_record_dict = {
                module_record.id: module_record for module_record in module_records
            }
            logger.debug(f"Fetched module records for module_ids: {module_ids}")
            return module_record_dict
        except Exception as e:
            logger.error(f"Error fetching module records: {e}")
            raise

    async def _fetch_recipes(self, module_ids: List[str]) -> Dict[str, Any]:
        try:
            recipes = await self.custom_python_widget_recipe_service.get_custom_python_widget_recipes_by_module_ids_async(
                module_ids
            )
            recipe_dict = {recipe.module_id: recipe for recipe in recipes}
            logger.debug(f"Fetched recipes for module_ids: {module_ids}")
            return recipe_dict
        except Exception as e:
            logger.error(f"Error fetching recipes: {e}")
            raise

    def _collect_widget_ids_and_module_ids(
        self, widgets: List[Dict]
    ) -> Tuple[Dict[str, str], List[str]]:
        """
        Collects Widget IDs and module IDs from a list of widgets.

        This method iterates over a list of widgets, extracting the Widget IDs and module IDs
        from widgets of type `WidgetType.CUSTOM_CODE`. It returns a dictionary mapping
        Module IDs to Widget IDs and a list of unique module IDs.

        Args:
            widgets (List[Dict]): A list of widget dictionaries. Each dictionary should
                                  contain a "config" key with a nested dictionary that
                                  includes a "module_id" key, and a "type" key indicating
                                  the widget type.

        Returns:
            Tuple[Dict[str, str], List[str]]: A tuple containing:
                - A dictionary mapping widget Module Ids to their corresponding Widget IDs.
                - A list of unique module IDs.
        """
        widget_ids: Dict[str, str] = {}
        module_ids_set = set()

        for widget in widgets:
            config = widget.get("config")
            if not config or widget.get("type") != WidgetType.CUSTOM_CODE:
                continue
            module_id = config.get("module_id")
            if not module_id:
                err = f"Widget {widget.get('urn')} is missing module_id in config."
                logger.error(err)
                raise ValueError(err)
            widget_ids[module_id] = config.get("widget_id")
            module_ids_set.add(module_id)

        module_ids = list(module_ids_set)
        logger.debug(f"Collected module_ids: {module_ids}")
        return widget_ids, module_ids

    def _build_modules_dict(
        self,
        module_ids: List[str],
        module_records: Dict[str, Any],
        recipes: Dict[str, Any],
    ) -> Dict[str, WidgetInfo]:
        """
        Builds a dictionary of modules with their corresponding information.

        Args:
            module_ids (List[str]): A list of module IDs to be processed.
            module_records (Dict[str, Any]): A dictionary containing module records,
                where keys are module IDs and values are module details.
            recipes (Dict[str, Any]): A dictionary containing recipes,
                where keys are module IDs and values are recipe details.

        Returns:
            Dict[str, WidgetInfo]: A dictionary where keys are module IDs and values
                are WidgetInfo objects containing the module path and recipe.
        """
        modules: Dict[str, WidgetInfo] = {}

        for module_id in module_ids:
            module_record = module_records.get(module_id)
            recipe = recipes.get(module_id)
            modules[module_id] = WidgetInfo(
                path=module_record.module_location.path.removeprefix(
                    str(self.base_path)
                ),
                recipe=recipe,
            )
            self.module_files.append(module_record.module_location.path)
            logger.debug(f"Added module {module_id} to modules dictionary")

        return modules

    def _add_hmac_to_zip(self, file_path: str, hmac: str) -> str:
        """
        Adds an HMAC (Hash-based Message Authentication Code) to a ZIP file.
        This method computes the HMAC for the given file, creates a new ZIP file,
        and writes the HMAC and the original file into the ZIP archive.
        Args:
            file_path (str): The path to the file for which the HMAC is to be computed.
            hmac (str): The HMAC string to be added to the ZIP file.
        Returns:
            str: The path to the newly created ZIP file containing the HMAC and the original file.
        """

        zip_file_path = os.path.join(self.temp_dir, f"{uuid4()}.zip")
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("hmac.txt", hmac)
            zipf.write(file_path, arcname="workflow.zip")

        return zip_file_path

    def create_zip_file(self, workflow_model: WorkflowModel) -> str:
        """
        Creates a ZIP file containing the workflow data and module files.

        Args:
            workflow_model (WorkflowModel): The workflow data to be included in the ZIP file.

        Returns:
            str: The file path to the created ZIP file.
        """
        logger.debug("Creating ZIP file for workflow export")
        zip_filename = os.path.join(self.temp_dir, f"{uuid4()}.zip")
        self.zip_file_path = zip_filename

        try:
            with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add workflow JSON
                workflow_json = workflow_model.model_dump_json(indent=4)
                zipf.writestr("workflow.json", workflow_json)
                logger.debug("Added workflow.json to ZIP file")

                # Add module files
                for file_path in self.module_files:
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"Module file not found: {file_path}")
                    arcname = os.path.relpath(file_path, self.base_path)
                    zipf.write(file_path, arcname=arcname)
                    logger.debug(f"Added {file_path} to ZIP file as {arcname}")

            logger.info(f"Created ZIP file at {zip_filename}")
            return zip_filename
        except Exception as e:
            logger.exception(f"Error creating ZIP file: {e}")
            self.cleanup()
            raise
