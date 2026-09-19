import { SortAmountDownIcon } from 'primeng/icons/sortamountdown';
import {
  WidgetClientTags,
  WorkflowClientTags,
} from '../pages/workflow-designer/client-tags';

abstract class BaseWorkflowModel {}

export enum TerminationCriteria {
  ON_LOOP_COUNT = 'ON_LOOP_COUNT',
  CUSTOM_CODE = 'CUSTOM_CODE',
}

export enum SourceType {
  NONE = 'NONE',
  LOCAL = 'LOCAL',
  BIGQUERY = 'BIGQUERY',
  MOUNTED_DRIVE = 'MOUNTED_DRIVE',
}

export enum FileType {
  CSV = 'CSV',
  Parquet = 'Parquet',
  Image = 'Image',
  PDF = 'PDF',
}

export enum BigQueryDatasetType {
  TABLE = 'TABLE',
  QUERY = 'QUERY',
}

export enum WidgetState {
  IDLE = 'IDLE',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  FAILED = 'FAILED',
  SUCCEEDED = 'SUCCEEDED',
}

export enum WorkflowState {
  IDLE = 'IDLE',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  FAILED = 'FAILED',
  SUCCEEDED = 'SUCCEEDED',
}

export enum WidgetType {
  DATA_COPY = 'DATA_COPY',
  JUPYTER = 'JUPYTER',
  FILTER = 'FILTER',
  DROP_MISSING = 'DROP_MISSING',
  CUSTOM_CODE = 'CUSTOM_CODE',
  SAVE = 'SAVE',
  MODEL_BUILDER = 'MODEL_BUILDER',
  MOBO = 'MOBO',
  RESCALE = 'RESCALE',
  DECISION = 'DECISION',
  LOOP_START = 'LOOP_START',
  LOOP_END = 'LOOP_END',
  THERMOCALC = 'THERMOCALC',
  PREDICTION = 'PREDICTION',
  DROP_COLUMNS = 'DROP_COLUMNS',
  RENAME_COLUMNS = 'RENAME_COLUMNS',
  DATATYPE_CONVERSION = 'DATATYPE_CONVERSION',

  // NOT SUPPORTED IN THE BACKEND YET
  PYTHON = 'PYTHON',
  UNION = 'UNION',
  JOIN = 'JOIN',
  APPEND = 'APPEND',
  CONFIG_FILE = 'CONFIG_FILE',
  PIVOT = 'PIVOT',
  POST_RESCALE = 'POST_RESCALE',
  RESCALE_TEMPLATE_CONNECTOR = 'RESCALE_TEMPLATE_CONNECTOR',
  Feature_Engineering = 'Feature_Engineering',
  EXPORT = 'EXPORT',
  ACTIVE_LEARNING = 'ACTIVE_LEARNING',
  GPR = 'GPR',
  MPR = 'MPR',
  AUTOML = 'AUTOML',
  LINEAR_REGRESSION = 'LINEAR_REGRESSION',
  LGBM = 'LGBM',
  RF = 'RF',
  NNFASTAI = 'NNFASTAI',
  NN_TORCH = 'NN_TORCH',
  XGBOOST = 'XGBOOST',
  CATBOOST = 'CATBOOST',
  KNEIGHBORS = 'KNEIGHBORS',
  EXTRA_TREES = 'EXTRA_TREES',
  ARIMA = 'ARIMA',
  SVM = 'SVM',
  GPC = 'GPC',
  IMAGE_DATASET = 'IMAGE_DATASET',
  REGION_PROPERTY = 'REGION_PROPERTY',

  IMAGE_SPATIAL_STATISTICS = 'SPATIAL_STATISTICS',
  TEXT_DATA = 'TEXT_DATA',

  // UX only
  UX = 'UX',
}

export enum ModelType {
  LIGHT_GBM = 'LIGHT_GBM',
}

export enum ScalingMethod {
  MIN_MAX = 'MIN_MAX',
  STANDARD = 'STANDARD',
  ROBUST = 'ROBUST',
}

export enum OptimizationMethod {
  GridSearch = 'GridSearch',
  RandomSearch = 'RandomSearch',
}

export class RandomSearchConfig implements BaseWorkflowModel {
  n_iter: number = 50;
}

export enum SaveOptions {
  DATASET = 'DATASET',
  JSON = 'JSON',
  MODEL = 'MODEL',
  RESULTS = 'RESULTS',
  VARIABLES = 'VARAIBLES',
}

export enum JoinType {
  SELECT = 'SELECT',
  INNER = 'INNER',
  LEFT = 'LEFT JOIN',
  RIGHT = 'RIGHT JOIN',
  OUTER = 'OUTER JOIN',
  // TABLE = 'TABLE JOIN'
}

export enum FilterType {
  FILTER_BY_COLUMN_VALUES = 'FILTER_BY_COLUMN_VALUES',
}

export enum DropColumnsType {
  DROP_BY_COLUMN_VALUES = 'DROP_BY_COLUMN_VALUES',
}

export enum DropMissingType {
  DROP_ROW_BY_MISSING_VALUE = 'DROP_ROW_BY_MISSING_VALUE',
}

export enum RenameColumnsType {
  RENAME_COLUMN_NAME = 'RENAME_COLUMN_NAME',
}

export enum DatatypeConversionType {
  CHANGE_DATATYPE_OF_COLUMNS = 'CHANGE_DATATYPE_OF_COLUMNS',
}

export enum CustomFunctionInputOutputTypes {
  DATA_FRAME = 'DATA_FRAME',
  JSON = 'JSON',
  STRING = 'STRING',
}

export enum RequestType {
  DATASET = 'DATASET',
  STRING = 'STRING',
  MODEL = 'MODEL',
  FAILED = 'FAILED',
  PATH = 'PATH',
  STRINGS_LIST = 'STRINGS_LIST',
  DICTIONARY = 'DICTIONARY',
}

export class BigQueryDatasetTableConfig implements BaseWorkflowModel {
  dataset_name: string | undefined;
  table_name: string | undefined;
}

export class BigQueryDatasetQueryConfig implements BaseWorkflowModel {
  query: string | undefined;
  query_params: any | undefined;
}

export class BigQueryDatasetConfig implements BaseWorkflowModel {
  project_id: string | undefined;
  dataset_type: BigQueryDatasetType | undefined;
  dataset: BigQueryDatasetTableConfig | BigQueryDatasetQueryConfig | undefined;
}

export class LocalFileConfiguration implements BaseWorkflowModel {
  version: string = '1.0';
  dataset_id: string | undefined;
}

export class MountedDriveConfiguration implements BaseWorkflowModel {
  version: string = '1.0';
  dataset_id: string;

  constructor(datasetId: string) {
    this.dataset_id = datasetId;
  }
}

export class BigQueryDatasetConfiguration implements BaseWorkflowModel {
  version: string = '1.0';
  bigquery_connector_id: string | undefined;
  dataset_configuration: BigQueryDatasetConfig | undefined;
}

export class SourceConfiguration implements BaseWorkflowModel {
  type: SourceType;
  configuration:
    | LocalFileConfiguration
    | BigQueryDatasetConfiguration
    | MountedDriveConfiguration;
  widget_type: WidgetType | undefined;

  constructor(
    type: SourceType,
    configuration:
      | LocalFileConfiguration
      | BigQueryDatasetConfiguration
      | MountedDriveConfiguration,
    widget_type?: WidgetType,
  ) {
    this.type = type;
    this.configuration = configuration;
    this.widget_type = widget_type;
  }
}

export class Sink implements BaseWorkflowModel {
  dataset_name: string | undefined;
  dataset_description: string | undefined;
}

export class DataCopyWidgetConfig implements BaseWorkflowModel {
  verion: string = '1.0';
  source: SourceConfiguration;
  sink: Sink | undefined;
  inputs: FunctionInputs[] = [];
  widget_type: WidgetType;

