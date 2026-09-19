from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import (
    BaseModel,
    Field,
    RootModel,
    field_validator,
    model_validator,
    validator,
    TypeAdapter,
)

from app.core.schemas.action_result import ActionResult, ActionResultType
from app.services.AI.automl.schemas import AutoMLConfig
from app.services.AI.catboost.schemas import CATBoostConfig
from app.services.AI.extratrees.schemas import ExtraTreesConfig
from app.services.AI.gaussian_process_cls.schemas import GPCConfig
from app.services.AI.gpr.schemas import GPRConfig
from app.services.AI.k_nearest_neighbors.schemas import KNNConfig
from app.services.AI.lgbm.schemas import LGBMConfig
from app.services.AI.linear_regression.schemas import LinearRegressionConfig
from app.services.AI.mobo.schemas import MOBOConfig
from app.services.AI.nn_torch.schemas import NNTorchConfig
from app.services.AI.nnfastai.schemas import NNFastAIConfig
from app.services.AI.post_rescale.schemas import PostRescaleConfig
from app.services.AI.prediction.schemas import PredictionConfig
from app.services.AI.randomforest.schemas import RandomForestConfig
from app.services.AI.rescale.schemas import RescaleConfig
from app.services.AI.svm.schemas import SVMRConfig
from app.services.AI.thermocalc.schemas import ThermocalcConfig
from app.services.AI.xgboost.schemas import XGBoostConfig
from app.services.data.assets.custom_python_widget_recipes.dropdown_schemas import *
from app.services.data.assets.datasets.schemas import ApiJobType, Dataset
from app.services.data.assets.image_datasets.schemas import ImageDatasetConfig, RegionPropertiesConfig
from app.services.apps.image_analysis.schema import SpatialStatisticsConfig
from app.services.data.bigquery.schemas import BigQueryDatasetQueryConfig
from app.services.data.snowflake.schemas import (
    SnowFlakeDatasetTypes,
    SFDatasetTableConfig,
    SFDatasetQueryConfig,
)
from app.services.data.correlation.schemas import CorrelationInputSchema
from app.services.data.curation.eda.visualizations.v1_0.model import DataVisualization
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.AI.multi_polynomial_regression.schemas import MPRConfig


class SourceType(str, Enum):

    NONE = "NONE"

    LOCAL = "LOCAL"

    BIGQUERY = "BIGQUERY"

    MOUNTED_DRIVE = "MOUNTED_DRIVE"

    SNOWFLAKE = "SNOWFLAKE"


class FileType(str, Enum):

    CSV = "CSV"

    Parquet = "Parquet"

    Image = "Image"

    PDF = "PDF"


class BigQueryDatasetType(str, Enum):

    TABLE = "TABLE"

    QUERY = "QUERY"


class WidgetState(str, Enum):

    IDLE = "IDLE"

    IGNORE = "IGNORE"


class WorkflowState(str, Enum):

    IDLE = "IDLE"

    IGNORE = "IGNORE"


class ModelType(str, Enum):

    LIGHT_GBM = "LIGHT_GBM"


class ScalingMethod(str, Enum):

    MIN_MAX = "MIN_MAX"

    STANDARD = "STANDARD"

    ROBUST = "ROBUST"


class OptimizationMethod(str, Enum):

    GRID_SEARCH = "GRID_SEARCH"

    RANDOM_SEARCH = "RANDOM_SEARCH"


class RandomSearchConfig(BaseModel):

    n_iter: int = Field(50, description="Number of iterations for random search")


class SaveOptions(str, Enum):

    DATASET = "DATASET"

    JSON = "JSON"

    MODEL = "MODEL"

    RESULTS = "RESULTS"

    VARIABLES = "VARIABLES"


class DropColumnsConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    selected_columns: List[str]


class DropColumnsActivityConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[
        WidgetType.DROP_COLUMNS
    ]  # To validate if the correct widget is selected

    config: DropColumnsConfig = Field(..., description="Drop Columns config")


class RenameConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    columns_to_rename: Dict[str, str] = Field(
        ..., description="Mapping of old column names to new column names"
    )


class RenameActivityConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[
        WidgetType.RENAME_COLUMNS
    ]  # To validate if the correct widget is selected

    config: RenameConfig = Field(..., description="Rename config")


class PreviewStatsConfig(BaseModel):

    job_type: Literal[ApiJobType.PREVIEW_STATS] = Field(ApiJobType.PREVIEW_STATS)

    dataset_id: str = Field(
        ..., description="dataset id for generating preview and stats"
    )


class UniqueValuesConfig(BaseModel):
    job_type: Literal[ApiJobType.UNIQUE_VALUES] = Field(ApiJobType.UNIQUE_VALUES)

    dataset_id: str = Field(..., description="dataset id for generating unique values")

    column_name: str = Field(
        ..., description="column name for which unique values are to be generated"
    )

class ExtDataPullConfig(BaseModel):

    job_type: Literal[ApiJobType.EXTERNEL_DATA_PULL] = Field(ApiJobType.EXTERNEL_DATA_PULL)

    superset_db_id: int = None


class ApiVisualizationConfig(BaseModel):

    job_type: Literal[ApiJobType.VISUALIZATION] = Field(ApiJobType.VISUALIZATION)

    dataset_id: str = Field(
        ..., description="dataset id for generating preview and stats"
    )

    visualization: DataVisualization = Field(..., description="visualization object")

    visualization_hash: str = Field(..., description="hash of visualization object")


class ApiCorrelationConfig(BaseModel):

    job_type: Literal[ApiJobType.CORRELATION] = Field(ApiJobType.CORRELATION)

    dataset_id: str = Field(
        ..., description="dataset id for generating preview and stats"
    )

    correlation_schema: CorrelationInputSchema = Field(
        ..., description="Correlation schema object"
    )

    correlation_hash: str = Field(..., description="hash of correlation schema object")


class ApiJobsConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[
        WidgetType.API_JOBS
    ]  # To validate if the correct widget is selected

    config: Annotated[
        Union[
            PreviewStatsConfig,
            ApiVisualizationConfig,
            ApiCorrelationConfig,
            UniqueValuesConfig,
            ExtDataPullConfig,
        ],
        Field(
            ...,
            discriminator="job_type",
            description="Configs of jobs submitted for apis",
        ),
    ]


class DTypeConversion(str, Enum):
    # INTEGER = "int16"
    # INTEGER = "int32"
    INTEGER = "int64"
    # FLOAT = "float16"
    # FLOAT = "float32"
    FLOAT = "float64"
    STRING = "string"
    DATE = "object"
    DATETIME = "datetime64[ns]"


class DataTypeConversionConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    column_type_mapping: Dict[str, str] = Field(
        ..., description="Mapping of column names to new data types"
    )

    @validator("column_type_mapping", pre=True)
    def validate_column_types(cls, value):
        valid_types = {dtype.name for dtype in DTypeConversion}  # Use enum member names
        for col, dtype in value.items():
            if dtype not in valid_types:
                raise ValueError(
                    f"Invalid data type '{dtype}' for column '{col}'. Must be one of: {list(valid_types)}."
                )
        return value

    # pref_type: DTypeConversion = Field(...,description="Preferred data type if needed")


class DataTypeConversionActivityConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[
        WidgetType.DATATYPE_CONVERSION
    ]  # To validate if the correct widget is selected

    config: DataTypeConversionConfig = Field(
        ..., description="Datatype Conversion config"
    )


class FilterType(str, Enum):

    FILTER_BY_COLUMN_VALUES = "FILTER_BY_COLUMN_VALUES"


