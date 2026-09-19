from __future__ import annotations

from pathlib import Path
from typing import Annotated

# from dask.dataframe.core import DataFrame
import dask.dataframe as dd
from pydantic import Field, RootModel

from ..type_ import DataType
from .v1_0.model import DataSinkModel as DataSinkModelV1_0


class DataSinkModel(RootModel):
    root: Annotated[DataSinkModelV1_0, Field(discriminator="version")]

    def to_sink(self, dataframe: dd.DataFrame):
        self.root.to_sink(dataframe)

    @staticmethod
    def from_path(path: str | Path, **kwargs) -> DataSinkModel:
        path = Path(path)
        version = "1.0"
        match path.suffix.lower():
            case ".csv":
                data_type = DataType.CSV
            case ".parquet":
                data_type = DataType.PARQUET
            case _:
                raise NotImplementedError(f"Unsupported file format {path.suffix}")
        return DataSinkModel.model_validate(
            {
                **kwargs,
                "version": version,
                "data_type": data_type,
                "path": path,
            }
        )
