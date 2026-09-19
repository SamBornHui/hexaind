from abc import ABC, abstractmethod
from typing import Literal

# from dask.dataframe.core import DataFrame
import dask.dataframe as dd
from pydantic import BaseModel


class DataSink(BaseModel, ABC):
    version: Literal["1.0"]

    @abstractmethod
    def to_sink(self, dataframe: dd.DataFrame): ...
