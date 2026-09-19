import logging
from typing import Literal

import dask.dataframe as dd
import numpy as np
import plotly.express as px
from pandas.api.types import is_numeric_dtype
from plotly.graph_objects import Figure

from ._visualization import _DataVisualization
from .viz_types import VisualizationType

logger = logging.getLogger(__package__)


class IQRPlot(_DataVisualization):
    plot_type: Literal[VisualizationType.IQR_PLOT]

    def figure(self, dataframe: dd.DataFrame) -> Figure:
        logger.info(f"[{VisualizationType.IQR_PLOT}]: Initializing")

        columns = list(filter(None, [self.x, self.y, self.color_by]))
        dataframe = dataframe[columns].compute()

        logger.info(
            f"[{VisualizationType.SCATTER_PLOT}]: Computed DataFrame with columns {columns}. Shape: {dataframe.shape}."
        )

        # Remove null values
        dataframe = dataframe.dropna(subset=[self.y])

        # assert dataframe[self.y] is numerical
        assert is_numeric_dtype(
            dataframe[self.y]
        ), f"X-axis column {self.y} should be numerical not {type(dataframe[self.y])}"

        # Calculate IQR
        IQR_min = np.percentile(dataframe[self.y], 25)
        IQR_max = np.percentile(dataframe[self.y], 75)

        fig = px.box(data_frame=dataframe, y=self.y)

        # Add IQR annotations
        fig.add_annotation(
            text=f"IQR Min (Q1): {IQR_min:.2f}<br>IQR Max (Q3): {IQR_max:.2f}",
            xref="paper",
            yref="paper",
            x=0,
            y=1,
            showarrow=False,
            bordercolor="black",
            borderwidth=1,
            borderpad=4,
            bgcolor="white",
        )

        fig.update_layout(
            title="IQR plot",
            yaxis_title="Values",
            xaxis=dict(showticklabels=False, title=self.y),
        )

        fig.update_traces(marker_color="#018786")

        return fig
