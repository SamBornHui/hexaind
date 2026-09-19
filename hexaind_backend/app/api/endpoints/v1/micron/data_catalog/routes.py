from typing import Annotated, Optional
import logging, traceback

from fastapi import APIRouter, Depends, status, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.db.db_utils import get_db_async
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer
from app.services.admin.authentication.service import AuthenticationService
from app.services.data.assets.datasets.schemas import DatasetUploadResponse
from app.services.micron.data_catalog.service import DataCatalogSessionMgntService
from app.services.micron.data_catalog.schemas import MicronDataCatalog, MicronDataCatalogSessionInput, MicronDataCatalogSessionOutput,\
                                                    GetAllMicronDataCatalogSessionResponse

from .fd import router as fd_router
from .query import router as query_router
#from .utils import get_data_catalog_pull_dao

logger = logging.getLogger(__package__)

router = APIRouter(prefix="/data_catalog", tags=["Data Catalog"])
router.include_router(fd_router)
router.include_router(query_router)


def get_datacatalog_session_mgnt_service(
        db_async_client: Annotated[AsyncIOMotorClient, Depends(get_db_async)]
) -> DataCatalogSessionMgntService:
    return DataCatalogSessionMgntService(
        db_async_client=db_async_client
    )


class DataCatalogSessionManager:
    
    def __init__(self):
        """
        Class Initialisation
        """
        pass
     
    @router.post("/create_session", 
                 status_code=status.HTTP_200_OK)
    async def create_data_catalog_session(create_catalog_session_input: MicronDataCatalogSessionInput, 
                                          token: str = Depends(JWTBearer()),
                                          client: AsyncIOMotorClient = Depends(get_db_async)) -> MicronDataCatalogSessionOutput:
        """
        This API is responsible for creating a new session for the user for download job in datacatalog
        
        """
        try:
            logger.info("Inside data_catalog create_session API.")

            auth_service = AuthenticationService(db_async_client=client)
            user = await auth_service.get_user_by_token_or_id(token=token)

            datacatalog_session_mgnt_service = DataCatalogSessionMgntService(db_async_client=client)

            datacatalog_session_id, data_pull_job_id = await datacatalog_session_mgnt_service.create_datacatalog_session( user_id=user.id,
                                                                                                        owner_name=user.name, 
                                                                                                        catalog_session=create_catalog_session_input)
            
            return MicronDataCatalogSessionOutput(session_id=datacatalog_session_id, data_pull_job_id=data_pull_job_id)
        
        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())

            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "Got exception while creating datacatalog session", "message": str(e)}
                    )
    
    @router.post("/create_data_catalog_session_without_token/{user_id}", 
                 status_code=status.HTTP_200_OK)
    async def create_data_catalog_session_without_token(create_catalog_session_input: MicronDataCatalogSessionInput, 
                                          user_id: str,
                                          client: AsyncIOMotorClient = Depends(get_db_async)) -> MicronDataCatalogSessionOutput:
        try:
            logger.info("Inside data_catalog create_session API.")

            auth_service = AuthenticationService(db_async_client=client)
            user = await auth_service.get_user_with_id(user_id=user_id)
            datacatalog_session_mgnt_service = DataCatalogSessionMgntService(db_async_client=client)
            datacatalog_session_id, data_pull_job_id = await datacatalog_session_mgnt_service.create_datacatalog_session( user_id=user.id,
                                                                                                        owner_name=user.name, 
                                                                                                        catalog_session=create_catalog_session_input)
            return MicronDataCatalogSessionOutput(session_id=datacatalog_session_id, data_pull_job_id=data_pull_job_id)
        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "Got exception while creating datacatalog session", "message": str(e)}
                    )

    @staticmethod
    @router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_session(
        session_id: str,
        datacatalog_session_mgnt_service: Annotated[DataCatalogSessionMgntService, Depends(get_datacatalog_session_mgnt_service)]
    ):
        try:
            logger.info("deleting a datacatalog session")
            logger.debug(f"deleting a datacatalog session {session_id=}")
            await datacatalog_session_mgnt_service.delete_session(session_id=session_id)
            logger.info("successfully deleted datacatalog session")
            logger.debug(f"successfully deleted datacatlog session {session_id=}")
        except Exception as e:
            logger.exception(f"unable to delete session")
            logger.debug(f"unable to delete session {session_id=}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": f"unable to delete session {session_id}"
                }
            ) from e
    
    @staticmethod
    @router.get("/sessions/{session_id}", status_code=status.HTTP_200_OK)
    async def get_session(
        session_id: str,
        datacatalog_session_mgnt_service: Annotated[DataCatalogSessionMgntService, Depends(get_datacatalog_session_mgnt_service)]
    ) -> MicronDataCatalog:
        try:
            logger.info("fetching a datacatalog session")
            logger.debug(f"fetching a datacatalog session {session_id=}")
            return await datacatalog_session_mgnt_service.get_datacatalog_session_async(session_id=session_id)
        except Exception as e:
            logger.exception(f"unable to fetch session")
            logger.debug(f"unable to fetch session {session_id=}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": f"unable to fetch session {session_id}"
                }
            ) from e

    @router.get('/get_all_sessions', status_code=status.HTTP_200_OK)
    async def get_all_session_by_id( 
                                projectId: str, 
                                page_limit: int = Query(default=10),
                                page_number: int = Query(default=1),
                                search_term: Optional[str] = None,
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> GetAllMicronDataCatalogSessionResponse:
        try:
            logger.info("getting datacatalog sessions")

            datacatalog_session_mgnt_service = DataCatalogSessionMgntService(db_async_client=client)

            datacatalog_sessions, total_count  = await datacatalog_session_mgnt_service.get_all_datacatalog_sessions_async(search_term=search_term,
                                                                                                                            page_number=page_number,
                                                                                                                            page_limit=page_limit,
                                                                                                                            project_id=projectId)
            logger.info(f"got all the datacatalog sessions. total projects: {total_count}")

            return GetAllMicronDataCatalogSessionResponse(datacatalog_sessions=datacatalog_sessions, total_count=total_count)
        
        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())

            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "while fetching datacatalog sessions", "message": str(e)}
                    )
