from __future__ import annotations

from typing import Any, List, Literal, Optional

import numpy as np
from pydantic import BaseModel, Field, PositiveInt

from ....data.source.model import DataSourceModel


class DataPreview(BaseModel):
    version: Literal["1.0"]
    column_names: List[str]
    data: List[List[Any]]
    total_rows: int = Field(ge=0)
    page: PositiveInt
    page_size: PositiveInt
    total_columns: Optional[int]

    @classmethod
    def from_data_source(
        cls,
        data_source: DataSourceModel,
        page: PositiveInt = 1,
        page_size: PositiveInt = 100,
    ) -> DataPreview:
        preview_data = (
            data_source.dataframe.loc[(page - 1) * page_size : page * page_size - 1]
            .fillna(np.nan)
            .replace([np.nan], [None])
            .compute()
            .to_dict(orient="split")
        )
        return cls(
            version="1.0",
            column_names=preview_data["columns"],
            data=preview_data["data"],
            total_rows=data_source.dataframe.shape[0].compute(),
            page=page,
            page_size=page_size,
            total_columns=data_source.dataframe.shape[1].compute(),
        )
