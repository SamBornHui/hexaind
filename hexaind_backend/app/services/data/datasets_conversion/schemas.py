from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DatasetsConversionType(str, Enum):
    TABULAR_PARQUET_TO_CSV = 'TABULAR_PARQUET_TO_CSV'
    TABULAR_CSV_TO_PARQUET = 'TABULAR_CSV_TO_PARQUET'


class DatasetsConversionFromConfig(BaseModel):
    dataset_id: str = Field(..., description="dataset_id selected for modification")


class DatasetsConversionToConfig(BaseModel):
    name: str


class DatasetsConversionRequest(BaseModel):
    conversion_type: DatasetsConversionType
    from_config: DatasetsConversionFromConfig
    to_config: Optional[DatasetsConversionToConfig] = Field(default=None, description="")
    retain_existing_data: bool = Field(default=True, description="Deletes/Retains existing data")


class DatasetsConversionResponse(BaseModel):
    succeeded: bool
    message: str
