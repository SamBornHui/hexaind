from functools import partial
from itertools import cycle
from typing import Literal

import dask.dataframe as dd
import plotly.express as px
from csaps import csaps
from numpy import linspace
from plotly.graph_objects import Figure

import logging
logger = logging.getLogger(__package__)

from ._visualization import _DataVisualization
from .viz_types import VisualizationType


def get_spline_data(
    df: dd.DataFrame, x: str, y: str, color: str, x_axis, smooth
):
    df = df.drop_duplicates(subset=x).sort_values(by=x).dropna(subset=x)
    if df.shape[0] > 1:
        return (
            csaps(df[x], df[y], x_axis, smooth=smooth),
            df[color].iloc[0] if color else None,
        )
    return None, None


class SplineFit(_DataVisualization):
    plot_type: Literal[VisualizationType.SPLINEFIT]

    def figure(
        self,
        dataframe: dd.DataFrame,
        smooth: float = 0.5,
    ) -> Figure:
        """
        This service is used for plotting the Splinefit

        Args:
            dataframe (dd.DataFrame): _description_
            smooth (float, optional): _description_. Defaults to 0.5.

        Raises:
            ValueError: _description_

        Returns:
            Figure: returns a plotly figure.
        """
        logger.info(f"[{VisualizationType.SPLINEFIT}]: Intializing")
        dataframe = dataframe[list(
            set(column for column in [self.x, self.y, self.color_by] if column is not None))].compute()
        logger.info(f"[{VisualizationType.SPLINEFIT}]: Computed the provided dataframe with given values.")

        if self.color_by and dataframe[self.color_by].nunique() > 100:
            logger.error(f"[{VisualizationType.SPLINEFIT}]: There are more 100 groups, please filter the dataset to have less groups in {self.color_by}")
            raise ValueError(
                f"There are more 100 groups, please filter the dataset to have less groups in {self.color_by}"
            )
        x_min, x_max = dataframe[self.x].min(), dataframe[self.x].max()
        figure = px.scatter(
            dataframe, x=self.x, y=self.y, color=self.color_by, opacity=0.5
        )
        logger.info(f"[{VisualizationType.SPLINEFIT}]: Plotted the scatter, next will plot the splinefit lines")

        x_axis = linspace(x_min, x_max, 1_000)
        color_cycle = cycle(figure.layout["template"]["layout"]["colorway"])
        if self.color_by is None:
            logger.info(f"[{VisualizationType.SPLINEFIT}]: {self.color_by} is None. Plotting the lines")
            y_axis, _ = get_spline_data(
                dataframe, self.x, self.y, self.color_by, x_axis, smooth
            )
            if y_axis is not None:
                figure.add_scattergl(
                    x=x_axis,
                    y=y_axis,
                    mode="lines",
                    name="spline",
                    line=dict(width=3),
                    marker_color=next(color_cycle),
                )
            figure.update_traces(marker_color='#018786')
            
        else:
            logger.info(f"[{VisualizationType.SPLINEFIT}]: {self.color_by} is not None. Plotting the lines")
            for (y_axis, group), color_ in zip(
                dataframe.groupby(self.color_by).apply(
                    partial(
                        get_spline_data,
                        x=self.x,
                        y=self.y,
                        color=self.color_by,
                        x_axis=x_axis,
                        smooth=smooth,
                    )
                ),
                color_cycle,
            ):
                if y_axis is not None:
                    figure.add_scattergl(
                        x=x_axis,
                        y=y_axis,
                        mode="lines",
                        name=f"{group} spline",
                        line=dict(width=3),
                        marker_color=color_,
                    )
        logger.info(f"[{VisualizationType.SPLINEFIT}]: Returning the splinefit figure")
        return figure
