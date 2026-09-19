from datetime import date, datetime
from enum import Enum, auto
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import polars as pl
from pydantic import AliasChoices, BaseModel, Field, RootModel

from app.services.micron.data_catalog.query import FilterRequest


class FDDataPullStages(str, Enum):
    IDLE = "IDLE"

    FACILITIES = "FACILITIES"

    TECH_NODE = "TECH_NODE"

    DESIGN_ID = "DESIGN_ID"

    TRAVELER_ID = "TRAVELER_ID"

    TRAVELER_STEP = "TRAVELER_STEP"

    SAVE_HIGH_LEVEL_DC_DETAILS = "SAVE_HIGH_LEVEL_DC_DETAILS"

    FD_CONTEXT = "FD_CONTEXT"

    FD_SENSOR = "FD_SENSOR"

    FD_TRACE = "FD_TRACE"

    LOT_ID = "LOT_ID"

    WAFER_ID = "WAFER_ID"

    LOT_WAFER_SAVE = "LOT_WAFER_SAVE"

    FINAL_DATA_AGGREGATE = "FINAL_DATA_AGGREGATE"

    UC3_FD_CONTEXT_APPLY_FILTERS = "UC3_FD_CONTEXT_APPLY_FILTERS"

    UC2_SIGMA_DATA = "UC2_SIGMA_DATA"

    UC3_SIGMA_DATA = "UC3_SIGMA_DATA"

    PROBE_CONTEXT = "PROBE_CONTEXT"

    PROBE_DATA_PULL = "PROBE_DATA_PULL"


