from typing import Dict
from app.core.dao.dao_base import *
from app.services.AI.mobo.schemas import *

class MOBODao(DaoBase):

    def update_record_sync(self, experiment_name, project_id, workflow_update: Dict=dict()):
        self.db_sync.workflow_trials.update_one({'workflow_name': experiment_name, 'project_id': project_id}, workflow_update)
    
    def clear_record_sync(self, experiment_name, project_id, num_iteration):
        self.db_sync.workflow_trials.delete_many({'workflow_name': experiment_name, 'project_id': project_id})
        self.db_sync.workflow_trials.insert_one({'workflow_name': experiment_name, 'project_id': project_id, 'num_iterations': num_iteration, 'stop_pending': False})

    def find_record_sync(self, experiment_name, project_id):
        workflow_trials_data = self.db_sync.workflow_trials.find_one({'workflow_name': experiment_name, 'project_id': project_id})
        return workflow_trials_data
    
    def insert_rescale_record_sync(self, data) -> str:
        """
        For inserting a record in mongo collection
        """
        self.db_sync.rescale_information.delete_many({'connector_id': data['connector_id']})
        result = self.db_sync.rescale_information.insert_one(data)
        if not result:
             raise Exception("not able to ingest data into rescale information")
        
    async def insert_rescale_record(self, data) -> str:
        """
        For inserting a record in mongo collection
        """
        await self.db_async.rescale_information.delete_many({'connector_id': data['connector_id']})
        result = await self.db_async.rescale_information.insert_one(data)
        if not result:
             raise Exception("not able to ingest data into rescale information")
        

    def get_rescale_record_id_sync(self, connector_id) -> str:
        """
        For fetching a record in mongo collection
        """
        
        result = self.db_sync.rescale_information.find_one({'connector_id': connector_id})
        return result
    
    async def get_rescale_record_id(self, connector_id) -> str:
        """
        For fetching a record in mongo collection
        """
        
        result = await self.db_async.rescale_information.find_one({'connector_id': connector_id})
        return result
        