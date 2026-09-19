from typing import Annotated

# from dask.dataframe.core import DataFrame
import dask.dataframe as dd
from pydantic import Field, RootModel

from .csv_sink import CSVDataSink
from .parquet_sink import ParquetDataSink


class DataSinkModel(RootModel):
    root: Annotated[
        CSVDataSink | ParquetDataSink, Field(discriminator="data_type")
    ]

    def to_sink(self, dataframe: dd.DataFrame):
        self.root.to_sink(dataframe)
