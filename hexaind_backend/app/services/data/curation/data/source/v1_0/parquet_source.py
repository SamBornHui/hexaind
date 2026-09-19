from typing import Literal

# from dask.dataframe.core import DataFrame
import dask.dataframe as dd
# from dask.dataframe.io.parquet.core import read_parquet
from pydantic import DirectoryPath, FilePath

from ...type_ import DataType
from ._source import DataSource


class ParquetDataSource(DataSource):
    data_type: Literal[DataType.PARQUET]
    path: FilePath | DirectoryPath

    @property
    def dataframe(self) -> dd.DataFrame:
        df = dd.read_parquet(self.path)
        return df.to_backend()
