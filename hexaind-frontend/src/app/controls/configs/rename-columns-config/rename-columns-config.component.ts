import { Component, OnInit, ViewChild, ViewContainerRef } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ConfigService, WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ApiService } from 'src/app/services/api.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { SettingsComponent } from '../settings/settings.component';
import { MatTableDataSource } from '@angular/material/table';
import { InputOutputConfig, RenameColumnsModel, RenameColumnsWidgetConfig, Widget, WidgetType } from 'src/app/models/workflow-models';
import { DataPreviewService } from 'src/app/dialogs/data-preview/services/data-preview.service';
import { MatDialog } from '@angular/material/dialog';
import { ColumnDropDownComponent } from 'src/app/util-components/column-drop-down/column-drop-down.component';

interface ColumnToSelect {
  name: string;
  checked: boolean;
}

interface ColumnsToRename {
  old_name: string;
  new_name: string;
  checked: boolean;
}

@Component({
  selector: 'app-rename-columns-config',
  templateUrl: './rename-columns-config.component.html',
  styleUrls: ['./rename-columns-config.component.less']
})
export class RenameColumnsConfigComponent implements OnInit {
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
  config: RenameColumnsWidgetConfig | undefined = undefined;
  configCache: RenameColumnsWidgetConfig | undefined = undefined;
  columnNamesWithTypes: any = [];
  columnsNames: any;
  valueType: any;

  matTabNames = [
    {name: "Information", isUserInputNeeded: false},
    {name: "Inputs", isUserInputNeeded: true},
    {name: "Outputs", isUserInputNeeded: false},
    {name: "Parameters", isUserInputNeeded: true},
    {name: "Settings", isUserInputNeeded: false}
  ];

  columnsList: ColumnToSelect[] = [];
  columnsDataSource!: MatTableDataSource<ColumnToSelect>;
  columnsFilterWord: string = "";

  isAllColumnsChecked = false;
  isAllSelectedColumnsChecked = false;
  prevWidgetURN: any;

  renameList: RenameColumnsModel[] = [];
  renameColumnsDataSource!: MatTableDataSource<ColumnsToRename>;
  renameColumnsList: ColumnsToRename[] = [];

  columnNamesAndTypes: Record<string, string> = {};

