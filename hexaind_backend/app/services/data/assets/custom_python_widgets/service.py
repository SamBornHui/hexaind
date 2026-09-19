import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import subprocess
import tempfile
import os

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.services.data.assets.custom_python_widget_recipes.schemas import (
    CustomPythonWidgetRecipe,
)
from app.services.data.assets.custom_python_widgets.dao import CustomPythonWidgetsDao
from app.services.data.assets.custom_python_widgets.helper import (
    CustomPythonWidgetServiceHelper,
)
from app.services.data.assets.custom_python_widgets.schemas import CustomPythonWidget, LintError
from app.services.data.assets.modules.schemas import AccessMode
from app.services.workflows.designer.dao import WorkflowDesignerDao
from app.services.workflows.designer.schemas import Workflow
from app.services.workflows.scheduling.dao import ScheduleDao
from app.services.workflows.scheduling.schemas import WFSchedule

logger = logging.getLogger(__package__)


class CustomPythonWidgetService:

    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:
        self.custom_python_widgets_dao = CustomPythonWidgetsDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.custom_python_widget_service_helper = CustomPythonWidgetServiceHelper(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.wf_designer_dao = WorkflowDesignerDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.wf_scheduling_dao = ScheduleDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    async def get_workflows_with_widget(self, widget_id: str) -> List[Workflow]:
        query = {
            "widgets": {
                "$elemMatch": {"type": "CUSTOM_CODE", "config.widget_id": widget_id}
            }
        }
        workflows, count = await self.wf_designer_dao.fetch_workflows_with_custom_query(
            query
        )
        if len(workflows) != count:
            raise NotImplementedError(f"fetched count is greater than expected")
        return workflows

    async def get_schedules_with_workflows(self, workflow_id: str) -> List[WFSchedule]:
        query = {"workflow_id": workflow_id}
        wf_schedules, count = (
            await self.wf_scheduling_dao.fetch_wf_schedules_with_custom_query(query)
        )
        if len(wf_schedules) != count:
            raise NotImplementedError(f"fetched count is greater than expected")

        return wf_schedules

    async def validate_widget_recipe(
        self,
        custom_python_widget_recipe: CustomPythonWidgetRecipe,
        user_id="",
        project_id="",
        site_id="",
    ):
        dataset_kwargs = {
            "user_id": user_id,
            "project_id": project_id,
            "site_id": site_id,
            "name": f"{uuid4()}",
        }
        current_version = str(
            await self.custom_python_widgets_dao.count_widgets_with_recipe_id(
                custom_python_widget_recipe.id
            )
        )
        self.custom_python_widget_service_helper.convert_recipe_to_widget(
            custom_python_widget_recipe,
            widget_version=current_version,
            dataset_kwargs=dataset_kwargs,
            dry_run=True,
        )
        # TODO: More validations to be added here i.e check module inputs with widget inputs..etc

    async def get_next_widget_version(self, widget_name: str):
        return str(await self.custom_python_widgets_dao.count_widgets(widget_name) + 1)

    async def publish_as_widget(
        self,
        custom_python_widget_recipe: CustomPythonWidgetRecipe,
        user_id="",
        project_id="",
        site_id="",
        widget_id: Optional[str] = None,
        widget_version: Optional[str] = None,
    ) -> str:
        # TODO: before publishing we need to check that validation is done or not.
        dataset_kwargs = {
            "user_id": user_id,
            "project_id": project_id,
            "site_id": site_id,
            "name": f"{uuid4()}",
        }
        if widget_id and widget_version:
            # check if widget_id and widget_version are valid
            existing_widgets_hash_map = {
                existing_widget.id: existing_widget
                for existing_widget in await self.custom_python_widgets_dao.get_widgets_with_recipe_id(
                    custom_python_widget_recipe.id
                )
            }
            if widget_id not in existing_widgets_hash_map:
                raise ValueError(
                    f"Provided widget {widget_id} is not linked with this draft {custom_python_widget_recipe.id}"
                )
            if existing_widgets_hash_map[widget_id].widget_version != widget_version:
                raise ValueError(f"Mismatched widget version and widget id.")

            existing_widget = existing_widgets_hash_map[widget_id]
            self.custom_python_widgets_dao.dump_to_old(existing_widget)
            overriding_widget = (
                self.custom_python_widget_service_helper.convert_recipe_to_widget(
                    custom_python_widget_recipe,
                    widget_version=widget_version,
                    dataset_kwargs=dataset_kwargs,
                )
            )
            await self.update_cpw_async(user_id, existing_widget.id, overriding_widget)
            return widget_id
        else:
            # not overriding a widget but creating a new one
            count = await self.custom_python_widgets_dao.count_widgets_with_recipe_id(
                custom_python_widget_recipe.id
            )
            widget_version = str(count + 1)
            widget = self.custom_python_widget_service_helper.convert_recipe_to_widget(
                custom_python_widget_recipe,
                widget_version=widget_version,
                dataset_kwargs=dataset_kwargs,
            )
            return self.custom_python_widgets_dao.insert_custom_python_widget(widget)

    async def get_all_widgets_async(
        self, project_id: str, search_term: str, page_number: int, page_limit: int, access_mode=None
    ) -> Tuple[List[CustomPythonWidget], int]:
        return await self.custom_python_widgets_dao.get_all_custom_python_widgets_async(
            project_id=project_id,
            search_term=search_term,
            page_number=page_number,
            page_limit=page_limit,
            access_mode=access_mode
        )

    async def get_widget_by_id(self, widget_id: str):
        return await self.custom_python_widgets_dao.get_widget_by_id(widget_id)

    async def delete_custom_python_widgets(
        self, widget_id: str, user_id: str, soft_delete=True
    ):
        if not soft_delete:
            raise NotImplementedError(f"Hard delete for widgets is not implemented yet")
        widget = await self.get_widget_by_id(widget_id)
        widget.last_modified_by_id = user_id
        widget.last_modified_at = datetime.now(timezone.utc)
        widget.access_mode = AccessMode.INTERNAL
        return await self.custom_python_widgets_dao.update_cpw(cpw_id=widget_id,cpw_dump=widget)

    def get_widget_by_id_sync(self, widget_id: str):
        return self.custom_python_widgets_dao.get_widget_by_id_sync(widget_id)

    async def update_cpw_async(
        self, user_id: str, cpw_id: str, cpw_dump: CustomPythonWidget
    ) -> bool:
        logger.info("inside update cpw.")

        # find the connector using cpw_id
        existing_cpw = self.get_widget_by_id(widget_id=cpw_id)
        logger.info("Found requested cpw.")

        if not existing_cpw:
            logger.exception("CPW not found.")
            raise ValueError("CPW not found")

        cpw_dump.last_modified_by_id = user_id
        cpw_dump.last_modified_at = datetime.now(timezone.utc)

        update_flag = await self.custom_python_widgets_dao.update_cpw(cpw_id, cpw_dump)
        logger.info(f"Updated the CPW with flag {update_flag}")

        return update_flag
