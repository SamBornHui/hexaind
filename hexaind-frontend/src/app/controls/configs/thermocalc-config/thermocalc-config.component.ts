import { Component, EventEmitter, Output, ViewChild } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import {
  Connector,
  ConnectorType,
  ThermoCalcConnectorConfiguration,
} from 'src/app/models/connector-models';
import {
  InputOutputConfig,
  ThermoCalcWidgetConfig,
  Widget,
  WidgetType,
} from 'src/app/models/workflow-models';
import { ActivatedRoute } from '@angular/router';
import { MatTableDataSource } from '@angular/material/table';
import { HttpClient } from '@angular/common/http';
import { ThermoCalcWidgetService } from './services/thermocalc-widget.service';
import { MatDialog } from '@angular/material/dialog';
import { SettingsComponent } from '../settings/settings.component';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { ToastrService } from 'ngx-toastr';
import { ImportDatasetDialogComponent } from 'src/app/dialogs/import-dataset-dialog/import-dataset-dialog.component';
import { ShowModuleDialogComponent } from 'src/app/dialogs/show-module-dialog/show-module-dialog.component';

@Component({
  selector: 'app-thermocalc-config',
  templateUrl: './thermocalc-config.component.html',
  styleUrls: ['./thermocalc-config.component.less'],
})
export class ThermoCalcConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  changeMade: boolean = false;
  config: ThermoCalcWidgetConfig | undefined = undefined;
  configCache: ThermoCalcWidgetConfig | undefined = undefined;
  outputName: string | undefined = undefined;
  inputName: string | undefined = undefined;

  public widgetControl: WidgetControl | undefined = undefined;
  private projectId: string = '';
  private siteId: string = '';
  private workflowId: string = '';
  
  connectors: Connector[] = [];
  isAuthenticationFailed: boolean = false;
  isAuthenticationSuccessful: boolean = false;
  spinner: boolean = false;
  
  data = {};
  selectedFiles: File[] = [];
  selectedInputWidget: Widget | undefined = undefined;
  inputWidgets: Widget[] = [];
  outputChangeMade:boolean = false;
  inputChangeMade:boolean = false;
  moduleInfo:object = {}
  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private apiService: ApiService,
    private route: ActivatedRoute,
    private thermoCalcService: ThermoCalcWidgetService,
    public sharedDataService: SharedDataService,
    private toaster: ToastrService,
    private dialog:MatDialog
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.config = this.widgetControl.Widget.config as ThermoCalcWidgetConfig;
    this.configCache = JSON.parse(JSON.stringify(this.config));

    if (this.widgetControl.Widget.outputs.length) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
    }
    if (this.widgetControl.Widget.inputs.length) {
      this.inputName = this.widgetControl.Widget.inputs[0].name;
    }

    this.route.queryParams.subscribe((params) => {
      this.projectId = params['projectId'];
      this.siteId = params['siteId'];
      this.workflowId = params['workflowId'];
    });
  }

  ngOnInit() {
    this.loadConnectors();

    this.data = {
      type: this.widgetControl?.Widget.type,
      description: this.widgetControl?.Widget.description,
      version: this.config?.version,
    };
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.workflowCanvasService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );

      // Remove any widgets that dont have outputs.
      if (this.inputWidgets && this.inputWidgets.length > 0) {
        this.inputWidgets = this.inputWidgets.filter(
          (widget) => widget.outputs.length > 0,
        );

        if (this.widgetControl.Widget.inputs.length > 0) {
          this.selectedInputWidget = this.inputWidgets.find(
            (t) => t.urn === this.widgetControl?.Widget.inputs[0].urn,
          );
        }else{
          if(this.inputWidgets.length === 1){
            this.selectedInputWidget = this.inputWidgets[0];
            this.onInputSave();
          }
        }
      }
      if (this.widgetControl.Widget.outputs.length) {
        this.outputName = this.widgetControl.Widget.outputs[0].name;
      }
    }

    if(this.configCache && this.configCache.module_id){
      this.getModuleInfo(this.configCache.module_id)
    }
  }
  
  moduleName(){
    if(this.moduleInfo && 'name' in this.moduleInfo && this.moduleInfo.name !=""){
      return this.moduleInfo.name
    }else{
      return ''
    }
  }
  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  selectScriptFileDialog() {
    const dialogRef = this.dialog.open(ShowModuleDialogComponent, {
      width: '90%',
      height: '90%',
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        if (this.configCache) {
          this.configCache.module_id = result.module._id;
          this.moduleInfo = result.module;
          this.changeMade = true;
          this.getFeatuers();
        }
      }
    });
  }


  importScriptFileDialog() {
    if (this.getConnectorId() != '' && this.getConnectorId() != undefined) {
      const dialogRef = this.dialog.open(ImportDatasetDialogComponent, {
        height: '90%',
        width: '60%',
        data: {
          file_type: 'python',
          destination_folder: '',
        },
      });
      dialogRef.afterClosed().subscribe((result) => {
        if (result.success) {
          this.configCache!.module_id = result.module_id;
          this.getModuleInfo(result.module_id);
          this.getFeatuers();
        }
      });
    }
  }

  onUploadJSONFile(event: any) {
    const file: File = event.target.files[0];
    if (file) {
      this.thermoCalcService
        .readJsonFile(file)
        .then((jsonData) => {
          this.setThermoCalcConfigs(JSON.stringify(jsonData));
        })
        .catch((error) => {
          const errorMessage =
            error?.error?.message ||
            error?.message ||
            'Error while reading JSON file';
          this.toaster.error(errorMessage, 'ERROR', {
            positionClass: 'custom-toast-position',
          });
        });
    }
  }

  getFeatuers() {
    if (this.configCache && this.configCache.module_id) {
      this.thermoCalcService
        .getFeatures(this.siteId, this.projectId, this.configCache.module_id)
        .subscribe({
          next: (response) => {
            if (this.configCache) {
              this.configCache.input_features = response.input_features;
              this.configCache.output_features = response.output_features;
              this.changeState();
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

  getModuleInfo(moduleId:string) {
    if (this.configCache && this.configCache.module_id) {
      this.thermoCalcService
        .getModuleInfo({
          siteId:this.siteId, 
          projectId:this.projectId, 
          moduleId:moduleId
        })
        .subscribe({
          next: (response) => {
           this.moduleInfo = response
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


  onChanageConnector() {
    this.isAuthenticationFailed = false;
    this.isAuthenticationSuccessful = false;
  }

  isRescaleConnectorSelected() {
    return this.configCache?.thermocalc_connector_id ? false : true;
  }

  authentication() {
    this.onChanageConnector();
    if (this.configCache?.thermocalc_connector_id) {
      let connection = this.connectors.filter(
        (val) => val._id == this.configCache?.thermocalc_connector_id,
      );
      if (connection.length > 0) {
        let configuration = connection[0]
          .configuration as ThermoCalcConnectorConfiguration;
        this.spinner = true;
        this.thermoCalcService
          .authenticate(this.siteId, this.projectId, configuration)
          .subscribe({
            next: (response: any) => {
              this.spinner = false;
              this.isAuthenticationFailed = false;
              this.isAuthenticationSuccessful = true;
            },
            error: (error: any) => {
              this.spinner = false;
              this.isAuthenticationSuccessful = false;
              this.isAuthenticationFailed = true;
            },
          });
      }
    }
  }

  async loadConnectors() {
    let allConnectors = await this.apiService.GetConnectors(
      this.siteId,
      this.projectId,
    );
    if (allConnectors) {
      var connectors = allConnectors.filter(
        (t) => t.type === ConnectorType.THERMOCALC,
      );
      this.connectors = connectors;
    }
  }
  getModuleId(): any | undefined {
    if (!this.configCache) {
      return;
    }
    return this.configCache.module_id;
  }
  setConnectorId(connectorId: string | undefined) {
    if (!this.configCache) {
      return;
    }
    if (this.configCache) {
      this.configCache.thermocalc_connector_id = connectorId;
    }
    this.onChanageConnector();
    this.changeState();
  }

  getThermoCalcConfigs(): string | undefined {
    if (!this.configCache) {
      return undefined;
    }
    if(this.configCache?.json_config){
      return JSON.stringify(this.configCache?.json_config, null, 2);
    }else{
      return undefined;
    }
  }

  setThermoCalcConfigs(value: string) {
    if (!this.configCache) {
      return undefined;
    }
    if (this.configCache) {
      let jsonObject = JSON.parse(value);
      this.configCache.json_config = jsonObject;
      this.changeState();
    }
  }

  getConnectorId() {
    if (!this.configCache) {
      return undefined;
    }
    return this.configCache.thermocalc_connector_id;
  }

  connectionIdActive() {
    if (this.getConnectorId() != '' && this.getConnectorId() != undefined) {
      return true;
    } else {
      return false;
    }
  }

  getSelectedInputWidget(): Widget | undefined {
    return this.selectedInputWidget;
  }

  setSelectedInputWidget(widget: Widget) {
    this.inputChangeMade = true;
    this.selectedInputWidget = widget;
  }
  onInputCancel() {
    this.loadSelectedInputWidget();
    this.inputChangeMade = false;
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
    }
  }
  onInputSave() {
    if (this.selectedInputWidget) {
      let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
      inputOutputConfig.name = this.selectedInputWidget.outputs[0].name;
      inputOutputConfig.urn = this.selectedInputWidget.urn;
      if (this.widgetControl) {
        this.widgetControl.Widget.inputs.length = 0;
        this.widgetControl.Widget.inputs.push(inputOutputConfig);
      }
      this.inputChangeMade = false;
    }
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

  onOutputCancel() {
    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
    }
    this.outputChangeMade = false;
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
    this.outputChangeMade = false;
  }
  onSave() {
    if (!this.configCache) {
      return;
    }
    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.settingsComponent.SaveAppSettings();
    if (this.widgetControl) {
      this.widgetControl.Widget.config = this.configCache;
      this.config = this.widgetControl.Widget.config;
      let clonedConfig = JSON.parse(JSON.stringify(this.config));
      this.configCache = clonedConfig;
      this.changeMade = false;
    } else {
      console.error('Widget control is not available');
      return;
    }
  }

  onCancel() {
    this.configCache = JSON.parse(JSON.stringify(this.config));
    this.changeMade = false;
  }
  changeState() {
    this.changeMade = true;
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }
}