  DATASET: string = "DATASET";
  isLoadingMetadata = false

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    public dialog: MatDialog,
    public sharedDataService: SharedDataService,
    private configService: ConfigService,
    private apiService: ApiService,
    public toaster: ToastrService,
    public dataPreviewService: DataPreviewService,
    private viewContainerRef: ViewContainerRef
  ) {

    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.siteId = this.configService.SelectedSiteId;
    this.projectId = this.configService.SelectedProjectId;
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.sessionId = this.workflowCanvasService.SelectedWorkflowSession?._id;

    if (this.widgetControl) {
      this.config = this.widgetControl.Widget.config as RenameColumnsWidgetConfig;

      if (this.config) {
        this.config.widget_type = WidgetType.RENAME_COLUMNS;
        this.configCache = JSON.parse(JSON.stringify(this.config));
        this.outputName = this.widgetControl.Widget.outputs[0].name;

        if (this.config.config) {
          this.renameList = this.config.config?.columns_to_rename && Object.entries(this.config.config?.columns_to_rename).map(([old_name, new_name]) => ({
            old_name,
            new_name
          }));
          if (this.renameList) {
            this.renameColumnsList = this.renameList.map((item: RenameColumnsModel) => ({
              old_name: item.old_name,
              new_name: item.new_name,
              checked: false
            }));
            this.renameColumnsDataSource = new MatTableDataSource(this.renameColumnsList);
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
    
    // else {
    //   if (this.inputWidgets.length === 1) {
    //     this.selectedInputWidget = this.inputWidgets[0];
    //     this.selectedInputWidgetIndex = 0;
    //     this.prevWidgetURN = this.inputWidgets[this.selectedInputWidgetIndex].urn;
    //     this.onSave();
    //     this.getDataSetId();
    //     this.getFieldsListFromData();
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
      description: 'Rename Columns allows users to rename columns',
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
        this.convertColumnNamesToRenameToDisplay();
        this.getOverviewOfSelectedColumns()
        this.isLoadingMetadata = false
      })
      .catch(error => {
        console.error('Failed to fetch metadata:', error);
        // this.resetSelectedList();
      });
    }
  }

  resetSelectedList() {
    this.renameList = [];
    this.renameColumnsList = [];
    this.renameColumnsDataSource = new MatTableDataSource(this.renameColumnsList);
  }

  validateAndResetSelectedList() {
    let isValid = true;

    if (!this.columnsNames || this.columnsNames.length===0) {
      // this.resetSelectedList();
      return;
    }
    
    if(this.renameList)
      for (let item of this.renameList) {
        if (!this.columnsNames.includes(item.old_name)) {
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
    const selectedSet = new Set(this.renameList);
    const selectedOldNames = new Set([...selectedSet].map(item => item.old_name));

    if (this.columnsNames) {
      this.columnsList = this.columnsNames
      .filter((name: string) => !selectedOldNames.has(name))
      .map((name: string) => ({
        name: name,
        checked: false
      }));
  
      this.columnsDataSource = new MatTableDataSource(this.columnsList);
    }
  }

  convertColumnNamesToRenameToDisplay() {
    if (this.renameList) {
      this.renameColumnsList = this.renameList
      .map((item: RenameColumnsModel) => ({ 
        old_name: item.old_name, 
        new_name: item.new_name,
        checked: false 
      }));
  
      this.renameColumnsDataSource = new MatTableDataSource(this.renameColumnsList);
    }
  }

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

  enableSave() {
    this.changeMade = true;
  }
  
  onSave() {
    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.changeMade = false;

    if (this.configCache && this.configCache.config) {
      this.configCache.config.columns_to_rename = this.renameColumnsList.reduce((item, {      old_name, new_name }) => {
        item[old_name] = new_name;
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
    this.isAllSelectedColumnsChecked = this.renameColumnsList.every(element => element.checked);
  }

  toggleAllSelectedColumns(event: any) {
    const checked = event.checked;
    this.renameColumnsList.forEach(element => {
      element.checked = checked; 
    });
    this.renameColumnsDataSource = new MatTableDataSource(this.renameColumnsList);
  }

  applyFilterOnColumns() {
    this.resetCheckedInColumnsList();
    this.isAllColumnsChecked = false;
    this.columnsDataSource.filter = this.columnsFilterWord.trim().toLowerCase();
  }

  // applyFilterOnSelectedColumns() {
  //   this.resetCheckedInSelectedColumnsList();
  //   this.isAllSelectedColumnsChecked = false;
  //   this.selectedColumnsDataSource.filter = this.selectedColumnsFilterWord.trim().toLowerCase();
  // }

  // when user changes filter work, the columns are unchecked - Available columns
  resetCheckedInColumnsList() {
    this.columnsList = this.columnsList.map(column => ({
      ...column, 
      checked: false 
    }));
    this.columnsDataSource = new MatTableDataSource(this.columnsList);
  }

  resetCheckedInSelectedColumnsList() {
    this.renameColumnsList = this.renameColumnsList.map(column => ({
      ...column, 
      checked: false 
    }));
    this.renameColumnsDataSource = new MatTableDataSource(this.renameColumnsList);
  }

  onSelectColumns() {
    const columnsToSelect = this.columnsList
    .filter(column => column.checked)
    .map(column => ({
      old_name: column.name,
      new_name: column.name, 
      checked: false 
    }));
    this.renameColumnsList = [
      ...this.renameColumnsList,
      ...columnsToSelect
    ];
    this.columnsList = this.columnsList.filter(column => !column.checked);
    this.renameColumnsDataSource = new MatTableDataSource(this.renameColumnsList);
    this.columnsDataSource = new MatTableDataSource(this.columnsList);

    if (columnsToSelect.length>0) this.changeMade = true;
    this.isAllColumnsChecked = false;
    this.columnsFilterWord = "";
  }

  onUnselectColumns() {
    const columnsToUnselect = this.renameColumnsList
    .filter(column => column.checked)
    .map(column => ({
      name: column.old_name,
      checked: false 
    }));
    this.columnsList = [
      ...this.columnsList,
      ...columnsToUnselect
    ];
    this.renameColumnsList = this.renameColumnsList.filter(column => !column.checked);
    this.renameColumnsDataSource = new MatTableDataSource(this.renameColumnsList);
    this.columnsDataSource = new MatTableDataSource(this.columnsList);

    if (columnsToUnselect.length>0) this.changeMade = true;
    this.isAllSelectedColumnsChecked = false;
  }


  openColumnDropDown() {
    const dialogRef = this.dialog.open(ColumnDropDownComponent, {
      width: '70vw',
      height: '90vh',
      data: {
        columnsList: this.columnsList,
        selectedColumnsList: this.renameColumnsList,
        infoRegardingTheColumns:"This is drop missing",
        widgetType: WidgetType.RENAME_COLUMNS,
        logicForMovingDataFromUnselectedToSelect: (arrayOfColumns: any) => {
          return arrayOfColumns
          .filter((column: any) => column.checked)
          .map((column: any) => ({
            old_name: column.name,
            new_name: column.name, 
            checked: false 
          }));
        },
        logicForMovingDataFromSelectedToUnSelect: (arrayOfColumns: any) => {
          return arrayOfColumns
          .filter((column: any) => column.checked)
          .map((column: any) => ({
            name: column.old_name,
            checked: false 
          }));
        }
      },
    })
    
    dialogRef.afterClosed().subscribe((result) => {
      if(result.isSaved) {
        this.columnsList = result.columnsList
        this.renameColumnsList = result.selectedColumnList
        this.getOverviewOfSelectedColumns()
        this.onSave()
      }
    })
  }

  overviewOfSelectedColumns = ""
  getOverviewOfSelectedColumns() {

    if(this.renameColumnsList.length == 0) {
      this.overviewOfSelectedColumns = "Click on Configure for selecting the columns"
      return 
    }
    let overAllString = ""
    for(const element of this.renameColumnsList.slice(0,20)) {
      overAllString += element.old_name + " -> " + element.new_name + " ".repeat(10);

    }
    this.overviewOfSelectedColumns = overAllString
  }


}
