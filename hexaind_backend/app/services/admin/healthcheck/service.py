from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import traceback

from app.config.env_vars import environment
from app.services.admin.healthcheck.dao import HealthCheckDao
from app.services.admin.authentication.schemas import UserStatus
from app.core.services.cloud_utils.utils import get_secret_manager

logger = logging.getLogger(__package__)

class HealthCheckService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        self.healthcheck_dao = HealthCheckDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.secret_manager = get_secret_manager()
        logger.info("inside HealthCheck service")

    async def check_database_status(self):
        db_status_dict = {}
        try:
            db_conn_info = await self.healthcheck_dao.get_db_connections()
            db_status_dict['db_conn_info'] = db_conn_info

            try:
                roles_list = await self.healthcheck_dao.get_server_roles()
                db_status_dict['roles_list'] = roles_list
            except Exception as e:
                db_status_dict['roles_list'] = f"Failed to get Roles collection. Exception {e}"

            try:
                server_admin_users_list = await self.healthcheck_dao.get_server_role_users()
                count = 0
                if server_admin_users_list and len(server_admin_users_list) > 0:
                    count = len(server_admin_users_list)
                db_status_dict['server_admin_users_count'] = count
            except Exception as e:
                db_status_dict['server_admin_users_list'] = f"Failed to get Server Admin users from collection users. Exception{e}"
            print(f">>>>>>>>>>>>>>\n{db_status_dict}")
            return db_status_dict
        except Exception as e:
            return f"Failed even to get database connection details {e}"
        
    async def get_user_details(self):
        user_det_dict = {}
        try:
            server_admin_users_list = await self.healthcheck_dao.get_server_role_users()
            if server_admin_users_list:
                user_det_dict['server_admin_users'] = server_admin_users_list
            else:
                user_det_dict['server_admin_users'] = 'None'

            sso_users_count = self.healthcheck_dao.get_users_count_based_on_column_filter({'is_sso_user': True})
            form_users_count = self.healthcheck_dao.get_users_count_based_on_column_filter({'is_sso_user': False})
            active_users_count = self.healthcheck_dao.get_users_count_based_on_column_filter({'status': UserStatus.ACTIVE})
            inactive_users_count = self.healthcheck_dao.get_users_count_based_on_column_filter({'status': UserStatus.INACTIVE})
            invited_users_count = self.healthcheck_dao.get_users_count_based_on_column_filter({'status': UserStatus.INVITED})
            total_users = self.healthcheck_dao.get_users_count_based_on_column_filter({})

            user_det_dict['sso_users_count'] = sso_users_count
            user_det_dict['form_users_count'] = form_users_count
            user_det_dict['active_users_count'] = active_users_count
            user_det_dict['inactive_users_count'] = inactive_users_count
            user_det_dict['invited_users_count'] = invited_users_count
            user_det_dict['total_users'] = total_users

            return user_det_dict
        except Exception as e:
            traceback.print_exc()
            return f"Failed even to Fetch User Details. Exception{e}"
        
    async def test_secret_manager_access(self):
        """Test access to configured secret manager"""
        status_dict = {}
        try:
            # Get the environment from the secret manager
            env = self.secret_manager.env
            
            # Get provider type
            provider_type = env.__class__.__name__.replace('Environment', '')
            status_dict['provider_type'] = provider_type
            
            # Get secret names list
            secret_names_list = env.get_vault_secret_names_list()
            status_dict['secret_names_list'] = secret_names_list

            # Test access to each secret
            if secret_names_list:
                for secret_name in secret_names_list:
                    try:
                        secret_value = self.secret_manager.get_secret(secret_name)
                        status_dict[secret_name] = 'Available' if secret_value else 'Not Available'
                    except Exception as e:
                        status_dict[secret_name] = f'Error: {str(e)}'
            
            return status_dict

        except Exception as e:
            logger.exception("Failed to check secret manager status")
            return f"Failed to check secret manager status. Exception: {e}"

    