class DataPullStatus(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"

    SAVED = "SAVED" # saved is used when user wanted to save inputs without downloaded

    CONFIGURED = "CONFIGURED"

    RUNNING = "RUNNING"

    SUCCESS = "SUCCESS"

    FAILED = "FAILED"


class DataCatalogStatus(str, Enum):
    IDLE = "IDLE"

    RUNNING = "RUNNING"

    SUCCESS = "SUCCESS"

    FAILED = "FAILED"


class BigQueryDataPullJobStage(str, Enum):
    IDLE = "IDLE"

    QUEUED = "QUEUED"

    QUERY_VERIFICATION = "QUERY_VERIFICATION"

    QUERY_REGISTRATION = "QUERY_REGISTRATION"

    QUERY_EXECUTION = "QUERY_EXECUTION"

    QUERY_RESULT_DOWNLOAD = "QUERY_RESULT_DOWNLOAD"

    SAVING_RESULTS = "SAVING_RESULTS"


class FdDataPullTabularDataFolder(BaseModel):
    source_file_path: Path = Field(description="Result of the stage query")

    source_folder_path: Path = Field(description="Result folder of the current stage")


class FdDataPullStausResult(BaseModel):
    current_stage: FDDataPullStages = Field(
        description="current stage of the data catalog session"
    )

    current_stage_status: DataPullStatus = Field(
        description="status of the current stage"
    )

    current_stage_results: dict = Field(
        description="results for client folder/file/exception"
    )

    current_stage_inputs: dict = Field(description="inputs for the current stage")


class BigQueryJobStatus(BaseModel):
    total_bytes_processed: str = Field(
        default="0", description="Dry run of google bigquery"
    )

    total_bytes_billed: str = Field(default="0", description="Cost of google bigquery")

    bigquery_job_id: Union[str, List[str]] = Field(
        default="", description="Job registred in bigquery asynchronously"
    )

    progress_percentage: int = Field(default=0, description="percentage of results")

    progress_message: str = Field(
        default="Not configured", description="job progress message"
    )


class BigQueryDataPullJobStatus(BaseModel):
    job_stage: BigQueryDataPullJobStage = Field(
        default=BigQueryDataPullJobStage.IDLE, description="bigqyery job stages"
    )

    job_stage_status: BigQueryJobStatus = Field(
        default=BigQueryJobStatus(), description="bigqyery job stages"
    )


class BigQueryAuthType(str, Enum):
    APPLICATION_DEFAULT_CREDENTIALS = "APPLICATION_DEFAULT_CREDENTIALS"

    SERVICE_ACCOUNT_FILE = "SERVICE_ACCOUNT_FILE"


class BigQueryAppDefaultCredFile(BaseModel):
    auth_type: Literal[BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS] = (
        BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS
    )

    project_id: str = Field(description="Bigquery project id")

    application_credentials_file_path: Path = Field(description="Bigquery service file")


class BigQueryServiceAccountFile(BaseModel):
    auth_type: Literal[BigQueryAuthType.SERVICE_ACCOUNT_FILE] = (
        BigQueryAuthType.SERVICE_ACCOUNT_FILE
    )

    service_account_file: Path = Field(description="Bigquery service file")


class BigQueryAuthentication(BaseModel):
    auth_type: BigQueryAuthType

    auth_config: Union[BigQueryAppDefaultCredFile, BigQueryServiceAccountFile] = Field(
        description="Authentication Config", discriminator="auth_type"
    )


class QueryValueType(str, Enum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.upper()

    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    DATE = auto()


class QueryParameterType(str, Enum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.upper()

    SCALAR = auto()
    ARRAY = auto()


class MultiSqlQuery(BaseModel):
    sql_query: str = Field(default="", description="sql query to execute")

    declarations: str = Field(
        default="",
        description="sql query declarations to execute, eg: DECLARE START_DATE;",
    )

    query_params: Dict[str, Tuple[QueryParameterType, QueryValueType, Any]] = Field(
        default_factory=dict, description="sql query parameters"
    )

    destination_folder_path: Optional[str] = Field(
        default=None, description="Folder path to write the results of the query"
    )

    cache_keys: Optional[List[str]] = Field(
        default=[], description="cache key per sql query output"
    )


class BigqueryDataPullJobConfig(BaseModel):
    authentication: Union[BigQueryAuthentication, None] = Field(
        default=None, description="Authentication Config"
    )

    cache_key: Optional[str] = Field(
        default="", description="cache key to store the result"
    )

    gcs_bucket_name: str = Field(default="", description="GCS bucket name")

    sql_query: Union[str, List[MultiSqlQuery]] = Field(
        default="", description="sql query gonna use at this stage"
    )

    task_id: str = Field(default="", description="task id being assigned to worker")

    job_status: BigQueryDataPullJobStatus = Field(
        default=BigQueryDataPullJobStatus(), description="Bigquery job stages"
    )


class FdDataPullStausResponse(BaseModel):
    current_stage: FDDataPullStages = Field(
        description="current stage of the data catalog session"
    )

    current_stage_status: DataPullStatus = Field(
        description="status of the current stage"
    )

    job_status: Union[BigQueryDataPullJobStatus, None] = Field(
        default=None, description="status of the current worker"
    )

    fd_data_pull_job_status: DataCatalogStatus = Field(
        description="status of the datacatalog session"
    )


class DataPullStatusConfig(BaseModel):
    status: DataPullStatus = Field(
        description="status of the current stage", default=DataPullStatus.NOT_CONFIGURED
    )

    job_config: dict = Field(
        description="custom job configuration. Ex: Airflow/NIFI/Celery job info",
        default=BigqueryDataPullJobConfig().model_dump(),
    )

    job_triggered_at: Union[datetime, None] = Field(
        description="job triggered timestamp", default=None
    )

    job_completed_at: Union[datetime, None] = Field(
        description="job finished timestamp", default=None
    )


class DataSourceType(str, Enum):
    FD_TRACE = "FD_TRACE"


class BaseDataPullResult(BaseModel):
    file_path: Path = Field(description="file path containing the tabular result")


class PathDataPullResult(BaseDataPullResult):
    selected_path: Path
    selected_column: str


class ValuesDataPullResult(BaseDataPullResult):
    selected_values: Optional[List[Any]] = Field(
        description="selected values", default=None
    )


class DataPullResult(RootModel):
    root: Union[
        PathDataPullResult,
        ValuesDataPullResult,
    ]

    @property
    def file_path(self) -> Path:
        return self.root.file_path

    @property
    def selected_values(self) -> Optional[List[Any]]:
        match self.root:
            case ValuesDataPullResult(selected_values=selected_values):
                return selected_values
            case PathDataPullResult(
                selected_path=selected_path, selected_column=selected_column
            ):
                return (
                    pl.read_parquet(selected_path, columns=[selected_column])
                    .unique()
                    .to_dict(as_series=False)[selected_column]
                )

    @selected_values.setter
    def selected_values(self, values: Optional[List[Any]]):
        match self.root:
            case ValuesDataPullResult() as result:
                result.selected_values = values
            case PathDataPullResult() as result:
                selected_df = pl.DataFrame({result.selected_column: values})
                (
                    pl.read_parquet(result.selected_path, n_rows=0)
                    .join(selected_df, on=result.selected_column, how="right")
                    .write_parquet(result.selected_path)
                )


class FacilitesDataPullInput(BaseModel):
    pass


class FacilitiesDataPullOutput(BaseModel):
    facilities: Optional[DataPullResult] = None


class FacilitesDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default=DataPullStatusConfig(), description="Current stage status"
    )

    stage: Literal[FDDataPullStages.FACILITIES] = FDDataPullStages.FACILITIES

    inputs: Union[FacilitesDataPullInput, None] = Field(
        default=None, description="inputs to use for this stage execution"
    )

    outputs: Union[FacilitiesDataPullOutput, None] = Field(
        default=None, description="outputs of this stage"
    )


class TechNodesDataPullInput(FacilitesDataPullInput, FacilitiesDataPullOutput):
    pass


class TechNodesDataPullOutput(BaseModel):
    tech_nodes: Optional[DataPullResult] = None


class TechNodeDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default=DataPullStatusConfig(), description="Current stage status"
    )

    stage: Literal[FDDataPullStages.TECH_NODE] = FDDataPullStages.TECH_NODE

    inputs: Union[TechNodesDataPullInput, None] = Field(
        default=None, description="Inputs for this stage"
    )

    outputs: Union[TechNodesDataPullOutput, None] = Field(
        default=None, description="Outputs for this stage"
    )


class DesignIdDataPullInput(TechNodesDataPullInput, TechNodesDataPullOutput):
    pass


class DesignIdDataPullOutput(BaseModel):
    design_ids: Optional[DataPullResult] = None


class DesignIdDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default=DataPullStatusConfig(), description="Current stage status"
    )

    stage: Literal[FDDataPullStages.DESIGN_ID] = FDDataPullStages.DESIGN_ID

    inputs: Union[DesignIdDataPullInput, None] = Field(
        default=None, description="Inputs for this stage"
    )

    outputs: Union[DesignIdDataPullOutput, None] = Field(
        default=None, description="Outputs for this stage"
    )


