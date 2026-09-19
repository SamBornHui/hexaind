import { Component, OnInit, ViewChild } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ConfigService, WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ApiService } from 'src/app/services/api.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { DatatypeConversionWidgetConfig, InputOutputConfig, Widget, WidgetType } from 'src/app/models/workflow-models';
import { SettingsComponent } from '../settings/settings.component';
import { MatTableDataSource } from '@angular/material/table';
import { DataPreviewService } from 'src/app/dialogs/data-preview/services/data-preview.service';
import { ColumnDropDownComponent } from 'src/app/util-components/column-drop-down/column-drop-down.component';
import { MatDialog } from '@angular/material/dialog';


interface ColumnToSelect {
  name: string;
  type: string;
  checked: boolean;
}

interface ColumnsToChangeType {
  name: string;
  type: string;
  new_type: string
  checked: boolean;
}

interface ChangeDataTypeModel {
  name: string;
  type: string;
}

@Component({
  selector: 'app-datatype-conversion-config',
  templateUrl: './datatype-conversion-config.component.html',
  styleUrls: ['./datatype-conversion-config.component.less']
})
export class DatatypeConversionConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  changeMade: boolean = false;
  data = {};
  public widgetControl: WidgetControl | undefined = undefined;
  inputName: string | undefined = undefined;
  outputName: string | undefined = undefined;
  updateInputWidget: any;
  inputWidgets: Widget[] = [];
  selectedInputWidget: Widget | undefined = undefined;
  selectedInputWidgetIndex: number = -1;
  // dataset: any;
  datasetId: any;
  siteId: any;
  projectId: any;
  sessionId: any;
  config: DatatypeConversionWidgetConfig | undefined = undefined;
  configCache: DatatypeConversionWidgetConfig | undefined = undefined;
  columnNamesWithTypes: any = [];
  columnsNames: any;
  valueType: any;

  columnsList: ColumnToSelect[] = [];
  columnsDataSource!: MatTableDataSource<ColumnToSelect>;
  columnsFilterWord: string = "";
 
  changeTypeList: ChangeDataTypeModel[] = [];
  changeTypeColumnsDataSource!: MatTableDataSource<ColumnsToChangeType>;
  changeTypeColumnsList: ColumnsToChangeType[] = [];

  isAllColumnsChecked = false;
  isAllSelectedColumnsChecked = false;
  prevWidgetURN: any;
  columnNamesAndTypes: Record<string, any> = {};
  isLoadingMetadata = false

  datatypeOptions = [
    "INTEGER",
    "FLOAT",
    "STRING",
    "DATE",
    "DATETIME"

  ];

  matTabNames = [
    {name: "Information", isUserInputNeeded: false},
    {name: "Inputs", isUserInputNeeded: true},
    {name: "Outputs", isUserInputNeeded: false},
    {name: "Parameters", isUserInputNeeded: true},
    {name: "Settings", isUserInputNeeded: false}
  ];

  DATASET: string = "DATASET";

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    public sharedDataService: SharedDataService,
    public dialog: MatDialog,
    private configService: ConfigService,
    private apiService: ApiService,
    public toaster: ToastrService,
    public dataPreviewService: DataPreviewService
  ) {

    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.siteId = this.configService.SelectedSiteId;
    this.projectId = this.configService.SelectedProjectId;
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;

    this.sessionId = this.workflowCanvasService.SelectedWorkflowSession?._id;

    if (this.widgetControl) {
      this.config = this.widgetControl.Widget.config as DatatypeConversionWidgetConfig;

      if (this.config) {
        this.config.widget_type = WidgetType.DATATYPE_CONVERSION;
        this.configCache = JSON.parse(JSON.stringify(this.config));
        this.outputName = this.widgetControl.Widget.outputs[0].name;

        if (this.config.config) {
          this.changeTypeList = Object.entries(this.config.config.column_type_mapping).map(([name, type]) => ({
            name,
            type,
          }));
          if (this.changeTypeList) {
            this.changeTypeColumnsList = this.changeTypeList.map((item: ChangeDataTypeModel) => ({
              name: item.name,
              type: item.type,
              new_type: item.type,
              checked: false
            }));
            this.changeTypeColumnsDataSource = new MatTableDataSource(this.changeTypeColumnsList);
          }
        }
      }

      if (this.widgetControl.Widget.inputs && this.widgetControl.Widget.inputs.length) {
        this.inputName = this.widgetControl.Widget.inputs[0].name;
      }
    }

  }

  ngOnInit(): void {
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
        this.loadSelectedInputWidget();
      }
    }
  }

  async getDataSetId() {
    if (this.siteId && this.projectId && this.sessionId && this.prevWidgetURN) {
      this.isLoadingMetadata = true
      this.apiService.GetPreviousTabularWidgetResults( this.siteId, this.projectId,
      this.sessionId, this.prevWidgetURN).then (prevWidgetResults => {
          if (this.selectedInputWidget) {
            this.datasetId = this.workflowCanvasService.getDataSetIdFromResults(prevWidgetResults,this.selectedInputWidget);
            if (this.datasetId) {
              this.getFieldsListFromData();
              return true;
            }
          }
          return false;
      })
      .catch(error => {
          // this.resetSelectedList();
          this.toaster.info("Please execute the previous widget to see the parameters")
      });
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
      if (this.selectedInputWidget) {
        let selectedWidgetUrn = this.selectedInputWidget.urn;
        this.selectedInputWidgetIndex = this.inputWidgets.findIndex(widget => widget.urn === selectedWidgetUrn)
        this.prevWidgetURN = this.inputWidgets[this.selectedInputWidgetIndex].urn;
        this.getDataSetId();
      }
    } 

    if (!this.selectedInputWidget) {
      // this.resetSelectedList();
    }

    // else {
    //   if (this.inputWidgets.length === 1) {
    //     this.selectedInputWidget = this.inputWidgets[0];
    //     this.selectedInputWidgetIndex = 0;
    //     this.prevWidgetURN = this.inputWidgets[this.selectedInputWidgetIndex].urn;
    //     this.getDataSetId();
    //     this.onSave();
    //   }
    // }
  }

  getInputingWidgetsOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let inputConfig: InputOutputConfig = widget.outputs[0];
      return inputConfig.name!;
    }
    return ""
  }

  initializeInformation() {
    this.data = {
      type: this.widgetControl?.Widget.type,
      description: 'Datatype conversion allows users to change datatype of a column',
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

  // getInputingWidgetsOutputName(inputOutputConfig: InputOutputConfig): string {
  //   return inputOutputConfig.name ?? '';
  // }

  get widgetOutput(): string | undefined {
    return this.outputName;
  }

  set widgetOutput(value: string | undefined) {
    this.outputName = value;
    this.changeMade = true;
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  setSelectedInputWidget(widget: Widget) {
    this.changeMade = true;
    this.selectedInputWidget = widget;
    let selectedWidgetUrn = widget.urn;
    this.selectedInputWidgetIndex = this.inputWidgets.findIndex(widget => widget.urn === selectedWidgetUrn)
    this.prevWidgetURN = this.inputWidgets[this.selectedInputWidgetIndex].urn;
    this.getDataSetId();
    // this.resetSelectedList();
  }

  resetSelectedList() {
    this.changeTypeList = [];
    this.changeTypeColumnsList = [];
    this.changeTypeColumnsDataSource = new MatTableDataSource(this.changeTypeColumnsList);
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

  onSave() {
    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.changeMade = false;

    if (this.configCache && this.configCache.config) {
      this.configCache.config.column_type_mapping = this.changeTypeColumnsList.reduce((item, { name, new_type }) => {
        item[name] = new_type;
        return item;
      }, {} as Record<string, string>);
    }

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

  onReset() {
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
    this.getFieldsListFromData();
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

  onAppSettingsUpdated() {
    this.changeMade = true;
  }

  async getFieldsListFromData() {
    // logic to read column names from meta data 
    if (this.datasetId) {
      this.dataPreviewService.getMetadata(this.datasetId).then(response => {
        let result = response;
        this.columnNamesAndTypes = result.data_column_types;

        if (this.columnNamesAndTypes && Object.keys(this.columnNamesAndTypes).length > 0) {
          this.columnsNames = Object.keys(this.columnNamesAndTypes);
        }

        this.convertColumnNamesToDisplay();
        this.convertColumnNamesToChangeTypeToDisplay();
        this.generateOverviewOfSelectedColumns()
        this.isLoadingMetadata = false
      })
      .catch(error => {
        console.error('Failed to fetch metadata:', error);
        // this.resetSelectedList();
      });
    }
  }

  validateAndResetSelectedList() {
    let isValid = true;

    if (!this.columnNamesAndTypes || Object.keys(this.columnNamesAndTypes).length === 0) {
      // this.resetSelectedList();
      return;
    }

    for (let item of this.changeTypeList) {
      if (!(item.name in this.columnNamesAndTypes)) {
        isValid = false;
        break;
      }
    }

    if (!isValid) {
      this.resetSelectedList();
    }
  }

  convertColumnNamesToDisplay() {
    this.validateAndResetSelectedList();
    const selectedSet = new Set(this.changeTypeList);
    const selectedNames = new Set([...selectedSet].map(item => item.name));
    if (this.columnNamesAndTypes) {
      this.columnsList = Object.entries(this.columnNamesAndTypes)
        .filter(([name]) => !selectedNames.has(name)) // Filter out names in changeTypeList
        .map(([name, value]) => ({
          name,
          type: this.convertTypeToDisplay(value.datatype),
          checked: false 
        }));
  
      this.columnsDataSource = new MatTableDataSource(this.columnsList);
    }
  }

  convertColumnNamesToChangeTypeToDisplay() {
    if (this.changeTypeList) {
      this.changeTypeColumnsList = this.changeTypeList
      .map((item: ChangeDataTypeModel) => ({ 
        name: item.name, 
        type: this.convertTypeToDisplay(this.columnNamesAndTypes[item.name].datatype),
        new_type: this.convertTypeToDisplay(item.type),
        checked: false 
      }));
  
      this.changeTypeColumnsDataSource = new MatTableDataSource(this.changeTypeColumnsList);
    }
  }

  onSelectColumns() {
    const columnsToSelect = this.columnsList
    .filter(column => column.checked)
    .map(column => ({
      name: column.name,
      type: column.type, 
      new_type: column.type,
      checked: false 
    }));
    this.changeTypeColumnsList = [
      ...this.changeTypeColumnsList,
      ...columnsToSelect
    ];
    this.columnsList = this.columnsList.filter(column => !column.checked);
    this.changeTypeColumnsDataSource = new MatTableDataSource(this.changeTypeColumnsList);
    this.columnsDataSource = new MatTableDataSource(this.columnsList);
    if (columnsToSelect.length>0) this.changeMade = true;
    this.isAllColumnsChecked = false;
    this.columnsFilterWord = "";
  }

  onUnselectColumns() {
    const columnsToUnselect = this.changeTypeColumnsList
    .filter(column => column.checked)
    .map(column => ({
      name: column.name,
      type: column.type,
      checked: false 
    }));
    this.columnsList = [
      ...this.columnsList,
      ...columnsToUnselect
    ];
    this.changeTypeColumnsList = this.changeTypeColumnsList.filter(column => !column.checked);
    this.changeTypeColumnsDataSource = new MatTableDataSource(this.changeTypeColumnsList);
    this.columnsDataSource = new MatTableDataSource(this.columnsList);
    if (columnsToUnselect.length>0) this.changeMade = true;
    this.isAllSelectedColumnsChecked = false;
  }

   // when user changes filter work, the columns are unchecked - Available columns
   resetCheckedInColumnsList() {
    this.columnsList = this.columnsList.map(column => ({
      ...column, 
      checked: false 
    }));
    this.columnsDataSource = new MatTableDataSource(this.columnsList);
  }

  // when user changes filter work, the columns are unchecked - Selected columns
  resetCheckedInSelectedColumnsList() {
    this.changeTypeColumnsList = this.changeTypeColumnsList.map(column => ({
      ...column, 
      checked: false 
    }));
    this.changeTypeColumnsDataSource = new MatTableDataSource(this.changeTypeColumnsList);
  }

  applyFilterOnColumns() {
    this.resetCheckedInColumnsList();
    this.isAllColumnsChecked = false;
    this.columnsDataSource.filter = this.columnsFilterWord.trim().toLowerCase();
  }

  onColumnClicked() {
    this.checkIfAllColumnsChecked();
  }

  checkIfAllColumnsChecked() {
    this.isAllColumnsChecked = this.columnsList.every(element => element.checked);
  }

  toggleAllColumns(event: any) {
    const checked = event.checked;
    const filteredColumnsList = this.columnsDataSource.filteredData.slice();
    this.columnsList.forEach(element => {
      if (filteredColumnsList.some(filteredElement => filteredElement.name === element.name)) {
        element.checked = checked; 
      }
    });
  }

  onSelectedColumnClicked() {
    this.checkIfAllSelectedColumnsChecked();
  }

  checkIfAllSelectedColumnsChecked() {
    this.isAllSelectedColumnsChecked = this.changeTypeColumnsList.every(element => element.checked);
  }

  toggleAllSelectedColumns(event: any) {
    const checked = event.checked;
    const filteredSelectedColumnsList = this.changeTypeColumnsDataSource.filteredData.slice();
    this.changeTypeColumnsList.forEach(element => {
      if (filteredSelectedColumnsList.some(filteredElement => filteredElement.name === element.name)) {
        element.checked = checked; 
      }
    });
  }

  enableSave() {
    this.changeMade = true;
  }

  convertTypeToDisplay(datatype: string) {
    const typeMapping: { [key: string]: string } = {
      "int16": "INTEGER",
      "int32": "INTEGER",
      "int64": "INTEGER",
      "float16": "FLOAT",
      "float32": "FLOAT",
      "float64": "FLOAT",
      "object": "STRING",
      "string": "STRING",
      "datetime64[ns]": "DATETIME"
  }
  
    return typeMapping[datatype] || datatype; 
  }


  openColumnDropDown() {

    const dialogRef = this.dialog.open(ColumnDropDownComponent, {
      width: '70vw',
      height: '90vh',
      data: {
        columnsList: this.columnsList,
        selectedColumnsList: this.changeTypeColumnsList,
        infoRegardingTheColumns:"This is drop missing",
        widgetType: WidgetType.DATATYPE_CONVERSION,
        logicForMovingDataFromUnselectedToSelect: (arrayOfColumns: any) => {
          return arrayOfColumns
          .filter((column: any) => column.checked)
          .map((column: { name: any; type: any; }) => ({
            name: column.name,
            type: column.type, 
            new_type: column.type,
            checked: false 
          }));
        },
        logicForMovingDataFromSelectedToUnSelect: (arrayOfColumns: any) => {
          return arrayOfColumns
          .filter((column: any) => column.checked)
          .map((column: { name: any; type: any; }) => ({
            name: column.name,
            type: column.type,
            checked: false 
          }));
        }
      },
    })

    dialogRef.afterClosed().subscribe((result) => {
      if(result.isSaved) {
        this.columnsList = result.columnsList
        this.changeTypeColumnsList = result.selectedColumnList
        this.generateOverviewOfSelectedColumns()
        this.onSave()
      }
    })

  }

  overviewOfSelectedColumns = ""
  generateOverviewOfSelectedColumns() {
    
    if(this.changeTypeColumnsList.length == 0) {
      this.overviewOfSelectedColumns = "Click on Configure for selecting the columns"
      return 
    }
    let overAllString = ""
    for (const element of this.changeTypeColumnsList.slice(0, 20)) {
      overAllString += element.name + "  " + element.type + " -> " + element.new_type + " ".repeat(8);
    }
    this.overviewOfSelectedColumns = overAllString
  }

}
