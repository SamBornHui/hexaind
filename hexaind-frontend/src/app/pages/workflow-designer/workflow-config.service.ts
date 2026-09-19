import { Injectable } from '@angular/core';
import {
  BigQueryDatasetConfig,
  BigQueryDatasetConfiguration,
  BigQueryDatasetTableConfig,
  BigQueryDatasetType,
  CustomCodeWidgetConfig,
  CustomFunctionInputOutputTypes,
  CustomFunctionOutputs,
  CustomFunctionInputs,
  DataCopyWidgetConfig,
  FilterConfig,
  FilterOperand,
  FilterOperator,
  FilterType,
  FilterWidgetConfig,
  ModelType,
  OptimizationMethod,
  RandomSearchConfig,
  SaveWidgetConfig,
  ScalingMethod,
  Sink,
  SourceConfiguration,
  SourceType,
  StartNodeWidgetConfig,
  WidgetType,
  LocalFileConfiguration,
  PivotWidgetConfig,
  JoinWidgetConfig,
  AppendWidgetConfig,
  UnionWidgetConfig,
  PythonWidgetConfig,
  RescaleWidgetConfig,
  MOBOWidgetConfig,
  PostRescaleWidgetConfig,
  DecisionWidgetConfig,
  DecisionCriteria,
  Widget,
  WidgetState,
  FeatureEngineeringWidgetConfig,
  FunctionInputs,
  RescaleConnectorConfig,
  LoopStartWidgetConfig,
  LoopEndWidgetConfig,
  TerminationCriteria,
  OnLoopTerminationCriteriaConfig,
  FeatureEngineeringConfig,
  DestinationTypes,
  DatasetConfiguration,
  // MountedDriveDestConfig,
  FileSaveOptions,
  SaveAsConfig,
  ThermoCalcWidgetConfig,
  SaveOptionConfig,
  ActiveLearningWidgetConfig,
  GPRWidgetConfig,
  MPRWidgetConfig,
  AutoMLWidgetConfig,
  LGBMMLWidgetConfig,
  LinearRegressionMLWidgetConfig,
  RandomForestRegressionMLWidgetConfig,
  KNearestNeighborMLWidgetConfig,
  XGBoostMLWidgetConfig,
  CatBoostMLWidgetConfig,
  NeuralNetworkRegressionMLWidgetConfig,
  NnTorchMLWidgetConfig,
  ExtraTreeMLWidgetConfig,
  ARIMAMLWidgetConfig,
  PredictionWidgetConfig,
  SVMWidgetConfig,
  GPCWidgetConfig,
  AutoMLConfigRegression,
  DropColumnsWidgetConfig,
  DropColumnsConfig,
  DropColumnsType,
  DropMissingWidgetConfig,
  DropMissingType,
  DropMissingConfig,
  RenameColumnsWidgetConfig,
  RenameColumnsType,
  RenameColumnsConfig,
  DatatypeConversionType,
  DatatypeConversionWidgetConfig,
  DatatypeConversionConfig,
  JoinType,
  LGBMParameters,
  InputScaling,
  ImageDatasetSelectionWidgetConfig,
  ImageRegionPropertiesWidgetConfig,
  ImageSpatialStatisticsWidgetConfig,
  TextWidgetConfig,
  JupyterWidgetConfig
} from 'src/app/models/workflow-models';

import { WidgetClientType } from './client-tags';