class TravelersIdDataPullInput(FacilitiesDataPullOutput, DesignIdDataPullOutput):
    pass


class TravelersIdDataPullOutput(BaseModel):
    traveler_ids: Optional[DataPullResult] = None


class TravelersIdDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default=DataPullStatusConfig(), description="Current stage status"
    )

    stage: Literal[FDDataPullStages.TRAVELER_ID] = FDDataPullStages.TRAVELER_ID

    inputs: Union[TravelersIdDataPullInput, None] = Field(
        default=None, description="Inputs for this stage"
    )

    outputs: Union[TravelersIdDataPullOutput, None] = Field(
        default=None, description="Outputs for this stage"
    )


class TravelerStepDataPullInput(
    FacilitiesDataPullOutput, DesignIdDataPullOutput, TravelersIdDataPullOutput
):
    pass


class TravelerStepDataPullOutput(BaseModel):
    traveler_steps: Optional[DataPullResult] = None
    baseline_line_traveler_id: Optional[str] = None


class TravelerStepDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default=DataPullStatusConfig(), description="Current stage status"
    )

    stage: Literal[FDDataPullStages.TRAVELER_STEP] = FDDataPullStages.TRAVELER_STEP

    inputs: Union[TravelerStepDataPullInput, None] = Field(
        default=None, description="Inputs for this stage"
    )

    outputs: Union[TravelerStepDataPullOutput, None] = Field(
        default=None, description="Outputs for this stage"
    )


class FdContextDateRangeInput(BaseModel):
    start_date: date = Field(..., description="Start date for the data pull")

    end_date: date = Field(..., description="End date for the data pull")


