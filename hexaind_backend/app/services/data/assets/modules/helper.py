from email.policy import strict
import json
import logging
from app.services.data.assets.custom_python_support.service import TextCPWDataset
from app.services.data.assets.modules.schemas import CodeValidationParameters
from app.services.data.assets.datasets.schemas import DatasetType, DatasetLocation
from app.core.services.action.schemas import WidgetResultResponse, StringActionResult
from app.core.schemas.action_result import (
    FileActionResult,
    IntegerActionResult,
    FloatActionResult,
    ListOffloatsActionResult,
    ListOfIntegersActionResult,
    ListOfStringsActionResult,
    DictionaryActionResult,
)
from app.services.data.assets.datasets.service import DatasetsService
from app.services.workflows.designer.schemas import CustomFunctionAcceptedPythonClasses
from app.services.workflows.designer.schemas import (
    ActionResultType,
    CustomFunctionParameters,
)

from app.utils.dataset_utils import generate_dataset_object

from app.core.tabular.file_utils import read_file
from app.config.env_vars import environment, cpw_constants
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import pandas as pd
import ast
from abc import ABC, abstractmethod
from typing import List, Any, Dict
from app.utils.file_utils import FileUtils

logger = logging.getLogger(__package__)


class Converters(ABC):

    @classmethod
    @abstractmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def to_(cls, data, action_result_type, **kwargs):
        pass


class TextCPWDatasetConverter(Converters):
    @classmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):
        if widget_result_response.result_type == ActionResultType.DATASET:
            if widget_result_response.result_value.dataset_type == DatasetType.TEXT:
                dataset_locations = [
                    Path(location.path)
                    for location in widget_result_response.result_value.dataset_location
                ]
                return TextCPWDataset(
                    dataset_id=widget_result_response.result_value.id,
                    dataset_file_paths=dataset_locations,
                )
        raise ValueError(f"Invalid inputs for converter : {cls.__name__}")

    @classmethod
    def to_(cls, data, action_result_type=ActionResultType.DATASET, **kwargs):
        if (
            isinstance(data, TextCPWDataset)
            and action_result_type == ActionResultType.DATASET
        ):
            file_prefix = (
                kwargs["file_prefix"]
                if kwargs["file_prefix"]
                else environment.datasets_folder
            )
            file_prefix_path = Path(file_prefix)
            file_prefix_path.mkdir(parents=True, exist_ok=True)

            if len(data.dataset_file_paths) != 1:
                raise NotImplementedError(
                    f"Implementation only done for file_paths of one size"
                )

            kwargs["file_path"] = str(
                file_prefix_path / f"{uuid4()}_{data.dataset_file_paths[0].name}"
            )
            # copying file to run folder and created data set with it
            FileUtils.create_deep_copy_file_or_folder(
                str(data.dataset_file_paths[0]), kwargs["file_path"]
            )
            return generate_dataset_object(dataset_type=DatasetType.TEXT, **kwargs)
        raise ValueError(f"Invalid inputs for converter : {cls.__name__}")


class IntegerConverter(Converters):

    @classmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):
        if widget_result_response.result_type == ActionResultType.INTEGER:
            return int(widget_result_response.result_value.integer_value)
        raise ValueError(f"Invalid inputs for converter: {cls.__name__}")

    @classmethod
    def to_(cls, data, action_result_type=ActionResultType.INTEGER, **kwargs):
        if isinstance(data, int) and action_result_type == ActionResultType.INTEGER:
            return IntegerActionResult(integer_value=data)
        raise ValueError(f"Invalid inputs for converter: {cls.__name__}")


class FloatConverter(Converters):

    @classmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):
        if widget_result_response.result_type == ActionResultType.FLOAT:
            return float(widget_result_response.result_value.float_value)
        raise ValueError(f"Invalid inputs for converter: {cls.__name__}")

    @classmethod
    def to_(cls, data, action_result_type=ActionResultType.FLOAT, **kwargs):
        if isinstance(data, float) and action_result_type == ActionResultType.FLOAT:
            return FloatActionResult(float_value=data)
        raise ValueError(f"Invalid inputs for converter: {cls.__name__}")


class ListIntConverter(Converters):

    @classmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):
        if widget_result_response.result_type == ActionResultType.INTEGERS_LIST:
            return list(
                map(int, widget_result_response.result_value.integers_list_value)
            )
        raise ValueError(f"Invalid inputs for converter: {cls.__name__}")

    @classmethod
    def to_(cls, data, action_result_type=ActionResultType.INTEGERS_LIST, **kwargs):
        if (
            isinstance(data, list)
            and all(isinstance(item, int) for item in data)
            and action_result_type == ActionResultType.INTEGERS_LIST
        ):
            return ListOfIntegersActionResult(integers_list_value=data)
        raise ValueError(f"Invalid inputs for converter: {cls.__name__}")