class CustomFunctionInputOutputTypes(str, Enum):

    DATA_FRAME = "DATA_FRAME"

    JSON = "JSON"

    STRING = "STRING"

    FILE_PATH = "FILE_PATH"


class CustomFunctionAcceptedPythonClasses(str, Enum):

    PANDAS = "<class 'pandas.core.frame.DataFrame'>"

    STRING = "<class 'str'>"

    INTEGER = "<class 'int'>"

    FLOAT = "<class 'float'>"

    JSONS = "typing.List[pydantic.Json]"

    DICTIONARY = "<class 'dict'>"

    TEXT_CPW_DATASET = "<class 'app.services.data.assets.custom_python_support.service.TextCPWDataset'>"

    STRINGS_LIST = "list[str]"  # Supporting list of strings

    FLOATS_LIST = "list[float]"  # Supporting list of floats

    INTEGERS_LIST = "list[int]"  # Supporting list of integers

    PATHLIB_PATH = "<class 'pathlib.Path'>"

class BigQueryDatasetTableConfig(BaseModel):

    dataset_name: str = Field(..., description="BigQuery Dataset Name")

    table_name: str = Field(..., description="BigQuery Table to be copied")


# class BigQueryDatasetQueryConfig(BaseModel):

#     query: str = Field(..., description="BigQuery SQL Query output to be copied")


class BigQueryDatasetConfig(BaseModel):

    project_id: str = Field(..., description="GCP Project ID")

    dataset_type: BigQueryDatasetType = Field(..., description="BigQuery Dataset Type")

    dataset: Union[BigQueryDatasetTableConfig, BigQueryDatasetQueryConfig] = Field(
        ..., description="BigQuery Dataset config"
    )

class SnowflakeDatasetConfig(BaseModel):

    project_id: str = Field(..., description="GCP Project ID")

    dataset_type: SnowFlakeDatasetTypes = Field(
        ..., description="Snowflake Dataset Type"
    )

    dataset: Union[SFDatasetTableConfig, SFDatasetQueryConfig] = Field(
        ..., description="Snowflake Dataset config"
    )

