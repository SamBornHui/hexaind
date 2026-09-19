from app.core.dao.dao_base import *
from app.services.AI.svm.schemas import *

class SVMDao(DaoBase):
    def insert_svm_record_sync(self, data, col_name: str = "models") -> str:
        """
        For inserting a record in mongo collection
        """
        result = self.db_sync[col_name].insert_one(data)
        if not result:
            raise Exception("not able to ingest data into model_temp col")