class FdContextDataPullInput(
    TravelerStepDataPullInput, FdContextDateRangeInput, TravelerStepDataPullOutput
):
    pass


class FdContextDataPullOutput(BaseModel):
    fd_contexts: Optional[DataPullResult] = None


class FdContextDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default=DataPullStatusConfig(), description="Current stage status"
    )

    stage: Literal[FDDataPullStages.FD_CONTEXT] = FDDataPullStages.FD_CONTEXT

    inputs: Union[FdContextDataPullInput, None] = Field(
        default=None, description="Inputs for this stage"
    )

    outputs: Union[FdContextDataPullOutput, None] = Field(
        default=None, description="Outputs for this stage"
    )


class FinalDataAggregateContextInput(FdContextDataPullInput):
    pass


class FinalDataAggregateContextOutput(BaseModel):
    recipes: Optional[DataPullResult] = None
    tool_ids: Optional[DataPullResult] = None
    step_ids: Optional[DataPullResult] = None
    sensors: Optional[DataPullResult] = None


class SaveHLDCConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default=DataPullStatusConfig(), description="Current stage status"
    )

    stage: Literal[FDDataPullStages.SAVE_HIGH_LEVEL_DC_DETAILS] = (
        FDDataPullStages.SAVE_HIGH_LEVEL_DC_DETAILS
    )

    inputs: Union[FdContextDataPullInput, None] = Field(
        default=None, description="Inputs for this stage"
    )

    outputs: Union[FdContextDataPullOutput, None] = Field(
        default=None, description="Outputs for this stage"
    )


class UC2SigmaSteps(BaseModel):
    run_parameters: Optional[DataPullResult] = None
    point_steps: Optional[DataPullResult] = None
    measurement_steps: Optional[DataPullResult] = None


class UC2SigmaMeasurementParameters(BaseModel):
    measurement_parameters: Optional[DataPullResult] = None


class UC2SigmaWaferParameters(BaseModel):
    wafer_parameters: Optional[DataPullResult] = None


class UC2SigmaPointParameters(BaseModel):
    point_parameters: Optional[DataPullResult] = None


class UC2SigmaMeasurementParametersFetchInput(FdContextDataPullInput, UC2SigmaSteps):
    pass


class UC2SigmaMeasurementStepsDependentParameters(
    UC2SigmaMeasurementParameters, UC2SigmaWaferParameters
):
    pass


class UC2SigmaMeasurementParametersFetchOutput(
    UC2SigmaMeasurementStepsDependentParameters, UC2SigmaPointParameters
):
    pass


class UC2SigmaParameters(
    UC2SigmaSteps, UC2SigmaMeasurementStepsDependentParameters, UC2SigmaPointParameters
):
    pass


class ToolNameToolId(BaseModel):
    tool_name: str
    tool_id: str


class FinalDataAggregateInput(
    FinalDataAggregateContextInput, FinalDataAggregateContextOutput
):
    pass


class FinalDataAggregateOutput(BaseModel):
    final_data: Optional[DataPullResult] = None


class FinalDataAggregateConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default_factory=DataPullStatusConfig, description="status of the current stage"
    )
    stage: Literal[FDDataPullStages.FINAL_DATA_AGGREGATE] = (
        FDDataPullStages.FINAL_DATA_AGGREGATE
    )
    inputs: Optional[FinalDataAggregateInput] = Field(
        default=None, description="inputs of the current stage"
    )
    outputs: Optional[FinalDataAggregateOutput] = Field(
        default=None, description="outpus of the current stage"
    )


class UC2SigmaGQLFileParsedContentFile(BaseModel):
    parquet_file_path: str
    gql_file_path: str
    gql_structure_file_path: Optional[str] = (
        None  # parquet file that also stores structure of parsed file
    )


class UploadCsvResponse(BaseModel):
    uploaded_file_path: str
    columns_file_path: Optional[str] = None
    selected_columns: Optional[List[Any]] = Field(
        description="seleted values", default=None
    )


class UC2SigmaDataPullInput(
    UC2SigmaParameters, FdContextDataPullInput, FdContextDataPullOutput
):
    gql_file_details: Optional[UC2SigmaGQLFileParsedContentFile] = Field(
        default=None, description="populated when GQL file is present"
    )


