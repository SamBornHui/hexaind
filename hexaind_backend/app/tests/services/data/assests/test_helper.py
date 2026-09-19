from pathlib import Path
import pytest
import pytest_mock
import tempfile
import os
import pandas as pd

#ToDo: Add this file in correct path and change this relative imports to absolute

from .....core.schemas.action_result import ActionResult, FailureActionResult, DatasetActionResult
from .....services.data.assets.datasets.service import DatasetsService
from .....services.data.assets.modules.helper import PandasDataFrameConverter, StringConverter, JsonConverter, \
    ConversionHelper
from .....core.services.action.schemas import WidgetResultResponse, ActionResultType, StringActionResult
from .....services.data.assets.datasets.schemas import DatasetType
from .....services.data.assets.modules.schemas import CodeValidationParameters
from .....services.workflows.designer.schemas import CustomFunctionAcceptedPythonClasses, CustomFunctionParameters
from .....utils.dataset_utils import generate_dataset_object
from mongomock import MongoClient
from mongomock_motor import AsyncMongoMockClient

@pytest.fixture
def mocked_sync_client():
    return MongoClient()

@pytest.fixture
def sample_widget_result_response():
    # Create a sample WidgetResultResponse object
    return WidgetResultResponse(
        result_type=ActionResultType.DATASET,
        result_value=generate_dataset_object(str(Path(__file__).parent.parent.parent.parent/"resources/penguin.csv"))
    )

def test_from_method_with_valid_input(sample_widget_result_response):
    # Test the from_ method with valid input
    dask_data_frame = PandasDataFrameConverter.from_(sample_widget_result_response)
    assert isinstance(dask_data_frame, pd.DataFrame)

def test_from_method_with_invalid_input():
    # Test the from_ method with invalid input
    invalid_widget_result_response = WidgetResultResponse(
        result_type=ActionResultType.FAILURE,
        result_value=FailureActionResult(error_code="400", error_description="test failure")
    )
    with pytest.raises(ValueError):
        PandasDataFrameConverter.from_(invalid_widget_result_response)

@pytest.mark.fixme
def test_to_method_with_valid_input():
    # Test the to_ method with valid input
    with tempfile.TemporaryDirectory() as tmpdir:
        file_prefix = ''
        sample_data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
        df = pd.DataFrame(sample_data)
        result = PandasDataFrameConverter.to_(df, file_prefix=file_prefix)
        assert os.path.exists(result.dataset_location[0].path)

def test_to_method_with_invalid_input():
    # Test the to_ method with invalid input
    invalid_data = "not_a_dataframe"
    with pytest.raises(ValueError):
        PandasDataFrameConverter.to_(invalid_data)


@pytest.fixture
def sample_widget_result_response_string():
    # Create a sample WidgetResultResponse object
    return WidgetResultResponse(
        result_type=ActionResultType.STRING,
        result_value=StringActionResult(string_value="Sample String")
    )

def test_from_method_with_valid_input_string(sample_widget_result_response_string):
    # Test the from_ method with valid input
    result = StringConverter.from_(sample_widget_result_response_string)
    assert result == "Sample String"

def test_from_method_with_invalid_input_string():
    # Test the from_ method with invalid input
    invalid_widget_result_response = WidgetResultResponse(
        result_type=ActionResultType.FAILURE,
        result_value=FailureActionResult(error_code="400", error_description="test failure")
    )
    with pytest.raises(ValueError):
        StringConverter.from_(invalid_widget_result_response)

def test_to_method_with_valid_input_string():
    # Test the to_ method with valid input
    result = StringConverter.to_("Sample String", action_result_type=ActionResultType.STRING)
    assert isinstance(result, StringActionResult)
    assert result.string_value == "Sample String"

def test_to_method_with_invalid_input_string():
    # Test the to_ method with invalid input
    invalid_data = 123  # Not a string
    with pytest.raises(ValueError):
        StringConverter.to_(invalid_data)


@pytest.fixture
def sample_widget_result_response_json():
    # Create a sample WidgetResultResponse object
    return WidgetResultResponse(
        result_type=ActionResultType.DATASET,
        result_value=generate_dataset_object(str(Path(__file__).parent.parent.parent.parent/"resources/penguin.json"), dataset_type=DatasetType.JSON)

    )

