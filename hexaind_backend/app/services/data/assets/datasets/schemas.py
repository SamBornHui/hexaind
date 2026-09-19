from __future__ import annotations

import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator, ValidationError

from app.services.workflows.designer.base_schemas import WidgetType
from app.services.AI.gpr.schemas import GPRConfig
from app.services.AI.automl.schemas import AutoMLConfig
from app.services.AI.randomforest.schemas import RandomForestConfig
from app.services.AI.linear_regression.schemas import LinearRegressionConfig
from app.services.AI.lgbm.schemas import LGBMConfig
from app.services.AI.xgboost.schemas import XGBoostConfig
from app.services.AI.catboost.schemas import CATBoostConfig
from app.services.AI.extratrees.schemas import ExtraTreesConfig
from app.services.AI.nn_torch.schemas import NNTorchConfig
from app.services.AI.nnfastai.schemas import NNFastAIConfig
from app.services.AI.k_nearest_neighbors.schemas import KNNConfig
from app.services.AI.gaussian_process_cls.schemas import GPCConfig
from app.services.AI.svm.schemas import SVMRConfig
from app.services.AI.multi_polynomial_regression.schemas import MPRConfig
from app.services.apps.scrap_analysis.schemas import SAMCustomInformation


class DatasetSubType(
    str, Enum
):  # This subtypes will be useful for under single data type if we have any special structure of data (ex: under tabular we have mobo recommendations/thermocalc)
    THERMOCALC_RESULTS = "THERMOCALC_RESULTS"
    PREDICTION_RESULTS = "PREDICTION_RESULTS"


class DatasetType(str, Enum):
    TABULAR = "TABULAR"
    MOBO_RECOMMENDATIONS = "MOBO_RECOMMENDATIONS"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    PDF = "PDF"
    JSON = "JSON"
    TEXT = "TEXT"
    FOLDER = "FOLDER"
    IMAGE_DATASET = "IMAGE_DATASET"
    IMAGES_FOLDER = "IMAGES_FOLDER"
    PYTHON = "PYTHON"
    PLOT = "PLOT"


class UploadStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INPROGRESS = "INPROGRESS"


class GraphType(str, Enum):
    DISTRIBUTION = "DISTRIBUTION"
    CONTOUR = "CONTOUR"
    SPLINEFIT = "SPLINEFIT"
    LINEARFIT = "LINEARFIT"


