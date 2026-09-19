import { Component, ViewChild, ElementRef, Inject, Optional } from '@angular/core';
import { WidgetControl } from '../../widget-control/widget-control';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import {
  CustomCodeWidgetConfig,
  Widget,
  InputOutputConfig,
  ResultValue,
  StringResult,
  DatasetResult,
  WidgetType,
  DataCopyWidgetConfig,
  LocalFileConfiguration,
  StringsListResult,
  IntegerResult,
  FloatResult,
  DictionaryResult,
  IntergerListResult,
  FloatListResult,
  BooleanResult,
  FilePathResult,
} from 'src/app/models/workflow-models';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from '@angular/material/dialog';
import { Module } from 'src/app/models/module-models';
import { ApiService } from 'src/app/services/api.service';
import { ConfigService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { Utils } from 'src/app/utils';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';

import { DataVisualizationComponent } from 'src/app/dialogs/data-visualization/data-visualization.component';
import { WidgetRunResult, DatasetWidgetResult } from 'src/app/models/workflow-sessions-api-response.models';
import { DomSanitizer } from '@angular/platform-browser';
import { MatTableDataSource } from '@angular/material/table';
import { debounce, debounceTime, distinctUntilChanged, Subject } from 'rxjs';
import { CodeMirrorEditorComponent } from 'src/app/monaco-editor/codemirror-editor.component';
import { EnlargedTextEditorComponent } from 'src/app/util-components/enlarged-text-editor/enlarged-text-editor.component';
import { ToastrService } from 'ngx-toastr';
import { CpwCodeEditorComponent } from 'src/app/util-components/cpw-code-editor/cpw-code-editor.component';
import JSZip from 'jszip';



@Component({
  selector: 'app-custom-code-config',
  templateUrl: './custom-code-config.component.html',
  styleUrls: ['./custom-code-config.component.less'],
})
export class CustomCodeConfigComponent {
  @ViewChild('fileInput')
  fileInput!: ElementRef;
  public widgetControl: WidgetControl | undefined = undefined;
  config: CustomCodeWidgetConfig | undefined = undefined;
  help_details: any;
  selectedTab = 'Function Inputs';
  modules: Module[] = [];
  selectedModule: Module | undefined = undefined;
  data = {};
  getWidgetDetails: any = {};
  inputWidgets: Widget[] = [];
  customConfig: any;
  progress: number = 0;
  selectedInputWidget: any[] = [];
  isWidgetBuilderPreview: boolean = false;

  savedSelections: any = {};
  isSaveDisabled: boolean = false;
  widgetoutputName: any;
  widgetParameters: any[] = [];
  inputWidgetsData = new Map();
  currentDataSetIdForFetchingMetaData: any;
  columnsFilterWord: any;
  isAllColumnsChecked: any;
  columnsList: any
  columnsDataSource: any;
  selectedColumnsFilterWord: any;
  isAllSelectedColumnsChecked: any;
  selectedColumnsList: any
  selectedColumnsDataSource: any
  changeMade: boolean = false
  selectedParameterForConfiguration: any
  showDropDownConfig: boolean = false
  filterSubject = new Subject<string>()
  selectedColumnFilterSubject = new Subject<string>()

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    public dialog: MatDialog,
    private apiService: ApiService,
    private configService: ConfigService,
    public sharedDataService: SharedDataService,
    public toaster: ToastrService,
    private sanitizer: DomSanitizer,
    @Optional() private dialogRef: MatDialogRef<CustomCodeConfigComponent>,
    @Optional() @Inject(MAT_DIALOG_DATA) public dialogData: any
  ) {
    let customWidgetPreviewData = dialogData?.widgetPreviewData;
    if (customWidgetPreviewData) {
      this.config = customWidgetPreviewData.config;
      this.processResponseData(customWidgetPreviewData)
      this.isWidgetBuilderPreview = true
      return;
    }
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    if ('widget_parameters' in this.widgetControl.Widget.config) {
      const configWithParams = this.widgetControl.Widget.config as CustomCodeWidgetConfig;
      this.widgetParameters = configWithParams.widget_parameters;
    }
    this.config = this.widgetControl.Widget.config as CustomCodeWidgetConfig;
    this.config.widget_type = WidgetType.CUSTOM_CODE;
  }

  ngOnInit() {
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.workflowCanvasService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );
      /**
      * Currently we are splitting multiple output widget into individual widgets with single output in the above findConnectedWidgets , but for cpw 
      * we already implemented custom method, so removing the extra widgets with same name in inputWidgets.
      */
      const uniqueWidgetNames = new Set()
      this.inputWidgets = this.inputWidgets.filter((widget: Widget) => {
        if (uniqueWidgetNames.has(widget.name)) {
          return false
        }
        else {
          uniqueWidgetNames.add(widget.name)
          return true
        }
      })
      this.initializeSelections();
      this.initializeSelectedInputWidgets();
      if (this.inputWidgets && this.inputWidgets.length > 0) {
        this.getConnectedWidgetsOutputData();
      }
    }
    this.loadModules();

    this.filterSubject.pipe(
      debounceTime(1000),
    ).subscribe(filterText => {
      this.resetCheckedInColumnList()
      this.isAllColumnsChecked = false;
      this.columnsDataSource = this.columnsDataSource.filter((item: any) => item.name.toLowerCase().includes(this.columnsFilterWord.toLowerCase()));
    })

    this.selectedColumnFilterSubject.pipe(
      debounceTime(1000),
    ).subscribe(filterText => {
      this.resetCheckedInSelectedColumnsList();
      this.isAllSelectedColumnsChecked = false;
      this.selectedColumnsDataSource = this.selectedColumnsDataSource.filter((item: any) => item.name.toLowerCase().includes(this.selectedColumnsFilterWord.toLowerCase()));
    })
    this.autoSelectSingleInputWidget();
  }

  handleChange() {
    this.isSaveDisabled = false;
  }

  async configureDataDropDown(widgetParameter: any) {

    this.selectedParameterForConfiguration = widgetParameter;
    await this.setDropDowndata({
      value: widgetParameter.drop_down_details.drop_down_source_details.dynamic_drop_down_source_data_name
    }, widgetParameter, true)
    this.columnsFilterWord = '';
    this.isAllColumnsChecked = false;
    if (
      !widgetParameter.drop_down_details.drop_down_source_details
        .drop_down_selected_values
    ) {
      widgetParameter.drop_down_details.drop_down_source_details.drop_down_selected_values =
        [];
    }
    this.columnsList =
      widgetParameter.drop_down_details?.drop_down_source_details.drop_down_values
        .filter(
          (element: any) =>
            !widgetParameter.drop_down_details.drop_down_source_details.drop_down_selected_values.includes(
              element,
            ),
        )
        .map((element: any) => {
          return {
            name: element,
            checked: false,
          };
        });

    this.columnsDataSource = this.columnsList;
    this.selectedColumnsFilterWord = '';
    this.isAllSelectedColumnsChecked = false;
    this.selectedColumnsList =
      widgetParameter.drop_down_details.drop_down_source_details.drop_down_selected_values.map(
        (element: any) => {
          return {
            name: element,
            checked: false,
          };
        },
      );
    this.selectedColumnsDataSource = this.selectedColumnsList,

      this.changeMade = false;
    this.showDropDownConfig = true;

  }

  onClosingConfigTemplate() {
    if (!this.selectedParameterForConfiguration) return;

    let selectedNamesArray = [
      ...this.selectedColumnsList.map((element: any) => element.name),
    ];
    this.configureTheFinalValueResult(
      selectedNamesArray,
      this.selectedParameterForConfiguration,
    );
    this.selectedParameterForConfiguration.drop_down_details.drop_down_source_details.drop_down_values = []
    this.showDropDownConfig = false;
  }

  configureTheFinalValueResult(event: any, params: any) {

    let firstKey = Object.keys(params.value.result)[0];

    if (params.drop_down_details.drop_down_type == 'SINGLE_SELECT') {
      let newlySelectedValue = event[0];
      if (!newlySelectedValue) return;
      params.drop_down_details.drop_down_source_details.drop_down_selected_values = [newlySelectedValue]

      if (params.value.type == 'INTEGER') {
        params.value.result[firstKey] = parseInt(newlySelectedValue);
        return;
      }
      if (params.value.type == 'FLOAT') {
        params.value.result[firstKey] = parseFloat(newlySelectedValue);
        return;
      }
      if (params.value.type == 'STRING') {
        params.value.result[firstKey] = newlySelectedValue;
        return;
      }
    } else {
      params.drop_down_details.drop_down_source_details.drop_down_selected_values =
        event;
    }
    if (params.value.type == 'INTEGERS_LIST') {
      params.value.result[firstKey] = event.map((str: any) => parseInt(str));
      return;
    }
    if (params.value.type == 'FLOATS_LIST') {
      params.value.result[firstKey] = event.map((str: any) => parseFloat(str));
      return;
    }
    params.value.result[firstKey] = event;
  }


  closeDropDownConfiguration() {
    this.unCheckEveryElement()
    this.showDropDownConfig = false
    this.selectedParameterForConfiguration.drop_down_details.drop_down_source_details.drop_down_values = []
  }

  unCheckEveryElement() {
    this.columnsList.forEach((element: any) => {
      element.checked = false
    })
    this.selectedColumnsList.forEach((element: any) => {
      element.checked = false
    })
  }



  applyFilterOnColumns() {
    this.filterSubject.next(this.columnsFilterWord)
  }

  resetCheckedInColumnList() {
    this.columnsList = this.columnsList.map((column: any) => ({
      ...column,
      checked: false
    }))
    this.columnsDataSource = this.columnsList;
  }

  toggleAllColumns(event: any) {
    const checked = event.checked;
    this.columnsDataSource.forEach((element: any) => {
      element.checked = checked
    })
  }

  onColumnClicked() {
    this.checkIfAllColumnsChecked();
  }
  checkIfAllColumnsChecked() {
    this.isAllColumnsChecked = this.columnsList.every((element: any) => element.checked);
  }


  onSelectColumns() {
    const columnsToSelect = this.columnsList
      .filter((column: any) => column.checked)
      .map((column: any) => ({
        ...column,
        checked: false,
      }));
    this.selectedColumnsList = [
      ...this.selectedColumnsList,
      ...columnsToSelect,
    ];
    this.columnsList = this.columnsList.filter(
      (column: any) => !column.checked,
    );
    this.selectedColumnsDataSource = this.selectedColumnsList,

      this.columnsDataSource = this.columnsList;

    if (columnsToSelect.length > 0) this.changeMade = true;
    this.isAllColumnsChecked = false;
    this.columnsFilterWord = '';
  }

  onUnselectColumns() {
    const columnsToUnselect = this.selectedColumnsList
      .filter((column: any) => column.checked)
      .map((column: any) => ({
        ...column,
        checked: false,
      }));
    this.columnsList = [...this.columnsList, ...columnsToUnselect];
    this.selectedColumnsList = this.selectedColumnsList.filter(
      (column: any) => !column.checked,
    );
    this.selectedColumnsDataSource = this.selectedColumnsList,
      this.columnsDataSource = this.columnsList;

    if (columnsToUnselect.length > 0) this.changeMade = true;
    this.isAllSelectedColumnsChecked = false;
    this.selectedColumnsFilterWord = '';
  }


  applyFilterOnSelectedColumns() {
    this.selectedColumnFilterSubject.next(this.selectedColumnsFilterWord)
  }


  resetCheckedInSelectedColumnsList() {
    this.selectedColumnsList = this.selectedColumnsList.map((column: any) => ({
      ...column,
      checked: false
    }));
    this.selectedColumnsDataSource = this.selectedColumnsList;
  }

  toggleAllSelectedColumns(event: any) {
    const checked = event.checked;
    this.selectedColumnsDataSource.forEach((element: any) => {
      element.checked = checked
    });
  }

  onSelectedColumnClicked() {
    this.checkIfAllSelectedColumnsChecked();
  }

  checkIfAllSelectedColumnsChecked() {
    this.isAllSelectedColumnsChecked = this.selectedColumnsList.every((element: any) => element.checked);
  }

  initializeSelectedInputWidgets(): void {
    if (this.widgetControl?.Widget?.inputs) {
      // Set default values or load existing values
      this.selectedInputWidget = this.widgetControl.Widget.inputs.map(input => {
        return this.inputWidgets.find(widget =>
          widget.outputs.some(output => output.name === input.name)
        )?.outputs.find(output => output.name === input.name) || null;
      });
    }
  }

  getInputingWidgetsOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let outputConfig: InputOutputConfig = widget.outputs[0];
      return outputConfig.name!;
    }

    return 'Not Set';
  }

  async getConnectedWidgetsOutputData() {
    this.inputWidgets.forEach(async (widget: Widget) => {
      let result = await this.getDatasetOfConnectedWidgetResult(widget)
      this.inputWidgetsData.set(widget.urn, result)
    })
  }


  async getDatasetOfConnectedWidgetResult(widget: Widget) {

    try {
      let widgetConfig = widget.config as DataCopyWidgetConfig;
      var source = widgetConfig?.source?.configuration as LocalFileConfiguration;
      var connectedDatasetId = source?.dataset_id;

      if (connectedDatasetId && connectedDatasetId != '') {
        return [{
          outputName: widgetConfig.sink?.dataset_name,
          resultValue: connectedDatasetId,
          resultType: 'DATASET'
        }];
      }
    }
    catch (error: any) {
      console.log(error)
    }

    try {
      let prevWidgetResults = await this.apiService.GetPreviousTabularWidgetResults(
        this.configService.SelectedSiteId,
        this.configService.SelectedProjectId!,
        this.workflowCanvasService.SelectedWorkflowSession?._id!,
        widget.urn!,);
      if (prevWidgetResults && prevWidgetResults.length > 0) {
          let thisWidgetOutputsMetadata = []
          for (let element of prevWidgetResults) {
            thisWidgetOutputsMetadata.push({
              outputName: element.output_name,
              resultValue: element.final_result,
              resultType: element.result_type
            })
          }
          return thisWidgetOutputsMetadata;
      }  
    } catch (error) {
      console.error(error)
    }

    return {};
  }

  getParamType(type: any) {
    switch (type) {
      case "<class 'str'>":
        return "String"
      case "list[str]":
        return "String list"
      case "<class 'float'>":
        return "Float"
      case "<class 'int'>":
        return "Integer"
      case "<class 'pandas.core.frame.DataFrame'>":
        return "Panda's DataFrame"
      case "list[float]":
        return "Float list"
      case "list[int]":
        return "Integer List"
      case "<class 'dict'>":
        return "Python Dictionary"
      case "<class 'pathlib.Path'>":
        return "File"
      default:
        return type
    }
  }

  getMessageDescriptionForDropDown() {

    if (this.selectedParameterForConfiguration.drop_down_details.drop_down_type == "SINGLE_SELECT") {
      return `This parameter '${this.selectedParameterForConfiguration.arg_name}' is of type ${this.getParamType(this.selectedParameterForConfiguration.type)} and takes only single value. Please select only one value`
    }
    if (this.selectedParameterForConfiguration.drop_down_details.drop_down_type == "MULTI_SELECT") {
      return `This parameter '${this.selectedParameterForConfiguration.arg_name}' is of type ${this.getParamType(this.selectedParameterForConfiguration.type)} and can take muliple values`
    }
    return ""
  }


  async getMetaData() {
    if (this.currentDataSetIdForFetchingMetaData) {
      return await this.apiService.getMetadataOfDataset(this.currentDataSetIdForFetchingMetaData);
    }
  }

  async resetIndividualParamterConfig(event: any, params: any) {

    let drop_down_source_details = params.drop_down_details?.drop_down_source_details
    drop_down_source_details.drop_down_selected_values = []
    if (!this.inputWidgetsData.has(event.value)) {
      return;
    }
    if (this.isSelectedWidgetHasMultipleOutputs(event.value)) {
      drop_down_source_details.output_list = this.inputWidgetsData.get(event.value)
      if (!drop_down_source_details.dynamic_drop_down_source_data_output_name) {
        drop_down_source_details.dynamic_drop_down_source_data_output_name = drop_down_source_details.output_list[0].outputName
      }
      return;
    }
    drop_down_source_details.dynamic_drop_down_source_data_output_name = null
    drop_down_source_details.output_list = []
  }

  /**
   * While selecting the widet for the firstTime always choose the first Output to fill the drop down values.
   * @param isSameSourceSelected , this flag is needed if we want to override the existing values.
   * If the selected previous widget has multiple ouputs we are storing it in output_list of drop_down_source_details.
   */

  async setDropDowndata(event: any, params: any, isSameSourceSelected?: boolean) {

    let drop_down_source_details = params.drop_down_details?.drop_down_source_details
    if (!this.inputWidgetsData.has(event.value)) {
      return;
    }
    if (this.isSelectedWidgetHasMultipleOutputs(event.value)) {
      drop_down_source_details.output_list = this.inputWidgetsData.get(event.value)
      if (!drop_down_source_details.dynamic_drop_down_source_data_output_name) {
        drop_down_source_details.dynamic_drop_down_source_data_output_name = drop_down_source_details.output_list[0].outputName
        await this.setDataBasedOnDynamicSubType(drop_down_source_details, drop_down_source_details.output_list[0])
      }
      else {
        let existingSelectedOutput = drop_down_source_details.dynamic_drop_down_source_data_output_name
        let widgetOutputResult = drop_down_source_details.output_list.find((element: any) => element.outputName == existingSelectedOutput)
        await this.setDataBasedOnDynamicSubType(drop_down_source_details, widgetOutputResult, isSameSourceSelected)
      }
      return;
    }
    await this.setDataBasedOnDynamicSubType(drop_down_source_details, this.inputWidgetsData.get(event.value)[0], isSameSourceSelected)
    drop_down_source_details.dynamic_drop_down_source_data_output_name = null
    drop_down_source_details.output_list = []
  }

  /**
   * If selected widgets has multiple ouputs show a dropdown to select the particular output 
   */
  isSelectedWidgetHasMultipleOutputs(widgetUrn: any) {
    if (this.inputWidgetsData.has(widgetUrn)) {
      let outputDetails = this.inputWidgetsData.get(widgetUrn)
      return outputDetails.length > 1
    }
    return false;
  }

  /**
   * In case if in future if we need statistical values then with the help of datasetId in datasetmetaData or in results api 
   * call the eda/statitics api and set the statistics values
   * @param datasetMetaData 
   */

  async setDataBasedOnDynamicSubType(drop_down_source_details: any, widgetOutputResult: any, isSameSourceSelected?: boolean) {

    if(widgetOutputResult.resultType == "DATASET") {
        drop_down_source_details.drop_down_values = await this.getAllColumnsList(widgetOutputResult.resultValue)
    }
    else {
      if(!(widgetOutputResult.resultValue instanceof Array)) {
        drop_down_source_details.drop_down_values = [widgetOutputResult.resultValue]
      }
      else {
        drop_down_source_details.drop_down_values = widgetOutputResult.resultValue
      }
    }

    if (!isSameSourceSelected) drop_down_source_details.drop_down_selected_values = []
   
  }

  resetSelectedValues(drop_down_source_details: any, event: any) {
    drop_down_source_details.drop_down_selected_values = []
  }

  async getAllColumnsList(datasetId: any) {

    try {
      this.selectedParameterForConfiguration.isLoading = true
      this.currentDataSetIdForFetchingMetaData = datasetId;
      let metadata = await this.getMetaData()
      let columnsListOfThatDataset = Object.keys(metadata.data_column_types)
      this.selectedParameterForConfiguration.isLoading = false
      return columnsListOfThatDataset
    }
    catch (error) {

    }
    this.selectedParameterForConfiguration.isLoading = false

    return []

  }

  onDropdownClick(params: any, matSelect: any): void {
    const currentSelection = params.drop_down_details?.drop_down_source_details.dynamic_drop_down_source_data_name;
    if (currentSelection != matSelect.value) return;
    this.setDropDowndata({ value: currentSelection }, params, true);
  }

  onSelectionChange(event: any, params: any) {

    let firstKey = Object.keys(params.value.result)[0];

    if (params.drop_down_details.drop_down_type == "SINGLE_SELECT") {

      let newlySelectedValue = this.getNewlySelectedValue(params.drop_down_details.drop_down_source_details.drop_down_selected_values, event.value)
      params.drop_down_details.drop_down_source_details.drop_down_selected_values = [newlySelectedValue]
      event.value = [newlySelectedValue]

      if (params.value.type == "INTEGER") {
        params.value.result[firstKey] = parseInt(newlySelectedValue)
        return;
      }
      if (params.value.type == "FLOAT") {
        params.value.result[firstKey] = parseFloat(newlySelectedValue)
        return;
      }
      if (params.value.type == "STRING") {
        params.value.result[firstKey] = newlySelectedValue
        return;
      }

    }
    else {
      params.drop_down_details.drop_down_source_details.drop_down_selected_values = event.value
    }
    if (params.value.type == "INTEGERS_LIST") {
      params.value.result[firstKey] = event.value.map((str: any) => parseInt(str))
      return
    }
    if (params.value.type == 'FLOATS_LIST') {
      params.value.result[firstKey] = event.value.map((str: any) => parseFloat(str))
      return
    }
    params.value.result[firstKey] = event.value
  }



  /**
   * Implemented this function to get the newly selected value in multiple select drop down
   * @param selectedWidget 
   * @param index 
   * Return a single element array 
   */
  getNewlySelectedValue(previouslySelectedValues: any, currentSelectedValues: any) {
    let newlySelectedValue = currentSelectedValues.find((value: any) => !previouslySelectedValues.includes(value))
    if (!newlySelectedValue) newlySelectedValue = "0"
    return newlySelectedValue
  }


  setSelectedInputWidget(selectedWidget: any, index: number): void {
    if (this.widgetControl?.Widget?.inputs) {
      this.selectedInputWidget[index] = selectedWidget;

      if (selectedWidget) {
        this.widgetControl.Widget.inputs[index].name = selectedWidget.name;
        this.widgetControl.Widget.inputs[index].urn = selectedWidget.urn;
      } else {
        this.widgetControl.Widget.inputs[index].name = '';
        this.widgetControl.Widget.inputs[index].urn = '';
      }
    }
    if(this.inputWidgets.length == 1 && this.inputWidgets[0].outputs.length === 1){
      this.isSaveDisabled = true;
    }else{
      this.isSaveDisabled = false;
    }
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  publish() {
    this.dialogRef.close({ isPublish: true })
  }

  SaveCpw() {
    this.isSaveDisabled = true; // Disable Save button after saving
  }

  loadModules() {
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.widget_id
    ) {
      this.apiService
        .GetCustomCodeWidget(this.widgetControl.Widget.widget_id)
        .then((response: any) => {
          if (response) {
            this.getWidgetDetails = response;
            this.processResponseData(response);
          }
        })
        .catch((error) => {
          console.log(error);
        });
    } else if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      (this.widgetControl.Widget.config as CustomCodeWidgetConfig)
    ) {
      this.config = this.widgetControl.Widget.config as CustomCodeWidgetConfig;
      this.customConfig = this.widgetControl.Widget;
      if (this.config.widget_id) {
        this.apiService
          .GetCustomCodeWidget(this.config.widget_id)
          .then((response: any) => {
            if (response) {
              this.getWidgetDetails = response;
              this.help_details = response.help_details;
            }
          });
      }
    }
  }

  getInputType(argumentName: any) {
    let type = "None";
    this.config?.function_inputs.forEach((functionInput:any) => {
      if (functionInput.arg_name == argumentName) {
        type = functionInput.type
      }
    })
    return this.getParamType(type)
  }

  private processResponseData(response: any) {
    this.help_details = response.help_details;
    this.customConfig = response;
    if (this.config && this.config.widget_parameters.length == 0) {
      this.config.module_id = response.config.module_id;
      this.config.widget_id = this.widgetControl?.Widget.widget_id;
      this.config.function_inputs = response.config.function_inputs;
      this.config.function_outputs = response.config.function_outputs;
      const initializedWidgetParameters = response.config.widget_parameters.map((el: any) => {
        if (el.value) {
          const clonedValue = JSON.parse(JSON.stringify(el.value));
          if (clonedValue.result &&
            clonedValue.result.string_value ===
            '<ToBeModifiedDuringWidgetRunTimeByUI>') {
            clonedValue.result.string_value = '';
          }
          if (clonedValue.result && clonedValue.result?.dataset_id) {
            clonedValue.result.dataset_id = '';
          }
          el.value = clonedValue;
        }
        return el;
      });

      this.config.widget_parameters = initializedWidgetParameters;
    }
    if (this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.inputs.length == 0) {
      this.widgetControl.Widget.inputs = this.customConfig.inputs;
    }

    this.customConfig.outputs.map((el: any, index: number) => {
      if (this.widgetControl && this.widgetControl.Widget) {
        this.createOutputConfig(el, this.widgetControl.Widget, index);
      }
    });
  }

  initializeSelections(): void {
    if (this.widgetControl?.Widget?.inputs) {
      this.selectedInputWidget = this.widgetControl.Widget.inputs.map(
        (input) => {
          const matchingWidget = this.inputWidgets.find((widget) =>
            widget.outputs.some(
              (output) =>
                output.name === input.name && output.urn === input.urn,
            ),
          );
          return matchingWidget || null;
        },
      );
    }
  }

  createOutputConfig(outputData: any, widget: Widget, index: number) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    let name = Utils.GetNamedOutput(widget, selectedProjectId);
    let outputConfig: InputOutputConfig = new InputOutputConfig();
    outputConfig.urn = widget.urn!;
    outputConfig.name = `${name!}${index + 1}`;
    outputConfig.map_to_argument = outputData.map_to_argument;
    outputConfig.type = outputData.type;
    widget.outputs[index] = outputConfig;
  }

  ngAfterViewInit() {
    if (this.customConfig) {
      this.data = {
        type: this.widgetControl?.Widget.name,
        description: this.customConfig?.description,
        version: this.customConfig?.version,
      };
    }
  }


  setSelectedInputWidget1(selectedWidget: any, index: number): void {
    if (!this.widgetControl?.Widget || !this.widgetControl.Widget.inputs) {
      return;
    }

    // Update the selected widget in the array
    this.selectedInputWidget[index] = selectedWidget;

    // If a widget is selected, update the input details
    if (selectedWidget) {
      this.widgetControl.Widget.inputs[index].name = selectedWidget.name;
      this.widgetControl.Widget.inputs[index].urn = selectedWidget.urn;
    } else {
      // Clear the input if no widget is selected
      this.widgetControl.Widget.inputs[index].name = '';
      this.widgetControl.Widget.inputs[index].urn = '';
    }
  }

  getWidgetOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let outputConfig: InputOutputConfig = widget.outputs[0];
      return outputConfig.name!;
    }

    return 'Not Set';
  }

  get widgetOutput(): string[] {
    if (!this.widgetControl?.Widget.outputs) {
      return [];
    }
    return this.widgetControl.Widget.outputs
      .map((output) => output.name)
      .filter((name): name is string => name !== undefined);
  }

  updateWidgetOutput(index: number, newName: string | undefined) {
    if (!this.widgetControl || newName === undefined) {
      return;
    }
    const trimmedName = newName.trim();
    if (
      this.widgetControl.Widget.outputs &&
      this.widgetControl.Widget.outputs.length > index
    ) {
      this.widgetControl.Widget.outputs[index].name = trimmedName;
      this.widgetoutputName = trimmedName;
    } else {
      console.warn(
        'Attempted to update an output that does not exist at index: ',
        index,
      );
    }
    this.isSaveDisabled = false;
  }

  setArgName(newArgName: string, index: number): void {
    if (
      index >= 0 &&
      index < this.customConfig.config.widget_parameters.length
    ) {
      this.customConfig.config.widget_parameters[index].arg_name = newArgName;
    }
  }

  setValue(newValue: string, index: number): void {
    if (
      index >= 0 &&
      index < this.customConfig.config.widget_parameters.length
    ) {
      let param = this.customConfig.config.widget_parameters[index];
      if (param.value && param.value.result) {
        if (newValue == '' || newValue == null) {
          param.value.result.string_value = param.value.result.string_value;
        } else {
          param.value.result.string_value = newValue;
        }
      }
    }
    this.isSaveDisabled = false;
  }

  setFloatValue(newValue: string, index: number): void {
    if (
      index >= 0 &&
      index < this.customConfig.config.widget_parameters.length
    ) {
      let param = this.customConfig.config.widget_parameters[index];
      if (param.value && param.value.result) {
        if (newValue == '' || newValue == null) {
          param.value.result.float_value = param.value.result.float_value;
        } else {
          param.value.result.float_value = parseFloat(newValue);
        }
      }
    }
    this.isSaveDisabled = false;
  }

  convertPythonDictionaryToJson(pythonDictString: any) {

    const jsonString = pythonDictString
      .replace(/'/g, '"')
      .replace(/None/g, 'null')
      .replace(/True/g, 'true')
      .replace(/False/g, 'false');

    return JSON.parse(jsonString);
  }

  convertJsonObjectToDictionary(jsonString: any) {
    try {
      // Assuming jsonObject is the parsed JSON object from the backend
      const pythonDictString = JSON.stringify(jsonString, null, 2)
        .replace(/"/g, "'")              // Replace double quotes with single quotes
        .replace(/null/g, 'None')         // Convert 'null' to 'None'
        .replace(/true/g, 'True')         // Convert 'true' to 'True'
        .replace(/false/g, 'False');      // Convert 'false' to 'False'

      return pythonDictString
    } catch (error) {
      console.error('Error converting JSON back to Python dictionary format:', error);
    }
    return ""
  }

  setDictionaryValue(newValue: any, index: number): void {
    if (
      index >= 0 &&
      index < this.customConfig.config.widget_parameters.length
    ) {
      let param = this.customConfig.config.widget_parameters[index];
      if (param.value && param.value.result) {
        if (newValue == '' || newValue == null) {
          param.value.result.dict_value = param.value.result.dict_value;
        }
        else {
          param.value.result.dict_value = newValue
        }
      }
      this.isSaveDisabled = false;
    }
  }

  openDictionaryInput(params: any) {
    const dialogRef = this.dialog.open(EnlargedTextEditorComponent, {
      width: '600px',
      height: '700px',
      data: {
        dataTobeDisplayed: params.value.result.dict_value
      }
    })

    dialogRef.afterClosed().subscribe((result) => {
      if (result.isSaved) {
        params.value.result.dict_value = result.data
      }
    })
  }


  setFloatListValues(newValue: any, index: number, param: any): void {
    if (
      index >= 0 &&
      index < this.customConfig.config.widget_parameters.length
    ) {
      if (param.value && param.value.result) {
        if (newValue == '' || newValue == null) {
          param.value.result.floats_list_value = param.value.result.floats_list_value;
        }
        else {
          if (newValue[newValue.length - 1] == ",") return;
          let floatArray = newValue.split(",")
          param.value.result.floats_list_value = floatArray.map((str: any) => parseFloat(str))
        }
      }
      this.isSaveDisabled = false;
    }
  }


  setIntegerListValue(newValue: any, index: number, param: any): void {
    if (
      index >= 0 &&
      index < this.customConfig.config.widget_parameters.length
    ) {
      if (param.value && param.value.result) {
        if (newValue == '' || newValue == null) {
          param.value.result.integers_list_value = param.value.result.integers_list_value;
        }
        else {
          if (newValue[newValue.length - 1] == ",") return;
          let integerArray = newValue.split(",")
          param.value.result.integers_list_value = integerArray.map((str: any) => parseInt(str))
        }
      }
      this.isSaveDisabled = false;
    }
  }

  setBooleanValue(newValue: any, index: number): void {
    if (
      index >= 0 &&
      index < this.customConfig.config.widget_parameters.length
    ) {
      let param = this.customConfig.config.widget_parameters[index];
      if (param.value && param.value.result) {
        if (newValue == '' || newValue == null) {
          param.value.result.boolean_value = param.value.result.boolean_value;
        }
        else {
          param.value.result.boolean_value = newValue
        }
      }
      this.isSaveDisabled = false;
    }
  }

  setStringListValue(newValue: string, index: number, param: any): void {
    if (
      index >= 0 &&
      index < this.customConfig.config.widget_parameters.length
    ) {
      if (newValue == '' || newValue == null) {
        param.value.result.strings_list_value = param.value.result.strings_list_value;
      }
      else {
        if (newValue[newValue.length - 1] == ",") return;
        let stringArray = newValue.split(",")
        param.value.result.strings_list_value = stringArray
      }
    }
    this.isSaveDisabled = false;
  }



  setIntegerValue(newValue: string, index: number): void {
    if (
      index >= 0 &&
      index < this.customConfig.config.widget_parameters.length
    ) {
      let param = this.customConfig.config.widget_parameters[index];
      if (param.value && param.value.result) {
        if (newValue == '' || newValue == null) {
          param.value.result.integer_value = param.value.result.integer_value;
        } else {
          param.value.result.integer_value = parseInt(newValue);
        }
      }
    }
    this.isSaveDisabled = false;
  }
  setDatasetValue(newValue: string, index: number): void {
    // Update dataset ID in customConfig.config.widget_parameters
    if (index >= 0 && index < this.customConfig.config.widget_parameters.length) {
      let param = this.customConfig.config.widget_parameters[index];
      if (param.value && param.value.result) {
        param.value.result.dataset_id = newValue;
      }
    }

    // Update dataset ID in config.widget_parameters
    if (this.config && this.config.widget_parameters && index >= 0 && index < this.config.widget_parameters.length) {
      let configParam = this.config.widget_parameters[index];
      if (configParam.value && configParam.value.result) {
        configParam.value.result.dataset_id = newValue;
      }
    }
    // Enable Save button when dataset value is set
    this.isSaveDisabled = false;
  }



  async onFileSelected(event: any, index: number): Promise<void> {
    const file = event.target.files[0];
    if (file) {
      try {
        const name = this.customConfig?.name || '';
        const description = this.customConfig?.description || '';

        this.apiService
          .UploadCsvFile(file, name, description, 'INTERNAL', (progress) => {
            this.progress = progress;
          })
          .subscribe({
            next: (response) => {
              if (response) {
                // Set the dataset value in the parameter
                this.setDatasetValue(response.dataset_id, index);
              }
            },
            error: (error) => {
              console.error('Upload failed:', error);
            },
          });
      } catch (error) {
        console.error('Error during file selection:', error);
      }
    }
    // Enable Save button even if file selection logic completes
    this.isSaveDisabled = false;
  }

  isFileUploadInProgress = false
  async uploadFileToFileSystem(event: any, params: any): Promise<any> {
    const file = event.target.files[0];
    this.isFileUploadInProgress = true
    if (file) {
      try {
        let response : any = await this.apiService.uploadFileWithFixedPath(
          file
        );
        params.value.result.file_path_value = response?.files[0].file_path
      } catch (error) {
        console.error('Error during file upload:', error);
      }
    }
    this.isFileUploadInProgress = false
  }

  getFileNameFromFilePath(filePath:any) {
    try{
      return filePath.split('/').pop()
    }
    catch(error) {
      console.error("File name not present")
    }
    return filePath
  }


  onUploadFile() {
    this.fileInput.nativeElement.click();
    this.isSaveDisabled = false;
  }

  isStringResult(result: ResultValue | undefined): result is StringResult {
    return !!result && 'string_value' in result;
  }

  isFloatResult(result: ResultValue | undefined): result is FloatResult {
    return !!result && 'float_value' in result;
  }
  isStringsListResult(result: ResultValue | undefined): result is StringsListResult {
    return !!result && 'strings_list_value' in result;
  }
  isIntegerResult(result: ResultValue | undefined): result is IntegerResult {
    return !!result && 'integer_value' in result;
  }

  isDictionaryResult(result: ResultValue | undefined): result is DictionaryResult {
    return !!result && 'dict_value' in result;
  }

  isIntergerListResult(result: ResultValue | undefined): result is IntergerListResult {
    return !!result && 'integers_list_value' in result;
  }

  isFloatListResult(result: ResultValue | undefined): result is FloatListResult {
    return !!result && 'floats_list_value' in result;
  }

  isBooleanResult(result: ResultValue | undefined): result is BooleanResult {
    return !!result && 'boolean_value' in result;
  }

  isFilePathResult(result: ResultValue | undefined): result is FilePathResult {
    return !!result && 'file_path_value' in result;
  }

  isDatasetResult(result: ResultValue | undefined): result is DatasetResult {
    return !!result && 'dataset_id' in result;
  }

  getResultStringValue(result: ResultValue | undefined): string | undefined {
    if (!result) {
      return 'N/A';
    }
    if (this.isStringResult(result)) {
      return result.string_value;
    }
    return 'N/A';
  }

  getResultDatasetValue(result: ResultValue | undefined): string {
    if (!result) {
      return 'N/A';
    }
    if (this.isDatasetResult(result)) {
      return result.dataset_id ?? 'N/A';
    }
    return 'N/A';
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

  openDataPreveiwDialog(event: any) {
    let results: WidgetRunResult[] = this.workflowCanvasService.getWidgetRunResults();
    if (results.length > 0) {
      let visualizationData = results.filter((result: any) => result.result_type === 'VISUALIZATION' || result.result_type === 'STRINGS_LIST');
      if (visualizationData.length > 0) {
        var plots: any = [];
        var string_value: boolean = false;
        for (let i = 0; i < visualizationData.length; i++) {
          let result_value: any = visualizationData[i]?.result_value
          if(result_value.string_value){
            let url = result_value.string_value;
            string_value = true;
            if (url && url != '') {
              plots.push(this.sanitizer.bypassSecurityTrustResourceUrl(`${this.configService.getAppAuxApiURL}/eda/file?path=${url}`));
            }
          }else{
            string_value = false;
            plots = [...result_value.strings_list_value]
          }
          if (i == (visualizationData.length - 1)) {
            const dialogRef = this.dialog.open(DataVisualizationComponent, {
              width: '95vw',
              maxWidth: '95vw',
              height: '95%',
              data: {
                type: 'CPW',
                plots: plots,
                string_value: string_value
              },
            });
            dialogRef.afterClosed().subscribe((result) => { });

          }
        }
      }
    }
  }

  uploadedType = 'PY'
  selectedFileName: any;
  filesExtracted = false;
  filesExtractedResponse: any;
  originalFilesCache: any;
  extractedPythonFilesForEditing: any;
  functionSignature: any;
  isCPWCodeEditButtonDisabled = false

  async getCpwFilesAndOpenEditor() {

    try {
      this.isCPWCodeEditButtonDisabled = true
      let module_id = this.getWidgetDetails?.config.module_id;
      let moduleMetadata = await this.apiService.getCustomWidgetModuleMetaData(
        '1',
        this.configService.getProjectId,
        module_id,
      );
      this.uploadedType = moduleMetadata?.module_location.extension
      this.functionSignature = moduleMetadata?.metadata.function_signature
      this.selectedFileName = moduleMetadata.module_location.path.split('/').pop()
      await this.processCPWCodeFilesAndOpenCodeEditor()
    }
    catch(error) {
      console.log(error)
    }
    finally {
      this.isCPWCodeEditButtonDisabled = false
    }
    
  }

  getPythonFunctionArguments() {
    let argumentsForPythonFunction:any = [];

    this.widgetControl?.Widget?.inputs?.forEach((widgetParameter: any) => {
      argumentsForPythonFunction.push({
        argumentName: widgetParameter.map_to_argument,
        argumentValue: "From Previous Widget"
      })
    })
    
    this.config?.widget_parameters.forEach((widgetParmeter:any) => {
      let firstKey = Object.keys(widgetParmeter.value.result)[0]
      argumentsForPythonFunction.push({
        argumentName: widgetParmeter.arg_name,
        argumentValue: widgetParmeter.value.result[firstKey]
      })
    })

    return argumentsForPythonFunction
  }


  async processCPWCodeFilesAndOpenCodeEditor() {

      let projectId: any = this.configService.SelectedProjectId;
      let files = [];
      const downloadUrl = await this.apiService.DownloadDatset(
        '1',
        projectId,
        this.getWidgetDetails?.config.module_id,
        'PYTHON',
      );
      const response = await fetch(downloadUrl, {
        method: 'GET',
        cache: 'no-store'
      })
      if (this.uploadedType == 'ZIP') {
        const zipBlob = await response.blob();
        const zip = await JSZip.loadAsync(zipBlob);
        for (const fileName of Object.keys(zip.files)) {
          const content = await zip.files[fileName].async('string');
          files.push({ name: fileName, content });
        }
      }

      if (this.uploadedType == 'PY') {
        let fileName = this.selectedFileName;
        const pythonFileAsString = await response.text();
        files.push({ name: fileName, content: pythonFileAsString });
      }

      this.extractedPythonFilesForEditing = files;
      this.openCPWCodeEditor();
  }

    openCPWCodeEditor() {
      this.originalFilesCache = this.extractedPythonFilesForEditing.map(
        (element: any) => {
          return { ...element };
        },
      );
      const dialogRef = this.dialog.open(CpwCodeEditorComponent, {
        disableClose: true,
        data: {
          arrayOfFiles: this.extractedPythonFilesForEditing,
          argumentsForPythonFunction: this.getPythonFunctionArguments(),
          isEditingInWorkflow: true
        },
      });

      dialogRef.componentInstance.saveEvent.subscribe(async () => {
        try {
          dialogRef.componentInstance.isSavingInProgress = true
          await this.saveAndPushTheChanges();
          if (this.filesExtracted == false) {
            dialogRef.componentInstance.updateBackendLogs(this.filesExtractedResponse)
            return;
          }
          this.updateTheCacheWithTheSavedChanges()
          dialogRef?.close({ isSaved: true })
        }
        catch (error) {
          console.error(error)
        }
        finally {
          dialogRef.componentInstance.isSavingInProgress = false
        }
      });

      dialogRef.afterClosed().subscribe((result) => {
        if (result?.isSaved == false) {
          this.revertTheFileChangesInEditor();
        }
      });
    }

   async saveAndPushTheChanges() {
      if(this.uploadedType == 'ZIP') {
        const zip = new JSZip()
        this.extractedPythonFilesForEditing.forEach((file:any) => {
          zip.file(file.name, file.content)
        })
        let zippedContent = await zip.generateAsync({type: 'blob'})
        await this.uploadTheCPWCode(zippedContent, this.selectedFileName)
      }
      if(this.uploadedType == 'PY') {
        const blob = new Blob([this.extractedPythonFilesForEditing[0].content], { type: 'text/x-python' });
  
        // Step 2: Create a File from the Blob with a .py extension
        const file = new File([blob], 'script.py', { type: 'text/x-python' });
        await this.uploadTheCPWCode(file, this.selectedFileName)
      }
      
    }

    async uploadTheCPWCode(file: any, fileName?: any) {
      let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
      if (!selectedProjectId) {
        return;
      }
  
      try {
        const response = await this.apiService.GetUploadFiles(
          file,
          selectedProjectId,
          1,
          this.selectedFileName.endsWith('.py'),
          fileName
        );
        if (response.finalresponse !== void 0 &&
          response.finalresponse.metadata) {
            if (this.functionSignature != response.finalresponse.metadata.function_signature) {
              this.filesExtracted = false;
              this.filesExtractedResponse = 'New Function Signature is not matching with the existing one, Please create a new CPW'
              return
            }
          }
  
          if (!response.finalresponse.succeeded) {
            this.filesExtracted = false;
            this.filesExtractedResponse = response.finalresponse.message;
            this.toaster.error(this.filesExtractedResponse,'', {
              positionClass: 'custom-toast-position'
            });
            return;
          }
          let pathOfTheNewlyUploadedFile = response.firstApiResponse.files[0].file_path;
          await this.apiService.replaceTheModuleFilePath(this.getWidgetDetails._id, pathOfTheNewlyUploadedFile)
          this.filesExtracted = true;
          this.filesExtractedResponse = 'New code is successfully updated';
          this.toaster.success("File is succuessfuly replaced",'', {
            positionClass: 'custom-toast-position'
          });
          return
      }
      catch{
        this.filesExtracted = false;
        this.filesExtractedResponse = "Something went wrong in API"
      }
    }

    revertTheFileChangesInEditor() {
      this.extractedPythonFilesForEditing = this.originalFilesCache.map((element: any) => {
        return {...element}
      })
    }
  
    updateTheCacheWithTheSavedChanges() {
      this.originalFilesCache = this.extractedPythonFilesForEditing.map((element: any) => {
        return {...element}
      })
    }
  
    autoSelectSingleInputWidget(): void {      
      if (this.inputWidgets.length === 1) {
        const singleWidget = this.inputWidgets[0];
        if (singleWidget.outputs.length === 1) {
          const singleOutput = singleWidget.outputs[0];
          this.selectedInputWidget[0] = singleOutput;
          this.setSelectedInputWidget(singleOutput, 0);
        }
      }
    }


}
