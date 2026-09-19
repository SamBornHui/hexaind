import { Component, OnInit, ViewChild } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ConfigService, WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ApiService } from 'src/app/services/api.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { DropColumnsWidgetConfig, InputOutputConfig, Widget, WidgetType } from 'src/app/models/workflow-models';
import { SettingsComponent } from '../settings/settings.component';
import { MatTableDataSource } from '@angular/material/table';
import { DataPreviewService } from 'src/app/dialogs/data-preview/services/data-preview.service';
import { ColumnDropDownComponent } from 'src/app/util-components/column-drop-down/column-drop-down.component';
import { MatDialog } from '@angular/material/dialog';


interface ColumnToSelect {
  name: string;
  checked: boolean;
}

@Component({
  selector: 'app-drop-columns-config',
  templateUrl: './drop-columns-config.component.html',
  styleUrls: ['./drop-columns-config.component.less']
})
export class DropColumnsConfigComponent {
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
  config: DropColumnsWidgetConfig | undefined = undefined;
  configCache: DropColumnsWidgetConfig | undefined = undefined;
  columnNamesWithTypes: any = [];
  columnsNames: any;
  valueType: any;

  columnsList: ColumnToSelect[] = [];
  selectedColumnsList: ColumnToSelect[] = [];
  selectedList: string[] = [];

  columnsDataSource!: any;
  selectedColumnsDataSource!: any;
  columnsFilterWord: string = "";
  selectedColumnsFilterWord: string = "";
  columnNamesAndTypes: Record<string, string> = {};

  isAllColumnsChecked = false;
  isAllSelectedColumnsChecked = false;
  isLoadingMetadata = false

  prevWidgetURN: any;

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
    private configService: ConfigService,
    public dialog: MatDialog,
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
      this.config = this.widgetControl.Widget.config as DropColumnsWidgetConfig;

