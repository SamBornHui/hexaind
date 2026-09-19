import logging
import traceback
from contextlib import contextmanager

from app.services.micron.data_catalog.fd_trace.schemas import FdDataPullConfig, FdDataPullJobConfig, DataPullStatus, DataCatalogStatus
from app.services.micron.data_catalog.schemas import MicronDataCatalog
from app.services.micron.data_catalog.service import FdTraceDataPullService
from app.services.micron.data_catalog.dao import DataCatalogMgntDao
from app.services.micron.data_catalog.fd_trace.job_dao import FdTraceJobDao
from app.core.db.db_utils import get_db_sync

logger = logging.getLogger(__package__)

class StageConfigJobHandler:

    def __init__(self, data_pull_job_id: str, stage_job_id: str):

        self.db_client = get_db_sync()
        self.data_pull_job_id = data_pull_job_id
        self.stage_job_id = stage_job_id

        self.fd_trace_service = FdTraceDataPullService(db_sync_client=self.db_client)
        self.fd_trace_job_dao = FdTraceJobDao(db_sync_client=self.db_client)
        self.datacatalog_session_mgnt_dao = DataCatalogMgntDao(db_sync_client=self.db_client, db_async_client=None)

        self.data_pull_job_record: FdDataPullConfig = self.fd_trace_service.get_fd_data_pull_job_record_sync(job_id=self.data_pull_job_id)
        self.stage_job_record: FdDataPullJobConfig = self.fd_trace_service.get_fd_data_pull_job_config_record_sync(job_config_id=self.stage_job_id)
        self.datacatalog_session_record: MicronDataCatalog =  self.datacatalog_session_mgnt_dao.get_datacatalog_session_sync(session_id=self.data_pull_job_record.session_id)

        if self.stage_job_record is None or self.data_pull_job_record is None:
            raise Exception(f"Unable to find out stage job config. Given data pull job: {self.data_pull_job_id} and stage job: {self.stage_job_id}")

@contextmanager
def common_data_pull_stage_manager(app, data_pull_job_id: str, stage_job_id: str):

    try:
        stage_config_obj = StageConfigJobHandler(data_pull_job_id=data_pull_job_id,
                                                 stage_job_id=stage_job_id)
        
        # checkt the stage job bigquery details configured or not
        if (stage_config_obj.stage_job_record.stage_config.status is None):
            raise Exception(f"can't execute the stage. Stage config is missing")
        
        elif stage_config_obj.stage_job_record.stage_config.status.job_config == {}:
            raise Exception(f"can't execute the stage. Job config is missing")
        
        # check the stage job configured correctly or not
        if stage_config_obj.stage_job_record.stage_config.status.status == DataPullStatus.NOT_CONFIGURED:
            raise Exception(f"can't execute the stage. Since it in {stage_config_obj.stage_job_record.stage_config.status.status}")
        
        if stage_config_obj.stage_job_record.stage_config.status.status == DataPullStatus.RUNNING: #TODO fetch the current job id resume or restart the stage job
            logger.info(f"Stage job: {stage_config_obj.stage_job_record.stage} status is already in running. Submitted again to the worker")
        

        #update the data pull job with status and current stage
        stage_config_obj.fd_trace_service.update_fd_data_pull_job_record_current_stage_sync(job_id=data_pull_job_id, 
                                                                                            current_stage=stage_config_obj.stage_job_record.stage, 
                                                                                            current_stage_status=DataCatalogStatus.RUNNING)

        #update the stage job record status
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_current_status_sync(job_id=stage_job_id, new_status=DataPullStatus.RUNNING)
        
        yield stage_config_obj

    except Exception as e:
        print(f"Exception occured while executing the micron stage job: {traceback.format_exc()}")
        logger.error(f"Exception occured while executing the micron stage job: {traceback.format_exc()}")
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_current_status_and_result_sync(job_id=stage_job_id, new_status=DataPullStatus.FAILED, result={"error":str(e)})  
        stage_config_obj.fd_trace_service.update_fd_data_pull_job_record_current_stage_sync(job_id=data_pull_job_id, 
                                                                                            current_stage=stage_config_obj.stage_job_record.stage, 
                                                                                            current_stage_status=DataCatalogStatus.IDLE)

    finally:
        if stage_config_obj and stage_config_obj.db_client:
            stage_config_obj.db_client.close()