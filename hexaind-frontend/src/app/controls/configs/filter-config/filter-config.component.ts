import { ChangeDetectorRef, Component, OnInit, ViewChild } from '@angular/core';
import { WidgetControl } from '../../widget-control/widget-control';
import {
  ConfigService,
  WorkflowCanvasService,
} from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { Connector, ConnectorType } from 'src/app/models/connector-models';
import {
  FilterOperand,
  FilterOperator,
  FilterValues,
  FilterWidgetConfig,
  InputOutputConfig,
  Widget,
  FilterConfig,
  FilterType,
  WidgetType,
  DataType,
  StringFilterOperator,
  DataCopyWidgetConfig,  
  LocalFileConfiguration,
} from 'src/app/models/workflow-models';
import { SettingsComponent } from '../settings/settings.component';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { Expression } from '@angular/compiler';
import { ApiService } from 'src/app/services/api.service';
import { ToastrService } from 'ngx-toastr';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { WidgetRunResult, DatasetWidgetResult } from 'src/app/models/workflow-sessions-api-response.models';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { FilterSelectionConfigComponent } from '../filter-selection-config/filter-selection-config.component';

export class FilterPanel {
  id: number = 0;
  filterOperands: string = '';
  filterValues: FilterValues = new FilterValues('', '', '', '');
  operators: (string | StringFilterOperator | FilterOperator)[] = [];  // Initialize with an empty array or default value
  valueType: string = '';
}


@Component({
  selector: 'app-filter-config',
  templateUrl: './filter-config.component.html',
  styleUrls: ['./filter-config.component.less'],
})
export class FilterConfigComponent implements OnInit {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;

  changeMade: boolean = false;
  config: FilterWidgetConfig | undefined = undefined;
  configCache: FilterWidgetConfig | undefined = undefined;
  outputName: string | undefined = undefined;
  inputName: string | undefined = undefined;
  selectedLogicalOperator: string = '';
  selectedFileType: string = '';
  connectors: Connector[] = [];
  files: any;
  dataset: any;
  datasetId: any;
  siteId: any;
  projectId: any;
  fieldValue: any = '';
  operatorsValue: any = '';
  logicalOperatordisable: boolean = true;
  inputValue: any;
  fieldTypeValue: any;
  updateInputWidget: any;
  columnsNames: any;
  columnsNamesData: any;
  valueType: any;
  logicalOperatorCount: any;
  data = {};
  operators: any = ['SELECT','EQ', 'NE', 'GT', 'GTE', 'LT', 'LTE'];
  logicalOperators: any = ['AND', 'OR', 'XOR'];
  numericalOperators: FilterOperator[] = [
    FilterOperator.SELECT,
    FilterOperator.EQ,
    FilterOperator.NE,
    FilterOperator.GT,
    FilterOperator.GTE,
    FilterOperator.LT,
    FilterOperator.LTE
  ];

  categoricalOperators: StringFilterOperator[] = [
    StringFilterOperator.STARTS_WITH,
    StringFilterOperator.ENDS_WITH,
    StringFilterOperator.EXACT_MATCH,
    StringFilterOperator.PARTIAL_MATCH
  ];
  public widgetControl: WidgetControl | undefined = undefined;
  selectedInputWidget: Widget | undefined = undefined;
  inputWidgets: Widget[] = [];
  columnNamesWithTypes: any = [];
  filterOperandValue: any;
  filterOperandButtonStatus: boolean = false;

  filterPanels: FilterPanel[] = [
    new FilterPanel()
  ];
  inputChangeMade = false;
  // statisticalData: any[] = []
  statisticalData: { [key: string]: any } = {};

  DATASET: string = "DATASET";

