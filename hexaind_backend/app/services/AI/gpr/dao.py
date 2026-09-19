from typing import Dict
from app.core.dao.dao_base import *
from app.services.AI.gpr.schemas import *
from typing import List, Any

class GPRDao(DaoBase):
    def insert_gpr_record_sync(self, data, col_name: str='models') -> str:
        """
        For inserting a record in mongo collection
        """
        result = self.db_sync[col_name].insert_one(data)
        if not result:
             raise Exception("not able to ingest data into model_temp col")



        