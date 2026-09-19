import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.core.db.db_utils import get_db_async
from app.core.services.jwt_token_utils.jwt_token_utils import decodeJWT
from app.services.impex.export.service import ExportService
from app.services.impex.schemas import WorkflowExportRequest
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/sites/{site_id}/projects/{project_id}",
    tags=["ImpEx", "Export"],
    route_class=CheckNameRoute,
)

@router.post("/sessions/{session_id}/workflow/export/{type}")
async def workflow_exporter(
    site_id: str,
    project_id: str,
    workflow_export_request: WorkflowExportRequest,
    background_tasks: BackgroundTasks,
    #token: str,
    client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
) -> FileResponse:

   # logger.info(token)
   # decoded_token = decodeJWT(token)
   # if not decoded_token or decoded_token["server_role_value"] != 1:
   #     raise HTTPException(status_code=403, detail="Unauthorized access")

    workflow_id = workflow_export_request.workflow_id

    if not workflow_id:
        raise HTTPException(status_code=400, detail="Invalid workflow_id")

    export_service = ExportService(db_async_client=client)
    try:
        logger.info(f"Exporting workflow_id: {workflow_id}")
        export_artifact_path = await export_service.export_workflow_artifact(
            workflow_id, gen_hmac=True
        )
        # Schedule cleanup after response
        background_tasks.add_task(export_service.cleanup)
        logger.info(f"Workflow export initiated for workflow_id: {workflow_id}")
        return FileResponse(
            path=export_artifact_path,
            media_type="application/zip",
            filename=f"workflow_{workflow_id}.zip",
            background=background_tasks,
        )
    except Exception as e:
        logger.exception(f"Error exporting workflow_id {workflow_id}: {e}")
        export_service.cleanup()
        raise HTTPException(status_code=500, detail=str(e))
