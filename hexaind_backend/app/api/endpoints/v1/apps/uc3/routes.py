import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import List

from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.core.db.db_utils import close_db_sync, get_db_async, get_db_sync
from app.services.apps.uc3.service import UC3Service

logger = logging.getLogger(__name__)

uc3_router = APIRouter(
    prefix="/v1/sites/{site_id}/projects/{project_id}/uc3",
    tags=["UC3"],
    route_class=CheckNameRoute,
)


@uc3_router.get("/get_workflow_names", response_model=dict)
async def get_workflow_names(
    site_id: str,
    project_id: str,
    service: UC3Service = Depends(),
    client: AsyncIOMotorClient = Depends(get_db_async),
):
    """Fetch workflow names."""
    logger.info(
        f"UC3_Dashboard: Fetching workflow names for site {site_id} and project {project_id}"
    )
    try:
        result = await service.get_workflow_names(
            site_id=site_id, project_id=project_id, client=client
        )
        logger.info(f"Fetched workflow names for site {site_id} and project {project_id}")
        return result
    except Exception as e:
        logger.exception("Failed to fetch workflow names.", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching workflow names.",
        ) from e


@uc3_router.get("/get_runs_for_workflow", response_model=dict)
async def get_runs_for_workflow(
    site_id: str,
    project_id: str,
    workflow_id: str = Query(..., description="Workflow ID"),
    service: UC3Service = Depends(),
    client: AsyncIOMotorClient = Depends(get_db_async),
):
    """Fetch runs of a workflow."""
    logger.info(
        f"UC3_Dashboard: Fetching runs for workflow {workflow_id} in site {site_id}, project {project_id}"
    )
    try:
        result = await service.get_runs_for_workflow(
            site_id=site_id,
            project_id=project_id,
            workflow_id=workflow_id,
            client=client,
        )
        logger.info(
            f"Fetched runs for workflow {workflow_id} in site {site_id}, project {project_id}"
        )
        return result
    except Exception as e:
        logger.exception(f"Failed to fetch runs for workflow: {workflow_id}", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching runs for workflow.",
        ) from e


@uc3_router.get("/get_dashboard_metadata", response_model=dict)
async def get_dashboard_metadata(
    site_id: str,
    project_id: str,
    run_id: str = Query(..., description="Run ID"),
    service: UC3Service = Depends()
):
    """Fetch dashboard metadata for a run."""
    logger.info(f"UC3_Dashboard: Fetching dashboard metadata for run {run_id}")
    try:
        result = await service.get_dashboard_metadata(
            run_id=run_id
        )
        logger.info(f"Fetched dashboard metadata for run {run_id}")
        return result
    except HTTPException as e:
        logger.warning(f"Dashboard metadata not found for run: {run_id}", exc_info=e)
        raise e
    except Exception as e:
        logger.exception(
            f"Failed to fetch dashboard metadata for run: {run_id}", exc_info=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching dashboard metadata.",
        ) from e


@uc3_router.get("/get_tool_recipe_plots", response_model=List)
async def get_tool_recipe_plots(
    site_id: str,
    project_id: str,
    run_id: str = Query(..., description="Run ID"),
    feature_name: str = Query(..., description="Feature name"),
    step_name: str = Query(..., description="Step name"),
    service: UC3Service = Depends(),
    sync_client: MongoClient = Depends(get_db_sync),
):
    """Fetch tool, recipe and time series plots for a run."""
    logger.info(f"UC3_Dashboard: Fetching tool, recipe and time series plots for run {run_id}")
    try:
        result = await service.get_tool_recipe_plots(run_id=run_id, feature_name=feature_name, step_name=step_name, sync_client=sync_client)
        logger.info(f"Fetched tool and recipe plots for run {run_id}")
        return result
    except HTTPException as e:
        logger.warning(f"Tool and recipe plots not found for run: {run_id}", exc_info=e)
        raise e
    except Exception as e:
        logger.exception(
            f"Failed to fetch tool and recipe plots for run: {run_id}", exc_info=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching tool and recipe plots.",
        ) from e
    finally:
        close_db_sync(sync_client)