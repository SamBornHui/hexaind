import asyncio
from collections import deque, Counter
import copy
from itertools import chain
import json
import logging
import os
from copy import deepcopy
from datetime import datetime, timezone
import shutil
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, ValidationError
from pymongo import MongoClient

from app.config.env_vars import environment, jupyterhub_environment
from app.core.celery.celery_worker import create_celery_app
from app.core.services.action.schemas import (
    Action,
    ActionRunStatus,
    WidgetResultResponse,
)
from app.services.AI.rescale.schemas import StopRescale
from app.services.workflows.actions.action_utils import ActionUtils
from app.services.workflows.actions.service import ActionServiceNew
from app.services.workflows.designer.schemas import Widget, Workflow
from app.services.workflows.designer.service import WorkflowDesignerService
from app.services.workflows.runner.schemas import (
    Run,
    RunActionsConfig,
    RunState,
    RunStatus,
    RunWidgetStatus,
)
from app.services.workflows.runner.service import RunService
from app.services.workflows.sessions.schemas import (
    CreateWorkflowSessionRequest,
    SavedWorkflowsFromSession,
    WorkflowSessionDB,
)
from app.services.workflows.sessions.service import WorkflowSessionService
from app.services.workflows.workflow_designer.schemas import SaveAsWorkflowRequest
from app.services.workflows.workflow_designer.workflow_utils import (
    WorkflowChangeDetector,
)
from app.services.workflows.workflow_utils import WFConfigService

from .dao import InteractiveWorkflowDesginerServiceDao
from .schemas import (
    DuplicateWorkflowRequest,
    SaveWorkflowRequest,
    WorkflowChanges,
    WorkflowSessionRunStatus,
    WorkflowSessionWidgetResults,
)


logger = logging.getLogger(__package__)


