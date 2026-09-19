from typing import Literal
import logging

import dask.dataframe as dd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objects import Figure

from ._visualization import _DataVisualization
from .viz_types import VisualizationType

logger = logging.getLogger(__package__)

class Distribution(_DataVisualization):
    plot_type: Literal[VisualizationType.DISTRIBUTION]

    def figure(self, dataframe: dd.DataFrame) -> Figure:
        """
        This service is being used for plotting the distribution plots

        Args:
            dataframe (dd.DataFrame): _description_

        Returns:
            Figure: Plotly figure
        """
        logger.info(f"[{VisualizationType.DISTRIBUTION}]: Intializing")

        columns = list(filter(None, [self.x, self.y, self.color_by]))
        dataframe = dataframe[columns].dropna().compute()
        logger.info(f"[{VisualizationType.DISTRIBUTION}]: Computed DataFrame with columns {columns}. Shape: {dataframe.shape}.")

        is_x_numerical = pd.api.types.is_numeric_dtype(dataframe[self.x])

        if self.x == self.y:
            logger.info(f"[{VisualizationType.DISTRIBUTION}] X==Y. Plotting and returning the histogram.")
            if is_x_numerical:
                fig = px.histogram(data_frame=dataframe, x=self.x) 
            else:
                fig = px.bar(data_frame=dataframe, x=self.x)  
            fig.update_traces(marker_color='#018786')

        else:
            logger.info(f"[{VisualizationType.DISTRIBUTION}] X!=Y. Plotting and returning the scatter.")
            if self.color_by:
                fig = px.scatter(
                    data_frame=dataframe, x=self.x, y=self.y, color=self.color_by
                )
            else:
                fig = px.scatter(
                    data_frame=dataframe, x=self.x, y=self.y
                )
                fig.update_traces(marker_color='#018786')


            fig.add_trace(
                go.Histogram(
                    x=dataframe[self.x],
                    marker=dict(color='blue', opacity=0.7),
                    showlegend=False,
                    yaxis="y2"
                )
            )

            fig.add_trace(
                go.Histogram(
                    y=dataframe[self.y],
                    marker=dict(color='red', opacity=0.7),
                    showlegend=False,
                    orientation='h',
                    xaxis="x2"
                )
            )

            fig.update_layout(
                xaxis=dict(domain=[0, 0.85]), 
                yaxis=dict(domain=[0, 0.85]),
                xaxis2=dict(domain=[0.85, 1], showgrid=False, zeroline=False),  
                yaxis2=dict(domain=[0.85, 1], showgrid=False, zeroline=False),  
                margin=dict(l=0, r=0, t=40, b=0),
                height=600,  
                width=800,   
            )

        return fig
