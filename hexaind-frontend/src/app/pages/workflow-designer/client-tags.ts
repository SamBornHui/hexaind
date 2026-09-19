import { ArrowObject } from 'src/app/controls/widget-control/arrowObject';

export enum WidgetClientType {
  None = 'NONE',
  // DATA_COPY
  BigQuery = 'BIG_QUERY',
  CSVFile = 'CSV_FILE',
  Jupyter = 'JUPYTER',
  ImageFile = 'IMAGE_FILE',
  ParquetFile = 'PARQUET_FILE',
  PDFFile = 'PDF_FILE',
  ExcelFile = 'EXCEL_FILE',
  PREDICTION = 'PREDICTION',

  // MODEL_BUILDER
  LGBM = 'LGBM',
  MOBO = 'MOBO',
  Rescale = 'RESCALE',
  ThermoCalc = 'THERMOCALC',
  RescaleTemplateConnector = 'RESCALE_TEMPLATE_CONNECTOR',

  Save = 'SAVE',
  Filter = 'FILTER',
  DropMissing = 'DROP_MISSING',
  Pivot = 'PIVOT',
  Join = 'JOIN',
  Append = 'APPEND',
  Union = 'UNION',
  Python = 'PYTHON',
  ConfigFile = 'CONFIG_FILE',
  CustomCode = 'CUSTOM_CODE',
  POST_RESCALE = 'POST_RESCALE',
  Decision = 'DECISION',
  Feature_Engineering = 'Feature_Engineering',
  DropColumns = 'DROP_COLUMNS',
  RenameColumns = 'RENAME_COLUMNS',
  DatatypeConversion = "DATATYPE_CONVERSION",

  LoopStart = 'LOOP_START',
  LoopEnd = 'LOOP_END',

  Start = 'START',
  End = 'END',
  ACTIVE_LEARNING = 'ACTIVE_LEARNING',
  GPR = 'GPR',
  MPR = 'MPR',
  AutoML = 'AutoML',
  LINEAR_REGRESSION = 'LINEAR_REGRESSION',
  RF = 'RF',
  NNFASTAI = 'NNFASTAI',
  NN_TORCH = 'NN_TORCH',
  CATBOOST = 'CATBOOST',
  XGBOOST = 'XGBOOST',
  KNEIGHBORS = 'KNEIGHBORS',
  EXTRA_TREES = 'EXTRA_TREES',
  IMAGE_DATASET = 'IMAGE_DATASET',
  REGION_PROPERTY = 'REGION_PROPERTY',
  IMAGE_SPATIAL_STATISTICS = 'SPATIAL_STATISTICS',
  ARIMA = 'ARIMA',
  SVM = 'SVM', 
  GPC = 'GPC',
  TEXT_FILE = 'TEXT_FILE',
}

export class WidgetClientTags {
  public PositionX: number = 0;
  public PositionY: number = 0;
  public Width: number = 0;
  public Height: number = 0;
  public Color: string = '';
  public ClientType: WidgetClientType = WidgetClientType.None;
  public widget_number: string | undefined;
}

export class Position {
  public X: number = 50;
  public Y: number = 50;

  constructor(x: number, y: number) {
    this.X = x;
    this.Y = y;
  }
}

export class WorkflowClientTags {
  public StartWidgetPosition: Position | undefined = undefined;
  public EndWidgetPosition: Position | undefined = undefined;
  public Arrows: ArrowObject[] = [];
  public arrowColor: string = 'gray'
}
