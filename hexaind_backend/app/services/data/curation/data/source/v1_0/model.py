from typing import Annotated

# from dask.dataframe.core import DataFrame
import dask.dataframe as dd

from pydantic import Field, RootModel

from .csv_source import CSVDataSource
from .excel_source import ExcelDataSource
from .parquet_source import ParquetDataSource


class DataSourceModel(RootModel):
    root: Annotated[
        CSVDataSource | ParquetDataSource | ExcelDataSource,
        Field(discriminator="data_type"),
    ]

    @property
    def dataframe(self) -> dd.DataFrame:
        return self.root.dataframe