@Injectable({
  providedIn: 'root',
})
export class WorkflowConfigService {
  constructor() { }
  private createDefaultBigQueryConfiguration(): DataCopyWidgetConfig {
    let bigQueryDatasetConfiguration: BigQueryDatasetConfiguration =
      new BigQueryDatasetConfiguration();
    bigQueryDatasetConfiguration.bigquery_connector_id = undefined;
    bigQueryDatasetConfiguration.dataset_configuration =
      new BigQueryDatasetConfig();
    bigQueryDatasetConfiguration.dataset_configuration.project_id = undefined;
    bigQueryDatasetConfiguration.dataset_configuration.dataset_type =
      BigQueryDatasetType.TABLE;
    bigQueryDatasetConfiguration.dataset_configuration.dataset =
      new BigQueryDatasetTableConfig();
    bigQueryDatasetConfiguration.dataset_configuration.dataset.dataset_name =
      undefined;
    bigQueryDatasetConfiguration.dataset_configuration.dataset.table_name =
      undefined;

    let sourceConfiguration: SourceConfiguration = new SourceConfiguration(
      SourceType.BIGQUERY,
      bigQueryDatasetConfiguration,
      WidgetType.DATA_COPY
    );

    let dataCopyWidgetConfig: DataCopyWidgetConfig = new DataCopyWidgetConfig(
      sourceConfiguration,
      WidgetType.DATA_COPY
    );
    dataCopyWidgetConfig.sink = new Sink();
    dataCopyWidgetConfig.sink.dataset_description = undefined;
    dataCopyWidgetConfig.sink.dataset_name = undefined;

    let functionInputs: FunctionInputs = new FunctionInputs();
    functionInputs.input_urn = undefined;
    dataCopyWidgetConfig.inputs.push(functionInputs);

    return dataCopyWidgetConfig;
  }

  private createDefaultCSVConfiguration(): DataCopyWidgetConfig {
    let csvDatasetConfiguration: LocalFileConfiguration =
      new LocalFileConfiguration();
    let sourceConfiguration: SourceConfiguration = new SourceConfiguration(
      SourceType.LOCAL,
      csvDatasetConfiguration,
      WidgetType.DATA_COPY
    );

    let dataCopyWidgetConfig: DataCopyWidgetConfig = new DataCopyWidgetConfig(
      sourceConfiguration,
      WidgetType.DATA_COPY
    );
    dataCopyWidgetConfig.sink = new Sink();
    dataCopyWidgetConfig.sink.dataset_description = undefined;
    dataCopyWidgetConfig.sink.dataset_name = undefined;

    return dataCopyWidgetConfig;
  }

  private createDefaultJUPYTERConfiguration(): JupyterWidgetConfig {
    let jupyterConfiguration: LocalFileConfiguration =
      new LocalFileConfiguration();
    let sourceConfiguration: SourceConfiguration = new SourceConfiguration(
      SourceType.LOCAL,
      jupyterConfiguration,
      WidgetType.JUPYTER
    );

    let jupyterWidgetConfig: JupyterWidgetConfig = new JupyterWidgetConfig(
      WidgetType.JUPYTER
    );

    return jupyterWidgetConfig;
  }

  private createDefaultImageConfiguration(): DataCopyWidgetConfig {
    let csvDatasetConfiguration: LocalFileConfiguration =
      new LocalFileConfiguration();
    csvDatasetConfiguration.dataset_id = '658f621716c58e50bdd3c45c';

    let sourceConfiguration: SourceConfiguration = new SourceConfiguration(
      SourceType.LOCAL,
      csvDatasetConfiguration,
      WidgetType.DATA_COPY
    );

    let dataCopyWidgetConfig: DataCopyWidgetConfig = new DataCopyWidgetConfig(
      sourceConfiguration,
      WidgetType.DATA_COPY
    );
    dataCopyWidgetConfig.sink = new Sink();
    dataCopyWidgetConfig.sink.dataset_description = 'data from image';
    dataCopyWidgetConfig.sink.dataset_name = 'image_dataset';

    return dataCopyWidgetConfig;
  }

  private createDefaultParquetConfiguration(): DataCopyWidgetConfig {
    let csvDatasetConfiguration: LocalFileConfiguration =
      new LocalFileConfiguration();
    csvDatasetConfiguration.dataset_id = '';

    let sourceConfiguration: SourceConfiguration = new SourceConfiguration(
      SourceType.LOCAL,
      csvDatasetConfiguration,
      WidgetType.DATA_COPY
    );

    let dataCopyWidgetConfig: DataCopyWidgetConfig = new DataCopyWidgetConfig(
      sourceConfiguration,
      WidgetType.DATA_COPY
    );
    dataCopyWidgetConfig.sink = new Sink();
    dataCopyWidgetConfig.sink.dataset_description = 'data from parquet';
    dataCopyWidgetConfig.sink.dataset_name = 'parquet_dataset';

    return dataCopyWidgetConfig;
  }