class InteractiveWorkflowDesginerService:

    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:

        self.interactive_workflow_desginer_dao = InteractiveWorkflowDesginerServiceDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

        self.session_service = WorkflowSessionService(db_async_client=db_async_client)

        self.run_service = RunService(db_async_client=db_async_client)

        self.action_service = ActionServiceNew(db_async_client=db_async_client)

        self.workflow_designer_service = WorkflowDesignerService(
            db_async_client=db_async_client
        )

        self.config_service = WFConfigService()

        self.action_utils = ActionUtils()

    def is_valid_workflow(
        self, workflow_req: SaveWorkflowRequest
    ) -> Tuple[bool, List[dict]]:

        # 1. check if all widgets are valid
        invalid_widgets = []
        for widget_data in workflow_req.widgets:
            try:
                Widget.model_validate(widget_data)
            except ValidationError as e:
                invalid_widgets.append(
                    {"urn": widget_data.get("urn", "unknown"), "errors": e.errors()}
                )

        if invalid_widgets:
            return (False, invalid_widgets)
        else:
            return (True, [])

        # 2. check if all the connections are valid in input and output
        pass

    async def save_invalid_workflow_in_session(
        self,
        session_id: str,
        save_workflow_obj: SaveWorkflowRequest,
        last_updated_by: Optional[str] = None,
    ):

        logger.info("Inside save_invalid_workflow_in_session function")
        session_record: WorkflowSessionDB = (
            await self.session_service.get_workflow_session_async(session_id=session_id)
        )
        prev_workflow: Workflow = (
            await self.workflow_designer_service.get_workflow_by_id_async(
                workflow_id=session_record.workflow_id
            )
        )
        current_workflow = copy.deepcopy(prev_workflow)
        current_workflow.is_valid = False
        current_workflow.validation_errors = save_workflow_obj.validation_errors
        current_workflow.partial_widgets = save_workflow_obj.invalid_widgets
        current_workflow.widgets = save_workflow_obj.valid_widgets
        current_workflow.start = save_workflow_obj.start
        current_workflow.end = save_workflow_obj.end
        current_workflow.last_modified_by_id = (
            last_updated_by if last_updated_by else save_workflow_obj.user_id
        )
        current_workflow.last_modified_at = datetime.now(timezone.utc)
        current_workflow.client_tags = save_workflow_obj.client_tags
        # Persist the workflow
        return await self.workflow_designer_service.update_workflow_async(
            user_id=save_workflow_obj.user_id,
            workflow_id=session_record.workflow_id,
            new_workflow=current_workflow,
        )

    @staticmethod
    def assign_numbers(graph: Dict[str, List[str]]) -> Dict[str, str]:
        indegrees: Counter[str] = Counter(chain.from_iterable(graph.values()))
        nodes = deque(node for node in graph if indegrees[node] == 0)
        level = 0
        mapping: Dict[str, str] = {}
        while nodes:
            level += 1
            for sibling in range(1, len(nodes) + 1):
                node = nodes.popleft()
                mapping[node] = f"{level}.{sibling}"
                nodes.extend(
                    neighbour
                    for neighbour in graph.get(node, [])
                    if neighbour not in mapping
                )
        return mapping

    # def _assign_numbers(self, graph):
    #     all_nodes = set(graph.keys())
    #     child_nodes = set(node for children in graph.values() for node in children)
    #     root = (all_nodes - child_nodes).pop()  # Root is the one that's not a child

    #     numbering = {}
    #     visited = set()
    #     visiting = set()  # Track nodes being visited

    #     def dfs(node, level, sibling_index=1):
    #         if node in visiting:
    #             # Cycle detected
    #             return False
    #         if node in visited:
    #             # Skip already processed nodes
    #             return True
            
    #         visiting.add(node)
    #         if level == 1:
    #             numbering[node] = str(level)
    #         else:
    #             numbering[node] = f"{level}.{sibling_index}"
            
    #         for i, child in enumerate(graph[node], start=1):
    #             if not dfs(child, level + 1, i):
    #                 return False
            
    #         visiting.remove(node)
    #         visited.add(node)
    #         return True

    #     # Start from the root with level 1
    #     if not dfs(root, 1):
    #         return None

    #     return numbering
    
    def update_widgets_with_number(self, widgets: List[Widget], urn_to_number: Dict[str, str]):
    # Iterate over each widget and update its client_tags with widget_number
        for widget in widgets:
            if type(widget) is Widget and widget.urn in urn_to_number:
                widget.client_tags['widget_number'] = str(urn_to_number[widget.urn])

            elif type(widget) is dict and widget['urn'] in urn_to_number:
                widget['client_tags']['widget_number'] = str(urn_to_number[widget['urn']])

        return widgets

    async def save_workflow_in_session(
        self,
        session_id: str,
        save_workflow_obj: SaveWorkflowRequest,
        last_updated_by: Optional[str] = None,
    ) -> bool:
        logger.info("Inside save_workflow_in_session function")
        session_record: WorkflowSessionDB = (
            await self.session_service.get_workflow_session_async(session_id=session_id)
        )

        run_record: Run = await self.run_service.get_run_by_id_async(
            run_id=session_record.run_id
        )

        if run_record.run_status == RunStatus.RUNNING:
            raise Exception(
                "Widgets execution is in-progress, can not modify workflow at this moment."
            )

        prev_workflow: Workflow = (
            await self.workflow_designer_service.get_workflow_by_id_async(
                workflow_id=session_record.workflow_id
            )
        )

        current_workflow = copy.deepcopy(prev_workflow)
        current_workflow.is_valid = len(save_workflow_obj.invalid_widgets) == 0
        current_workflow.validation_errors = save_workflow_obj.validation_errors
        current_workflow.partial_widgets = save_workflow_obj.invalid_widgets
        current_workflow.widgets = save_workflow_obj.valid_widgets
        current_workflow.start = save_workflow_obj.start
        current_workflow.end = save_workflow_obj.end
        current_workflow.last_modified_by_id = (
            last_updated_by if last_updated_by else save_workflow_obj.user_id
        )
        current_workflow.last_modified_at = datetime.now(timezone.utc)
        current_workflow.client_tags = save_workflow_obj.client_tags

        if (
            current_workflow.end == [] and len(current_workflow.start) > 0
        ):  # If user didn't give end for a workflow, we are finding the end(leaf-nodes) using dfs algoritm.
            widgets = current_workflow.widgets
            graph = self.action_service.get_graph_from_widgets(widgets=widgets)
            current_workflow.end = self.action_service.find_end_widgets_in_a_workflow(
                graph=graph, start=save_workflow_obj.start[0]
            )

        workflow_change_detector = WorkflowChangeDetector(
            previous_workflow=prev_workflow.model_dump(),
            current_workflow=current_workflow.model_dump(),
        )
        workflow_changes: WorkflowChanges = workflow_change_detector.detect_changes()

        existing_urn_action_id_map = {
            action.urn: action.action_id for action in run_record.actions
        }

        # Removing all deleted widgets actions
        deleted_action_ids = []
        for widget_urn in workflow_changes.deleted_widgets:
            if widget_urn in existing_urn_action_id_map:  # deleted widgets
                deleted_action_ids.append(existing_urn_action_id_map.get(widget_urn))
                continue

        await asyncio.gather(
            *[
                self.action_service.delete_action_record_by_action_id_async(
                    action_id=action_id, force_delete=True
                )
                for action_id in deleted_action_ids
            ]
        )

        # creating new action records for newly added widgets and at the same time Resetting all affected widgets action records
        actions_list: List[Action] = self.action_utils.get_actions_from_widgets(
            run_id=session_record.run_id, actions=current_workflow.widgets + current_workflow.partial_widgets
        )

        run_actions_list: List[RunActionsConfig] = []
        for action in actions_list:
            action.run_id = session_record.run_id

            if action.action_config.urn in workflow_changes.new_widgets:  # new widgets
                action_id = await self.action_service.create_action_async(action=action)

            elif (
                action.action_config.urn in workflow_changes.affected_widgets
            ):  # affected widgets
                action_id = existing_urn_action_id_map.get(action.action_config.urn)
                await self.action_service.reset_action_record_by_action_id_async(
                    action_id=action_id, new_action_record=action
                )

            else:  # non-affected widgets
                action_id = existing_urn_action_id_map.get(action.action_config.urn)
                await self.action_service.update_action_config_by_action_id_async(
                    action_id=action_id, new_action_config=action.action_config
                )

            run_actions_list.append(
                RunActionsConfig(urn=action.action_config.urn, action_id=action_id)
            )

        # update run with new actions_list

        await self.run_service.update_run_action_config_async(
            run_id=session_record.run_id, run_action_config_list=run_actions_list
        )

        # update the workflow record with new widgets
        wf_graph = self.action_service.get_graph_from_widgets(widgets=current_workflow.widgets + current_workflow.partial_widgets)
        logger.info(f"GRAPH: {wf_graph}")

        # Assign hierarchical numbers
        numbered_graph = self.assign_numbers(wf_graph)
        logger.info(f"NUMBERED GRAPH: {numbered_graph}")

        current_workflow.widgets = self.update_widgets_with_number(widgets=current_workflow.widgets, urn_to_number=numbered_graph)
        #TODO: need to consider partial widgets as well.

        return await self.workflow_designer_service.update_workflow_async(
            user_id=save_workflow_obj.user_id,
            workflow_id=session_record.workflow_id,
            new_workflow=current_workflow,
        )

    async def duplicate_version_workflow(
        self, session_id: str, duplicate_workflow_obj: DuplicateWorkflowRequest
    ):
        logger.info("Inside duplicate_master_workflow function")
        logger.info(f"session to be saveas:{session_id}")
        original_session = await self.session_service.get_workflow_session_async(
            session_id=session_id
        )
        if await self.session_service.check_existing_published_workflow_in_session_async(
            session_id=session_id,
            workflow_name=duplicate_workflow_obj.name,
            workflow_version_tag=duplicate_workflow_obj.version_tag,
        ):
            raise Exception("Workflow already present with same or version tag")

        workflow_obj: Workflow = (
            await self.workflow_designer_service.get_workflow_by_id_async(
                workflow_id=duplicate_workflow_obj.workflow_id
            )
        )

        # check if workflow is valid or not
        if not workflow_obj.is_valid:
            logger.error(
                "Unable to publish the workflow at this moment. Invalid Workflow Please try again."
            )
            raise Exception(
                "Unable to publish the workflow at this moment. Invalid Workflow Please try again."
            )

        workflow_obj.workflow_version = duplicate_workflow_obj.version_tag
        workflow_obj.name = duplicate_workflow_obj.name
        workflow_obj.description = duplicate_workflow_obj.description
        workflow_obj.owner_id = duplicate_workflow_obj.user_id
        workflow_obj.owner_name = duplicate_workflow_obj.user_name
        workflow_obj.last_modified_at = datetime.now(timezone.utc)
        workflow_obj.last_modified_by_id = duplicate_workflow_obj.user_id
        workflow_obj.created_at = workflow_obj.last_modified_at
        workflow_obj.interactive_mode = False
        workflow_obj.widgets = self.config_service.update_widget_config_paths(widgets=workflow_obj.widgets)

        published_workflow_id = (
            await self.workflow_designer_service.create_workflow_async(
                workflow=workflow_obj
            )
        )

        published_workflow_bj = SavedWorkflowsFromSession(
            workflow_id=published_workflow_id,
            workflow_version=workflow_obj.workflow_version,
            name=workflow_obj.name,
            description=workflow_obj.description,
        )

        if await self.session_service.update_session_record_with_latest_published_workflow(
            session_id=session_id, saveas_workflow=published_workflow_bj
        ):
            return {"new_workflow_id": published_workflow_id}

        else:
            logger.error(
                "Unable to publish the workflow at this moment. Please try again later...."
            )
            raise Exception(
                "Unable to publish the workflow at this moment. Please try again later...."
            )

    async def duplicate_master_workflow(
        self,
        duplicate_workflow_request_obj: DuplicateWorkflowRequest,
        site_id: str,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        Duplicates a master workflow based on the provided request object.

        Args:
            duplicate_workflow_request_obj (DuplicateWorkflowRequest): The request object containing original workflow details.
            site_id (str): The site ID.
            project_id (str): The project ID.

        Returns:
            Dict[str, Any]: A dictionary containing the status and IDs of the new workflow.
        """
        new_session_id = None
        try:
            logger.info("Starting master workflow duplication process")

            # Create new session
            new_session_id = await self.session_service.create_workflow_session_async(
                user_id=duplicate_workflow_request_obj.user_id,
                user_name=duplicate_workflow_request_obj.user_name,
                site_id=site_id,
                project_id=project_id,
                create_session_req_obj=CreateWorkflowSessionRequest(
                    name=duplicate_workflow_request_obj.name,
                    description=duplicate_workflow_request_obj.description,
                ),
            )

            # Get original workflow from duplicate workflow request
            original_workflow = await self.workflow_designer_service.get_workflow_by_id_without_schema_check_async(
                workflow_id=duplicate_workflow_request_obj.workflow_id
            )
            
            logger.debug(f"Original workflow retrieved with ID: {duplicate_workflow_request_obj.workflow_id}")

            new_workflow, urn_mappings = InteractiveWorkflowDesginerService.replace_urns_in_workflow(workflow_data=original_workflow, return_mappings=True)
            
            logger.debug(f"Created new workflow object and replaced URNs")
            
            # urn_mappings is a dictionary with old URNs as keys and new URNs as values
            # swap the keys and values to get a dictionary with new URNs as keys and old URNs as values
            # this will be used to update the widget config paths
            urn_mappings = {v: k for k, v in urn_mappings.items()}
            new_workflow["widgets"] = self.config_service.update_widget_config_paths(widgets=new_workflow["widgets"], urn_mappings=urn_mappings)

            # Save new workflow
            save_object = {
                "widgets": new_workflow["widgets"],
                "start": new_workflow["start"],
                "end": new_workflow["end"],
                "client_tags": new_workflow["client_tags"],
                "user_id": duplicate_workflow_request_obj.user_id,
                "user_name": duplicate_workflow_request_obj.user_name
            }

            return {
                "save_object": save_object,
                "new_session_id": new_session_id
            }

        except Exception as e:
            logger.error(f"Error duplicating workflow: {e}")
            if new_session_id:
                await self.session_service.delete_workflow_session_async(session_id=new_session_id)
                logger.error(f"Deleting new session with session_id: {new_session_id}, due to error.")
                
            raise e

    async def save_workflow_as_template(
        self,
        session_id: str,
        project_id: str,
        templateObj: DuplicateWorkflowRequest,
        file: UploadFile,
    ):
        logger.info("Inside save_workflow_as_template function")
        logger.info(f"session to be saved as template:{session_id}")
        original_session = await self.session_service.get_workflow_session_async(
            session_id=session_id
        )

        new_workflow_id = (
            await self.interactive_workflow_desginer_dao.duplicate_workflow(
                templateObj.workflow_id, templateObj
            )
        )
        new_run_id = await self.interactive_workflow_desginer_dao.duplicate_run(
            original_session.run_id, new_workflow_id, templateObj
        )
        new_actions_id = await self.interactive_workflow_desginer_dao.duplicate_actions(
            original_session.run_id, new_run_id, new_workflow_id, templateObj
        )
        current_timestamp = datetime.now(timezone.utc)
        # Create the new workflow session object
        new_session = original_session.copy()

        new_session.name = templateObj.name
        new_session.description = templateObj.description
        new_session.created_at = current_timestamp
        new_session.last_modified_at = current_timestamp
        new_session.run_id = new_run_id
        new_session.workflow_id = new_workflow_id
        new_session.saved_workflows = []
        new_session.owner_id = templateObj.user_id
        new_session.owner_name = templateObj.user_name
        new_session.is_template = True

        upload_folder = environment.datasets_folder / f"p_{project_id}"
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        upload_folder_workflow = upload_folder / f"w_{new_workflow_id}"
        if not os.path.exists(upload_folder_workflow):
            os.makedirs(upload_folder_workflow)

        file_location = os.path.join(upload_folder_workflow, file.filename)
        with open(file_location, "wb") as f:
            f.write(file.file.read())

        new_session.template_screenshot = file_location

        # Insert the new session
        new_session_id = (
            await self.interactive_workflow_desginer_dao.create_workflow_session(
                new_session
            )
        )

        return {
            "status": True,
            "msg": "Workflow saved as template successfully",
            "new_session_id": new_session_id,
            "new_run_id": new_run_id,
            "new_workflow_id": new_workflow_id,
        }

    async def saveas_workflow_in_session(
        self, session_id: str, save_workflow_obj: SaveAsWorkflowRequest
    ):
        logger.info("Inside saveas_workflow_in_session function")
        logger.info(f"session to be saveas:{session_id}")
        session_record = await self.session_service.get_workflow_session_async(
            session_id=session_id
        )

        # verify if we already have the same workflow published (with name and version tag)
        if await self.session_service.check_existing_published_workflow_in_session_async(
            session_id=session_id,
            workflow_name=save_workflow_obj.name,
            workflow_version_tag=save_workflow_obj.version_tag,
        ):
            raise Exception("Workflow already present with same or version tag")

        workflow_obj: Workflow = (
            await self.workflow_designer_service.get_workflow_by_id_async(
                workflow_id=session_record.workflow_id
            )
        )

        # check if workflow is valid or not
        if not workflow_obj.is_valid:
            logger.error(
                "Unable to publish the workflow at this moment. Invalid Workflow Please try again."
            )
            raise Exception(
                "Unable to publish the workflow at this moment. Invalid Workflow Please try again."
            )

        workflow_obj.workflow_version = save_workflow_obj.version_tag
        workflow_obj.name = save_workflow_obj.name
        workflow_obj.description = save_workflow_obj.description
        workflow_obj.owner_id = save_workflow_obj.user_id
        workflow_obj.owner_name = save_workflow_obj.user_name
        workflow_obj.last_modified_at = datetime.now(timezone.utc)
        workflow_obj.last_modified_by_id = save_workflow_obj.user_id
        workflow_obj.created_at = workflow_obj.last_modified_at
        workflow_obj.interactive_mode = False
        workflow_obj.widgets = self.config_service.update_widget_config_paths(widgets=workflow_obj.widgets)
        workflow_obj.is_master = False

        published_workflow_id = (
            await self.workflow_designer_service.create_workflow_async(
                workflow=workflow_obj
            )
        )

        # cloning jupyter data
        workflow_dir = jupyterhub_environment.workflow_dir(workflow_obj.project_id, workflow_obj.id or "")
        master_workflow_dir = workflow_dir / "master"
        published_workflow_dir = workflow_dir / "published" / workflow_obj.workflow_version / "master clone"
        if master_workflow_dir.exists():
            # TODO make it read only
            shutil.copytree(master_workflow_dir, published_workflow_dir)

        published_workflow_bj = SavedWorkflowsFromSession(
            workflow_id=published_workflow_id,
            workflow_version=workflow_obj.workflow_version,
            name=workflow_obj.name,
            description=workflow_obj.description,
        )

        if await self.session_service.update_session_record_with_latest_published_workflow(
            session_id=session_id, saveas_workflow=published_workflow_bj
        ):
            return published_workflow_id
        else:
            logger.error(
                "Unable to publish the workflow at this moment. Please try again later...."
            )
            raise Exception(
                "Unable to publish the workflow at this moment. Please try again later...."
            )

    def trigger_workflow_run(self, start_action_id: str):
        # inserting the start task in queue
        celeryApp = create_celery_app("run_workflow_session")
        celeryApp.send_task(
            "start_action",
            kwargs={"action_id": start_action_id},
            queue="start_end",
            routing_key="start",
        )
    
    def teriminate_tasks_from_execution(self, task_ids: list[str]):
        if task_ids:
            celeryApp = create_celery_app("stop_workflow_session")
            [celeryApp.control.revoke(task_id, terminate=True, signal="SIGTERM") for task_id in task_ids]
        return

    async def run_workflow_in_session(self, session_id: str, clear_outputs: bool):
        logger.info("Inside run_workflow_in_session function")
        logger.info(f"Run workflow in session:{session_id}")
        session_record = await self.session_service.get_workflow_session_async(
            session_id=session_id
        )

        # check if workflow is valid or not
        workflow: Workflow = (
            await self.workflow_designer_service.get_workflow_by_id_async(
                workflow_id=session_record.workflow_id
            )
        )
        if not workflow.is_valid:
            logger.error(
                "Unable to Run the workflow at this moment. Invalid Workflow Please try again."
            )
            raise Exception(
                "Unable to Run the workflow at this moment. Invalid Workflow Please try again."
            )

        run_record: Run = await self.run_service.get_run_by_id_async(
            run_id=session_record.run_id
        )

        if run_record.run_status == RunStatus.RUNNING:
            logger.error(
                "Widgets execution is in-progress, can not run workflow at this moment."
            )
            raise Exception(
                "Widgets execution is in-progress, can not run workflow at this moment."
            )

        # clear all the widgets which are not success.
        for action in run_record.actions:

            action_record = await self.action_service.get_action_by_action_id_async(
                action_id=action.action_id
            )

            if action_record.status == ActionRunStatus.IDLE:
                continue

            if action_record.status in [
                ActionRunStatus.RUNNING,
                ActionRunStatus.SCHEDULED,
            ]:
                logger.error(
                    "Widget execution is in-progress, can not run workflow at this moment."
                )
                raise Exception(
                    "Widget execution is in-progress, can not run workflow at this moment."
                )

            elif action_record.status != ActionRunStatus.SUCCEEDED:
                await self.action_service.reset_action_record_by_action_id_async(
                    action_id=action.action_id
                )

        if clear_outputs:
            # clear all the action result records
            await asyncio.gather(
                *[
                    self.action_service.reset_action_record_by_action_id_async(
                        action_id=action.action_id, force_delete=True
                    )
                    for action in run_record.actions
                ]
            )

        new_schedule_to_delete_widgets = []
        running_action_records_celery_task_ids = []
        for action in run_record.schedule_to_delete_widgets:
            action_record = await self.action_service.get_action_by_action_id_async(
                action_id=action.action_id
            )
            if action_record.status == ActionRunStatus.STOPPED:
                await self.action_service.delete_action_record_by_action_id_async(
                    action_id=action.action_id, force_delete=True
                )
            else:
                new_schedule_to_delete_widgets.append(
                    RunActionsConfig(urn=action.urn, action_id=action.action_id)
                )

        run_record.run_status = RunStatus.RUNNING
        run_record.recent_run_created_at = datetime.now(timezone.utc)
        run_record.run_state = RunState.START
        run_record.is_single_widget_run = False
        run_record.schedule_to_delete_widgets = new_schedule_to_delete_widgets

        await self.run_service.update_run_async(
            run_id=session_record.run_id, run_record=run_record
        )

        # get all the action ids from the start widget urns
        workflow: Workflow = (
            await self.workflow_designer_service.get_workflow_by_id_async(
                workflow_id=session_record.workflow_id
            )
        )

        start_action_urns = []
        if isinstance(workflow.start, list):
            start_action_urns.extend(workflow.start)
        elif isinstance(workflow.start, str):
            start_action_urns.append(workflow.start)

        start_action_ids = []
        for action_urn in start_action_urns:
            for action in run_record.actions:
                if action.urn == action_urn:
                    start_action_ids.append(action.action_id)
                    break

        for start_action_id in start_action_ids:
            self.trigger_workflow_run(start_action_id=start_action_id)

    async def stop_workflow_in_session(self, session_id: str, stop_rescale_info: StopRescale=None) -> bool:
        logger.info("Inside stop_workflow_in_session function")
        
        if stop_rescale_info and stop_rescale_info.run_id:
            run_id = stop_rescale_info.run_id
        else:    
            session_record = await self.session_service.get_workflow_session_async(session_id=session_id)
            stop_rescale_info.run_id = run_id = session_record.run_id
            
        if stop_rescale_info and stop_rescale_info.stop_pending:
            logger.info("Stopping the rescale jobs")
            rescale_stop_update = {
                "stop_pending": stop_rescale_info.stop_pending,
                "stop_all": stop_rescale_info.stop_all
            }
            await self.interactive_workflow_desginer_dao.update_rescale_running_info_async(wf_run_id=stop_rescale_info.run_id, rescale_running_info=rescale_stop_update)
            logger.info("Updates rescale jobs info in db")
            if not stop_rescale_info.stop_all:
                logger.info("in stopping the rescale pending job")
                return
            
            logger.info("In stopping all the rescale jobs") 
            
    
        run_record: Run = await self.run_service.get_run_by_id_async(run_id=run_id)
        if run_record.run_status == RunStatus.IDLE:
            return

        running_action_ids = []
        running_action_records_celery_task_ids = []
        for action in run_record.actions:
            action_record: Action = (
                await self.action_service.get_action_by_action_id_async(
                    action_id=action.action_id
                )
            )
            if action_record.status == ActionRunStatus.RUNNING:
                running_action_ids.append((action.action_id, action_record))
                running_action_records_celery_task_ids.append(action_record.celery_task_id)

        new_action_ids = []
        scheduled_to_delete_widgets = []
        for action_id, action_record in running_action_ids:

            # make a copy of all the running actions.
            new_action_record = copy.deepcopy(action_record)
            # new_action_record.action_config.urn = f'{new_action_record.action_config.urn}_{time.time()}'
            new_action_record.sub_action_ids = []
            new_action_record.result_ids = []
            new_action_record.custom_run_state = None
            new_action_record.status = ActionRunStatus.IDLE
            new_action_record.celery_task_id = None
            new_action_id = await self.action_service.create_action_async(
                action=new_action_record
            )
            new_action_ids.append((new_action_record.action_config.urn, new_action_id))

            # update action ids.
            await self.action_service.update_action_record_delete_on_complete_async(
                action_id=action_id, delete_on_complete=True
            )

            scheduled_to_delete_widgets.append(
                RunActionsConfig(
                    urn=action_record.action_config.urn, action_id=action_id
                )
            )

            # adding sub actions also to delete schedule
            if action_record.sub_action_ids:
                scheduled_to_delete_widgets.extend(
                    [
                        RunActionsConfig(
                            urn=action_record.action_config.urn, action_id=sub_action_id
                        )
                        for sub_action_id in action_record.sub_action_ids
                    ]
                )
        
        # sending stop signals to the workers
        self.teriminate_tasks_from_execution(task_ids=running_action_records_celery_task_ids)

        # remove them from action record and add the copied action ids to run record.
        run_actions_list: List[RunActionsConfig] = []
        for action in run_record.actions:
            if action.action_id not in [i[0] for i in running_action_ids]:
                run_actions_list.append(
                    RunActionsConfig(urn=action.urn, action_id=action.action_id)
                )

        for new_action_urn, new_action_id in new_action_ids:
            run_actions_list.append(
                RunActionsConfig(urn=new_action_urn, action_id=new_action_id)
            )

        # reset run record
        run_record.schedule_to_delete_widgets.extend(scheduled_to_delete_widgets)
        run_record.actions = run_actions_list
        run_record.run_state = RunState.START
        run_record.run_status = RunStatus.IDLE

        await self.run_service.update_run_async(
            run_id=run_id, run_record=run_record
        )

    async def run_widget_workflow_in_session(self, session_id: str, widget_urn: str):
        logger.info("Inside run_widget_workflow_in_session function")
        # check if widget dependencies are satisfied or nor
        session_record = await self.session_service.get_workflow_session_async(
            session_id=session_id
        )

        workflow_obj: Workflow = (
            await self.workflow_designer_service.get_workflow_by_id_async(
                workflow_id=session_record.workflow_id
            )
        )
        if not workflow_obj.is_valid:
            logger.error(
                "Unable to Run the widget at this moment. Invalid Workflow Please try again."
            )
            raise Exception(
                "Unable to Run the widget at this moment. Invalid Workflow Please try again."
            )

        run_record: Run = await self.run_service.get_run_by_id_async(
            run_id=session_record.run_id
        )

        if run_record.run_status == RunStatus.RUNNING:
            logger.error(
                "Widgets execution is in-progress, can not run widget at this moment."
            )
            raise Exception(
                "Widgets execution is in-progress, can not run widget at this moment."
            )

        action_id = None
        for action in run_record.actions:
            if action.urn == widget_urn:
                action_id = action.action_id
                break

        if not action_id:
            logger.error("action id not found")
            Exception("action id not found")

        await self.action_service.reset_action_record_by_action_id_async(
            action_id=action_id
        )

        action_record = await self.action_service.get_action_by_action_id_async(
            action_id=action_id
        )

        prev_action_ids = []
        for prev_action_urn in action_record.depends_on:
            for action in run_record.actions:
                if action.urn == prev_action_urn:
                    prev_action_ids.append(action.action_id)
                    break

        for prev_action_id in prev_action_ids:
            action_record = await self.action_service.get_action_by_action_id_async(
                action_id=prev_action_id
            )
            if action_record.status != ActionRunStatus.SUCCEEDED:
                logger.error("cannot schedule widget. dependencies not satisfied")
                raise Exception("cannot schedule widget. dependencies not satisfied")

        # Now change the run status to "RUNNING" and set True for is_single_widget_run
        run_record.run_status = RunStatus.RUNNING
        run_record.run_state = RunState.START
        run_record.is_single_widget_run = True
        await self.run_service.update_run_async(
            run_id=session_record.run_id, run_record=run_record
        )

        self.trigger_workflow_run(start_action_id=action_id)

    async def get_workflow_run_status_in_session(
        self, session_id: str
    ) -> WorkflowSessionRunStatus:
        logger.info("Inside get_workflow_run_status_in_session function")

        session_record = await self.session_service.get_workflow_session_async(
            session_id=session_id
        )

        run_record: Run = await self.run_service.get_run_by_id_async(
            run_id=session_record.run_id
        )
        
        # get action id's from run record
        action_ids = InteractiveWorkflowDesginerService.get_action_ids_from_run_record(run_record)
        
        # get all the action records from action id's
        actions: List[Action] = await self.action_service.get_actions_from_list_of_action_ids_async(action_ids)
        
        widgets_status = [
            RunWidgetStatus(urn=action.action_config.urn, status=action.status)
            for action in actions
        ]

        workflow = await self.workflow_designer_service.get_workflow_by_id_async(
            workflow_id=session_record.workflow_id
        )

        return WorkflowSessionRunStatus(
            workflow=copy.deepcopy(workflow),
            widgets_status=widgets_status,
            run_status=run_record.run_status,
            is_single_widget_run = run_record.is_single_widget_run
        )

    async def get_widget_run_results_workflow_in_session(
        self, session_id: str, widget_urn: str,
        output_name: Optional[str] = None
    ) -> List[WidgetResultResponse]:

        session_record = await self.session_service.get_workflow_session_async(
            session_id=session_id
        )

        widget_responses = (
            await self.action_service.get_action_result_by_run_id_and_urn_async(
                run_id=session_record.run_id, urn=widget_urn, output_name=output_name
            )
        )

        return widget_responses
        
    @staticmethod
    def get_action_ids_from_run_record(run_record: Run) -> List[str]:
        """Get action ids from run record

        Args:
            run_record (Run): The run record object.

        Returns:
            List[str]: A list of action ids.
        """
        
        return [action.action_id for action in run_record.actions]

    @staticmethod    
    def replace_urns_in_workflow(workflow_data: Any, return_mappings=False) -> Any:
        """Replace URNs in workflow data

        Args:
            workflow_data (Any): json data containing workflow information

        Returns:
            Any: json data with replaced URNs
        """
        urn_mapping = {}
    
        # Traverse through widgets to collect and replace URNs
        for widget in workflow_data.get("widgets", []):
            old_urn = widget.get("urn")
            if old_urn:
                # Generate new unique URN
                new_urn = str(uuid4())
                urn_mapping[old_urn] = new_urn
    
        # Replace URNs across the entire JSON data
        workflow_str = json.dumps(workflow_data, default=str)
        for old_urn, new_urn in urn_mapping.items():
            workflow_str = workflow_str.replace(old_urn, new_urn)
            
        if return_mappings:
            return json.loads(workflow_str), urn_mapping
    
        return json.loads(workflow_str)
    