class ListFloatConverter(Converters):

    @classmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):
        if widget_result_response.result_type == ActionResultType.FLOATS_LIST:
            return list(
                map(float, widget_result_response.result_value.floats_list_value)
            )
        raise ValueError(f"Invalid inputs for converter: {cls.__name__}")

    @classmethod
    def to_(cls, data, action_result_type=ActionResultType.FLOATS_LIST, **kwargs):
        if (
            isinstance(data, list)
            and all(isinstance(item, float) for item in data)
            and action_result_type == ActionResultType.FLOATS_LIST
        ):
            return ListOffloatsActionResult(floats_list_value=data)
        raise ValueError(f"Invalid inputs for converter: {cls.__name__}")


class ListStrConverter(Converters):

    @classmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):
        if widget_result_response.result_type == ActionResultType.STRINGS_LIST:
            return list(widget_result_response.result_value.strings_list_value)
        raise ValueError(f"Invalid inputs for converter: {cls.__name__}")

    @classmethod
    def to_(cls, data, action_result_type=ActionResultType.STRINGS_LIST, **kwargs):
        if (
            isinstance(data, list)
            and all(isinstance(item, str) for item in data)
            and action_result_type == ActionResultType.STRINGS_LIST
        ):
            return ListOfStringsActionResult(strings_list_value=data)
        raise ValueError(f"Invalid inputs for converter: {cls.__name__}")


class DictConverter(Converters):
    output_dir = environment.wf_action_results_folder  # Directory to save JSON files

    @classmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):
        if widget_result_response.result_type == ActionResultType.DICTIONARY:
            if widget_result_response.result_value.dict_file_path:
                with open(
                    widget_result_response.result_value.dict_file_path, "r"
                ) as file:
                    data = json.load(file)
                    # if type(data) != dict:
                    #     data = ast.literal_eval(data)
                return data
            else:
                return ast.literal_eval(widget_result_response.result_value.dict_value)

        elif widget_result_response.result_type == ActionResultType.DATASET:
            logger.info("in dataset case from dict convertor")
            logger.info(
                f"location :   {widget_result_response.result_value.dataset_location}"
            )
            if widget_result_response.result_value.dataset_location[0].path.endswith(
                ("xlsx", "xls")
            ):
                return pd.read_excel(
                    widget_result_response.result_value.dataset_location[0].path,
                    sheet_name=None,
                )

        raise ValueError(f"Invalid inputs for dict converter: {cls.__name__}")

    @classmethod
    def to_(
        cls,
        data,
        action_result_type=ActionResultType.DICTIONARY,
        **kwargs,
    ):
        if isinstance(data, dict) and action_result_type == ActionResultType.DICTIONARY:
            file_name_json = cls.output_dir / f"{uuid4().hex}.json"

            # Convert DataFrame objects to JSON-compatible formats
            json_data = {}
            for key, value in data.items():
                if isinstance(value, pd.DataFrame):
                    json_data[key] = value.to_dict(
                        orient="records"
                    )  # Convert DataFrame to list of dicts
                else:
                    json_data[key] = value

            # Dump the entire dictionary to JSON
            with open(file_name_json, "w") as file:
                json.dump(json_data, file, indent=4)

            return DictionaryActionResult(dict_value="", dict_file_path=str(file_name_json))

        raise ValueError(f"Invalid inputs for converter: {cls.__name__}")