  private createDefaultPDFConfiguration(): DataCopyWidgetConfig {
    let csvDatasetConfiguration: LocalFileConfiguration =
      new LocalFileConfiguration();
    csvDatasetConfiguration.dataset_id = '658f621716c58e50bdd3c45c';

    let sourceConfiguration: SourceConfiguration = new SourceConfiguration(
      SourceType.LOCAL,
      csvDatasetConfiguration,
      WidgetType.DATA_COPY
    );

    let dataCopyWidgetConfig: DataCopyWidgetConfig = new DataCopyWidgetConfig(
      sourceConfiguration,
      WidgetType.DATA_COPY
    );
    dataCopyWidgetConfig.sink = new Sink();
    dataCopyWidgetConfig.sink.dataset_description = 'data from PDF';
    dataCopyWidgetConfig.sink.dataset_name = 'pdf_dataset';

    return dataCopyWidgetConfig;
  }

  private createDefaultLoopStartConfiguration(): LoopStartWidgetConfig {
    let loopStartWidgetConfig: LoopStartWidgetConfig =
      new LoopStartWidgetConfig(WidgetType.LOOP_START);
    return loopStartWidgetConfig;
  }

  private createDefaultLoopEndConfiguration(): LoopEndWidgetConfig {
    let onLoopTerminationCriteriaConfig: OnLoopTerminationCriteriaConfig =
      new OnLoopTerminationCriteriaConfig();
    onLoopTerminationCriteriaConfig.loop_count = 1;

    let loopEndWidgetConfig: LoopEndWidgetConfig = new LoopEndWidgetConfig(
      TerminationCriteria.ON_LOOP_COUNT,
      onLoopTerminationCriteriaConfig,
      WidgetType.LOOP_END
    );

    return loopEndWidgetConfig;
  }

  private createDefaultExcelConfiguration(): DataCopyWidgetConfig {
    let localFileConfiguration: LocalFileConfiguration =
      new LocalFileConfiguration();
    localFileConfiguration.dataset_id = '';

    let sourceConfiguration: SourceConfiguration = new SourceConfiguration(
      SourceType.LOCAL,
      localFileConfiguration,
      WidgetType.DATA_COPY,
    );

    let dataCopyWidgetConfig: DataCopyWidgetConfig = new DataCopyWidgetConfig(
      sourceConfiguration,
      WidgetType.DATA_COPY
    );
    dataCopyWidgetConfig.sink = new Sink();
    dataCopyWidgetConfig.sink.dataset_description = 'data from Excel';
    dataCopyWidgetConfig.sink.dataset_name = 'excel_dataset';

    return dataCopyWidgetConfig;
  }

  public createDefaultFilterConfiguration(): FilterWidgetConfig {
    let filterWidgetConfig: FilterWidgetConfig = new FilterWidgetConfig(
      FilterType.FILTER_BY_COLUMN_VALUES,
      WidgetType.FILTER,
    );
    filterWidgetConfig.config = new FilterConfig();
    return filterWidgetConfig;
  }

  public createDefaultDropColumnsConfiguration(): DropColumnsWidgetConfig {
    let dropColumnsWidgetConfig: DropColumnsWidgetConfig = new DropColumnsWidgetConfig(
      DropColumnsType.DROP_BY_COLUMN_VALUES,
      WidgetType.DROP_COLUMNS,
    );
    dropColumnsWidgetConfig.config = new DropColumnsConfig();
    return dropColumnsWidgetConfig;
  }

  public createDefaultDropMissingConfiguration(): DropMissingWidgetConfig {
    let dropMissingWidgetConfig: DropMissingWidgetConfig = new DropMissingWidgetConfig(
      DropMissingType.DROP_ROW_BY_MISSING_VALUE,
      WidgetType.DROP_MISSING,
    );
    dropMissingWidgetConfig.config = new DropMissingConfig();
    return dropMissingWidgetConfig;
  }

  public createDefaultRenameColumnsConfiguration(): RenameColumnsWidgetConfig {
    let renameColumnsWidgetConfig: RenameColumnsWidgetConfig = new RenameColumnsWidgetConfig(
      RenameColumnsType.RENAME_COLUMN_NAME,
      WidgetType.RENAME_COLUMNS,
    );
    renameColumnsWidgetConfig.config = new RenameColumnsConfig();
    return renameColumnsWidgetConfig;
  }