class SnowflakeDatasetConfiguration(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the widget")

    snowflake_connector_id: str = Field(
        ..., description="Authentication details for Snowflake"
    )

    dataset_configuration: SnowflakeDatasetConfig = Field(
        ..., description="bigquery dataset configuration"
    )


class LocalFileConfiguration(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the widget")

    dataset_id: str = Field(
        ..., description="Id of existing dataset id uploaded using /upload API"
    )


class MountedDriveConfiguration(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the widget")

    dataset_id: str = Field(
        ..., description="Id of existing dataset id uploaded using /upload API"
    )


class BigQueryDatasetConfiguration(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the widget")

    bigquery_connector_id: str = Field(
        ..., description="Authentication details for BigQuery"
    )

    dataset_configuration: BigQueryDatasetConfig = Field(
        ..., description="bigquery dataset configuration"
    )


class SourceConfiguration(BaseModel):
    type: SourceType = Field(..., description="Source type")

    configuration: Union[
        LocalFileConfiguration,
        BigQueryDatasetConfiguration,
        SnowflakeDatasetConfiguration,
        MountedDriveConfiguration,
    ] = Field(..., description="Source Configuration")


class Sink(BaseModel):

    dataset_name: str = Field(
        ..., description="User defined name for the ingested dataset"
    )

    dataset_description: str= Field(
        ..., description="User defined description for the dataset"
    )


class DataCopyActivityConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[WidgetType.DATA_COPY]

    source: SourceConfiguration = Field(..., description="Source configuration")

    sink: Optional[Sink] = Field(default=None, description="Sink configuration")

    @validator("sink", always=True)  # validation for sink
    def check_sink_based_on_source(cls, v, values):
        if "source" in values and values["source"].type == SourceType.LOCAL:
            return v  # Allows 'sink' to be None if source type is LOCAL
        if v is None:
            raise ValueError(
                "Sink configuration is required for non-LOCAL source types"
            )
        return v

class TextConfig(BaseModel):
    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[WidgetType.TEXT_DATA]
    
    source: List[SourceConfiguration] = Field(..., description="Source configuration")

    sink: List[Sink] = Field(default=None, description="Sink configuration")



class DropMissingConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    selected_columns: Optional[List[str]] = None


class DropMissingActivityConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[
        WidgetType.DROP_MISSING
    ]  # To validate if the correct widget is selected

    config: DropMissingConfig = Field(..., description="DropMissing config")


class FilterOperator(str, Enum):
    EQ = "EQ"
    NE = "NE"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    BETWEEN = "BETWEEN"
    REGEX = "REGEX"


class StringFilterOperator(str, Enum):
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    EXACT_MATCH = "EXACT_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"


class FilterOperand(str, Enum):
    AND = "AND"
    OR = "OR"
    XOR = "XOR"


class DFDataTypes(str, Enum):
    NUMERICAL = "NUMERICAL"
    CATEGORICAL = "CATEGORICAL"


class FilterValues(BaseModel):

    column_name: str = Field(..., description="Column name to apply column filter")

    operator: Union[FilterOperator, StringFilterOperator] = Field(
        ..., description="Filter Operator"
    )

    value: Union[
        str, int, bool, float, datetime, List[Union[str, int, bool, float, datetime]]
    ]

    data_type: Optional[DFDataTypes] = None


class FilterConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    filter_operands: Optional[Union[FilterOperand, List[FilterOperand]]] = Field(
        default=FilterOperand.AND, description="Filter operands"
    )

    filter_values: List[FilterValues] = Field(..., description="Filter values")


class FilterActivityConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[WidgetType.FILTER]

    type: FilterType = Field(..., description="Filter type")

    config: FilterConfig = Field(..., description="Filter config")


class CustomFunctionOutputs(BaseModel):

    type: Union[CustomFunctionInputOutputTypes, CustomFunctionAcceptedPythonClasses] = (
        Field(..., description="Type of input required")
    )

    arg_name: str = Field(
        ...,
        description="Name of the keyword argument in the custom code function output",
    )


class CustomFunctionInputs(BaseModel):
    type: Union[CustomFunctionInputOutputTypes, CustomFunctionAcceptedPythonClasses] = (
        Field(..., description="Type of input required")
    )

    input_urn: Optional[str] = Field(
        default=None, description="Input from which previous widget"
    )

    arg_name: str = Field(
        ..., description="Name of the keyword argument in the custom code function"
    )


class WidgetInputParametersUIType(str, Enum):
    TEXT_BOX = "TEXT_BOX"
    CSV_BROWSE_BUTTON = "CSV_BROWSE_BUTTON"


class BrowseButtonConfig(BaseModel):
    allowed_suffixes: List[str]


class WidgetParameterDetails(BaseModel):
    ui_type: WidgetInputParametersUIType
    ui_config: Optional[BrowseButtonConfig]


class CustomFunctionParameters(BaseModel):
    type: CustomFunctionAcceptedPythonClasses

    arg_name: str

    value: Optional[ActionResult] = Field(
        default=None, description="default_value from builder"
    )

    is_mandatory: bool = Field(default=True)

    default_value: Optional[ActionResult] = Field(
        default=None, description="default_value from builder"
    )

    ui_details: Optional[Union[WidgetParameterDetails]] = Field(
        default=None, description="Used in UI to show details"
    )

    drop_down_details: Optional[DropDownDetails] = Field(
        default=None, description="details about drop down"
    )


class CustomCodeActivityConfig(BaseModel):
    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_id: Optional[str] = Field(
        default=None, description="Widget Id from which module id is selected."
    )

    widget_type: Literal[WidgetType.CUSTOM_CODE]

    module_id: str = Field(
        ..., description="ID of the uploaded module using /upload API"
    )

    function_inputs: List[CustomFunctionInputs] = Field(
        ..., description="Function inputs that come during run time"
    )

    widget_parameters: Optional[List[CustomFunctionParameters]] = Field(
        default=None, description="Function inputs configured as parameters"
    )

    function_outputs: List[CustomFunctionOutputs] = Field(
        ..., description="Function outputs"
    )

    propagate_widget_changes: Optional[bool] = Field(
        default=True,
        description="Picks updated function inputs,module_id..etc on widget update",
    )


class SaveScope(str, Enum):

    GLOBAL = "GLOBAL"
    WORKFLOW = "WORKFLOW"
    RUN = "RUN"


class SaveConfig(BaseModel):

    name: str = Field(..., description="name of the saved object")

    description: str = Field(default="", description="description for the saved object")

    scope: SaveScope = Field(default=SaveScope.RUN, description="saved asset scope")


class SaveActivityConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[WidgetType.SAVE]

    type: SaveOptions = Field(..., description="save options")

    config: SaveConfig = Field(..., description="Save configuration")


class DestinationTypes(str, Enum):
    MOUNTED_DRIVE = "MOUNTED_DRIVE"
    HEXAIND_PLATFORM = "HEXAIND_PLATFORM"
    CUSTOM_PATH = "CUSTOM_PATH"


class FileFormatOptions(str, Enum):
    CSV = "CSV"
    PARQUET = "PARQUET"
    EXCEL = "EXCEL"


class FileSaveOptions(str, Enum):
    REPLACE = "REPLACE"
    SAVE_AS = "SAVE_AS"


class SaveAsConfig(BaseModel):
    file_name: str


class ReplaceConfig(BaseModel):
    existing_dataset_id: str
    destination_path: str


class SaveOptionConfig(BaseModel):
    file_Format: FileFormatOptions
    save_options: FileSaveOptions
    save_option_config: Union[ReplaceConfig, SaveAsConfig]
    destination_folder_path: Optional[str] = None


class DatasetConfiguration(BaseModel):
    dataset_name: str
    destination_type: DestinationTypes
    destination_config: SaveOptionConfig
    doNotSaveFlag: bool = False


class SaveWidgetConfig(BaseModel):
    version: str = "1.0"

    widget_type: Literal[WidgetType.SAVE]

    datasetConfig: List[DatasetConfiguration]

    # this is added as part of the config validation
    # commented for partial save feature

    # @field_validator('datasetConfig')
    # def dataset_config_must_not_be_empty(cls, v):
    #     if len(v) == 0:
    #         raise ValueError(f"Save widget dataset config is empty")
    #     return v


class LGBMModelParameters(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    min_depth: int = Field(..., description="min_depth")

    max_depth: int = Field(..., description="max_depth")

    sample_no_depth: int = Field(..., description="sample_no_depth")

    min_num_leaves: int = Field(..., description="min_num_leaves")

    max_num_leaves: int = Field(..., description="max_num_leaves")

    sample_no_num_leaves: int = Field(..., description="sample_no_num_leaves")

    min_child_samples: int = Field(..., description="min_child_samples")

    max_child_samples: int = Field(..., description="max_child_samples")

    sample_no_child_samples: int = Field(..., description="sample_no_child_samples")


class ModelBuilderConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[WidgetType.MODEL_BUILDER]

    input_columns: List[str]

    output_column: str

    scaling_method: Optional[ScalingMethod]

    hyper_parameter_optimization_method: Optional[OptimizationMethod]

    test_data_split_ratio: float = Field(default=30)

    random_search_params: Optional[RandomSearchConfig] = None

    n_folds: int = Field(5, description="Number of cross-validation folds")

    random_state: Optional[int]

    model: ModelType

    parameters: LGBMModelParameters


class ColumnType(str, Enum):
    OBJ_TYPE = "object"
    INT_TYPE = "int64"
    FLOAT_TYPE = "float64"
    BOOL_TYPE = "bool"
    NONE_TYPE = "None"


class ColumnAndType(BaseModel):
    column_name: str
    pref_type: ColumnType


class AppendConfig(BaseModel):
    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[WidgetType.APPEND]

    max_rows: int = Field(description="Maximum number of rows to append", default=0)

    ignore_index: bool = Field(
        description="If True, do not use the index labels", default=True
    )

    column_type_pref_list: Optional[List[ColumnAndType]] = []

    convert_words_to_number: Optional[bool] = True


class JoinType(str, Enum):
    INNER = "INNER"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    OUTER = "OUTER JOIN"


class JoinConfig(BaseModel):

    widget_type: Literal[WidgetType.JOIN]

    left_column: Optional[str] = ""

    right_column: Optional[str] = ""

    left_columns: Optional[List[str]] = []

    right_columns: Optional[List[str]] = []

    join_type: JoinType


class DecisionCriteria(BaseModel):
    field: str

    operator: str

    value: Any


class DecisionActivityConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[WidgetType.DECISION]

    criteria: DecisionCriteria = Field(
        ..., description="This is optional(Criteria for making the decision)"
    )


class Dummy(BaseModel):

    xyz: int
    abc: int


class LoopStartConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[WidgetType.LOOP_START]

    loop_start_config: Dummy = Field(
        ..., description="config for the loop-start widget"
    )


class TerminationCriteria(str, Enum):

    ON_LOOP_COUNT = "ON_LOOP_COUNT"

    CUSTOM_CODE = "CUSTOM_CODE"


class CustomCodeTerminationCriteriaConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    module_id: str = Field(
        ..., description="ID of the uploaded module using /upload API"
    )

    function_inputs: List[CustomFunctionInputs] = Field(
        ..., description="Function inputs"
    )


class OnLoopTerminationCriteriaConfig(BaseModel):

    loop_count: int = Field(..., description="based on no.of passes through the cycle")


class LoopEndConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[WidgetType.LOOP_END]

    termination_criteria: TerminationCriteria = Field(
        ..., description="type of termination criteria"
    )

    loop_end_config: Union[
        OnLoopTerminationCriteriaConfig, CustomCodeTerminationCriteriaConfig
    ] = Field(default={}, description="config for the loop-start widget")

    on_loop: List[str] = Field(..., description="widget urns's for loop continutation")

    on_termination: List[str] = Field(
        ..., description="widget urns's for loop terimination"
    )


class InputOutputConfig(BaseModel):

    urn: str = Field(..., description="input widget urn")

    map_to_argument: Optional[str] = Field(
        default="",
        description="argument name to pass this as input (when multiple inputs are accepted by widget)",
    )

    type: Optional[ActionResultType] = Field(
        default=None,
        description="used in verification and converstion from functions outputs to custom code widget ouputs",
    )

    name: str = Field(..., description="unique name of the input/output for the widget")


class JupyterServerConfig(BaseModel):
    memory_limit: str = Field(default="2G", description="memory limit")
    cpu_limit: float = Field(default=2, description="cpu limit")
    notebook_dir: str = Field(default="/home/jovyan/work", description="notebook root dir")
    notebook_image: str = Field(default="jupyter/base-notebook:latest", description="notebook docker image")

class JupyterConfig(JupyterServerConfig):
    version: str = Field(default="1.0", description="Version of the widget")
    widget_type: Literal[WidgetType.JUPYTER]
    notebook_file: str = Field(description="notebook file selected")


WidgetConfig = Annotated[
    Union[
        DataCopyActivityConfig,
        FilterActivityConfig,
        CustomCodeActivityConfig,
        ModelBuilderConfig,
        DecisionActivityConfig,
        MOBOConfig,
        RescaleConfig,
        PostRescaleConfig,
        LoopStartConfig,
        LoopEndConfig,
        AppendConfig,
        JoinConfig,
        ThermocalcConfig,
        SaveWidgetConfig,
        GPRConfig,
        AutoMLConfig,
        RandomForestConfig,
        LinearRegressionConfig,
        LGBMConfig,
        XGBoostConfig,
        CATBoostConfig,
        NNFastAIConfig,
        KNNConfig,
        ExtraTreesConfig,
        NNTorchConfig,
        GPCConfig,
        SVMRConfig,
        PredictionConfig,
        DropMissingActivityConfig,
        DropColumnsActivityConfig,
        RenameActivityConfig,
        DataTypeConversionActivityConfig,
        MPRConfig,
        ApiJobsConfig,
        ImageDatasetConfig,
        RegionPropertiesConfig,
        SpatialStatisticsConfig,
        TextConfig,
        JupyterConfig,

    ], Field(
        discriminator="widget_type",
    ),
]


class WidgetConfig_(RootModel):
    root: WidgetConfig


class Widget(BaseModel):

    urn: str = Field(
        ..., description="Unique Resource name for the widget in the workflow"
    )

    name: str = Field(..., description="Custom widget name")

    description: str = Field(default="", description="Custom workflow description")

    type: WidgetType = Field(..., description="Type of widget in hexaind-platform")

    config_file_path: Optional[str] = None

    config: Optional[WidgetConfig] = Field(
        default=None, description="Custom widget config"
    )

    state: WidgetState = Field(
        default=WidgetState.IDLE, description="Type of widget in hexaind-platform"
    )

    on_success: Union[List[str], str] = Field(
        default=[], description="Action IDs of widget it is dependent on"
    )

    on_failure: Union[List[str], str] = Field(
        default=[], description="Action IDs of widget it is dependent on"
    )

    on_complete: Union[List[str], str] = Field(
        default=[], description="Action IDs of widget it is dependent on"
    )

    inputs: List[InputOutputConfig] = Field(
        default=[], description="Inputs configured for the widgets"
    )

    outputs: List[InputOutputConfig] = Field(
        default=[], description="Outputs configured for the widgets"
    )

    use_gpu: bool = Field(default=False, description="mode of task execusion")

    retry_interval_in_sec: int = Field(
        default=0, ge=0, description="retry task in seconds"
    )

    retry_count: int = Field(
        default=0, ge=0, description="no.of times we can retry the task"
    )

    client_tags: Optional[dict] = Field(
        default={},
        description="JSON object representing a list of properties used by the UX for a widget.",
    )

    @model_validator(mode="before")
    @classmethod
    def file_loading(cls, data: dict) -> dict:
        if data.get('config_file_path') is None or data.get('config') is not None:
            return data
        
        with open(data["config_file_path"]) as config_file:
            data["config"] = json.load(config_file)
        
        return data


class Workflow(BaseModel):

    id: Optional[str] = Field(default=None, description="Workflow Id", alias="_id")

    interactive_mode: bool = Field(
        default=False,
        description="It will represents the worklfow is interactive or regular",
    )

    name: str = Field(..., description="Workflow name")

    description: str = Field(..., description="Workflow description")

    workflow_version: str = Field(default="", description="Workflow version")

    widgets: List[Widget] = Field(
        default=[], description="List of Widgets in the workflow"
    )

    state: WorkflowState = Field(
        default=WorkflowState.IDLE, description="Type of widget in hexaind-platform"
    )

    start: List[str] = Field(
        default=[],
        description="single or multiple widgets at the begining of the workflow",
    )

    end: List[str] = Field(
        default=[], description="single or multiple actions at the end of the workflow"
    )

    owner_id: str = Field(
        default=None, description="ID of the user who created the workflow"
    )

    owner_name: str = Field(
        default=None, description="Name of the user who created the workflow"
    )

    created_at: datetime = Field(
        default=None, description="Created Date and Time UTC format"
    )

    last_modified_by_id: str = Field(
        default=None, description="ID of the user who recently modified the workflow"
    )

    last_modified_at: datetime = Field(
        default=None, description="Created Date and Time UTC format"
    )

    project_id: str = Field(default=None, description="Project ID")

    site_id: str = Field(default=None, description="Project ID")

    version: Optional[str] = Field(default="1.0", description="Version of the workflow")

    client_tags: Optional[dict] = Field(
        default={},
        description="JSON object representing a list of properties used by the UX for the workflow.",
    )

    is_valid: Optional[bool] = Field(
        default=True, description="Indicate saved workflow is valid or not"
    )

    validation_errors: Optional[List[dict]] = Field(
        default=[], description="Workflow Validation Errors"
    )

    partial_widgets: Optional[List[dict]] = Field(
        default=[], description="To store the partially filled widgets"
    )

    favourited_by: Optional[List[str]] = Field(default=[], description="favouritee")

    is_template: Optional[bool] = Field(
        default=False, description="Indicates if the session is a template"
    )

    template_screenshot: Optional[str] = Field(
        default=None, description="Indicates the session has template screenshot"
    )

    is_master: bool = Field(
        default=True, description="Indicates the worflow is a master or published"
    )


class CreateWorkflowResponse(BaseModel):

    workflow_id: str


class GetAllWorkflowsResponse(BaseModel):

    workflows: List[Workflow]

    workflows_count: int

    page_number: int

    page_limit: int


class UpdateWorkflowResponse(BaseModel):

    success: bool


class TabularDatasetFileExtensions(str, Enum):

    CSV = "CSV"

    PARQUET = "PARQUET"


class ImageDatasetFileExtensions(str, Enum):

    PNG = "PNG"

    JPEG = "JPEG"


class ModelWidgetResultSubTypes(str, Enum):

    LGBM = "LGBM"


class WidgetInputOutputConfigBounds(BaseModel):

    min: int = Field(
        default=1,
        description="Minimum number of times a imput type is expected by widget",
    )

    max: int = Field(
        default=-1,
        description="Maximum number of times a imput type is expected by widget",
    )


class TabularDatasetConstraints(BaseModel):

    file_extension: TabularDatasetFileExtensions

    file_size: Optional[int]

    num_rows: Optional[int]

    num_columns: Optional[int]

    required_columns: Optional[List[str]]

    required_schemas: Optional[dict]


class ImageDatasetConstraints(BaseModel):

    file_extension: ImageDatasetFileExtensions

    file_size: Optional[int]

    dimensions: Optional[str]


class DatasetTypes(str, Enum):

    TABULAR = "TABULAR"

    IMAGE = "IMAGE"

    JSON = "JSON"

    PDF = "PDF"

    TEXT = "TEXT"


class DatasetConstraints(BaseModel):

    sub_type: DatasetTypes

    constraints: Optional[
        Union[TabularDatasetConstraints, ImageDatasetConstraints, None]
    ] = Field(default=None)


class ModelConstraints(BaseModel):
    pass


class WidgetInputOutputConfig(BaseModel):

    count: Optional[Union[int, WidgetInputOutputConfigBounds]] = Field(
        default=1, description="Total number of times this input type is expected"
    )

    expected_type: ActionResultType

    expected_type_constraints: Optional[DatasetConstraints] = Field(default=None)

    optional: Optional[bool] = Field(default=False)


class WidgetInputOutputs(BaseModel):

    count: Union[int, WidgetInputOutputConfigBounds] = Field(
        default=1,
        description="Total number of inputs widget can accept: if -1 it can accept 0..N number of inputs",
    )

    config: List[WidgetInputOutputConfig] = Field(
        default=[],
        description="List of each input configs. if WidgetInputs.count != -1 the len of the list should be equal to the WidgetInputs.count",
    )


class WidgetRule(BaseModel):

    inputs: WidgetInputOutputs

    outputs: WidgetInputOutputs
