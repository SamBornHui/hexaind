from __future__ import annotations

from typing import Annotated

import dask.dataframe as dd
from plotly.graph_objects import Figure
from pydantic import Field, RootModel

from .contour import Contour
from .distribution import Distribution
from .linearfit import LinearFit
from .splinefit import SplineFit
from .boxplot import BoxPlot
from .scatterplot import ScatterPlot
from .histogram import Histogram
from .iqrplot import IQRPlot

class DataVisualization(RootModel):
    root: Annotated[
        Distribution | LinearFit | SplineFit | Contour | BoxPlot | ScatterPlot | Histogram | IQRPlot,
        Field(discriminator="plot_type"),
    ]

    def figure(self, dataframe: dd.DataFrame) -> Figure:
        return self.root.figure(dataframe=dataframe)