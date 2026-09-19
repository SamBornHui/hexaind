from typing import List, Optional

from pydantic import BaseModel, Field


class CorrelationInputSchema(BaseModel):
    dataset_id: str = Field(...)
    columns: List[str] = Field(...)
    min_period: Optional[int] = Field(...)
    clip_percentiles: float = Field(...)
    symmetric_bounds: bool = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": "6593c2bbc42365afd78354e8",
                "columns": [
                    "cat_0",
                    "cat_1",
                    "cat_2",
                    "cat_3",
                    "cat_4",
                    "num_0",
                    "num_1",
                ],
            }
        }


class CorrHeatmap(BaseModel):
    columns: List[str]
    heatmap_data_z: List[List[float]]
    vmin: float
    vmax: float


class CorrelationResponse(BaseModel):
    corr_heatmap: Optional[CorrHeatmap]
    correlation_job_id: Optional[str]
    file_path: Optional[str]


class CorrelationSuccessResponse(BaseModel):
    status: bool
    data: CorrelationResponse


class CorrelationFailureResponse(BaseModel):
    status: bool
    msg: str
