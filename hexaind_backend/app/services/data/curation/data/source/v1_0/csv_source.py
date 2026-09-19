from typing import Literal

import dask.dataframe as dd
import pandas as pd
from pandas import read_csv
from pydantic import FilePath

from ...type_ import DataType
from ._source import DataSource
from .guess_types import guess_datatypes


class CSVDataSource(DataSource):
    data_type: Literal[DataType.CSV]
    path: FilePath

    @property
    def dataframe(self) -> dd.DataFrame:
        dataframe = read_csv(self.path)
        if dataframe.shape[0] == 0:
            dataframe.index = dataframe.index.astype(int)
        dataframe = guess_datatypes(dataframe)
        ddf = dd.from_pandas(dataframe, npartitions=1)  # ✅ Use public API
        return ddf.to_backend()  # Optional, depending on what backend you expect
