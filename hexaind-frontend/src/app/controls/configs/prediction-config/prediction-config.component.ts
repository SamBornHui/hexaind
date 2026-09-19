import { Component, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import {
  DataCopyWidgetConfig,
  EvaluationMetric,
  InputOutputConfig,
  LocalFileConfiguration,
  Widget,
  WorkflowRun,
  PredictionWidgetConfig,
  MOBOWidgetConfig,
  ActiveLearningWidgetConfig,
  ThermoCalcWidgetConfig,
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
import { MatchingModelsDialogComponent } from 'src/app/dialogs/matching-models-dialog/matching-models-dialog.component';
import { PredictionWidgetService } from './services/prediction-widget.service';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import {
  WidgetRunResult,
  DatasetWidgetResult,
} from 'src/app/models/workflow-sessions-api-response.models';

@Component({
  selector: 'app-prediction-config',
  templateUrl: './prediction-config.component.html',
  styleUrls: ['./prediction-config.component.less'],
})
export class PredictionConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  selectedRun: WorkflowRun | undefined = undefined;
  changeMade: boolean = false;
  loopFlag: boolean = false;
  outputChangeMade: boolean = false;
  inputChangeMade: boolean = false;
  changeSetting: boolean = false;
  config: PredictionWidgetConfig | undefined = undefined;
  configCache: PredictionWidgetConfig | undefined = undefined;
  widgetControl: WidgetControl | undefined;
  outputName: string | undefined = undefined;
  inputName: string | undefined = undefined;

  widgetdataInformation = {};
  columnNames: any[] = [];
  selectedInputColumns: string[] = [];
  selectedOutputColumn: string = '';
  moboInputVariables: any[] = [];
  moboOutputVariables: any[] = [];

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
  categoricalDisplayedColumns: string[] = ['name', 'input', 'output'];
  dataSource: any[] = [];
  project_id: string = '';
  site_id: string = '1';
  module_list: any;
  inputWidgets: Widget[] = [];
  inputURN: Widget[] = [];
  inputURNMOBO: Widget[] = [];
  inputURNActiveLearning: Widget[] = [];
  inputURNThermocalc: Widget[] = [];
  widget: any;
  selectedInputWidget: Widget | undefined = undefined;
  numericalDataSource: any[] = [];
  categoricalDataSource: any[] = [];
  convertval: string | number = '';
  ml_id: string = '';
  modelInfo: any;
  show: boolean = false;

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private moboConfigService: MoboConfigService,
    private route: ActivatedRoute,
    private dialog: MatDialog,
    public sharedDataService: SharedDataService,
    public toaster: ToastrService,
    public PredictionWidgetService: PredictionWidgetService,
    private workflowsSessionsApiService: WorkflowsSessionsApiService,
    private configService: ConfigService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.widget = this.widgetControl.Widget as Widget;
    this.config = this.widgetControl.Widget.config as PredictionWidgetConfig;
    this.configCache = JSON.parse(JSON.stringify(this.config));

    if (this.widgetControl.Widget.outputs.length) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
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
        this.checkForMOBOALConfiguration();
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

  loadSavedConfiguration() {
    if (this.configCache) {
      if (this.configCache && this.configCache.ml_id !== undefined) {
        this.ml_id = this.configCache.ml_id;
      }
    }
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  loadFeatures() {
    this.widgetdataInformation = {
      type: this.widgetControl?.Widget.type + ' widget',
      description:
        'The Prediction widget allows supported HEXAIND 3.0 users to perform predictions using a deployed ML model',
      version: this.configCache?.version,
    };
  }

  checkForMOBOALConfiguration() {
    var inputURNMOBOInputs: any[] = [];
    var inputURNActiveLearningInputs: any[] = [];
    var inputURNThermocalOutputs: any[] = [];
    this.inputURNMOBO =
      this.workflowCanvasService.findConnectedByWidgetType('MOBO');
    if (this.inputURNMOBO.length > 0) {
      var moboConfig = this.inputURNMOBO[0].config as MOBOWidgetConfig;
      if (
        moboConfig &&
        moboConfig.input_variables &&
        moboConfig.output_variables
      ) {
        this.loopFlag = true;
        inputURNMOBOInputs = moboConfig.input_variables;
        this.moboOutputVariables = moboConfig.output_variables;
      } else {
        this.loopFlag = false;
      }
    } else {
      this.inputURNActiveLearning =
        this.workflowCanvasService.findConnectedByWidgetType('ACTIVE_LEARNING');
      if (this.inputURNActiveLearning.length > 0) {
        var ALConfig = this.inputURNActiveLearning[0]
          .config as ActiveLearningWidgetConfig;
        if (ALConfig && ALConfig.input_variables && ALConfig.output_variables) {
          this.loopFlag = true;
          inputURNActiveLearningInputs = ALConfig.input_variables;
          this.moboOutputVariables = ALConfig.output_variables;
        } else {
          this.loopFlag = false;
        }
      }
    }
    this.inputURNThermocalc =
      this.workflowCanvasService.findConnectedByWidgetType('THERMOCALC');
    if (this.inputURNThermocalc.length > 0) {
      var TC_Config = this.inputURNThermocalc[0]
        .config as ThermoCalcWidgetConfig;
      if (TC_Config && TC_Config.output_features) {
        inputURNThermocalOutputs = TC_Config.output_features;
      } else {
        this.loopFlag = false;
      }
    }
    var combinedInputs = inputURNMOBOInputs.concat(
      inputURNActiveLearningInputs,
      inputURNThermocalOutputs,
    );
    let uniqueCombinedInputs = combinedInputs.filter((item, index) => {
      return combinedInputs.indexOf(item) === index;
    });

    this.selectedInputColumns = uniqueCombinedInputs;
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
              this.columnNames = originalData[1]
                ? originalData[0].column_names.concat(
                    originalData[1].column_names,
                  )
                : originalData[0].column_names;
              this.selectedInputColumns = this.columnNames;

              if (this.configCache && this.configCache.ml_id) {
                this.getModelInfo(this.configCache.ml_id);
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

  convertScientific(number: number): void {
    if (number) {
      const fractionalPart = number.toString().split('.')[1];
      const fractionalLength = fractionalPart ? fractionalPart.length : 0;
      if (fractionalLength > 3) {
        this.convertval = number.toExponential(3);
      } else {
        this.convertval = number;
      }
    } else {
      this.convertval = number;
    }
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
          const columnObject: any = {
            name: columnName,
            inputChecked: true,
            outputChecked: false,
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

  isColumnSelectedForInput(columnName: string): boolean {
    return this.selectedInputColumns.includes(columnName);
  }

  isColumnSelectedForOutput(columnName: string): boolean {
    return this.selectedOutputColumn === columnName;
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
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

  getModelId() {
    if (!this.configCache) {
      return undefined;
    }
    return this.configCache.ml_id;
  }

  getModelName() {
    if (
      this.modelInfo &&
      'model' in this.modelInfo &&
      this.modelInfo.model.name
    ) {
      return this.modelInfo.model.name;
    } else {
      return '';
    }
  }

  getModelInfo(modelId: string) {
    if (this.configCache && this.configCache.ml_id) {
      this.PredictionWidgetService.getModeleInfo({
        siteId: this.site_id,
        projectId: this.project_id,
        modelId: modelId,
      }).subscribe({
        next: (response) => {
          this.modelInfo = response;

          if (
            this.modelInfo &&
            this.modelInfo.ml_deployed_status &&
            this.modelInfo.ml_deployed_status?.status === 'deployed'
          ) {
            const modelOutputColumns = Array.isArray(
              this.modelInfo.model.configs.output_cols,
            )
              ? this.modelInfo.model.configs.output_cols
              : [this.modelInfo.model.configs.output_col];

            const filteredInputColumns = this.selectedInputColumns.filter(
              (column) => !modelOutputColumns.includes(column),
            );

            const modelInputColumns =
              this.modelInfo.model.configs.input_cols || [];
            const isSubset = modelInputColumns.every((column: any) =>
              filteredInputColumns.includes(column),
            );

            if (!isSubset) {
              this.ml_id = '';
              if (this.configCache) {
                this.configCache.ml_id = '';
              }
              this.modelInfo = null;
            } else {
              this.show = true;
            }
          } else {
            this.ml_id = '';
            if (this.configCache) {
              this.configCache.ml_id = '';
            }
            this.modelInfo = null;
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

  openModelSelectionDialog() {
    const dialogRef = this.dialog.open(MatchingModelsDialogComponent, {
      width: '95vw',
      maxWidth: '95vw',
      height: '95%',
      data: {
        input_cols: this.selectedInputColumns,
        output_cols: this.moboOutputVariables ? this.moboOutputVariables : [],
        flag: this.loopFlag,
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result && result.success) {
        this.configCache!.ml_id = result.model._id;
        this.changeMade = true;
        this.modelInfo = result.model;
        this.show = true;
      }
    });
  }
}