  public createDefaultDatatypeConversionConfiguration(): DatatypeConversionWidgetConfig {
    let datatypeConversionWidgetConfig: DatatypeConversionWidgetConfig = new DatatypeConversionWidgetConfig(
      DatatypeConversionType.CHANGE_DATATYPE_OF_COLUMNS,
      WidgetType.DATATYPE_CONVERSION,
    );
    datatypeConversionWidgetConfig.config = new DatatypeConversionConfig();
    return datatypeConversionWidgetConfig;
  }

  private createDefaultSaveConfiguration(): SaveWidgetConfig {
    let saveWidgetConfig: SaveWidgetConfig = new SaveWidgetConfig();
    saveWidgetConfig.version = '1.0';
    saveWidgetConfig.widget_type = WidgetType.SAVE;
    return saveWidgetConfig;
  }

  public createNewWidget(
    widgetConfiguration: any,
    widget: any,
    tags: any,
    DefaultWidgetName: any,
    widgetId: string | null = null,
  ): Widget {
    let effectiveWidgetId = widgetId ?? '';
    let defaultWidget: Widget = new Widget(
      DefaultWidgetName,
      'DefaultWidgetDescription',
      widget,
      widgetConfiguration,
      WidgetState.IDLE,
      [],
      [],
      [],
      [],
      [],
      false,
      30,
      30,
      tags,
      effectiveWidgetId,
    );
    return defaultWidget;
  }

  private createDefaultPivotConfiguration(): PivotWidgetConfig {
    let pivotWidgetConfig: PivotWidgetConfig = new PivotWidgetConfig();
    pivotWidgetConfig.widget_type = WidgetType.PIVOT;
    return pivotWidgetConfig;
  }

  private createDefaultJoinConfiguration(): JoinWidgetConfig {
    let joinWidgetConfig: JoinWidgetConfig = new JoinWidgetConfig();
    joinWidgetConfig.left_columns = [];
    joinWidgetConfig.right_columns = [];
    joinWidgetConfig.join_type = JoinType.SELECT
    joinWidgetConfig.widget_type = WidgetType.JOIN;
    return joinWidgetConfig;
  }

  private createDefaultAppendConfiguration(): AppendWidgetConfig {
    let appendWidgetConfig: AppendWidgetConfig = new AppendWidgetConfig();
    appendWidgetConfig.widget_type = WidgetType.APPEND;
    return appendWidgetConfig;
  }

  private createDefaultUnionConfiguration(): UnionWidgetConfig {
    let unionWidgetConfig: UnionWidgetConfig = new UnionWidgetConfig();
    unionWidgetConfig.widget_type = WidgetType.UNION;
    return unionWidgetConfig;
  }

  private createDefaultPythonConfiguration(): PythonWidgetConfig {
    let pythonWidgetConfig: PythonWidgetConfig = new PythonWidgetConfig();
    pythonWidgetConfig.widget_type = WidgetType.PYTHON;
    return pythonWidgetConfig;
  }

  private createDefaultRescaleConfiguration(): RescaleWidgetConfig {
    let rescaleWidgetConfig: RescaleWidgetConfig = new RescaleWidgetConfig();
    rescaleWidgetConfig.rescale_configs = {};
    rescaleWidgetConfig.widget_type = WidgetType.RESCALE;
    return rescaleWidgetConfig;
  }

  private createDefaultPostRescaleConfiguration(): PostRescaleWidgetConfig {
    let postRescaleWidgetConfig: PostRescaleWidgetConfig =
      new PostRescaleWidgetConfig();
    postRescaleWidgetConfig.widget_type = WidgetType.POST_RESCALE;
    return postRescaleWidgetConfig;
  }

