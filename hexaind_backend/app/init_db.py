import asyncio
from pathlib import Path

from dotenv import load_dotenv
from app.core.db.db_utils import get_db_async
from app.services.access_controls.features.schemas import EndPointsFeatureMappings
from app.services.access_controls.features.service import EndPointsFeatureMappingsService
from app.services.access_controls.roles.service import RolesFeaturesMapService
from app.utils.file_utils import FileUtils
from app.custom_logging import load_logging
from logging import getLogger
from app.core.services.cloud_utils.utils import get_secret_manager
from app.services.admin.authentication.service import AuthenticationService

# Load environment variables from a .env file
secret_manager = get_secret_manager()
load_dotenv()
load_logging()
logger = getLogger(__package__)

async def generate_user_and_roles(db_async_client):
    roles_feature_service = RolesFeaturesMapService(db_async_client=db_async_client)
    try:
        await roles_feature_service.create_user_and_roles()
        logger.info("Updated db with insert/update Server roles and server admin user")
    except Exception as e:
        logger.exception(f"Unable to create user and roles{e}")

async def generate_system_generated_roles(db_async_client):
    try:
        roles_feature_service = RolesFeaturesMapService(db_async_client=db_async_client)
        await roles_feature_service.generate_or_update_system_generated_project_roles()
        logger.info(f"updated db with system generated project roles")
    except Exception as e:
        logger.exception(f"Unable to update or insert system generated roles..{e}")


async def generate_endpoints_features_table(db_async_client):
    try:
        abs_file_path = Path(__file__).parent/"api"/"endpoints"/"v1"/"access_controls"/"endpoints_features_mappings.json"
        logger.info(f"reading json data from {abs_file_path}")
        endpoints_features_mappings_json = FileUtils.read_from_json(
            str(abs_file_path.absolute()))
        endpoints_feature_mappings_service = EndPointsFeatureMappingsService(
            db_async_client=db_async_client)
        for json_obj in endpoints_features_mappings_json:
            await endpoints_feature_mappings_service.create_or_replace_mapping(
                EndPointsFeatureMappings(**json_obj))
        logger.info(f"updated db with endpoints from json file.")
    except Exception as e:
        logger.exception(f"Unable to update endpoints json table. {e}")

async def generate_app_permisssions_table(db_async_client):
    roles_feature_service = RolesFeaturesMapService(db_async_client=db_async_client)
    try:
        cnt = await roles_feature_service.generate_app_permisssions_table()
        logger.info(f"Updated db with insert/update App Permissions. Number of Permissions created: {cnt}")
    except Exception as e:
        logger.exception(f"Unable to create App Permissions{e}")

async def main():
    db_client_async = get_db_async()
    await generate_user_and_roles(db_client_async)
    await generate_system_generated_roles(db_client_async)
    await generate_endpoints_features_table(db_client_async)
    await generate_app_permisssions_table(db_client_async)

if __name__ == "__main__":
    asyncio.run(main())