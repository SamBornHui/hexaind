import pytest
from motor.motor_asyncio import AsyncIOMotorClient


from app.services.data.datasets_conversion.service import DatasetsConversionsService
from app.services.data.datasets_conversion.schemas import DatasetsConversionRequest, DatasetsConversionFromConfig, \
    DatasetsConversionType
from app.api.endpoints.v1.data.assets_modifications.routes import AssetsModificationsRouter


@pytest.fixture
def mocked_datasets_conversion_service(mocker):
    mocker.patch.object(DatasetsConversionsService, 'convert_dataset', return_value=None)


async def do_nothing(datasets_conversion_request, user_id):
    return


@pytest.mark.asyncio
async def test_convert_dataset_success(mocker, mocked_datasets_conversion_service):
    db_client = AsyncIOMotorClient()
    dataset_conversion_request = DatasetsConversionRequest(
        conversion_type=DatasetsConversionType.TABULAR_PARQUET_TO_CSV,
        from_config=DatasetsConversionFromConfig(dataset_id='test_dataset_id'))

    # Mock ModuleService.save_python_module_helper_async function
    mock_jwt_token = mocker.patch('app.api.endpoints.v1.data.assets_modifications.routes.decodeJWT')
    mock_jwt_token.return_value = {"email": "admin@office.com", "user_id": "new_user_id"}

    mocker.patch('app.api.endpoints.v1.data.assets_modifications.routes.DatasetsConversionsService.convert_dataset',
                 side_effect=do_nothing)
    response = await AssetsModificationsRouter.convert_dataset(
        'site_id',
        'project_id',
        dataset_conversion_request,
        async_client=db_client,
        token=''
    )
    assert response.succeeded is True