class UC2SigmaDataPullOutput(BaseModel):
    uc2_sigma_data: Optional[DataPullResult] = None


class UC2SigmaDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default_factory=DataPullStatusConfig, description="status of the current stage"
    )
    stage: Literal[FDDataPullStages.UC2_SIGMA_DATA] = FDDataPullStages.UC2_SIGMA_DATA
    inputs: Optional[UC2SigmaDataPullInput] = Field(
        default=None, description="inputs of the current stage"
    )
    outputs: Optional[UC2SigmaDataPullOutput] = Field(
        default=None, description="output of the current stage"
    )


class SensorsDataPullInput(FdContextDataPullInput, FdContextDataPullOutput):
    pass


class SensorsDataPullOutput(BaseModel):
    sensors: Optional[DataPullResult] = None


class SensorsDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default=DataPullStatusConfig(), description="Current stage status"
    )

    stage: Literal[FDDataPullStages.FD_SENSOR] = FDDataPullStages.FD_SENSOR

    inputs: Union[SensorsDataPullInput, None] = Field(
        default=None, description="Inputs for this stage"
    )

    outputs: Union[SensorsDataPullOutput, None] = Field(
        default=None, description="Outputs for this stage"
    )


class FdTraceDataPullInput(SensorsDataPullInput, SensorsDataPullOutput):
    pass


class FdTraceDataPullOutput(BaseModel):
    fd_trace: Optional[DataPullResult] = None


class FdTraceDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default=DataPullStatusConfig(), description="Current stage status"
    )

    stage: Literal[FDDataPullStages.FD_TRACE] = FDDataPullStages.FD_TRACE

    inputs: Union[FdTraceDataPullInput, None] = Field(
        default=None, description="Inputs for this stage"
    )

    outputs: Union[FdTraceDataPullOutput, None] = Field(
        default=None, description="Outputs for this stage"
    )


class LotIdsDataPullInput(
    FacilitiesDataPullOutput,
    DesignIdDataPullOutput,
    TravelersIdDataPullOutput,
    TravelerStepDataPullOutput,
    FdContextDateRangeInput,
):
    pass


class LotIdsDataPullOutput(BaseModel):
    lot_ids: Optional[DataPullResult] = None


class LotIdsDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default_factory=DataPullStatusConfig, description="current stage status"
    )
    stage: Literal[FDDataPullStages.LOT_ID] = FDDataPullStages.LOT_ID
    inputs: Optional[LotIdsDataPullInput] = Field(
        default=None, description="inputs for this stage"
    )
    outputs: Optional[LotIdsDataPullOutput] = Field(
        default=None, description="outputs for this stage"
    )


class WaferIdsDataPullInput(LotIdsDataPullInput, LotIdsDataPullOutput):
    pass


class WaferIdsDataPullOutput(BaseModel):
    wafer_ids: Optional[DataPullResult] = None


class WaferIdsDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default_factory=DataPullStatusConfig, description="current stage status"
    )
    stage: Literal[FDDataPullStages.WAFER_ID] = FDDataPullStages.WAFER_ID
    inputs: Optional[WaferIdsDataPullInput] = Field(
        default=None, description="inputs for this stage"
    )
    outputs: Optional[WaferIdsDataPullOutput] = Field(
        default=None, description="outputs for this stage"
    )


class UC3SigmaMetroStepsCommonTestIds(BaseModel):
    uc3_sigma_metro_steps: Optional[DataPullResult] = None
    common_test_ids: Optional[DataPullResult] = None


class ProbeContextDataPullInput(FacilitiesDataPullOutput, DesignIdDataPullOutput):
    pass


class ProbeContextDataPullOutput(BaseModel):
    paretoname: Optional[DataPullResult] = None
    paretotitle: Optional[DataPullResult] = None


class ProbeContextDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default=DataPullStatusConfig(), description="Current stage status"
    )

    stage: Literal[FDDataPullStages.PROBE_CONTEXT] = FDDataPullStages.PROBE_CONTEXT

    inputs: Union[ProbeContextDataPullInput, None] = Field(
        default=None, description="Inputs for this stage"
    )

    outputs: Union[ProbeContextDataPullOutput, None] = Field(
        default=None, description="Outputs for this stage"
    )


