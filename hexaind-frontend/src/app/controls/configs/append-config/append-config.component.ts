import { Component, TemplateRef, ViewChild } from '@angular/core';
import {
  AppendWidgetConfig,
  DataCopyWidgetConfig,
  InputOutputConfig,
  LocalFileConfiguration,
  Widget,
  WidgetType,
} from 'src/app/models/workflow-models';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { FormGroup } from '@angular/forms';
import { BigQueryPreviewComponent } from 'src/app/dialogs/big-query-preview/big-query-preview.component';
import { MatDialog } from '@angular/material/dialog';
import { SettingsComponent } from '../settings/settings.component';
import { NotificationComponent } from '../../notification/notification.component';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { FormControl } from '@angular/forms';
import { ApiService } from 'src/app/services/api.service';

@Component({
  selector: 'app-append',
  templateUrl: './append-config.component.html',
  styleUrls: ['./append-config.component.less'],
})
export class AppendComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  @ViewChild('notification') notificationComponent!: NotificationComponent;
  @ViewChild('moreDialog')
  moreDialog!: TemplateRef<any>;
  @ViewChild('missingDialog')missingDialog!: TemplateRef<any>;
  appendForm!: FormGroup;
  changeMade: boolean = true;
  config: AppendWidgetConfig | undefined = undefined;
  configCache: AppendWidgetConfig | undefined = undefined;
  outputName: string | undefined = undefined;

  allWidgets: any;
  dataSourceOptions: any[] = [];
  enableAppend: boolean = true;
  selectedInputWidget1: any;
  selectedInputWidget2: any;
  inputWidgets: Widget[] = [];
  widgetControl: WidgetControl | undefined = undefined;
  data = {};
  widget: Widget | undefined = undefined;
  isOutputChanged: boolean = false;
  inputsCount: number | undefined;
  inputIndexes: number[] = [];
  selectionChangedFromInputTab: boolean = true;
  allOutputs: InputOutputConfig[] = [];
  misMatchResult : any;
  misMatchResultDetails: any;
  misMatchColumns: any[] = [];
  getmisMatchColumns: any[]=[];
  misMatchBool: boolean = false;
  missingColumns: any[]= [];
  uncommoncolumns: any[]= [];
  savedMisMatchResult: any[]=[];
  selectFormControl = new FormControl();
  userInteracted = false;
  DataTypes: any = [];
  selectedInputsStatus: boolean = false;
  

  constructor(
    private editWorkflowService: WorkflowCanvasService,
    private dialog: MatDialog,
    public sharedDataService: SharedDataService,
    public workflowCanvasService: WorkflowCanvasService,
    private apiService: ApiService,
  ) {
    if (!this.editWorkflowService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.editWorkflowService.selectedWidgetControl;
    this.widget = this.widgetControl.Widget;
    this.config = this.widgetControl.Widget.config as AppendWidgetConfig;
    this.config.widget_type = WidgetType.APPEND;  
    this.configCache = JSON.parse(JSON.stringify(this.config));
  }

  async ngOnInit() {
    this.initializeInformation();
    this.savedMisMatchResult = this.config!.column_type_pref_list;
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.editWorkflowService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );

      // Remove any widgets that dont have outputs.
      if (this.inputWidgets && this.inputWidgets.length > 0) {
        this.inputWidgets = this.inputWidgets.filter(
          (widget) => widget.outputs.length > 0,
        );
      }

      this.setSelectedInputWidgets();
      if (this.widgetControl.Widget.outputs.length) {
        this.outputName = this.widgetControl.Widget.outputs[0].name;
      }
    }
    this.saveButton();    
    this.getMisMatchResult();
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  getDisplayedValues(details: Array<any>): string {
    return details.slice(0, 2)
      .map(widget => `${widget.name} (${widget.data_type})`)
      .join(', ');
  }

  // Open the popup dialog with the remaining values
  openMoreDialog(details: Array<any>): void {
    this.dialog.open(this.moreDialog, {
      data:  details.slice(2),
      width: '300px',
      height: 'auto',
    });
  }

  getMissingDisplayedValues(details: Array<any>): string {
    return details.slice(0, 3)
      .map(widget => widget)
      .join(', ');
  }

  openMissingDialog(details: Array<any>): void {
    this.dialog.open(this.missingDialog, {
      data:  details.slice(3),
      width: '300px',
      height: 'auto',
    });
  }

  displayMisMatchvalues(details: Array<any>){
    return details.slice(2).length;
  }

  displayMorevalues(details: Array<any>){
    return details.slice(3).length;
  }

  saveButton(){
    //console.log("this.allOutputs.length: ", this.allOutputs, this.widgetControl!.Widget.inputs)
    if(this.widgetControl!.Widget.inputs.length === this.allOutputs.length){
      this.widgetControl!.Widget.inputs.map((input: any) => {
        this.allOutputs.filter((col) => {
          if(col.urn !== input.urn){
            this.changeMade = true;
            this.selectedInputsStatus = true
            return;
          }else{
            this.changeMade = false;
          }
        });
      });
      
    }else{
      this.changeMade = true;
    }
  }

  userInputInteracted(){
    console.log("the input widget clicked...")
  }

  getSelectedInputWidget1(): any {
    return this.selectedInputWidget1;
  }

  getSelectedInputWidget2(): Widget | undefined {
    return this.selectedInputWidget2;
  }

  setSelectedInputWidget1(widget: Widget) {
    this.selectedInputWidget1 = widget;
    if (this.userInteracted) this.changeMade = true;
  }

  setSelectedInputWidget2(widget: Widget) {
    this.selectedInputWidget2 = widget;
    if (this.userInteracted) this.changeMade = true;
  }

  setSelectedDatasetId(event : Event){
    console.log("the selected dataset id: ",event)
    this.changeMade = true;
  }

  setSelectedInputDataType(event :Event, value : string){
    const index = this.DataTypes.findIndex((dataType: any) => dataType.column_name == value);
    const selectedPrefType = event;
    if (index !== -1) {
      this.DataTypes[index].pref_type = selectedPrefType;
    } else {
      this.DataTypes.push({ column_name: value, pref_type: selectedPrefType });
    }
    this.changeMade = true;
  }

  openPreveiwDialog(): void {
    const dialogRef = this.dialog.open(BigQueryPreviewComponent, {
      width: '1300px',
      height: '95%',
    });
    dialogRef.afterClosed().subscribe((result: any) => {
      console.log('Dialog closed');
    });
  }

  getDataCsvWidgetConfig(): Widget | null {
    let dataCsvActivityConfig: Widget = this.widgetControl?.Widget as Widget;

    return dataCsvActivityConfig;
  }


  // onIgnoreIndexChange(isChecked: boolean) {     
  //   this.ignore_index = isChecked;
  // }

  setPayload() {
    if (!this.config) {
      return;
    }
    this.config.user_id = 'temp_test_trans_user';
    this.config.max_rows = 0;
    this.config.ignore_index = true;
    this.config.output_dataset_name = this.widgetOutput;
    this.config.transform_type = WidgetType.APPEND;
    this.config.column_type_pref_list = [];
  }

  handleInputChange() {
    this.isOutputChanged = this.widgetOutput ? true : false;
  }

  saveOutput() {
    if (!this.config) {
      return;
    }
    this.config.output_dataset_name = this.widgetOutput;
    (this.config.max_rows = 0), (this.config.ignore_index = true);
    this.isOutputChanged = false;
  }

  setSelectedInputWidgets() {
    this.allOutputs = this.inputWidgets.flatMap((widget) => widget.outputs);
    if (this.widgetControl) {
      if (this.widgetControl.Widget.inputs.length > 0) {
        this.selectedInputWidget1 = this.allOutputs.find(
          (t) =>
            t.urn === this.widgetControl?.Widget.inputs[0].urn &&
            t.name === this.widgetControl?.Widget.inputs[0].name,
        );
      } else {
        this.selectedInputWidget1 = undefined;
      }
      if (this.widgetControl.Widget.inputs.length > 1) {
        this.selectedInputWidget2 = this.allOutputs.find(
          (t) =>
            t.urn === this.widgetControl?.Widget.inputs[1].urn &&
            t.name === this.widgetControl?.Widget.inputs[1].name,
        );
      } else {
        this.selectedInputWidget2 = undefined;
      }
      if (this.selectedInputWidget1)
        this.setSelectedInputWidget1(this.selectedInputWidget1);
      if (this.selectedInputWidget2)
        this.setSelectedInputWidget2(this.selectedInputWidget2);
    }
  }

  initializeInformation() {
    this.data = {
      type: this.widgetControl?.Widget.type,
      description: "The Append Widget Type allows approved users to:  1. add a new Tabular Dataset to another new Tabular Dataset of identical or similar columns  2. add a new Tabular Dataset to an existing Tabular Dataset of identical or similar columns  3. add an existing Tabular Dataset to an existing Tabular Dataset of identical or similar columns. ",
      version: '',
    };
  }

  getInputingWidgetsOutputName(inputOutputConfig: InputOutputConfig): string {
    return inputOutputConfig.name ?? '';
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

  setAppendInputValue(event : Event){
    console.log("event  is : ", event)
  }

  getAppendInputValue(){

  }

  getUniqueDataTypes(details: any[]): string[] {
    const dataTypes = details.map(detail => detail.data_type);
    return Array.from(new Set(dataTypes));
  }

  async getMisMatchResult(){
    let getDatasetids: any[] = [];
    this.inputWidgets.map((input)=>{
      let config: DataCopyWidgetConfig =input.config as unknown as DataCopyWidgetConfig;
      if(config.source.configuration){
        getDatasetids.push((config.source.configuration as LocalFileConfiguration).dataset_id!);
      }
      
    })
    //console.log("getDatasetids: ",getDatasetids);
      this.misMatchResult = await this.apiService.getAppendMismatches(getDatasetids);
      this.misMatchResultDetails = this.misMatchResult.detail;
      // this.misMatchColumns = this.misMatchResultDetails.mismatch_datatype_columns;
      // this.uncommoncolumns = this.misMatchResultDetails.uncommon_columns;

      this.misMatchColumns = this.misMatchResult.detail.mismatch_datatype_columns.map((mismatch: any) => {
         let savedColumn;
         if(this.savedMisMatchResult){
          savedColumn = this.savedMisMatchResult.find((col: any) => col.column_name === mismatch.column);
         }
         
        const prefType = savedColumn ? savedColumn.pref_type : 'None';
  
        return {
          column: mismatch.column,
          details: mismatch.details,
          pref_type: prefType
        };
      });
      this.missingColumns = this.misMatchResultDetails.missing_columns;
      if(this.missingColumns.length > 0 && this.misMatchColumns.length > 0) {
        this.setPayload();
      }
  }

  onSave() {
    // this.getMisMatchResult();
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
    
    if(this.DataTypes){
      this.config!.column_type_pref_list = [];
      this.DataTypes.map((dataType : any)=>{
        this.config?.column_type_pref_list.push(dataType);
      })
    }
    this.widgetControl.Widget.inputs.length = 0;
    if(this.allOutputs){
      this.allOutputs.map((input)=>{
        this.widgetControl?.Widget.inputs.push(input as InputOutputConfig);
      })
    }
    //this.getMisMatchResult();
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
    this.changeMade = false;
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }
}
