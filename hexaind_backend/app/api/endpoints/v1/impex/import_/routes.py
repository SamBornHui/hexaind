import asyncio
import logging

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import JSONResponse
from app.services.impex.schemas import WorkflowImportRequest
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.endpoints.v1.workflows.workflow_designer.routes import (
    InteractiveWorkflowDesignerRouter,
)
from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.core.db.db_utils import get_db_async
from app.core.services.jwt_token_utils.jwt_token_utils import decodeJWT
from app.services.impex.import_.service import ImportService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/sites/{site_id}/projects/{project_id}/import",
    tags=["ImpEx", "Import"],
    route_class=CheckNameRoute,
)


@router.post("/workflow", response_class=JSONResponse)
async def workflow_importer(
    site_id: str,
    project_id: str,
    zip_file: UploadFile = File(..., description="Zip file to import"),
    workflow_name: str = Form(..., description="Name of the workflow"),
    workflow_description: str = Form(..., description="Description of the workflow"),
    user_name: str = Form(..., description="Name of the user"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    token: str = Form(...),
    client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
):
    logger.info("Received workflow import request")
    import_service = ImportService(db_async_client=client)

    try:
        decoded_token = decodeJWT(token)
        if not decoded_token or decoded_token.get("server_role_value") != 1:
            raise HTTPException(status_code=403, detail="Unauthorized access")

        # Process the uploaded ZIP file
        await asyncio.to_thread(import_service.process_zip_file, zip_file)

        # Prepare import request data
        workflow_import_request = WorkflowImportRequest(
            user_id=decoded_token["user_id"],
            user_name=user_name,
            workflow_name=workflow_name,
            workflow_description=workflow_description,
        )

        # Import workflow artifact
        data = await import_service.import_workflow_artifact(
            site_id=site_id,
            project_id=project_id,
            import_request=workflow_import_request,
        )

        # Save the imported data
        await InteractiveWorkflowDesignerRouter.save_workflow_in_session(
            siteId=site_id,
            projectId=project_id,
            sessionId=data["new_session_id"],
            saveObj=data["save_object"],
            user_id=workflow_import_request.user_id,
            client=client,
        )

        logger.info(
            f"Workflow imported successfully, session_id: {data['new_session_id']}"
        )

        # Schedule cleanup after response
        background_tasks.add_task(import_service.cleanup)
        return JSONResponse(content={"session_id": data["new_session_id"]})
    except Exception as e:
        logger.exception(f"Error importing workflow: {e}")
        import_service.cleanup()
        raise HTTPException(status_code=500, detail=str(e))