  constructor(source: SourceConfiguration, widget_type: WidgetType) {
    this.source = source;
    this.sink = new Sink();
    this.widget_type = widget_type;
  }
}

// export class JupyterWidgetConfig implements BaseWorkflowModel {
//   version: string = '1.0'; // ✅ Corrected typo
//   inputs: FunctionInputs[] = [];
//   widget_type: WidgetType;

//   constructor(widget_type: WidgetType) {
//     this.widget_type = widget_type;
//   }
// }

export class JupyterWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  widget_type: WidgetType;
  cpu_limit: number | undefined;
  memory_limit: string | undefined;
  notebook_image: string | undefined;
  notebook_dir: string | undefined;
  notebook_file: string | undefined;

  constructor(widget_type: WidgetType) {
    this.widget_type = widget_type;
  }
}

export enum FilterOperator {
  SELECT = 'SELECT',
  EQ = 'EQ',
  NE = 'NE',
  GT = 'GT',
  GTE = 'GTE',
  LT = 'LT',
  LTE = 'LTE',
  // REGEX = 'REGEX',
}

export enum StringFilterOperator {
  STARTS_WITH = 'STARTS_WITH',
  ENDS_WITH = 'ENDS_WITH',
  EXACT_MATCH = 'EXACT_MATCH',
  PARTIAL_MATCH = 'PARTIAL_MATCH',
}

export enum FilterOperand {
  SELECT = 'SELECT',
  AND = 'AND',
  OR = 'OR',
  XOR = 'XOR',
}

export enum DataType {
  NUMERICAL = 'NUMERICAL',
  CATEGORICAL = 'CATEGORICAL',
}
export class FilterValues implements BaseWorkflowModel {
  column_name: string;
  operator: FilterOperator | StringFilterOperator;
  value: string | number | boolean | (string | number | boolean)[];
  data_type: DataType;

  constructor(column_name: string, operator: any, value: any, data_type: any) {
    this.column_name = column_name;
    this.operator = FilterOperator.SELECT;
    this.value = value;
    this.data_type = data_type;
  }
}

export class FilterConfig implements BaseWorkflowModel {
  version: string = '1.0';
  filter_operands: FilterOperand[] = [];
  filter_values: FilterValues[] = [];
  widget_type: WidgetType | undefined;
}

export class FilterWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  type: FilterType;
  config: FilterConfig | undefined;
  widget_type: WidgetType | undefined;

  constructor(type: FilterType, widget_type?: WidgetType) {
    this.type = type;
    this.widget_type = widget_type;
  }
}

export class DropColumnsConfig implements BaseWorkflowModel {
  version: string = '1.0';
  widget_type: WidgetType | undefined;
  selected_columns: string[] = [];
}

export class DropColumnsWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  type: DropColumnsType;
  config: DropColumnsConfig | undefined;
  widget_type: WidgetType | undefined;
  constructor(type: DropColumnsType, widget_type?: WidgetType) {
    this.type = type;
    this.widget_type = widget_type;
  }
}

export class DropMissingConfig implements BaseWorkflowModel {
  version: string = '1.0';
  widget_type: WidgetType | undefined;
  selected_columns: string[] = [];
}

export class DropMissingWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  type: DropMissingType;
  config: DropMissingConfig | undefined;
  widget_type: WidgetType | undefined;

  constructor(type: DropMissingType, widget_type?: WidgetType) {
    this.type = type;
    this.widget_type = widget_type;
  }
}

export class RenameColumnsModel {
  old_name: string = '';
  new_name: string = '';
}

export class RenameColumnsConfig implements BaseWorkflowModel {
  version: string = '1.0';
  widget_type: WidgetType | undefined;
  columns_to_rename: Record<string, string> = {};
}

export class RenameColumnsWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  type: RenameColumnsType;
  config: RenameColumnsConfig | undefined;
  widget_type: WidgetType | undefined;

  constructor(type: RenameColumnsType, widget_type?: WidgetType) {
    this.type = type;
    this.widget_type = widget_type;
  }
}

export class DatatypeConversionConfig implements BaseWorkflowModel {
  version: string = '1.0';
  widget_type: WidgetType | undefined;
  column_type_mapping: Record<string, string> = {};
}

export class DatatypeConversionWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  type: DatatypeConversionType;
  config: DatatypeConversionConfig | undefined;
  widget_type: WidgetType | undefined;

  constructor(type: DatatypeConversionType, widget_type?: WidgetType) {
    this.type = type;
    this.widget_type = widget_type;
  }
}
export class CustomFunctionOutputs implements BaseWorkflowModel {
  type: CustomFunctionInputOutputTypes;
  arg_name: string;

  constructor(type: CustomFunctionInputOutputTypes, argName: string) {
    this.type = type;
    this.arg_name = argName;
  }
}

export class CustomFunctionInputs implements BaseWorkflowModel {
  type: CustomFunctionInputOutputTypes | undefined;
  input_urn: string | undefined;
  arg_name: string | undefined;

  constructor(
    type: CustomFunctionInputOutputTypes,
    inputUrn: string,
    argName: string,
  ) {
    this.type = type;
    this.input_urn = inputUrn;
    this.arg_name = argName;
  }
}

export class ResultValue {
  dataset_id: string | undefined;
}

export class StringResult extends ResultValue {
  string_value: string;

  constructor(string_value: string) {
    super();
    this.string_value = string_value;
  }
}

export class FilePathResult extends ResultValue {
  file_path_value: string;

  constructor(file_path_value: string) {
    super();
    this.file_path_value = file_path_value;
  }
}

export class StringsListResult extends ResultValue {
  strings_list_value: [];

  constructor(strings_list_value: []) {
    super();
    this.strings_list_value = strings_list_value;
  }
}

export class FloatListResult extends ResultValue {
  floats_list_value: [];

  constructor(floats_list_value: []) {
    super();
    this.floats_list_value = floats_list_value;
  }
}

export class IntergerListResult extends ResultValue {
  integers_list_value: [];

  constructor(integers_list_value: []) {
    super();
    this.integers_list_value = integers_list_value;
  }
}

export class BooleanResult extends ResultValue {
  boolean_value: [];

  constructor(boolean_value: []) {
    super();
    this.boolean_value = boolean_value;
  }
}

export class FloatResult extends ResultValue {
  float_value: string;

  constructor(float_value: string) {
    super();
    this.float_value = float_value;
  }
}
export class IntegerResult extends ResultValue {
  integer_value: string;

  constructor(integer_value: string) {
    super();
    this.integer_value = integer_value;
  }
}

export class DictionaryResult extends ResultValue {
  dict_value: Object;
  dict_input: any;
  constructor(dict_value: any, dict_input: any) {
    super();
    this.dict_value = dict_value;
    this.dict_input = dict_input;
  }
}

export class DatasetResult extends ResultValue {
  override dataset_id: string;

  constructor(dataset_id: string) {
    super();
    this.dataset_id = dataset_id;
  }
}

export class DefaultValue {
  type?: string | undefined;
  result?: ResultValue | undefined;

  constructor(type?: string, result?: ResultValue) {
    this.type = type;
    this.result = result;
  }
}

export class DropDownDetails {
  is_dropdown: boolean | undefined;
  drop_down_type: string | undefined;
  drop_down_source_details: any;
}

export class CustomFunctionParameters implements BaseWorkflowModel {
  type: string | undefined;
  arg_name: string;
  value: DefaultValue;
  is_mandatory: boolean = false;
  default_value: DefaultValue;
  ui_details: string | undefined;
  drop_down_details: DropDownDetails | undefined;
  isLoading: boolean = false;

  constructor(
    type: string,
    arg_name: string,
    value: DefaultValue,
    is_mandatory: boolean,
    default_value: DefaultValue,
    ui_details: string,
  ) {
    this.type = type;
    this.arg_name = arg_name;
    this.value = value;
    this.is_mandatory = is_mandatory;
    this.default_value = default_value;
    this.ui_details = ui_details;
  }
}

