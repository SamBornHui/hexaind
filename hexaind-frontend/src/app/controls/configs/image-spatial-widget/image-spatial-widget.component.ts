import { Component, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import {
  ImageRegionPropertiesWidgetConfig,
  WidgetType,
  WorkflowRun,
  Widget,
  InputOutputConfig,
  ImageDataset,
  ImageDatasetSelectionWidgetConfig,
  ImageSpatialStatisticsWidgetConfig
} from 'src/app/models/workflow-models';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { WorkflowCanvasService, ConfigService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { SettingsComponent } from '../settings/settings.component';
import { ToastrService } from 'ngx-toastr';
import { HttpClient } from '@angular/common/http';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { ImageSpatialWidgetService } from './services/image-spatial-widget.service';
import { WebSocketService } from 'src/app/services/web-sockets.service';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

export interface imageDataset {
  dataset_id: string;
  dataset_name: string;
  dataset_location: string;
  segmented: boolean;
  // Add other properties here as needed
}
export interface quantificationModel {
  title: string;
  value: string;
}
export interface phaseModel {
  title: string;
  value: number[];
}
@Component({
  selector: 'app-image-spatial-widget',
  templateUrl: './image-spatial-widget.component.html',
  styleUrls: ['./image-spatial-widget.component.less']
})
export class ImageSpatialWidgetComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  selectedRun: WorkflowRun | undefined = undefined;
  changeMade: boolean = false;
  outputChangeMade: boolean = false;
  inputChangeMade: boolean = false;
  widget: any;
  changeSetting: boolean = false;
  config: ImageSpatialStatisticsWidgetConfig | undefined = undefined;
  configCache: ImageSpatialStatisticsWidgetConfig | undefined = undefined;
  widgetControl: WidgetControl | undefined;
  selectedQuantification:string = '';

  selectedInputWidget: Widget | undefined = undefined;
  outputName: string | undefined = undefined;
  inputName: string | undefined = undefined;
  widgetdataInformation = {};
  inputWidgets: Widget[] = [];
  quantificationList: quantificationModel[] = [
    { title: "Two-point Statistics", value: "TwoPointStats" },
    { title: "Pair-correlations", value: "PairCorrelation" },
    { title: "Rotationally Invariant 2-pt Statistics", value: "RotatInvariance" },
    { title: "Angulary Resolved Chord Length Distributions", value: "AngularyResolvedChordLengthDistributions" },
    { title: "Chord Length Distributions", value: "ChordLengthDist" }
  ];
  phaseList:any = {
    "TwoPointStats": [
      { title: "[Phase1, Phase1]", value: [0, 0] },
      { title: "[Phase1, Phase2]", value: [0, 1] },
      { title: "[Phase2, Phase1]", value: [1, 0] },
      { title: "[Phase2, Phase2]", value: [1, 1] }
    ],
    "PairCorrelation": [
      { title: "[Phase1, Phase1]", value: [0, 0] },
      { title: "[Phase1, Phase2]", value: [0, 1] },
      { title: "[Phase2, Phase1]", value: [1, 0] },
      { title: "[Phase2, Phase2]", value: [1, 1] }
    ],
    "RotatInvariance": [
      { title: "[Phase1, Phase1]", value: [0, 0] },
      { title: "[Phase1, Phase2]", value: [0, 1] },
      { title: "[Phase2, Phase1]", value: [1, 0] },
      { title: "[Phase2, Phase2]", value: [1, 1] }
    ],
    "AngularyResolvedChordLengthDistributions": [
      { title: "Phase1", value: [0] },
      { title: "Phase2", value: [1] }
    ],
    "ChordLengthDist": [
      { title: "Phase1", value: [0] },
      { title: "Phase2", value: [1] }
    ]
  }

  addedPhaseList:phaseModel[] = [];
  highlightedPhase:string = "";
  featureTypeResult:any = [];
  selectedPhase:string = '';

  selectedDataset:any = {};
  datasetId:any = '';
  datasetImages:any[] = [];
  metadata:string = '';
  imageDisplayUrl = `${this.configService.getImageDatasetUrl()}/get_image_contnet_by_path`;
  selectedImage:any[] = [];
  cutoff = 2;
  angularInterval = 15;
  coarsening = 1;
  cutoffSlider:any = {
    min:0,
    max:0,
    stepValue:0
  }
  apiCall: boolean = false;
  angImageView: boolean = false;
  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private route: ActivatedRoute,
    private dialog: MatDialog,
    public sharedDataService: SharedDataService,
    public toaster: ToastrService,
    private http: HttpClient,
    private workflowsSessionsApiService:WorkflowsSessionsApiService,
    private configService:ConfigService,
    private imageSpatialWidgetService:ImageSpatialWidgetService,
    private webSocketService: WebSocketService,
    public sanitizer: DomSanitizer

  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.widget = this.widgetControl.Widget as Widget;
    this.config = this.widgetControl.Widget.config as ImageSpatialStatisticsWidgetConfig;
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
    // if(this.configCache && this.configCache.region_properties.length>0){
    //   this.selectedProperties = this.configCache!.region_properties
    // }

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
        // this.getConnectedDatasetInformation();
        this.loadSelectedInputWidget();
      }
    }
    this.assignConfigValues();

  }
  assignConfigValues(){
    if (this.configCache) {
      console.log(this.configCache)
      var imageConfig = this.inputWidgets[0].config;
      if ("image_datasets" in imageConfig) {
        let datasets: ImageDataset[] = imageConfig.image_datasets;
        if(this.configCache.datasetId && this.configCache.datasetId !=''){
          if(this.configCache.datasetId != datasets[0].dataset_id){
            this.datasetId = datasets[0].dataset_id;
          }else{
            this.datasetId = this.configCache.datasetId;
          }
        }else{
          if (datasets[0]?.dataset_id) {
            this.datasetId = datasets[0].dataset_id;
            this.configCache.datasetId = datasets[0].dataset_id;
          } 
          // this.configCache.datasetId = datasets[0].dataset_id;
        }
        this.getDatasetImages();

      }
      if(this.configCache.cutoff){
        this.cutoff = this.configCache.cutoff;
      }
      if(this.configCache.ang_int){
        this.angularInterval = this.configCache.ang_int;
      }
      if(this.configCache.coarsening){
        this.coarsening = this.configCache.coarsening;
      }
      if(this.configCache.quantTech !=''){
        this.selectedQuantification = this.configCache.quantTech;
        if(this.configCache.local_states && this.configCache.local_states.length>0){
          this.addedPhaseList = this.phaseList[this.configCache.quantTech].filter((item:any) =>
            this.configCache?.local_states.some(
              filterVal => JSON.stringify(filterVal) === JSON.stringify(item.value)
            )
          );
        }
      }
    }
  }

  changeQuantificationTechnique() {
    this.addedPhaseList = [];
    this.highlightedPhase = "";
    this.featureTypeResult = [];
    this.changeMade = true;
    if(this.configCache){
      this.configCache.local_states = [];
      this.configCache.quantTech = this.selectedQuantification;
      this.changeMade = true;
    }
  }

  imageUrl(image:any){
    return (image)?`${this.imageDisplayUrl}?file_path=${image.thumbnail_path}&&file_name=${this.getImageName(image.path)}`:'';
  }
  getImageName(filePath: string): string {
    if (filePath) {
      const parts = filePath.split('/');
      return parts.pop() || ''; // Returns the last part or an empty string if the path is empty
    } else {
      return 'viewimage';
    }
  }
  imageFeatureStats(image:any){
    if (image.selected) {
      image.selected = false;
      var newSelected = [];
      for (var i = 0; i < this.selectedImage.length; i++) {
        if (this.selectedImage[i].path != image.path) {
          newSelected.push(this.selectedImage[i]);
        }
      }
      this.selectedImage = newSelected;
      var index = this.featureTypeResult.findIndex((val:any) => val['orignal_path'] == image.path);
      this.featureTypeResult.splice(index, 1);
    } else {
      if (this.selectedImage.length == 2) {
        this.toaster.error('Only two images can be compared at once. Please un-check one of the previous selection');
        return;
      } else {
        image.selected = true;
        this.selectedImage.push(image);
        if (this.selectedImage.length > 0 && this.addedPhaseList.length > 0 && this.highlightedPhase != "") {
          this.featureTypeResult = [];
          this.callMultipleImages();
        }
      }
    }

  }
  callMultipleImages() {
    var paths = [];
    for (var i = 0; i < this.selectedImage.length; i++) {
      paths.push(this.selectedImage[i].path);
    }
    if(this.selectedImage.length>0){
      this.getComparisonImages(paths);
    }
  }
  deleteAddedPhase() {
    this.addedPhaseList = [];
    this.highlightedPhase = "";
    this.featureTypeResult = [];
    this.changeMade = true;
    if(this.configCache){
      this.configCache.local_states = [];
      this.changeMade = true;
    }
  }

  deleteOneAddedPhase(title:any) {
    this.addedPhaseList = this.addedPhaseList.filter((phase:phaseModel)=>phase.title !=title)
    if (this.addedPhaseList.length == 0) {
      this.highlightedPhase = "";
      this.featureTypeResult = [];
    }
    if(this.configCache){
      this.configCache.local_states = (this.addedPhaseList.length>0)?this.addedPhaseList.map((phase:phaseModel)=>phase.value):[];
      this.changeMade = true;
    }
    
  }

  highLightPhase(phase:string) {
    this.highlightedPhase = phase;
    this.featureTypeResult = [];
    if(this.selectedImage.length==0){
      this.toaster.error('Please select image first');
      return
    }
    this.callMultipleImages();
  }

  getComparisonImages(image:any) {
    let index = this.addedPhaseList.findIndex(val => val.title == this.highlightedPhase);
    if(index != -1){
      let value = this.addedPhaseList[index].value;
      let inputData:any = {
        "path_image": image,
        "cutoff": this.cutoff,
        "local_state_1": value[0],
        "quantTech": this.selectedQuantification,
        "user_id": localStorage.getItem('currUserID'),
        "metadata": this.metadata
      }
      if (this.selectedQuantification == "TwoPointStats" || this.selectedQuantification == "RotatInvariance" || this.selectedQuantification == "PairCorrelation") {
        inputData["local_state_2"] = value[1];
      } else {
        inputData["local_state_2"] = 0;
      }
      inputData["ang_int"] = this.angularInterval;
      if (this.selectedQuantification == "AngularyResolvedChordLengthDistributions" || this.selectedQuantification == "ChordLengthDist") {
        inputData["coarsening"] = this.coarsening;
      }
      this.apiCall = true;
      this.featureTypeResult = [];
      this.imageSpatialWidgetService
      .quanticationTechnique(this.configService.SelectedSiteId,this.configService.SelectedProjectId,this.datasetId,inputData)
      .subscribe({
        next: (response:any) => {
          if (response) {
            
            let visualized_plots:any = response['visualized_plots'];
              for(let i=0;i<visualized_plots.length;i++){
                let feature = visualized_plots[i];
                feature["microstructure_image"] = this.sanitizer.bypassSecurityTrustResourceUrl(`${this.configService.getAppAuxApiURL}/eda/file?path=${feature["microstructure_image"]}`)
                if('visualized_plot' in feature){
                  feature["visualized_plot"] = this.sanitizer.bypassSecurityTrustResourceUrl(`${this.configService.getAppAuxApiURL}/eda/file?path=${feature["visualized_plot"]}`)
                }
                if('visualize_ARCLD_Angle' in feature){
                  feature["visualize_ARCLD_Angle"] = this.sanitizer.bypassSecurityTrustResourceUrl(`${this.configService.getAppAuxApiURL}/eda/file?path=${feature["visualize_ARCLD_Angle"]}`)
                }
                this.featureTypeResult.push(feature);

              }
            setTimeout(() => {
              this.apiCall = false;
            }, 50);
              
          }else{
            this.apiCall = false;
            this.toaster.error(response['msg']);
          }
        },
        error: (error:any) => {
          const errorMessage = error?.error?.message || error?.message || 'An unexpected error occurred';
          this.toaster.error(errorMessage, 'ERROR', {
            positionClass: 'custom-toast-position',
          });
        },
      });
    }
  }

  changeAngImageView() {
    if (this.angImageView) {
      this.angImageView = false;
    } else {
      this.angImageView = true;
    }
  }
  
  getDatasetImages(){
    if(this.datasetId && this.datasetId !=''){
      this.imageSpatialWidgetService
      .getSegmentedImages(this.configService.SelectedSiteId,this.configService.SelectedProjectId,this.datasetId)
      .subscribe({
        next: (response:any) => {
          if (response) {
            if (response['status']) {
              if (response['data']) {
                var data = response['data']['imagesdata'];
                this.metadata = response['data']['metadata'];

                if(this.configCache){
                  if(this.configCache.metadata != this.metadata){
                    this.configCache.metadata = this.metadata;
                    this.changeMade = true;  
                  }
                }
                for (var i = 0; i < data.length; i++) {
                  data[i]['selected'] = false;
                }
                this.datasetImages = data;
                this.setCutOffValue();
              }
            } else {
              if (response['message']) {
                this.toaster.error(response['message']);
              } else {
                this.toaster.error(response['msg']);
              }
              // this.router.navigate(['/assets']);
            }
          }
        },
        error: (error:any) => {
          const errorMessage = error?.error?.message || error?.message || 'An unexpected error occurred';
          this.toaster.error(errorMessage, 'ERROR', {
            positionClass: 'custom-toast-position',
          });
        },
      });
    }    
  }
  changeSliders() {
    this.featureTypeResult = [];
    if(this.configCache){
      this.configCache.cutoff = this.cutoff;
      this.configCache.coarsening = this.coarsening;
      this.changeMade = true;
    }

    this.callMultipleImages();
  }
  setCutOffValue() {
    this.imageSpatialWidgetService
    .getImageSize(this.configService.SelectedSiteId,this.configService.SelectedProjectId,this.datasetImages[0].path)
    .subscribe({
      next: (response:any) => {
        if (response) {
          if (response['status']) {
            this.cutoffSlider.min = (response['data'].width * 1 / 20 * 22 / 1024);
            this.cutoffSlider.max = (response['data'].width * 1 / 2 * 22 / 1024);
            this.cutoffSlider.stepValue = round(Number((this.cutoffSlider.max - this.cutoffSlider.min) / 20), 2);
          }
        }
      },
      error: (error:any) => {
        const errorMessage = error?.error?.message || error?.message || 'An unexpected error occurred';
        this.toaster.error(errorMessage, 'ERROR', {
          positionClass: 'custom-toast-position',
        });
      },
    });
  }

  phaseListToDisplay() {
    return this.phaseList[this.selectedQuantification];
  }

  addPhaseToList() {
    if (this.selectedPhase != "") {
      var index = this.addedPhaseList.findIndex((val:phaseModel) => val.title == this.selectedPhase);
      if (index != -1) {
        this.toaster.error("Already added.")
      } else {
        let index = this.phaseList[this.selectedQuantification].findIndex((phase:any)=>phase.title==this.selectedPhase);
        if(index != -1){
          this.addedPhaseList.push(this.phaseList[this.selectedQuantification][index]);
          if(this.configCache){
            this.configCache.local_states = this.addedPhaseList.map((phase:phaseModel)=>phase.value);
            this.changeMade = true;
          }
        }
      }
    } else {
      this.toaster.error("Select phase first.")
    }
  }


  changeFeatureType() {
    this.addedPhaseList = [];
    this.highlightedPhase = "";
    this.featureTypeResult = [];
    this.selectedPhase = this.phaseList[this.selectedQuantification][0].title;
    if(this.configCache){
      this.configCache.quantTech = this.selectedQuantification;
      this.configCache.local_states = [];
      this.changeMade = true;
    }
  }
  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 3;
  }

  loadFeatures() {
    this.widgetdataInformation = {
      type: this.widgetControl?.Widget.type + ' widget',
      description: 'The Spatial Statistics Widget computes spatial metrics to quantify the distribution, clustering, and relationships between defects in segmented images. It provides both numerical results and visualizations for statistical analysis.',
      version: this.configCache?.version,
      spatial_statistics_information: true
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
    this.resetConfigCache();
    this.changeMade = false;
  }

  resetConfigCache(){
    if (this.configCache) {
      if(this.configCache.cutoff){
        this.cutoff = this.configCache.cutoff;
      }
      if(this.configCache.ang_int){
        this.angularInterval = this.configCache.ang_int;
      }
      if(this.configCache.coarsening){
        this.coarsening = this.configCache.coarsening;
      }
      if(this.configCache.quantTech !=''){
        this.selectedQuantification = this.configCache.quantTech;
        if(this.configCache.local_states && this.configCache.local_states.length>0){
          this.addedPhaseList = this.phaseList[this.configCache.quantTech].filter((item:any) =>
            this.configCache?.local_states.some(
              filterVal => JSON.stringify(filterVal) === JSON.stringify(item.value)
            )
          );
        }
      }
    }
  }



  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

}
function round(num:any, places:any) {
  num = parseFloat(num);
  places = (places ? parseInt(places, 10) : 0)
  if (places > 0) {
    let length = places;
    places = "1";
    for (let i = 0; i < length; i++) {
      places += "0";
      places = parseInt(places, 10);
    }
  } else {
    places = 1;
  }
  return Math.round((num + Number.EPSILON) * (1 * places)) / (1 * places)
}

