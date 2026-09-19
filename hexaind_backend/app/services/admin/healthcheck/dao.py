
import logging

from app.core.dao.dao_base import DaoBase

logger = logging.getLogger(__package__)

class HealthCheckDao(DaoBase):
    async def get_db_connections(self):
        sync_db_str = self.db_sync
        async_db_str = self.db_async
        resp = {"async_db":f"{sync_db_str}","sync_db": f"{async_db_str}"}
        return resp
    
    async def get_server_roles(self):
        roles_list = list(self.db_sync.roles.find({}))
        return roles_list
    
    async def get_server_role_users(self):
        server_admin_users_list = list(self.db_sync.users.find({'server_role_value': 1},{'_id':0,'password':0}))
        return server_admin_users_list
    
    def get_users_count_based_on_column_filter(self, filter_dict):
        ret_value = self.db_sync.users.count_documents(filter_dict)
        return ret_value

