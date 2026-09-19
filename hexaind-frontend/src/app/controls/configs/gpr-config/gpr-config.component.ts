import {
  Component,
  ViewChild,
  OnInit,
  OnDestroy,
  ChangeDetectorRef,
} from '@angular/core';
import {
  DataCopyWidgetConfig,
  GPRWidgetConfig,
  InputOutputConfig,
  LocalFileConfiguration,
  Widget,
  WidgetType,
} from 'src/app/models/workflow-models';
import { WidgetControl } from '../../widget-control/widget-control';
import {
  WorkflowCanvasService,
  ConfigService,
} from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ActivatedRoute } from '@angular/router';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { MoboConfigService } from '../mobo-config/mobo-config.service';
import { MatDialog } from '@angular/material/dialog';
import { SettingsComponent } from '../settings/settings.component';
import { ToastrService } from 'ngx-toastr';
import { ModelPreviewDialogBoxComponent } from 'src/app/dialogs/model-preview-dialog-box/model-preview-dialog-box.component';
import { Utils } from 'src/app/utils';
import { GPR } from '../../../../assets/json-files/information-tooltip.json';
import { HttpClient } from '@angular/common/http';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import {
  WidgetRunResult,
  DatasetWidgetResult,
} from 'src/app/models/workflow-sessions-api-response.models';

@Component({
  selector: 'app-gpr-config',
  templateUrl: './gpr-config.component.html',
  styleUrls: ['./gpr-config.component.less'],
})
export class GprConfigComponent implements OnInit, OnDestroy {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;

  changeMade: boolean = false;
  outputChangeMade: boolean = false;
  inputChangeMade: boolean = false;

  changeSetting: boolean = false;
  config: GPRWidgetConfig | undefined = undefined;
  configCache: GPRWidgetConfig | undefined = undefined;
  widgetControl: WidgetControl | undefined;
  outputName: string | undefined = undefined;
  outputName2: string | undefined = undefined;
  inputName: string | undefined = undefined;

  widgetdataInformation = {};
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

  selectedMean: string = '';
  dataSource: any[] = [];
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

  private kernelNames: string[] = [
    'RBF',
    'ARD RBF',
    'Matern',
    'ARD Matern',
    'Linear',
  ];

  numLatents: number | null = null;
  numInducing: number | null = null;
  numMixture: number | null = null;
  dataSetRows!: number;
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
  GPR_information: any;
  endRangeOfInducingPoints: number = 0;

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
    public sharedDataService: SharedDataService,
    public toaster: ToastrService,
    private http: HttpClient,
    private workflowsSessionsApiService: WorkflowsSessionsApiService,
    private configService: ConfigService,
    private cdr: ChangeDetectorRef,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.widget = this.widgetControl.Widget as Widget;
    this.config = this.widgetControl.Widget.config as GPRWidgetConfig;
    this.config.widget_type = WidgetType.GPR;
    this.configCache = JSON.parse(JSON.stringify(this.config));

