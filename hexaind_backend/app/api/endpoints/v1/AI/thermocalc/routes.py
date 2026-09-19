from fastapi import APIRouter, HTTPException ,status,Depends
from app.services.data.assets.modules.schemas import *
from app.services.data.assets.modules.service import ModuleService
from app.services.AI.thermocalc.schemas import ThermocalcConfig, Features, ScriptFile, ThermocalcGetResultApiParams
from app.services.AI.thermocalc.service import ThermocalcService
from app.core.dao.dao_base import *
import asyncio
from app.core.db.db_utils import get_db_async
import logging, traceback

thermocalc_router = APIRouter(tags=["Thermocalc"])

logger = logging.getLogger(__package__)


class ThermocalcRouter():

    def __init__(self):
        pass
    
    @thermocalc_router.post("/v1/sites/{site_id}/projects/{project_id}/thermocalc/getFeatures")
    async def get_features(site_id: str,
                           project_id: str,
                           module_id: str,
                           client: AsyncIOMotorClient = Depends(get_db_async))-> Features:
        try:
            module_service = ModuleService(db_async_client=client)
            module:Module = await module_service.get_module_record_by_id_async(module_id=module_id)

            thermocalc_service = ThermocalcService(db_async_client=client)
            result = thermocalc_service.verify_and_get_features_from_user_code(file_path=module.module_location.path)

            return result

        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed with exception {e} : {site_id} , {project_id}, {module_id}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to extract the input and output features from user uploaded module due to:{e}"
            )

