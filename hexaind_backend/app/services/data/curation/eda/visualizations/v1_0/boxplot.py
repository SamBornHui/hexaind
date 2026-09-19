import logging
from typing import Literal

import dask.dataframe as dd
import plotly.express as px
from pandas.api.types import is_numeric_dtype
from plotly.graph_objects import Figure

from ._visualization import _DataVisualization
from .viz_types import VisualizationType

logger = logging.getLogger(__package__)


class BoxPlot(_DataVisualization):
    plot_type: Literal[VisualizationType.BOX_PLOT]

    def figure(self, dataframe: dd.DataFrame) -> Figure:
        logger.info(f"[{VisualizationType.BOX_PLOT}]: Initializing")

        columns = list(filter(None, [self.x, self.y, self.color_by]))
        dataframe = dataframe[columns].compute()

        logger.info(
            f"[{VisualizationType.BOX_PLOT}]: Computed DataFrame with columns {columns}. Shape: {dataframe.shape}."
        )

        # assert dataframe[self.y] is numerical
        assert is_numeric_dtype(
            dataframe[self.y]
        ), f"Y-axis column {self.y} should be numerical not not {type(dataframe[self.y])}"

        fig = px.box(data_frame=dataframe, x=self.x, y=self.y, color=self.color_by)

        return fig