export class CustomCodeWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  module_id: string | undefined;
  widget_id: string | undefined;
  function_inputs: CustomFunctionInputs[] = [];
  function_outputs: CustomFunctionOutputs[] = [];
  widget_parameters: CustomFunctionParameters[] = [];
  widget_type: WidgetType | undefined;
}

export enum SaveScope {
  GLOBAL = 'GLOBAL',
  WORKFLOW = 'WORKFLOW',
  RUN = 'RUN',
}

export enum DestinationTypes {
  MOUNTED_DRIVE = 'MOUNTED_DRIVE',
  HEXAIND_PLATFORM = 'HEXAIND_PLATFORM',
  DATA_STORE = 'DATA_STORE',
}

export enum FileFormatOptions {
  CSV = 'CSV',
  PARQUET = 'PARQUET',
  IMAGE = 'IMAGE',
  VIDEO = 'VIDEO',
  EXCEL = 'EXCEL',
}

export enum FileSaveOptions {
  REPLACE = 'REPLACE',
  SAVE_AS = 'SAVE_AS',
}

export class SaveAsConfig {
  file_name: string | undefined;
}

export class ReplaceConfig {
  existing_dataset_id: string | undefined;
  destination_path: string = '';
}

export class SaveOptionConfig {
  file_Format: FileFormatOptions | undefined;
  save_options: FileSaveOptions | undefined;
  save_option_config: ReplaceConfig | SaveAsConfig | undefined;
  destination_folder_path: string = '';
}
export class DatasetConfiguration {
  dataset_name: string | undefined;
  destination_type: DestinationTypes | undefined;
  destination_config: SaveOptionConfig | undefined;
  doNotSaveFlag: boolean | undefined;
}

export class SaveWidgetConfig {
  version: string = '1.0';
  datasetConfig: DatasetConfiguration[] = [];
  widget_type: WidgetType | undefined;
}

export class FunctionInputs implements BaseWorkflowModel {
  input_urn: string | undefined;
  urn: string | undefined;
  name: string | undefined;
}

export class PivotWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  widget_type: WidgetType | undefined;
}

export class JoinWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  transform_type: string | undefined;
  left_dataset_path: string | undefined;
  right_dataset_path: string | undefined;
  left_columns: string[] | undefined;
  right_columns: string[] | undefined;
  join_type: JoinType | undefined = undefined;
  user_id: string | undefined;
  widget_type: WidgetType | undefined;

  constructor() {
    this.version = '1.0';
    this.left_columns = [];
    this.right_columns = [];
  }
}

export class AppendWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  user_id: string | undefined;
  output_dataset_name: string | undefined;
  max_rows: number | undefined;
  ignore_index: boolean | undefined;
  transform_type: WidgetType = WidgetType.APPEND;
  widget_type: WidgetType | undefined;
  column_type_pref_list: any | undefined;
}

export class UnionWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  widget_type: WidgetType | undefined;
}

export class PythonWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  widget_type: WidgetType | undefined;
}
export enum RescaleConnectionTypes {
  Abacus = 'Abaqus',
  'LS-DYNA' = 'LS-DYNA',
}

export class RescaleWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  input_file_name: string | undefined;
  rescale_connector_id: string | undefined;
  rescale_configs: any | undefined;
  JSONFileName: string | undefined;
  widget_type: WidgetType | undefined;
}
export class DecisionWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  criteria: DecisionCriteria | undefined;
  widget_type: WidgetType | undefined;
}
export class DecisionCriteria implements BaseWorkflowModel {
  field: string | undefined;
  operator: string | undefined;
  value: any | undefined;
}

export class RescaleConfig implements BaseWorkflowModel {
  workflow_name: string | undefined;
  description: string | undefined;
  mobo_output: string = 'mobo_output';
  rescale_conn_id: string | undefined;
  widget_type: WidgetType | undefined;
}

export class RescaleConnectorWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  config: RescaleConnectorConfig | undefined;
  widget_type: WidgetType | undefined;
}

export class PostRescaleWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  post_rescale_module_id: string = '658aea3e9b4341f250e66888';
  post_rescale_data: { file_name: string; path: string }[] | undefined;
  inputs: FunctionInputs[] = [];
  widget_type: WidgetType | undefined;
}

export class FeatureEngineeringWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  config: FeatureEngineeringConfig | undefined;
  inputs: FunctionInputs[] = [];
  widget_type: WidgetType | undefined;
}

export class FeatureEngineeringConfig implements BaseWorkflowModel {
  name: string | undefined;
  description: string | undefined;
  widget_type: WidgetType | undefined;
}

export class Inputs implements BaseWorkflowModel {}

export class Outputs implements BaseWorkflowModel {}

interface FeatureDetail {
  name: string;
  dataType: string;
  selected: boolean;
  input?: boolean;
  output?: boolean;
  min?: number;
  max?: number;
}

export class MOBOWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  input_variables: string[] = [];
  input_variables_constraints: [number, number][] = [[0, 0]];
  output_variables: string[] = [];
  output_variables_objectives: string[] = [];
  output_variables_thresholds: number[] = [];
  num_iterations: number = 1;
  initialize_experiment: boolean = true;
  run_iterations: boolean = true;
  experiment_type: string = 'OPTIMIZATION';
  batch_size: number = 2;
  constraints_module_id: string | undefined | null;
  outcome_constraints_active?: boolean = false;
  outcome_constraints_variable?: string | undefined;
  outcome_constraints_operator?: string | undefined;
  outcome_constaints_inputvalue?: number = 2;
  features_detail: FeatureDetail[] = [];
  widget_type: WidgetType | undefined;
  dataset: string | undefined;
}

export class ActiveLearningWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  input_variables: string[] = [];
  input_variables_constraints: [number, number][] = [[0, 0]];
  output_variables: string[] = [];
  output_variables_objectives: string[] = [];
  output_variables_thresholds: number[] = [];
  num_iterations: number = 1;
  initialize_experiment: boolean = true;
  run_iterations: boolean = true;
  experiment_type: string = 'ACTIVE_LEARNING';
  batch_size: number = 2;
  constraints_module_id: string | undefined;
  features_detail: FeatureDetail[] = [];
  widget_type: WidgetType | undefined;
}

export class CustomCodeTerminationCriteriaConfig implements BaseWorkflowModel {
  version: string | undefined;
  module_id: string | undefined;
  function_inputs: CustomFunctionInputs[] = [];
  widget_type: WidgetType | undefined;
}

export class OnLoopTerminationCriteriaConfig implements BaseWorkflowModel {
  loop_count: number = 0;
}

export class LoopStartWidgetConfig implements BaseWorkflowModel {
  version: string | undefined;
  loop_start_config: { xyz: 1; abc: 1 } = { xyz: 1, abc: 1 };
  widget_type: WidgetType | undefined;
  constructor(widget_type?: WidgetType) {
    this.widget_type = widget_type;
  }
}

export class LoopEndWidgetConfig implements BaseWorkflowModel {
  version: string | undefined;
  termination_criteria: TerminationCriteria;
  loop_end_config:
    | OnLoopTerminationCriteriaConfig
    | CustomCodeTerminationCriteriaConfig;
  // Widget urns's for loop continutation
  on_loop: string[] = [];
  // Widget urns's for loop terimination
  on_termination: string[] = [];
  widget_type: WidgetType | undefined;

  constructor(
    termination_criteria: TerminationCriteria,
    loop_end_config:
      | OnLoopTerminationCriteriaConfig
      | CustomCodeTerminationCriteriaConfig,
    widget_type?: WidgetType,
  ) {
    this.termination_criteria = termination_criteria;
    this.loop_end_config = loop_end_config;
    this.widget_type = widget_type;
  }
}

