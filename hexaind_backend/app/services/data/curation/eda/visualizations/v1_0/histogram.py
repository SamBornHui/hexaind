import logging
from typing import Literal

import dask.dataframe as dd
import plotly.express as px
from pandas.api.types import is_categorical_dtype, is_numeric_dtype
from plotly.graph_objects import Figure

from ._visualization import _DataVisualization
from .viz_types import VisualizationType

logger = logging.getLogger(__package__)


class Histogram(_DataVisualization):
    plot_type: Literal[VisualizationType.HISTOGRAM]

    def figure(self, dataframe: dd.DataFrame) -> Figure:
        logger.info(f"[{VisualizationType.HISTOGRAM}]: Initializing")

        columns = list(filter(None, [self.x, self.y, self.color_by]))
        dataframe = dataframe[columns].compute()

        logger.info(
            f"[{VisualizationType.HISTOGRAM}]: Computed DataFrame with columns {columns}. Shape: {dataframe.shape}."
        )

        # assert dataframe[self.x] should be numerical or categorical
        assert (is_numeric_dtype(dataframe[self.x])or is_categorical_dtype(
            dataframe[self.x]
        ),f"X-axis column {self.x} should be numerical or categorical not {type(dataframe[self.x])}",)

        fig = px.histogram(
            data_frame=dataframe, x=self.x, y=self.y, color=self.color_by
        )

        return fig
