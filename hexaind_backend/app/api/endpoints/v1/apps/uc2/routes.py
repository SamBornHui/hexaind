import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.services.apps.uc2.schemas import (
    UC2ProjectData,
    UC2ProjectMetadata,
    UC2ProjectNames,
    UpdateChamberStatusResponse,
    SPCChartData,
)
from app.services.apps.uc2.service import UC2Service
from app.actions import Actions
logger = logging.getLogger(__name__)
uc2_router = APIRouter(prefix="/v1/uc2", tags=["UC2"], route_class=CheckNameRoute)


class UC2Router:
    def __init__(self, service: UC2Service):
        self.service = service

    @staticmethod
    @uc2_router.get("/get_project_names", response_model=UC2ProjectNames)
    async def get_project_names(service: UC2Service = Depends(UC2Service)):
        """
        Fetches all project names.
        """

        try:
            project_names = await service.get_project_names()
            return UC2ProjectNames(project_names=project_names)
        except Exception as e:
            logger.exception("Failed to fetch project names.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred while fetching project names: {str(e)}",
            )

    @staticmethod
    @uc2_router.get("/get_project_metadata", response_model=UC2ProjectMetadata)
    async def get_project_metadata(
        project_name: str = Query(..., description="Name of the project"),
        service: UC2Service = Depends(UC2Service),
    ):
        """
        Fetches metadata for a specific project.
        """

        try:
            project_metadata = await service.get_project_metadata(project_name)
            if not project_metadata:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project metadata for '{project_name}' not found.",
                )
            return UC2ProjectMetadata(project_metadata=project_metadata)
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.exception(f"Failed to fetch metadata for project: {project_name}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred while fetching project metadata: {str(e)}",
            )

    @staticmethod
    @uc2_router.get("/get_project_data", response_model=UC2ProjectData)
    async def get_project_data(
        project_name: str = Query(..., description="Name of the project"),
        work_week_folder_name: str = Query(..., description="Name of the work week folder"),
        output_column_name: str = Query(... , description="output column name"),
        optimization_folder: Optional[str] = Query(None, description="Name of the optimization folder"),
        service: UC2Service = Depends(UC2Service),
    ):
        """
        Fetches data for a specific project and work week folder.
        """

        try:
            project_data = await service.get_project_data(
                project_name, work_week_folder_name, output_column_name, optimization_folder
            )
            return project_data
        except Exception as e:
            logger.exception(
                f"Failed to fetch data for project: {project_name}, work week: {work_week_folder_name}, output column: {output_column_name}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred while fetching project data: {str(e)}",
            )

    
    @staticmethod
    @uc2_router.get("/get_project_data_with_chamber_count", response_model=UC2ProjectData,openapi_extra={"actions":Actions.UC2_Visualization.value})
    async def get_project_data_with_chamber_count(
        project_name: str = Query(..., description="Name of the project"),
        work_week_folder_name: str = Query(..., description="Name of the work week folder"),
        output_column_name: str = Query(..., description="Output column name"),
        optimization_folder: Optional[str] = Query(None, description="Name of the optimization folder"),
        service: UC2Service = Depends(UC2Service),
    ):
        
        try:
            project_data_with_chamber_count = await service.fetch_project_data_with_chamber_count(
                project_name, work_week_folder_name, output_column_name, optimization_folder
            )
            return project_data_with_chamber_count
        except Exception as e:
            logger.exception(
                f"Failed to fetch project data with chamber count for project: {project_name}, work week: {work_week_folder_name}, output column: {output_column_name}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred while fetching project data with chamber count: {str(e)}",
            )
    
    @staticmethod
    @uc2_router.post("/update_chamber_status", response_model=UpdateChamberStatusResponse)
    async def update_chamber_status(
        project_name: str = Query(..., description="Name of the project"),
        work_week_folder_name: str = Query(..., description="Name of the work week folder"),
        output_column_name: str = Query(..., description="Output column name"),
        start_date: str = Query(..., description="Start date for calculating the interval (YYYY-MM-DD)"),
        end_date: str = Query(..., description="End date for calculating the interval (YYYY-MM-DD)"),
        interval: int = Query(..., description="week_interval"),
        status: str = Query(..., description="Status of the chamber (Active or InActive)"),
        chamber_id : str = Query(..., description="Name of the chamber"),
        optimization_folder: Optional[str] = Query(None, description="Name of the optimization folder"),
        service: UC2Service = Depends(UC2Service),
    ):
        """
        Updates the `status_tracking.csv` file based on the provided status parameter.
        """
        try:
            if status not in ["Active", "InActive"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status. Allowed values are 'Active' or 'InActive'.",
                )
            await service.update_status(project_name, work_week_folder_name, output_column_name, interval, status, chamber_id,optimization_folder)

            return {"message": "Status tracking file updated successfully."}

        except FileNotFoundError as e:
            logger.exception(f"File not found: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {e}")
        except KeyError as e:
            logger.exception(f"Key error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing key in data: {e}")
        except ValueError as e:
            logger.exception(f"Value error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}",
            )
    

    @staticmethod
    @uc2_router.get("/get_spc_charts_data",response_model=SPCChartData)
    async def get_spc_charts_data(
        project_name: str = Query(..., description="Name of the project"),
        work_week_folder_name: str = Query(..., description="Name of the work week folder"),
        output_column_name: str = Query(..., description="Output column name in data_spc_charts.csv"),
        chamber_ids: Optional[List[str]] = Query(None, description="List of chamber IDs"),
        filter_by_feedforward: bool = Query(False, description="If True, drop rows with NaN in feedforward param columns"),
        optimization_folder: Optional[str] = Query(None, description="Name of the optimization folder"), 
        service: UC2Service = Depends(UC2Service),
    ):
        """
        Reads data from 'data_spc_charts.csv', optionally filtered by the given chamber IDs.
        If filter_by_feedforward=true, any row with NaN in feedforward param columns is dropped.
        Returns a dict containing:
        - ucl, lcl, target (from metadata)
        - chambers: { ChamberID: { runcomplete_datetime: [...], output_values: [...] }, ... }
        """
        try:
            all_metadata = await service.get_project_metadata(project_name)
            folder_metadata = next(
                (m for m in all_metadata if m.work_week_folder_name == work_week_folder_name),
                None
            )
            if not folder_metadata:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No metadata found for folder: {work_week_folder_name}",
                )

            feedforward_params = folder_metadata.feedforward_params or {}
            ucl = folder_metadata.ucl
            lcl = folder_metadata.lcl
            target = folder_metadata.target

            data = await service.get_spc_data_csv(
                project_name=project_name,
                work_week_folder_name=work_week_folder_name,
                output_column_name=output_column_name,
                feedforward_params=feedforward_params,
                ucl=ucl,
                lcl=lcl,
                target=target,
                chamber_ids=chamber_ids,
                filter_by_feedforward=filter_by_feedforward,
                optimization_folder=optimization_folder

            )

            return data

        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.exception(
                f"Failed to get SPC data for "
                f"project={project_name}, folder={work_week_folder_name}, output_column={output_column_name}, "
                f"chambers={chamber_ids}, filter={filter_by_feedforward}. Error: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}",
            )
    
    @staticmethod
    @uc2_router.get("/get_siso_plots",response_model=List[str])
    async def get_siso_plots(
        project_name: str = Query(..., description="Name of the project"),
        work_week_folder_name: str = Query(..., description="Name of the work week folder"),
        output_column_name: str = Query(..., description="Output column name"),
        optimization_folder: str = Query(..., description="optimization_folder name"),
        subfolder: str = Query(..., description="subfolder name"),
        service: UC2Service = Depends(UC2Service),
    ): 
        return await service.get_siso_plots(
        project_name=project_name,
        work_week_folder_name=work_week_folder_name,
        output_column_name=output_column_name,
        optimization_folder=optimization_folder,
        subfolder=subfolder
    )
        


     

        