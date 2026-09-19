import { Component, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import {
  AutoMLWidgetConfig,
  DataCopyWidgetConfig,
  EvaluationMetric,
  InputOutputConfig,
  InputScaling,
  LocalFileConfiguration,
  Widget,
  WorkflowRun,
  ProblemType,
  ClassificationMetrics,
  AutoMLConfigRegression,
  AutoMLConfigClassification,
  WidgetType,
} from 'src/app/models/workflow-models';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { MoboConfigService } from '../mobo-config/mobo-config.service';
import {
  WorkflowCanvasService,
  ConfigService,
} from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { SettingsComponent } from '../settings/settings.component';
import { ToastrService } from 'ngx-toastr';
import { ModelPreviewDialogBoxComponent } from 'src/app/dialogs/model-preview-dialog-box/model-preview-dialog-box.component';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import {
  WidgetRunResult,
  DatasetWidgetResult,
} from 'src/app/models/workflow-sessions-api-response.models';

export interface filterTypeName {
  name: string;
  // Add other properties here as needed
}

@Component({
  selector: 'app-auto-ml-config',
  templateUrl: './auto-ml-config.component.html',
  styleUrls: ['./auto-ml-config.component.less'],
})
export class AutoMlConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  selectedRun: WorkflowRun | undefined = undefined;
  changeMade: boolean = false;
  outputChangeMade: boolean = false;
  inputChangeMade: boolean = false;
  selectedOption: string | undefined;
  changeSetting: boolean = false;
  config: AutoMLWidgetConfig | undefined = undefined;
  configCache: AutoMLWidgetConfig | undefined = undefined;
  widgetControl: WidgetControl | undefined;
  outputName: string | undefined = undefined;
  outputName2: string | undefined = undefined;
  inputName: string | undefined = undefined;
  numberOfTrials = 0;
  isScientificNotationEnabled: boolean = false;

  widgetdataInformation = {};
  columnNames: string[] = [];
  selectedInputColumns: string[] = [];
  selectedOutputColumn: string = '';
  displayedColumns: string[] = [
    'name',
    'input',
    'output',
    'count',
    'mean',
    'std',
    'min',
    'max',
  ];
  numericalDisplayedColumns: string[] = [
    'name',
    'input',
    'output',
    'count',
    'mean',
    'std',
    'min',
    'max',
  ];
  categoricalDisplayedColumns: string[] = [
    'name',
    'input',
    'output',
    'count',
    'unique',
    'top',
    'freq',
    'missing',
  ];
  dataSource: any[] = [];

  selectedInputScalling = InputScaling.Standard;
  selectedEvaluationMetric = EvaluationMetric.root_mean_squared_error;
  selectedClasEvMetric = ClassificationMetrics.Accuracy;
  site_id: string = '1';
  project_id: any;
  module_list: any;
  inputWidgets: Widget[] = [];
  inputURN: Widget[] = [];
  widget: any;
  dataset_id: string | undefined;
  selectedInputWidget: Widget | undefined = undefined;
  selectedDataset: any = {
    features: [],
    features_io_info: [],
    features_meta_data: {},
  };
  selectedProblemType = ProblemType.Regression;
  problemTypes = Object.values(ProblemType).filter(
    (value) => typeof value === 'string',
  );

  classificationMetrics = Object.values(ClassificationMetrics).filter(
    (value) => typeof value === 'string',
  );

  inputScaling = Object.values(InputScaling).filter(
    (value) => typeof value === 'string',
  );

  evaluationMetric = Object.values(EvaluationMetric).filter(
    (value) => typeof value === 'string',
  );
  numericalDataSource: any[] = [];
  categoricalDataSource: any[] = [];
  convertval: string | number = '';
  allInputChecked = true;
  allCatInputChecked = true;
  AutoML_information: any;
  numFeatureSearch: string = '';
  catFeatureSearch: string = '';
  globalFeatureSearch: string = '';

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private moboConfigService: MoboConfigService,
    private route: ActivatedRoute,
    private dialog: MatDialog,
    public sharedDataService: SharedDataService,
    public toaster: ToastrService,
    private http: HttpClient,
    private sanitizer: DomSanitizer,
    private workflowsSessionsApiService: WorkflowsSessionsApiService,
    private configService: ConfigService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.widget = this.widgetControl.Widget as Widget;
    this.config = this.widgetControl.Widget.config as AutoMLWidgetConfig;
    this.config.widget_type = WidgetType.AUTOML;
    this.configCache = JSON.parse(JSON.stringify(this.config));

    if (this.configCache?.problem_type === ProblemType.Classification) {
      this.configCache.automl_config = this.configCache
        .automl_config as AutoMLConfigClassification;
    } else if (this.configCache?.problem_type === ProblemType.Regression) {
      this.configCache.automl_config = this.configCache
        .automl_config as AutoMLConfigRegression;
    }

    if (this.widgetControl.Widget.outputs.length) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
      this.outputName2 = this.widgetControl.Widget.outputs[1]?.name;
    }
    if (this.widgetControl.Widget.inputs.length) {
      this.inputName = this.widgetControl.Widget.inputs[0].name;
    }
  }

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      this.project_id = params['projectId'];
    });

    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.workflowCanvasService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );
      if (this.inputWidgets.length > 0) {
        this.inputURN = this.workflowCanvasService.findConnectedMLWidget(
          this.widgetControl?.Widget.inputs[0]?.urn ?? '',
        );
        if (this.inputURN.length > 0) {
          this.getConnectedWidgetDataset();
        }
      }

      // Remove any widgets that dont have outputs.
      if (this.inputWidgets && this.inputWidgets.length > 0) {
        this.inputWidgets = this.inputWidgets.filter(
          (widget) => widget.outputs.length > 0,
        );
        this.loadSelectedInputWidget();
      }
    }
    this.loadFeatures();
    this.fetchToopTipInformation();
  }

  async getConnectedWidgetDataset() {
    var configuration = this.inputURN[0].config as DataCopyWidgetConfig;
    var source = configuration?.source?.configuration as LocalFileConfiguration;
    var dataset_id = source?.dataset_id;
    if (dataset_id && dataset_id != '') {
      this.getTheFeaturesMetaData(dataset_id);
    } else {
      try {
        let result: WidgetRunResult[] =
          await this.workflowsSessionsApiService.GetWorkflowSessionWidgetRunStatus(
            this.configService.SelectedSiteId,
            this.configService.SelectedProjectId!,
            this.workflowCanvasService.SelectedWorkflowSession?._id!,
            this.inputURN[0].urn!,
          );
        if (result && result.length > 0) {
          let response = result[0];
          let datasetWidgetResult: DatasetWidgetResult =
            response.result_value as DatasetWidgetResult;
          if (result[0]['result_type'] === 'DATASET') {
            var dataset_id = datasetWidgetResult._id;
            this.getTheFeaturesMetaData(dataset_id);
          }
        }
      } catch (error) {
        console.error(error);
      }
    }
  }

  isRegressionType() {
    if (this.configCache) {
      return this.configCache.problem_type === ProblemType.Regression
        ? true
        : false;
    } else {
      return false;
    }
  }
  storeSelectedProblemType(event: any) {
    this.selectedProblemType = event.value;
    if (this.configCache) {
      this.configCache.problem_type = this.selectedProblemType;
      if (this.configCache?.problem_type === ProblemType.Classification) {
        this.configCache.automl_config = new AutoMLConfigClassification();
        this.resetNumericalOutput();
      } else if (this.configCache?.problem_type === ProblemType.Regression) {
        this.configCache.automl_config = new AutoMLConfigRegression();
        this.resetCatInputOutput();
      }
      this.changeMade = true;
    }
  }
  resetCatInputOutput() {
    if (this.categoricalDataSource.length > 0) {
      for (var i = 0; i < this.categoricalDataSource.length; i++) {
        this.categoricalDataSource[i].outputChecked = false;
        this.categoricalDataSource[i].inputChecked = false;
      }
    }
  }
  resetNumericalOutput() {
    if (this.numericalDataSource.length > 0) {
      for (var i = 0; i < this.numericalDataSource.length; i++) {
        this.numericalDataSource[i].outputChecked = false;
      }
    }
  }
  storeSelectedClassMetric(event: any) {
    this.selectedClasEvMetric = event.value as ClassificationMetrics;
    if (this.configCache) {
      let automl_config = this.configCache
        .automl_config as AutoMLConfigClassification;
      automl_config.evaluation_metric_cls = this.selectedClasEvMetric;
      this.configCache.automl_config = automl_config;
      this.changeMade = true;
    }
  }

  isClassificationType() {
    if (this.configCache) {
      return this.configCache.problem_type === ProblemType.Classification
        ? true
        : false;
    } else {
      return false;
    }
  }
  loadSavedConfiguration() {
    if (this.configCache) {
      if (this.configCache && this.configCache.input_cols !== undefined) {
        this.selectedInputColumns = this.configCache.input_cols;
      }

      if (this.configCache && this.configCache.output_col !== undefined) {
        this.selectedOutputColumn = this.configCache.output_col;
      }

      if (this.configCache && this.configCache.problem_type !== undefined) {
        this.selectedProblemType = this.configCache.problem_type;
      }

      if (this.configCache?.problem_type === ProblemType.Classification) {
        let automl_config = this.configCache
          .automl_config as AutoMLConfigClassification;
        this.selectedClasEvMetric =
          automl_config.evaluation_metric_cls as ClassificationMetrics;
      } else if (this.configCache?.problem_type === ProblemType.Regression) {
        let automl_config = this.configCache
          .automl_config as AutoMLConfigRegression;
        this.selectedEvaluationMetric =
          automl_config.evaluation_metric as EvaluationMetric;
      }

      setTimeout(() => {
        this.searchFeaureInputChanged('numerical');
        this.searchFeaureInputChanged('categorical');
      }, 100);
    }
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  loadFeatures() {
    this.widgetdataInformation = {
      type: this.widgetControl?.Widget.type + ' widget',
      description:
        'AutoML widget allows supported HEXAIND 3.0 users to train multiple ML models in one go and rank them in the order of performance.',
      version: this.configCache?.version,
    };
    this.updateSelectAllCheckboxStatus();
  }

  getTheFeaturesMetaData(dataset_id: string | undefined) {
    if (dataset_id !== undefined) {
      this.moboConfigService
        .getDataset(this.site_id, this.project_id, dataset_id)
        .subscribe({
          next: (response) => {
            if (response) {
              var originalData = response.statistics;
              const numericalData = originalData.filter(
                (item: { column_type: string }) =>
                  item.column_type === 'NUMERICAL',
              );
              const categoricalData = originalData.filter(
                (item: { column_type: string }) =>
                  item.column_type === 'CATEGORICAL',
              );

              const transformedNumericalData = this.transformData(
                numericalData,
                false,
              );
              const transformedCategoricalData = this.transformData(
                categoricalData,
                true,
              );

              this.numericalDataSource = transformedNumericalData;
              this.categoricalDataSource = transformedCategoricalData;
              this.updateSelectAllCheckboxStatus();

              if (this.configCache) {
                if (this.configCache.input_cols.length > 0) {
                  let allCols =
                    originalData.length > 1
                      ? originalData[0].column_names.concat(
                          originalData[1].column_names,
                        )
                      : originalData[0].column_names;
                  if (
                    this.checkInputOutputAvailableDataset(
                      allCols,
                      this.configCache.input_cols,
                    )
                  ) {
                    if (this.configCache.output_col != undefined) {
                      this.loadSavedConfiguration();
                    } else {
                      this.setFeaturesInformation(originalData, false);
                    }
                  } else {
                    this.setFeaturesInformation(originalData, true);
                  }
                } else {
                  this.setFeaturesInformation(originalData, false);
                }
              }
            }
          },
          error: (error) => {
            const errorMessage =
              error?.error?.message ||
              error?.message ||
              'An unexpected error occurred';
            this.toaster.error(errorMessage, 'ERROR', {
              positionClass: 'custom-toast-position',
            });
          },
        });
    }
  }
  setFeaturesInformation(originalData: any, changeMode: boolean) {
    if (this.configCache) {
      this.changeMade = changeMode;
      for (var i = 0; i < this.numericalDataSource.length; i++) {
        this.numericalDataSource[i].inputChecked = true;
      }
      for (var i = 0; i < this.categoricalDataSource.length; i++) {
        this.categoricalDataSource[i].inputChecked = true;
      }
      this.columnNames =
        originalData.length > 1
          ? originalData[0].column_names.concat(originalData[1].column_names)
          : originalData[0].column_names;
      this.selectedInputColumns = this.columnNames;
      this.configCache.input_cols = this.selectedInputColumns;
      this.configCache.output_col = '';
      this.selectedOutputColumn = '';

      setTimeout(() => {
        this.searchFeaureInputChanged('numerical');
        this.searchFeaureInputChanged('categorical');
      }, 100);
    }
  }
  checkInputOutputAvailableDataset(newInputs: any, oldInputs: any) {
    if (this.configCache) {
      const allPresent = oldInputs.every((element: any) =>
        newInputs.includes(element),
      );
      if (this.configCache.output_col != undefined) {
        return allPresent && newInputs.includes(this.configCache.output_col)
          ? true
          : false;
      } else {
        return allPresent ? true : false;
      }
    } else {
      return false;
    }
  }
  disabledOutputFeature() {
    return this.configCache?.problem_type === ProblemType.Classification
      ? true
      : false;
  }
  disabledInputOutputFeature() {
    return this.configCache?.problem_type === ProblemType.Regression
      ? true
      : false;
  }
  toggleCheckbox(event: any, elementData: any, type: 'input' | 'output'): void {
    const columnName = elementData.name;
    if (this.configCache?.problem_type === ProblemType.Classification) {
      if (elementData.data_type === 'numerical' && type === 'output') {
        // If it's a numerical feature, prevent selecting it as an output
        this.toaster.info(
          'Numerical features cannot be selected as output',
          'INFO',
          { positionClass: 'custom-toast-position' },
        );
        elementData.outputChecked = false;
        return;
      }
    }

    if (type === 'input' && this.configCache) {
      if (elementData.inputChecked) {
        if (!this.configCache.input_cols.includes(columnName)) {
          this.configCache.input_cols.push(columnName);
        }
        if (this.configCache.output_col === columnName) {
          this.configCache.output_col = ''; // Reset output_col if it matches columnName
        }
        elementData.outputChecked = false;
      } else {
        const inputIndex = this.configCache.input_cols.indexOf(columnName);
        if (inputIndex > -1) {
          this.configCache.input_cols.splice(inputIndex, 1);
        }
      }
      this.searchFeaureInputChanged('numerical');
      this.searchFeaureInputChanged('categorical');
    } else if (type === 'output' && this.configCache) {
      if (elementData.outputChecked) {
        if (this.configCache.output_col !== columnName) {
          this.configCache.output_col = columnName; // Set output_col to columnName
        }
        const inputIndex = this.configCache.input_cols.indexOf(columnName);
        if (inputIndex > -1) {
          this.configCache.input_cols.splice(inputIndex, 1);
        }
        elementData.inputChecked = false;

        if (this.configCache?.problem_type === ProblemType.Regression) {
          for (var i = 0; i < this.numericalDataSource.length; i++) {
            if (this.numericalDataSource[i].name != elementData.name) {
              this.numericalDataSource[i].outputChecked = false;
            }
          }
          for (var i = 0; i < this.categoricalDataSource.length; i++) {
            this.categoricalDataSource[i].outputChecked = false;
          }
        }
        if (this.configCache?.problem_type === ProblemType.Classification) {
          for (var i = 0; i < this.numericalDataSource.length; i++) {
            this.numericalDataSource[i].outputChecked = false;
          }
          for (var i = 0; i < this.categoricalDataSource.length; i++) {
            if (this.categoricalDataSource[i].name != elementData.name) {
              this.categoricalDataSource[i].outputChecked = false;
            }
          }
        }
      } else {
        if (this.configCache.output_col === columnName) {
          this.configCache.output_col = ''; // Reset output_col if it matches columnName
        }
      }
      this.searchFeaureInputChanged('numerical');
      this.searchFeaureInputChanged('categorical');
    }
    this.updateSelectAllCheckboxStatus();
    this.changeMade = true;
  }

  updateSelectAllCheckboxStatus(): void {
    this.allInputChecked = this.numericalDataSource.every(
      (item) => item.inputChecked,
    );
    this.allCatInputChecked = this.categoricalDataSource.every(
      (item) => item.inputChecked,
    );
  }

  transformData(originalData: any[], isCategorical: boolean) {
    const transformedData: {
      name: any;
      inputChecked: boolean | undefined;
      outputChecked: boolean | undefined;
    }[] = [];
    originalData.forEach(
      (dataSet: { column_names: any; row_names: any; data: any }) => {
        const columns = dataSet.column_names;
        const rows = dataSet.row_names;
        const data = dataSet.data;

        columns.forEach((columnName: string, columnIndex: string | number) => {
          if (this.configCache?.output_col === undefined) {
            this.configCache!.input_cols.push(columnName);
          }

          const columnObject: any = {
            name: columnName,
            inputChecked: this.configCache?.input_cols.includes(columnName),
            outputChecked:
              this.configCache?.output_col === columnName ? true : false,
            data_type: isCategorical ? 'categorical' : 'numerical',
          };
          rows.forEach(
            (rowName: string | number, rowIndex: string | number) => {
              columnObject[rowName] = data[columnIndex][rowIndex];
            },
          );
          transformedData.push(columnObject);
        });
      },
    );
    return transformedData;
  }

  getAttachedWidgetData() {
    this.inputURN = this.workflowCanvasService.findConnectedMLWidget(
      this.widgetControl?.Widget.inputs[0]?.urn ?? '',
    );
    if (this.inputURN.length > 0) {
      this.getConnectedWidgetDataset();
    }
  }

  loadSelectedInputWidget() {
    this.selectedInputWidget = undefined;
    if (!this.widgetControl) {
      return;
    }
    if (this.widgetControl.Widget.inputs.length > 0) {
      this.selectedInputWidget = this.inputWidgets.find(
        (t) => t.urn === this.widgetControl?.Widget.inputs[0].urn,
      );
    } else {
      if (this.inputWidgets.length === 1) {
        this.selectedInputWidget = this.inputWidgets[0];
        this.onInputSave();
      }
    }
  }

  onInputChange(columnName: string, event: any) {
    if (event.checked) {
      this.selectedInputColumns.push(columnName);
      if (this.selectedOutputColumn === columnName) {
        this.selectedOutputColumn = '';
      }
    } else {
      const index = this.selectedInputColumns.indexOf(columnName);
      if (index !== -1) {
        this.selectedInputColumns.splice(index, 1);
      }
    }

    if (this.configCache) {
      this.configCache.input_cols = this.selectedInputColumns;
      this.configCache.output_col = this.selectedOutputColumn;
      this.changeMade = true;
    }
  }

  onOutputChange(columnName: string, event: any) {
    if (event.checked) {
      this.selectedOutputColumn = columnName;
      if (this.selectedInputColumns.includes(columnName)) {
        this.selectedInputColumns = this.selectedInputColumns.filter(
          (col) => col !== columnName,
        );
      }
    } else {
      this.selectedOutputColumn = '';
    }

    if (this.configCache) {
      this.configCache.output_col = this.selectedOutputColumn;
      this.configCache.input_cols = this.selectedInputColumns;
      this.changeMade = true;
    }
  }

  isColumnSelectedForInput(columnName: string): boolean {
    return this.selectedInputColumns.includes(columnName);
  }

  isColumnSelectedForOutput(columnName: string): boolean {
    return this.selectedOutputColumn === columnName;
  }

  storeSelectedMetric(event: any) {
    this.selectedEvaluationMetric = event.value as EvaluationMetric;
    if (this.configCache) {
      let automl_config = this.configCache
        .automl_config as AutoMLConfigRegression;
      automl_config.evaluation_metric = this.selectedEvaluationMetric;
      this.configCache.automl_config = automl_config;
      this.changeMade = true;
    }
  }

  onAppSettingsUpdated() {
    this.changeSetting = true;
  }

  getSelectedInputWidget(): Widget | undefined {
    return this.selectedInputWidget;
  }

  setSelectedInputWidget(widget: Widget) {
    this.inputChangeMade = true;
    this.selectedInputWidget = widget;
  }

  getWidgetOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let outputConfig: InputOutputConfig = widget.outputs[0];
      return outputConfig.name!;
    }

    return 'Not Set';
  }

  get widgetOutput(): string | undefined {
    return this.outputName;
  }

  set widgetOutput(value: string | undefined) {
    this.outputName = value;
    this.outputChangeMade = true;
  }
  get widgetOutput2(): string | undefined {
    return this.outputName2;
  }
  set widgetOutput2(value: string | undefined) {
    this.outputName2 = value;
    this.outputChangeMade = true;
  }

  onInputSave() {
    if (this.selectedInputWidget) {
      let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
      inputOutputConfig.name = this.selectedInputWidget.outputs[0].name;
      inputOutputConfig.urn = this.selectedInputWidget.urn;
      if (this.widgetControl) {
        this.widgetControl.Widget.inputs.length = 0;
        this.widgetControl.Widget.inputs.push(inputOutputConfig);
        this.getAttachedWidgetData();
      }

      this.inputChangeMade = false;
    }
  }

  onInputCancel() {
    this.loadSelectedInputWidget();
    this.inputChangeMade = false;
  }

  onOutputSave() {
    if (this.outputName) {
      this.outputName = this.outputName.trim();
      if (
        this.widgetControl &&
        this.widgetControl.Widget.outputs &&
        this.widgetControl.Widget.outputs.length > 0
      ) {
        this.widgetControl.Widget.outputs[0].name = this.outputName;
      }
    }
    if (this.outputName2) {
      this.outputName2 = this.outputName2.trim();
      if (
        this.widgetControl &&
        this.widgetControl.Widget.outputs &&
        this.widgetControl.Widget.outputs.length > 0
      ) {
        this.widgetControl.Widget.outputs[1].name = this.outputName2;
      }
    }
    this.outputChangeMade = false;
  }

  onOutputCancel() {
    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
    }
    this.outputChangeMade = false;
  }

  onSaveSetting() {
    this.settingsComponent.SaveAppSettings();
    this.changeSetting = false;
  }

  onCancelSetting() {
    this.settingsComponent.RevertAppSetting();
    this.changeSetting = false;
  }

  onSave() {
    if (
      this.configCache?.output_col == undefined ||
      this.configCache?.output_col == ''
    ) {
      this.toaster.error('Please select the output feature', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }

    if (this.configCache?.input_cols.length === 0) {
      this.toaster.error('Please select the input features', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }

    if (
      this.configCache?.output_col != undefined ||
      this.configCache?.output_col != ''
    ) {
      if (this.configCache.problem_type === ProblemType.Classification) {
        let existsInCategorical = this.categoricalDataSource.filter(
          (data: any) => data.name == this.configCache?.output_col,
        );
        if (existsInCategorical.length == 0) {
          this.toaster.error('Please select categorical output feature', '', {
            positionClass: 'custom-toast-position',
          });
          return;
        }
      }
    }

    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.settingsComponent.SaveAppSettings();

    if (this.widgetControl && this.configCache) {
      this.widgetControl.Widget.config = this.configCache;
      this.config = this.widgetControl?.Widget.config;
      this.configCache = JSON.parse(JSON.stringify(this.config));
    }
    if (!this.widgetControl) {
      return;
    }
    this.changeMade = false;
  }

  onCancel() {
    // Deep clone to prevent updates from modifying original
    this.configCache = JSON.parse(JSON.stringify(this.config));
    this.changeMade = false;
    this.loadFeatures();
    this.getAttachedWidgetData();
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

  setSplitRatio(event: any) {
    let value = event.target ? +event.target.value : event;
    if (!this.configCache || !this.configCache.split_ratio) {
      return undefined;
    }

    this.configCache.split_ratio = value;
    this.changeMade = true;
  }

  getSplitRatio() {
    if (!this.configCache || !this.configCache!.split_ratio) {
      return undefined;
    }
    return this.configCache.split_ratio;
  }

  setNumberOfTrials(event: any) {
    let value = parseFloat(event.target.value);
    if (
      !this.configCache ||
      !this.configCache.additional_hyperparameter_tune_kwargs
    ) {
      return;
    }

    this.configCache.additional_hyperparameter_tune_kwargs.num_trials = value;
    this.changeMade = true;
  }

  getNumberOfTrials() {
    if (
      !this.configCache ||
      !this.configCache.additional_hyperparameter_tune_kwargs
    ) {
      return undefined;
    }
    return this.configCache.additional_hyperparameter_tune_kwargs.num_trials;
  }

  openModelPreveiwDialog(data: any) {
    const dialogRef = this.dialog.open(ModelPreviewDialogBoxComponent, {
      width: '95vw',
      maxWidth: '95vw',
      height: '95%',
      data: {
        type: 'Regression',
        urn: this.widget.urn,
        selectedPreview: data.view,
      },
    });
    dialogRef.afterClosed().subscribe((result) => {});
  }

  toggleAllCheckbox(event: any) {
    if (this.allInputChecked && this.configCache) {
      if (this.numFeatureSearch == '') {
        for (var i = 0; i < this.numericalDataSource.length; i++) {
          this.numericalDataSource[i].inputChecked = true;
          this.numericalDataSource[i].outputChecked = false;
          let index = this.configCache?.input_cols.findIndex(
            (item: any) => item == this.numericalDataSource[i].name,
          );
          if (index == -1) {
            this.configCache?.input_cols.push(this.numericalDataSource[i].name);
          }
          this.configCache.output_col = '';
        }
      } else {
        let filtereditems = this.numericalDataSource.filter((item: any) => {
          // Ensure the name exists and is a string before searching
          return (
            item.name &&
            item.name
              .toLowerCase()
              .includes(this.numFeatureSearch.toLocaleLowerCase())
          );
        });
        if (filtereditems.length > 0) {
          filtereditems.forEach((feature: any) => {
            let index = this.numericalDataSource.findIndex(
              (item: any) => item.name == feature.name,
            );
            this.numericalDataSource[index].inputChecked = true;
            this.numericalDataSource[index].outputChecked = false;

            let indexCol = this.configCache?.input_cols.findIndex(
              (item: any) => item == feature.name,
            );
            if (indexCol == -1) {
              this.configCache?.input_cols.push(feature.name);
            }

            if (!this.configCache?.input_cols.includes(feature.name)) {
              this.configCache?.input_cols.push(feature.name);
            }

            if (this.configCache?.output_col == feature.name) {
              this.configCache!.output_col = '';
            }
          });
        }
      }
      this.changeMade = true;
    } else {
      if (this.numFeatureSearch == '') {
        for (var i = 0; i < this.numericalDataSource.length; i++) {
          this.numericalDataSource[i].inputChecked = false;
          if (this.configCache) {
            let index = this.configCache.input_cols.indexOf(
              this.numericalDataSource[i].name,
            );
            if (index != -1) {
              this.configCache.input_cols.splice(index, 1);
            }
          }
        }
      } else {
        let filtereditems = this.numericalDataSource.filter((item: any) => {
          // Ensure the name exists and is a string before searching
          return (
            item.name &&
            item.name
              .toLowerCase()
              .includes(this.numFeatureSearch.toLocaleLowerCase())
          );
        });
        if (filtereditems.length > 0) {
          filtereditems.forEach((feature: any) => {
            let index = this.numericalDataSource.findIndex(
              (item: any) => item.name == feature.name,
            );
            this.numericalDataSource[index].inputChecked = false;
            if (this.configCache) {
              let index1 = this.configCache?.input_cols.findIndex(
                (item: any) => item == feature.name,
              );
              if (index1 != -1) {
                this.configCache.input_cols.splice(index1, 1);
              }
            }
          });
        }
      }

      this.changeMade = true;
    }
  }

  onsearchFeaureInput(type: string) {
    if (type == 'numerical' && this.numFeatureSearch != '') {
      this.allInputChecked = false;
    } else {
      this.searchFeaureInputChanged('numerical');
    }

    if (type == 'categorical' && this.catFeatureSearch != '') {
      this.allCatInputChecked = false;
    } else {
      this.searchFeaureInputChanged('categorical');
    }
  }

  searchFeaureInputChanged(type: string) {
    if (type == 'numerical') {
      let numSelected = this.numericalDataSource.filter(
        (item: any) => item.inputChecked,
      );
      let numUnSelected = this.numericalDataSource.filter(
        (item: any) => item.outputChecked,
      );
      // if(this.numericalDataSource.length == (numSelected.length + numUnSelected.length)){
      //   this.allInputChecked = true;
      // }else{
      //   this.allInputChecked = false;
      // }
    }

    if (type == 'categorical') {
      let catSelected = this.categoricalDataSource.filter((item: any) => {
        return item.inputChecked == true;
      });
      let catUnSelected = this.categoricalDataSource.filter((item: any) => {
        return item.outputChecked == true;
      });
    }
  }

  onGlobalSearchInput() {
    this.numFeatureSearch = this.globalFeatureSearch;
    this.catFeatureSearch = this.globalFeatureSearch;
    this.searchFeaureInputChanged('numerical');
    this.searchFeaureInputChanged('categorical');
  }

  toggleAllCheckboxCategorical(event: any) {
    if (this.allCatInputChecked && this.configCache) {
      if (this.catFeatureSearch == '') {
        for (var i = 0; i < this.categoricalDataSource.length; i++) {
          this.categoricalDataSource[i].inputChecked = true;
          this.categoricalDataSource[i].outputChecked = false;
          let index = this.configCache?.input_cols.findIndex(
            (item: any) => item == this.categoricalDataSource[i].name,
          );
          if (index == -1) {
            this.configCache?.input_cols.push(
              this.categoricalDataSource[i].name,
            );
          }
        }
      } else {
        let filtereditems = this.categoricalDataSource.filter((item: any) => {
          // Ensure the name exists and is a string before searching
          return (
            item.name &&
            item.name
              .toLowerCase()
              .includes(this.numFeatureSearch.toLocaleLowerCase())
          );
        });
        if (filtereditems.length > 0) {
          filtereditems.forEach((feature: any) => {
            let index = this.categoricalDataSource.findIndex(
              (item: any) => item.name == feature.name,
            );
            this.categoricalDataSource[index].inputChecked = true;
            this.categoricalDataSource[index].outputChecked = false;

            if (!this.configCache?.input_cols.includes(feature.name)) {
              this.configCache?.input_cols.push(feature.name);
            }

            if (this.configCache?.output_col == feature.name) {
              this.configCache!.output_col = '';
            }
          });
        }
      }
      this.changeMade = true;
    } else {
      if (this.catFeatureSearch == '') {
        for (var i = 0; i < this.categoricalDataSource.length; i++) {
          this.categoricalDataSource[i].inputChecked = false;
          if (this.configCache) {
            let index = this.configCache.input_cols.indexOf(
              this.categoricalDataSource[i].name,
            );
            if (index != -1) {
              this.configCache.input_cols.splice(index, 1);
            }
          }
        }
      } else {
        let filtereditems = this.categoricalDataSource.filter((item: any) => {
          // Ensure the name exists and is a string before searching
          return (
            item.name &&
            item.name
              .toLowerCase()
              .includes(this.numFeatureSearch.toLocaleLowerCase())
          );
        });
        if (filtereditems.length > 0) {
          filtereditems.forEach((feature: any) => {
            let index = this.categoricalDataSource.findIndex(
              (item: any) => item.name == feature.name,
            );
            this.categoricalDataSource[index].inputChecked = false;
            if (this.configCache) {
              let index1 = this.configCache?.input_cols.findIndex(
                (item: any) => item == feature.name,
              );
              if (index1 != -1) {
                this.configCache.input_cols.splice(index1, 1);
              }
            }
          });
        }
      }
    }
    this.updateSelectAllCheckboxStatus();
    this.changeMade = true;
  }
  fetchToopTipInformation(): void {
    this.http
      .get<any>('assets/json-files/' + 'information-tooltip.json')
      .subscribe((data) => {
        this.AutoML_information = data.Auto_ML;
      });
  }
}