    if (this.widgetControl.Widget.outputs.length) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
      this.outputName2 = this.widgetControl.Widget.outputs[1]?.name;
    }
    if (this.widgetControl.Widget.inputs.length) {
      this.inputName = this.widgetControl.Widget.inputs[0].name;
    }
  }
  ngOnDestroy(): void {}

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

  fetchToopTipInformation(): void {
    this.http
      .get<any>('assets/json-files/' + 'information-tooltip.json')
      .subscribe((data) => {
        this.GPR_information = data.GPR;
      });
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  loadFeatures() {
    let description: string =
      'GPR widget allows supported HEXAIND 3.0 users to train GPR models based on a GPyTorch implementation for regression tasks';

    if (this.configCache && this.configCache.problem_type) {
      if (Utils.isRegressionModel(this.configCache)) {
        description =
          'GPR widget allows supported HEXAIND 3.0 users to train GPR models based on a GPyTorch implementation for regression tasks';
      } else if (Utils.isClassificationModel(this.configCache)) {
        description =
          'GPR widget allows supported HEXAIND 3.0 users to train GPR models based on a GPyTorch implementation for classification tasks';
      }
    }

    var kernals_information = [
      {
        name: 'Linear kernel',
        image: 'assets/Linear kernel.png',
        description: '',
      },
    ];

    this.widgetdataInformation = {
      type: `${this.widgetControl?.Widget.type} widget`,
      description: description,
      version: this.configCache?.version,
      kernals_information: kernals_information,
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
                    if (this.configCache.output_cols.length == 0) {
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
      this.configCache.input_cols =
        originalData.length > 1
          ? originalData[0].column_names.concat(originalData[1].column_names)
          : originalData[0].column_names;
      this.configCache.output_cols = [];
    }
  }

  checkInputOutputAvailableDataset(newInputs: any, oldInputs: any) {
    if (this.configCache) {
      const allPresent = oldInputs.every((element: any) =>
        newInputs.includes(element),
      );
      if (this.configCache.output_cols.length > 0) {
        const allPresentOut = this.configCache.output_cols.every(
          (element: any) => newInputs.includes(element),
        );
        return allPresent && allPresentOut ? true : false;
      } else {
        return allPresent ? true : false;
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

  toggleCheckbox(elementData: any, type: string): void {
    const columnName = elementData.name;
    if (type === 'input' && this.configCache) {
      if (elementData.inputChecked) {
        const outputIndex = this.configCache.output_cols.indexOf(columnName);
        if (outputIndex > -1) {
          this.configCache.output_cols.splice(outputIndex, 1);
          elementData.outputChecked = false;
        }

        if (!this.configCache.input_cols.includes(columnName)) {
          this.configCache.input_cols.push(columnName);
        }
      } else {
        if (this.configCache.input_cols.indexOf(columnName) != -1) {
          this.configCache.input_cols.splice(
            this.configCache.input_cols.indexOf(columnName),
            1,
          );
        }
      }
    } else if (type === 'output' && this.configCache) {
      elementData.inputChecked = false;
      const inputIndex = this.configCache.input_cols.indexOf(columnName);
      if (inputIndex > -1) {
        this.configCache.input_cols.splice(inputIndex, 1);
      }

      if (elementData.outputChecked) {
        this.configCache.output_cols.push(columnName);
      } else {
        this.configCache.output_cols.splice(
          this.configCache.output_cols.indexOf(columnName),
          1,
        );
      }
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
      this.configCache?.output_cols == undefined ||
      this.configCache?.output_cols.length == 0
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
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.widget = this.widgetControl?.Widget as Widget;
    this.config = this.widgetControl?.Widget.config as GPRWidgetConfig;
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

  storeSelectedMean(event: any) {
    this.selectedMean = event.value;
    if (this.configCache) {
      this.configCache.mean = this.selectedMean;
      this.changeMade = true;
    }
  }

  toggleSpectralKernel(checked: boolean): void {
    if (this.configCache) {
      if (checked) {
        this.configCache.kernel_selected.fill(false);
        this.configCache.spectral_kernel = {
          spectral_selected: true,
          num_mixtures: 7,
        };
      } else {
        this.configCache.spectral_kernel = false;
      }
    }
  }

  updateKernelSelection(index: number, isChecked: boolean): void {
    if (this.configCache) {
      this.changeMade = true;
      this.configCache.kernel_selected[index] = isChecked;
      if (isChecked) {
        this.configCache.spectral_kernel = false;
      }
    }
    this.updateSpectralKernel();
  }

  updateSpectralKernel() {
    if (this.configCache) {
      if (this.configCache.kernel_selected.every((value) => value == false)) {
        const numMixtures =
          this.configCache.spectral_kernel &&
          typeof this.configCache.spectral_kernel === 'object'
            ? this.configCache.spectral_kernel.num_mixtures || 7
            : 7;
        this.configCache.spectral_kernel = {
          spectral_selected: true,
          num_mixtures: numMixtures,
        };
      } else {
        this.configCache.spectral_kernel = false;
      }
    }
  }

  trackByFn(index: any, item: any) {
    return index;
  }

  handleSpectralKernelChange(checked: boolean) {
    if (checked && this.configCache) {
      this.configCache.kernel_selected.fill(false);
    }
  }

  handleKernelSelectedChange(index: number, checked: boolean) {
    if (checked && this.configCache) {
      this.configCache.spectral_kernel = false;
    }
  }

  getKernelName(index: number): string {
    return this.kernelNames[index] || 'Unknown';
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
      for (let i = 0; i < this.numericalDataSource.length; i++) {
        this.numericalDataSource[i].inputChecked = true;
        this.numericalDataSource[i].outputChecked = false;
        if (
          !this.configCache.input_cols.includes(
            this.numericalDataSource[i].name,
          )
        ) {
          this.configCache.input_cols.push(this.numericalDataSource[i].name);
          if (
            this.configCache.problem_type === 'regression' &&
            this.configCache.output_cols.includes(
              this.numericalDataSource[i].name,
            )
          ) {
            this.configCache.output_cols.splice(
              this.configCache.output_cols.indexOf(
                this.numericalDataSource[i].name,
              ),
              1,
            );
          }
        }
      }
    } else {
      for (let i = 0; i < this.numericalDataSource.length; i++) {
        this.numericalDataSource[i].inputChecked = false;
        const index: any = this.configCache?.input_cols.indexOf(
          this.numericalDataSource[i].name,
        );
        if (index > -1) {
          this.configCache?.input_cols.splice(index, 1);
        }
      }
    }
    this.changeMade = true;
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
    if (!this.configCache || !this.configCache.split_ratio) {
      return undefined;
    }
    return this.configCache.split_ratio;
  }

  getNumberOfLatents() {
    if (!this.configCache || !this.configCache.variational) {
      return undefined;
    }
    return this.configCache.variational.num_latents;
  }

  setNumberOfLatents(event: any): void {
    if (this.configCache && this.configCache.variational) {
      let value: number;

      if (event.value !== undefined) {
        value = +event.value;
      } else if (event.target && event.target.value !== undefined) {
        value = +event.target.value;
      } else {
        return;
      }

      const min = this.startRangeForLatentGps();
      const max = this.endRangeForLatentGps();

      value = Math.max(min, Math.min(max, value));

      this.configCache.variational.num_latents = Math.round(value);

      this.changeMade = true;
      this.cdr.detectChanges();
    }
  }

  setNumOfInducing(event: any) {
    let value = event.target ? +event.target.value : event;
    if (!this.configCache || !this.configCache.variational) {
      return undefined;
    }

    this.configCache.variational.num_inducing = value;
    this.changeMade = true;
  }

  getNumOfInducing() {
    if (!this.configCache || !this.configCache.variational) {
      return undefined;
    }
    return this.configCache.variational.num_inducing;
  }

  get getNumberOfInducingPoints() {
    if (!this.configCache || !this.configCache.variational) {
      return undefined;
    }
    return this.configCache.variational.num_inducing;
  }

  setNumberOfInducingPoints(event: any): void {
    if (this.configCache && this.configCache.variational) {
      let value: number;

      if (event.value !== undefined) {
        value = +event.value;
      } else if (event.target && event.target.value !== undefined) {
        value = +event.target.value;
      } else {
        return;
      }

      const min = this.startRangeForInducingpoints();
      const max = this.endRangeForInducingpoints;

      value = Math.max(min, Math.min(max, value));

      this.configCache.variational.num_inducing = Math.round(value);
      this.changeMade = true;
      this.cdr.detectChanges();
    }
  }

  setNumerOfMixtures(event: any) {
    let value = event.target ? +event.target.value : event;
    if (!this.configCache || !this.configCache.spectral_kernel) {
      return undefined;
    }

    this.configCache.spectral_kernel.num_mixtures = value;
    this.changeMade = true;
  }

  getNumerOfMixtures() {
    if (!this.configCache || !this.configCache.spectral_kernel) {
      return undefined;
    }
    return this.configCache.spectral_kernel.num_mixtures;
  }

  startRangeForLatentGps(): number {
    const outputFeatureSelected = this.categoricalDataSource.filter(
      (item) => item.outputChecked === true,
    );
    const num_latents =
      outputFeatureSelected.length > 0
        ? outputFeatureSelected[0]?.unique * 0.5
        : 4;
    if (this.configCache?.variational) {
      this.configCache.variational.num_latents = num_latents;
    }

    return num_latents;
  }

  get endRangeForInducingpoints(): number {
    const outputFeatureSelected = this.categoricalDataSource.filter(
      (item) => item.name === this.configCache?.output_cols[0],
    );
    this.endRangeOfInducingPoints = Math.round(outputFeatureSelected[0]?.count);

    return outputFeatureSelected.length > 0
      ? outputFeatureSelected[0]?.count
      : 3000;
  }

  endRangeForLatentGps(): number {
    const outputFeatureSeleted = this.categoricalDataSource.filter(
      (item) => item.outputChecked === true,
    );
    this.endRangeOfInducingPoints = outputFeatureSeleted[0]?.count;
    return outputFeatureSeleted.length > 0
      ? outputFeatureSeleted[0]?.unique * 3
      : 100;
  }

  startRangeForInducingpoints() {
    const outputFeatureSelected = this.categoricalDataSource.filter(
      (item) => item.outputChecked === true,
    );
    const startRange =
      outputFeatureSelected.length > 0
        ? +outputFeatureSelected[0]?.count * 0.05
        : 200;

    if (this.configCache?.variational) {
      this.configCache.variational.num_inducing = startRange;
    }

    return startRange;
  }

  variationalCheck(checked: boolean): void {
    if (this.configCache?.variational) {
      if (checked) {
        this.configCache.variational = { num_latents: 4, num_inducing: 4 };
        this.configCache.variational.num_latents = Math.round(
          this.startRangeForLatentGps(),
        );
        this.configCache.variational.num_inducing = Math.round(
          this.startRangeForInducingpoints(),
        );
      } else {
        this.configCache.variational.num_latents = 4;
        this.configCache.variational.num_inducing = 200;
      }
      this.changeMade = true;
    }
  }

  disable_variational_func() {
    const outputFeatureSeleted = this.numericalDataSource.filter(
      (item) => item.outputChecked === true,
    );

    if (outputFeatureSeleted.length > 0) {
      return outputFeatureSeleted[0]?.count > 1500 ? false : true;
    }
    return true;
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
      if (
        this.numericalDataSource.length ==
        numSelected.length + numUnSelected.length
      ) {
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

      if (
        this.categoricalDataSource.length ==
        catSelected.length + catUnSelected.length
      ) {
        this.allCatInputChecked = true;
      } else {
        this.allCatInputChecked = false;
      }
    }
  }

  getOutputLength() {
    return this.configCache?.output_cols
      ? this.configCache?.output_cols.length
      : 0;
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

      this.changeMade = true;
    }
  }
}
