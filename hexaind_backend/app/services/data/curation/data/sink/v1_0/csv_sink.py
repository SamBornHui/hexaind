from typing import Literal
from pathlib import Path
# from dask.dataframe.core import DataFrame
import dask.dataframe as dd
# from pydantic import NewPath

from ...type_ import DataType
from ._sink import DataSink


class CSVDataSink(DataSink):
    data_type: Literal[DataType.CSV]
    path: Path

    def to_sink(self, dataframe: dd.DataFrame):
        dataframe.compute().to_csv(str(self.path), index=False)