  private createDefaultMOBOConfiguration(): MOBOWidgetConfig {
    let moboWidgetConfig: MOBOWidgetConfig = new MOBOWidgetConfig();
    moboWidgetConfig.input_variables = [
      'dcpSpacerThickness',
      'ppSpacerThickness',
      'ipsPressure',
      'upPressure',
      'frictionCf',
    ];
    moboWidgetConfig.input_variables_constraints = [
      [0.18, 0.18001799999999998],
      [0.144, 58],
      [61.75703273, 116.5307904],
      [60, 60.006],
      [0.05, 5],
    ];
    moboWidgetConfig.output_variables = ['bucklingPressure', 'maxThinning'];
    moboWidgetConfig.output_variables_objectives = ['MAXIMUM', 'MINIMUM'];
    moboWidgetConfig.output_variables_thresholds = [111.0, 11.0];
    moboWidgetConfig.num_iterations = 1;
    moboWidgetConfig.initialize_experiment = true;
    moboWidgetConfig.run_iterations = true;
    moboWidgetConfig.experiment_type = 'OPTIMIZATION';
    moboWidgetConfig.batch_size = 2;
    moboWidgetConfig.constraints_module_id = null;
    moboWidgetConfig.outcome_constraints_active = false;
    moboWidgetConfig.outcome_constraints_variable = '';
    moboWidgetConfig.outcome_constraints_operator = '';
    moboWidgetConfig.outcome_constaints_inputvalue = 1;
    moboWidgetConfig.widget_type = WidgetType.MOBO;
    return moboWidgetConfig;
  }

  private createDefaultActiveLearningConfiguration(): ActiveLearningWidgetConfig {
    let ALWidgetConfig: ActiveLearningWidgetConfig =
      new ActiveLearningWidgetConfig();
    ALWidgetConfig.input_variables = [
      'dcpSpacerThickness',
      'ppSpacerThickness',
      'ipsPressure',
      'upPressure',
      'frictionCf',
    ];
    ALWidgetConfig.input_variables_constraints = [
      [0.18, 0.18001799999999998],
      [0.144, 58],
      [61.75703273, 116.5307904],
      [60, 60.006],
      [0.05, 5],
    ];
    ALWidgetConfig.output_variables = ['bucklingPressure', 'maxThinning'];
    ALWidgetConfig.output_variables_objectives = ['MAXIMUM', 'MINIMUM'];
    ALWidgetConfig.output_variables_thresholds = [111.0, 11.0];
    ALWidgetConfig.num_iterations = 1;
    ALWidgetConfig.initialize_experiment = true;
    ALWidgetConfig.run_iterations = true;
    ALWidgetConfig.experiment_type = 'ACTIVE_LEARNING';
    ALWidgetConfig.batch_size = 1;
    ALWidgetConfig.constraints_module_id = '';
    ALWidgetConfig.widget_type = WidgetType.ACTIVE_LEARNING;
    return ALWidgetConfig;
  }

  private createDefaultCustomCodeConfiguration(): CustomCodeWidgetConfig {
    let customCodeWidgetConfig: CustomCodeWidgetConfig =
      new CustomCodeWidgetConfig();
    customCodeWidgetConfig.module_id = '658aeaa79b4341f250e6688a';
    // customCodeWidgetConfig.function_inputs = []
    customCodeWidgetConfig.widget_type = WidgetType.CUSTOM_CODE;
    let customFunctionInputs: CustomFunctionInputs = new CustomFunctionInputs(
      CustomFunctionInputOutputTypes.DATA_FRAME,
      '1',
      'test_df',
    );
    customCodeWidgetConfig.function_inputs.push(customFunctionInputs);

    let customFunctionOutputs: CustomFunctionOutputs =
      new CustomFunctionOutputs(
        CustomFunctionInputOutputTypes.STRING,
        'sql_query',
      );
    customCodeWidgetConfig.function_outputs.push(customFunctionOutputs);

    return customCodeWidgetConfig;
  }

  private createDefaultDecisionConfiguration(): DecisionWidgetConfig {
    let decisionWidgetConfig: DecisionWidgetConfig = new DecisionWidgetConfig();
    decisionWidgetConfig.criteria = new DecisionCriteria();
    decisionWidgetConfig.criteria.field = '';
    decisionWidgetConfig.criteria.operator = '';
    decisionWidgetConfig.criteria.value = '';
    decisionWidgetConfig.widget_type = WidgetType.DECISION;
    return decisionWidgetConfig;
  }

  private createDefaultFeatureEngineeringConfiguration(): FeatureEngineeringWidgetConfig {
    let featureEngineeringWidgetConfig: FeatureEngineeringWidgetConfig =
      new FeatureEngineeringWidgetConfig();
    let functionInputs: FunctionInputs = new FunctionInputs();
    functionInputs.urn = '1';
    functionInputs.name = '';
    featureEngineeringWidgetConfig.inputs.push(functionInputs);
    featureEngineeringWidgetConfig.config = new FeatureEngineeringConfig();
    featureEngineeringWidgetConfig.config.name = 'Feature Engineering';
    featureEngineeringWidgetConfig.config.description =
      'Feature Engineering description';
    featureEngineeringWidgetConfig.widget_type = WidgetType.Feature_Engineering;
    return featureEngineeringWidgetConfig;
  }

