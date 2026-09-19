import logging
import traceback
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

from app.actions import Actions
from app.api.rbac.end_points_v1_access_control import CheckNameRoute

# from app.services.AI.mobo.service import MOBOService
from app.core.db.db_utils import get_db_async
from app.core.services.data_transformation.tabular.schemas import (
    AppendMismatchCheckResponse,
    ObjectIdAsStr,
)
from app.core.services.data_transformation.tabular.service import AppendHelper
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer, decodeJWT
from app.services.admin.authentication.service import AuthenticationService
from app.services.AI.mobo.schemas import CreateFolderResponse
from app.services.data.assets.custom_python_widget_recipes.service import (
    CustomPythonWidgetRecipeService,
)
from app.services.data.assets.custom_python_widgets.service import (
    CustomPythonWidgetService,
)
from app.services.workflows.designer.schemas import (
    CreateWorkflowResponse,
    GetAllWorkflowsResponse,
    UpdateWorkflowResponse,
    Workflow,
)
from app.services.workflows.designer.service import WorkflowDesignerService
from app.services.workflows.designer.widget_rules import *
from app.services.workflows.scheduling.service import ScheduleService

logger = logging.getLogger(__package__)
workflow_router = APIRouter(
    tags=["Workflows", "WF Designer"], route_class=CheckNameRoute
)