class AccessMode(str, Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class UploadPlace(str, Enum):
    WORKFLOWS = "WORKFLOWS"
    DATASETS = "DATASETS"


class TabularColumnType(str, Enum):

    NUMERICAL = "NUMERICAL"

    CATEGORICAL = "CATEGORICAL"


class ColumnStatistics(BaseModel):
    name: str
    type: TabularColumnType
    parameters: dict


class Visualization(BaseModel):
    x_axis: str
    y_axis: str
    graph: str
    graph_type: GraphType
    color_by: str


class DatasetSchema(BaseModel):
    column_name: str
    data_type: str


class UploadStats(BaseModel):
    percentage: str


class DatasetLocation(BaseModel):
    isfolder: bool
    size: str
    extension: str
    path: str
    last_modified_by: Optional[str] = None
    last_modified_at: datetime.datetime | None = Field(
        default_factory=datetime.datetime.utcnow
    )


class RescaleMediaFiles(BaseModel):
    trail_number: str
    media_files: List[DatasetLocation]


class RescaleWidgetCustomInformation(BaseModel):
    trail_data: List[RescaleMediaFiles]


class TabularDatasetInformation(BaseModel):
    preview: Union[dict, None] = Field(default=None)
    statistics: Union[List[ColumnStatistics], None] = Field(default=None)
    row_count: Optional[int] = Field(default=None)
    col_count: Optional[int] = Field(default=None)
    visualize: Union[List[Visualization], None] = Field(default=None)
    dataset_schema: Union[List[DatasetSchema], None] = Field(default=None)

    # Adding new fields for storing paths to statistics files
    numerical_statistics_file: Optional[str] = None
    numerical_col_count: Optional[int] = Field(default=None)
    categorical_statistics_file: Optional[str] = None
    categorical_col_count: Optional[int] = Field(default=None)

    preview_file: Optional[str] = None


class TabularDatasetInformationAndMetadata(BaseModel):
    tabular_dataset_info: TabularDatasetInformation
    metadata: DatasetMetadata


class WorkflowDatasetCustomInformation(BaseModel):
    widget_type: WidgetType
    custom_information: Union[RescaleWidgetCustomInformation, None] = Field(
        default=None
    )


class DatasetSourceFormats:
    LOCAL_FILE_UPLOAD_FORMAT = "Local File Upload({})"
    MOUNTED_DRIVE_FILE_UPLOAD_FORMAT = "Mounted Drive File Upload({})"
    GENERATED_FROM_EXISTING_DATASET_FORMAT = "Generated From Existing Dataset({})"
    GENERATED_IN_WORKFLOW_EXECUTION_FORMAT = "Generated In Workflow Execution({})"
    GENERATED_IN_DATA_CATALOG_FORMAT = "Generated In Data Catalog"


class DatasetMetadata(BaseModel):
    data_source: Optional[str] = Field(default="")
    columns_metadata: Optional[dict] = None
    columns_metadata_file: Optional[str] = None


class Dataset(BaseModel):
    id: Optional[str] = Field(default=None, description="Workflow Id", alias="_id")
    version: Optional[str] = Field(default="1.0")
    user_id: str
    project_id: str
    site_id: str
    action_id: str
    name: str
    description: str
    dataset_type: DatasetType
    dataset_sub_type: Optional[DatasetSubType] = Field(
        default=None,
        description="To identify the underlying structure of the main data. Ex: mobo recommendations. So that processing logic will vary accordingly",
    )
    dataset_information: List[TabularDatasetInformation] = Field(default=[])
    upload_status: UploadStatus
    upload_stats: UploadStats
    metadata: Optional[DatasetMetadata] = Field(
        default={}
    )  # Define this more precisely based on the structure of 'metadata'
    created_at: datetime.datetime
    created_by: Optional[str] = Field(default=None)
    dataset_location: List[DatasetLocation]
    access_mode: AccessMode
    tags: List[str]
    excel_sheets_name: Optional[List[str]] = Field(default=None)
    custom_information: Optional[
        Union[WorkflowDatasetCustomInformation, None, SAMCustomInformation]
    ] = Field(default=None)
    api_job_id: Optional[str] = Field(default="")
    visualization_paths: Optional[Dict[str, str]] = Field(
        default={},
        description="Dictionary mapping hash of visualization config to visualization path",
    )
    visualization_job_ids: Optional[Dict[str, str]] = Field(
        default={},
        description="Dictionary mapping hash of visualization config to visualization API job ID",
    )
    correlation_paths: Optional[Dict[str, str]] = Field(
        default={},
        description="Dictionary mapping hash of correlation config to correlation data path",
    )
    correlation_job_ids: Optional[Dict[str, str]] = Field(
        default={},
        description="Dictionary mapping hash of correlation config to correlation API job ID",
    )


class ApiJobType(str, Enum):
    PREVIEW_STATS = "PREVIEW_STATS"
    VISUALIZATION = "VISUALIZATION"
    CORRELATION = "CORRELATION"
    UNIQUE_VALUES = "UNIQUE_VALUES"
    EXTERNEL_DATA_PULL = "EXTERNEL_DATA_PULL"


class ApiJob(BaseModel):
    id: Optional[str] = Field(default=None, description="ApiJob Id", alias="_id")
    version: Optional[str] = Field(default="1.0", description="ApiJob Version")
    api_job_type: ApiJobType = Field(..., description="ApiJob Type")
    dataset_id: str = Field(..., description="Dataset Id")
    visualization_hash: Optional[str] = Field(
        default=None, description="hash of visualization config"
    )
    correlation_hash: Optional[str] = Field(
        default=None, description="hash of corelation config"
    )
    action_id: Optional[str] = Field(default=None, description="Action Id")
    user_id: str = Field(..., description="User Id")
    created_at: datetime.datetime = Field(..., description="ApiJob Created At")
    column_name: Optional[str] = Field(default=None, description="Column Name")

    @model_validator(mode="after")
    def check_hashes(cls, obj):
        if (
            obj.api_job_type == ApiJobType.VISUALIZATION
            and obj.visualization_hash is None
        ):
            raise ValidationError(
                "visualization_hash cannot be null when api_job_type is VISUALIZATION"
            )
        if obj.api_job_type == ApiJobType.CORRELATION and obj.correlation_hash is None:
            raise ValidationError(
                "correlation_hash cannot be null when api_job_type is CORRELATION"
            )
        if obj.api_job_type == ApiJobType.UNIQUE_VALUES and obj.column_name is None:
            raise ValidationError(
                "column_name cannot be null when api_job_type is UNIQUE_VALUES"
            )

        return obj


class DeleteModelsResponse(BaseModel):
    status: str
    deleted_count: int = 0


class ModelDetails(BaseModel):
    name: str
    type: str
    ml_sub_type: Optional[str] = Field(default=None)
    configs: Union[
        AutoMLConfig,
        GPRConfig,
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
        MPRConfig,
    ]
    testing_samples: int
    training_samples: int
    cv_metrics: Optional[Dict] = Field(default=None)
    dataset_name: str
    metrics: Dict
    additional_info: Optional[Dict] = Field(default=None)
    feature_imp_plot: Optional[Union[str, List]] = Field(None)
    feature_imp_plot_violen: Optional[Union[str, List]] = Field(None)
    visualizations: Optional[List[str]] = Field(None)


class MLFlowDetail(BaseModel):
    experiment_id: str
    experiment_name: str
    run_id: str


class DeployedStatus(str, Enum):
    trained = "trained"
    deployed = "deployed"


class MLDeploymentStatus(BaseModel):
    status: DeployedStatus = Field(
        default=DeployedStatus.trained, description="model current status"
    )
    port: int = Field(default=0, description="port no where model deployed")


class MachineLearningModel(BaseModel):
    id: Optional[str] = Field(default=None, description="Workflow Id", alias="_id")
    version: Optional[str] = Field(default="1.0")
    user_id: str
    user_name: str
    project_id: str
    site_id: str
    wf_run_id: str
    widget_urn: Optional[str] = Field(default=None, description="widget urn")
    description: str
    created_at: datetime.datetime
    ml_model_file_path: str
    access_mode: AccessMode
    tags: List[str]
    model: ModelDetails
    ml_flow_detail: MLFlowDetail
    dataset_path: Optional[str] = Field(default=None, description="dataset path")
    ml_deployed_status: MLDeploymentStatus = Field(default_factory=MLDeploymentStatus)


class AssetsListResponse(BaseModel):

    datasets: List[Dataset]

    total_count: int


class DatasetUploadResponse(BaseModel):

    dataset_id: str


class DatasetFileTypes(str, Enum):

    CSV = "CSV"
    PARQUET = "PARQUET"
    JSON = "JSON"
    TEXT = "TEXT"
    EXCEL = "EXCEL"


class DatasetSource(str, Enum):
    LOCAL = "LOCAL"
    MOUNTED_DRIVE = "MOUNTED_DRIVE"


class TabularDatasetField(BaseModel):
    column_name: str = Field(description="Name of field in schema")
    column_type: TabularColumnType = Field(
        description="Data types from SchemaFieldType"
    )


class MountedFile(BaseModel):
    name: str
    type: str = "file"
    full_path: Optional[Path]


class MountedFolder(BaseModel):
    name: str
    type: str = "folder"
    children: List[MountedFile] = []


class DatasetRenameBody(BaseModel):
    dataset_id: str
    name: str


class DatasetRenameResponse(BaseModel):
    status: bool
    new_name: Optional[str] = None
    message: str


class DatasetDeleteType(str, Enum):

    HARD = "HARD"  # delete dataset with the files in it

    SOFT = "SOFT"  # mark dataset it as internal


class DeleteDatasetResponseStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"


class DeleteDatasetResponse(BaseModel):
    dataset_id: str
    status: DeleteDatasetResponseStatus
    message: Optional[str]


class DeleteDatasetsRequest(BaseModel):
    dataset_ids: List[str]
    dataset_type: str


class DeleteDatasetsResponse(BaseModel):
    response: List[DeleteDatasetResponse]


class DatasetFileDataPreviewResponse(BaseModel):
    file_data: Union[str, bytes] = None
    next_page_number: int = 0
    error_message: Optional[str] = None


class GetFilesListMountedRequest(BaseModel):
    folder_path: str = Field(default='',description="folder_path")