  private createDefaultGPRConfiguration(): GPRWidgetConfig {
    let gprWidgetConfig: GPRWidgetConfig = new GPRWidgetConfig();
    gprWidgetConfig.widget_type = WidgetType.GPR;
    return gprWidgetConfig;
  }

  private createDefaultMPRConfiguration(): MPRWidgetConfig {
    let mprWidgetConfig: MPRWidgetConfig = new MPRWidgetConfig();
    mprWidgetConfig.widget_type = WidgetType.MPR;
    return mprWidgetConfig;
  }

  private createDefaultPredictionConfiguration(): PredictionWidgetConfig {
    let predictionWidgetConfig: PredictionWidgetConfig =
      new PredictionWidgetConfig();
    return predictionWidgetConfig;
  }

  private createDefaultSVMConfiguration(): SVMWidgetConfig {
    let svmWidgetConfig: SVMWidgetConfig = new SVMWidgetConfig();
    return svmWidgetConfig;
  }

  private createDefaultAutoMLConfiguration(): AutoMLWidgetConfig {
    let autoMLWidgetConfig: AutoMLWidgetConfig = new AutoMLWidgetConfig();
    autoMLWidgetConfig.automl_config = new AutoMLConfigRegression();
    autoMLWidgetConfig.widget_type = WidgetType.AUTOML;
    return autoMLWidgetConfig;
  }

  private createDefaultLRMLConfiguration(): LinearRegressionMLWidgetConfig {
    let lrMLWidgetConfig: LinearRegressionMLWidgetConfig =
      new LinearRegressionMLWidgetConfig();
    lrMLWidgetConfig.widget_type = WidgetType.LINEAR_REGRESSION;
    return lrMLWidgetConfig;
  }
  private createDefaultLGBMMLConfiguration(): LGBMMLWidgetConfig {
    let lgbmMLWidgetConfig: LGBMMLWidgetConfig = new LGBMMLWidgetConfig();
    lgbmMLWidgetConfig.widget_type = WidgetType.LGBM;
    lgbmMLWidgetConfig.input_scaling = InputScaling.Standard;
    lgbmMLWidgetConfig.lgbm_hyperparameters = {
      GBM: new LGBMParameters(
        OptimizationMethod.GridSearch,
        5,
        42,
        undefined,
        20,
        100,
        4,
        16,
        128,
        4,
        20,
        10,
        4
      )
    };

    return lgbmMLWidgetConfig;
  }
  private createDefaultRandomForestRegressionMLWidgetConfig(): RandomForestRegressionMLWidgetConfig {
    let rfMLWidgetConfig: RandomForestRegressionMLWidgetConfig =
      new RandomForestRegressionMLWidgetConfig();
    rfMLWidgetConfig.widget_type = WidgetType.RF;
    return rfMLWidgetConfig;
  }

  private createDefaultExtreaTreeMLWidgetConfig(): ExtraTreeMLWidgetConfig {
    let etMLWidgetConfig: ExtraTreeMLWidgetConfig =
      new ExtraTreeMLWidgetConfig();
    etMLWidgetConfig.widget_type = WidgetType.EXTRA_TREES;
    return etMLWidgetConfig;
  }
  private createDefaultImageDatasetSelectionConfiguration(): ImageDatasetSelectionWidgetConfig {
    let imageDatasetWidgetConfig: ImageDatasetSelectionWidgetConfig =
      new ImageDatasetSelectionWidgetConfig();
    imageDatasetWidgetConfig.widget_type = WidgetType.IMAGE_DATASET;
    return imageDatasetWidgetConfig;
  }
  private createDefaultImageRegionPropertiesConfiguration(): ImageRegionPropertiesWidgetConfig {
    let imageRegionPropertiesWidgetConfig: ImageRegionPropertiesWidgetConfig =
      new ImageRegionPropertiesWidgetConfig();
    imageRegionPropertiesWidgetConfig.widget_type = WidgetType.REGION_PROPERTY;
    return imageRegionPropertiesWidgetConfig;
  }