export class InputOutputConfig implements BaseWorkflowModel {
  urn: string | undefined = undefined;
  map_to_argument: string | undefined = undefined;
  type: RequestType = RequestType.DATASET;
  name: string | undefined = undefined;
}

export enum sampleType {
  none = 'none',
  smote = 'smote',
  randomus = 'randomus',
}

export class CovariancFunction implements BaseWorkflowModel {
  kernel_selected: Boolean = false;
  covariance_function_selection: boolean[] = [
    false,
    false,
    false,
    false,
    false,
  ];
}

export class GPCWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  widget_type: WidgetType | undefined;
  input_cols: string[] = [];
  output_col: string | undefined;
  mean = 'constant';

  variational: boolean = false;
  num_latents: number = 4;
  num_inducing: number = 200;
  problem_type: ProblemType | undefined;

  spectral_kernel_setting:
    | {
        spectral_kernel: boolean;
        num_mixtures: number | null;
      }
    | false = false;

  sampler_type: sampleType | undefined;
  max_trains: number | undefined;
  covariance_function: CovariancFunction | undefined;

  constructor(data?: Partial<GPCWidgetConfig>) {
    Object.assign(this, data);

    if (
      data?.spectral_kernel_setting &&
      typeof data.spectral_kernel_setting === 'object'
    ) {
      this.spectral_kernel_setting = {
        spectral_kernel: true,
        num_mixtures: data.spectral_kernel_setting.num_mixtures ?? 7,
      };
    } else {
      this.spectral_kernel_setting = false;
    }

    // Default values
    this.sampler_type = data?.sampler_type ?? sampleType.none;
    this.max_trains = data?.max_trains ?? 1500;
    this.covariance_function = {
      kernel_selected: false,
      covariance_function_selection: [false, true, false, false, false],
    };
    this.widget_type = WidgetType.GPC;
    this.problem_type = ProblemType.Classification;
  }
}

export class GPRWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  input_cols: string[] = [];
  output_cols: string[] = [];
  mean = 'zero';

  variational:
    | {
        num_latents?: number | null;
        num_inducing?: number | null;
      }
    | false = false;

  spectral_kernel:
    | {
        spectral_selected: boolean;
        num_mixtures: number | null;
      }
    | false = false;

  kernel_selected: boolean[] = [false, false, false, false, false];
  widget_type: WidgetType | undefined;
  problem_type: ProblemType | undefined;
  split_ratio: number | undefined;

  constructor(data?: Partial<GPRWidgetConfig>, widget_type?: WidgetType) {
    Object.assign(this, data);
    this.problem_type = ProblemType.Regression;
    this.kernel_selected = data?.kernel_selected || [
      false,
      true,
      false,
      false,
      false,
    ];
    // Check and assign variational only if not explicitly false and data is provided
    if (data?.variational && typeof data.variational === 'object') {
      this.problem_type = ProblemType.Regression;
      this.variational = {
        num_latents: data.variational.num_latents ?? 4,
        num_inducing: data.variational.num_inducing ?? 4,
      };
    } else {
      this.variational = false;
    }

    if (data?.spectral_kernel && typeof data.spectral_kernel === 'object') {
      this.spectral_kernel = {
        spectral_selected: true,
        num_mixtures: data.spectral_kernel.num_mixtures ?? 7,
      };
    } else {
      this.spectral_kernel = false;
    }
    this.widget_type = widget_type;
    this.split_ratio = 80;
  }
}
export class MPRWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  input_cols: string[] = [];
  output_col: string | undefined;
  split_type: string | undefined | null;
  input_scaling: string | null;
  polynomial_degree: number | null;
  polynomial_degree_feature:
    | { feature_name: string; feature_value: number }[]
    | null = [];
  cross_validation_folds: number | null;
  random_state: number | string | null;
  categorical_encoding: string | undefined | null;
  widget_type: WidgetType | undefined;
  problem_type: ProblemType | undefined;
  split_ratio: number | undefined;

  constructor(data?: Partial<MPRWidgetConfig>, widget_type?: WidgetType) {
    Object.assign(this, data);
    this.problem_type = ProblemType.Regression;
    this.split_type = 'Random';
    this.input_scaling = 'Standard';
    this.polynomial_degree = 2;
    this.polynomial_degree_feature = [];
    this.cross_validation_folds = 10;
    this.random_state = null;
    this.categorical_encoding = 'One_hot';
    this.widget_type = widget_type;
    this.split_ratio = 20;
  }
}

export class AdditionalHyperparameterTuneKWargs implements BaseWorkflowModel {
  scheduler?: string | undefined;
  searcher?: string | undefined;
  num_trials: number | undefined;
  time_out?: number | undefined;
}

export class AutoMLHyperparameters implements BaseWorkflowModel {
  GBM: {} | undefined;
  CAT: {} | undefined;
  XGB: {} | undefined;
  RF: {} | undefined;
  XT: {} | undefined;
  KNN: {} | undefined;
  LR: {} | undefined;
  NN_TORCH: {} | undefined;
  FASTAI: {} | undefined;
  ARIMA: {} | undefined;
}

export class LRMLHyperparameters implements BaseWorkflowModel {
  LR: {} | undefined;
}

export class LGBMMLHyperparameters implements BaseWorkflowModel {
  GBM: {} | undefined;
}

export enum EvaluationMetric {
  root_mean_squared_error = 'root_mean_squared_error',
  mean_squared_error = 'mean_squared_error',
  mean_absolute_error = 'mean_absolute_error',
  mean_absolute_percentage_error = 'mean_absolute_percentage_error',
}

export enum InputScaling {
  Min_Max = 'Min-Max',
  Standard = 'Standard',
  Robust = 'Robust',
}

export enum ProblemType {
  Regression = 'regression',
  Classification = 'classification',
}

export enum ClassificationMetrics {
  Accuracy = 'accuracy',
  Log_Loss = 'f1_weighted',
  Weighted_F1_Score = 'log_loss',
}

export class AutoMLConfigRegression implements BaseWorkflowModel {
  evaluation_metric: EvaluationMetric | undefined;
  automl_hyperparameters: AutoMLHyperparameters | undefined;

  widget_type: WidgetType | undefined;

  constructor(widget_type?: WidgetType) {
    this.evaluation_metric = EvaluationMetric.root_mean_squared_error;
    this.widget_type = widget_type;
    this.automl_hyperparameters = {
      GBM: {},
      CAT: {},
      XGB: {},
      RF: {},
      XT: {},
      KNN: {},
      LR: {},
      NN_TORCH: {},
      FASTAI: {},
      ARIMA: {},
    };
  }
}

export class AutoMLHyperparametersCls implements BaseWorkflowModel {
  GBM: any[] | undefined;
  CAT: {} | undefined;
  XGB: {} | undefined;
  RF: any[] | undefined;
  XT: any[] | undefined;
  KNN: any[] | undefined;
  LR: {} | undefined;
  NN_TORCH: {} | undefined;
  FASTAI: {} | undefined;
  ARIMA: {} | undefined;
}

export class AutoMLConfigClassification implements BaseWorkflowModel {
  evaluation_metric_cls: ClassificationMetrics | undefined;
  automl_hyperparameters_cls: AutoMLHyperparametersCls | undefined;

