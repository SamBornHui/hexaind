from app.core.dao.dao_base import *

class XGBoosttDao(DaoBase):
    def insert_record_sync(self, data, col_name: str='models') -> str:
        """
        For inserting a record in mongo collection
        """
        result = self.db_sync[col_name].insert_one(data)
        if not result:
             raise Exception("not able to ingest data into model_temp col")

    