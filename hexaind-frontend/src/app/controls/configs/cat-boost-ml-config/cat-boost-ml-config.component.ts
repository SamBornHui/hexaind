import { Component, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import {
  CatBoostMLWidgetConfig,
  DataCopyWidgetConfig,
  EvaluationMetric,
  InputOutputConfig,
  InputScaling,
  LocalFileConfiguration,
  ProblemType,
  Widget,
  WidgetType,
  WorkflowRun,
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
import { Utils } from 'src/app/utils';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import {
  WidgetRunResult,
  DatasetWidgetResult,
} from 'src/app/models/workflow-sessions-api-response.models';

@Component({
  selector: 'app-cat-boost-ml-config',
  templateUrl: './cat-boost-ml-config.component.html',
  styleUrls: ['./cat-boost-ml-config.component.less'],
})
export class CatBoostMlConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  selectedRun: WorkflowRun | undefined = undefined;
  changeMade: boolean = false;
  outputChangeMade: boolean = false;
  inputChangeMade: boolean = false;
  selectedOption: string | undefined;
  changeSetting: boolean = false;
  config: CatBoostMLWidgetConfig | undefined = undefined;
  configCache: CatBoostMLWidgetConfig | undefined = undefined;
  widgetControl: WidgetControl | undefined;
  outputName: string | undefined = undefined;
  outputName2: string | undefined = undefined;
  inputName: string | undefined = undefined;
  numberOfTrials = 0;

  widgetdataInformation = {};
  columnNames: string[] = [];
  selectedInputColumns: string[] = [];
  selectedOutputColumn: string = '';
  dataSource: any[] = [];
  evaluationMetric = Object.values(EvaluationMetric).filter(
    (value) => typeof value === 'string',
  );
  selectedEvaluationMetric = EvaluationMetric.root_mean_squared_error;
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

  numericalDataSource: any[] = [];
  categoricalDataSource: any[] = [];
  convertval: string | number = '';

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private moboConfigService: MoboConfigService,
    private route: ActivatedRoute,
    private dialog: MatDialog,
    public sharedDataService: SharedDataService,
    public toaster: ToastrService,
    private workflowsSessionsApiService: WorkflowsSessionsApiService,
    private configService: ConfigService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.widget = this.widgetControl.Widget as Widget;

    this.config = this.widgetControl.Widget.config as CatBoostMLWidgetConfig;
    this.config.widget_type = WidgetType.CATBOOST;
    this.configCache = JSON.parse(JSON.stringify(this.config));

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
      if (this.configCache && this.configCache.input_cols !== undefined) {
        this.selectedInputColumns = this.configCache.input_cols;
      }

      if (this.configCache && this.configCache.output_col !== undefined) {
        this.selectedOutputColumn = this.configCache.output_col;
      }

      if (
        this.configCache &&
        this.configCache.evaluation_metric !== undefined
      ) {
        this.selectedEvaluationMetric = this.configCache.evaluation_metric;
      }
    }
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  loadFeatures() {
    let description: string =
      'CatBoost widget allows supported HEXAIND 3.0 users to train CatBoost Regression models, based on AutoGluon implementation';

    if (this.configCache && this.configCache.problem_type) {
      if (Utils.isRegressionModel(this.configCache)) {
        description =
          'CatBoost widget allows supported HEXAIND 3.0 users to train CatBoost Regression models, based on AutoGluon implementation';
      } else if (Utils.isClassificationModel(this.configCache)) {
        description =
          'CatBoost widget allows supported HEXAIND 3.0 users to train CatBoost Classification models, based on AutoGluon implementation';
      }
    }

    this.widgetdataInformation = {
      type: `${this.widgetControl?.Widget.type} widget`,
      description: description,
      version: this.configCache?.version,
    };
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

  storeSelectedMetric(event: any) {
    this.selectedEvaluationMetric = event.value;
    if (this.configCache) {
      this.configCache.evaluation_metric = this.selectedEvaluationMetric;
      this.configCache.evaluation_metric = this.selectedEvaluationMetric;
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
      this.outputName2 = this.widgetControl.Widget.outputs[1]?.name;
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
}