  constructor() {
    this.evaluation_metric_cls = ClassificationMetrics.Accuracy;
    this.automl_hyperparameters_cls = {
      GBM: [
        { extra_trees: true, ag_args: { name_suffix: 'XT' } },
        {},
        'GBMLarge',
      ],
      CAT: {},
      XGB: {},
      RF: [
        {
          criterion: 'gini',
          ag_args: {
            name_suffix: 'Gini',
            problem_types: ['binary', 'multiclass'],
          },
        },
        {
          criterion: 'entropy',
          ag_args: {
            name_suffix: 'Entr',
            problem_types: ['binary', 'multiclass'],
          },
        },
        {
          criterion: 'squared_error',
          ag_args: {
            name_suffix: 'MSE',
            problem_types: ['regression', 'quantile'],
          },
        },
      ],
      XT: [
        {
          criterion: 'gini',
          ag_args: {
            name_suffix: 'Gini',
            problem_types: ['binary', 'multiclass'],
          },
        },
        {
          criterion: 'entropy',
          ag_args: {
            name_suffix: 'Entr',
            problem_types: ['binary', 'multiclass'],
          },
        },
        {
          criterion: 'squared_error',
          ag_args: {
            name_suffix: 'MSE',
            problem_types: ['regression', 'quantile'],
          },
        },
      ],
      KNN: [
        { weights: 'uniform', ag_args: { name_suffix: 'Unif' } },
        { weights: 'distance', ag_args: { name_suffix: 'Dist' } },
      ],
      LR: {},
      NN_TORCH: {},
      FASTAI: {},
      ARIMA: {},
    };
  }
}

export class AutoMLWidgetConfig implements BaseWorkflowModel {
  problem_type: ProblemType | undefined;
  version: '1.0';
  input_cols: string[] = [];
  output_col: string | undefined;
  split_ratio: number | undefined;
  automl_config:
    | AutoMLConfigRegression
    | AutoMLConfigClassification
    | undefined;
  additional_hyperparameter_tune_kwargs:
    | AdditionalHyperparameterTuneKWargs
    | undefined;
  widget_type: WidgetType | undefined;

  constructor(widget_type?: WidgetType) {
    this.problem_type = ProblemType.Regression;
    this.version = '1.0';
    this.input_cols = [];
    this.output_col = undefined;
    this.split_ratio = 80;
    this.additional_hyperparameter_tune_kwargs = { num_trials: 3 };
    this.widget_type = widget_type;
  }
}

export class RandomForestRegressionMLHyperparameters
  implements BaseWorkflowModel
{
  RF: {} | undefined;
}
export class RandomForestRegressionMLWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  input_cols: string[] = [];
  output_col: string | undefined;
  split_ratio: number | undefined;
  evaluation_metric: EvaluationMetric | undefined;
  rf_hyperparameters: RandomForestRegressionMLHyperparameters | undefined;
  additional_hyperparameter_tune_kwargs:
    | AdditionalHyperparameterTuneKWargs
    | undefined;
  widget_type: WidgetType | undefined;
  problem_type: ProblemType | undefined;

  constructor(widget_type?: WidgetType) {
    this.version = '1.0';
    this.problem_type = ProblemType.Regression;
    this.input_cols = [];
    this.output_col = undefined;
    this.split_ratio = 80;
    this.evaluation_metric = EvaluationMetric.root_mean_squared_error;
    this.rf_hyperparameters = {
      RF: {},
    };
    this.additional_hyperparameter_tune_kwargs = { num_trials: 3 };
    this.widget_type = widget_type;
  }
}
export class CatBoostMLHyperparameters implements BaseWorkflowModel {
  CAT: {} | undefined;
}
export class CatBoostMLWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  input_cols: string[] = [];
  output_col: string | undefined;
  split_ratio: number | undefined;
  evaluation_metric: EvaluationMetric | undefined;
  catboost_hyperparameters: CatBoostMLHyperparameters | undefined;
  additional_hyperparameter_tune_kwargs:
    | AdditionalHyperparameterTuneKWargs
    | undefined;
  widget_type: WidgetType | undefined;
  problem_type: ProblemType | undefined;

  constructor(widget_type?: WidgetType) {
    this.version = '1.0';
    this.problem_type = ProblemType.Regression;
    this.input_cols = [];
    this.output_col = undefined;
    this.split_ratio = 80;
    this.evaluation_metric = EvaluationMetric.root_mean_squared_error;
    this.catboost_hyperparameters = {
      CAT: {},
    };
    this.additional_hyperparameter_tune_kwargs = { num_trials: 3 };
    this.widget_type = WidgetType.CATBOOST;
  }
}

export class ExtreaTreeMLHyperparameters implements BaseWorkflowModel {
  XT: {} | undefined;
}
export class ExtraTreeMLWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  input_cols: string[] = [];
  output_col: string | undefined;
  split_ratio: number | undefined;
  evaluation_metric: EvaluationMetric | undefined;
  extratrees_hyperparameters: ExtreaTreeMLHyperparameters | undefined;
  additional_hyperparameter_tune_kwargs:
    | AdditionalHyperparameterTuneKWargs
    | undefined;
  widget_type: WidgetType | undefined;
  problem_type: ProblemType | undefined;
  constructor(widget_type?: WidgetType) {
    this.version = '1.0';
    this.problem_type = ProblemType.Regression;
    this.input_cols = [];
    this.output_col = undefined;
    this.split_ratio = 80;
    this.evaluation_metric = EvaluationMetric.root_mean_squared_error;
    this.extratrees_hyperparameters = {
      XT: {},
    };
    this.additional_hyperparameter_tune_kwargs = { num_trials: 3 };
    this.widget_type = WidgetType.EXTRA_TREES;
  }
}
export class KNearestNeighborMLHyperparameters implements BaseWorkflowModel {
  KNN: {} | undefined;
}
export class KNearestNeighborMLWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  input_cols: string[] = [];
  output_col: string | undefined;
  split_ratio: number | undefined;
  evaluation_metric: EvaluationMetric | undefined;
  knn_hyperparameters: KNearestNeighborMLHyperparameters | undefined;
  widget_type: WidgetType | undefined;
  additional_hyperparameter_tune_kwargs:
    | AdditionalHyperparameterTuneKWargs
    | undefined;
  problem_type: ProblemType | undefined;
  constructor(widget_type?: WidgetType) {
    this.version = '1.0';
    this.problem_type = ProblemType.Regression;
    this.input_cols = [];
    this.output_col = undefined;
    this.split_ratio = 80;
    this.evaluation_metric = EvaluationMetric.root_mean_squared_error;
    this.knn_hyperparameters = {
      KNN: {},
    };
    this.additional_hyperparameter_tune_kwargs = { num_trials: 3 };
    this.widget_type = WidgetType.KNEIGHBORS;
  }
}

export enum SplitType {
  Random = 'Random',
  Sequential = 'Sequential',
}

export enum EncodingType {
  Onehot = 'Onehot',
  Mean = 'Mean',
}

export enum XGBoostInputScaling {
  Standard = 'Standard',
  Min_Max = 'Min-Max',
  Robust = 'Robust',
  None = 'None',
}

export enum SamScenrioTypes {
  Scrap = 'scrap',
  Demand = 'demand',
  Plant = 'plant',
  LimitScrap = 'limit-scrap',
  LimitDemand = 'limit-demand',
}

export class XGBoostParams implements BaseWorkflowModel {
  // Main Model parameters:
  input_scaling!: XGBoostInputScaling | null;
  split_type: SplitType | undefined | null;
  split_ratio: number | undefined;
  k_fold: number | null = null;
  n_estimators!: number | null;
  max_depth: number | undefined;
  learning_rate: number | undefined;

  // Advanced parameters:
  subsample: number | undefined;
  colsample_bytree: number | undefined;
  colsample_bylevel: number | undefined;
  colsample_bynode: number | undefined;
  num_parallel_tree: number | undefined;
  encoding_type!: EncodingType | null;
  split_random_state!: number | null;
}
export class XGBoostMLWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  widget_type: WidgetType | undefined;
  problem_type: ProblemType | undefined;
  input_cols: string[] = [];
  output_col: string | undefined;
  hyper_params: XGBoostParams | undefined;

  constructor(widget_type?: WidgetType) {
    this.version = '1.0';
    this.problem_type = ProblemType.Regression;
    this.input_cols = [];
    this.output_col = undefined;
    this.hyper_params = new XGBoostParams();
    this.hyper_params.split_ratio = 20;
    this.hyper_params.learning_rate = 0.1;
    this.hyper_params.k_fold = 10;
    // this.hyper_params.n_estimators = [10, 200, 10];
    this.hyper_params.n_estimators = 100;
    this.hyper_params.max_depth = 6;
    this.hyper_params.input_scaling = XGBoostInputScaling.Standard;
    this.hyper_params.split_type = SplitType.Random;
    this.hyper_params.subsample = 1;
    this.hyper_params.colsample_bytree = 1;
    this.hyper_params.colsample_bylevel = 1;
    this.hyper_params.colsample_bynode = 1;
    this.hyper_params.num_parallel_tree = 1;
    this.hyper_params.encoding_type = null;
    this.widget_type = widget_type;
    this.hyper_params.split_random_state = null;
  }
}

