import { Component, ViewChild } from '@angular/core';
import { Connector, ConnectorType } from 'src/app/models/connector-models';
import {
  BigQueryDatasetConfiguration,
  BigQueryDatasetTableConfig,
  BigQueryDatasetQueryConfig,
  BigQueryDatasetType,
  DataCopyWidgetConfig,
  Widget,
  BigQueryDatasetConfig,
  SourceConfiguration,
  SourceType,
  Sink,
  WidgetType,
} from 'src/app/models/workflow-models';
import { ApiService } from 'src/app/services/api.service';
import { ConfigService, WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { MatDialog } from '@angular/material/dialog';
import { BigQueryPreviewComponent } from '../../../dialogs/big-query-preview/big-query-preview.component';
// import { ColorPickerService, Cmyk } from 'ngx-color-picker';
import { SettingsComponent } from '../settings/settings.component';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { NewConnectorService } from 'src/app/dialogs/connector-dialog/services/new-connector.service';
import { Router } from '@angular/router';
import { BigQueryResultPreviewComponent } from 'src/app/dialogs/big-query-result-preview/big-query-result-preview.component';
import { BigQueryLoadSavedQueryComponent } from 'src/app/dialogs/big-query-load-saved-query/big-query-load-saved-query.component';
import { ToastrService } from 'ngx-toastr';
import { WorkflowConfigService } from 'src/app/pages/workflow-designer/workflow-config.service'

interface TreeNode {
  item: string;
  children?: TreeNode[];
}

interface FlatNode {
  item: string;
  level: number;
  expandable: boolean;
}
@Component({
  selector: 'app-big-query-config',
  templateUrl: './big-query-config.component.html',
  styleUrls: ['./big-query-config.component.less'],
})
export class BigQueryConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  connectors: Connector[] = [];

  BigQueryDatasetType = BigQueryDatasetType;
  datasetTypeOptions = Object.values(BigQueryDatasetType).filter(
    (value) => typeof value === 'string',
  );
  data = {};
  files: any;

  allConnectors:any;
  authdetails: any;
  getQueries: any;
  textBoxQuery: any;
  queryName: string = '';
  authentication_type: any;
  siteId: any;
  saveButtonText: string = 'SAVE';
  projectId: any;
  parentTableName: any;
  parametersName: any;
  parametersValue: any;
  parametersType: any;
  parametersSubtype: any;
  query_params: any = {};
  params: any;
  childName: any;
  bigDataConfiguration: any;
  datasetType: string= 'QUERY';
  isLoadQuery: boolean = false
  isJsonAuthenticationSuccessful:boolean = false;
  isJsonAuthenticationFailed: boolean = false;
  deleteButton: boolean = false;
  savebutton: boolean = true;
  querId: any;
  parameterButtonStatus: boolean = false;
  loadQueryFileName: any;
  spinner: boolean = false;
  selectedQuery: string = 'New Query';
  showConfirmationBox: boolean = false;
  changeMade: boolean = false;
  config: DataCopyWidgetConfig | undefined = undefined;
  configCache: DataCopyWidgetConfig | undefined = undefined;
  outputName: string | undefined = undefined;

  inputWidgets: Widget[] = [];
  selectedInputWidget: Widget | undefined = undefined;
  public widgetControl: WidgetControl | undefined = undefined;
  selectedRadioButtonValue: string = '';
  parentItems: any = [];
  TableNames: any = [];
  selectedChild: string | null = null;
  clickTimeout: any;
  parameters = [
    {
      name: '',
      value: '',
      type: '',
      subtype: '',
      required: false
    }
  ];

  constructor(
    private apiService: ApiService,
    private dialog: MatDialog,
    public sharedDataService: SharedDataService,
    public workflowCanvasService: WorkflowCanvasService,
    private configService: ConfigService,
    private connectorService: NewConnectorService,
    private router: Router,
    public toaster: ToastrService,
    public WorkflowConfigService: WorkflowConfigService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.projectId = this.configService.SelectedProjectId;
    this.siteId = this.configService.SelectedSiteId;
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.config = this.widgetControl.Widget.config as DataCopyWidgetConfig;
    this.config.widget_type = WidgetType.DATA_COPY;  
    this.configCache = JSON.parse(JSON.stringify(this.config));
    this.outputName = this.widgetControl.Widget.outputs[0].name;
  }

  ngOnInit() {
    this.loadConnectors();
    this.initializeInformation();

    this.queryName = this.widgeFileName ? this.widgeFileName : '';
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  initializeInformation() {
    this.data = {
      type: this.config?.source.type,
      description: 'Big query is a relational data base, you need to write a query',
      version: this.config?.source.configuration.version,
    };
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.workflowCanvasService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );
    }
  }

  openTab(event: any, tabName: string) {
    // Get all elements with class="tabcontent" and hide them
    let tabcontent = document.getElementsByClassName('tabcontent');
    for (let i = 0; i < tabcontent.length; i++) {
      let element = tabcontent[i] as HTMLElement; // Type assertion
      element.style.display = 'none';
    }
    // Get all elements with class="tablinks" and remove the class "active"
    let tablinks = document.getElementsByClassName('tablinks');
    for (let i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(' active', '');
    }

    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(tabName)!.style.display = 'block';
    if (!event) {
      // Iterate over tablinks to find the one that matches the tabName
      for (let i = 0; i < tablinks.length; i++) {
        let tabLink = tablinks[i] as HTMLElement;
        if (tabLink.textContent?.trim() === tabName) {
          tabLink.className += ' active';
          break;
        }
      }
    } else {
      // Existing logic for setting active class...
      event.currentTarget.className += ' active';
    }
  }

  isBigQueryDatasetConfiguration(
    configuration: any,
  ): configuration is BigQueryDatasetConfiguration {
    return configuration;
  }

  get connectorId(): string | undefined {
    if (!this.configCache) {
      return '';
    }
    if (
      this.isBigQueryDatasetConfiguration(this.configCache.source.configuration)
    ) {
      let bigQueryDatasetConfiguration: BigQueryDatasetConfiguration =
        this.configCache.source.configuration;
      return bigQueryDatasetConfiguration.bigquery_connector_id;
    }

    return undefined;
  }

  set connectorId(value: string) {
    this.changeMade = true;

    if (!this.configCache) {
      return;
    }
    if (
      this.isBigQueryDatasetConfiguration(this.configCache.source.configuration)
    ) {
      let bigQueryDatasetConfiguration: BigQueryDatasetConfiguration =
        this.configCache.source.configuration;
      bigQueryDatasetConfiguration.bigquery_connector_id = value;
      this.widgetControl!.Widget.config = this.configCache;
    }
  }

  getDatasetName(): string | undefined {
    const config = this.configCache?.source.configuration;

    if (this.isBigQueryDatasetConfiguration(config)) {
      const bigQueryDatasetConfig = config as BigQueryDatasetConfiguration;

      if (
        bigQueryDatasetConfig.dataset_configuration?.dataset_type ===
        BigQueryDatasetType.TABLE
      ) {
        let bigQueryDatasetTableConfig: BigQueryDatasetTableConfig | undefined =
          bigQueryDatasetConfig.dataset_configuration
            ?.dataset as BigQueryDatasetTableConfig;
        return bigQueryDatasetTableConfig.dataset_name;
      }
    }

    return undefined;
  }

  setDatasetName(value: string) {
    if (!this.configCache) {
      return;
    }

    if (
      this.isBigQueryDatasetConfiguration(this.configCache.source.configuration)
    ) {
      let bigQueryDatasetConfiguration:
        | BigQueryDatasetConfiguration
        | undefined = this.configCache.source?.configuration;
      if (bigQueryDatasetConfiguration) {
        if (
          bigQueryDatasetConfiguration.dataset_configuration?.dataset_type ==
          BigQueryDatasetType.TABLE
        ) {
          this.changeMade = true;
          let bigQueryDatasetTableConfig:
            | BigQueryDatasetTableConfig
            | undefined = bigQueryDatasetConfiguration.dataset_configuration
            ?.dataset as BigQueryDatasetTableConfig;
          bigQueryDatasetTableConfig.dataset_name = value;
        }
      }
    }
  }

  getDatasetType(): BigQueryDatasetType | undefined {
    if (
      this.configCache &&
      this.isBigQueryDatasetConfiguration(this.configCache.source.configuration)
    ) {
      let bigQueryDatasetConfiguration:
        | BigQueryDatasetConfiguration
        | undefined = this.configCache.source?.configuration;
      if (bigQueryDatasetConfiguration) {
        if (
          bigQueryDatasetConfiguration.dataset_configuration?.dataset_type ==
          BigQueryDatasetType.TABLE
        ) {
          return bigQueryDatasetConfiguration.dataset_configuration
            .dataset_type;
        } else {
          return bigQueryDatasetConfiguration.dataset_configuration
            ?.dataset_type;
        }
      }
    }
    return undefined;
  }

  setDatasetType(value: BigQueryDatasetType) {
    if (!this.configCache) {
      return;
    }
    if (
      this.isBigQueryDatasetConfiguration(this.configCache.source.configuration)
    ) {
      let bigQueryDatasetConfiguration:
        | BigQueryDatasetConfiguration
        | undefined = this.configCache.source?.configuration;
      if (
        bigQueryDatasetConfiguration &&
        bigQueryDatasetConfiguration.dataset_configuration
      ) {
        this.changeMade = true;
        bigQueryDatasetConfiguration.dataset_configuration.dataset_type = value;
        if (
          bigQueryDatasetConfiguration.dataset_configuration.dataset_type ==
          BigQueryDatasetType.TABLE
        ) {
          bigQueryDatasetConfiguration.dataset_configuration.dataset =
            new BigQueryDatasetTableConfig();
          bigQueryDatasetConfiguration.dataset_configuration.dataset.dataset_name =
            'test_demo';
          bigQueryDatasetConfiguration.dataset_configuration.dataset.table_name =
            'BOSTONTRAIN';
        } else if (
          bigQueryDatasetConfiguration.dataset_configuration.dataset_type ==
          BigQueryDatasetType.QUERY
        ) {
          bigQueryDatasetConfiguration.dataset_configuration.dataset =
            new BigQueryDatasetQueryConfig();
          bigQueryDatasetConfiguration.dataset_configuration.dataset.query = this.textBoxQuery;
        }
      }
    }
  }

  getTableName(): string | undefined {
    const config = this.configCache?.source.configuration;

    if (this.isBigQueryDatasetConfiguration(config)) {
      const bigQueryDatasetConfig = config as BigQueryDatasetConfiguration;

      if (
        bigQueryDatasetConfig.dataset_configuration?.dataset_type ===
        BigQueryDatasetType.TABLE
      ) {
        let bigQueryDatasetTableConfig: BigQueryDatasetTableConfig | undefined =
          bigQueryDatasetConfig.dataset_configuration
            ?.dataset as BigQueryDatasetTableConfig;
        return bigQueryDatasetTableConfig.table_name;
      }
    }

    return undefined;
  }

  setTableName(value: string) {
    if (
      this.isBigQueryDatasetConfiguration(
        this.configCache?.source.configuration,
      )
    ) {
      let bigQueryDatasetConfiguration:
        | BigQueryDatasetConfiguration
        | undefined = this.configCache.source?.configuration;
      if (bigQueryDatasetConfiguration) {
        if (
          bigQueryDatasetConfiguration.dataset_configuration?.dataset_type ==
          BigQueryDatasetType.TABLE
        ) {
          this.changeMade = true;
          let bigQueryDatasetTableConfig:
            | BigQueryDatasetTableConfig
            | undefined = bigQueryDatasetConfiguration.dataset_configuration
            ?.dataset as BigQueryDatasetTableConfig;
          bigQueryDatasetTableConfig.table_name = value;
        }
      }
    }
  }

  getQueryString(): string | undefined {
    const config = this.configCache?.source.configuration;

    if (this.isBigQueryDatasetConfiguration(config)) {
      const bigQueryDatasetConfig = config as BigQueryDatasetConfiguration;

      if (
        bigQueryDatasetConfig.dataset_configuration?.dataset_type ===
        BigQueryDatasetType.QUERY
      ) {
        let bigQueryDatasetQueryConfig: BigQueryDatasetQueryConfig | undefined =
          bigQueryDatasetConfig.dataset_configuration
            ?.dataset as BigQueryDatasetQueryConfig;
        return bigQueryDatasetQueryConfig.query;
      }
    }

    return undefined;
  }

  setQueryString(value: any) {
    this.textBoxQuery = value
    if (
      this.isBigQueryDatasetConfiguration(
        this.configCache?.source.configuration,
      )
    ) {
      let bigQueryDatasetConfiguration:
        | BigQueryDatasetConfiguration
        | undefined = this.configCache.source?.configuration;
      if (bigQueryDatasetConfiguration) {
        if (
          bigQueryDatasetConfiguration.dataset_configuration?.dataset instanceof
          BigQueryDatasetQueryConfig
        ) {
          this.changeMade = true;
          let bigQueryDatasetQueryConfig: BigQueryDatasetQueryConfig =
            bigQueryDatasetConfiguration.dataset_configuration?.dataset;
          bigQueryDatasetQueryConfig.query = value;
          this.widgetControl!.Widget.config = this.configCache;
        }
      }
    }
  }

  async loadConnectors() {
    this.projectId = this.configService.SelectedProjectId;
    if(this.projectId){
        let allConnectors = await this.apiService.GetConnectors('1', this.projectId);
    if (allConnectors) {
      this.connectors = allConnectors.filter(
        (t) => t.type === ConnectorType.BIGQUERY,
      );
    }
  }
  }

  singleClickHandler(childItem: string, parentName: string) {
    clearTimeout(this.clickTimeout);
    this.clickTimeout = setTimeout(() => {
      this.selectedChild = childItem;
    }, 250);
   this.parameterButtonStatus = true;
   this.savebutton = false;
   this.childName = childItem;
    this.parentTableName = parentName;
  }

  doubleClickHandler(childItem: string, parentName: string) {
    clearTimeout(this.clickTimeout);
    this.parameterButtonStatus = true;
    this.savebutton = false;
    this.viewTableData(childItem, parentName);
  }

  connectorsOption(event: any){
    this.connectors.filter((session)=>{
      if(session._id === event)
        {
          this.authdetails = session.configuration;
        }
    })

  }


  queryFirstOption(){
    this.textBoxQuery = '';
    this.deleteButton = false;
    this.saveButtonText = 'Save';
    this.queryName = this.widgeFileName ? this.widgeFileName: '';
    this.isLoadQuery = false; 
    this.parameterButtonStatus = false;
    this.savebutton = false;
    this.selectedQuery = 'New Query';
    this.parameters=[];
    this.parameters.push({
      name: '',
      value: '',
      type: '',
      subtype: '',
      required: false
    });
  }

  queryOption(event: any){
    this.textBoxQuery = event.query;

    this.queryName = event.name;
    this.querId = event._id;
    this.deleteButton = true;
    this.isLoadQuery = false;
    this.savebutton = false;  
    this.parameterButtonStatus = false; 
    this.params = event.query_params;
    this.query_params = this.params;
    if (Object.keys(this.query_params).length !== 0) {
      this.populateParametersFromResponse(this.params); 
    }else{
      this.parameters=[];
      this.parameters.push({
        name: '',
        value: '',
        type: '',
        subtype: '',
        required: false
      });
    }
  }

  populateParametersFromResponse(response : any) {
    this.parameters = Object.keys(response).map(key => {
      return {
        name: key,
        value: response[key].value.data,
        type: response[key].type.toLowerCase(),   
        subtype: response[key].value.type.toLowerCase(),
        required: response[key].value.optinal
      };
    });
  }

  confirmDelete(confirm: boolean): void {
    if (confirm) {
      this.deleteItem();
    }
    // Hide the confirmation box
    this.showConfirmationBox = false;
  }

  cancelDelete(){
    this.showConfirmationBox = false;
  }

  async deleteItem(){
    const result : any = await this.connectorService.deleteQuery(
      this.querId,
      this.siteId, 
      this.projectId
    );
    if(result.succeeded){
      this.selectedQuery = 'New Query';
      this.onRadioButtonChange()
      this.queryFirstOption();
      this.toaster.success('Query Deleted Succesfully', '', {
        positionClass: 'custom-toast-position'
      });
    }else{
      this.toaster.error('Query not Deleted Succesfully', '', {
        positionClass: 'custom-toast-position'
      });
    }
  }

  systemGenerate(){
    const dialogRef = this.dialog.open(BigQueryLoadSavedQueryComponent, {
      width: '700px',
      height: '80%',
      data: {
        title:'Usage of System Generate Parameters',
        connectorId: this.connectorId,
        load: false
        },
    });
  }

  addParameter() {
    const lastParameter = this.parameters[this.parameters.length - 1];
    if (lastParameter.name && lastParameter.value && lastParameter.type && lastParameter.subtype) {
      this.parameters.push({
        name: '',
        value: '',
        type: '',
        subtype: '',
        required: false
      });
    } else {
      this.toaster.info('Please fill out all fields before adding a new parameter', '', {
        positionClass: 'custom-toast-position'
      });
    }
    this.savebutton = false;
  }

  removeParameter(index: number) {
    console.log("index")
    this.parameters.splice(index, 1);
  }

  async getQueryResult(){
    let textBoxQueryResult;
      textBoxQueryResult = await this.connectorService.getQueryPreviewData(
        this.textBoxQuery,
        this.siteId, 
        this.projectId,
        this.connectorId,
        this.query_params
      );
    const dialogRef = this.dialog.open(BigQueryResultPreviewComponent, {
      width: '1000px',
      height: '95%',
      data: {
        title:'Big Query Result Data',
        result: textBoxQueryResult,
        tableData: false
      },
    });
    dialogRef.afterClosed().subscribe(() => {});
  }

  get widgeFileName(): string | undefined {
    return this.outputName;
  }

  set widgeFileName(value: string | undefined) {
    this.outputName = value;
    this.changeMade = true;
  }

  bigQuerySaved(event : any){
    let name = event.trim();
    if(name){
      this.queryName = event;
      this.saveButtonText = 'Save As';
    }
  }

  async saveQueryName(){
    if(this.selectedRadioButtonValue === '1'){
      this.datasetType = 'TABLE';
      await this.connectorService.createTableQuery(this.childName,this.parentTableName,this.queryName,this.siteId,this.projectId,this.connectorId)
    }else{
      this.datasetType = 'QUERY';
      this.parameters.forEach(parameter => {
        if(parameter.name !== '' && parameter.type !=='' && parameter.subtype !=='' && parameter.value !=='')
        {
          this.query_params[parameter.name] = {
            "type": parameter.type.toUpperCase(),
            "value": {
              "type": parameter.subtype.toUpperCase(),
              "data": parameter.value
            }
          };
        }else{
          this.query_params = {};
        }
      });
      await this.connectorService.createQuery(
          this.query_params,
          this.textBoxQuery,
          this.queryName,
          this.siteId,
          this.projectId,
          this.connectorId
        )
    }
    
    // Adding the all details to WidgetControl for workflow save

    if(!this.configCache){
      return ;
    }
    this.bigDataConfiguration = this.configCache.source.configuration;
    this.widgetControl!.Widget.config = this.configCache;
  
    this.bigDataConfiguration.dataset_configuration =
    new BigQueryDatasetConfig();
    this.bigDataConfiguration.dataset_configuration.project_id = this.projectId;
    if(this.datasetType == 'QUERY'){
      this.bigDataConfiguration.dataset_configuration.dataset_type = BigQueryDatasetType.QUERY;
      this.bigDataConfiguration.dataset_configuration.dataset = new BigQueryDatasetQueryConfig();
      this.bigDataConfiguration.dataset_configuration.dataset.query = this.textBoxQuery;
      this.bigDataConfiguration.dataset_configuration.dataset.query_params = this.query_params;
    }else{
      this.bigDataConfiguration.dataset_configuration.dataset_type = BigQueryDatasetType.TABLE;
      this.bigDataConfiguration.dataset_configuration.dataset = new BigQueryDatasetTableConfig();
      this.bigDataConfiguration.dataset_configuration.dataset.dataset_name = this.parentTableName;
      this.bigDataConfiguration.dataset_configuration.dataset.table_name = this.childName;
    }
    this.configCache.source.configuration = this.bigDataConfiguration;
    this.widgetControl!.Widget.config = this.configCache;
    let sourceConfiguration: SourceConfiguration = new SourceConfiguration(
      SourceType.BIGQUERY,
      this.bigDataConfiguration,
    );
    let dataCopyWidgetConfig: DataCopyWidgetConfig = new DataCopyWidgetConfig(
      sourceConfiguration,
      WidgetType.DATA_COPY
    );
    dataCopyWidgetConfig.sink = new Sink();
    dataCopyWidgetConfig.sink.dataset_description = 'Big-Query Widget';
    dataCopyWidgetConfig.sink.dataset_name = this.widgetOutput;
    this.widgetControl!.Widget.config = dataCopyWidgetConfig;
    this.savebutton = true;
    this.toaster.success('Saved Succesfully', '', {
      positionClass: 'custom-toast-position'
    });
    //Pop up
  }
  
  getLoadProjectQueries(){

    const dialogRef = this.dialog.open(BigQueryLoadSavedQueryComponent, {
      width: '700px',
      height: '80%',
      data: {
        title:'Big Query load project Data',
        connectorId: this.connectorId,
        load: true
        },
      });
      dialogRef.afterClosed().subscribe((result) => {
        if(result){
          this.textBoxQuery = result.displayQuery;
          this.loadQueryFileName = result.loadQueryFileName;
          this.isLoadQuery = true;
          this.params = result.query_params;
          if (Object.keys(this.params).length !== 0) {
            this.populateParametersFromResponse(this.params); 
          }
        }
      });

  }

  async viewTableData(childName: any, parentName:any){
    this.childName = childName;
    this.parentTableName = parentName;
    let tableResult = await this.connectorService.getTableData(this.parentTableName,this.childName,this.siteId, this.projectId,this.connectorId);
    const dialogRef = this.dialog.open(BigQueryResultPreviewComponent, {
    width: '1000px',
    height: '95%',
    data: {
      title:'Big Query Table Result Data',
      result: tableResult,
      tableData: true
      },
    });
    dialogRef.afterClosed().subscribe(() => {});
  }

  onRadioButtonChange() {
    if (this.selectedRadioButtonValue === '1') {
      this.callTheFunctionalityForDatasetList();
    } else if(this.selectedRadioButtonValue === '2'){
      setTimeout(async () => {
      this.getQueries = await this.connectorService.getallqueries(
        this.siteId, 
        this.projectId,
        this.connectorId,
      );
      this.getQueries =this.getQueries.queries;
    }, 1000);
      
    }
  }

  async callTheFunctionalityForDatasetList() {
    try {
      const getDatasetList = await this.apiService.getDatasetList(
        '1',
        '1',
        this.connectorId,
      );
      if (getDatasetList !== undefined) {
        this.parentItems = this.convertToItemsWithExpandedProperty(
          getDatasetList.data_list,
        );
      } else {
        console.error('getDatasetList is undefined');
      }
    } catch (error) {
      console.error('Error fetching dataset list:', error);
    }
  }

  convertToItemsWithExpandedProperty(
    items: string[],
  ): { name: string; expanded: boolean }[] {
    return items.map((item) => ({ name: item, expanded: false }));
  }

  AuthenticateTheConnector() {
    
    this.spinner = true;
    this.isJsonAuthenticationSuccessful = false;
    this.isJsonAuthenticationFailed = false;
    let obj = {
      "auth_object": this.authdetails.authentication_details,
      "auth_type": "SERVICE_ACCOUNT_FILE"
    };
    this.connectorService.authenticateConnector(this.siteId, this.projectId, obj).subscribe({
      next: (response: any) => {
        this.spinner = false;
        this.isJsonAuthenticationFailed = false
        this.isJsonAuthenticationSuccessful = true;
      },
      error: (error: any) => {
        this.spinner = false;
        this.isJsonAuthenticationSuccessful = false;
        this.isJsonAuthenticationFailed = true
      }
    });
  }

  AuthenticateTheQuery() {}

  openBigQueryPreveiwDialog(): void {
    const dialogRef = this.dialog.open(BigQueryPreviewComponent, {
      width: '1300px',
      height: '95%',
    });
    dialogRef.afterClosed().subscribe(() => {});
  }

  getInputWidget(index: number): Widget | undefined {
    if (!this.configCache) {
      return undefined;
    }

    let urn: string | undefined = this.configCache.inputs[index].input_urn;
    if (urn) {
      return this.inputWidgets.find((t) => t.urn === urn);
    }

    return undefined;
  }

  setInputWidget(index: number, widget: Widget) {
    this.selectedInputWidget = widget;
    if (this.configCache) {
      this.configCache.inputs[index].urn = widget.urn;
    }
  }

  toggleCollapse(parentItem: any) {
    parentItem.expanded = !parentItem.expanded;
    if (parentItem.expanded) {
      this.callTheFunctionalityForTableList(parentItem.name);
    }
  }

  async callTheFunctionalityForTableList(parentName: string) {
    this.TableNames=[];
    try {
      const getTableList = await this.apiService.getTableList(
        '1',
        '1',
        parentName,
        this.connectorId,
      );
      if (getTableList !== undefined) {
        this.TableNames = getTableList.data_list;
      } else {
        console.error('getTableList is undefined');
      }
    } catch (error) {
      console.error('Error fetching Table list:', error);
    }
  }

  get widgetOutput(): any {
    return this.outputName;
  }

  set widgetOutput(value: any) {
    this.outputName = value;
    this.changeMade = true;
  }

  onAppSettingsUpdated() {
    this.changeMade = true;
  }

  onSave() {
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

    this.changeMade = false;
  }

  onCancel() {
    this.settingsComponent.RevertAppSetting();
    // Deep clone to prevent updates from modifying original
    this.configCache = JSON.parse(JSON.stringify(this.config));
    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
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
