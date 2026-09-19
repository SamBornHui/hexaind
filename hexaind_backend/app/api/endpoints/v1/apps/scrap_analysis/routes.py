import os
import re
import sys
import logging
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient

from app.services.access_controls.user_projects.service import (
    UsersProjectsMappingsService,
)
from app.config.env_vars import environment as env
from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from app.core.db.db_utils import get_db_async
from app.services.data.assets.datasets.schemas import AssetsListResponse
from app.services.apps.scrap_analysis.service import SAMService
from app.services.apps.scrap_analysis.schemas import (
    FormatBaselineResponse,
    ExtractAlloyResponse,
    ExtractAlloyRequest,
    SAMUseCase,
    ScenariosResponse,
    SAMViz,
    DeleteSAMResponse,
    GetLimitsResponse,
)

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

sam_router = APIRouter(tags=["SAM"], route_class=CheckNameRoute)


class ScrapAnalysisRouter:

    def __init__(self):
        """
        Class Initialization
        """
        pass

    @sam_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/sam/get_baselines",
        response_model=AssetsListResponse,
    )
    async def get_baseline_files(
        siteId: str,
        projectId: str,
        search_term: str = Query(default=None),
        page_limit: int = Query(default=10),
        page_number: int = Query(default=1),
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> AssetsListResponse:

        try:
            logger.info("inside get datasets method.")
            sam_handler = SAMService(db_async_client=client)
            datasets, count = await sam_handler.get_baseline_files(
                site_id=siteId,
                project_id=projectId,
                search_term=search_term,
                page_number=page_number,
                page_limit=page_limit,
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @sam_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/sam/format_scrap_data",
        response_model=FormatBaselineResponse,
    )
    async def format_scrap_data(
        siteId: str,
        projectId: str,
        file_path: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> FormatBaselineResponse:

        try:
            logger.info("inside fetch scrap data method.")
            sam_handler = SAMService(db_async_client=client)
            scrap_data = await sam_handler.format_baseline_data(
                project_id=projectId,
                file_path=file_path,
            )
            logger.info(f"retrieved scrap data.")
            return FormatBaselineResponse(**scrap_data)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @sam_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sam/extract_alloys_data",
        response_model=ExtractAlloyResponse,
    )
    async def extract_alloys_detail(
        siteId: str,
        projectId: str,
        request_data: ExtractAlloyRequest,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> ExtractAlloyResponse:

        try:
            logger.info("inside fetch scrap data method.")
            sam_handler = SAMService(db_async_client=client)
            extracted_data = await sam_handler.extract_data(
                project_id=projectId,
                alloys=request_data.alloys,
                file_path=request_data.file_path,
                baseline_file=request_data.baseline_file,
            )
            logger.info(f"retrieved scrap data.")
            return ExtractAlloyResponse(extracted_data=extracted_data)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @sam_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sam/save_scenarios",
        response_model=ScenariosResponse,
    )
    async def save_scenarios(
        siteId: str,
        projectId: str,
        request_data: SAMUseCase,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> ScenariosResponse:

        try:
            logger.info("inside save scenarios method.")
            sam_handler = SAMService(db_async_client=client)
            print("config file :     ", request_data.config_content)
            #### implement the logic to save config file
            config_file_path = request_data.config_content
            if config_file_path and not os.path.exists(config_file_path):
                logger.info("Config file content received.")
                parent_dir = os.path.join(
                    env.base_path,
                    "scrap_analysis",
                    str(projectId),
                    f"{request_data.usecase_name}_{request_data.user_id}",
                )
                os.makedirs(parent_dir, exist_ok=True)
                config_file_path = os.path.join(parent_dir, "config.ini")
                # Write the string content into the .ini file
                with open(config_file_path, "w", encoding="utf-8") as f:
                    f.write(request_data.config_content)

                request_data.config_content = config_file_path

            result = await sam_handler.save_scenarios(
                project_id=projectId, scenarios_data=request_data
            )
            logger.info(f"saved scenarios data. {result}")
            return ScenariosResponse(
                usecase_id=result["usecase_id"],
                message=result["message"],
                usecase_data=result["usecase_data"],
            )

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @sam_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/sam/get_scenarios",
        response_model=List[SAMUseCase],
    )
    async def get_scenarios(
        siteId: str,
        projectId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> List[SAMUseCase]:

        try:
            logger.info("inside get scenarios method.")
            sam_handler = SAMService(db_async_client=client)
            result = await sam_handler.get_scenarios(project_id=projectId)
            return result

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @sam_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sam/usecase/{usecaseId}/run_scenarios",
        response_model=SAMUseCase,
    )
    async def run_scenarios(
        siteId: str,
        projectId: str,
        usecaseId: str,
        user_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> SAMUseCase:

        try:
            logger.info("inside run scenarios method.")
            sam_handler = SAMService(db_async_client=client)
            result = await sam_handler.run_scenarios(
                project_id=projectId, usecase_id=usecaseId, user_id=user_id
            )
            if not result:
                raise Exception
            return result

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @sam_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sam/plot_viz",
        response_model=List[str],
    )
    async def sam_visualization(
        siteId: str,
        projectId: str,
        viz_data: SAMViz,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> List[str]:

        try:
            logger.info("inside sam viz scenarios.")
            sam_handler = SAMService(db_async_client=client)
            result = await sam_handler.plot_viz(viz_data=viz_data)
            if not result:
                logger.error("Unable to generate plots")
                raise Exception
            return result

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @sam_router.delete(
        "/v1/sites/{siteId}/projects/{projectId}/sam/type/{sam_type}/id/{samId}",
        response_model=DeleteSAMResponse,
    )
    async def delete_sam(
        siteId: str,
        projectId: str,
        sam_type: str,
        samId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> DeleteSAMResponse:

        try:
            logger.info("inside sam delete .")
            sam_handler = SAMService(db_async_client=client)
            result = await sam_handler.remove_sam_data(
                project_id=projectId, sam_case=sam_type, sam_id=samId
            )
            if not result:
                logger.error("Unable to delete SAM data")
                raise Exception
            return DeleteSAMResponse(**result)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @sam_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/sam/get_limits",
        response_model=GetLimitsResponse,
    )
    async def get_limits(
        siteId: str,
        projectId: str,
        file_path: str = Query(..., description="Path to the baseline file"),
    ) -> GetLimitsResponse:
        """
        Fetches limit data for a given project.

        Args:
            siteId (str): Site ID.
            projectId (str): Project ID.
            file_path (str): Path to the baseline file (passed as query parameter).

        Returns:
            GetLimitsResponse: Limits data for the frontend.
        """
        try:
            logger.info(
                f"Fetching limit data for project {projectId} at site {siteId}."
            )

            sam_handler = SAMService()
            result = await sam_handler.list_limit_data(
                project_id=projectId, file_path=file_path
            )

            return result

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}", exc_info=True)
            return GetLimitsResponse(limits=[], demands=[], message="File not found")

        except ValueError as e:
            logger.error(f"Invalid file format: {str(e)}", exc_info=True)
            return GetLimitsResponse(
                limits=[], demands=[], message="Invalid file format"
            )

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return GetLimitsResponse(limits=[], demands=[], message=str(e))

    # @sam_router.get(
    #     "/v1/sites/{siteId}/projects/{projectId}/sam/plot/baselines/{baselineId}",
    #     response_model=GetLimitsResponse,
    # )
    # async def plot_baseline(
    #     siteId: str,
    #     projectId: str,
    #     baselineId: str = Query(..., description="baseline id"),
    # ) -> GetLimitsResponse:
    #     """
    #     Plot baseline data  (Prime) for a given project

    #     Args:
    #         siteId (str): Site ID.
    #         projectId (str): Project ID.
    #         baselineId (str): baseline id.

    #     Returns:
    #         GetLimitsResponse: Limits data for the frontend.
    #     """
    #     try:
    #         logger.info(
    #             f"plot_baseline {projectId} at site {siteId}. baselineId {baselineId}"
    #         )

    #         sam_handler = SAMService()
    #         result = await sam_handler.prime_plot(
    #             project_id=projectId, baselineId=baselineId
    #         )

    #         return result

    #     except ValueError as e:
    #         logger.error(f"Invalid file format: {str(e)}", exc_info=True)
    #         return GetLimitsResponse(
    #             limits=[], demands=[], message="Invalid file format"
    #         )

    #     except Exception as e:
    #         logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    #         return GetLimitsResponse(limits=[], demands=[], message=str(e))


sam_router_obj = ScrapAnalysisRouter()