class DieCountsPerRegionInput(BaseModel):
    A: int = Field(default=0)
    B: int = Field(default=0)
    C: int = Field(default=0)
    D: int = Field(default=0)
    E: int = Field(default=0)


class ProbeDataPullInputs(
    FdContextDateRangeInput, ProbeContextDataPullInput, ProbeContextDataPullOutput
):
    die_counts_per_region: DieCountsPerRegionInput
    uploaded_probe_data: Optional[UploadCsvResponse] = None


class ProbeDataPullOutputs(BaseModel):
    probe_data: Optional[DataPullResult] = None


class ProbeDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default=DataPullStatusConfig(), description="Current stage status"
    )

    stage: Literal[FDDataPullStages.PROBE_DATA_PULL] = FDDataPullStages.PROBE_DATA_PULL

    inputs: Union[ProbeDataPullInputs, None] = Field(
        default=None, description="Inputs for this stage"
    )

    outputs: Union[ProbeDataPullOutputs, None] = Field(
        default=None, description="Outputs for this stage"
    )


class LotWaferInput(WaferIdsDataPullInput, WaferIdsDataPullOutput):
    pass


class LotWaferOutput(BaseModel):
    pass


class LotWaferConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default_factory=DataPullStatusConfig, description="status of the current stage"
    )
    stage: Literal[FDDataPullStages.LOT_WAFER_SAVE] = FDDataPullStages.LOT_WAFER_SAVE
    inputs: Optional[LotWaferInput] = Field(
        default=None, description="inputs of the current stage"
    )
    outputs: Optional[LotWaferOutput] = Field(
        default=None, description="output of the current stage"
    )


class UC3SigmaCommonTestIdInput(LotWaferInput, LotWaferOutput):
    uc3_sigma_metro_steps_: List[List[str]] = Field(alias="uc3_sigma_metro_steps")
    cached_traveler_steps: Optional[List[str]] = None
    wafer_level: bool = False
    point_level: bool = False

    @cached_property
    def uc3_sigma_metro_steps(self) -> List[str]:
        return list(chain.from_iterable(self.uc3_sigma_metro_steps_))


class UC3SigmaInput(LotWaferInput, LotWaferOutput):
    metro_step_common_step_ids: List[UC3SigmaMetroStepsCommonTestIds] = []
    cached_traveler_steps: List[str] = Field(default_factory=list)
    padding_days: int = 60
    integrate_back_of_wafer_mesurement: bool = False
    wafer_level: bool = False
    point_level: bool = False
    regions: Optional[DataPullResult] = None
    use_probe: bool = False


class UC3SigmaOutput(BaseModel):
    uc3_sigma_data: Optional[DataPullResult] = None


class UC3SigmaDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default_factory=DataPullStatusConfig, description="status of the current stage"
    )
    stage: Literal[FDDataPullStages.UC3_SIGMA_DATA] = FDDataPullStages.UC3_SIGMA_DATA
    inputs: Optional[UC3SigmaInput] = Field(
        default=None, description="inputs of the current stage"
    )
    outputs: Optional[UC3SigmaOutput] = Field(
        default=None, description="output of the current stage"
    )


class UC3FDContextApplyFiltersInput(WaferIdsDataPullInput, WaferIdsDataPullOutput):
    filters: Optional[List[FilterRequest]] = None


class UC3FDContextApplyFiltersOutput(BaseModel):
    aggregated_file_path: Optional[str] = None


class UC3FDContextApplyFiltersDataPullConfig(BaseModel):
    status: DataPullStatusConfig = Field(
        default_factory=DataPullStatusConfig, description="current stage status"
    )
    stage: Literal[FDDataPullStages.UC3_FD_CONTEXT_APPLY_FILTERS] = (
        FDDataPullStages.UC3_FD_CONTEXT_APPLY_FILTERS
    )
    inputs: Optional[UC3FDContextApplyFiltersInput] = Field(
        default=None, description="inputs for this stage"
    )
    outputs: Optional[UC3FDContextApplyFiltersOutput] = Field(
        default=None, description="outputs for this stage"
    )


