import {
  Component,
  ViewChild,
  OnInit,
  OnDestroy,
  ChangeDetectorRef,
} from '@angular/core';
import {
  DataCopyWidgetConfig,
  MPRWidgetConfig,
  InputOutputConfig,
  LocalFileConfiguration,
  Widget,
  WidgetType,
  ProblemType,
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
import { MPR } from '../../../../assets/json-files/information-tooltip.json';
import { HttpClient } from '@angular/common/http';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import {
  WidgetRunResult,
  DatasetWidgetResult,
} from 'src/app/models/workflow-sessions-api-response.models';

@Component({
  selector: 'app-mpr-config',
  templateUrl: './mpr-config.component.html',
  styleUrls: ['./mpr-config.component.less'],
})
export class MprConfigComponent implements OnInit, OnDestroy {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;

  changeMade: boolean = false;
  outputChangeMade: boolean = false;
  inputChangeMade: boolean = false;

  changeSetting: boolean = false;
  config: MPRWidgetConfig | undefined = undefined;
  configCache: MPRWidgetConfig | undefined = undefined;
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
  selectedInputColumns: string[] = [];
  selectedOutputColumn: string = '';
  columnNames: string[] = [];
  dataSource: any[] = [];

  dataSetRows!: number;
  numericalDataSource: any[] = [];
  categoricalDataSource: any[] = [];
  MPR_information: any;
  poly_deg_feat_checked: boolean = true;
  polynomial_degree_feature: { feature_name: string; feature_value: number }[] =
    [];
  cat_encoding: boolean = false;
  isCVFoldsEnabled: boolean = true;
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
    this.config = this.widgetControl.Widget.config as MPRWidgetConfig;
    this.config.widget_type = WidgetType.MPR;
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
    this.initializePolynomialDegreeFeature();
    this.getCVFoldsValue();
  }

  getCVFoldsValue() {
    this.isCVFoldsEnabled = this.configCache?.cross_validation_folds !== null;
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
        this.MPR_information = data.MPR;
      });
  }

  loadSavedConfiguration() {
    if (this.configCache) {
      if (this.configCache && this.configCache.input_cols !== undefined) {
        this.selectedInputColumns = this.configCache.input_cols;
      }

      if (this.configCache && this.configCache.output_col !== undefined) {
        this.selectedOutputColumn = this.configCache.output_col;
      }
    }
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  loadFeatures() {
    let description: string =
      'MPR Widget allows supported HEXAIND 3.0 users to train MPR models based on scikit learn LinearRegression module';

    if (this.configCache && this.configCache.problem_type) {
      if (Utils.isRegressionModel(this.configCache)) {
        description =
          'MPR Widget allows supported HEXAIND 3.0 users to train MPR models based on scikit learn LinearRegression module';
      } else if (Utils.isClassificationModel(this.configCache)) {
        description =
          'MPR Widget allows supported HEXAIND 3.0 users to train MPR models based on scikit learn LinearRegression modules';
      }
    }

    this.widgetdataInformation = {
      type: `${this.widgetControl?.Widget.type} widget`,
      description: description,
      version: this.configCache?.version,
      mpr_information: true,
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
      this.configCache?.output_col.length == 0
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

    if (!this.poly_deg_feat_checked) {
      this.configCache.polynomial_degree_feature = null;
    }

    if (this.configCache.input_scaling == 'None') {
      this.configCache.input_scaling = null;
    }

    if (
      this.getRandomState() == null ||
      this.configCache!.split_type == 'Sequential' ||
      this.configCache!.split_ratio === 0
    ) {
      this.configCache.random_state = null;
    }

    const hasCategoricalColumns =
      this.categoricalDataSource && this.categoricalDataSource.length > 0;
    const hasCategoricalSelected = this.categoricalDataSource.some(
      (item) => item.inputChecked,
    );

    if (!hasCategoricalColumns || !hasCategoricalSelected) {
      this.configCache.categorical_encoding = null;
    }

    if (this.poly_deg_feat_checked) {
      this.configCache.polynomial_degree = null;
    }

    if (this.configCache!.split_ratio === 0) {
      this.configCache.split_type = null;
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
    this.configCache = JSON.parse(JSON.stringify(this.config));
    // Reset checkbox states in the data source arrays
    this.numericalDataSource.forEach((elementData: any) => {
      elementData.inputChecked = this.configCache!.input_cols.includes(
        elementData.name,
      );
      elementData.outputChecked =
        this.configCache!.output_col === elementData.name;
    });

    this.categoricalDataSource.forEach((elementData: any) => {
      elementData.inputChecked = this.configCache!.input_cols.includes(
        elementData.name,
      );
      elementData.outputChecked =
        this.configCache!.output_col === elementData.name;
    });

    this.loadFeatures();
    this.initializePolynomialDegreeFeature();
    this.changeMade = false;
    this.getAttachedWidgetData();
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
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

  setSplitRatio(event: any): void {
    // Extract the split ratio value from the event
    let value = event.target ? +event.target.value : +event;
    const adjustedValue = value < 0 ? 0 : Math.min(99, value);

    if (this.configCache && this.configCache.split_ratio !== undefined) {
      // Check if the split_ratio is changing from 0 to a non-zero value and split_type is currently null
      if (
        this.configCache.split_ratio === 0 &&
        adjustedValue !== 0 &&
        this.configCache.split_type === null
      ) {
        this.configCache.split_type = 'Random'; // Set split_type to 'Random'
      }

      // Update the split_ratio in the config
      this.configCache.split_ratio = adjustedValue;
      this.changeMade = true;

      // Update the input field if the event came from an input element
      if (event.target) {
        event.target.value = adjustedValue;
      }
    }
  }

  getSplitRatio() {
    return this.configCache?.split_ratio;
  }

  // getSplitType() {
  //   if (!this.configCache || !this.configCache.split_type) {
  //     return 'Random'; // Return default value
  //   }
  //   return this.configCache.split_type;
  // }

  getSplitType(): string | null {
    if (this.configCache?.split_ratio === 0) {
      return null; // Disable selection if split ratio is 0
    }
    return this.configCache?.split_type || 'Random';
  }

  // Setter for split type
  setSplitType(value: string) {
    if (!this.configCache) {
      return;
    }
    if (this.configCache?.split_ratio === 0) {
      return; // Prevent setting if split ratio is 0
    }
    this.configCache.split_type = value;
    this.changeMade = true; // Track changes
  }

  getInputScaling(): string {
    return this.configCache?.input_scaling === null
      ? 'None'
      : this.configCache?.input_scaling || 'Standard';
  }

  // Setter for input scaling
  setInputScaling(value: string): void {
    if (this.configCache) {
      this.configCache.input_scaling = value; // Update config cache
      this.changeMade = true; // Mark as changed
    }
  }

  getPolynomialDegree(): number {
    if (this.configCache?.polynomial_degree == null) {
      this.configCache!.polynomial_degree = 2;
    }
    return this.configCache?.polynomial_degree ?? 2;
  }

  setPolynomialDegree(event: any): void {
    const value = event.target ? +event.target.value : event;
    const adjustedValue = value <= 0 ? 1 : Math.min(10, value);

    if (this.configCache) {
      this.configCache.polynomial_degree = adjustedValue;
      this.changeMade = true;
      if (event.target) {
        event.target.value = adjustedValue;
      }
    }
  }

  toggleCVFolds(event: any): void {
    this.isCVFoldsEnabled = event.checked;
    if (!this.isCVFoldsEnabled && this.configCache) {
      this.configCache.cross_validation_folds = null;
      this.changeMade = true;
    }

    if (this.isCVFoldsEnabled && this.configCache) {
      this.configCache.cross_validation_folds = 10;
      this.changeMade = true;
    }
  }

  getCVFolds(): number | null {
    return this.configCache?.cross_validation_folds ?? 10;
  }

  setCVFolds(event: any): void {
    if (this.isCVFoldsEnabled && this.configCache) {
      const value = event.target ? +event.target.value : +event.value;
      const adjustedValue = value < 2 ? 2 : Math.min(100, value);

      this.configCache.cross_validation_folds = adjustedValue;
      this.changeMade = true;

      if (event.target) {
        event.target.value = adjustedValue;
      }
    }
  }

  setDefaultPolynomialDegreeFeature() {
    if (!this.configCache?.polynomial_degree_feature) {
      this.configCache!.polynomial_degree_feature =
        this.configCache!.input_cols.map((col: string) => ({
          feature_name: col,
          feature_value: 2,
        }));
    }
  }

  initializePolynomialDegreeFeature() {
    // Check if polynomial_degree_feature is null and set poly_deg_feat_checked to false
    if (this.configCache?.polynomial_degree_feature === null) {
      this.poly_deg_feat_checked = false;
      return;
    }

    if (this.configCache && this.configCache.input_cols) {
      // Filter out any features not in input_cols if polynomial_degree_feature exists
      if (this.configCache.polynomial_degree_feature) {
        this.configCache.polynomial_degree_feature =
          this.configCache.polynomial_degree_feature.filter((feature: any) =>
            this.configCache!.input_cols.includes(feature.feature_name),
          );
      }

      // Add missing input columns to polynomial_degree_feature with default value if not already present
      if (this.configCache.polynomial_degree_feature) {
        this.configCache.input_cols.forEach((col: string) => {
          const existingFeature =
            this.configCache!.polynomial_degree_feature!.find(
              (f: any) => f.feature_name === col,
            );
          if (!existingFeature) {
            this.configCache!.polynomial_degree_feature!.push({
              feature_name: col,
              feature_value: 2,
            });
          }
        });
      }
    }

    // Set poly_deg_feat_checked based on presence of features in polynomial_degree_feature
    this.poly_deg_feat_checked =
      Array.isArray(this.configCache?.polynomial_degree_feature) &&
      (this.configCache?.polynomial_degree_feature?.length ?? 0) > 0;
  }

  getPolynomialDegreeFeature(featureName: string): number {
    if (!this.configCache?.polynomial_degree_feature) {
      return 1;
    }
    const feature = this.configCache.polynomial_degree_feature.find(
      (f) => f.feature_name === featureName,
    );
    return feature ? feature.feature_value : 1;
  }

  setPolynomialDegreeFeature(event: any, featureName: string): void {
    if (!this.configCache?.polynomial_degree_feature) {
      return;
    }

    const feature = this.configCache.polynomial_degree_feature.find(
      (f) => f.feature_name === featureName,
    );

    if (feature) {
      const value = event.target ? +event.target.value : +event.value;
      feature.feature_value = value <= 0 ? 1 : value;
      this.changeMade = true;
      if (event.target) {
        event.target.value = feature.feature_value;
      }
    }
  }

  categoricalDataInput(): boolean {
    if (
      !this.categoricalDataSource ||
      this.categoricalDataSource.length === 0
    ) {
      return false;
    }
    const hasCategoricalSelected = this.categoricalDataSource.some(
      (item) => item.inputChecked,
    );
    if (!hasCategoricalSelected && this.configCache) {
      this.configCache.categorical_encoding = null;
    }
    if (
      hasCategoricalSelected &&
      this.configCache &&
      !this.configCache.categorical_encoding
    ) {
      this.configCache.categorical_encoding = 'One_hot';
    }

    return hasCategoricalSelected;
  }

  getCategoricalEncoding(): string {
    return this.configCache?.categorical_encoding || 'One_hot';
  }

  setCategoricalEncoding(value: string): void {
    if (this.configCache) {
      this.configCache.categorical_encoding = value;
      this.changeMade = true;
    }
  }

  // Retrieve the random state; if unset, default to null (selects "None" by default)
  getRandomState(): number | string | null {
    if (this.configCache?.random_state === 0) return 0;
    if (this.configCache?.random_state === 42) return 42;
    return this.configCache?.random_state ?? null;
  }

  setRandomState(event: any): void {
    let value =
      event === null ? null : event.target ? +event.target.value : +event;
    if (value === null) {
      this.configCache!.random_state = null;
      this.changeMade = true;
    } else {
      const adjustedValue = Math.min(100, Math.max(0, value));
      if (this.configCache) {
        this.configCache.random_state = adjustedValue;
        this.changeMade = true;
        if (event && event.target) {
          event.target.value = adjustedValue;
        }
      }
    }
  }

  checkCatagoricalInputSelected(): boolean {
    const hasCategoricalSelected = this.categoricalDataSource.some(
      (item) => item.inputChecked,
    );
    if (hasCategoricalSelected) {
      this.poly_deg_feat_checked = false;
    }
    return hasCategoricalSelected;
  }

  check_poly_deg_feat(event: any) {
    this.poly_deg_feat_checked = event.checked;
    // If checked, initialize existing data or set defaults if none exist
    if (event.checked) {
      if (this.configCache?.polynomial_degree_feature) {
        this.initializePolynomialDegreeFeature();
      } else {
        this.setDefaultPolynomialDegreeFeature();
      }
    }
    this.changeMade = true;
  }
}
