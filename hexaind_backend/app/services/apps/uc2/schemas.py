from typing import Any, List, Dict

from pydantic import BaseModel, Field

from enum import Enum

from typing import Literal, Optional


class Metadata(BaseModel):
    """Model representing metadata for a project."""

    step_name: str = Field(..., description="Step name")
    tech_node: str = Field(..., description="Tech node")
    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    interval: int = Field(..., description="interval")
    output_column_names: List[str] = Field(..., description="output column names")
    work_week_folder_name: str = Field(..., description="Work week folder name")
    feedforward_params: Optional[Dict[str, Any]] = None
    ucl: Optional[float] = None
    lcl: Optional[float] = None
    target: Optional[float] = None
    optimization_folders: Dict[str, List[str]] = Field(default_factory=dict)


class TablePreview(BaseModel):
    """Model representing a preview of a table."""

    version: str = Field(default="1.0", description="Version")
    column_names: List[str] = Field(..., description="Column names")
    data: List[List[Any]] = Field(..., description="Data")
    total_rows: int = Field(default=10, description="Total rows")
    page: int = Field(default=1, description="Page")
    page_size: int = Field(default=50, description="Page size")


class UC2ProjectNames(BaseModel):
    """Model representing a list of project names."""

    project_names: List[str] = Field(
        default=[], description="List of project names from UC2 parent folder"
    )


class UC2ProjectMetadata(BaseModel):
    """Model representing metadata for multiple projects."""

    project_metadata: List[Metadata] = Field(
        default=[], description="List of project metadata from UC2 parent folder"
    )


# class UC2ProjectData(BaseModel):
#     """Model representing data for a specific project."""

#     line_charts: List[str] = Field(
#         ..., description="Line charts image file paths. List of .png or .html"
#     )

#     bar_plot: str = Field(..., description="Bar plot image file path. .png or .html")

#     models_comparison_df: str = Field(
#         ..., description="Models comparison CSV file path"
#     )

#     models_comparison_df_preview: TablePreview = Field(
#         ..., description="Models comparison CSV file preview"
#     )

#     chambers_comparison_df: str = Field(
#         ..., description="Chambers comparison CSV file path"
#     )

#     chambers_comparison_df_preview: TablePreview = Field(
#         ..., description="Chambers comparison CSV file preview"
#     )

#     fan_out_line_charts: List[str] = Field(
#         ..., description="Line charts image file paths. List of .png or .html"
#     )
#     fan_out_bar_plot: str = Field(..., description="Bar plot image file path. .png or .html")
    
#     fan_out_models_comparison_df: str = Field(
#         ..., description="Models comparison CSV file path"
#     )

#     fan_out_models_comparison_df_preview: TablePreview = Field(
#         ..., description="Models comparison CSV file preview"
#     )

#     fan_out_chambers_comparison_df: str = Field(
#         ..., description="Chambers comparison CSV file path"
#     )

#     fan_out_chambers_comparison_df_preview: TablePreview = Field(
#         ..., description="Chambers comparison CSV file preview"
#     )
class PlotType(str, Enum):

    BOX_PLOT = "BOX_PLOT"

    LINE_PLOT = "LINE_PLOT"

    PIE_CHART = "PIE_CHART"

class PlotData(BaseModel):
    
    type: PlotType = Field(default=PlotType.PIE_CHART)

    title: str = Field(default="")

    file_paths: List[str] = Field(default=[])

class TableData(BaseModel):

    title: str = Field(default="")

    data: dict = Field(default={})

    file_path: str = Field(default="")

class ModelFanOutData(BaseModel):
    
    table1: TableData

    table2: TableData

    table3: TableData

    pie_chart: PlotData

    bar_plot: Optional[PlotData] = Field(default=None)

    line_plot: Optional[PlotData] = Field(default=None)


class ModelRefreshData(BaseModel):
    
    table1: TableData

    table2: TableData

    bar_plot: PlotData

    line_plot: PlotData


class UC2ProjectData(BaseModel):

    model_fanout: ModelFanOutData

    model_refresh: ModelRefreshData

    unique_chamber_count_Fanout: int = Field(default=0, description="Unique chamber count for Fanout")
    unique_chamber_count_Refresh: int = Field(default=0, description="Unique chamber count for Refresh")

    chamber_plot_paths: Dict[str, Dict[str, str]] = Field(default_factory=dict)   

class UpdateChamberStatusResponse(BaseModel):
    message: str = Field(default="Status tracking file updated successfully.", description="Success message")

class ChamberData(BaseModel):
    runcomplete_datetime: List[str] = Field(
        ...,
        description="List of timestamps (strings) for each data point"
    )
    output_values: List[float] = Field(
        ...,
        description="List of numeric values from the output column for each data point"
    )

class SPCChartData(BaseModel):
    ucl: Optional[float] = Field(None, description="Upper Control Limit")
    lcl: Optional[float] = Field(None, description="Lower Control Limit")
    target: Optional[float] = Field(None, description="Target Value")
    chambers: Dict[str, ChamberData] = Field(
        ...,
        description="Dictionary mapping each chamber ID to ChamberData"
    )