from typing import Literal
import logging

import dask.dataframe as dd
import plotly.express as px
from plotly.graph_objects import Figure

from ._visualization import _DataVisualization
from .viz_types import VisualizationType

logger = logging.getLogger(__package__)


class LinearFit(_DataVisualization):
    plot_type: Literal[VisualizationType.LINEARFIT]

    def figure(self, dataframe: dd.DataFrame) -> Figure:
        """
        This service is used for generating a LinearFit plot

        Args:
            dataframe (dd.DataFrame): _description_

        Raises:
            ValueError: _description_

        Returns:
            Figure: returns a plotly figure
        """
        logger.info(f"[{VisualizationType.LINEARFIT}]: Intializing")

        dataframe = dataframe[
            list(
                set(
                    column
                    for column in [self.x, self.y, self.color_by]
                    if column is not None
                )
            )
        ].compute()
        logger.info(
            f"[{VisualizationType.LINEARFIT}]: Computed the provided dataframe with given values."
        )

        if self.color_by and dataframe[self.color_by].nunique() > 100:
            logger.error(
                f"[{VisualizationType.LINEARFIT}]: There are more 100 groups, please filter the dataset to have less groups in {self.color_by}"
            )
            raise ValueError(
                f"There are more 100 groups, please filter the dataset to have less groups in {self.color_by}"
            )

        if not self.color_by:
            fig = px.scatter(
                data_frame=dataframe,
                x=self.x,
                y=self.y,
                trendline="ols",
            )
            fig.update_traces(marker_color='#018786')

        else:
            fig = px.scatter(
                data_frame=dataframe,
                x=self.x,
                y=self.y,
                color=self.color_by,
                trendline="ols",
            )
        logger.info(f"[{VisualizationType.LINEARFIT}]: Returning the linearfit figure")
        return fig
