from abc import ABC, abstractmethod
from typing import Literal, Optional

import dask.dataframe as dd
from plotly.graph_objects import Figure
from pydantic import BaseModel

class AdditionalConfig(BaseModel):
    line_fit: Optional[bool] = None #To handle frontend additional config (line_fit)
class _DataVisualization(BaseModel, ABC):
    version: Literal["1.0"]
    x: Optional[str] = None
    y: Optional[str] = None
    color_by: Optional[str] = None
    interactive: Optional[bool] = None
    additional_config: Optional[AdditionalConfig] = AdditionalConfig()
    
    @property
    def line_fit(self) -> Optional[bool]:
        return self.additional_config.line_fit #To fetch values easily without function call

    @abstractmethod
    def figure(self, dataframe: dd.DataFrame) -> Figure: ...
