from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Annotated

# from dask.dataframe.core import DataFrame
import dask.dataframe as dd

from pydantic import Field, RootModel

from ....assets.datasets.schemas import Dataset, DatasetType
from ...data.type_ import DataType
from .v1_0.model import DataSourceModel as DataSourceModelV1_0


class DataSourceModel(RootModel):
    root: Annotated[DataSourceModelV1_0, Field(discriminator="version")]

    @cached_property
    def dataframe(self) -> dd.DataFrame:
        df = self.root.dataframe
        for column, dtype in zip(df.columns, df.dtypes):
            if dtype in ("object", "datetime", "timedelta", "datetimetz", "boolean"):
                df[column] = df[column].astype(str)  # type: ignore
        return df

    @cached_property
    def original_dataframe(self) -> dd.DataFrame:
        return self.root.dataframe

    @staticmethod
    def from_dataset(dataset: Dataset) -> DataSourceModel:
        if dataset.dataset_type != DatasetType.TABULAR:
            raise TypeError(dataset.dataset_type)
        match dataset.dataset_location:
            case [dataset_location]:
                return DataSourceModel.from_path(dataset_location.path)
            case _:
                raise NotImplementedError(
                    "Only implemented for single dataset location"
                )

    @staticmethod
    def from_path(path: str | Path, **kwargs) -> DataSourceModel:
        path = Path(path)
        version = "1.0"
        if path.is_dir():
            data_type = DataType.PARQUET
        else:
            match path.suffix.lower():
                case ".csv":
                    data_type = DataType.CSV
                case ".parquet":
                    data_type = DataType.PARQUET
                case ".xls" | ".xlsx":
                    data_type = DataType.EXCEL
                case _:
                    raise NotImplementedError(f"Unsupported file format {path.suffix}")
        return DataSourceModel.model_validate(
            {
                **kwargs,
                "version": version,
                "data_type": data_type,
                "path": path,
            }
        )