  dialogRef: MatDialogRef<FilterSelectionConfigComponent> | null = null;

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    public sharedDataService: SharedDataService,
    private configService: ConfigService,
    private apiService: ApiService,
    public toaster: ToastrService,
    public workflowsSessionsApiService:WorkflowsSessionsApiService,
    private dialog: MatDialog,
    private cdr: ChangeDetectorRef,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.siteId = this.configService.SelectedSiteId;
    this.projectId = this.configService.SelectedProjectId;
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    if (this.widgetControl) {
      this.config = this.widgetControl.Widget.config as FilterWidgetConfig;
      this.config.widget_type = WidgetType.FILTER;
      this.configCache = JSON.parse(JSON.stringify(this.config));
      this.outputName = this.widgetControl.Widget.outputs[0].name;

      if (this.widgetControl.Widget.inputs.length) {
        this.inputName = this.widgetControl.Widget.inputs[0].name;
      }


      this.createFilterUX();
    }
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  createFilterUX() {
    if (this.config && this.config.config!.filter_values.length > 0) {
      let index: number = 0;
      this.filterPanels = [];
      this.config.config?.filter_values.forEach((filter: FilterValues) => {
        let filterPanel: FilterPanel = new FilterPanel();
        filterPanel.id = index++;
        filterPanel.filterValues.column_name = filter.column_name ?? '';
        this.fieldValue = filter.column_name;
        this.inputValue = filter.value;
        setTimeout(() => {
          this.columnNamesWithTypes.forEach((item: any) => {
            if (filter.column_name == item.column_name) {
              filterPanel.valueType = item.column_type;
            }
          });
        }, 1000);

        filterPanel.filterValues.value = filter.value ?? '';
        this.filterPanels.push(filterPanel);
      });
      index = 0;
      if (this.config.config!.filter_operands.length > 0) {
        this.config.config?.filter_operands.forEach((operator:any) => {
          this.filterPanels[index].filterOperands = operator;
          index++;
        });
      }
    } else {
      if (this.configCache) {
        this.configCache.config!.filter_values.push(
          new FilterValues('', '', '', ''),
        );
      }
    }
  }

  ngOnInit() {
    this.initializeInformation();
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {

      this.inputWidgets = this.workflowCanvasService.findConnectedWidgetsAndFilter(
        this.widgetControl.Widget.urn, this.DATASET
      );

      // Remove any widgets that dont have outputs.
      if (this.inputWidgets && this.inputWidgets.length > 0) {
        this.inputWidgets = this.inputWidgets.filter(
          (widget) => widget.outputs.length > 0,
        );

        this.dataset = this.inputWidgets[0].config;
        if (this.dataset.source?.configuration.dataset_id) {
          this.datasetId = this.dataset.source.configuration.dataset_id;
        }
        
        this.loadSelectedInputWidget();
      }
    }
    // this.getFilterWidgetFields();
    // this.selectedInputWidgets();
    
  }

  async getDataseOfConnectedWidgetResult() {
    if(this.selectedInputWidget){
        try {
          let result: WidgetRunResult[] =
          await this.workflowsSessionsApiService.GetWorkflowSessionWidgetRunStatus(
            this.configService.SelectedSiteId,
            this.configService.SelectedProjectId!,
            this.workflowCanvasService.SelectedWorkflowSession?._id!,
            this.selectedInputWidget.urn!,
          );
          if (result && result.length>0) {
            this.datasetId = this.workflowCanvasService.getDataSetIdFromResults(result,this.selectedInputWidget)
            if (this.datasetId) {
              this.getFilterWidgetFields();
            }
          }
        } catch (error) {
          console.error(error) 
        }
    } else {
      this.getFilterWidgetFields();
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
      this.getDataseOfConnectedWidgetResult();

    } else {
      if (this.inputWidgets.length === 1) {
        this.selectedInputWidget = this.inputWidgets[0];
        this.onSave();
        this.getDataseOfConnectedWidgetResult();
      }
    }
    // console.log('this.selectedInputWidget',this.selectedInputWidget);
    // this.getDataseOfConnectedWidget();
    
  }

  getInputingWidgetsOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let inputConfig: InputOutputConfig = widget.outputs[0];
      return inputConfig.name!;
    }
    return ""
  }

  getFilterColumnName(panel: FilterPanel): string {
    return panel.filterValues.column_name || '';
  }

  setFilterColumnName(panel: FilterPanel, event: any) {
    const columnName = event.option.value;
    panel.filterValues.column_name = columnName;
    const index = this.filterPanels.indexOf(panel);

    if (this.configCache && this.configCache.config && index !== -1) {
      this.changeMade = true;
      this.configCache.config.filter_values[index].column_name = columnName;
      const dataType = this.getColumnType(columnName);
      this.configCache.config.filter_values[index].data_type = dataType;

      // Update operators based on the data type
      panel.operators = this.getOperatorsForType(dataType);
    }
  }

  getOperatorsForType(dataType: DataType): string[] {
    return dataType === 'NUMERICAL' ? this.numericalOperators : this.categoricalOperators;
  }

  getColumnType(columnName: string): DataType{
    if (this.statisticalData && this.statisticalData[columnName] !== undefined) {
      const columnType = this.statisticalData[columnName];
      return (columnType['data_category'] === 'NUMERICAL') ? DataType.NUMERICAL : DataType.CATEGORICAL;
    }
    return DataType.NUMERICAL;
  }

  getFilterDataType(panel: FilterPanel):  DataType | '' {
    const columnName = panel?.filterValues?.column_name;
  
    if (columnName && this.statisticalData[columnName]) {
      const columnType = this.statisticalData[columnName];
      return (columnType['data_category'] === 'NUMERICAL') ? DataType.NUMERICAL : DataType.CATEGORICAL;
    }
    
    return '';

  }

  isFilterSelectionPopupEnabled(panel: FilterPanel) {
    let type = this.getFilterDataType(panel);
    if (type === DataType.CATEGORICAL) {
      return true;
    }

    return false;
  }

  getDataType(i: number) {
    return this.configCache?.config?.filter_values[i].data_type === 'CATEGORICAL' ? 'text' : 'number';
  }

  onInputChange(event: any) {
    this.columnsNames = this._filter(event.target.value);
  }

  private _filter(value: string): string[] {
    const filterValue = value.toLowerCase();
    return (filterValue) ? this.columnsNames.filter((columnName: string) => columnName.toLowerCase().includes(filterValue)) : this.columnsNamesData;
  }

  getFilterValue(panel: FilterPanel) {
    return panel.filterValues.value ?? '';
  }

  setFilterValue(panel: FilterPanel, value: string) {
    panel.filterValues.value = value;
    this.inputValue = value;
    let index: number = this.filterPanels.indexOf(panel);
    if (this.configCache && this.configCache.config && index !== -1) {
      this.changeMade = true;
      this.configCache.config.filter_values[index].value = value;
    }
  }

  getFilterOperator(i: number) {
    return this.configCache?.config?.filter_values[i].operator || FilterOperator.SELECT;
  }

  getFilterInputValue(i: number) {
    return this.configCache?.config?.filter_values[i].value;
  }

  setFilterOperator(panel: FilterPanel, value: FilterOperator) {
    this.operatorsValue = value;
    panel.filterValues.operator = value;

    let index: number = this.filterPanels.indexOf(panel);
    if (this.configCache && this.configCache.config && index !== -1) {
      this.changeMade = true;
      this.configCache.config.filter_values[index].operator = value;
    }
  }

  operatorsArray(i: number, panel: FilterPanel): { value: string, display: string }[] {
    const dataType = this.getColumnType(panel.filterValues.column_name);
    const operators = this.getOperatorsForType(dataType);

    const displayMap: any = {
      SELECT: 'SELECT',
      EQ: 'EQ (==)',
      NE: 'NE (!=)',
      GT: 'GT (>)',
      GTE: 'GTE (>=)',
      LT: 'LT (<)',
      LTE: 'LTE (<=)',
    };
    return operators.map(operator => ({
      value: operator,
      display: displayMap[operator] || operator, // Fallback to operator itself
    }));
  }


  trackByOperator(index: number, operator: { value: string; display: string }): string {
    return operator.value; // Unique identifier
  }


  getValueType(panel: FilterPanel) {
    return panel.valueType ?? '';
  }

  setValueType(panel: FilterPanel, value: FilterOperator) {
    panel.valueType = value;
  }

  getFilterOperands(panel: FilterPanel) {
    return panel.filterOperands;
  }

  setFilterOperands(panel: FilterPanel, value: FilterOperand) {
    //panel.filterOperands = value;
    this.filterOperandValue = value;
    // this.filterOperandButtonStatus = true;
    let count = this.filterPanels.length;
    let index: number = this.filterPanels.indexOf(panel);
    this.logicalOperatordisable = true;
    panel.filterOperands = value;

    if (
      this.configCache &&
      this.configCache.config &&
      this.configCache.config.filter_operands &&
      index !== -1
    ) {
      this.changeMade = true;
      this.configCache.config.filter_operands[index] = value;
    }
  }

  isConfigValid() {    
    if (!this.configCache || !this.configCache.config || !Array.isArray(this.configCache.config.filter_values) || this.configCache.config.filter_values.length === 0) {
      return false;
    }

    for (const item of this.configCache.config.filter_values) {
      if (!item.column_name || !item.value || !item.operator || !item.data_type) {
        this.toaster.info('Please fill out all fields before adding a new parameter', '', {
          positionClass: 'custom-toast-position'
        });
        return false;
      }
    }

    if (this.configCache.config.filter_operands.length != this.configCache.config.filter_values.length) {
      this.toaster.info('Please fill out the logical operator field', '', {
        positionClass: 'custom-toast-position'
      });
      return false;
    }

    if (this.configCache.config) {
      const newId = this.filterPanels.length;
      const newFilterPanel = new FilterPanel();
      newFilterPanel.id = newId;
      this.filterPanels.push(newFilterPanel);
      this.configCache.config.filter_values.push(new FilterValues('', '', '', ''));
      this.logicalOperatordisable = false;
      this.changeMade = false;
    } else {
      console.error('ConfigCache is not initialized.');
    }
    return true;
  }

  removeFilterPanel(id: number) {
    if (this.configCache) {
      const index = this.filterPanels.findIndex((panel) => panel.id === id);
      this.changeMade = true;
      this.filterPanels.splice(index, 1);
      this.configCache.config?.filter_values.splice(index, 1);
      if (this.filterPanels.length === 0) {
        this.newFilterPanel();
      }
    }
  }

  newFilterPanel() {
    const newId = this.filterPanels.length + 1;
    const newFilterPanel = new FilterPanel();
    newFilterPanel.id = newId;
    this.filterPanels.push(newFilterPanel);
  }

  async getFilterWidgetFields() {
    let result;
    if (this.datasetId) {
      this.columnsNames = await this.apiService.getFilterWidgetFields(
        this.siteId,
        this.projectId,
        this.datasetId,
      );
      this.statisticalData = this.columnsNames.data_column_types
     
      // result = this.columnsNames;
      // this.valueType = Array.from(
      //   new Set(
      //     this.columnsNames.data_column_types.map((stat: any) => stat.column_type),
      //   ),
      // );
      // this.columnsNames = this.columnsNames.data_column_types.reduce(
      //   (acc: string[], session: any) => {
      //     return acc.concat(session.column_names);
      //   },
      //   [],
      // );
      this.columnsNamesData = Object.keys(this.columnsNames.data_column_types);
      this.columnsNames = Object.keys(this.columnsNames.data_column_types);
      // this.statisticalData = this.columnsNames.statistics
      // result = this.columnsNames;
      // this.valueType = Array.from(
      //   new Set(
      //     this.columnsNames.statistics.map((stat: any) => stat.column_type),
      //   ),
      // );
      // this.columnsNames = this.columnsNames.statistics.reduce(
      //   (acc: string[], session: any) => {
      //     return acc.concat(session.column_names);
      //   },
      //   [],
      // );
      // this.columnsNamesData = [...this.columnsNames]

      // if (result && Array.isArray(result.statistics)) {
      //   result.statistics.forEach((stat: any) => {
      //     if (stat.column_names && Array.isArray(stat.column_names)) {
      //       stat.column_names.forEach((columnName: string) => {
      //         this.columnNamesWithTypes.push({
      //           column_name: columnName,
      //           column_type: stat.column_type,
      //         });
      //       });
      //     }
      //   });
      // }
      // filterPanel.filterValues.column_name = this.columnsNames
      // this.filterPanels.push(filterPanel);
    }
  }

  resetFilters() { }

  initializeInformation() {
    this.data = {
      type: this.widgetControl?.Widget.type,
      description: 'Filtering allows users to quickly subset their data based on specific criteria',
      version: '1.0',
    };
  }

  get widgetInput(): string | undefined {
    return this.inputName;
  }

  set widgetInput(value: string | undefined) {
    this.updateInputWidget = value;
    this.inputName = value;
    this.changeMade = true;
  }

  get widgetOutput(): string | undefined {
    return this.outputName;
  }

  set widgetOutput(value: string | undefined) {
    this.outputName = value;
    this.changeMade = true;
  }

  setSelectedInputWidget(widget: Widget) {
    this.changeMade = true;
    this.selectedInputWidget = widget;
    this.getDataseOfConnectedWidgetResult();
  }

  getSelectedInputWidget(): Widget | undefined {
    return this.selectedInputWidget;
  }

  getWidgetOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let outputConfig: InputOutputConfig = widget.outputs[0];
      return outputConfig.name!;
    }

    return 'Not Set';
  }

  onAppSettingsUpdated() {
    this.changeMade = true;
  }

  onSave() {
    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.changeMade = false;
    this.settingsComponent?.SaveAppSettings();
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

    if (this.selectedInputWidget) {
      let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
      inputOutputConfig.name = this.selectedInputWidget.outputs[0].name;
      inputOutputConfig.urn = this.selectedInputWidget.urn;
      if (this.widgetControl) {
        this.widgetControl.Widget.inputs.length = 0;
        this.widgetControl.Widget.inputs.push(inputOutputConfig);
      }
    }
  }

  onCancel() {
    this.inputName = undefined;
    this.outputName = undefined;
    this.settingsComponent.RevertAppSetting();
    // Deep clone to prevent updates from modifying original
    this.configCache = JSON.parse(JSON.stringify(this.config));
    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
      if (this.widgetControl.Widget.inputs.length) {
        this.inputName = this.widgetControl.Widget.inputs[0].name;
      }
    }
    this.changeMade = false;
    this.createFilterUX();
    this.loadSelectedInputWidget();
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

  openFilterSelectionDialog(index: number) {
    let config = this.configCache?.config;
    var data: any = null;

    if (config && config.filter_values) {
      data = {
        "config": config.filter_values[index],
        "dataset_id": this.datasetId
      }
    }

    if (data) {
      this.dialogRef = this.dialog.open(FilterSelectionConfigComponent, {
        width: '95vw',
        maxWidth: '95vw',
        height: '95%',
        data: data
      });
      this.dialogRef.afterClosed().subscribe((result) => {
        let configCopy = this.configCache?.config;

        if (this.configCache && configCopy) {
          if (result && result.selected_values) {
            // when we allow multi select, this logic needs to be changed
            configCopy.filter_values[index].value = result.selected_values[0];
          }
          this.configCache.config = config;
          this.changeMade = true;
        }

        this.dialogRef = null;
        this.cdr.detectChanges();
      });
    }
    
  }
}
