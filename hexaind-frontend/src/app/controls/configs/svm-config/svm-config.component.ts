import { Component, ViewChild, OnInit, OnDestroy } from '@angular/core';
import {
  DataCopyWidgetConfig,
  SVMWidgetConfig,
  InputOutputConfig,
  LocalFileConfiguration,
  Widget,
  WidgetType,
} from 'src/app/models/workflow-models';
import { WidgetControl } from '../../widget-control/widget-control';
import { WorkflowCanvasService, ConfigService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ActivatedRoute } from '@angular/router';
import { MoboConfigService } from '../mobo-config/mobo-config.service';
import { MatDialog } from '@angular/material/dialog';
import { SettingsComponent } from '../settings/settings.component';
import { ToastrService } from 'ngx-toastr';
import { ModelPreviewDialogBoxComponent } from 'src/app/dialogs/model-preview-dialog-box/model-preview-dialog-box.component';
import { Utils } from 'src/app/utils';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { WidgetRunResult, DatasetWidgetResult } from 'src/app/models/workflow-sessions-api-response.models';

@Component({
  selector: 'app-svm-config',
  templateUrl: './svm-config.component.html',
  styleUrls: ['./svm-config.component.less'],
})
export class SvmConfigComponent implements OnInit {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;

  dataset_id: string | undefined;
  project_id: any;
  site_id: string = '1';
  dataSource: any[] = [];

  widgetdataInformation = {};
  inputWidgets: Widget[] = [];
  inputURN: Widget[] = [];
  widget: any;

  selectedInputWidget: Widget | undefined = undefined;
  widgetControl: WidgetControl | undefined;
  config: SVMWidgetConfig | undefined = undefined;
  configCache: SVMWidgetConfig | undefined = undefined;

  outputName: string | undefined = undefined;
  outputName2: string | undefined = undefined;
  inputName: string | undefined = undefined;

  changeMade: boolean = false;
  outputChangeMade: boolean = false;
  inputChangeMade: boolean = false;
  changeSetting: boolean = false;

  numericalDataSource: any[] = [];
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
  categoricalDataSource: any[] = [];
  categoricalDisplayedColumns: string[] = [
    'name',
    'input',
    'output',
    'unique',
    'count',
    'top',
    'freq',
    'missing',
  ];

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