      if (this.config) {
        this.config.widget_type = WidgetType.DROP_COLUMNS;
        this.configCache = JSON.parse(JSON.stringify(this.config));
        this.outputName = this.widgetControl.Widget.outputs[0].name;

        if (this.config.config) {
          this.selectedList = this.config.config?.selected_columns;
          if (this.selectedList) {
            this.selectedColumnsList = this.selectedList.map((item: string) => ({
              name: item,
              checked: false
            }));
            this.selectedColumnsDataSource = this.selectedColumnsList;
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
      description: 'Drop Columns allows users to drop columns as per selection',
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
    this.selectedList = [];
    this.selectedColumnsList = [];
    this.selectedColumnsDataSource = this.selectedColumnsList;
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
      this.configCache.config.selected_columns = this.selectedColumnsList.map(column => column.name);
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
    this.resetSelectedColumnsList();
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

  resetSelectedColumnsList() {
    if (this.config?.config) {
      this.selectedList = this.config.config?.selected_columns;
      if (this.selectedList) {
        this.selectedColumnsList = this.selectedList.map((item: string) => ({
          name: item,
          checked: false
        }));
        } 
    } else this.selectedColumnsList = [];
    this.selectedColumnsDataSource = this.selectedColumnsList;
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
        this.getOverviewOfSelectedColumns()
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

    if (!this.columnsNames || this.columnsNames.length===0) {
      // this.resetSelectedList();
      return;
    }

    for (let item of this.selectedList) {
      if (!this.columnsNames.includes(item)) {
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
    const selectedSet = new Set(this.selectedList);

    if (this.columnsNames) {
      this.columnsList = this.columnsNames
      .filter((name: string) => !selectedSet.has(name))
      .map((name: string) => ({ 
        name: name, 
        checked: false 
      }));
  
      this.columnsDataSource = this.columnsList;
    }
  }

  onSelectColumns() {
    const columnsToSelect = this.columnsList
    .filter(column => column.checked)
    .map(column => ({
      ...column, 
      checked: false 
    }));
    this.selectedColumnsList = [
      ...this.selectedColumnsList,
      ...columnsToSelect
    ];
    this.columnsList = this.columnsList.filter(column => !column.checked);
    this.selectedColumnsDataSource = this.selectedColumnsList;
    this.columnsDataSource = this.columnsList;

    if (columnsToSelect.length>0) this.changeMade = true;
    this.isAllColumnsChecked = false;
    this.columnsFilterWord = "";
  }

  onUnselectColumns() {
    const columnsToUnselect = this.selectedColumnsList
    .filter(column => column.checked)
    .map(column => ({
      ...column, 
      checked: false 
    }));
    this.columnsList = [
      ...this.columnsList,
      ...columnsToUnselect
    ];
    this.selectedColumnsList = this.selectedColumnsList.filter(column => !column.checked);
    this.selectedColumnsDataSource = this.selectedColumnsList;
    this.columnsDataSource = this.columnsList;

    if (columnsToUnselect.length>0) this.changeMade = true;
    this.isAllSelectedColumnsChecked = false;
    this.selectedColumnsFilterWord = "";
  }

   // when user changes filter work, the columns are unchecked - Available columns
   resetCheckedInColumnsList() {
    this.columnsList = this.columnsList.map(column => ({
      ...column, 
      checked: false 
    }));
    this.columnsDataSource = this.columnsList;
  }

  // when user changes filter work, the columns are unchecked - Selected columns
  resetCheckedInSelectedColumnsList() {
    this.selectedColumnsList = this.selectedColumnsList.map(column => ({
      ...column, 
      checked: false 
    }));
    this.selectedColumnsDataSource = this.selectedColumnsList;
  }

  applyFilterOnColumns() {
    this.resetCheckedInColumnsList();
    this.isAllColumnsChecked = false;
    this.columnsDataSource = this.columnsDataSource.filter((item: any) => item.name.includes(this.columnsFilterWord));;
  }

  applyFilterOnSelectedColumns() {
    this.resetCheckedInSelectedColumnsList();
    this.isAllSelectedColumnsChecked = false;
    this.selectedColumnsDataSource = this.selectedColumnsDataSource.filter((item: any) => item.name.includes(this.selectedColumnsFilterWord));
  }

  onColumnClicked() {
    this.checkIfAllColumnsChecked();
  }

  checkIfAllColumnsChecked() {
    this.isAllColumnsChecked = this.columnsList.every(element => element.checked);
  }

  toggleAllColumns(event: any) {
    const checked = event.checked;
    const filteredColumnsList = this.columnsDataSource.slice();
    this.columnsList.forEach(element => {
      if (filteredColumnsList.some((filteredElement: { name: string; }) => filteredElement.name === element.name)) {
        element.checked = checked; 
      }
    });
  }

  onSelectedColumnClicked() {
    this.checkIfAllSelectedColumnsChecked();
  }

  checkIfAllSelectedColumnsChecked() {
    this.isAllSelectedColumnsChecked = this.selectedColumnsList.every(element => element.checked);
  }

  toggleAllSelectedColumns(event: any) {
    const checked = event.checked;
    const filteredSelectedColumnsList = this.selectedColumnsDataSource.slice();
    this.selectedColumnsList.forEach(element => {
      if (filteredSelectedColumnsList.some((filteredElement: { name: string; }) => filteredElement.name === element.name)) {
        element.checked = checked; 
      }
    });
  }

  openColumnDropDown() {

    const dialogRef = this.dialog.open(ColumnDropDownComponent, {
      width: '70vw',
      height: '90vh',
      data: {
        columnsList: this.columnsList,
        selectedColumnsList: this.selectedColumnsList,
        infoRegardingTheColumns:"",
        widgetType: WidgetType.DROP_COLUMNS,
      },
    })

    dialogRef.afterClosed().subscribe((result:any) => {
      if(result.isSaved) {
        this.columnsList = result.columnsList
        this.selectedColumnsList = result.selectedColumnList
        this.getOverviewOfSelectedColumns()
        this.onSave()
      }
    })

  }

  overviewOfSelectedColumns = ""
  getOverviewOfSelectedColumns() {

    if(this.selectedColumnsList.length == 0) {
      this.overviewOfSelectedColumns = "Click on Configure for selecting the columns"
      return
    }
    let overAllString = ""
    for (const element of this.selectedColumnsList.slice(0,20)) {
      overAllString += element.name + " ".repeat(8);
    }
    this.overviewOfSelectedColumns = overAllString
  }
  
}
