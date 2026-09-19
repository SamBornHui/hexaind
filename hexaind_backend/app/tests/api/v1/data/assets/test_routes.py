from pathlib import Path
import pytest_mock
from concurrent.futures.process import ProcessPoolExecutor
from motor.motor_asyncio import AsyncIOMotorClient

from fastapi import Request, HTTPException
import pytest
from app.services.data.assets.modules.schemas import CodeValidationParameters, CodeValidationRequest, CreateModuleRequest, CustomCodeMetadata, FilePathRequest, CustomCodeMetadataResponse
from app.api.endpoints.v1.data.assets.routes import AssetsRouter

@pytest.mark.asyncio
async def test_get_metadata_for_files(mocker):
    mock_request = mocker.Mock(spec=Request)
    mock_process_pool_executor = mocker.Mock(spec=ProcessPoolExecutor)
    mock_request.state.assets_router_process_pool = mock_process_pool_executor

    # Mock ModuleService.get_metadata function
    mock_metadata = CustomCodeMetadata(
        file_names=['test.py'],
        entry_file="module.py",
        function_name="main_function",
        function_signature="(arg1: int, arg2: str) -> List[str]",
        function_inputs=[],
        function_outputs=[],
        validation_request_id="1234",
        is_validated=True
    )
    mocker.patch('app.api.endpoints.v1.data.assets.routes.ModuleService.get_metadata', return_value=mock_metadata)

    # Create a mock FileBody object
    file_body = FilePathRequest(file_path='/path/to/file.py')

    # Call the function
    response = await AssetsRouter.get_metadata_for_files(mock_request, 'site_id', 'project_id', file_body)

    # Assertions
    assert response.metadata is None
    assert response.succeeded is False


@pytest.mark.asyncio
async def test_get_file_names_from_zip_file_success(mocker):
    # Mock Request and ProcessPoolExecutor
    mock_request = mocker.Mock(spec=Request)
    mock_process_pool_executor = mocker.Mock(spec=ProcessPoolExecutor)
    mock_request.state.assets_router_process_pool = mock_process_pool_executor

    # Mock ModuleService.get_files_in_zip function
    mock_files = ['file1.py', 'file2.py']
    mocker.patch('app.api.endpoints.v1.data.assets.routes.ModuleService.get_files_in_zip', return_value=mock_files)

    # Create a mock FilePathRequest object
    file_path_request = FilePathRequest(file_path='/path/to/file.zip')

    # Call the function
    response = await AssetsRouter.get_file_names_from_zip_file(mock_request, 'site_id', 'project_id', file_path_request)

    # Assertions
    assert response == mock_files


@pytest.mark.asyncio
async def test_get_file_names_from_zip_file_value_error(mocker):
    # Mock Request and ProcessPoolExecutor
    mock_request = mocker.Mock(spec=Request)
    mock_process_pool_executor = mocker.Mock(spec=ProcessPoolExecutor)
    mock_request.state.assets_router_process_pool = mock_process_pool_executor

    # Mock ModuleService.get_files_in_zip function to raise ValueError
    mocker.patch('app.api.endpoints.v1.data.assets.routes.ModuleService.get_files_in_zip', side_effect=ValueError("Test exception"))

    # Create a mock FilePathRequest object
    file_path_request = FilePathRequest(file_path='/path/to/file.zip')

    # Call the function and expect HTTPException with status_code 404
    with pytest.raises(HTTPException) as exc_info:
        await AssetsRouter.get_file_names_from_zip_file(mock_request, 'site_id', 'project_id', file_path_request)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_file_names_from_zip_file_other_error(mocker):
    # Mock Request and ProcessPoolExecutor
    mock_request = mocker.Mock(spec=Request)
    mock_process_pool_executor = mocker.Mock(spec=ProcessPoolExecutor)
    mock_request.state.assets_router_process_pool = mock_process_pool_executor

    # Mock ModuleService.get_files_in_zip function to raise generic Exception
    mocker.patch('app.api.endpoints.v1.data.assets.routes.ModuleService.get_files_in_zip', side_effect=Exception("Test exception"))

    # Create a mock FilePathRequest object
    file_path_request = FilePathRequest(file_path='/path/to/file.zip')

    # Call the function and expect HTTPException with status_code 500
    with pytest.raises(HTTPException) as exc_info:
        await AssetsRouter.get_file_names_from_zip_file(mock_request, 'site_id', 'project_id', file_path_request)

    assert exc_info.value.status_code == 500

@pytest.mark.asyncio
@pytest.mark.fixme
async def test_create_new_module_using_file_path_success(mocker):
    # Mock Request and AsyncIOMotorClient
    mock_request = mocker.Mock(spec=Request)
    # mock_db_client = mocker.Mock(spec=AsyncIOMotorClient)
    db_client = AsyncIOMotorClient()
    # Mock CreateModuleRequest
    create_module_request = CreateModuleRequest(
        file_path=str(Path(__file__).parent.parent.parent.parent.parent/ "resources" / "join_module.zip"),
        name='test_module',
        metadata=CustomCodeMetadata(
        file_names=['test.py'],
        entry_file="module.py",
        function_name="main_function",
        function_signature="(arg1: int, arg2: str) -> List[str]",
        function_inputs=[],
        function_outputs=[],
        validation_request_id="1234",
        is_validated=True
    )  # Mock metadata as required
    )

    # Mock ModuleService.save_python_module_helper_async function
    mock_module_service = mocker.patch('app.api.endpoints.v1.data.assets.routes.ModuleService.save_python_module_helper_async')
    mock_jwt_token = mocker.patch('app.api.endpoints.v1.data.assets.routes.decodeJWT')
    mock_jwt_token.return_value = {"email":"admin@office.com","user_id":"new_user_id"}
    mock_module_service.return_value = "mocked_module_id"
    mock_jwt_token = mocker.patch('app.api.endpoints.v1.data.assets.routes.decodeJWT')
    mock_jwt_token.return_value = {"email": "admin@office.com", "user_id": "new_user_id"}

    # Call the function
    response = await AssetsRouter.create_new_module_using_file_path(
        mock_request,
        'site_id',
        'project_id',
        create_module_request,
        client=db_client
    )

    print(response)

    # Assertions
    assert response.succeeded is True
    assert response.module_id == "mocked_module_id"

