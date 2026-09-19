from pathlib import Path
import pytest
from dask.dataframe import from_pandas
import pandas as pd
import dask.dataframe as dd
from plotly.graph_objects import Figure
from pydantic import ValidationError
from app.services.data.curation.eda.visualizations.v1_0.distribution import Distribution
from app.services.data.curation.eda.visualizations.v1_0.viz_types import VisualizationType

@pytest.fixture
def sample_dataframe():
    df = dd.read_csv(Path(__file__).parent.parent.parent.parent/"resources/penguin.csv")
    
    return df, 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm'


def test_distribution_figure(sample_dataframe):
    df, x, y, color_by = sample_dataframe
    distribution = Distribution(version="1.0", x=x, y=y, color_by=color_by, plot_type=VisualizationType.DISTRIBUTION)
    figure = distribution.figure(df)
    assert isinstance(figure, Figure)

def test_distribution_figure_no_color(sample_dataframe):
    df, x, y, color_by = sample_dataframe
    distribution = Distribution(version="1.0", x=x, y=y, plot_type=VisualizationType.DISTRIBUTION)
    figure = distribution.figure(df)
    assert isinstance(figure, Figure)

@pytest.mark.fixme
def test_distribution_figure_x_equals_y(sample_dataframe):
    df, x, y, color_by = sample_dataframe
    distribution = Distribution(version="1.0", x=x, y=x, color_by=color_by, plot_type=VisualizationType.DISTRIBUTION)
    figure = distribution.figure(df)
    assert isinstance(figure, Figure)
