from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class StringActionResult(BaseModel):
    string_value: str


class FileActionResult(BaseModel):
    file_path_value: str


class ListOfStringsActionResult(BaseModel):
    strings_list_value: list[str]


class IntegerActionResult(BaseModel):
    integer_value: int


class ListOfIntegersActionResult(BaseModel):
    integers_list_value: list[int]


class FloatActionResult(BaseModel):
    float_value: float


class ListOffloatsActionResult(BaseModel):
    floats_list_value: list[float]


class JSONActionResult(BaseModel):
    json_value: dict


class DictionaryActionResult(BaseModel): #do not add  default values here, instead prefer them in the service or other fucntions where we are returing the ActionResult

    dict_value: str # basically to avoid confusion we are showing/asking users the raw python dictionary as STRING (use case CPW) (we can convert dict_str to dict using "ast.literal_eval(raw_dict_string)")
    dict_file_path: Optional[str] = None


class FailureActionResult(BaseModel):
    error_code: str
    error_description: str


class DatasetActionResult(BaseModel):
    dataset_id: str


class VisualizationActionResult(BaseModel):
    plot_path_: str
    visualization_id_: str


class MOBOActionResult(BaseModel):
    mobo_output: Path


class RescaleActionResult(BaseModel):
    rescale_output: Path


class PostRescaleActionResult(BaseModel):
    post_rescale_output: Path


class ActionResultType(str, Enum):
    FAILURE = "FAILURE"

    DATASET = "DATASET"

    STRING = "STRING"

    STRINGS_LIST = "STRINGS_LIST"

    INTEGER = "INTEGER"

    INTEGERS_LIST = "INTEGERS_LIST"

    FLOAT = "FLOAT"

    FLOATS_LIST = "FLOATS_LIST"

    DICTIONARY = "DICTIONARY"

    MODEL = "MODEL"

    PATH = Path

    FILE_OR_FOLDER_PATH = "FILE_OR_FOLDER_PATH"

    VISUALIZATION = "VISUALIZATION"

    # FILE_PATH = "FILE_PATH"


class ActionResult(BaseModel):
    id: Optional[str] = Field(default=None, description="Result Id", alias="_id")

    output_name: Optional[str] = Field(
        default=None, description="Output Name from widget"
    )

    type: ActionResultType

    result: Union[
        FailureActionResult,
        DatasetActionResult,
        StringActionResult,
        ListOfStringsActionResult,
        IntegerActionResult,
        ListOfIntegersActionResult,
        FloatActionResult,
        ListOffloatsActionResult,
        DictionaryActionResult,
        JSONActionResult,
        VisualizationActionResult,
        FileActionResult,
    ]