class PandasDataFrameConverter(Converters):

    @classmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):

        if widget_result_response.result_type == ActionResultType.DATASET:
            if widget_result_response.result_value.dataset_type == DatasetType.TABULAR:
                # dask_data_frame = read_file(widget_result_response.result_value.dataset_location[0].path)
                # return dask_data_frame.compute()
                # TODO: changing to pd from dask suspecting issues with multithreading.(jira:HEXAIND-8731)
                if len(widget_result_response.result_value.dataset_location) != 1:
                    raise Exception(
                        f"Expecting only one dataset location value to convert to pandas dataframe,"
                        + f" got {len(widget_result_response.result_value.dataset_location)}"
                    )

                if (
                    str(widget_result_response.result_value.dataset_location[0].path)
                    .lower()
                    .endswith("csv")
                ):
                    return pd.read_csv(
                        widget_result_response.result_value.dataset_location[0].path
                    )

                elif (
                    str(widget_result_response.result_value.dataset_location[0].path)
                    .lower()
                    .endswith(("xls", "xlsx"))
                ):
                    return pd.read_excel(
                        widget_result_response.result_value.dataset_location[0].path,
                        sheet_name=None,
                    )

                else:
                    return pd.read_parquet(
                        widget_result_response.result_value.dataset_location[0].path
                    )

        raise ValueError(f"Invalid inputs for converter : {cls.__name__}")

    @classmethod
    def to_(cls, data, action_result_type=ActionResultType.DATASET, **kwargs):

        if (
            isinstance(data, pd.DataFrame)
            and action_result_type == ActionResultType.DATASET
        ):
            file_prefix = (
                kwargs["file_prefix"]
                if kwargs["file_prefix"]
                else environment.datasets_folder
            )
            file_prefix_path = Path(file_prefix)

            file_prefix_path.mkdir(parents=True, exist_ok=True)
            kwargs["file_path"] = str(file_prefix_path / f"{kwargs['name']}_{uuid4()}.parquet")
            if(data.attrs.get(cpw_constants.data_source_path)):
                try:
                    if not isinstance(data.attrs.get(cpw_constants.data_source_path),str):
                        raise TypeError(f"Invalid Type for {data.attrs.get(cpw_constants.data_source_path)}, expected type : str")
                    original_file_path = Path(data.attrs[cpw_constants.data_source_path])
                    suffix = original_file_path.suffix if original_file_path.is_file() else ""
                    kwargs["file_path"] = str(file_prefix_path / f"{kwargs['name']}_{uuid4()}{suffix}")
                    FileUtils.create_deep_copy_file_or_folder(str(original_file_path),kwargs['file_path'],dirs_exist_ok=True)
                except Exception as e:
                    logger.info(f'Got exception for while handling {data.attrs.get(cpw_constants.data_source_path)} fall back to manual writing flow : {e}')
                    kwargs["file_path"] = str(file_prefix_path / f"{kwargs['name']}_{uuid4()}.parquet")
                    data.to_parquet(kwargs["file_path"], index=False)
            else:                
                data.to_parquet(kwargs["file_path"], index=False)

            # return DatasetsService.save_tabular_dataset_helper_sync(
            #     input_data=kwargs["file_path"],
            #     project_id=kwargs["project_id"],
            #     user_id=kwargs["user_id"],
            #     site_id=kwargs["site_id"],
            #     name=kwargs["name"],
            #     workflow_id=kwargs["workflow_id"],
            #     run_id=kwargs["run_id"],
            #     action_id=kwargs["action_id"],
            # )

            return generate_dataset_object(dataset_type=DatasetType.TABULAR, **kwargs)

        raise ValueError(f"Invalid inputs for converter : {cls.__name__}")


class StringConverter(Converters):

    @classmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):
        if widget_result_response.result_type == ActionResultType.STRING:
            return widget_result_response.result_value.string_value
        raise ValueError(f"Invalid inputs for converter : {cls.__name__}")

    @classmethod
    def to_(cls, data, action_result_type=ActionResultType.STRING, **kwargs):
        if isinstance(data, str) and action_result_type == ActionResultType.STRING:
            return StringActionResult(string_value=data)
        raise ValueError(f"Invalid inputs for converter : {cls.__name__}")
    
class PathsConverters(Converters):

    @classmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):
        if widget_result_response.result_type == ActionResultType.FILE_OR_FOLDER_PATH:
            return Path(widget_result_response.result_value.file_path_value)
        raise ValueError(f"Invalid inputs for converter : {cls.__name__}")

    @classmethod
    def to_(cls, data, action_result_type=ActionResultType.FILE_OR_FOLDER_PATH, **kwargs):
        if isinstance(data, Path) and action_result_type == ActionResultType.FILE_OR_FOLDER_PATH:
            return FileActionResult(file_path_value=str(data))
        raise ValueError(f"Invalid inputs for converter : {cls.__name__}")


class JsonConverter(Converters):

    @classmethod
    def from_(cls, widget_result_response: WidgetResultResponse, **kwargs):
        if widget_result_response.result_type == ActionResultType.DATASET:
            if widget_result_response.result_value.dataset_type == DatasetType.JSON:
                raise NotImplementedError(
                    "Need to implement this to typing.List[pydantic.JSON]"
                )
        raise ValueError(f"Invalid inputs for converter : {cls.__name__}")

    @classmethod
    def to_(cls, data, action_result_type=ActionResultType.DATASET, **kwargs):
        if action_result_type == ActionResultType.DATASET:
            raise NotImplementedError(
                "Need to implement this to typing.List[pydantic.JSON]"
            )
        raise ValueError(f"Invalid inputs for converter : {cls.__name__}")