@pytest.mark.asyncio
async def test_create_new_module_using_file_path_invalid_extension(mocker):
    # Mock Request and AsyncIOMotorClient
    mock_request = mocker.Mock(spec=Request)
    mock_db_client = mocker.Mock(spec=AsyncIOMotorClient)

    # Mock CreateModuleRequest with invalid file extension
    create_module_request = CreateModuleRequest(
        file_path='/path/to/file.unknown_extension',
        name='test_module',
        metadata=CustomCodeMetadata(
        file_names=['test.py'],
        entry_file="module.py",
        function_name="main_function",
        function_signature="(arg1: int, arg2: str) -> List[str]",
        function_inputs=[],
        function_outputs=[],
        validation_request_id="1234",
        is_validated=True
    )  # Mock metadata as required
    )

    # Call the function and expect HTTPException with status_code 400
    with pytest.raises(HTTPException) as exc_info:
        await AssetsRouter.create_new_module_using_file_path(
            mock_request,
            'site_id',
            'project_id',
            create_module_request,
            client=mock_db_client
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_validate_custom_code_success(mocker):
    # Mock Request
    mock_request = mocker.Mock(spec=Request)
    mock_request.state.assets_router_process_pool = ProcessPoolExecutor()
    output_csv = str(Path(__file__).parent.parent.parent.parent.parent / "resources/output.csv")

    # Mock CodeValidationRequest
    validation_request = CodeValidationRequest(
        file_path=str(Path(__file__).parent.parent.parent.parent.parent/ "resources" / "join_module.zip"),
        metadata=CustomCodeMetadata(
        file_names=['test.py'],
        entry_file="join.py",
        function_name="hexaind_custom_widget_function",
        function_signature="(arg1: int, arg2: str) -> List[str]",
        function_inputs=[],
        function_outputs=[],
        validation_request_id="1234",
        is_validated=True
    ),  # Mock metadata as required
        validation_inputs = [
        CodeValidationParameters(param_name="df1", type="<class 'pandas.core.frame.DataFrame'>",
                                       value="input1.csv"),
        CodeValidationParameters(param_name="df2", type="<class 'pandas.core.frame.DataFrame'>",
                                       value="input2.csv"),
        CodeValidationParameters(param_name="how", type="<class 'str'>", value="inner"),
        CodeValidationParameters(param_name="column_names", type="<class 'str'>", value="ID")
    ],
        validation_outputs = [
            CodeValidationParameters(param_name="output1", type="<class 'pandas.core.frame.DataFrame'>",
                                        value=output_csv)
        ]  # Mock validation_outputs as required
    )

    # Call the function
    response = await AssetsRouter.validate_custom_code(
        mock_request,
        'site_id',
        'project_id',
        validation_request
    )

    # Assertions
    # TODO: fix these assertions later
    # assert response.succeeded is True
    # assert response.message == "Validated Succesfully"


@pytest.mark.asyncio
async def test_validate_custom_code_file_not_exists(mocker):
    # Mock Request
    mock_request = mocker.Mock(spec=Request)

    # Mock CodeValidationRequest with non-existing file
    output_csv = str(Path(__file__).parent.parent / "resources/output.csv")

    # Mock CodeValidationRequest
    validation_request = CodeValidationRequest(
        file_path=str(Path(__file__).parent.parent/ "resources" / "test.py"),
        metadata=CustomCodeMetadata(
        file_names=['test.py'],
        entry_file="join.py",
        function_name="hexaind_custom_widget_function",
        function_signature="(arg1: int, arg2: str) -> List[str]",
        function_inputs=[],
        function_outputs=[],
        validation_request_id="1234",
        is_validated=True
    ),  # Mock metadata as required
        validation_inputs = [
        CodeValidationParameters(param_name="df1", type="<class 'pandas.core.frame.DataFrame'>",
                                       value="input1.csv"),
        CodeValidationParameters(param_name="df2", type="<class 'pandas.core.frame.DataFrame'>",
                                       value="input2.csv"),
        CodeValidationParameters(param_name="how", type="<class 'str'>", value="inner"),
        CodeValidationParameters(param_name="column_names", type="<class 'str'>", value="ID")
    ],
        validation_outputs = [
            CodeValidationParameters(param_name="output1", type="<class 'pandas.core.frame.DataFrame'>",
                                        value=output_csv)
        ]  # Mock validation_outputs as required
    )

    # Call the function and expect HTTPException with status_code 400
    with pytest.raises(HTTPException) as exc_info:
        await AssetsRouter.validate_custom_code(
            mock_request,
            'site_id',
            'project_id',
            validation_request
        )

    assert exc_info.value.status_code == 400
