import { Component, Input, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';
import { Subscription } from 'rxjs';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { WidgetControl } from '../../widget-control/widget-control';
import {
  Widget,
  JoinType,
  JoinWidgetConfig,
  InputOutputConfig,
  DataCopyWidgetConfig,
  LocalFileConfiguration,
  WidgetType,
} from 'src/app/models/workflow-models';
import { Connector, ConnectorType } from 'src/app/models/connector-models';
import {
  WorkflowCanvasService,
  ConfigService,
} from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { SettingsComponent } from '../settings/settings.component';
import { JoinSelectColumnComponent } from 'src/app/dialogs/join-select-columns/join-select-columns.component';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import { MoboConfigService } from '../mobo-config/mobo-config.service';
import { ToastrService } from 'ngx-toastr';
import { v4 as uuidv4 } from 'uuid';
import {
  WidgetRunResult,
  DatasetWidgetResult,
} from 'src/app/models/workflow-sessions-api-response.models';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { DataPreviewService } from 'src/app/dialogs/data-preview/services/data-preview.service';

@Component({
  selector: 'app-join',
  templateUrl: './join.component.html',
  styleUrls: ['./join.component.less'],
})
export class JoinComponent implements OnInit {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  private dataSubscription!: Subscription;
  @Input() connectorData: any;
  joinForm!: FormGroup;

  changeMade: boolean = false;
  config: JoinWidgetConfig | undefined = undefined;
  configCache: JoinWidgetConfig | undefined = undefined;
  outputName: string | undefined = undefined;

  widgetType = 'JOIN';
  allWidgets: any;
  allDataSource: any[] = [];
  data = {};

  dataSourceOptions: any[] = [];
  widgetControl: WidgetControl | undefined = undefined;
  selectedInputWidget1: Widget | undefined = undefined;
  selectedInputWidget2: Widget | undefined = undefined;
  inputWidgets: Widget[] = [];
  isJoinDisable: boolean = false;

  joinTypes = Object.values(JoinType).filter(
    (value) => typeof value === 'string',
  );
  options1 = ['Option 1', 'Option 2', 'Option 3'];
  options2 = ['Option A', 'Option B', 'Option C'];
  rows = [{ selectedOption1: '', selectedOption2: '' }];

  inputURN_1: any;
  inputURN_2: any;
  project_id: string | undefined;
  site_id: string = '1';
  columnPairs: FormGroup[] = [];
  rightColumnNames: any[] = [];
  leftColumnNames: any[] = [];
  filteredLeftColumns: any[] = [];
  filteredRightColumns: any[] = [];
  leftData: any[] = [];
  rightData: any[] = [];

  searchLeftTerms: string[] = [];
  searchRightTerms: string[] = [];

  constructor(
    private fb: FormBuilder,
    public sharedDataService: SharedDataService,
    private dialog: MatDialog,
    public workflowCanvasService: WorkflowCanvasService,
    private route: ActivatedRoute,
    private moboConfigService: MoboConfigService,
    public toaster: ToastrService,
    private workflowsSessionsApiService: WorkflowsSessionsApiService,
    private configService: ConfigService,
    private dataPreviewService: DataPreviewService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.config = this.widgetControl.Widget.config as JoinWidgetConfig;
    this.config.widget_type = WidgetType.JOIN;
    this.configCache = JSON.parse(JSON.stringify(this.config));
  }

  ngOnInit() {
    this.route.queryParams.subscribe((params) => {
      this.project_id = params['projectId'];
    });
    this.initializeInformation();

    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.workflowCanvasService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );

      if (this.inputWidgets && this.inputWidgets.length > 0) {
        // this.getTheUpdatedFeatures();
        this.setSelectedInputWidgets();
        if (this.widgetControl.Widget.outputs.length) {
          this.outputName = this.widgetControl.Widget.outputs[0].name;
        }
      }
      // this.handleConnectorData(this.workflowCanvasService.widgetControls);
      this.loadSavedConfiguration();
    }
  }

  async getTheUpdatedFeatures() {
    this.inputURN_1 = this.workflowCanvasService.findConnectedMLWidget(
      this.widgetControl?.Widget.inputs[0]?.urn ?? '',
    );
    this.inputURN_2 = this.workflowCanvasService.findConnectedMLWidget(
      this.widgetControl?.Widget.inputs[1]?.urn ?? '',
    );

    if (this.inputURN_1.length > 0) {
      var configuration = this.inputURN_1[0].config as DataCopyWidgetConfig;
      var source = configuration?.source
        ?.configuration as LocalFileConfiguration;
      var dataset_id = source?.dataset_id;
      if (dataset_id) {
        this.getTheFeaturesMetaDataLeftColumn(dataset_id);
      } else {
        try {
          let result: WidgetRunResult[] =
            await this.workflowsSessionsApiService.GetWorkflowSessionWidgetRunStatus(
              this.configService.SelectedSiteId,
              this.configService.SelectedProjectId!,
              this.workflowCanvasService.SelectedWorkflowSession?._id!,
              this.inputURN_1[0].urn!,
            );
          if (result && result.length > 0) {
            let response = result[0];
            let datasetWidgetResult: DatasetWidgetResult =
              response.result_value as DatasetWidgetResult;
            if (result[0]['result_type'] === 'DATASET') {
              var dataset_id = datasetWidgetResult._id;
              this.getTheFeaturesMetaDataLeftColumn(dataset_id);
            }
          }
        } catch (error) {
          console.error(error);
        }
      }
    }
    if (this.inputURN_2.length > 0) {
      var configuration = this.inputURN_2[0].config as DataCopyWidgetConfig;
      var source = configuration?.source
        ?.configuration as LocalFileConfiguration;
      var dataset_id = source?.dataset_id;
      if (dataset_id && dataset_id != '') {
        this.getTheFeaturesMetaDataRightColumn(dataset_id);
      } else {
        try {
          let result: WidgetRunResult[] =
            await this.workflowsSessionsApiService.GetWorkflowSessionWidgetRunStatus(
              this.configService.SelectedSiteId,
              this.configService.SelectedProjectId!,
              this.workflowCanvasService.SelectedWorkflowSession?._id!,
              this.inputURN_2[0].urn!,
            );
          if (result && result.length > 0) {
            let response = result[0];
            let datasetWidgetResult: DatasetWidgetResult =
              response.result_value as DatasetWidgetResult;
            if (result[0]['result_type'] === 'DATASET') {
              var dataset_id = datasetWidgetResult._id;
              this.getTheFeaturesMetaDataRightColumn(dataset_id);
            }
          }
        } catch (error) {
          console.error(error);
        }
      }
      // this.dataset_id = source?.dataset_id;
    }
  }

  getTheFeaturesMetaDataLeftColumn(dataset_id: string | undefined) {
    if (dataset_id !== undefined) {
      this.dataPreviewService
        .getMetadata(dataset_id)
        .then((response) => {
          if (response) {
            var data = Object.keys(response.data_column_types);
            this.leftData = Object.keys(response.data_column_types);
            this.leftColumnNames = Object.keys(response.data_column_types);
            this.filteredLeftColumns = this.leftColumnNames.map(() =>
              this.leftColumnNames.slice(),
            );
          }
        })
        .catch((error) => {
          const errorMessage =
            error?.error?.message ||
            error?.message ||
            'An unexpected error occurred';
          this.toaster.error(errorMessage, 'ERROR', {
            positionClass: 'custom-toast-position',
          });
        });

      // Join widget should not use mobo config service
      // this.moboConfigService
      //   .getDataset(this.site_id, this.project_id ?? '', dataset_id)
      //   .subscribe({
      //     next: (response) => {
      //       if (response) {
      //         var data = Object.keys(response.data_column_types);
      //         this.leftData = Object.keys(response.data_column_types);
      //         this.leftColumnNames = Object.keys(response.data_column_types);
      //         // var data = response.statistics;
      //         // this.leftData = response.statistics;
      //         // this.leftColumnNames = this.extractAndCombineColumnNames(data);
      //         this.filteredLeftColumns = this.leftColumnNames.map(() => this.leftColumnNames.slice());
      //       }
      //     },
      //     error: (error) => {
      //       const errorMessage =
      //         error?.error?.message ||
      //         error?.message ||
      //         'An unexpected error occurred';
      //       this.toaster.error(errorMessage, 'ERROR', {
      //         positionClass: 'custom-toast-position',
      //       });
      //     },
      //   });
    }
  }

  getTheFeaturesMetaDataRightColumn(dataset_id: string | undefined) {
    if (dataset_id !== undefined) {
      this.dataPreviewService
        .getMetadata(dataset_id)
        .then((response) => {
          if (response) {
            var data = Object.keys(response.data_column_types);
            this.rightData = Object.keys(response.data_column_types);
            this.rightColumnNames = Object.keys(response.data_column_types);
            this.filteredRightColumns = this.rightColumnNames.map(() =>
              this.rightColumnNames.slice(),
            );
          }
        })
        .catch((error) => {
          const errorMessage =
            error?.error?.message ||
            error?.message ||
            'An unexpected error occurred';
          this.toaster.error(errorMessage, 'ERROR', {
            positionClass: 'custom-toast-position',
          });
        });

      // Join widget should not depend on moboconfig service

      // this.moboConfigService
      //   .getDataset(this.site_id, this.project_id ?? '', dataset_id)
      //   .subscribe({
      //     next: (response) => {
      //       if (response) {
      //         var data = Object.keys(response.data_column_types);
      //         this.rightData = Object.keys(response.data_column_types);
      //         this.rightColumnNames = Object.keys(response.data_column_types);
      //         // var data = response.statistics;
      //         // this.rightData = response.statistics;
      //         // this.rightColumnNames = this.extractAndCombineColumnNames(data);
      //         this.filteredRightColumns = this.rightColumnNames.map(() => this.rightColumnNames.slice());
      //       }
      //     },
      //     error: (error) => {
      //       const errorMessage =
      //         error?.error?.message ||
      //         error?.message ||
      //         'An unexpected error occurred';
      //       this.toaster.error(errorMessage, 'ERROR', {
      //         positionClass: 'custom-toast-position',
      //       });
      //     },
      //   });
    }
  }

  extractAndCombineColumnNames(data: any) {
    const combinedColumns: any = [];
    data.forEach((item: { column_names: any }) => {
      combinedColumns.push(...item.column_names);
    });

    return combinedColumns;
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  setSelectedInputWidgets() {
    this.selectedInputWidget1 = undefined;
    this.selectedInputWidget2 = undefined;

    if (this.widgetControl) {
      if (this.widgetControl.Widget.inputs.length > 0) {
        this.selectedInputWidget1 = this.inputWidgets.find(
          (t) => t.urn === this.widgetControl?.Widget.inputs[0].urn,
        );
      }
      if (this.widgetControl.Widget.inputs.length > 1) {
        this.selectedInputWidget2 = this.inputWidgets.find(
          (t) => t.urn === this.widgetControl?.Widget.inputs[1].urn,
        );
      }
      this.getTheUpdatedFeatures();
    }
  }

  getSelectedInputWidget1(): Widget | undefined {
    return this.selectedInputWidget1;
  }

  getSelectedInputWidget2(): Widget | undefined {
    return this.selectedInputWidget2;
  }

  getInputingWidgetsOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let outputConfig: InputOutputConfig = widget.outputs[0];
      return outputConfig.name!;
    }

    return 'Not Set';
  }

  joinTypeValues() {
    return Object.values(JoinType);
  }

  private handleConnectorData(widgetControls: WidgetControl[]) {
    var widgetControlsFiltered = widgetControls.filter(
      (cn: any) => cn.Widget.name !== 'Start' && cn.Widget.type !== 'JOIN',
    );
    // this.populateDataSourceOptions(widgetControlsFiltered);
  }
  //Kept for future use
  // private populateDataSourceOptions(widgets: WidgetControl[]) {
  //   this.dataSourceOptions = [];

  //   for (const widget of widgets) {
  //     if (widget.Widget.type == 'DATA_COPY') {
  //       let config: DataCopyWidgetConfig = widget.Widget
  //         .config as DataCopyWidgetConfig;

  //       if (config) {
  //         if (
  //           config.sink!.dataset_name &&
  //           (config.source.configuration as LocalFileConfiguration).dataset_id!
  //         ) {
  //           this.dataSourceOptions.push({
  //             name: config.sink!.dataset_name,
  //             dataset_id: (
  //               config.source.configuration as LocalFileConfiguration
  //             ).dataset_id,
  //           });
  //         }
  //       }
  //     }
  //   }
  // }

  getControl(pair: FormGroup, controlName: string): FormControl {
    return pair.get(controlName) as FormControl;
  }

  getDataCsvWidgetConfig(): Widget | null {
    let dataCsvActivityConfig: Widget = this.widgetControl?.Widget as Widget;

    return dataCsvActivityConfig;
  }

  initializeInformation() {
    this.data = {
      type: this.widgetControl?.Widget.type,
      description:
        'Join Widget allows users to combine two pre-existing tabular datasets within the HEXAIND 3.0 platform, into a single Tabular Dataset, to be used as an asset for further processing.',
      version: '',
    };
    this.loadSavedConfiguration();
  }

  get widgetOutput(): string | undefined {
    return this.outputName;
  }

  set widgetOutput(value: string | undefined) {
    this.outputName = value;
    this.changeMade = true;
  }

  onAppSettingsUpdated() {
    this.changeMade = true;
  }

  get inputWidget1(): Widget | undefined {
    return this.selectedInputWidget1;
  }

  input2Widget(widget: Widget | undefined, index: number) {
    if (!widget || !widget.outputs.length) {
      return;
    }
    this.selectedInputWidget1 = this.inputWidgets.find(
      (t) => t.outputs.length && t.outputs[0].name === widget.outputs[0].name,
    );
    if (this.selectedInputWidget1 && this.widgetControl?.Widget.inputs) {
      let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
      inputOutputConfig.name = this.selectedInputWidget1.outputs[0].name;
      inputOutputConfig.urn = this.selectedInputWidget1.urn;

      this.widgetControl.Widget.inputs =
        this.widgetControl?.Widget.inputs.filter(
          (input) =>
            !(
              input.name === inputOutputConfig.name &&
              input.urn === inputOutputConfig.urn
            ),
        );

      if (index < this.widgetControl.Widget.inputs.length) {
        this.widgetControl.Widget.inputs[index] = inputOutputConfig;
      } else {
        this.widgetControl.Widget.inputs.push(inputOutputConfig);
      }
    }
    this.getTheUpdatedFeatures();
    this.changeMade = true;
  }

  get inputWidget2(): Widget | undefined {
    return this.selectedInputWidget2;
  }

  input2widget(widget: Widget | undefined, index: number) {
    if (
      !widget ||
      (!widget.outputs.length && this.widgetControl?.Widget.inputs)
    ) {
      return;
    }
    this.selectedInputWidget2 = this.inputWidgets.find(
      (t) => t.outputs.length && t.outputs[0].name === widget.outputs[0].name,
    );
    if (this.selectedInputWidget2 && this.widgetControl?.Widget.inputs) {
      let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
      inputOutputConfig.name = this.selectedInputWidget2.outputs[0].name;
      inputOutputConfig.urn = this.selectedInputWidget2.urn;

      this.widgetControl.Widget.inputs =
        this.widgetControl?.Widget.inputs.filter(
          (input) =>
            !(
              input.name === inputOutputConfig.name &&
              input.urn === inputOutputConfig.urn
            ),
        );

      if (index < this.widgetControl.Widget.inputs.length) {
        this.widgetControl.Widget.inputs[index] = inputOutputConfig;
      } else {
        this.widgetControl.Widget.inputs.push(inputOutputConfig);
      }
    }
    this.getTheUpdatedFeatures();
    this.changeMade = true;
  }

  onSave() {
    if (
      this.columnPairs.length > 0 &&
      this.inputURN_1.length > 0 &&
      this.inputURN_2.length > 0
    ) {
      const hasMissingValues = this.columnPairs.some((pair, index) => {
        const leftValue = pair.get('left')?.value;
        const rightValue = pair.get('right')?.value;

        if (this.columnPairs.length === 1 && !leftValue && !rightValue) {
          return false;
        }
        return !leftValue || !rightValue;
      });

      if (hasMissingValues) {
        this.toaster.info(
          'Cannot add a new row until all existing left and right values are filled in.',
        );
        return;
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

    if (this.outputName) {
      this.outputName = this.outputName.trim();
      if (
        this.widgetControl.Widget.outputs &&
        this.widgetControl.Widget.outputs.length > 0
      ) {
        this.widgetControl.Widget.outputs[0].name = this.outputName;
      }
    }
    this.widgetControl.Widget.inputs.length = 0;

    if (this.selectedInputWidget1) {
      let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
      inputOutputConfig.name = this.selectedInputWidget1.outputs[0].name;
      inputOutputConfig.urn = this.selectedInputWidget1.urn;
      this.widgetControl.Widget.inputs.push(inputOutputConfig);
    }

    if (this.selectedInputWidget2) {
      let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
      inputOutputConfig.name = this.selectedInputWidget2.outputs[0].name;
      inputOutputConfig.urn = this.selectedInputWidget2.urn;
      this.widgetControl.Widget.inputs.push(inputOutputConfig);
    }
    this.getTheUpdatedFeatures();
    this.changeMade = false;
  }

  onCancel() {
    this.outputName = undefined;
    this.settingsComponent.RevertAppSetting();
    // Deep clone to prevent updates from modifying original
    this.configCache = JSON.parse(JSON.stringify(this.config));
    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
      this.setSelectedInputWidgets();
    }

    if (this.configCache) {
      this.searchLeftTerms = [...(this.configCache.left_columns || [])];
      this.searchRightTerms = [...(this.configCache.right_columns || [])];

      this.loadSavedConfiguration();
    }
    this.changeMade = false;
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

  getDatasetName(selectedInputWidget: Widget | undefined): string | undefined {
    if (!selectedInputWidget) return undefined;

    const widget = this.inputWidgets.find(
      (value) => value.urn === selectedInputWidget.urn,
    );
    return widget ? widget.name : undefined;
  }

  // Taimoor's code ---->>>>>>
  loadSavedConfiguration() {
    if (this.configCache) {
      this.columnPairs = [];
      const leftColumns = this.configCache.left_columns || [];
      const rightColumns = this.configCache.right_columns || [];
      if (leftColumns.length > 0 || rightColumns.length > 0) {
        const maxLength = Math.max(leftColumns.length, rightColumns.length);

        this.searchLeftTerms = [...leftColumns];
        this.searchRightTerms = [...rightColumns];
        this.filteredLeftColumns = leftColumns.map(() => [...leftColumns]);
        this.filteredRightColumns = rightColumns.map(() => [...rightColumns]);

        for (let index = 0; index < maxLength; index++) {
          const left = leftColumns[index] || '';
          const right = rightColumns[index] || '';
          const uniqueKey = uuidv4();

          const pairForm = new FormGroup({
            key: new FormControl(uniqueKey),
            left: new FormControl(left),
            right: new FormControl(right),
          });

          this.columnPairs.push(pairForm);
        }
      } else {
        this.addRow();
      }
    }
  }

  filterLeftColumns(rowIndex: number) {
    const searchTermLower = this.searchLeftTerms[rowIndex]?.toLowerCase() || '';
    if (searchTermLower === '') {
      this.filteredLeftColumns[rowIndex] = this.leftColumnNames.slice();
    } else {
      this.filteredLeftColumns[rowIndex] = this.leftColumnNames.filter(
        (column) => column.toLowerCase().includes(searchTermLower),
      );
    }
  }

  filterRightColumns(rowIndex: number) {
    const searchTermLower =
      this.searchRightTerms[rowIndex]?.toLowerCase() || '';
    this.filteredRightColumns[rowIndex] = this.rightColumnNames.filter(
      (column) => column.toLowerCase().includes(searchTermLower),
    );
  }

  updateConfigCache(
    index: number,
    side: 'left' | 'right',
    columnValue: string,
  ) {
    if (!this.configCache) {
      this.configCache = new JoinWidgetConfig();
    }
    if (!this.configCache.left_columns) {
      this.configCache.left_columns = [];
    }
    if (!this.configCache.right_columns) {
      this.configCache.right_columns = [];
    }
    const pair = this.columnPairs[index];

    if (side === 'left') {
      pair.get('left')?.setValue(columnValue);
      this.configCache.left_columns[index] = columnValue;
    } else {
      pair.get('right')?.setValue(columnValue);
      this.configCache.right_columns[index] = columnValue;
    }
    this.changeMade = true;
  }

  getColumnType(column_name: any) {
    for (const data of this.leftData) {
      const index = data.column_names.indexOf(column_name);
      if (index !== -1) {
        return data.column_type; // Return the column type if found
      }
    }
    return null;
  }

  getRightColumnType(column_name: any) {
    for (const data of this.rightData) {
      const index = data.column_names.indexOf(column_name);
      if (index !== -1) {
        return data.column_type; // Return the column type if found
      }
    }
    return null;
  }

  onJoinTypeChange(selectedJoinType: JoinType) {
    if (this.configCache) {
      this.configCache.join_type = selectedJoinType;
      this.changeMade = true;
    }
  }

  addRow() {
    const hasMissingValues = this.columnPairs.some((pair) => {
      const leftValue = pair.get('left')?.value;
      const rightValue = pair.get('right')?.value;
      return !leftValue || !rightValue;
    });

    if (hasMissingValues) {
      this.toaster.info(
        'Cannot add a new row until all existing left and right values are filled in.',
      );
      return;
    }

    const uniqueKey = uuidv4();
    const pairForm = new FormGroup({
      left: new FormControl(''),
      right: new FormControl(''),
      key: new FormControl(uniqueKey),
    });
    this.columnPairs.push(pairForm);
  }

  removeRow(value: any) {
    if (this.columnPairs.length > 0) {
      const index = this.columnPairs.findIndex((p) => p.get('key') === value);

      if (index > -1) {
        this.columnPairs.splice(index, 1);

        if (this.configCache) {
          if (this.configCache.left_columns) {
            this.configCache.left_columns.splice(index, 1);
          }
          if (this.configCache.right_columns) {
            this.configCache.right_columns.splice(index, 1);
          }
        }
        this.loadSavedConfiguration();
        this.getTheUpdatedFeatures();
        this.changeMade = true;
      }
    }
  }

  openSelectColumns(): void {
    this.dialog.open(JoinSelectColumnComponent, {
      width: '90%',
      height: '90%',
      data: { name: 'Angular' },
    });
  }
}
