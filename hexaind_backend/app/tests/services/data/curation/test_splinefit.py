import pytest
from dask.dataframe import from_pandas
import pandas as pd
from plotly.graph_objects import Figure
from app.services.data.curation.eda.visualizations.v1_0.splinefit import SplineFit
from app.services.data.curation.eda.visualizations.v1_0.viz_types import VisualizationType

@pytest.fixture
def sample_dataframe():
    data = {
        'x': [1, 2, 3, 4, 5],
        'y': [6, 7, 8, 9, 10],
        'color_by': ['A', 'A', 'B', 'B', 'B']
    }
    return from_pandas(pd.DataFrame(data), npartitions=1)

def test_spline_fit_figure(sample_dataframe):
    spline_fit = SplineFit(version="1.0", x='x', y='y', color_by='color_by', plot_type=VisualizationType.SPLINEFIT)
    figure = spline_fit.figure(sample_dataframe)
    assert isinstance(figure, Figure)

def test_spline_fit_figure_no_color(sample_dataframe):
    spline_fit = SplineFit(version="1.0", x='x', y='y', plot_type=VisualizationType.SPLINEFIT)
    figure = spline_fit.figure(sample_dataframe)
    assert isinstance(figure, Figure)

def test_spline_fit_figure_too_many_groups(sample_dataframe):
    too_many_groups_dataframe = from_pandas(pd.DataFrame({
        'x': [f'x_{i}' for i in range(101)],
        'y': [f'y_{i}' for i in range(101)],
        'color_by': [f'group_{i}' for i in range(101)]  # Creating more than 100 unique groups
    }), npartitions=1)
    spline_fit = SplineFit(version="1.0", x='x', y='y', color_by='color_by', plot_type=VisualizationType.SPLINEFIT)
    with pytest.raises(ValueError):
        spline_fit.figure(too_many_groups_dataframe)
