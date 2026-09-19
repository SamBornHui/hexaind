from pydantic import BaseModel, GetCoreSchemaHandler
from typing import List, Optional, Union, Any
from enum import Enum
from app.services.data.assets.datasets.service import Dataset
from app.services.workflows.designer.schemas import JoinType, ColumnAndType
from bson import ObjectId
from pydantic_core import CoreSchema, core_schema
from pydantic_core.core_schema import ValidationInfo, str_schema
from bson.errors import InvalidId
from fastapi import HTTPException

class ObjectIdAsStr(ObjectId):
    """
    Object Id field. Compatible with Pydantic.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _: ValidationInfo):
        if isinstance(v, bytes):
            v = v.decode("utf-8")
        try:
            return ObjectIdAsStr(v)
        except (InvalidId, TypeError):
            raise HTTPException(status_code=422, detail="ids must be of valid string of ObjectId")

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:  # type: ignore
        return core_schema.json_or_python_schema(
            python_schema=core_schema.with_info_plain_validator_function(cls.validate),
            json_schema=str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: str(instance)
            ),
        )

class AppendModel(BaseModel):
    datasets_list: List[Dataset]
    max_rows: int
    ignore_index: bool
    column_type_pref_list: Optional[List[ColumnAndType]] = []
    convert_words_to_number: Optional[bool] = True

class JoinModel(BaseModel):
    left_dataset: Dataset
    right_dataset: Dataset
    left_columns: Optional[List[str]] = []
    right_columns: Optional[List[str]] = []
    join_type: JoinType

class DatasetDataframe(BaseModel):
    id: str
    name: str
    dataframe: Optional[object]

class MisMatchDataset(BaseModel):
    dataset_id: str
    name: str
    data_type: str

class ColumnAndDetails(BaseModel):
    column: str
    details: List[Union[str, MisMatchDataset]]

class Detail(BaseModel):
    mismatch_datatype_columns: List[ColumnAndDetails]
    missing_columns: List[ColumnAndDetails]

class AppendMismatchCheckResponse(BaseModel):
    status: bool
    detail: Union[str, Detail]