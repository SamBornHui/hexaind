from typing import Literal
import logging

import dask.dataframe as dd
from numpy import linspace, meshgrid
from plotly.graph_objects import Figure
from scipy.interpolate import griddata

from ._visualization import _DataVisualization
from .viz_types import VisualizationType

logger = logging.getLogger(__package__)

class Contour(_DataVisualization):
    plot_type: Literal[VisualizationType.CONTOUR]
    color_by: str

    def figure(self, dataframe: dd.DataFrame) -> Figure:
        """
        This service is used for plotting the contour plot.

        Args:
            dataframe (dd.DataFrame): _description_

        Returns:
            Figure: Plotly figure
        """
        logger.info(f"[{VisualizationType.CONTOUR}]: Intializing")
        
        dataframe = dataframe[list(
            set(column for column in [self.x, self.y, self.color_by] if column is not None))].dropna().compute()
        logger.info(f"[{VisualizationType.CONTOUR}]: Computed the provided dataframe with given values.")

        x_min, x_max = dataframe[self.x].min(), dataframe[self.x].max()
        y_min, y_max = dataframe[self.y].min(), dataframe[self.y].max()
        x_axis = linspace(x_min, x_max, 200)
        y_axis = linspace(y_min, y_max, 200)
        X, Y = meshgrid(x_axis, y_axis)
        Z = griddata(
            (dataframe[self.x], dataframe[self.y]),
            dataframe[self.color_by],
            (X, Y),
            method="cubic",
        )
        logger.info(f"[{VisualizationType.CONTOUR}]: computed the required data for contour.")

        figure = Figure()
        figure.add_contour(
            x=x_axis,
            y=y_axis,
            z=Z,
            colorscale=["blue", "lightgrey", "red"],
            contours=dict(coloring="heatmap"),
            line=dict(width=0),
            colorbar=dict(title=self.color_by),
        )
        logger.info(f"[{VisualizationType.CONTOUR}] X==Y. Plotting and returning the contour plot.")
        return figure