class FdDataPullJobConfig(BaseModel):
    id: Optional[str] = Field(
        description="id",
        default=None,
        serialization_alias="_id",
        validation_alias=AliasChoices("_id", "id"),
    )

    session_id: str = Field(
        default="", description="Data pull created in session with id as:"
    )

    stage: FDDataPullStages = Field(
        default=FDDataPullStages.FACILITIES,
        description="current stage of the data catalog session",
    )

    stage_config: Optional[
        Union[
            FacilitesDataPullConfig,
            TechNodeDataPullConfig,
            DesignIdDataPullConfig,
            TravelersIdDataPullConfig,
            TravelerStepDataPullConfig,
            SaveHLDCConfig,
            FdContextDataPullConfig,
            SensorsDataPullConfig,
            FdTraceDataPullConfig,
            LotIdsDataPullConfig,
            WaferIdsDataPullConfig,
            LotWaferConfig,
            UC2SigmaDataPullConfig,
            UC3FDContextApplyFiltersDataPullConfig,
            FinalDataAggregateConfig,
            UC3SigmaDataPullConfig,
            ProbeContextDataPullConfig,
            ProbeDataPullConfig,
        ]
    ] = Field(default=None, description="", discriminator="stage")


class FdDataPullConfig(BaseModel):
    id: Optional[str] = Field(
        description="id",
        default=None,
        serialization_alias="_id",
        validation_alias=AliasChoices("_id", "id"),
    )

    session_id: str = Field(
        default="", description="Data pull created in session with id as:"
    )

    data_source_type: Literal[DataSourceType.FD_TRACE] = Field(
        default=DataSourceType.FD_TRACE,
        description="this record is created for fd_trace data pull job",
    )

    data_pull_status: DataCatalogStatus = Field(
        default=DataCatalogStatus.IDLE, description="status of the datacatalog session"
    )

    current_stage: FDDataPullStages = Field(
        default=FDDataPullStages.IDLE,
        description="current stage of the data catalog session",
    )

    facility_stage_job_id: str = Field(
        default="", description="status about facility_stage"
    )

    tech_node_stage_job_id: str = Field(
        default="", description="status about tech_node"
    )

    design_ids_stage_job_id: str = Field(
        default="", description="status about design_ids_stage"
    )

    traveler_id_step_stage_job_id: str = Field(
        default="", description="status about traveler_id_step_stage"
    )

    traveler_step_stage_job_id: str = Field(
        default="", description="status about traverler step satge"
    )

    save_high_level_dc_details_job_id: str = Field(
        default="", description="status about saving selected high level dc items"
    )

    fd_context_stage_job_id: str = Field(
        default="", description="status about traverler fd_context"
    )

    sensors_stage_job_id: str = Field(
        default="", description="status about traverler sensors_stage"
    )

    fd_trace_stage_job_id: str = Field(
        default="", description="status about traverler fd_trace stage"
    )

    lot_ids_stage_job_id: str = Field(
        default="", description="status about lot ids stage"
    )

    wafer_ids_stage_job_id: str = Field(
        default="", description="status about wafer stage"
    )

    lot_wafer_stage_job_id: str = Field(
        default="", description="status about lot wafer save stage"
    )

    uc2_sigma_job_id: str = Field(default="", description="status about uc2 sigma job")

    uc3_fd_context_apply_filters_job_id: str = Field(
        default="", description="status about uc3 apply stage"
    )

    uc3_sigma_job_id: str = Field(default="", description="status about uc3 sigma job")

    final_data_aggregate_stage_job_id: str = Field(
        default="", description="status about final_data_aggregate stage"
    )

    probe_context_job_id: str = Field(
        default="", description="status about probe context data pull"
    )

    probe_data_pull_job_id: str = Field(
        default="", description="status about probe data pull"
    )


class FdTracePullFullStatusResponse(BaseModel):
    stage: FDDataPullStages

    status: DataPullStatus

    inputs: Union[dict, None] = Field(
        default=None, description="Inputs/Selection made to the current stage"
    )
