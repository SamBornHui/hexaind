from typing import Dict
from app.core.dao.dao_base import *

class PredictionDao(DaoBase):
    

   def get_document_by_id_sync(self, filter_document: Dict, collection: str=None):
      model_document = self.db_sync[collection].find_one(filter_document)
      return model_document
   
   async def get_document(self, filter_document: Dict, collection: str=None):
      model_document = await self.db_async[collection].find_one(filter_document)
      return model_document
    
   async def update_document(self, filter_document: Dict=None, new_value: Dict=None, collection: str=None):
      await self.db_async[collection].update_one(filter_document, {"$set": new_value})
      
   async def delete_document(self, filter_document: Dict=None, collection: str=None):
      await self.db_async[collection].delete_one(filter_document)
       
       
   async def get_all_document(self, query: Dict=None, collection: str="models"):
        models_cursor = self.db_async[collection].aggregate(
            [   
                {"$match": query},
                {"$addFields": {"_id": {"$toString": "$_id"},
                                "created_at": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S.%LZ", "date": "$created_at"}},
                                "last_modified_at": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S.%LZ", "date": "$last_modified_at"}}
                                }},
            ]
        )

        models = await models_cursor.to_list(length=500)

        return models


    