from datetime import datetime
from enum import Enum, auto
from typing import Annotated, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field, RootModel, field_validator


class SchemaFieldType(str, Enum):
    NUMERIC = "NUMERIC"
    CATEGORICAL = "CATEGORICAL"

    @staticmethod
    def from_bigquery_type(bg_field_type: str):
        # https://cloud.google.com/bigquery/docs/reference/rest/v2/tables#TableFieldSchema.FIELDS.type
        numeric_field_types = ["INTEGER", "INT64", "FLOAT", "FLOAT64", "NUMERIC"]
        if bg_field_type in numeric_field_types:
            return SchemaFieldType.NUMERIC
        else:
            return SchemaFieldType.CATEGORICAL


class SchemaField(BaseModel):
    name: str = Field(description="Name of field in schema")
    field_type: SchemaFieldType = Field(description="Field types from SchemaFieldType")


class DryRunResponseModel(BaseModel):
    fields: Optional[List[SchemaField]] = Field(
        description="List containing all schema fields"
    )
    size: Optional[int] = Field(description="Size of data in bytes")


class DatasetTableListResponse(BaseModel):
    data_list: List[str]


class PreviewResponse(BaseModel):
    # preview: List[dict]
    columns: List
    data: List


class TablesList(BaseModel):
    dataset_name: str




class StrEnum(str, Enum):
    @staticmethod
    def _generate_next_value_(name: str, start, count, last_values) -> str:
        return name.upper()


class ParamType(StrEnum):
    SCALAR = auto()
    TUPLE = auto()
    LIST = auto()
    DATE = auto()


class ParamValueType(StrEnum):
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    RANGE = auto()
    LIST = auto()

class CommonQueryParam(BaseModel):
    optional: bool = False


class IntegerScalarQueryParam(CommonQueryParam):
    type: Literal[ParamValueType.INTEGER]
    data: int | None


class FloatScalarQueryParam(CommonQueryParam):
    type: Literal[ParamValueType.FLOAT]
    data: float | None


class StringScalarQueryParam(CommonQueryParam):
    type: Literal[ParamValueType.STRING]
    data: str | None


class ScalarQueryParamValue(RootModel):
    root: Annotated[
        IntegerScalarQueryParam | FloatScalarQueryParam | StringScalarQueryParam,
        Field(discriminator="type"),
    ]


class IntegerTupleQueryParam(CommonQueryParam):
    type: Literal[ParamValueType.INTEGER]
    data: Tuple[int] | None


class FloatTupleQueryParam(CommonQueryParam):
    type: Literal[ParamValueType.FLOAT]
    data: Tuple[float] | None


class StringTupleQueryParam(CommonQueryParam):
    type: Literal[ParamValueType.STRING]
    data: Tuple[str] | None


class TupleQueryParamValue(RootModel):
    root: Annotated[
        IntegerTupleQueryParam | FloatTupleQueryParam | StringTupleQueryParam,
        Field(discriminator="type"),
    ]


class IntegerListQueryParam(CommonQueryParam):
    type: Literal[ParamValueType.INTEGER]
    data: List[int] | None


class FloatListQueryParam(CommonQueryParam):
    type: Literal[ParamValueType.FLOAT]
    data: List[float] | None


class StringListQueryParam(CommonQueryParam):
    type: Literal[ParamValueType.STRING]
    data: List[str] | None


class ListQueryParamValue(RootModel):
    root: Annotated[
        IntegerListQueryParam | FloatListQueryParam | StringListQueryParam,
        Field(discriminator="type"),
    ]


class DateRangeQueryParam(CommonQueryParam):
    type: Literal[ParamValueType.RANGE]
    data: Tuple[datetime, datetime]

    @field_validator("data")
    @classmethod
    def check_date_range(
        cls, data: Tuple[datetime, datetime]
    ) -> Tuple[datetime, datetime]:
        start, end = data
        if start > end:
            raise ValueError(f"Invalid daterange {start=} must be before {end=}")
        return data


class DateListQueryParam(CommonQueryParam):
    type: Literal[ParamValueType.LIST]
    data: List[datetime] = []


class DateQueryParamValue(RootModel):
    root: Annotated[
        DateRangeQueryParam | DateListQueryParam, Field(discriminator="type")
    ]


class ScalarQueryParam(BaseModel):
    type: Literal[ParamType.SCALAR]
    value: ScalarQueryParamValue


class ListQueryParam(BaseModel):
    type: Literal[ParamType.LIST]
    value: ListQueryParamValue


class TupleQueryParam(BaseModel):
    type: Literal[ParamType.TUPLE]
    value: TupleQueryParamValue


class DateQueryParam(BaseModel):
    type: Literal[ParamType.DATE]
    value: DateQueryParamValue


class QueryParam(RootModel):
    root: Annotated[
        ScalarQueryParam | TupleQueryParam | ListQueryParam | DateQueryParam,
        Field(discriminator="type"),
    ]


class BigQueryDatasetQueryConfig(BaseModel):
    query: str = Field(..., description="BigQuery SQL Query output to be copied")
    query_params: Dict[str, QueryParam] = {}


class PreviewObj(BaseModel):
    dataset_name: Optional[str] = ""
    table_name: Optional[str] = ""
    query_config: Optional[BigQueryDatasetQueryConfig] = None