export class LGBMParameters implements BaseWorkflowModel {
  Selected_Optimization_method: OptimizationMethod =
    OptimizationMethod.GridSearch;
  cv: number;
  random_state: number;
  n_iter: number | undefined;
  Min_depth: number;
  Max_depth: number;
  SampleNo_depth: number;
  Min_num_leaves: number;
  Max_num_leaves: number;
  SampleNo_num_leaves: number;
  Min_child_samples: number;
  Max_child_samples: number;
  SampleNo_child_samples: number;

  constructor(
    Selected_Optimization_method: OptimizationMethod = OptimizationMethod.GridSearch,
    cv: number,
    random_state: number,
    n_iter: number | undefined,
    Min_depth: number,
    Max_depth: number,
    SampleNo_depth: number,
    Min_num_leaves: number,
    Max_num_leaves: number,
    SampleNo_num_leaves: number,
    Min_child_samples: number,
    Max_child_samples: number,
    SampleNo_child_samples: number,
  ) {
    (this.Selected_Optimization_method = Selected_Optimization_method),
      (this.cv = cv),
      (this.random_state = random_state),
      (this.n_iter = n_iter),
      (this.Min_depth = Min_depth),
      (this.Max_depth = Max_depth),
      (this.SampleNo_depth = SampleNo_depth),
      (this.Min_num_leaves = Min_num_leaves),
      (this.Max_num_leaves = Max_num_leaves),
      (this.SampleNo_num_leaves = SampleNo_num_leaves),
      (this.Min_child_samples = Min_child_samples),
      (this.Max_child_samples = Max_child_samples),
      (this.SampleNo_child_samples = SampleNo_child_samples);
  }
}

export class LGBMMLWidgetConfigMLHyperparameters implements BaseWorkflowModel {
  GBM: LGBMParameters | undefined;
}
export class LGBMMLWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  input_cols: string[] = [];
  output_col: string | undefined;
  split_ratio: number | undefined;
  input_scaling: InputScaling | undefined;
  random_search: RandomSearchConfig | undefined;
  evaluation_metric: EvaluationMetric | undefined;
  lgbm_hyperparameters: LGBMMLWidgetConfigMLHyperparameters | undefined;
  widget_type: WidgetType | undefined;
  additional_hyperparameter_tune_kwargs:
    | AdditionalHyperparameterTuneKWargs
    | undefined;
  problem_type: ProblemType | undefined;
  constructor(widget_type?: WidgetType) {
    this.version = '1.0';
    this.problem_type = ProblemType.Regression;
    this.input_cols = [];
    this.output_col = undefined;
    this.split_ratio = 80;
    this.input_scaling = InputScaling.Standard;
    this.evaluation_metric = EvaluationMetric.root_mean_squared_error;
    // this.lgbm_hyperparameters = lgbm_hyperparameters;

    // this.lgbm_hyperparameters = {
    //   GBM: {}
    // };
    this.additional_hyperparameter_tune_kwargs = {
      num_trials: 3,
      scheduler: 'local',
      searcher: 'auto',
      time_out: 600,
    };
    this.widget_type = widget_type;
  }
}

export class LRMLWidgetConfigMLHyperparameters implements BaseWorkflowModel {
  LR: {} | undefined;
}
export class LinearRegressionMLWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  input_cols: string[] = [];
  output_col: string | undefined;
  split_ratio: number | undefined;
  evaluation_metric: EvaluationMetric | undefined;
  lr_hyperparameters: LRMLWidgetConfigMLHyperparameters | undefined;
  widget_type: WidgetType | undefined;
  additional_hyperparameter_tune_kwargs:
    | AdditionalHyperparameterTuneKWargs
    | undefined;
  problem_type: ProblemType | undefined;
  constructor(widget_type?: WidgetType) {
    this.version = '1.0';
    this.input_cols = [];
    this.output_col = undefined;
    this.problem_type = ProblemType.Regression;
    this.split_ratio = 80;
    this.evaluation_metric = EvaluationMetric.root_mean_squared_error;
    this.lr_hyperparameters = {
      LR: {},
    };
    this.additional_hyperparameter_tune_kwargs = { num_trials: 3 };
    this.widget_type = widget_type;
  }
}

export class NeuralNetworkRegressionMLHyperparameters
  implements BaseWorkflowModel
{
  FASTAI: {} | undefined;
}
export class NeuralNetworkRegressionMLWidgetConfig
  implements BaseWorkflowModel
{
  version = '1.0';
  input_cols: string[] = [];
  output_col: string | undefined;
  split_ratio: number | undefined;
  evaluation_metric: EvaluationMetric | undefined;
  fastai_hyperparameters: NeuralNetworkRegressionMLHyperparameters | undefined;
  widget_type: WidgetType | undefined;
  additional_hyperparameter_tune_kwargs:
    | AdditionalHyperparameterTuneKWargs
    | undefined;
  problem_type: ProblemType | undefined;
  constructor(widget_type?: WidgetType) {
    this.version = '1.0';
    this.problem_type = ProblemType.Regression;
    this.input_cols = [];
    this.output_col = undefined;
    this.split_ratio = 80;
    this.evaluation_metric = EvaluationMetric.root_mean_squared_error;
    this.fastai_hyperparameters = {
      FASTAI: {},
    };
    this.additional_hyperparameter_tune_kwargs = { num_trials: 3 };
    this.widget_type = WidgetType.NNFASTAI;
  }
}
export class NNTorchMLHyperparameters implements BaseWorkflowModel {
  NN_TORCH: {} | undefined;
}

export class NnTorchMLWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  input_cols: string[] = [];
  output_col: string | undefined;
  split_ratio: number | undefined;
  evaluation_metric: EvaluationMetric | undefined;
  nntorch_hyperparameters: NNTorchMLHyperparameters | undefined;
  widget_type: WidgetType | undefined;
  additional_hyperparameter_tune_kwargs:
    | AdditionalHyperparameterTuneKWargs
    | undefined;
  problem_type: ProblemType | undefined;

  constructor(widget_type?: WidgetType) {
    this.version = '1.0';
    this.problem_type = ProblemType.Regression;
    this.input_cols = [];
    this.output_col = undefined;
    this.split_ratio = 80;
    this.evaluation_metric = EvaluationMetric.root_mean_squared_error;
    this.nntorch_hyperparameters = {
      NN_TORCH: {},
    };
    this.additional_hyperparameter_tune_kwargs = { num_trials: 3 };
    this.widget_type = WidgetType.NN_TORCH;
  }
}

export class ARIMAMLHyperparameters implements BaseWorkflowModel {
  ARIMA: {} | undefined;
}
export class ARIMAMLWidgetConfig implements BaseWorkflowModel {
  version = '1.0';
  input_cols: string[] = [];
  output_col: string | undefined;
  split_ratio: number | undefined;
  evaluation_metric: EvaluationMetric | undefined;
  arima_hyperparameters: ARIMAMLHyperparameters | undefined;
  widget_type: WidgetType | undefined;
  additional_hyperparameter_tune_kwargs:
    | AdditionalHyperparameterTuneKWargs
    | undefined;

