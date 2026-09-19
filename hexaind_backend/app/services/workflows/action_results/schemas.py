from typing import Optional, Union, List
from enum import Enum
from pydantic import BaseModel, Field
from pathlib import Path

class StringActionResult(BaseModel):

    string_value: str

class JSONActionResult(BaseModel):

    json_value: dict

class FailureActionResult(BaseModel):

    error_code: str
    error_description: str

class DatasetActionResult(BaseModel):

    dataset_id: str

class MOBOActionResult(BaseModel):
    mobo_output: Path

class RescaleActionResult(BaseModel):
    rescale_output: Path

class PostRescaleActionResult(BaseModel):
    post_rescale_output: Path

class ActionResultType(str, Enum):

    DATASET = "DATASET"

    STRING = "STRING"

    MODEL = "MODEL"

    FAILURE = "FAILURE"

    PATH = Path

class ActionResult(BaseModel):

    id: Optional[str] = Field(default=None, description="Result Id", alias="_id")

    type: ActionResultType

    result: Union[DatasetActionResult, FailureActionResult, StringActionResult, JSONActionResult]