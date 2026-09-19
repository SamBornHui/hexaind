import { Component, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import {
  ImageDatasetSelectionWidgetConfig,
  WidgetType,
  ImageTypes,
  WorkflowRun,
  Widget,
  InputOutputConfig
} from 'src/app/models/workflow-models';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { WorkflowCanvasService, ConfigService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { SettingsComponent } from '../settings/settings.component';
import { ToastrService } from 'ngx-toastr';
import { HttpClient } from '@angular/common/http';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { ApiService } from 'src/app/services/api.service';
import { ImageWidgetService } from './services/image-widget.service';
export interface imageDataset {
  dataset_id: string;
  dataset_name: string;
  dataset_location: string;
  segmented: boolean;
  defect_metadata_path?:string
  // Add other properties here as needed
}

@Component({
  selector: 'app-image-dataset-selection-widget',
  templateUrl: './image-dataset-selection-widget.component.html',
  styleUrls: ['./image-dataset-selection-widget.component.less']
})
export class ImageDatasetSelectionWidgetComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  selectedRun: WorkflowRun | undefined = undefined;
  changeMade: boolean = false;
  outputChangeMade: boolean = false;
  inputChangeMade: boolean = false;
  widget: any;
  changeSetting: boolean = false;
  config: ImageDatasetSelectionWidgetConfig | undefined = undefined;
  configCache: ImageDatasetSelectionWidgetConfig | undefined = undefined;
  widgetControl: WidgetControl | undefined;
  selectedImageType = ImageTypes.Segmented;
  imagesTypes = Object.values(ImageTypes).filter(
    (value) => typeof value === 'string',
  );
  selectedDatasets:any[] = [];
  imagesDatasets:imageDataset[] = [];
  selectedInputWidget: Widget | undefined = undefined;
  outputName: string | undefined = undefined;
  inputName: string | undefined = undefined;
  widgetdataInformation = {};
  inputWidgets: Widget[] = [];


  selectedFiles: File[] = [];

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private route: ActivatedRoute,
    private dialog: MatDialog,
    public sharedDataService: SharedDataService,
    public toaster: ToastrService,
    private http: HttpClient,
    private workflowsSessionsApiService:WorkflowsSessionsApiService,
    private configService:ConfigService,
    private apiService:ApiService,
    private imageWidgetService:ImageWidgetService

  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.widget = this.widgetControl.Widget as Widget;
    this.config = this.widgetControl.Widget.config as ImageDatasetSelectionWidgetConfig;
    this.config.widget_type = WidgetType.IMAGE_DATASET;
    this.configCache = JSON.parse(JSON.stringify(this.config));

    if (this.configCache?.image_type === ImageTypes.Raw) {
      this.selectedImageType = ImageTypes.Raw;
    } else if(this.configCache?.image_type === ImageTypes.Segmented) {
      this.selectedImageType = ImageTypes.Segmented;
    }

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
    this.getImagesDatasets();
  }
  getFilteredDatasets(){
    let filteredDatasets;
    if (this.selectedImageType === ImageTypes.Segmented) {
      filteredDatasets = this.imagesDatasets.filter((dataset: imageDataset) => dataset.segmented);
    } else {
      filteredDatasets = this.imagesDatasets;
    }
    return filteredDatasets;

  }
  getImagesDatasets(){
    this.apiService
      .getImageDatasets(this.configService.SelectedSiteId,this.configService.SelectedProjectId)
      .subscribe({
        next: (response:any) => {
          if (response) {
            if(response['image_datasets']){
              this.imagesDatasets = response['image_datasets'];
              if(this.configCache && this.configCache.image_datasets && this.configCache.image_datasets.length>0){
                let datasetIds = this.configCache.image_datasets.map((datasets:any)=>datasets.dataset_id);
                if(datasetIds.length>0){
                  let selectedDatasts = this.imagesDatasets.filter((dataset:imageDataset)=>datasetIds.includes(dataset.dataset_id));
                  this.selectedDatasets = selectedDatasts;
                }
              }
            }else{
              this.imagesDatasets = [];
            }
          }
        },
        error: (error:any) => {
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
  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 3;
  }

  loadFeatures() {
    this.widgetdataInformation = {
      type: this.widgetControl?.Widget.type + ' widget',
      description: 'The Image Dataset Widget provides functionalities for ingesting, filtering, and managing image datasets. It supports metadata-driven filtering and tagging for efficient dataset curation and preparation for image analytics workflows.',
      version: this.configCache?.version,
      image_dataset_selection_information:true
    };
  }
  storeSelectedImageType(type:any){
    this.selectedImageType = type;
    if (
      !this.configCache ||
      !this.configCache.image_type
    ) {
      return;
    }

    this.configCache.image_type = type;
    this.changeMade = true;
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

  onSave() {
    if(this.selectedDatasets.length>0){
      let datasetsToBeSaved = this.selectedDatasets.map((dataset: imageDataset) => {
        return {
          dataset_id: dataset.dataset_id,
          dataset_name: dataset.dataset_name,
          defect_metadata_path:dataset.defect_metadata_path
        };
      });
      if (this.configCache && datasetsToBeSaved.length) {
        this.configCache.image_datasets = datasetsToBeSaved;
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

  onCheckboxChange(event:any, dataset_id:string){
    if(event.checked){
      let datasets = this.getFilteredDatasets();
      let datasetIndex = datasets.findIndex((dataset:imageDataset)=>dataset.dataset_id == dataset_id);
      this.selectedDatasets.push(datasets[datasetIndex])
    }else{
      let datasetIndex = this.selectedDatasets.findIndex((dataset:any)=>dataset.dataset_id == dataset_id);
      if (datasetIndex !== -1) {
        this.selectedDatasets.splice(datasetIndex, 1);
      } 
    }
    this.changeMade = true;
  }
  isSelectedDataset(dataset_id:string){
    let datasets = this.selectedDatasets.filter((dataset:any)=>dataset.dataset_id == dataset_id);
    if(datasets.length>0){
      return true;
    }else{
      return false;
    }
  }
  getFilename(dataset:imageDataset){
    if(dataset.defect_metadata_path && dataset.defect_metadata_path !=''){
      return dataset.defect_metadata_path.split('/').pop();
    }else{
      return '';
    }
  }

  onFilesSelected(event: any, dataset:any) {
    const selectedFiles = event.target.files;
    this.selectedFiles = [];
    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      var fileMatch = this.selectedDatasets.filter(
        (val: any) => val.dataset_name+'.csv' === file.name,
      );
      if (fileMatch.length > 0) {
        file['dataset_id'] = fileMatch[0].dataset_id;
        file['dataset_location'] = fileMatch[0].dataset_location;     
        this.selectedFiles.push(file);
      }
    }
    
    if(this.selectedFiles.length>0){
      let data = {
        siteId: this.configService.SelectedSiteId,
        projectId: this.configService.SelectedProjectId,
        files: this.selectedFiles,
      };
      this.imageWidgetService.uploadMetaDataFiles(data).subscribe({
        next: (response:any) => {
          if(response && response.defect_metadata){
            response.defect_metadata.forEach((element:any) => {
              let index = this.selectedDatasets.findIndex((dataset:any)=>dataset.dataset_id==element.dataset_id);
              let index2 = this.imagesDatasets.findIndex((dataset:imageDataset)=>dataset.dataset_id==element.dataset_id);
              if(index != -1){
                this.selectedDatasets[index]['defect_metadata_path'] =  element.file_path;                
              }
              if(index2 != -1){
                this.imagesDatasets[index2]['defect_metadata_path'] =  element.file_path;           
              }              
            });
            this.changeMade = true;
          }
        },
        error: (error) => {
          // this.uploadScriptFlag = false;
          console.error('Upload error', error);
        },
      });
    }

  }


}