  private createDefaultImageSpatialStatisticsConfiguration(): ImageSpatialStatisticsWidgetConfig {
    let imageSpatialStatisticsWidgetConfig: ImageSpatialStatisticsWidgetConfig =
      new ImageSpatialStatisticsWidgetConfig();
    imageSpatialStatisticsWidgetConfig.widget_type = WidgetType.IMAGE_SPATIAL_STATISTICS;
    return imageSpatialStatisticsWidgetConfig;
  }

  private createDefaultKNearestNeighborMLWidgetConfig(): KNearestNeighborMLWidgetConfig {
    let knnMLWidgetConfig: KNearestNeighborMLWidgetConfig =
      new KNearestNeighborMLWidgetConfig();
    knnMLWidgetConfig.widget_type = WidgetType.KNEIGHBORS;
    return knnMLWidgetConfig;
  }

  private createDefaultCatBoostMLWidgetConfig(): CatBoostMLWidgetConfig {
    let catBoostMLWidgetConfig: CatBoostMLWidgetConfig =
      new CatBoostMLWidgetConfig();
    catBoostMLWidgetConfig.widget_type = WidgetType.CATBOOST;
    return catBoostMLWidgetConfig;
  }

  private createDefaultXGBoostMLWidgetConfig(): XGBoostMLWidgetConfig {
    let xgBoostMLWidgetConfig: XGBoostMLWidgetConfig =
      new XGBoostMLWidgetConfig();
    xgBoostMLWidgetConfig.widget_type = WidgetType.XGBOOST;
    return xgBoostMLWidgetConfig;
  }

  private createDefaultGPCConfiguration(): GPCWidgetConfig {
    let gpcWidgetConfig: GPCWidgetConfig = new GPCWidgetConfig();
    return gpcWidgetConfig;
  }

  private createDefaultThermocalcConfiguration(): ThermoCalcWidgetConfig {
    let thermocalcWidgetConfig: ThermoCalcWidgetConfig =
      new ThermoCalcWidgetConfig();
    thermocalcWidgetConfig.widget_type = WidgetType.THERMOCALC;
    return thermocalcWidgetConfig;
  }

  private createDefaultNeuralNetworkRegressionMLWidgetConfig(): NeuralNetworkRegressionMLWidgetConfig {
    let neuralNetworkRegressionMLWidgetConfig: NeuralNetworkRegressionMLWidgetConfig =
      new NeuralNetworkRegressionMLWidgetConfig();
    return neuralNetworkRegressionMLWidgetConfig;
  }

  private createDefaultNNTorchMLWidgetConfig(): NnTorchMLWidgetConfig {
    let nnTorchMLWidgetConfig: NnTorchMLWidgetConfig =
      new NnTorchMLWidgetConfig();
    return nnTorchMLWidgetConfig;
  }

  private createDefaultARIMAMLWidgetConfig(): ARIMAMLWidgetConfig {
    let arimaAMLWidgetConfig: ARIMAMLWidgetConfig = new ARIMAMLWidgetConfig();
    return arimaAMLWidgetConfig;
  }

  private createDefaultTextWidgetConfiguration(): TextWidgetConfig {
    let textWidgetConfig: TextWidgetConfig = new TextWidgetConfig();
    return textWidgetConfig;
  }

