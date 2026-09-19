import logging
from fastapi import APIRouter, Depends, status, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.db.db_utils import get_db_async
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer, decodeJWT
from app.services.data.datasets_conversion.schemas import DatasetsConversionRequest, DatasetsConversionResponse
from app.services.data.datasets_conversion.service import DatasetsConversionsService
from app.api.rbac.end_points_v1_access_control import CheckNameRoute

logger = logging.getLogger(__package__)

assets_modifications_router = APIRouter(tags=["AssetsModifications"], route_class=CheckNameRoute)


class AssetsModificationsRouter:
    def __init__(self):
        pass

    @staticmethod
    @assets_modifications_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets_modification/datasets_conversion",
        response_model=DatasetsConversionResponse,
    )
    async def convert_dataset(site_id, project_id, datasets_conversion_request: DatasetsConversionRequest,
                              async_client: AsyncIOMotorClient = Depends(get_db_async),
                              token: str = '') -> DatasetsConversionResponse:
        try:
            user = decodeJWT(token=token)
            dataset_service = DatasetsConversionsService(db_async_client=async_client)
            await dataset_service.convert_dataset(datasets_conversion_request=datasets_conversion_request,
                                                  user_id=user["user_id"])
            return DatasetsConversionResponse(succeeded=True,
                                              message=f"Completed {datasets_conversion_request.conversion_type} operation successfully.")
        except ValueError as e:
            logger.exception(f"Failed with Exception: {str(e)}")
            return DatasetsConversionResponse(succeeded=False, message=str(e))
        except Exception as e:
            logger.exception(f"Failed with Exception: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to convert given dataset, {e}"
            )


assets_modifications_obj = AssetsModificationsRouter()