  constructor(widget_type?: WidgetType) {
    this.version = '1.0';
    this.input_cols = [];
    this.output_col = undefined;
    this.split_ratio = 80;
    this.evaluation_metric = EvaluationMetric.root_mean_squared_error;
    this.arima_hyperparameters = {
      ARIMA: {},
    };
    this.additional_hyperparameter_tune_kwargs = { num_trials: 3 };
    this.widget_type = widget_type;
  }
}

export class ThermoCalcWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  thermocalc_connector_id: string | undefined;
  module_id: string | undefined;
  input_features: string[] | undefined;
  output_features: string[] | undefined;
  json_config: any | undefined;
  widget_type: WidgetType | undefined;

  constructor(widget_type?: WidgetType) {
    this.version = '1.0';
    this.thermocalc_connector_id = undefined;
    this.module_id = undefined;
    this.input_features = [];
    this.output_features = [];
    this.json_config = undefined;
    this.widget_type = WidgetType.THERMOCALC;
  }
}

export class PredictionWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0';
  widget_type: string = WidgetType.PREDICTION;
  ml_id: string | undefined;
  constructor() {
    this.version = '1.0';
    this.widget_type = WidgetType.PREDICTION;
  }
}

export class LocalTextConfiguration implements BaseWorkflowModel {
  version: string = '1.0';
  dataset_id: string = ''; // Initialize with an empty string to avoid undefined issues
}

export class SourceTextConfig implements BaseWorkflowModel {
  type: SourceType;
  configuration:
    | LocalTextConfiguration
    | BigQueryDatasetConfiguration
    | MountedDriveConfiguration;
  widget_type: WidgetType;

  constructor(
    type: SourceType,
    configuration:
      | LocalTextConfiguration
      | BigQueryDatasetConfiguration
      | MountedDriveConfiguration,
    widget_type: WidgetType = WidgetType.TEXT_DATA, // Set default value if not provided
  ) {
    this.type = type;
    this.configuration = configuration;
    this.widget_type = widget_type;
  }
}

export class SinkTextWidget implements BaseWorkflowModel {
  dataset_name: string = ''; // Initialized to avoid undefined
  dataset_description: string = ''; // Initialized to avoid undefined
}

export class TextWidgetConfig implements BaseWorkflowModel {
  version: string = '1.0'; // Default version
  widget_type: WidgetType = WidgetType.TEXT_DATA; // Default widget type
  source: SourceTextConfig[] = [
    new SourceTextConfig(SourceType.LOCAL, new LocalTextConfiguration()),
  ]; // Default source with one entry
  sink: SinkTextWidget[] = [new SinkTextWidget()]; // Default sink with one entry
}

export class SVMWidgetConfig {
  problem_type: 'regression' | 'classification' = 'regression';
  version = '1.0';
  input_cols: string[] = [];
  output_cols: string[] = [];
  sampling?: sampleType | undefined = sampleType.none;
  kernel: 'rbf' | 'poly' | 'linear' | 'sigmoid' = 'sigmoid';
  C: number | undefined = 0.1;
  gamma?: number | undefined = 0.00001;
  coef0?: number | undefined = 1.2;
  degree?: number | undefined = 3;
  widget_type: WidgetType | undefined;

  constructor(config?: Partial<SVMWidgetConfig>) {
    if (config) {
      Object.assign(this, config);
    }
    this.setDefaults(this.kernel);
    this.toggleProblemType(this.problem_type);
  }

  public setDefaults(kernel: 'rbf' | 'poly' | 'linear' | 'sigmoid'): void {
    this.kernel = kernel;
    switch (kernel) {
      case 'linear':
        this.gamma = undefined;
        this.coef0 = undefined;
        this.degree = undefined;
        break;
      case 'rbf':
        this.gamma = this.gamma ?? 0.00001;
        this.coef0 = undefined;
        this.degree = undefined;
        break;
      case 'poly':
        this.gamma = this.gamma ?? 0.00001;
        this.coef0 = this.coef0 ?? 1.2;
        this.degree = this.degree ?? 3;
        break;
      case 'sigmoid':
        this.gamma = this.gamma ?? 0.00001;
        this.coef0 = this.coef0 ?? 1.2;
        this.degree = undefined;
        break;
    }
  }

  public toggleProblemType(
    problem_type: 'regression' | 'classification',
  ): void {
    this.problem_type = problem_type;
    if (problem_type === 'regression') {
      this.problem_type = problem_type;
    } else if (problem_type === 'classification') {
      this.problem_type = problem_type;
    }
  }

  public toggleSampling(samplingType: any): void {
    this.sampling = samplingType;
  }
}

export enum ImageTypes {
  Raw = 'Raw',
  Segmented = 'Segmented',
}
export class ImageDataset {
  dataset_id: string | undefined;
  dataset_name: string | undefined;
}

export enum GeometricProperties {
  orientation = 'orientation',
  solidity = 'solidity',
  extent = 'extent',
}

export enum GeometricPropertiesScaled {
  perimeter = 'perimeter',
  perimeter_crofton = 'perimeter_crofton',
  feret_diameter_max = 'feret_diameter_max',
  axis_minor_length = 'axis_minor_length',
  axis_major_length = 'axis_major_length',
  area_convex = 'area_convex',
  area_filled = 'area_filled',
  area_bbox = 'area_bbox',
  area = 'area',
  equivalent_diameter_area = 'equivalent_diameter_area',
  bbox = 'bbox',
  'A.R' = 'A.R',
  'A.R_ell' = 'A.R_ell',
  'No. of objects' = 'No. of objects',
}

export enum CalculatedPropertiesScaled {
  // bbox_length = 'bbox_length',
  // bbox_height = 'bbox_height',
  bbox = 'bbox',
  'A.R' = 'A.R',
  'A.R_ell' = 'A.R_ell',
  'No. of objects' = 'No. of objects',
}

export enum IntensityBasedProperties {
  intensity_min = 'intensity_min',
  intensity_max = 'intensity_max',
  intensity_mean = 'intensity_mean',
  sd_intensity = 'sd_intensity',
  skew_intensity = 'skew_intensity',
}

export class ImageDatasetSelectionWidgetConfig {
  widget_type: WidgetType = WidgetType.IMAGE_DATASET;
  version = '1.0';
  image_type: ImageTypes = ImageTypes.Segmented;
  image_datasets: ImageDataset[] = [];
  constructor(config?: Partial<ImageDatasetSelectionWidgetConfig>) {
    if (config) {
      Object.assign(this, config);
    }
  }
}

export class ImageRegionPropertiesWidgetConfig {
  widget_type: WidgetType = WidgetType.REGION_PROPERTY;
  version = '1.0';
  region_properties: any[] = ['label'];
  constructor(config?: Partial<ImageRegionPropertiesWidgetConfig>) {
    if (config) {
      Object.assign(this, config);
    }
  }
}

export class ImageSpatialStatisticsWidgetConfig {
  widget_type: WidgetType = WidgetType.IMAGE_SPATIAL_STATISTICS;
  version = '1.0';
  cutoff: number = 2;
  quantTech: string = '';
  datasetId: string = '';
  local_states: number[][] = [];
  metadata: string = '';
  ang_int: number = 15;
  coarsening: number = 1;
  constructor(config?: Partial<ImageSpatialStatisticsWidgetConfig>) {
    if (config) {
      Object.assign(this, config);
    }
  }
}

