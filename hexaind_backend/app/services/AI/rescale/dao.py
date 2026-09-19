import logging
from bson.objectid import ObjectId

from app.core.dao.dao_base import *
from .schemas import RescaleRunningINFO
from app.services.AI.mobo.schemas import *
from app.services.admin.connectors.schemas import *

logger = logging.getLogger(__package__)


class RescaleDao(DaoBase):
   
    def get_connector(self, connector_id: str) -> Connector:
        result = self.db_sync.connectors.find_one({"_id": ObjectId(connector_id)})
        if not result:
            raise Exception("connector not found")
        
        result["_id"] = str(result["_id"])

        return Connector(**result)

    def save_rescale_running_info(self, rescale_running_info: Dict):
        result  = self.get_rescale_running_info(rescale_running_info["run_id"])
        if result:
            logger.info("rescale_running_info already exists")
            self.db_sync.rescale_runs.update_many({"run_id": rescale_running_info["run_id"]}, {"$set": rescale_running_info})
        else:
            logger.info("rescale_running_info not found.. inserting new one")
            self.db_sync.rescale_runs.insert_one(rescale_running_info)
        
    def get_rescale_running_info(self, wf_run_id: str) -> RescaleRunningINFO:
        result = self.db_sync.rescale_runs.find_one({"run_id": wf_run_id})
        if not result:
            logger.info("rescale_running_info not found")
            return None
        
        result["_id"] = str(result["_id"])

        return RescaleRunningINFO(**result)
    
    async def update_rescale_running_info_async(self, wf_run_id: str, rescale_running_info: Dict):
        await self.db_async.rescale_runs.update_many({"run_id": wf_run_id}, {"$set": rescale_running_info})
    
    def update_rescale_running_info(self, wf_run_id: str, rescale_running_info: Dict):
        self.db_sync.rescale_runs.update_many({"run_id": wf_run_id}, {"$set": rescale_running_info})
    
    
    
    

    
