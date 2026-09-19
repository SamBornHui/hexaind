import { Component, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import {
  ImageRegionPropertiesWidgetConfig,
  WidgetType,
  WorkflowRun,
  Widget,
  InputOutputConfig,
  GeometricProperties,
  GeometricPropertiesScaled,
  CalculatedPropertiesScaled,
  IntensityBasedProperties
} from 'src/app/models/workflow-models';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { WorkflowCanvasService, ConfigService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { SettingsComponent } from '../settings/settings.component';
import { ToastrService } from 'ngx-toastr';
import { HttpClient } from '@angular/common/http';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { ApiService } from 'src/app/services/api.service';

export interface imageDataset {
  dataset_id: string;
  dataset_name: string;
  dataset_location: string;
  segmented: boolean;
  // Add other properties here as needed
}

@Component({
  selector: 'app-image-region-properties-widget',
  templateUrl: './image-region-properties-widget.component.html',
  styleUrls: ['./image-region-properties-widget.component.less']
})
export class ImageRegionPropertiesWidgetComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  selectedRun: WorkflowRun | undefined = undefined;
  changeMade: boolean = false;
  outputChangeMade: boolean = false;
  inputChangeMade: boolean = false;
  widget: any;
  changeSetting: boolean = false;
  config: ImageRegionPropertiesWidgetConfig | undefined = undefined;
  configCache: ImageRegionPropertiesWidgetConfig | undefined = undefined;
  widgetControl: WidgetControl | undefined;
  selectedProperties:string[] = [];

  selectedInputWidget: Widget | undefined = undefined;
  outputName: string | undefined = undefined;
  inputName: string | undefined = undefined;
  widgetdataInformation = {};
  inputWidgets: Widget[] = [];

  checkPropertiesFlags:any = {
    geometric_properties:false,
    geometric_properties_scaled:false,
    intensity_based_properties:false
  }

  geometricProperties:string[] = Object.values(GeometricProperties) as string[]
  geometricPropertiesScaled:string[] = Object.values(GeometricPropertiesScaled) as string[]
  intensityBasedProperties:string[] = Object.values(IntensityBasedProperties) as string[]

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private route: ActivatedRoute,
    private dialog: MatDialog,
    public sharedDataService: SharedDataService,
    public toaster: ToastrService,
    private http: HttpClient,
    private workflowsSessionsApiService:WorkflowsSessionsApiService,
    private configService:ConfigService,
    private apiService:ApiService

  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.widget = this.widgetControl.Widget as Widget;
    this.config = this.widgetControl.Widget.config as ImageRegionPropertiesWidgetConfig;
    this.configCache = JSON.parse(JSON.stringify(this.config));

    if (this.widgetControl.Widget.outputs.length) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
    }
    if (this.widgetControl.Widget.inputs.length) {
      this.inputName = this.widgetControl.Widget.inputs[0].name;
    }
  }
  ngOnInit(){
    this.loadFeatures()
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.workflowCanvasService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );
    }
    if(this.configCache && this.configCache.region_properties.length>0){
      this.selectedProperties = this.configCache!.region_properties
    }

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
        this.loadSelectedInputWidget();
      }
    }
  }

  toggleAllProperties(event:boolean,type:string){
    if(type == 'geometric_properties'){
      if(event){
        this.selectedProperties = Array.from(new Set([...this.selectedProperties, ...this.geometricProperties]));
        this.changeMade = true;      
      }else{
        this.selectedProperties = this.selectedProperties.filter(item => !this.geometricProperties.includes(item))
        this.changeMade = true;
      }
    }else if(type == 'geometric_properties_scaled'){
      if(event){
        this.selectedProperties = Array.from(new Set([...this.selectedProperties, ...this.geometricPropertiesScaled]));
        this.changeMade = true;      
      }else{
        this.selectedProperties = this.selectedProperties.filter(item => !this.geometricPropertiesScaled.includes(item))
        this.changeMade = true;
      }
    }else if(type == 'intensity_based_properties'){
      if(event){
        this.selectedProperties = Array.from(new Set([...this.selectedProperties, ...this.intensityBasedProperties]));
        this.changeMade = true;      
      }else{
        this.selectedProperties = this.selectedProperties.filter(item => !this.intensityBasedProperties.includes(item))
        this.changeMade = true;
      }
    }
  }
  isSelectedProperty(property:string){
    return this.selectedProperties.includes(property)
  }  
  
  onCheckboxChange(event: any, property: string) {
    if (event) {
      this.selectedProperties.push(property);
      if(property =='axis_minor_length' || property =='axis_major_length'){
        let array2 = ['axis_minor_length','axis_major_length'];
        const allItemsExist = array2.every((item:any) => this.selectedProperties.includes(item));
        if(allItemsExist){
          this.selectedProperties.push('A.R_ell');
        }
      }
    } else {
      const index = this.selectedProperties.indexOf(property);
      if (index > -1) {
        this.selectedProperties.splice(index, 1);
      }

      if(property =='axis_minor_length' || property =='axis_major_length'){
        const index = this.selectedProperties.indexOf('A.R_ell');
        if (index > -1) {
          this.selectedProperties.splice(index, 1);
        }
      }
    }
    this.changeMade = true;
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 3;
  }

  loadFeatures() {
    this.widgetdataInformation = {
      type: this.widgetControl?.Widget.type + ' widget',
      description: 'The Region Props Widget computes region-based geometric and intensity properties from segmented images. The extracted properties are stored in tabular format for use in feature extraction, training, or evaluation workflows.',
      version: this.configCache?.version,
      region_properties_information: true
    };
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
    } else {
      if (this.inputWidgets.length === 1) {
        this.selectedInputWidget = this.inputWidgets[0];
        this.onInputSave();
      }
    }
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

  onOutputCancel() {
    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
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
  setSelectedProperties(event:any){
    this.changeMade = true;
  }
  onSave() {
    if(this.selectedProperties.length>0){
      if (this.configCache && this.selectedProperties.length>0) {
        this.configCache.region_properties = this.selectedProperties;
      }            
    }else{
      this.toaster.error('Please select the properties', '', {
        positionClass: 'custom-toast-position',
      });
      return;
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
    // Deep clone to prevent updates from modifying original
    this.configCache = JSON.parse(JSON.stringify(this.config));
    this.changeMade = false;
    this.loadFeatures();
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

}
