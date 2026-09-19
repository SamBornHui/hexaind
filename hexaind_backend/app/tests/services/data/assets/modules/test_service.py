import datetime
from pathlib import Path

import pandas as pd
import pytest
import pytest_mock
from mongomock_motor import AsyncMongoMockClient


from app.services.data.assets.modules.schemas import CodeValidationParameters
from app.services.data.assets.modules.service import ModuleService
from app.services.data.assets.modules.schemas import (
    CustomCodeMetadata,
    Module,
    ModuleType,
    UploadStatus,
    UploadStats,
    ModuleLocation,
    ModuleExtenstion,
    AccessMode,
)


def test_get_files_in_zip(mocker):
    file_path = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/join_module.zip"
    )

    mocked_find_files_in_zip = mocker.patch(
        "app.services.data.assets.modules.service.find_files_in_zip"
    )
    mocked_find_files_in_zip.return_value = ["file1.py", "file2.py"]

    files = ModuleService.get_files_in_zip(file_path)
    assert files == ["file1.py", "file2.py"]
    mocked_find_files_in_zip.assert_called_once_with(Path(file_path))


def test_get_files_in_zip_not_zip(mocker):
    file_path = "not_a_zip.txt"
    with pytest.raises(ValueError):
        ModuleService.get_files_in_zip(file_path)


def test_get_files_in_zip_not_exist(mocker):
    file_path = "nonexistent.zip"
    mocked_find_files_in_zip = mocker.patch(
        "app.services.data.assets.modules.service.find_files_in_zip"
    )
    mocked_find_files_in_zip.return_value = ["file1.py", "file2.py"]

    with pytest.raises(ValueError):
        ModuleService.get_files_in_zip(file_path)


def test_get_metadata(mocker):
    module_location = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/join_module.zip"
    )

    mocked_get_custom_code_metadata = mocker.patch(
        "app.services.data.assets.modules.service.get_custom_code_metadata"
    )
    mocked_get_custom_code_metadata.return_value = CustomCodeMetadata(
        file_names=["test.txt"],
        function_name="test_method",
        entry_file="test.txt",
        function_signature="test",
        function_inputs=[],
        function_outputs=[],
    )

    metadata = ModuleService.get_metadata(module_location)
    assert metadata.function_signature == "test"
    assert metadata.entry_file == "test.txt"
    assert isinstance(metadata, CustomCodeMetadata)
    mocked_get_custom_code_metadata.assert_called_once_with(
        module_location, function_name="hexaind_custom_widget_function"
    )


@pytest.mark.fixme
def test_validate_custom_code_zip(mocker):
    module_location = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/join_module.zip"
    )
    output_csv = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/output.csv"
    )
    validation_inputs = [
        CodeValidationParameters(
            param_name="df1",
            type="<class 'pandas.core.frame.DataFrame'>",
            value="input1.csv",
        ),
        CodeValidationParameters(
            param_name="df2",
            type="<class 'pandas.core.frame.DataFrame'>",
            value="input2.csv",
        ),
        CodeValidationParameters(param_name="how", type="<class 'str'>", value="inner"),
        CodeValidationParameters(
            param_name="column_names", type="<class 'str'>", value="ID"
        ),
    ]
    validation_outputs = [
        CodeValidationParameters(
            param_name="output1",
            type="<class 'pandas.core.frame.DataFrame'>",
            value=output_csv,
        )
    ]

    custom_code_metadata = ModuleService.get_metadata(
        module_location, "hexaind_custom_widget_function"
    )
    ModuleService.validate_custom_code(
        module_location, custom_code_metadata, validation_inputs, validation_outputs
    )


def test_validate_custom_code_not_zip(mocker):
    module_path = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/output.csv"
    )
    custom_code_metadata = CustomCodeMetadata(
        file_names=["test.py"],
        entry_file="module.py",
        function_name="main_function",
        function_signature="(arg1: int, arg2: str) -> List[str]",
        function_inputs=[],
        function_outputs=[],
        validation_request_id="1234",
        is_validated=True,
    )
    validation_inputs = [
        CodeValidationParameters(param_name="arg1", type="<class 'str'>", value="test"),
        CodeValidationParameters(param_name="arg2", type="<class 'str'>", value="test"),
    ]
    validation_outputs = [
        CodeValidationParameters(
            param_name="output1", type="<class 'str'>", value="test"
        )
    ]

    with pytest.raises(NotImplementedError):
        ModuleService.validate_custom_code(
            module_path, custom_code_metadata, validation_inputs, validation_outputs
        )


def test_validate_custom_code_missing_metadata(mocker):
    module_file_path = "module.zip"
    custom_code_metadata = None
    validation_inputs = []
    validation_outputs = []

    with pytest.raises(Exception):
        ModuleService.validate_custom_code(
            module_file_path,
            custom_code_metadata,
            validation_inputs,
            validation_outputs,
        )


def test_validate_custom_code_different_output_length(mocker):
    module_file_path = "module.zip"
    custom_code_metadata = CustomCodeMetadata(
        file_names=["test.txt"],
        entry_file="main.py",
        function_name="main_function",
        function_signature="(arg1: int, arg2: str) -> List[str]",
        function_inputs=[],
        function_outputs=[],
        validation_request_id="1234",
        is_validated=True,
    )
    validation_inputs = [
        CodeValidationParameters(param_name="arg1", type="<class 'str'>", value="test"),
        CodeValidationParameters(param_name="arg2", type="<class 'str'>", value="test"),
    ]
    validation_outputs = []

    with pytest.raises(Exception):
        ModuleService.validate_custom_code(
            module_file_path,
            custom_code_metadata,
            validation_inputs,
            validation_outputs,
        )


def test_run_module_happy_case(mocker):
    mocked_find_files_in_zip = mocker.patch(
        "app.services.data.assets.modules.service.ModulesDao.get_module_record_by_id"
    )
    module_location_ = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/join_module.zip"
    )
    custom_code_metadata = ModuleService.get_metadata(
        module_location_, "hexaind_custom_widget_function"
    )
    mocked_find_files_in_zip.return_value = Module(
        user_id="",
        project_id="",
        site_id="",
        action_id="",
        name="",
        description="",
        module_type=ModuleType.PYTHON,
        upload_status=UploadStatus.COMPLETED,
        upload_stats=UploadStats(percentage="100"),
        metadata=custom_code_metadata,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        module_location=ModuleLocation(
            extension=ModuleExtenstion.ZIP, path=module_location_
        ),
        access_mode=AccessMode.INTERNAL,
        tags=[],
    )

    input1_csv = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/input1.csv"
    )
    input2_csv = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/input2.csv"
    )

    module_service = ModuleService(db_async_client=AsyncMongoMockClient())
    x = module_service.run_module(
        "test_module_id",
        {
            "df1": pd.read_csv(input1_csv),
            "df2": pd.read_csv(input2_csv),
            "column_names": "ID",
            "how": "inner",
        },
        additional_params={
            "RESULTS_DIR": str(
                Path(__file__).parent.parent.parent.parent.parent / "resources"
            ),
            "CURRENT_PROJECT_ID": "project_id",
        },
    )

    assert len(x) == 1
    assert x[0].shape == (2, 4)