class ConverterFactory:

    @staticmethod
    def get_converter(type_: str, action_result_type: ActionResultType):

        if (
            type_ == CustomFunctionAcceptedPythonClasses.INTEGER
            and action_result_type == ActionResultType.INTEGER
        ):

            return IntegerConverter()

        elif (
            type_ == CustomFunctionAcceptedPythonClasses.FLOAT
            and action_result_type == ActionResultType.FLOAT
        ):

            return FloatConverter()

        elif (
            type_ == CustomFunctionAcceptedPythonClasses.STRINGS_LIST
            and action_result_type == ActionResultType.STRINGS_LIST
        ):

            return ListStrConverter()

        elif (
            type_ == CustomFunctionAcceptedPythonClasses.FLOATS_LIST
            and action_result_type == ActionResultType.FLOATS_LIST
        ):

            return ListFloatConverter()

        elif (
            type_ == CustomFunctionAcceptedPythonClasses.INTEGERS_LIST
            and action_result_type == ActionResultType.INTEGERS_LIST
        ):
            return ListIntConverter()

        elif (
            type_ == CustomFunctionAcceptedPythonClasses.PANDAS
        ) and action_result_type == ActionResultType.DATASET:
            return PandasDataFrameConverter()

        elif (
            type_ == CustomFunctionAcceptedPythonClasses.STRING
            and action_result_type == ActionResultType.STRING
        ):
            return StringConverter()

        elif (
            type_ == CustomFunctionAcceptedPythonClasses.JSONS
            and action_result_type == ActionResultType.DATASET
        ):
            return JsonConverter()

        elif type_ == CustomFunctionAcceptedPythonClasses.DICTIONARY and (
            action_result_type == ActionResultType.DICTIONARY
            or action_result_type == ActionResultType.DATASET
        ):
            return DictConverter()

        elif (
            type_ == CustomFunctionAcceptedPythonClasses.TEXT_CPW_DATASET
            and action_result_type == ActionResultType.DATASET
        ):
            return TextCPWDatasetConverter()
        
        elif (
            type_ == CustomFunctionAcceptedPythonClasses.PATHLIB_PATH or type_ == CustomFunctionAcceptedPythonClasses.STRING
            and action_result_type == ActionResultType.FILE_OR_FOLDER_PATH
        ):

            return PathsConverters()

        raise ValueError(
            f"Unable to find converter for given {type_} and {action_result_type}"
        )


