from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

import logging
from datetime import datetime, timezone
from .schemas import MicronDataCatalogSessionInput, MicronDataCatalogSessionOutput, MicronDataCatalog
from .dao import *
from app.services.micron.data_catalog.fd_trace.job_dao import FdTraceJobDao 
from app.services.micron.data_catalog.fd_trace.service import FdTraceDataPullService
# from .dao import 

logger = logging.getLogger(__package__)

class DataCatalogSessionMgntService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        
        self.datacatalog_session_mgnt_dao = DataCatalogMgntDao(db_sync_client=db_sync_client, db_async_client=db_async_client)

        self.fd_trace_job_dao = FdTraceJobDao(db_sync_client=db_sync_client, db_async_client=db_async_client)

        self.fd_trace_data_service = FdTraceDataPullService(db_sync_client=db_sync_client, db_async_client=db_async_client)

    async def create_datacatalog_session(self, user_id: str, owner_name: str, catalog_session: MicronDataCatalogSessionInput) -> Tuple[str, str]:
        
        logger.info("Inside create_datacatalog_session_async function")
        current_timestamp = datetime.now(timezone.utc)

        # creating datacatalog session record
        catalog_session_record = MicronDataCatalog(user_id=user_id,
                                                   owner_name=owner_name,
                                                   project_id=catalog_session.project_id,
                                                   name=catalog_session.name,
                                                   description=catalog_session.description,
                                                   data_source_type=catalog_session.data_source_type,
                                                   created_at=current_timestamp,
                                                   data_pull_job_id=""
                                                   )
         
        session_id: str = await self.datacatalog_session_mgnt_dao.create_data_catalog_session_async(config=catalog_session_record)

        #creating fd-data pull job record
        fd_data_pull_job_id = await self.fd_trace_data_service.initialize_fd_data_pull(session_id=session_id)


        await self.datacatalog_session_mgnt_dao.update_session_record_with_fd_data_pull_job_id(session_id=session_id, fd_data_pull_job_id=fd_data_pull_job_id)

        
        return session_id, fd_data_pull_job_id
    
    async def get_datacatalog_session_async(self, session_id: str) -> MicronDataCatalog:

        logger.info(f"getting the the datacatalog session with id {session_id}")

        return await self.datacatalog_session_mgnt_dao.get_datacatalog_session_async(session_id=session_id)
    
    async def get_all_datacatalog_sessions_async(self, search_term: str, page_number: int, page_limit: int, project_id: str = None) -> Tuple[List[MicronDataCatalog], int]:
        
        logger.info("getting all the datacatalog sessions.")

        datacatalog_sessions, total_count = await self.datacatalog_session_mgnt_dao.get_all_datacatalog_sessions_async(
                                                                                                                    search_term=search_term,
                                                                                                                    page_number=page_number,
                                                                                                                    page_limit=page_limit,
                                                                                                                    projectId=project_id
                                                                                                                    )
        logger.info(f"Found {total_count} number of datacatalog sessions.")
        return (datacatalog_sessions, total_count)

    async def delete_session(self, session_id: str):
        is_deleted = await self.datacatalog_session_mgnt_dao.delete_session(session_id)
        if not is_deleted:
            raise Exception("Unable to delete session", session_id)