  allInputChecked = true;
  allCatInputChecked = true;
  numFeatureSearch: string = '';
  catFeatureSearch: string = '';
  isScientificNotationEnabled: boolean = false;
  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private moboConfigService: MoboConfigService,
    private route: ActivatedRoute,
    private dialog: MatDialog,
    public toaster: ToastrService,
    private workflowsSessionsApiService: WorkflowsSessionsApiService,
    private configService: ConfigService

  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.widget = this.widgetControl.Widget as Widget;
    this.config = this.widgetControl.Widget.config as SVMWidgetConfig;
    this.config.widget_type = WidgetType.SVM;
    let clonedConfig = JSON.parse(JSON.stringify(this.config));
    this.configCache = new SVMWidgetConfig(clonedConfig);
    if (this.widgetControl.Widget.outputs.length) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
      this.outputName2 = this.widgetControl.Widget.outputs[1]?.name;
    }
    if (this.widgetControl.Widget.inputs.length) {
      this.inputName = this.widgetControl.Widget.inputs[0].name;
    }

    this.loadFeatures();
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
        this.inputURN = this.workflowCanvasService.findConnectedWidgets(
          this.widgetControl?.Widget.outputs[0]?.urn ?? '',
        );
        if (this.inputURN.length > 0) {
          this.getConnectedWidgetDataset()
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
          let response = result[0]
          let datasetWidgetResult: DatasetWidgetResult = response.result_value as DatasetWidgetResult;
          if (result[0]['result_type'] === 'DATASET') {
            var dataset_id = datasetWidgetResult._id;
            this.getTheFeaturesMetaData(dataset_id);
          }
        }
      } catch (error) {
        console.error(error)
      }
    }
  }

  loadFeatures() {
    let description: string =
      'The purpose of the SVM widget is to allow users to build a support vector machine (SVM) for regression tasks';

    if (this.configCache && this.configCache.problem_type) {
      if (Utils.isRegressionModel(this.configCache)) {
        description =
          'The purpose of the SVM widget is to allow users to build a support vector machine (SVM) for regression tasks';
      } else if (Utils.isClassificationModel(this.configCache)) {
        description =
          'The purpose of the SVM widget is to allow users to build a support vector machine (SVM) for classification tasks';
      }
    }

    this.widgetdataInformation = {
      type: `${this.widgetControl?.Widget.type} widget`,
      description: description,
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
              const originalData = response.statistics;
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
                'NUMERICAL',
              );
              const transformedCategoricalData = this.transformData(
                categoricalData,
                'CATEGORICAL',
              );

              this.numericalDataSource = transformedNumericalData;
              this.categoricalDataSource = transformedCategoricalData;
              this.updateSelectAllCheckboxStatus();

              if (this.configCache) {
                if (this.configCache.input_cols.length > 0) {
                  let allCols = (originalData.length > 1) ? originalData[0].column_names.concat(originalData[1].column_names) : originalData[0].column_names;
                  if (this.checkInputOutputAvailableDataset(allCols, this.configCache.input_cols)) {
                    if (this.configCache.output_cols.length == 0) {
                      this.setFeaturesInformation(originalData, false)
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
            this.toaster.error(
              'An error occurred while fetching the dataset',
              'ERROR',
              {
                positionClass: 'custom-toast-position',
              },
            );
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
      this.configCache.input_cols = (originalData.length > 1) ? originalData[0].column_names.concat(originalData[1].column_names) : originalData[0].column_names;
      this.configCache.output_cols = [];
    }
  }

  checkInputOutputAvailableDataset(newInputs: any, oldInputs: any) {
    if (this.configCache) {
      const allPresent = oldInputs.every((element: any) => newInputs.includes(element));
      if (this.configCache.output_cols.length > 0) {
        const allPresentOut = this.configCache.output_cols.every((element: any) => newInputs.includes(element));
        return (allPresent && allPresentOut) ? true : false;
      } else {
        return (allPresent) ? true : false;
      }

    } else {
      return false;
    }
  }


  transformData(originalData: any, columnType: string) {
    const transformedData: any[] = [];

    originalData.forEach((stat: any) => {
      const columns = stat.column_names;
      const rows = stat.row_names;
      const data = stat.data;

      columns.forEach((columnName: string, columnIndex: number) => {
        if (this.configCache?.output_cols.length === 0) {
          this.configCache.input_cols.push(columnName);
        }

        const columnObject: any = {
          name: columnName,
          type: columnType,
          inputChecked: this.configCache?.input_cols.includes(columnName),
          outputChecked: this.configCache?.output_cols.includes(columnName),
        };

        rows.forEach((rowName: string, rowIndex: number) => {
          columnObject[rowName] = data[columnIndex][rowIndex];
        });

        transformedData.push(columnObject);
      });
    });

    return transformedData;
  }

  toggleCheckbox(elementData: any, type: 'input' | 'output'): void {
    const columnName = elementData.name;

    if (type === 'input' && this.configCache) {
      if (elementData.inputChecked) {
        if (!this.configCache.input_cols.includes(columnName)) {
          this.configCache.input_cols.push(columnName);
        }
        const outputIndex = this.configCache.output_cols.indexOf(columnName);
        if (outputIndex > -1) {
          this.configCache.output_cols.splice(outputIndex, 1);
        }
        elementData.outputChecked = false;
      } else {
        const inputIndex = this.configCache.input_cols.indexOf(columnName);
        if (inputIndex > -1) {
          this.configCache.input_cols.splice(inputIndex, 1);
        }
      }
    } else if (type === 'output' && this.configCache) {
      if (elementData.outputChecked) {
        if (!this.configCache.output_cols.includes(columnName)) {
          this.configCache.output_cols.push(columnName);
        }
        const inputIndex = this.configCache.input_cols.indexOf(columnName);
        if (inputIndex > -1) {
          this.configCache.input_cols.splice(inputIndex, 1);
        }
        elementData.inputChecked = false;
      } else {
        const outputIndex = this.configCache.output_cols.indexOf(columnName);
        if (outputIndex > -1) {
          this.configCache.output_cols.splice(outputIndex, 1);
        }
      }
    }
    this.updateSelectAllCheckboxStatus();
    this.changeMade = true;
  }

  updateSelectAllCheckboxStatus(): void {
    this.allInputChecked = this.numericalDataSource.every((item) => item.inputChecked);
    this.allCatInputChecked = this.categoricalDataSource.every((item) => item.inputChecked);
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
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

  onInputCancel() {
    this.loadSelectedInputWidget();
    this.inputChangeMade = false;
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

  getAttachedWidgetData() {
    this.inputURN = this.workflowCanvasService.findConnectedWidgets(
      this.widgetControl?.Widget.inputs[0]?.urn ?? '',
    );
    if (this.inputURN.length > 0) {
      this.getConnectedWidgetDataset()
    }
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

  onOutputCancel() {
    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
      this.outputName2 = this.widgetControl.Widget.outputs[1]?.name;
    }
    this.outputChangeMade = false;
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

  onAppSettingsUpdated() {
    this.changeSetting = true;
  }

  onCancelSetting() {
    this.settingsComponent.RevertAppSetting();
    this.changeSetting = false;
  }
  onSaveSetting() {
    this.settingsComponent.SaveAppSettings();
    this.changeSetting = false;
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

  onCancel() {
    let clonedConfig = JSON.parse(JSON.stringify(this.config));
    this.configCache = new SVMWidgetConfig(clonedConfig);
    this.changeMade = false;
    this.loadFeatures();
    this.getAttachedWidgetData();
  }

  onSave() {
    if (!this.configCache) {
      return;
    }
    if (
      this.configCache.output_cols === undefined ||
      this.configCache.output_cols.length === 0
    ) {
      this.toaster.error('Please select the output feature', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }
    if (this.configCache.input_cols.length === 0) {
      this.toaster.error('Please select the input features', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }
    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.settingsComponent.SaveAppSettings();
    if (this.widgetControl) {
      this.widgetControl.Widget.config = this.configCache;
      this.config = this.widgetControl.Widget.config;
      let clonedConfig = JSON.parse(JSON.stringify(this.config));
      this.configCache = new SVMWidgetConfig(clonedConfig);
      this.changeMade = false;
    } else {
      console.error('Widget control is not available');
      return;
    }
  }

  openModelPreveiwDialog(data: any) {
    const dialogRef = this.dialog.open(ModelPreviewDialogBoxComponent, {
      width: '95vw',
      maxWidth: '95vw',
      height: '95%',
      data: {
        type: 'Regression',
        urn: this.widget.urn,
        selectedPreview: data.view
      },
    });
    dialogRef.afterClosed().subscribe((result) => { });
  }

  onProblemTypeChange(newProblemType: 'regression' | 'classification'): void {
    if (!this.configCache) {
      return;
    }
    this.loadFeatures();
    this.configCache.toggleProblemType(newProblemType);

    this.configCache.output_cols = [];

    this.numericalDataSource.forEach((item: any) => {
      if (item.outputChecked) {
        item.outputChecked = false;
      }
      item.inputChecked = true;
      if (
        this.configCache &&
        !this.configCache.input_cols.includes(item.name)
      ) {
        this.configCache.input_cols.push(item.name);
      }
    });

    this.categoricalDataSource.forEach((item: any) => {
      if (item.outputChecked) {
        item.outputChecked = false;
      }
      item.inputChecked = true;
      if (
        this.configCache &&
        !this.configCache.input_cols.includes(item.name)
      ) {
        this.configCache.input_cols.push(item.name);
      }
    });
    this.changeMade = true;
  }

  ontoggleSamplingChange(samplingType: any) {
    if (!this.configCache) {
      return;
    }
    this.configCache.toggleSampling(samplingType);
    this.changeMade = true;
  }

  onKernelChange(newKernel: 'rbf' | 'poly' | 'linear' | 'sigmoid'): void {
    if (!this.configCache) {
      return;
    }
    this.configCache.setDefaults(newKernel);
    this.changeMade = true;
  }

  categoricalOutputColumn(): boolean {
    if (this.configCache && this.configCache.output_cols) {
      return (
        this.configCache.output_cols.length > 0 ||
        this.configCache.problem_type === 'regression'
      );
    }
    return false;
  }

  inputChange() {
    this.changeMade = true;
  }


  toggleAllCheckbox(event: any) {
    if (this.allInputChecked && this.configCache) {
      for (let i = 0; i < this.numericalDataSource.length; i++) {
        this.numericalDataSource[i].inputChecked = true;
        this.numericalDataSource[i].outputChecked = false;
        if (!this.configCache.input_cols.includes(this.numericalDataSource[i].name)) {
          this.configCache.input_cols.push(this.numericalDataSource[i].name);
          if (this.configCache.problem_type === 'regression' && this.configCache.output_cols.includes(this.numericalDataSource[i].name)) {
            this.configCache.output_cols.splice(this.configCache.output_cols.indexOf(this.numericalDataSource[i].name), 1);
          }
        }
      }
    } else {
      for (let i = 0; i < this.numericalDataSource.length; i++) {
        this.numericalDataSource[i].inputChecked = false;
      }

      if (this.configCache) {
        this.configCache.input_cols = [];

        this.categoricalDataSource.forEach((item: any) => {
          if (!this.configCache?.input_cols.includes(item.name)) {
            this.configCache?.input_cols.push(item.name);
          }
        });
      }
    }
    this.changeMade = true;
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
      let numSelected = this.numericalDataSource.filter((item: any) => item.inputChecked);
      let numUnSelected = this.numericalDataSource.filter((item: any) => item.outputChecked);
      if (this.numericalDataSource.length == (numSelected.length + numUnSelected.length)) {
        this.allInputChecked = true;
      } else {
        this.allInputChecked = false;
      }
    }

    if (type == 'categorical') {
      let catSelected = this.categoricalDataSource.filter((item: any) => {
        return item.inputChecked == true;
      });
      let catUnSelected = this.categoricalDataSource.filter((item: any) => {
        return item.outputChecked == true;
      });

      if (this.categoricalDataSource.length == (catSelected.length + catUnSelected.length)) {
        this.allCatInputChecked = true;
      } else {
        this.allCatInputChecked = false;
      }
    }
  }

  getOutputLength() {
    return this.configCache?.output_cols ? this.configCache?.output_cols.length : 0;
  }

  toggleAllCheckboxCategorical(event: any) {
    if (this.allCatInputChecked && this.configCache) {
      if (this.catFeatureSearch == '') {
        for (var i = 0; i < this.categoricalDataSource.length; i++) {
          this.categoricalDataSource[i].inputChecked = true;
          this.categoricalDataSource[i].outputChecked = false;
          let index = this.configCache?.input_cols.findIndex((item: any) => item == this.categoricalDataSource[i].name);
          if (index == -1) {
            this.configCache?.input_cols.push(this.categoricalDataSource[i].name);
            const outputIndex = this.configCache?.output_cols?.indexOf(this.categoricalDataSource[i].name);
            if (outputIndex > -1) {
              this.configCache.output_cols.splice(outputIndex, 1);
            }
          }
        }
      } else {
        let filtereditems = this.categoricalDataSource.filter((item: any) => {
          return item.name && item.name.toLowerCase().includes(this.numFeatureSearch.toLocaleLowerCase());
        });
        if (filtereditems.length > 0) {
          filtereditems.forEach((feature: any) => {
            let index = this.categoricalDataSource.findIndex((item: any) => item.name == feature.name);
            this.categoricalDataSource[index].inputChecked = true;
            this.categoricalDataSource[index].outputChecked = false;

            if (!this.configCache?.input_cols.includes(feature.name)) {
              this.configCache?.input_cols.push(feature.name);
            }

            if (this.configCache?.input_cols.includes(feature.name)) {
              const index = this.configCache.input_cols.indexOf(feature.name);
              if (index > -1) {
                this.configCache.input_cols.splice(index, 1);
              }
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
            let index = this.configCache.input_cols.indexOf(this.categoricalDataSource[i].name);
            if (index != -1) {
              this.configCache.input_cols.splice(index, 1);
            }
          }
        }
      } else {
        let filtereditems = this.categoricalDataSource.filter((item: any) => {
          return item.name && item.name.toLowerCase().includes(this.numFeatureSearch.toLocaleLowerCase());
        });
        if (filtereditems.length > 0) {
          filtereditems.forEach((feature: any) => {
            let index = this.categoricalDataSource.findIndex((item: any) => item.name == feature.name);
            this.categoricalDataSource[index].inputChecked = false;
            if (this.configCache) {
              let index1 = this.configCache?.input_cols.findIndex((item: any) => item == feature.name);
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
}
