from abc import ABC, abstractmethod
from typing import Literal

# from dask.dataframe.core import DataFrame
import dask.dataframe as dd
from pydantic import BaseModel


class DataSource(BaseModel, ABC):
    version: Literal["1.0"]

    @property
    @abstractmethod
    def dataframe(self) -> dd.DataFrame: ...
