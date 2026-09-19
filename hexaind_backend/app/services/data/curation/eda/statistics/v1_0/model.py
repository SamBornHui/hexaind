from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Annotated, Any, List, Literal, Optional

import numpy as np
from dask.dataframe import concat
from pydantic import BaseModel, Field, RootModel

from ....data.source.model import DataSourceModel


class ColumnType(str, Enum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.upper()

    NUMERICAL = auto()
    CATEGORICAL = auto()


class _DataStatistics(BaseModel, ABC):
    column_names: List[str]
    row_names: List[str]
    data: List[List[Any]]

    @staticmethod
    @abstractmethod
    def from_data_source(data_source: DataSourceModel) -> _DataStatistics: ...


class NumericalStatistics(_DataStatistics):
    column_type: Literal[ColumnType.NUMERICAL]

    @staticmethod
    def from_data_source(data_source: DataSourceModel) -> _DataStatistics:
        df = data_source.dataframe.select_dtypes(include="number")
        data = (
            concat(
                [
                    df.describe(include="number"),
                    df.isnull().sum().to_frame(name="missing").compute().T,
                ],
            )
            .fillna(np.nan)
            .replace([np.nan], [None])
            .compute()
            .T.to_dict(orient="split")
        )
        return NumericalStatistics(
            column_type=ColumnType.NUMERICAL,
            column_names=data["index"],
            row_names=data["columns"],
            data=data["data"],
        )


class CategoricalStatistics(_DataStatistics):
    column_type: Literal[ColumnType.CATEGORICAL]

    @staticmethod
    def from_data_source(data_source: DataSourceModel) -> _DataStatistics:
        df = data_source.dataframe.select_dtypes(exclude="number")
        data = (
            concat(
                [
                    df.describe(exclude="number"),
                    df.isnull().sum().to_frame(name="missing").compute().T,
                ],
            )
            .fillna(np.nan)
            .replace([np.nan], [None])
            .compute()
            .T.to_dict(orient="split")
        )
        return CategoricalStatistics(
            column_type=ColumnType.CATEGORICAL,
            column_names=data["index"],
            row_names=data["columns"],
            data=data["data"],
        )


class DataStatistics(RootModel):
    root: Annotated[
        NumericalStatistics | CategoricalStatistics,
        Field(discriminator="column_type"),
    ]

class DataStatisticsModel(BaseModel):
    version: Literal["1.0"]
    statistics: List[DataStatistics] = []
    rows_count: Optional[int] = None
    columns_count: Optional[int] = None
    numerical_columns_count: Optional[int] = None
    categorical_columns_count: Optional[int] = None

    @classmethod
    def from_data_source(
        cls,
        data_source: DataSourceModel,
    ) -> DataStatisticsModel:
        statistics = []
        try:
            numerical = NumericalStatistics.from_data_source(data_source)
            statistics.append(numerical)
        except Exception:
            pass
        try:
            categorical = CategoricalStatistics.from_data_source(data_source)
            statistics.append(categorical)
        except Exception:
            pass
        return cls(version="1.0", statistics=statistics)
