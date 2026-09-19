import logging
from typing import Literal

import dask.dataframe as dd
import plotly.express as px
from pandas.api.types import is_numeric_dtype
from plotly.graph_objects import Figure

from ._visualization import _DataVisualization
from .viz_types import VisualizationType


logger = logging.getLogger(__package__)


class ScatterPlot(_DataVisualization):
    plot_type: Literal[VisualizationType.SCATTER_PLOT]

    def figure(self, dataframe: dd.DataFrame) -> Figure:
        logger.info(f"[{VisualizationType.SCATTER_PLOT}]: Initializing")

        # Select relevant columns
        columns = [self.x, self.y] + ([self.color_by] if self.color_by else [])
        dataframe = dataframe[columns].compute()

        logger.info(f"[{VisualizationType.SCATTER_PLOT}]: Computed DataFrame with columns {columns}. Shape: {dataframe.shape}.")

        # Ensure X and Y are numeric
        assert is_numeric_dtype(dataframe[self.x]), f"X-axis column '{self.x}' should be numerical, but got {dataframe[self.x].dtype}."
        assert is_numeric_dtype(dataframe[self.y]), f"Y-axis column '{self.y}' should be numerical, but got {dataframe[self.y].dtype}."

        # Log if color_by is used
        if self.color_by:
            logger.info(f"[{VisualizationType.SCATTER_PLOT}]: Coloring by '{self.color_by}'.")

        # Log trendline status
        if self.line_fit:
            logger.info(f"[{VisualizationType.SCATTER_PLOT}]: Applying trendline (OLS).")

        # Create scatter plot
        fig = px.scatter(
            data_frame=dataframe,
            x=self.x,
            y=self.y,
            color=self.color_by,
            trendline="ols" if self.line_fit else None
        )

        return fig

