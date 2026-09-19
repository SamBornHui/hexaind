from bson import ObjectId
from datetime import datetime, timezone
from typing import List, Optional, Union, Tuple, Any
import json
from app.core.dao.dao_base import *
from app.services.admin.connectors.schemas import *

class ConnectorDao(DaoBase):

    async def create_connector_async(self, connector: Connector) -> str:

        result = await self.db_async.connectors.insert_one(connector.model_dump())
        if not result:
            raise Exception("not able to create connectors")
        
        connector_id = str(result.inserted_id)

        return connector_id
    
    async def get_connector_by_id_async(self, connector_id: str) -> Connector:

        connector = await self.db_async.connectors.find_one({"_id": ObjectId(connector_id)})
        
        if not connector:
            raise Exception("Connector not found")
        
        connector["_id"] = str(connector["_id"])
        return Connector(**connector)

    async def get_all_connectors_async(self, project_id: str, search_term: str, page_number: int, page_limit: int) -> Tuple[List[Connector], int]:

        query = {"project_id": project_id}

        if search_term:
            search_query = {"$regex": search_term, "$options": "i"} # Case-insensitive search
            query["$or"] = [{"name": search_query}, {"description": search_query},  {"owner_name": search_query}]

        offset = (page_number - 1) * page_limit if page_number and page_limit else 0

        connectors_cursor = self.db_async.connectors.aggregate(
            [   
                {"$match": query},
                {"$addFields": {"_id": {"$toString": "$_id"},
                                "created_at": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S.%LZ", "date": "$created_at"}},
                                "last_modified_at": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S.%LZ", "date": "$last_modified_at"}}
                                }},
                {"$skip": offset},
                {"$match": {
                    "$or": [
                        {"is_active": True},
                        {"is_active": {"$exists": False}}
                    ]
                }},
                {"$limit": page_limit}
            ]
        )

        connectors = await connectors_cursor.to_list(length=page_limit)

        total_count = await self.db_async.connectors.count_documents(query)

        return (connectors, total_count)
    
    async def update_connector_async(self, connector_id: str, connector: Connector) -> bool:

        result = await self.db_async.connectors.find_one_and_update(
            {"_id": ObjectId(connector_id)},
            {"$set": connector.model_dump()}
            )
        if not result:
            raise Exception("Unable to update connector")
        
        return True

    @staticmethod
    def search_key_and_value_in_dict(document, field_value, keys: list):
        if isinstance(document, dict):
            for key, value in document.items():
                if value == field_value and key in keys :
                    return True
                elif isinstance(value, dict):
                    if ConnectorDao.search_key_and_value_in_dict(value, field_value, keys):
                        return True
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            if ConnectorDao.search_key_and_value_in_dict(item, field_value, keys):
                                return True

    
    async def delete_connector_async(self, connector: Connector, user_id) -> DeleteConnectorResponse:
        # Check the usage in Workflows if found don't delete
        connector_id = connector.id
        found_usage = False
        project_id = connector.project_id
        connector_key_in_workflow = None
        conn_type = connector.type
        if conn_type == ConnectorType.RESCALE:
             connector_key_in_workflow = 'rescale_connector_id'
        elif conn_type == ConnectorType.BIGQUERY:
            connector_key_in_workflow = 'bigquery_connector_id'
        else:
            connector_key_in_workflow = 'thermocalc_connector_id'
        
        wf_cursor = self.db_async.workflows.find({'project_id': project_id})
        async for document in wf_cursor:
            if ConnectorDao.search_key_and_value_in_dict(document, connector_id, [connector_key_in_workflow]):
                found_usage = True
                break

        # in case of rescale, there is a possibility to use in rescale_information
        if found_usage == False and conn_type == ConnectorType.RESCALE:
            connector_info = await self.db_async.rescale_information.find_one({'connector_id':connector_id})
            if connector_info:
                found_usage = True
        if found_usage == True:
            return DeleteConnectorResponse(success=False, message="Connector cannot be deleted since it is already in use.")
        else:
            updated_dt_time = datetime.now(timezone.utc).astimezone()
            result = await self.db_async.connectors.update_one({"_id": ObjectId(connector_id)},{"$set": {"is_active": False, 'last_modified_by_id': user_id, 'last_modified_at': updated_dt_time}})
            if result.matched_count >0 and result.modified_count > 0:
                return DeleteConnectorResponse(success=True, message="Connector Succcessfully deleted.")
            else: 
                return DeleteConnectorResponse(success=False, message="Connector already deleted(Marked as deleted).")
    
    def get_connector(self, connector_id: str) -> Connector:

        result = self.db_sync.connectors.find_one({"_id": ObjectId(connector_id)})

        if not result:
            raise Exception("connector not found")
        
        result["_id"] = str(result["_id"])

        return Connector(**result)
    
    async def fetch_rescale_record_async(self, connector_id) -> Any:
        """
        For fetching a record in mongo collection
        """
        
        result = await self.db_async.rescale_information.find_one({'connector_id': connector_id})
        if not result:
            raise Exception("rescale data not found")
        
        return RescalePlatformFiles(**result)
    
    def fetch_rescale_record(self, connector_id) -> Any:
        """
        For fetching a record in mongo collection
        """
        
        result = self.db_sync.rescale_information.find_one({'connector_id': connector_id})
        if not result:
            raise Exception("rescale data not found")
        
        return RescalePlatformFiles(**result)
    
    async def insert_rescale_record_async(self, data) -> str:

        """
        For inserting a record in mongo collection
        """
        await self.db_async.rescale_information.delete_one({'connector_id': data['connector_id']})
        result = await self.db_async.rescale_information.insert_one(data)
        if not result:
             raise Exception("not able to ingest data into rescale information")
        
    def insert_rescale_record(self, data) -> str:

        """
        For inserting a record in mongo collection
        """
        self.db_sync.rescale_information.delete_one({'connector_id': data['connector_id']})
        result = self.db_sync.rescale_information.insert_one(data)
        if not result:
             raise Exception("not able to ingest data into rescale information")

    async def get_connector_by_superset_id_async(self, superset_id: int) -> Connector:
        connector = await self.db_async.connectors.find_one(
            {"database_id": superset_id}
        )

        if not connector:
            raise Exception("Connector not found")

        connector["_id"] = str(connector["_id"])
        return Connector(**connector)