@pytest.mark.fixme
def test_from_method_with_valid_input_json(sample_widget_result_response_json):
    # Test the from_ method with valid input for JSON dataset
    with pytest.raises(NotImplementedError):
        JsonConverter.from_(sample_widget_result_response_json)

def test_from_method_with_invalid_input_json():
    # Test the from_ method with invalid input for JSON dataset
    invalid_widget_result_response = WidgetResultResponse(
        result_type=ActionResultType.FAILURE,
        result_value=FailureActionResult(error_code="400", error_description="test failure")
    )
    with pytest.raises(ValueError):
        JsonConverter.from_(invalid_widget_result_response)

def test_to_method_with_valid_input_json():
    # Test the to_ method with valid input for JSON dataset
    with pytest.raises(NotImplementedError):
        JsonConverter.to_(data={}, action_result_type=ActionResultType.DATASET)

def test_to_method_with_invalid_input_json():
    # Test the to_ method with invalid input for JSON dataset
    invalid_data = {}  # Not a valid JSON dataset
    with pytest.raises(NotImplementedError):
        JsonConverter.to_(invalid_data)


@pytest.fixture
def sample_validation_inputs_conversion():
    # Create sample CustomCodeValidationParameters objects
    return [
        CodeValidationParameters(
            param_name="param1",
            type=CustomFunctionAcceptedPythonClasses.STRING,
            value="Sample String"
        ),
        CodeValidationParameters(
            param_name="param2",
            type=CustomFunctionAcceptedPythonClasses.PANDAS,
            value=str(Path(__file__).parent.parent.parent.parent/"resources/penguin.csv")
        )
    ]

@pytest.mark.fixme
def test_convert_validation_parameters_to_kwargs_conversion(sample_validation_inputs_conversion):
    # Test the convert_validation_parameters_to_kwargs method for conversion
    kwargs = ConversionHelper.convert_validation_parameters_to_kwargs(sample_validation_inputs_conversion)
    assert "param1" in kwargs
    assert "param2" in kwargs
    assert isinstance(kwargs["param1"], str)
    assert isinstance(kwargs["param2"], pd.DataFrame)

def test_convert_from_widget_result_response_conversion():
    # Test the convert_from_widget_result_response method for conversion
    widget_result_response = WidgetResultResponse(
        result_type=ActionResultType.STRING,
        result_value=StringActionResult(string_value="Sample String")
    )
    result = ConversionHelper.convert_from_widget_result_response(
        widget_result_response, CustomFunctionAcceptedPythonClasses.STRING, {})

    assert isinstance(result, str)
    assert result == "Sample String"

def test_convert_from_custom_function_parameters_conversion_string():
    custom_function_parameter = CustomFunctionParameters(
        type=CustomFunctionAcceptedPythonClasses.STRING,
        arg_name="random",
        value=ActionResult(type=ActionResultType.STRING,result=StringActionResult(string_value="Sample String"))
    )
    result = ConversionHelper.convert_from_custom_function_parameters(custom_function_parameter, None, {})
    assert "Sample String" == result

def test_convert_from_custom_function_parameters_conversion_pd_dataframe(mocker, mocked_sync_client):
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)
    datasets_service = DatasetsService(db_sync_client=mocked_sync_client, db_async_client=AsyncMongoMockClient())
    dataset = generate_dataset_object(str(Path(__file__).parent.parent.parent.parent / "resources/penguin.csv"))
    results = mocked_sync_client.Hexaind.datasets.insert_one(dataset.model_dump())
    custom_function_parameter = CustomFunctionParameters(
        type=CustomFunctionAcceptedPythonClasses.PANDAS,
        arg_name="random",
        value=ActionResult(type=ActionResultType.DATASET,
                           result=DatasetActionResult(dataset_id=str(results.inserted_id)))
    )
    result = ConversionHelper.convert_from_custom_function_parameters(custom_function_parameter, datasets_service, {})

    assert isinstance(result, pd.DataFrame)
    assert result.shape == pd.read_csv(str(Path(__file__).parent.parent.parent.parent / "resources/penguin.csv")).shape

def test_convert_to_action_result_type_conversion():
    # Test the convert_to_action_result_type method for conversion
    data = "Sample Data"
    result = ConversionHelper.convert_to_action_result_type(
        data, ActionResultType.STRING, CustomFunctionAcceptedPythonClasses.STRING, {})
    assert isinstance(result, StringActionResult)
    assert result.string_value == "Sample Data"