export class Widget implements BaseWorkflowModel {
  _id: string | null = null;
  urn: string | undefined;
  name: string;
  description: string;
  type: WidgetType;
  config:
    | DataCopyWidgetConfig
    | JupyterWidgetConfig
    | FilterWidgetConfig
    | CustomCodeWidgetConfig
    | SaveWidgetConfig
    | DecisionWidgetConfig
    | MOBOWidgetConfig
    | RescaleWidgetConfig
    | PostRescaleWidgetConfig
    | RescaleConnectorWidgetConfigurations
    | JoinWidgetConfig
    | AppendWidgetConfig
    | FeatureEngineeringWidgetConfig
    | LoopStartWidgetConfig
    | LoopEndWidgetConfig
    | GPRWidgetConfig
    | MPRWidgetConfig
    | ThermoCalcWidgetConfig
    | ActiveLearningWidgetConfig
    | AutoMLWidgetConfig
    | LinearRegressionMLWidgetConfig
    | LGBMMLWidgetConfig
    | RandomForestRegressionMLWidgetConfig
    | XGBoostMLWidgetConfig
    | CatBoostMLWidgetConfig
    | NeuralNetworkRegressionMLWidgetConfig
    | ExtraTreeMLWidgetConfig
    | KNearestNeighborMLWidgetConfig
    | NnTorchMLWidgetConfig
    | ARIMAMLWidgetConfig
    | PredictionWidgetConfig
    | SVMWidgetConfig
    | GPCWidgetConfig
    | DropColumnsWidgetConfig
    | DropMissingWidgetConfig
    | RenameColumnsWidgetConfig
    | DatatypeConversionWidgetConfig
    | ImageDatasetSelectionWidgetConfig
    | ImageRegionPropertiesWidgetConfig
    | ImageSpatialStatisticsWidgetConfig
    | TextWidgetConfig;
  state: WidgetState;
  on_success: string[] = [];
  on_failure: string[] = [];
  on_complete: string[] = [];
  inputs: InputOutputConfig[] = [];
  outputs: InputOutputConfig[] = [];
  use_gpu: boolean;
  retry_interval_in_sec: number;
  retry_count: number;
  client_tags: WidgetClientTags;
  widget_id: string | undefined;
  status: string | undefined;

  static GetPositionX(widget: Widget) {
    return widget.client_tags.PositionX;
  }

  static GetPositionY(widget: Widget) {
    return widget.client_tags.PositionY;
  }

  static GetWidth(widget: Widget) {
    return widget.client_tags.Width;
  }

  static GetHeight(widget: Widget) {
    return widget.client_tags.Height;
  }

  static GetConnectorPointPositions(widget: Widget) {
    let topConnector: [number, number] = [
      Widget.GetPositionX(widget) + Widget.GetWidth(widget) / 2,
      Widget.GetPositionY(widget) - 15,
    ];
    let bottomConnector: [number, number] = [
      Widget.GetPositionX(widget) + Widget.GetWidth(widget) / 2,
      Widget.GetPositionY(widget) + Widget.GetHeight(widget) + 15,
    ];
    let leftConnector: [number, number] = [
      Widget.GetPositionX(widget) - 15,
      Widget.GetPositionY(widget) + Widget.GetHeight(widget) / 2,
    ];
    let rightConnector: [number, number] = [
      Widget.GetPositionX(widget) + Widget.GetWidth(widget) + 15,
      Widget.GetPositionY(widget) + Widget.GetHeight(widget) / 2,
    ];

    return [topConnector, bottomConnector, leftConnector, rightConnector];
  }

  constructor(
    name: string,
    description: string,
    type: WidgetType,
    config: any,
    state: WidgetState,
    on_success: string[],
    on_failure: string[],
    on_complete: string[],
    inputs: InputOutputConfig[],
    outputs: InputOutputConfig[],
    use_gpu: boolean,
    retry_interval_in_sec: number,
    retry_count: number,
    client_tags: WidgetClientTags,
    widget_id: string,
  ) {
    this.name = name;
    this.description = description;
    this.type = type;
    this.client_tags = client_tags;
    this.config = config;
    this.state = state;
    this.on_success = on_success;
    this.on_failure = on_failure;
    this.on_complete = on_complete;
    this.inputs = inputs;
    this.outputs = outputs;
    this.use_gpu = use_gpu;
    this.retry_interval_in_sec = retry_interval_in_sec;
    this.retry_count = retry_count;
    this.widget_id = widget_id;
  }
}

export class Workflow implements BaseWorkflowModel {
  _id: string | null = null;
  interactive_mode: boolean = false;
  name: string;
  description: string;
  workflow_version: string = '';
  widgets: Widget[] = [];
  state: WorkflowState = WorkflowState.IDLE;
  start: string[] = [];
  end: string[] = [];
  owner_id: string;
  owner_name: string;
  created_at: any;
  last_modified_by_id: string | undefined = undefined;
  last_modified_at: any;
  project_id: string;
  site_id: string;
  version: string | undefined = undefined;
  client_tags: WorkflowClientTags;
  partial_widgets: any;
  older_version_cpw_urns: any;
  constructor(
    name: string,
    description: string,
    ownerName: string,
    ownerId: string,
    projectId: string,
    siteId: string,
    client_tags: WorkflowClientTags,
  ) {
    this.name = name;
    this.description = description;
    this.owner_name = ownerName;
    this.owner_id = ownerId;
    this.project_id = projectId;
    this.site_id = siteId;
    this.widgets = [];
    this.client_tags = client_tags;
  }
}

export class RescaleConnectorWidgetConfigurations implements BaseWorkflowModel {
  version: string = '1.0';
  config: RescaleConnectorConfig | undefined;
}
export class filesObject implements BaseWorkflowModel {
  id: string | undefined;
  name: string | undefined;
}
export class RescaleConnectorConfig implements BaseWorkflowModel {
  software_configurations: any | undefined;
}

export class RescaleConnTemplate implements BaseWorkflowModel {
  name: string | undefined;
  test_mode: boolean | undefined;
  run_job: boolean | undefined;
  software: SoftwareConfig | undefined;

  // constructor(mlWorkflowModel: RescaleConnTemplate) {
  //   this.name = mlWorkflowModel.name;
  //   this.test_mode = mlWorkflowModel.test_mode;
  //   this.run_job = mlWorkflowModel.run_job;
  //   this.software = new SoftwareConfig(mlWorkflowModel.software);
  // }
}

export class SoftwareConfig implements BaseWorkflowModel {
  analysis: {
    code: string;
    version: string;
  };
  hardware: {
    coresPerSlot: number;
    slots: number;
    coreType: string;
    walltime: number;
    type?: string;
  };
  command: string;
  output_file: string;
  visualize_files?: string[];
  onDemandLicenseSeller?: string | null;
  envVars: { [key: string]: string };

  constructor(softwareConfig: SoftwareConfig) {
    this.analysis = softwareConfig.analysis;
    this.hardware = softwareConfig.hardware;
    this.command = softwareConfig.command;
    this.output_file = softwareConfig.output_file;
    this.visualize_files = softwareConfig.visualize_files;
    this.envVars = softwareConfig.envVars;
  }
}

export class StartNodeWidgetConfig implements BaseWorkflowModel {}

export class Action {
  urn: string | undefined = undefined;
  action_id: string | undefined = undefined;
}

export class WorkflowRun implements BaseWorkflowModel {
  _id: string | null = null;
  interactive_mode: boolean = false;
  is_single_widget_run: boolean = false;
  name: string;
  description: string;
  run_source: string;
  run_state: string;
  run_status: WorkflowState = WorkflowState.IDLE;
  actions: Action[] = [];
  owner_id: string;
  owner_name: string;
  created_at: any;
  last_modified_by_id: string | undefined = undefined;
  last_modified_at: any;
  project_id: string;
  site_id: string;
  workflow_id: string;
  version: string | undefined = undefined;

  constructor(
    name: string,
    description: string,
    ownerName: string,
    ownerId: string,
    projectId: string,
    siteId: string,
    run_source: string,
    run_state: string,
    workflow_id: string,
  ) {
    this.name = name;
    this.description = description;
    this.owner_name = ownerName;
    this.owner_id = ownerId;
    this.project_id = projectId;
    this.site_id = siteId;
    this.run_source = run_source;
    this.run_state = run_state;
    this.workflow_id = workflow_id;
  }
}

export class DatasetModel {
  name: string = '';
  id: string = '';

  constructor(name: string, id: string) {
    this.name = name;
    this.id = id;
  }
}