class ConversionHelper:

    @staticmethod
    def _convert_validation_parameters_to_widget_result_responses_(
        custom_code_validation_param: CodeValidationParameters,
    ):
        if (
            custom_code_validation_param.type
            == CustomFunctionAcceptedPythonClasses.STRING
        ):
            widget_result_response = WidgetResultResponse(
                result_type=ActionResultType.STRING,
                result_value=StringActionResult(
                    string_value=custom_code_validation_param.value
                ),
            )
            return widget_result_response
        elif (
            custom_code_validation_param.type
            == CustomFunctionAcceptedPythonClasses.PANDAS
        ):
            dataset_location = DatasetLocation(
                isfolder=False,
                size="2",
                extension=".csv",
                path=custom_code_validation_param.value,
                last_modified_by=None,
                last_modified_at=datetime.now(timezone.utc),
            )
            widget_result_response = WidgetResultResponse(
                result_type=ActionResultType.DATASET,
                result_value=generate_dataset_object(dataset_location=dataset_location),
            )
            return widget_result_response

        elif (
            custom_code_validation_param.type
            == CustomFunctionAcceptedPythonClasses.TEXT_CPW_DATASET
        ):
            # TODO: for now assuming custom_code_validation_param.value for text cpw also contain file path
            #  in future its best if we validate with existing dataset id's.
            dataset_location = DatasetLocation(
                isfolder=False,
                size="2",
                extension=".txt",  # hardcoding to .txt, it might not cause issue.
                path=custom_code_validation_param.value,
                last_modified_by=None,
                last_modified_at=datetime.now(),
            )
            widget_result_response = WidgetResultResponse(
                result_type=ActionResultType.DATASET,
                result_value=generate_dataset_object(
                    dataset_type=DatasetType.TEXT, dataset_location=dataset_location
                ),
            )
            return widget_result_response

        else:
            raise Exception("Invalid type found for custom code validation parameter")

    @staticmethod
    def convert_validation_parameters_to_kwargs(
        validation_inputs: List[CodeValidationParameters],
    ) -> Dict[str, Any]:

        widget_result_responses = {}
        types_map = {}
        # Convert validation inputs to widget result responses
        for validation_input in validation_inputs:
            converted_input = ConversionHelper._convert_validation_parameters_to_widget_result_responses_(
                validation_input
            )
            widget_result_responses[validation_input.param_name] = converted_input
            types_map[validation_input.param_name] = validation_input.type
        # Convert widget result responses to kwargs (allowed python types)
        kwargs = {
            arg_name: ConversionHelper.convert_from_widget_result_response(
                widget_result_responses.get(arg_name), types_map.get(arg_name), {}
            )
            for arg_name in widget_result_responses
        }
        return kwargs

    @staticmethod
    def convert_from_widget_result_response(widget_result_response, type_, kwargs):
        converter = ConverterFactory.get_converter(
            type_=type_, action_result_type=widget_result_response.result_type
        )
        return converter.from_(widget_result_response, **kwargs)

    @staticmethod
    def convert_from_custom_function_parameters(
        custom_function_parameter: CustomFunctionParameters,
        datasets_service: DatasetsService,
        kwargs: dict,
    ):

        action_result = (
            custom_function_parameter.value
            if custom_function_parameter.value
            else custom_function_parameter.default_value
        )

        if (
            custom_function_parameter.type == CustomFunctionAcceptedPythonClasses.STRING
            or custom_function_parameter.type
            == CustomFunctionAcceptedPythonClasses.INTEGER
            or custom_function_parameter.type
            == CustomFunctionAcceptedPythonClasses.FLOAT
            or custom_function_parameter.type
            == CustomFunctionAcceptedPythonClasses.INTEGERS_LIST
            or custom_function_parameter.type
            == CustomFunctionAcceptedPythonClasses.FLOATS_LIST
            or custom_function_parameter.type
            == CustomFunctionAcceptedPythonClasses.STRINGS_LIST
            or custom_function_parameter.type
            == CustomFunctionAcceptedPythonClasses.DICTIONARY
            or custom_function_parameter.type
            == CustomFunctionAcceptedPythonClasses.PATHLIB_PATH
        ):

            widget_response_type = WidgetResultResponse(
                result_type=action_result.type, result_value=action_result.result
            )

        elif (
            custom_function_parameter.type == CustomFunctionAcceptedPythonClasses.PANDAS
        ):
            dataset = datasets_service.get_dataset_by_id_sync(
                action_result.result.dataset_id
            )
            widget_response_type = WidgetResultResponse(
                result_type=action_result.type, result_value=dataset
            )
        else:
            raise NotImplementedError("Not implemented for other types")

        return ConversionHelper.convert_from_widget_result_response(
            widget_response_type, custom_function_parameter.type, kwargs
        )

    @staticmethod
    def convert_to_action_result_type(data, action_result_type, type_, kwargs):
        converter = ConverterFactory.get_converter(
            type_=type_, action_result_type=action_result_type
        )
        return converter.to_(data, action_result_type=action_result_type, **kwargs)


class Comparator(ABC):
    @staticmethod
    @abstractmethod
    def compare(actual, expected):
        pass


class TextCPWDatasetDataComparator(Comparator):
    @staticmethod
    def compare(actual, expected):
        file_paths1 = actual.dataset_file_paths
        file_paths2 = expected.dataset_file_paths
        if len(file_paths1) != len(file_paths2):
            return False
        for file_path1, file_path2 in zip(file_paths1, file_paths2):
            diff = FileUtils.file_diff(
                str(file_path1.absolute()), str(file_path2.absolute())
            )
            if diff:
                print(diff)
                return False
        return True


class PandasComparator(Comparator):
    @staticmethod
    def compare(actual, expected):
        return (actual == expected).all().all()


class StringComparator(Comparator):
    @staticmethod
    def compare(actual, expected):
        return actual == expected


class ComparatorFactory:
    @staticmethod
    def get_comparator(type):
        if type == CustomFunctionAcceptedPythonClasses.PANDAS:
            return PandasComparator()
        elif type == CustomFunctionAcceptedPythonClasses.STRING:
            return StringComparator()
        elif type == CustomFunctionAcceptedPythonClasses.TEXT_CPW_DATASET:
            return TextCPWDatasetDataComparator()
        else:
            raise Exception("Unknown type for comparison.")


class ComparisonHelper:
    @staticmethod
    def compare(type, actual, expected):
        try:
            comparator = ComparatorFactory.get_comparator(type)
            return comparator.compare(actual, expected)
        except Exception as e:
            raise Exception(f"Comparison failed: {e}")
