from app.core.dao.dao_base import *


class ThermocalcDao(DaoBase):
    async def find_record(self, filter):
       record = await self.db_async.ThermoCalcBatchJobs.find_one(filter)
       return record


    async def insert_record(self, main_job):
        result = await self.db_async.ThermoCalcBatchJobs.insert_one(main_job)
        return result

    async def update_record(self, filter,value):
        result = await self.db_async.ThermoCalcBatchJobs.update_one(filter,value)
        return result

    async def delete_record(self, filter):
        result = await self.db_async.ThermoCalcBatchJobs.delete_one(filter)
        return result

    def update_job_result(self, filter, value):
        result = self.db_sync.ThermoCalcBatchJobs.update_one(filter,value)
        return result