  public CreateDefaultConfigurationForWidgetType(
    widgetType: WidgetType,
    widgetClientType: WidgetClientType,
  ): DataCopyWidgetConfig | StartNodeWidgetConfig | FilterWidgetConfig | null {
    switch (widgetType) {
      case WidgetType.DATA_COPY:
        switch (widgetClientType) {
          case WidgetClientType.BigQuery:
            return this.createDefaultBigQueryConfiguration();
          case WidgetClientType.CSVFile:
            return this.createDefaultCSVConfiguration();
          case WidgetClientType.Jupyter:
            return this.createDefaultJUPYTERConfiguration();  
          case WidgetClientType.ImageFile:
            return this.createDefaultImageConfiguration();
          case WidgetClientType.ParquetFile:
            return this.createDefaultParquetConfiguration();
          case WidgetClientType.PDFFile:
            return this.createDefaultPDFConfiguration();
          case WidgetClientType.ExcelFile:
            return this.createDefaultExcelConfiguration();
        }
        break;
      case WidgetType.LOOP_START:
        return this.createDefaultLoopStartConfiguration();
      case WidgetType.LOOP_END:
        return this.createDefaultLoopEndConfiguration();
      case WidgetType.FILTER:
        return this.createDefaultFilterConfiguration();
      case WidgetType.DROP_MISSING:
        return this.createDefaultDropMissingConfiguration();
      case WidgetType.RENAME_COLUMNS:
        return this.createDefaultRenameColumnsConfiguration();
      case WidgetType.SAVE:
        return this.createDefaultSaveConfiguration();
      case WidgetType.PIVOT:
        return this.createDefaultPivotConfiguration();
      case WidgetType.JOIN:
        return this.createDefaultJoinConfiguration();
      case WidgetType.APPEND:
        return this.createDefaultAppendConfiguration();
      case WidgetType.UNION:
        return this.createDefaultUnionConfiguration();
      case WidgetType.PYTHON:
        return this.createDefaultPythonConfiguration();
      case WidgetType.CUSTOM_CODE:
        return this.createDefaultCustomCodeConfiguration();
      case WidgetType.RESCALE:
        return this.createDefaultRescaleConfiguration();
      case WidgetType.POST_RESCALE:
        return this.createDefaultPostRescaleConfiguration();
      case WidgetType.DECISION:
        return this.createDefaultDecisionConfiguration();
      case WidgetType.UX:
        return new StartNodeWidgetConfig();
      case WidgetType.MOBO:
        return this.createDefaultMOBOConfiguration();
      case WidgetType.Feature_Engineering:
        return this.createDefaultFeatureEngineeringConfiguration();
      case WidgetType.THERMOCALC:
        return this.createDefaultThermocalcConfiguration();
      case WidgetType.ACTIVE_LEARNING:
        return this.createDefaultActiveLearningConfiguration();
      case WidgetType.GPR:
        return this.createDefaultGPRConfiguration();
      case WidgetType.MPR:
        return this.createDefaultMPRConfiguration();
      case WidgetType.PREDICTION:
        return this.createDefaultPredictionConfiguration();
      case WidgetType.SVM:
        return this.createDefaultSVMConfiguration();
      case WidgetType.AUTOML:
        return this.createDefaultAutoMLConfiguration();
      case WidgetType.LINEAR_REGRESSION:
        return this.createDefaultLRMLConfiguration();
      case WidgetType.LGBM:
        return this.createDefaultLGBMMLConfiguration();
      case WidgetType.RF:
        return this.createDefaultRandomForestRegressionMLWidgetConfig();
      case WidgetType.XGBOOST:
        return this.createDefaultXGBoostMLWidgetConfig();
      case WidgetType.CATBOOST:
        return this.createDefaultCatBoostMLWidgetConfig();
      case WidgetType.NNFASTAI:
        return this.createDefaultNeuralNetworkRegressionMLWidgetConfig();
      case WidgetType.NN_TORCH:
        return this.createDefaultNNTorchMLWidgetConfig();
      case WidgetType.EXTRA_TREES:
        return this.createDefaultExtreaTreeMLWidgetConfig();
      case WidgetType.KNEIGHBORS:
        return this.createDefaultKNearestNeighborMLWidgetConfig();
      case WidgetType.ARIMA:
        return this.createDefaultARIMAMLWidgetConfig();
      case WidgetType.GPC:
        return this.createDefaultGPCConfiguration();
      case WidgetType.DROP_COLUMNS:
        return this.createDefaultDropColumnsConfiguration();
      case WidgetType.DATATYPE_CONVERSION:
        return this.createDefaultDatatypeConversionConfiguration();
      case WidgetType.IMAGE_DATASET:
        return this.createDefaultImageDatasetSelectionConfiguration();
      case WidgetType.REGION_PROPERTY:
        return this.createDefaultImageRegionPropertiesConfiguration();
      case WidgetType.IMAGE_SPATIAL_STATISTICS:
        return this.createDefaultImageSpatialStatisticsConfiguration();
      case WidgetType.TEXT_DATA:
        return this.createDefaultTextWidgetConfiguration();
    }
    return null;
  }
}