class WorkflowDesignerRouter:

    def __init__(self):
        pass

    @workflow_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/workflow",
        response_model=CreateWorkflowResponse,
        status_code=status.HTTP_201_CREATED,
        openapi_extra={"actions":Actions.Create_workflow.value}
    )
    async def create_workflow(
        siteId: str,
        projectId: str,
        workflow: Workflow,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> CreateWorkflowResponse:

        try:
            logger.info("creating workflow.")
            workflow_service = WorkflowDesignerService(db_async_client=client)

            auth_service = AuthenticationService(db_async_client=client)
            user = await auth_service.get_user_by_token_or_id(token=token)

            workflow.owner_id = user.id
            workflow.owner_name = user.name
            workflow.last_modified_by_id = user.id
            workflow.created_at = datetime.now(timezone.utc)
            workflow.last_modified_at = workflow.created_at
            workflow.site_id = siteId
            workflow.project_id = projectId

            workflow_id = await workflow_service.create_workflow_async(
                workflow=workflow
            )
            logger.info(f"created workflow with workflow id {workflow_id}")

            return CreateWorkflowResponse(workflow_id=workflow_id)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "workflow_creation_error", "message": str(e)},
            )

    @workflow_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/workflow/{workflowId}",
        response_model=dict,
        status_code=status.HTTP_200_OK,
    )
    async def get_workflow_by_id(
        siteId: str,
        projectId: str,
        workflowId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> dict:
        try:
            logger.info("getting workflow with workflow id")
            workflow_service = WorkflowDesignerService(db_async_client=client)
            cpw_service = CustomPythonWidgetRecipeService(db_async_client=client)
            logger.info("returning the workflow from workflow service.")
            workflow_dict = await workflow_service.get_workflow_by_id_without_schema_check_async(
                workflow_id=workflowId
            )

            # check if workflow has older versions of cpw
            cpw_module_ids = {widget["config"]["module_id"]: widget["urn"] for widget in workflow_dict['widgets'] if widget["type"] == "CUSTOM_CODE"}                        
            recipe_module_ids = [ recipe.module_id for recipe in await cpw_service.get_custom_python_widget_recipes_by_module_ids_async(list(cpw_module_ids.keys()),ignore_empty_results=True)]            
            older_version_cpw_urns = [cpw_module_ids[module_id] for module_id in cpw_module_ids if module_id not in recipe_module_ids]
            workflow_dict["older_version_cpw_urns"] = older_version_cpw_urns

            return workflow_dict
        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "while fetching workflows", "message": str(e)},
            )

    @workflow_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/workflow",
        response_model=GetAllWorkflowsResponse,
        status_code=status.HTTP_200_OK,
    )
    async def get_all_workflows(
        siteId: str,
        projectId: str,
        page_limit: int = Query(default=10),
        page_number: int = Query(default=1),
        search_term: Optional[str] = None,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> GetAllWorkflowsResponse:
        try:
            logger.info("getting all the workflows.")
            workflow_service = WorkflowDesignerService(db_async_client=client)
            workflows, count = await workflow_service.get_all_workflows_async(
                projectId=projectId,
                search_term=search_term,
                page_number=page_number,
                page_limit=page_limit,
            )
            logger.info(
                f"retrieved all the workflows from database. Workflows count: {count}"
            )

            return GetAllWorkflowsResponse(
                workflows=workflows,
                workflows_count=count,
                page_number=page_number,
                page_limit=page_limit,
            )

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "while fetching workflows", "message": str(e)},
            )

    @workflow_router.put(
        "/v1/sites/{siteId}/projects/{projectId}/workflow/{workflowId}",
        status_code=status.HTTP_200_OK,
        openapi_extra={"actions":Actions.Update_workflow.value}

        
    )
    async def update_workflow(
        siteId: str,
        projectId: str,
        workflowId: str,
        workflow: Workflow,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> JSONResponse:
        try:
            logger.info("Updating the workflow...")
            workflow_service = WorkflowDesignerService(db_async_client=client)

            user = decodeJWT(token)

            await workflow_service.update_workflow_async(
                user_id=user["user_id"], workflow_id=workflowId, new_workflow=workflow
            )
            logger.info(f"updated the workflow. {UpdateWorkflowResponse(success=True)}")

            return UpdateWorkflowResponse(success=True)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "workflow_update_error", "message": str(e)},
            )

    @workflow_router.delete(
        "/v1/sites/{siteId}/projects/{projectId}/workflow/{workflowId}"
    )
    async def delete_workflow(
        siteId: str,
        projectId: str,
        workflowId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> JSONResponse:
        try:
            logger.info("Deleting workflows...")
            workflow_service = WorkflowDesignerService(db_async_client=client)
            scheduling_service = ScheduleService(db_async_client=client)

            # add delete service schedules
            schedule_records = (
                await scheduling_service.fetch_schedules_by_workflow_id_async(
                    workflow_id=workflowId
                )
            )
            # logger.info(f"schedule records {schedule_records}")
            logger.info(f"schedule records length {len(schedule_records)}")
            if len(schedule_records) > 0:
                for schedule_record in schedule_records:
                    await scheduling_service.delete_schedule(
                        schedule_id=schedule_record.dag_id
                    )

            await workflow_service.delete_workflow_async(workflow_id=workflowId)
            logger.info(
                f"deleted workflow for the given workflow id {workflowId} with status {UpdateWorkflowResponse(success=True)}"
            )
            return UpdateWorkflowResponse(success=True)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "workflow_delete_error", "message": str(e)},
            )

    @workflow_router.get("/v1/widget/{widget_type}/schema")
    async def get_workflow_input_output_schema(widget_type: UIWidgetType) -> WidgetRule:
        try:
            return WorkflowDesignerService.get_widget_schema(widget_type)

        except Exception as e:
            print("Exception occured: ", traceback.print_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "workflow_delete_error", "message": str(e)},
            )

    @staticmethod
    @workflow_router.post("/v1/workflows/widgets/append/get_append_mismatches")
    async def get_append_mismatches(
        dataset_ids_list: List[ObjectIdAsStr],
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> AppendMismatchCheckResponse:
        try:
            append_service_helper = AppendHelper(db_async_client=client)
            return append_service_helper.get_append_mismatches(dataset_ids_list)

        except Exception as e:
            logger.exception(
                "Exception while trying to get mis matches between datasets."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "get_append_mismatches_error", "message": str(e)},
            )


workflow_router_obj = WorkflowDesignerRouter()
