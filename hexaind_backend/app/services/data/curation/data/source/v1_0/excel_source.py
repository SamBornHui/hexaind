from typing import Literal, Union

import pandas as pd
import dask.dataframe as dd
from pydantic import FilePath

from ...type_ import DataType
from ._source import DataSource
from .guess_types import guess_datatypes


class ExcelDataSource(DataSource):
    data_type: Literal[DataType.EXCEL]
    path: FilePath
    sheet_name: Union[str, int] = 0  # Defaults to the first sheet

    @property
    def dataframe(self) -> dd.DataFrame:
        """
        Returns a Dask DataFrame for a specific sheet.
        """
        df = pd.read_excel(self.path, sheet_name=self.sheet_name)
        df = guess_datatypes(df)
        ddf = dd.from_pandas(df, npartitions=1)  # ✅ Use the public API
        return ddf.to_backend()
