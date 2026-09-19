import { ChangeDetectorRef, Component, ElementRef, EventEmitter, Input, OnInit, Output, Renderer2, ViewChild, AfterViewInit, OnDestroy } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import { DragulaService } from 'ng2-dragula';
import clone from 'clone';
import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';
import { SaveWorkflowDialogBox } from './save-workflow-dialogbox/save-workflow-dialogbox.component';
import { SaveWorkflowConfirmationDialogboxComponent } from './save-workflow-confirmation-dialogbox/save-workflow-confirmation-dialogbox.component';
import { SaveAnalysisConfirmationDialogComponent } from './save-analysis-confirmation-dialog/save-analysis-confirmation-dialog.component';
import { ConfigService } from 'src/app/services/config.service';
import { MatExpansionPanel } from '@angular/material/expansion';
import { FormControl, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
@Component({
  selector: 'manage-workflow',
  templateUrl: './manage-workflow.component.html',
  styleUrls: ['./manage-workflow.component.less']
})
export class ManageWorkflowComponent implements OnInit {

  @Input() datasetId: any;
  @Input() datasetName: any;
  @Input() selectedFolderId: any;
  @Input() selectedFolderName: any;
  @Input() segmentationworkflow: any;
  @Input() allWorkFlows: any;
  @Input() editWorkflowData: any;
  @Input() saveWorkflowBtn: boolean = false;
  @Input() apiCall: boolean = false;
  @Input() closeType: any;

  @Output() activiateApiCallEvent = new EventEmitter();
  @Output() invokeAllWorkflowsFuncEvent = new EventEmitter();
  @Output() updateSegementationEvent = new EventEmitter();
  @Output() saveWorkflowBtnEvent = new EventEmitter();
  @Output() selectedFirstTab = new EventEmitter();

  @ViewChild('canvasWrap') public canvasWrap!: ElementRef;
  @ViewChild('cropcanvas') public cropcanvas!: ElementRef;
  @ViewChild('scalecanvas') public scalecanvas!: ElementRef;

  @ViewChild('templateCanvasWrap') public templateCanvasWrap!: ElementRef;
  @ViewChild('templateCanvas') public templateCanvas!: ElementRef;
  @ViewChild('cropImageExp') cropImageExp!: MatExpansionPanel;


  // @ViewChild('panelH') panelH: MatExpansionPanel; 
  currentUser: any = {};
  featuresDescriptionList: any = {
    "1": { "fid": 1, "Name": "Shadow removal", "Value": "intensitygradientreduction", "Params": "", "Steps": 1, "selected": true, "slider": {}, "info": "Reduction of intensity gradient over the image (e.g., shadow)" },
    // "2" : {"fid": 2, "Name": "Frequency domain filter", "Value": "frequencydomainfilter", "Params": "", "Steps": 1,"selected":true,"slider":{},"info":"Info message..."},
    "3": { "fid": 3, "Name": "Gaussian filter", "Value": "filters.gaussian", "default_value": -1, "Params": { "sigma": -1 }, "Steps": 1, "selected": true, "slider": { "sigma": { "name": "Sigma (px)", "connect": true, "from": 0, "start": 1, "step": 0.5, "tooltips": true, "range": { min: 0, max: 4 }, "behaviour": "tap" } }, "info": "Apply image smoothing using a 2-D Gaussian kernel" },
    "4": { "fid": 4, "Name": "Bilateral filter", "Value": "restoration.denoise_bilateral", "Params": { "sigma_color": 0.1, "sigma_spatial": 1 }, "Steps": 1, "selected": true, "slider": { "sigma_color": { "name": "Sigma color", "connect": true, "from": 0, "start": 0.1, "step": 0.05, "tooltips": true, "range": { min: 0, max: 1 }, "behaviour": "tap" }, "sigma_spatial": { "name": "Sigma spatial", "connect": true, "from": 0.5, "start": 1, "step": 0.5, "tooltips": true, "range": { min: 0.5, max: 4 }, "behaviour": "tap" } }, "info": "Apply an edge-preserving image smoothing using a 2D Gaussian kernel" },
    "5": { "fid": 5, "Name": "Median filter", "Value": "filters.median", "Params": { "selem": 2 }, "Steps": 1, "selected": true, "slider": { "selem": { "name": "Neighborhood size", "connect": true, "from": 2, "start": 2, "step": 1, "tooltips": true, "range": { min: 2, max: 10 }, "behaviour": "tap", "info": "NxN neighborhood that is used to assign the median value" } }, "info": "Perform median filtering for each pixel" },
    "6": { "fid": 6, "Name": "Non-local means filtering", "Value": "restoration.denoise_nl_means", "Params": { "patch_size": 1, "patch_distance": 1 }, "Steps": 1, "selected": true, "slider": { "patch_size": { "name": "Patch size", "connect": true, "from": 1, "start": 1, "step": 1, "tooltips": true, "range": { min: 1, max: 15 }, "behaviour": "tap", "info": "Size of patch around the target pixel" }, "patch_distance": { "name": "Patch distance", "connect": true, "from": 1, "start": 1, "step": 1, "tooltips": true, "range": { min: 1, max: 15 }, "behaviour": "tap", "info": "Distance of patch used to compare to target pixels" } }, "info": "Apply patch-based image smoothing" },
    "7": { "fid": 7, "Name": "Contrast stretching", "Value": "exposure.rescale_intensity", "Params": "", "Steps": 1.5, "selected": true, "slider": {}, "info": "Expand the range of pixel intensities values in the image" },
    "8": { "fid": 8, "Name": "Histogram equalization", "Value": "exposure.equalize_hist", "Params": "", "Steps": 1.5, "selected": true, "slider": {}, "info": "Increase image contrast by stretching the most frequent intensity values in the image histogram." },
    "9": { "fid": 9, "Name": "Adaptive histogram equalization", "Value": "exposure.equalize_adapthist", "Params": { "kernel_size": 5 }, "Steps": 1.5, "selected": true, "slider": { "kernel_size": { "name": "Kernel size", "connect": true, "from": 5, "start": 5, "step": 5, "tooltips": true, "range": { min: 5, max: 15 }, "behaviour": "tap" } }, "info": "Perform contrast enhancement by histogram equalization on subregions throughout the image." },
    "10": { "fid": 10, "Name": "Image sharpening", "Value": "filters.unsharp_mask", "Params": { "radius": 2, "amount": 0.1 }, "Steps": 1.5, "selected": true, "slider": { "radius": { "name": "Radius", "connect": true, "from": 1, "start": 2, "step": 0.5, "tooltips": true, "range": { min: 1, max: 4 }, "behaviour": "tap", "info": "Degree of detail smoothing before contrast enhancement." }, "amount": { "name": "Amount", "connect": true, "from": 0.1, "start": 0.1, "step": 0.1, "tooltips": true, "range": { min: 0.1, max: 10 }, "behaviour": "tap", "info": "Strength of contrast amplification." } }, "info": "Increase contrast of image details using unsharp masking." },
    "11": { "fid": 11, "Name": "Global threshold", "Value": "filters.threshold_otsu", "Params": { "visualization": "Black/white (default)", "color": "magenta" }, "Steps": 2, "selected": true, "slider": {}, "info": "Perform thresholding using Otsu’s method automatically.", "manual": false },
    "12": { "fid": 12, "Name": "Adaptive threshold", "Value": "filters.threshold_local", "Params": { "block_size": 51, "offset": 0, "visualization": "Black/white (default)", "color": "magenta" }, "Steps": 2, "selected": true, "slider": { "block_size": { "name": "Subregion size (px)", "connect": true, "from": 3, "start": 51, "step": 2, "tooltips": true, "range": { min: 3, max: 51 }, "behaviour": "tap", "info": "Size of square subregions used in local thresholding" }, "offset": { "name": "Offset", "connect": true, "from": -30, "start": 0, "step": 2, "tooltips": true, "range": { min: -30, max: 30 }, "behaviour": "tap", "info": "Offset in intensity for local thresholding" } }, "info": "Perform thresholding locally on subregions in the image" },
    "13": { "fid": 13, "Name": "Manual threshold", "Value": "manualthreshold", "Params": { "threshold_value": -1, "visualization": "Black/white (default)", "color": "magenta" }, "Steps": 2, "selected": true, "slider": { "threshold_value": { "name": "Threshold value", "connect": true, "from": -1, "start": -1, "step": 1, "tooltips": true, "range": { min: -1, max: 254 }, "behaviour": "tap" } }, "info": "Define a threshold manually" },
    // "14" : {"fid":14,"Name":"Global multithreshold","Value":"filters.threshold_multiotsu", "Params":{"classes":3,"selected_layers":{"local_state_0":[1,2],"local_state_1":[0]},"visualization":"Black/white (default)","color":"magenta"},"Steps":2,"selected":true,"slider":{"classes":{"name":"No. of classes","connect":true,"from":3,"start": 3,"step": 1,"tooltips": true,"range": {min: 3,max: 5},"behaviour": "tap"}},"info":"Define multiple thresholds using Otsu multithreshold method"},
    // "15" : {"fid":15,"Name":"K means segmentation","Value":"segmentation.slic", "Params":{"classes":3,"compactness":0.01,"selected_layers":{"local_state_0":[1,2],"local_state_1":[0]},"visualization":"Black/white (default)","color":"magenta"},"Steps":2,"selected":true,"slider":{"classes":{"name":"N segments","connect":true,"from":2,"start": 3,"step": 1,"tooltips": true,"range": {min: 2,max: 5},"behaviour": "tap"},"compactness":{"name":"Compactness","connect":true,"from":0.01,"start": 0.01,"tooltips": true,"range": {min: [0.01],'0%':[0.01,0.99],'30%':[0.1,0.9],'70%':[1,9],max: 10},"behaviour": "tap-drag"}},"info":"Define multiple thresholds using k-means algorithm"},
    "16": { "fid": 16, "Name": "Flip black/white colors (for binary images)", "Value": "invertimage", "Params": "", "Steps": 3, "selected": true, "slider": {}, "info": "" },
    "17": { "fid": 17, "Name": "Remove small objects", "Value": "morphology.remove_small_objects", "Params": { "minimum size to be removed": 50 }, "Steps": 3, "selected": true, "slider": { "minimum size to be removed": { "name": "Minimum size to be removed (px)", "connect": true, "from": 0, "start": 50, "step": 2, "tooltips": true, "range": { min: 1, max: 2000 }, "behaviour": "tap" } }, "info": "Remove objects in segmented image below a specified size." },
    "18": { "fid": 18, "Name": "Fill small holes", "Value": "morphology.remove_small_holes", "Params": { "Equivalent diameter (µm)": 50 }, "Steps": 3, "selected": true, "slider": { "Equivalent diameter (µm)": { "name": "Equivalent diameter (px)", "connect": true, "from": 0, "start": 50, "step": 2, "tooltips": true, "range": { min: 1, max: 2000 }, "behaviour": "tap" } }, "info": "Fill holes in segmented image below a specified size." },
    "19": { "fid": 19, "Name": "Dilation", "Value": "morphology.binary_dilation", "Params": { "structure_element": "disk", "width": "", "height": "", "radius": 1 }, "Steps": 3, "selected": true, "slider": { "width": { "name": "Width (px)", "connect": true, "from": 1, "start": 3, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" }, "height": { "name": "Height (px)", "connect": true, "from": 1, "start": 10, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" }, "radius": { "name": "Radius (px)", "connect": true, "from": 1, "start": 1, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" } }, "info": "Dilate objects in segmented image using a specified element.", "shapes": { "rectangle": "Rectangle", "square": "Square", "disk": "Disk" } },
    "20": { "fid": 20, "Name": "Erosion", "Value": "morphology.binary_erosion", "Params": { "structure_element": "disk", "width": "", "height": "", "radius": 1 }, "Steps": 3, "selected": true, "slider": { "width": { "name": "Width (px)", "connect": true, "from": 1, "start": 3, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" }, "height": { "name": "Height (px)", "connect": true, "from": 1, "start": 10, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" }, "radius": { "name": "Radius (px)", "connect": true, "from": 1, "start": 1, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" } }, "info": "Erode objects in segmented image using a specified element.", "shapes": { "rectangle": "Rectangle", "square": "Square", "disk": "Disk" } },
    "21": { "fid": 21, "Name": "Opening", "Value": "morphology.binary_opening", "Params": { "structure_element": "disk", "width": "", "height": "", "radius": 1 }, "Steps": 3, "selected": true, "slider": { "width": { "name": "Width (px)", "connect": true, "from": 1, "start": 3, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" }, "height": { "name": "Height (px)", "connect": true, "from": 1, "start": 10, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" }, "radius": { "name": "Radius (px)", "connect": true, "from": 1, "start": 1, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" } }, "info": "Open objects in segmented image using a specified element (erosion followed by dilation).", "shapes": { "rectangle": "Rectangle", "square": "Square", "disk": "Disk" } },
    "22": { "fid": 22, "Name": "Closing", "Value": "morphology.binary_closing", "Params": { "structure_element": "disk", "width": "", "height": "", "radius": 1 }, "Steps": 3, "selected": true, "slider": { "width": { "name": "Width (px)", "connect": true, "from": 1, "start": 3, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" }, "height": { "name": "Height (px)", "connect": true, "from": 1, "start": 10, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" }, "radius": { "name": "Radius (px)", "connect": true, "from": 1, "start": 1, "step": 1, "tooltips": true, "range": { min: 1, max: 300 }, "behaviour": "tap" } }, "info": "Close objects in segmented image using a specified element (dilation followed by erosion).", "shapes": { "rectangle": "Rectangle", "square": "Square", "disk": "Disk" } },
    "23": { "fid": 23, "Name": "Remove objects touching border", "Value": "segmentation.clear_border", "Params": "", "Steps": 3, "selected": true, "slider": {}, "info": "Remove any objects in segmented image that are touching the image border." },
    "24": { "fid": 24, "Name": "Trace boundaries", "Value": "segmentation.find_boundaries", "Params": "", "Steps": 3, "selected": true, "slider": {}, "info": "Trace outlines of segmented objects." },
    "26": { "fid": 26, "Name": "Mask out object clusters", "Value": "Maskoutobjectclusters", "Params": { "structure_element": "disk", "width": "", "height": "", "radius": 10, "size_removed": -1 }, "Steps": 3, "selected": true, "slider": { "width": { "name": "Width (px)", "connect": true, "from": 1, "start": 3, "step": 1, "tooltips": true, "range": { min: 1, max: 30 }, "behaviour": "tap" }, "height": { "name": "Height (px)", "connect": true, "from": 1, "start": 10, "step": 1, "tooltips": true, "range": { min: 1, max: 30 }, "behaviour": "tap" }, "radius": { "name": "Radius (px)", "connect": true, "from": 1, "start": 10, "step": 1, "tooltips": true, "range": { min: 1, max: 30 }, "behaviour": "tap" }, "size_removed": { "name": "Minimum size to be removed (px)", "connect": true, "from": 0, "start": 50, "step": 2, "tooltips": true, "range": { min: 1, max: 1000 }, "behaviour": "tap" } }, "info": "Create a mask using dilation to retain large clusters of objects.", "shapes": { "rectangle": "Rectangle", "square": "Square", "disk": "Disk" } },

    // "25" : {"fid":25,"Name":"Template matching","Value":"feature.match_template","Params":{"template_cord":{},"threshold_value":0.2,"visualization":"Black/white (default)","color":"magenta"},"Steps":2,"selected":true,"slider":{"threshold_value":{"name":"Match sensitivity","connect":true,"from":0,"start": 0.2,"step": 0.05,"tooltips": true,"range": {min: 0,max: 1},"behaviour": "tap"}},"info":"Perform template matching"}
  };
  searchKeywords: any = [
    { "word": "noisy results", "fids": [3, 4, 5] },
    { "word": "small holes", "fids": [3, 4, 5] },
    { "word": "object not filled", "fids": [3, 4, 5] },
    { "word": "rough edges", "fids": [3, 4, 5] },
    { "word": "pixel hole", "fids": [3, 4, 5] },
    { "word": "fill holes", "fids": [3, 4, 5, 18] },
    { "word": "remove holes", "fids": [18] },
    { "word": "fill pore", "fids": [18] },
    { "word": "connect object", "fids": [22] },
    { "word": "fill object", "fids": [22] },
    { "word": "incorrect", "fids": [12] },
    { "word": "segmentation", "fids": [11, 12] },
    { "word": "threshold", "fids": [11, 12] },
    { "word": "oversegmentation", "fids": [12] },
    { "word": "local correction", "fids": [12] },
    { "word": "extra objects", "fids": [12] },
    { "word": "refine segmentation", "fids": [12] },
    { "word": "did not segment all", "fids": [12] },
    { "word": "faint objects not segmented", "fids": [12] },
    { "word": "low contrast objects not segmented", "fids": [12] },
    { "word": "not all objects identified", "fids": [17] },
    { "word": "disconnect particles", "fids": [21] },
  ];
  segmentation_analysis_list: any = {
    "pillar-pattern-analysis": [
      { "key": "cd", "name": "Pillar critical dimension analysis", "title": "Critical dimensions" },
      { "key": "xdir", "name": "Pillar X direction spacing", "title": "Distance and pitch between the pillars(X-dir)" },
      { "key": "ydir", "name": "Pillar Y direction spacing", "title": "Distance and pitch between the pillars(Y-dir)" },
      { "key": "zdir", "name": "Pillar diagonal-direction spacing", "title": "Distance and pitch between the pillars (z-dir)" },
      { "key": "hex_packing", "name": "Pillar hexagon packing fraction", "title": "Pillar packing fraction (within hexagon)" },
      { "key": "xy_pg_packing", "name": "Pillar parallelogram packing fraction (X-Y direction)", "title": "Pillar packing fraction within parallelogram (X-Y dir)" },
      { "key": "xd_pg_packing", "name": "Pillar parallelogram packing fraction (X-Diagonal direction)", "title": "Pillar packing fraction within parallelogram (X-Diagonal dir)" },
      { "key": "yd_pg_packing", "name": "Pillar packing fraction within parallelogram (Y-Diagonal direction)" }
    ],
    "feature-profile-analysis": [
      { "key": "fpt", "name": "Feature profile thickness (horizontal direction)", "title": "Thickness" },
      { "key": "fpo", "name": "Feature profile outline", "title": "Outline" }
    ],
    "tier-analysis": [
      { "key": "tva", "name": "Tier void analysis", "title": "Tier void analysis" },
      { "key": "tta", "name": "Tier thickness analysis", "title": "Tier thickness analysis" }
    ],
    "metal-recess-analysis": [
      { "key": "metal_recess", "name": "Metal recess analysis", "title": "Metal recess analysis" },
      { "key": "metal_recess_sec_t", "name": "Metal recess second tier analysis", "title": "Metal recess second tier" },
      { "key": "metal_recess_tier_thick", "name": "Metal recess tier thickness analysis", "title": "Metal recess tier thickness" }
    ],
    "bubble-analysis": [
      { "key": "bubble_analysis", "name": "Bubble analysis", "title": "Bubble analysis" },
    ],
    "pillar-anomaly-analysis": [
      { "key": "pillar_anomaly", "name": "Pillar anomaly analysis", "title": "Pillar anomaly analysis" },
    ],
    "pillar-c2c-analysis": [
      { "key": "pillar2", "name": "Pillar c2c analysis", "title": "Pillar c2c analysis" },
    ],
    "metal-voids-analysis": [
      { "key": "metal_voids", "name": "Metal voids analysis", "title": "Metal voids analysis" },
    ]
  };
  preprocessingLayers: any = {
    "total": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "imageNoise": [1, 2, 3, 4, 5, 6],
    "contrastEnhance": [7, 8, 9, 10]
  };
  segmentationLayers: any = {
    "total": [11, 12, 13, 14, 15, 25],
    "two_localstates": [11, 12, 13],
    "more_localstates": [14, 15],
    "using_template": [25]
  };
  postprocessingLayers: any = {
    "total": [16, 17, 18, 19, 20, 21, 22, 23, 24, 26],
    "segmentaionCleanup": [16, 17, 18],
    "morphologicalOperations": [19, 20, 21, 22, 23, 24, 26]
  };
  currentLayerData: any = {
    "type": "",
    "layer": "",
    "actionType": "",
    "subActionType": "",
    "changedObj": {
      "key": "",
      "val": ""
    },
    "inputImage": ""
  };
  backupWorkflow: any = {
    "preprocessingWorkflowFeatures": [],
    "segmentationWorkflowFeatures": [],
    "postprocessingWorkflowFeatures": []
  };
  unitValues: any = [
    { "unit": "nm", "value": "1e-9" },
    { "unit": "µm", "value": "1e-6​" },
    { "unit": "μm", "value": "1e-6​" },
    { "unit": "um", "value": "1e-6​" },
    { "unit": "mm", "value": "1e-3" },
  ];
  mouseHoverTime: any;
  segInputImageSizeLimit = 500;
  segmentParamsChangeFlag = false;
  features: any = {};
  segmentedImageDetails: any = {};
  dropDownLayersDefaultValues: any = { "type": "", "mainVal": "", "val": "" };
  originalImagedropDownLayer: any = clone(this.dropDownLayersDefaultValues);
  dropDownLayer: any = {};
  dropDownVisualization: any = { "type": 'solid', "val": 'Black/white (default)', "disVal": 'Black/white (default)', "mainVal": 'solid,Black/white (default),Black/white (default)' };
  dropDownAnalysisVisualization: any = { "type": '', "val": '', "mainVal": '' };
  newWorkflow: Boolean = false;
  retrieveWorkflow: Boolean = false;
  editWorkflowId: any = "";
  editWorkflowName: any = "";
  workflowLoading: Boolean = false;
  analysisData: any = {
    "pillar-pattern-analysis": {
      "analysisExploreBtn": false,
      "analysisExplored": false,
      "analysisExpandedId": -1
    },
    "feature-profile-analysis": {
      "analysisExploreBtn": false,
      "analysisExplored": false,
      "analysisExpandedId": -1
    },
    "tier-analysis": {
      "analysisExploreBtn": false,
      "analysisExplored": false,
      "analysisExpandedId": -1
    },
    "metal-recess-analysis": {
      "analysisExploreBtn": false,
      "analysisExplored": false,
      "analysisExpandedId": -1
    },
    "bubble-analysis": {
      "analysisExploreBtn": false,
      "analysisExplored": false,
      "analysisExpandedId": -1
    },
    "pillar-anomaly-analysis": {
      "analysisExploreBtn": false,
      "analysisExplored": false,
      "analysisExpandedId": -1
    },
    "pillar-c2c-analysis": {
      "analysisExploreBtn": false,
      "analysisExplored": false,
      "analysisExpandedId": -1
    },
    "metal-voids-analysis": {
      "analysisExploreBtn": false,
      "analysisExplored": false,
      "analysisExpandedId": -1
    }
  };
  addNewWorkflowLayer: Boolean = false;
  newLayerFor: any = "";
  newInnerLayer: Boolean = false;
  newInnerLayerDetails: any = {};
  editTempBinarization: Boolean = false;
  tempBinarization: any = {};
  editBinarization: Boolean = false;
  binarization: any = {};
  editTemplateMatching: boolean = false;
  matchingCoords: any = {};
  templateMatchingId = -1;
  workflowChanged: Boolean = false;
  updateAnalysis: any = {
    "pillar-pattern-analysis": false,
    "feature-profile-analysis": false,
    "tier-analysis": false,
    "metal-recess-analysis": false,
    "bubble-analysis": false,
    "pillar-anomaly-analysis": false,
    "pillar-c2c-analysis": false,
    "metal-voids-analysis": false
  };
  preProcessingLayerSubscription: any;
  segmentaionLayerSubscription: any;
  postProcessingLayerSubscription: any;
  previewImage: any = "";
  showPreviewImage: Boolean = false;
  showSearchFilters: Boolean = false;
  searchFiltersList: any = [];
  imageCropTabObj: any = {
    "defaultCoordinates": {
      "x1": 0,
      "y1": 0,
      "x2": 100,
      "y2": 100,
      "w": 100,
      "h": 100
    },
    "manualCoordinates": {},
    "imageCropperLoaded": false,
    "imageLoaded": false,
    "cropperPosition": {},
    "cropImageShape": {},
    "imageCropChanged": false,
    "tempImage": "",
    "croppedImageWidth": 0,
    "croppedImageHeight": 0,
    "imageCropped": false
  };
  segmentedWorkflowProgress = 0;
  defaultWorkflow = false;
  applyToAll = false;
  defaultGuasionValue = -1;
  carryForwardCrop = false;
  carryForwardScalebar = false;
  carryForwardAnalysis = false;
  wf_for_incomingimages = false;
  isAnalysisExists: Boolean = false;
  segmentationUsingThresholding = false;
  cropApplied: Boolean = false;
  segAndCropTabSelected: number = 0;
  triggerCloseWorkflowSubcription: any;

  imageDisplayUrl = `${this.configService.getImageDatasetUrl()}/get_image_contnet_by_path`;
  downloadXlsxFileURL = '/imageAnalysis/downloadXlsxFile?file=';
  spockCase = false;
  @ViewChild('panelH') panelH!: ElementRef;
  isExpandedPanel: boolean = false;
  previewImage_url: any;

  selectedMask: any
  expandedPanelIndex: number | null = null;
  @ViewChild('maskCanvasElement') public maskCanvasElement!: ElementRef;
  private ctx!: CanvasRenderingContext2D;
  applySelectedMask = false;
  maskApplied: boolean = false;
  private offsetX: number = 0;
  private offsetY: number = 0;
  private dragging: boolean = false;
  private resizing: boolean = false;
  private resizingSide: string | null = null;
  private imageCache: HTMLImageElement | null = null;
  private isDrawing: boolean = false;
  private RESIZE_MARGIN: number = 10;
  public selectedSegmentedValue: string = '';
  public zoomLevel: number = 2; // Set your default zoom level
  private magnifierGlass!: HTMLElement;

  @ViewChild('filteredImageMagnifier') filteredImageMagnifier: any;
  @ViewChild('originalImageMagnifier') originalImageMagnifier: any;
  @ViewChild('previewImageMagnifier') previewImageMagnifier: any;

  segmentedLoading: boolean = false;
  originalLoading: boolean = false;
  previewLoading: boolean = false;
  targetElements: string[] = [];
  mangifierElement: string = '';

  constructor(
    public imageAnalysisService: ImageAnalysisService,
    public dialog: MatDialog,
    private toastr: ToastrService,
    // private socket: SocketService,
    private dragulaService: DragulaService,
    private elementRef: ElementRef,
    private renderer: Renderer2,
    private configService: ConfigService,
    private toaster: ToastrService,
    private cdRef: ChangeDetectorRef,
    private el: ElementRef,
    private cdr: ChangeDetectorRef,
    private router: Router,
    private activatedRoute: ActivatedRoute,
  ) {
    this.preProcessingLayerSubscription = this.dragulaService.dropModel("PRE_PROCESSING_LAYERS").subscribe((args: any) => {
      const { targetModel, item } = args;
      if (this.apiCall || !this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected']) {
        const initPos = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].indexOf(item);
        const currPos = targetModel.indexOf(item);
        setTimeout((_: any) => {
          targetModel.splice(currPos, 1);
          targetModel.splice(initPos, 0, item);
          this.showMsg('pre-processing');
        }, 0);
      } else {
        this.currentLayerData['type'] = "pre-processing";
        this.currentLayerData['layer'] = args.targetIndex;
        this.currentLayerData['actionType'] = 'edit';
        this.currentLayerData['subActionType'] = 'drag';
        this.currentLayerData["changedObj"] = {};
        this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'] = args.targetModel;
        this.saveWorkflowBtnEvent.emit(true);
        this.workflowChanged = true;
        // this.dropDownLayer = this.getLatestLayerData();
        // this.setOriginalImageDropDown(true);
        // setTimeout((_: any) => {
        //   this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
        // }, 50);
        // this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
      }
    });
    this.segmentaionLayerSubscription = this.dragulaService.dropModel("SEGMENTATION_LAYERS").subscribe((args: any) => {
      const { targetModel, item } = args;
      if (this.apiCall || !this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected']) {
        const initPos = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].indexOf(item);
        const currPos = targetModel.indexOf(item);
        setTimeout((_: any) => {
          targetModel.splice(currPos, 1);
          targetModel.splice(initPos, 0, item);
          this.showMsg('segmentation');
        }, 0);
      } else {
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'] = args.targetModel;
        this.saveWorkflowBtnEvent.emit(true);
        this.workflowChanged = true;
      }
    });
    this.postProcessingLayerSubscription = this.dragulaService.dropModel("POST_PROCESSING_LAYERS").subscribe((args: any) => {
      const { targetModel, item } = args;
      if (this.apiCall || !this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] ||
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => val['selected'] == true).length == 0 ||
        !this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected']) {
        const initPos = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].indexOf(item);
        const currPos = targetModel.indexOf(item);
        setTimeout((_: any) => {
          targetModel.splice(currPos, 1);
          targetModel.splice(initPos, 0, item);
          this.showMsg('post-processing');
        }, 0);
      } else {
        this.currentLayerData['type'] = "post-processing";
        this.currentLayerData['layer'] = args.targetIndex;;
        this.currentLayerData['actionType'] = 'edit';
        this.currentLayerData['subActionType'] = 'drag';
        this.currentLayerData["changedObj"] = {};
        this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'] = args.targetModel;
        this.saveWorkflowBtnEvent.emit(true);
        this.workflowChanged = true;
        // this.dropDownLayer = this.getLatestLayerData();
        // this.setOriginalImageDropDown(true);
        // this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
      }
    });
  }

  togglePanel() {
    this.isExpandedPanel = !this.isExpandedPanel;
  }

  ngOnInit() {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    this.triggerCloseWorkflow();
    this.getFiltersList();
    this.resetSegmentedImageDetailsVariable();
    this.intiSegmentationSocket();

    if (this.editWorkflowData['editType'] == 'workflow') {
      this.editworkflow(this.editWorkflowData);
    } else {
      this.displaySegmentationImage(this.editWorkflowData['image'], 'image');
    }
  }
  getImageContent(obj: any, key: string) {
    let path = (key == 'previewImage') ? this.previewImage : obj[key];
    if (path && path != '') {
      this.imageAnalysisService
        .getIndividualImageContent({ path: path, name: this.getImageName(path) })
        .subscribe(
          (result) => {
            if (key == 'previewImage') {
              this.previewImage_url = result;
            } else {
              let newPathKey = key + '_url'
              obj[newPathKey] = '';
              obj[newPathKey] = result;
            }
          },
          (error) => {
            console.error('Error fetching image content:', error);
          },
        );
    }
  }

  triggerCloseWorkflow() {
    this.triggerCloseWorkflowSubcription = this.imageAnalysisService.saveWorkflowBtnChange.subscribe(_type => {
      this.closeAddWorkflow();
    });
  }

  intiSegmentationSocket() {
    // this.socket.ImageProgressSocket(localStorage.getItem('currUserID')).subscribe(data => {
    //   if (data.user_id == localStorage.getItem('currUserID')) {
    //     this.segmentedWorkflowProgress = data['progressbar'];
    //   }
    // });
  }

  activiateApiCall(status: any) {
    this.activiateApiCallEvent.emit(status);
  }

  returnKeysFromObject(inpObj: any) {
    return Object.keys(inpObj);
  }

  checkOddInteger(val: number) {
    return Math.abs(val % 2) == 1;
  }

  fetchImageIndex(imagePath: string) {
    return this.segmentationworkflow['images'].findIndex((val: any) => val['path'] == imagePath);
  }

  getFiltersList() {
    this.features = JSON.parse(JSON.stringify(this.featuresDescriptionList));
  }

  updateLayersData(layerType: any, data: any) {
    if (data.length > 0) {
      let graphIndex = 0;
      for (let i = 0; i < this.segmentedImageDetails['selectedSegmentedImage'][layerType].length; i++) {
        if (this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['selected'] == true && this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['fid'] == data[graphIndex]['fid']) {
          this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result'] = {
            "filtered_image": data[graphIndex]['filterd_image'],
            "histogram_path": data[graphIndex]['histogram_path']
          }

          // this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result'], 'filtered_image')
          this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result'], 'histogram_path')


          if (data[graphIndex]['black&white'] != undefined && data[graphIndex]['black&white'] != "") {
            this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result']['black&white'] = data[graphIndex]['black&white'];
            // this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result'], 'black&white')
          }
          if (data[graphIndex]['previewchanges'] != undefined && data[graphIndex]['previewchanges'] != "") {
            this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result']['previewchanges'] = data[graphIndex]['previewchanges'];
            // this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result'], 'previewchanges')
          }
          if (this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['fid'] == 14 ||
            this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['fid'] == 15) {
            this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result']['perula'] = data[graphIndex]['perula'];
            // this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result'], 'perula')
          }
          if (data[graphIndex]['region_properties'] != undefined &&
            this.returnKeysFromObject(data[graphIndex]['region_properties']).length > 0
          ) {
            this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result']['region_properties'] = data[graphIndex]['region_properties'];
          }
          if (layerType == 'postprocessingWorkflowFeatures' || layerType == "segmentationWorkflowFeatures") {
            this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result']['temp_region_properties_csv_file'] = "";
            this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result']['region_properties_csv_file'] = "";
            if (data[graphIndex]['temp_region_properties_csv_file'] != undefined) {
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result']['temp_region_properties_csv_file'] = data[graphIndex]['temp_region_properties_csv_file'];
            }
            if (data[graphIndex]['region_properties_csv_file'] != undefined) {
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result']['region_properties_csv_file'] = data[graphIndex]['region_properties_csv_file'];
            }
          }

          if (data[graphIndex]['boundary_excel'] != undefined &&
            this.returnKeysFromObject(data[graphIndex]['boundary_excel']).length > 0
          ) {
            this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['result']['boundary_excel'] = data[graphIndex]['boundary_excel'];
          }
          if (this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['fid'] == 13) {
            if (data[graphIndex]['default_val']) {
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['slider']['threshold_value']['range']['min'] = data[graphIndex]['min_range'];
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['slider']['threshold_value']['range']['max'] = data[graphIndex]['maxrange'];
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['slider']['threshold_value']['from'] = data[graphIndex]['min_range'];
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['slider']['threshold_value']['start'] = data[graphIndex]['default_val'];
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['Params']['threshold_value'] = data[graphIndex]['default_val'];
            }
          }
          if (this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['fid'] == 26) {
            if (data[graphIndex]['default_val']) {
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['slider']['size_removed']['range']['min'] = data[graphIndex]['min_range'];
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['slider']['size_removed']['range']['max'] = data[graphIndex]['maxrange'];
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['slider']['size_removed']['from'] = data[graphIndex]['min_range'];
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['slider']['size_removed']['start'] = data[graphIndex]['default_val'];
              this.segmentedImageDetails['selectedSegmentedImage'][layerType][i]['Params']['size_removed'] = data[graphIndex]['default_val'];
            }
          }
          graphIndex++;
        }
      }
    }
  }

  processInputImageSegmentation(detail: any) {
    let data: any = {
      "original_image": this.segmentedImageDetails['selectedSegmentedImage']['image'],
      "image": "",
      "applied": (this.editWorkflowId == "") ? false : this.cropApplied,
      "path": true,
      "orignalpath": this.segmentedImageDetails['selectedSegmentedImage']['path'],
      "sample_image": this.getSampleImage(),
      "draw_val": this.segmentedImageDetails['selectedSegmentedImage']["scalebarByImage"],
      "popup_val": this.segmentedImageDetails['selectedSegmentedImage']["scalebarByPhysical"],
      "popup_unit": this.segmentedImageDetails['selectedSegmentedImage']["scalebarByPhysicalUnit"],
      "PixleX": detail.PixelSizeX,
      "PixleY": detail.PixelSizeY,
      "images_names": ['test'],
      "workflow": [
        {
          "_id": (this.editWorkflowId) ? this.editWorkflowId : "",
          "retrieve": this.retrieveWorkflow,
          "features": []
        }
      ]
    }

    let segLastImage: any = {};
    if (this.currentLayerData['type'] == "pre-processing") {
      if (this.currentLayerData['actionType'] == 'add') {
        if (this.segmentedImageDetails['selectedSegmentedImage'].hasOwnProperty("tempPreprocessingWorkflowFeatures") && this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'].length > 0) {
          if (this.segmentedImageDetails['selectedSegmentedImage']["preprocessingWorkflowFeatures"].length == 0) {
            if (this.segmentedImageDetails['selectedSegmentedImage']['masked_image'] != '') {
              data['image'] = this.segmentedImageDetails['selectedSegmentedImage']['masked_image'];
            } else {
              data['image'] = this.getLastSegmentedImage('pre-processing', false, "")["filtered_image"];
            }
          } else {
            data['image'] = this.getLastSegmentedImage('pre-processing', false, "")["filtered_image"];
          }
          data["workflow"][0]["features"] = data["workflow"][0]["features"].concat(this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures']);
        }
      } else {
        if (this.currentLayerData['layer'] >= 0) {
          let filters = this.segmentedImageDetails['selectedSegmentedImage']["preprocessingWorkflowFeatures"].filter((filter: any) => filter.selected);
          if (filters.length == 0 || filters.length == 1) {
            if (this.segmentedImageDetails['selectedSegmentedImage']['masked_image'] != '') {
              data['image'] = this.segmentedImageDetails['selectedSegmentedImage']['masked_image'];
            } else {
              data['image'] = this.getLastSegmentedImage('pre-processing', true, "")["filtered_image"];
            }
          } else {
            data['image'] = this.getLastSegmentedImage('pre-processing', true, "")["filtered_image"];
          }

          // data['image'] = this.getLastSegmentedImage('pre-processing', true, this.currentLayerData['layer'])["filtered_image"];

          if (this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] != undefined &&
            this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] == true) {
            data["workflow"][0]["features"] = data["workflow"][0]["features"].concat(this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].filter((val: any, index: number) => (val['selected'] == true && index >= this.currentLayerData['layer'])));
          }
        }
      }
      data["workflow"][0]["features"] = this.setWorkflowFeaturesToApply(data["workflow"][0]["features"], 'segmentation');
      data["workflow"][0]["features"] = this.setWorkflowFeaturesToApply(data["workflow"][0]["features"], 'post-processing');
    }
    else if (this.currentLayerData['type'] == "segmentation") {
      if (this.currentLayerData['actionType'] == 'add') {
        if (this.segmentedImageDetails['selectedSegmentedImage'].hasOwnProperty("tempSegmentationWorkflowFeatures") && this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'].length > 0) {
          if (this.currentLayerData['inputImage'] != undefined && this.currentLayerData['inputImage'] != "") {
            data['image'] = this.currentLayerData['inputImage'];
          } else {
            data['image'] = this.getLastSegmentedImage('pre-processing', false, "")["filtered_image"];
          }
          data["workflow"][0]["features"] = data["workflow"][0]["features"].concat(this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures']);
        }
      }

      else {
        if (this.currentLayerData['layer'] >= 0) {
          if (this.currentLayerData['inputImage'] != undefined && this.currentLayerData['inputImage'] != "") {
            data['image'] = this.currentLayerData['inputImage'];
          } else {
            data['image'] = this.getLastSegmentedImage('segmentation', true, this.currentLayerData['layer'])["filtered_image"];
          }
          if (this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] != undefined &&
            this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] == true) {
            data["workflow"][0]["features"] = data["workflow"][0]["features"].concat(this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any, index: number) => (val['selected'] == true && index == this.currentLayerData['layer'])));
          }
        }
      }
      data["workflow"][0]["features"] = this.setWorkflowFeaturesToApply(data["workflow"][0]["features"], 'post-processing');
    }
    else if (this.currentLayerData['type'] == "post-processing") {
      if (this.currentLayerData['actionType'] == 'add') {
        segLastImage = this.getLastSegmentedImage('post-processing', false, "");
        if (segLastImage["black&white"] != undefined && segLastImage["black&white"] != "") {
          data['image'] = segLastImage["black&white"];
        } else {
          data['image'] = segLastImage["filtered_image"];
        }
        if (
          this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] != undefined &&
          this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] == true &&
          this.getFeaturesCount('segmentationWorkflowFeatures') > 0
        ) {
          data["workflow"][0]["features"] = data["workflow"][0]["features"].concat(this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures']);
        }
      } else {
        segLastImage = this.getLastSegmentedImage('post-processing', true, this.currentLayerData['layer']);
        if (segLastImage["black&white"] != undefined && segLastImage["black&white"] != "") {
          data['image'] = segLastImage["black&white"];
        } else {
          data['image'] = segLastImage["filtered_image"];
        }
        if (
          this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] != undefined &&
          this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] == true &&
          this.getFeaturesCount('segmentationWorkflowFeatures') > 0 &&
          this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] != undefined &&
          this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] == true
        ) {
          data["workflow"][0]["features"] = data["workflow"][0]["features"].concat(this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].filter((val: any, index: number) => (val['selected'] == true && index >= this.currentLayerData['layer'])));
        }
      }
    }
    else if (this.currentLayerData['type'] == 'scratch') {
      data['image'] = this.segmentedImageDetails['inputImageForSegmentation'];
      data["workflow"][0]["features"] = this.setWorkflowFeaturesToApply(data["workflow"][0]["features"], 'pre-processing');
      data["workflow"][0]["features"] = this.setWorkflowFeaturesToApply(data["workflow"][0]["features"], 'segmentation');
      data["workflow"][0]["features"] = this.setWorkflowFeaturesToApply(data["workflow"][0]["features"], 'post-processing');
    }
    data["workflow"][0]['post_visualization'] = {};
    if (this.getFeaturesCount('tempSegmentationWorkflowFeatures') > 0) {
      data["workflow"][0]['post_visualization']['visualization'] = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['Params']['visualization'];
      data["workflow"][0]['post_visualization']['color'] = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['Params']['color'];
    }
    else if (
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] == true &&
      this.getFeaturesCount('segmentationWorkflowFeatures') > 0
    ) {
      let segWorkflow = this.segmentedImageDetails['selectedSegmentedImage']["segmentationWorkflowFeatures"].filter((val: any) => val['selected'] == true);
      data["workflow"][0]['post_visualization']['visualization'] = segWorkflow[segWorkflow.length - 1]['Params']['visualization'];
      data["workflow"][0]['post_visualization']['color'] = segWorkflow[segWorkflow.length - 1]['Params']['color'];
    }

    if (this.currentLayerData['type'] != 'scratch' && (data["workflow"][0]["features"].length == 0 || data["workflow"][0]["features"].length < 1)) {
      if (this.currentLayerData['subActionType'] == "checkbox" || this.currentLayerData['subActionType'] == "delete"
      ) {
        this.segmentedImageDetails['segmentedImage'] = data['image'];

        if (this.currentLayerData['type'] == "post-processing") {
          let segWorkflowselected = this.segmentedImageDetails['selectedSegmentedImage']["segmentationWorkflowSelected"];
          let segWorkflow = this.segmentedImageDetails['selectedSegmentedImage']["segmentationWorkflowFeatures"].filter((val: any) => val['selected'] == true);
          if (segWorkflowselected != undefined && segWorkflowselected == true && segWorkflow != undefined && segWorkflow.length > 0) {
            if (segWorkflow[segWorkflow.length - 1]['Params']['visualization'] == 'Black/white (default)' && segLastImage['black&white'] != undefined && segLastImage['black&white'] != "") {
              this.segmentedImageDetails['segmentedImage'] = segLastImage['black&white'];
            } else {
              this.segmentedImageDetails['segmentedImage'] = segLastImage['filtered_image'];
            }
          } else {
            this.segmentedImageDetails['segmentedImage'] = segLastImage['filtered_image'];
          }
        }
        this.setRegionProps();
      }

      return false;
    }
    if (data["workflow"][0]["features"].length == 0) {
      return false
    }

    this.apiCall = true;
    this.segmentedWorkflowProgress = 1;
    this.imageAnalysisService.getCroppedAndSegmentedImage(data).then((response) => {
      if (response) {
        var parsedData = response;
        let parsedImageData = parsedData['imagedata'];
        this.segmentedWorkflowProgress = 0;
        if (typeof parsedData['imagedata'] != 'undefined') {
          // this.apiCall = false;
          this.segmentedImageDetails['selectedSegmentedImage']['cropimg'] = parsedImageData['cropimg'];
          this.segmentedImageDetails['inputImageForSegmentation'] = parsedImageData['cropimg'];
          // this.segmentedImageDetails['displayInputImage'] = parsedImageData['cropimg'];

          // this.getImageContent(this.segmentedImageDetails, 'displayInputImage')

          // this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage'], 'cropimg')
          // this.getImageContent(this.segmentedImageDetails, 'inputImageForSegmentation')
          // this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage'], 'manual_image')



          this.segmentedImageDetails['selectedSegmentedImage']['cropimgShape'] = parsedImageData['cropimg_shape']

          this.retrieveWorkflow = false;
          this.cropApplied = false;
          // if (!this.newInnerLayer) {
          //   this.segmentedImageDetails['segmentedImage'] = parsedImageData['segmented_img'];
          //   this.getImageContent(this.segmentedImageDetails,'segmentedImage')
          // }
          this.segmentedImageDetails['segmentedImage'] = parsedImageData['segmented_img'];
          this.getImageContent(this.segmentedImageDetails, 'segmentedImage')

          this.previewImage = parsedImageData['segmented_img'];
          this.getImageContent({}, 'previewImage')

          let preProcessedResult = parsedImageData['preprocessedlayers'];
          let segmentaionResult = parsedImageData['segmentationlayers'];
          let postProcessedResult = parsedImageData['postprocessedlayers'];
          if (this.currentLayerData['type'] == "pre-processing") {
            if (this.currentLayerData['actionType'] == 'add') {
              if (preProcessedResult.length > 0) {
                if (this.segmentedImageDetails['selectedSegmentedImage'].hasOwnProperty("tempPreprocessingWorkflowFeatures") && this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'].length > 0) {
                  let findIndex = this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'].findIndex((data: any) => (data['selected'] == true && data['fid'] == preProcessedResult[(preProcessedResult.length - 1)]['fid']));
                  if (findIndex > -1) {
                    this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][findIndex]['result'] = {
                      "filtered_image": preProcessedResult[(preProcessedResult.length - 1)]['filterd_image'],
                      "histogram_path": preProcessedResult[(preProcessedResult.length - 1)]['histogram_path']
                    }
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][findIndex]['result'], 'filtered_image')
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][findIndex]['result'], 'histogram_path')

                    if (preProcessedResult[(preProcessedResult.length - 1)]['fid'] == 3 &&
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][findIndex]['fid'] == 3 &&
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][findIndex]['default_value'] == -1) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][findIndex]["default_value"] = preProcessedResult[(preProcessedResult.length - 1)]['gaussain_defaultval'];
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][findIndex]["Params"]["sigma"] = preProcessedResult[(preProcessedResult.length - 1)]['gaussain_defaultval'];
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][findIndex]["slider"]["sigma"]["start"] = preProcessedResult[(preProcessedResult.length - 1)]['gaussain_defaultval'];
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][findIndex]["slider"]["sigma"]["step"] = 0.25;
                    }
                    preProcessedResult.splice(-1, 1);
                  }
                }
              }
            } else {
              if (preProcessedResult.length > 0 && this.currentLayerData['layer'] >= 0) {
                let graphIndex = 0;
                for (let i = 0; i < this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].length; i++) {
                  if (i >= this.currentLayerData['layer'] && this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][i]['selected'] == true && this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][i]['fid'] == preProcessedResult[graphIndex]['fid']) {
                    this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][i]['result'] = {
                      "filtered_image": preProcessedResult[graphIndex]['filterd_image'],
                      "histogram_path": preProcessedResult[graphIndex]['histogram_path']
                    }
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][i]['result'], 'filtered_image')
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][i]['result'], 'histogram_path')

                    graphIndex++;
                  }
                }
              }
            }
            this.updateLayersData('segmentationWorkflowFeatures', segmentaionResult);
            this.updateLayersData('postprocessingWorkflowFeatures', postProcessedResult);
          } else if (this.currentLayerData['type'] == "segmentation") {
            if (this.currentLayerData['actionType'] == 'add') {
              if (segmentaionResult.length > 0) {
                if (this.segmentedImageDetails['selectedSegmentedImage'].hasOwnProperty("tempSegmentationWorkflowFeatures") && this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'].length > 0) {
                  let findIndex = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'].findIndex((data: any) => (data['selected'] == true && data['fid'] == segmentaionResult[(segmentaionResult.length - 1)]['fid']));
                  if (findIndex > -1) {
                    let visualization = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['Params']['visualization'];
                    if (this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result'] == undefined) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result'] = {};
                    }
                    this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result']['filtered_image'] = segmentaionResult[(segmentaionResult.length - 1)]['filterd_image'];
                    this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result']['black&white'] = segmentaionResult[(segmentaionResult.length - 1)]['black&white'];
                    this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result']['previewchanges'] = segmentaionResult[(segmentaionResult.length - 1)]['previewchanges'];

                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result'], 'filtered_image')
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result'], 'black&white')
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result'], 'previewchanges')


                    if (visualization == 'Black/white (default)' || visualization == '') {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result']['histogram_path'] = segmentaionResult[(segmentaionResult.length - 1)]['histogram_path'];
                      this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result'], 'histogram_path')
                    }
                    if (segmentaionResult[(segmentaionResult.length - 1)]['region_properties'] != undefined &&
                      this.returnKeysFromObject(segmentaionResult[(segmentaionResult.length - 1)]['region_properties']).length > 0
                    ) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result']['region_properties'] = segmentaionResult[(segmentaionResult.length - 1)]['region_properties'];
                    }
                    this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result']['temp_region_properties_csv_file'] = "";
                    this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result']['region_properties_csv_file'] = "";

                    if (segmentaionResult[(segmentaionResult.length - 1)]['temp_region_properties_csv_file'] != undefined) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result']['temp_region_properties_csv_file'] = segmentaionResult[(segmentaionResult.length - 1)]['temp_region_properties_csv_file'];
                    }
                    if (segmentaionResult[(segmentaionResult.length - 1)]['region_properties_csv_file'] != undefined) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result']['region_properties_csv_file'] = segmentaionResult[(segmentaionResult.length - 1)]['region_properties_csv_file'];
                    }
                    if (this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['fid'] == 14 ||
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['fid'] == 15) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result']['perula'] = segmentaionResult[(segmentaionResult.length - 1)]['perula'];
                      this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['result']['perula'], 'perula')
                    }
                    if (this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['fid'] == 13) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['slider']['threshold_value']['range']['min'] = segmentaionResult[(segmentaionResult.length - 1)]['min_range'];
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['slider']['threshold_value']['range']['max'] = segmentaionResult[(segmentaionResult.length - 1)]['maxrange'];
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['slider']['threshold_value']['from'] = segmentaionResult[(segmentaionResult.length - 1)]['min_range'];
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['slider']['threshold_value']['start'] = segmentaionResult[(segmentaionResult.length - 1)]['default_val'];
                      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][findIndex]['Params']['threshold_value'] = segmentaionResult[(segmentaionResult.length - 1)]['default_val'];
                    }
                    segmentaionResult.splice(-1, 1);
                  }
                }
              }
            } else {
              if (segmentaionResult.length > 0) {
                let graphIndex = 0;
                for (let i = 0; i < this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].length; i++) {
                  if (i >= this.currentLayerData['layer'] && this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['selected'] == true && this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['fid'] == segmentaionResult[graphIndex]['fid']) {
                    if (this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result'] == undefined) {
                      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result'] = {};
                    }
                    this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result']['filtered_image'] = segmentaionResult[graphIndex]['filterd_image'];
                    this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result']['black&white'] = segmentaionResult[graphIndex]['black&white'];
                    this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result']['previewchanges'] = segmentaionResult[graphIndex]['previewchanges'];
                    this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result']['histogram_path'] = segmentaionResult[graphIndex]['histogram_path'];

                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result'], 'filterd_image')
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result'], 'black&white')
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result'], 'histogram_path')
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result'], 'previewchanges')


                    if (segmentaionResult[graphIndex]['region_properties'] != undefined &&
                      this.returnKeysFromObject(segmentaionResult[graphIndex]['region_properties']).length > 0
                    ) {
                      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result']['region_properties'] = segmentaionResult[graphIndex]['region_properties'];
                    }
                    this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result']['temp_region_properties_csv_file'] = "";
                    this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result']['region_properties_csv_file'] = "";
                    if (segmentaionResult[graphIndex]['temp_region_properties_csv_file'] != undefined) {
                      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result']['temp_region_properties_csv_file'] = segmentaionResult[graphIndex]['temp_region_properties_csv_file'];
                    }
                    if (segmentaionResult[graphIndex]['region_properties_csv_file'] != undefined) {
                      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result']['region_properties_csv_file'] = segmentaionResult[graphIndex]['region_properties_csv_file'];
                    }

                    if (this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['fid'] == 14 ||
                      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['fid'] == 15) {
                      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result']['perula'] = segmentaionResult[graphIndex]['perula'];
                      this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['result']['perula'], 'perula')
                    }
                    if (this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['fid'] == 13) {
                      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['slider']['threshold_value']['range']['min'] = segmentaionResult[graphIndex]['min_range'];
                      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['slider']['threshold_value']['range']['max'] = segmentaionResult[graphIndex]['maxrange'];
                      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['slider']['threshold_value']['from'] = segmentaionResult[graphIndex]['min_range'];
                      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['slider']['threshold_value']['start'] = segmentaionResult[graphIndex]['default_val'];
                      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][i]['Params']['threshold_value'] = segmentaionResult[graphIndex]['default_val'];
                    }
                    graphIndex++;
                  }
                }
              }
            }
            this.updateLayersData('postprocessingWorkflowFeatures', postProcessedResult);
          } else if (this.currentLayerData['type'] == "post-processing") {
            if (this.currentLayerData['actionType'] == 'add') {
              if (postProcessedResult.length > 0) {
                if (this.segmentedImageDetails['selectedSegmentedImage'].hasOwnProperty("tempPostprocessingWorkflowFeatures") && this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'].length > 0) {
                  let findIndex = this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'].findIndex((data: any) => (data['selected'] == true && data['fid'] == postProcessedResult[(postProcessedResult.length - 1)]['fid']));
                  if (findIndex > -1) {
                    this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result'] = {
                      "filtered_image": postProcessedResult[(postProcessedResult.length - 1)]['filterd_image'],
                      "histogram_path": postProcessedResult[(postProcessedResult.length - 1)]['histogram_path'],
                      "previewchanges": postProcessedResult[(postProcessedResult.length - 1)]['previewchanges']
                    }

                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result'], 'filterd_image')
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result'], 'histogram_path')
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result'], 'previewchanges')


                    if (postProcessedResult[(postProcessedResult.length - 1)] != undefined && postProcessedResult[(postProcessedResult.length - 1)] != "") {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result']['black&white'] = postProcessedResult[(postProcessedResult.length - 1)]['black&white'];
                      this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result'], 'black&white')
                    }
                    if (postProcessedResult[(postProcessedResult.length - 1)]['region_properties'] != undefined &&
                      this.returnKeysFromObject(postProcessedResult[(postProcessedResult.length - 1)]['region_properties']).length > 0
                    ) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result']['region_properties'] = postProcessedResult[(postProcessedResult.length - 1)]['region_properties'];
                    }

                    this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result']['temp_region_properties_csv_file'] = "";
                    this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result']['region_properties_csv_file'] = "";
                    if (postProcessedResult[(postProcessedResult.length - 1)]['temp_region_properties_csv_file'] != undefined) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result']['temp_region_properties_csv_file'] = postProcessedResult[(postProcessedResult.length - 1)]['temp_region_properties_csv_file'];
                    }
                    if (postProcessedResult[(postProcessedResult.length - 1)]['region_properties_csv_file'] != undefined) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result']['region_properties_csv_file'] = postProcessedResult[(postProcessedResult.length - 1)]['region_properties_csv_file'];
                    }

                    if (postProcessedResult[(postProcessedResult.length - 1)]['boundary_excel'] != undefined &&
                      this.returnKeysFromObject(postProcessedResult[(postProcessedResult.length - 1)]['boundary_excel']).length > 0
                    ) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['result']['boundary_excel'] = postProcessedResult[(postProcessedResult.length - 1)]['boundary_excel'];
                    }
                    if (this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['fid'] == 26) {
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['slider']['size_removed']['range']['min'] = postProcessedResult[(postProcessedResult.length - 1)]['min_range'];
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['slider']['size_removed']['range']['max'] = postProcessedResult[(postProcessedResult.length - 1)]['maxrange'];
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['slider']['size_removed']['from'] = postProcessedResult[(postProcessedResult.length - 1)]['min_range'];
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['slider']['size_removed']['start'] = postProcessedResult[(postProcessedResult.length - 1)]['default_val'];
                      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][findIndex]['Params']['size_removed'] = postProcessedResult[(postProcessedResult.length - 1)]['default_val'];
                    }
                    postProcessedResult.splice(-1, 1);
                  }
                }
              }
            } else {
              if (postProcessedResult.length > 0) {
                let graphIndex = 0;
                for (let i = 0; i < this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].length; i++) {
                  if (i >= this.currentLayerData['layer'] && this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['selected'] == true && this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['fid'] == postProcessedResult[graphIndex]['fid']) {
                    this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result'] = {
                      "filtered_image": postProcessedResult[graphIndex]['filterd_image'],
                      "histogram_path": postProcessedResult[graphIndex]['histogram_path'],
                      "previewchanges": postProcessedResult[graphIndex]['previewchanges']
                    }

                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result'], 'filterd_image')
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result'], 'histogram_path')
                    this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result'], 'previewchanges')


                    if (postProcessedResult[graphIndex] != undefined && postProcessedResult[graphIndex] != "") {
                      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result']['black&white'] = postProcessedResult[graphIndex]['black&white'];
                      this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result'], 'black&white')
                    }
                    if (postProcessedResult[graphIndex]['region_properties'] != undefined &&
                      this.returnKeysFromObject(postProcessedResult[graphIndex]['region_properties']).length > 0
                    ) {
                      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result']['region_properties'] = postProcessedResult[graphIndex]['region_properties'];
                    }

                    this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result']['temp_region_properties_csv_file'] = "";
                    this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result']['region_properties_csv_file'] = ""
                    if (postProcessedResult[graphIndex]['temp_region_properties_csv_file'] != undefined) {
                      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result']['temp_region_properties_csv_file'] = postProcessedResult[graphIndex]['temp_region_properties_csv_file'];
                    }
                    if (postProcessedResult[graphIndex]['region_properties_csv_file'] != undefined) {
                      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result']['region_properties_csv_file'] = postProcessedResult[graphIndex]['region_properties_csv_file'];
                    }

                    if (postProcessedResult[graphIndex]['boundary_excel'] != undefined &&
                      this.returnKeysFromObject(postProcessedResult[graphIndex]['boundary_excel']).length > 0
                    ) {
                      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['result']['boundary_excel'] = postProcessedResult[graphIndex]['boundary_excel'];
                    }
                    if (this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['fid'] == 26) {
                      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['slider']['size_removed']['range']['min'] = postProcessedResult[graphIndex]['min_range'];
                      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['slider']['size_removed']['range']['max'] = postProcessedResult[graphIndex]['maxrange'];
                      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['slider']['size_removed']['from'] = postProcessedResult[graphIndex]['min_range'];
                      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['slider']['size_removed']['start'] = postProcessedResult[graphIndex]['default_val'];
                      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][i]['Params']['size_removed'] = postProcessedResult[graphIndex]['default_val'];
                    }
                    graphIndex++;
                  }
                }
              }
            }
          } else if (this.currentLayerData['type'] == 'scratch') {
            this.updateLayersData('preprocessingWorkflowFeatures', preProcessedResult);
            this.updateLayersData('segmentationWorkflowFeatures', segmentaionResult);
            this.updateLayersData('postprocessingWorkflowFeatures', postProcessedResult);
            this.currentLayerData['type'] = "";
          }

          if (this.currentLayerData['actionType'] != 'add') {
            this.resetCurrentLayerData();
          } else {
            this.currentLayerData['inputImage'] = "";
          }
          if (parsedImageData['draw_val'] != undefined && parsedData['draw_val'] != "") {
            this.segmentedImageDetails['selectedSegmentedImage']["scalebarByImage"] = parsedData['draw_val'];
          }
          if (parsedData['popup_val'] != undefined && parsedData['popup_val'] != "") {
            this.segmentedImageDetails['selectedSegmentedImage']["scalebarByPhysical"] = parsedData['popup_val'];
            this.segmentedImageDetails['selectedSegmentedImage']['scalebarByPhysicalUnit'] = parsedData['popup_unit'];
          }

          this.setRegionProps();
          // if (this.workflowLoading && this.saveWorkflowBtn) {
          //   this.saveWorkFlow('save');
          // }
          this.dropDownLayer = this.getLatestLayerData();
          this.workflowLoading = false;
          this.setLatestLayerForBaseLayer();
          // setTimeout(() => {
          //   this.apiCall = false;
          // }, 3000);

        }

      } else {
        this.apiCall = false;
        // this.toaster.error('Failed to fetch the images data', '', {
        //   positionClass: 'custom-toast-position',
        // });
      }
    })
      .catch((error) => {
        this.apiCall = false;
        console.error('Error fetching mounted drive data:', error);
        this.toastr.error(error, '', {
          positionClass: 'custom-toast-position',
        });

      });

    return true;
  }

  getBaseLayerImage(val: string) {
    let split_val: any = [];
    let opImage = "";
    if (val != "" && val != 'masked_image') {
      split_val = val.split('_');
      if (split_val[0] == 'pre-processing') {
        opImage = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][split_val[1]]['result']['filtered_image'];
      } else if (split_val[0] == 'segmentation') {
        let segmentationData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
        if (this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][split_val[1]]['Params']['visualization'] == 'Black/white (default)') {
          opImage = segmentationData[0]['result']['black&white'];
        } else {
          opImage = segmentationData[0]['result']['filtered_image'];
        }
      } else if (split_val[0] == 'post-processing') {
        let segmentationData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
        if (segmentationData[0]['Params']['visualization'] == 'Black/white (default)') {
          opImage = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][+split_val[1]]['result']['black&white'];
        } else {
          opImage = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][+split_val[1]]['result']['filtered_image'];
        }
      }
    } else {
      if (val == 'masked_image') {
        opImage = this.segmentedImageDetails['selectedSegmentedImage']['masked_image'];
      } else {
        opImage = this.segmentedImageDetails!['selectedSegmentedImage']['manual_image']
      }
    }
    return opImage;

  }

  getSegmentedImage(event: any) {
    let val = event;
    let opImage = "";
    let region_properties = {};
    if (!event) {
      if (this.segmentedImageDetails['selectedSegmentedImage']['masked_image'] && this.segmentedImageDetails['selectedSegmentedImage']['masked_image'] != '') {
        this.dropDownLayer = { "type": "masked", "mainVal": "masked", "val": "masked" };
        opImage = this.segmentedImageDetails['selectedSegmentedImage']['masked_image'];
      } else {
        this.dropDownLayer = { "type": "original", "mainVal": "original", "val": "original" };
        opImage = this.segmentedImageDetails['selectedSegmentedImage']['manual_image'];
      }
    } else {
      if (val != "" && val != 'masked_image') {
        let layerInfo: any = {};
        let split_val: any = []
        if (val == 'masked' || val == 'original') {
          // layerInfo = { "type": val, "mainVal": val, "val": val };  
        } else {
          split_val = val.split('_');
          // layerInfo = { "type": split_val[0], "mainVal": val, "val": parseInt(split_val[1]) + 1 };  
        }
        this.selectedSegmentedValue = val;
        // this.dropDownLayer = layerInfo;

        if (val != 'masked' && val != 'original') {
          if (split_val[0] == 'pre-processing') {
            opImage = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][+split_val[1]]['result']['filtered_image'];
          } else if (split_val[0] == 'segmentation') {
            if (this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][split_val[1]]['Params']['visualization'] == 'Black/white (default)') {
              opImage = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][+split_val[1]]['result']['black&white'];
            } else {
              opImage = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][+split_val[1]]['result']['filtered_image'];
            }
            region_properties = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][+split_val[1]]['result']['region_properties'];
          } else if (split_val[0] == 'post-processing') {
            let segmentationData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
            if (segmentationData[0]['Params']['visualization'] == 'Black/white (default)') {
              if (this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][+split_val[1]]['result']) {
                opImage = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][+split_val[1]]['result']['black&white'];
              }
            } else {
              opImage = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][+split_val[1]]['result']['filtered_image'];
            }
            // region_properties = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][split_val[1]]['result']['region_properties'];
          }
        } else {
          if (val == 'masked') {
            opImage = this.segmentedImageDetails['selectedSegmentedImage']['masked_image'];
          } else if (val == 'original') {
            opImage = this.segmentedImageDetails['selectedSegmentedImage']['manual_image'];
          }
        }

      } else {
        let getLastseg = this.getLastSegmentedImage('post-processing', false, "");
        opImage = getLastseg['filtered_image'];
      }
    }

    return opImage
  }

  get segmentedImageUrl(): string {
    return this.getSegmentatedImageURL()['url'];
  }

  get shouldDisplaySimpleImage(): boolean {
    return this.segInputImageSizeLimit >= this.segmentedImageDetails['selectedSegmentedImage']['cropimgShape'][1];
  }

  get shouldDisplayZoomedImage(): boolean {
    return this.segmentedImageDetails['segmentedImage'] &&
      this.segmentedImageDetails['selectedSegmentedImage']['cropimgShape'][1] > this.segInputImageSizeLimit;
  }



  isOriginalMaskedSelected() {
    return (this.dropDownLayer['mainVal'] == 'masked' || this.dropDownLayer['mainVal'] == 'original') ? true : false;
  }

  displayPreprocessing() {
    if (!this.isOriginalMaskedSelected() && this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] != undefined && this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] && this.getBelowLayers('preprocessingWorkflowFeatures', true).length > 0) {
      return true;
    } else {
      return false;
    }
  }
  displaySegmentedOptions() {
    if (
      !this.isOriginalMaskedSelected() &&
      (this.dropDownLayer['type'] == 'segementation' || this.dropDownLayer['type'] == 'post-processing') &&
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] &&
      this.getBelowLayers('segmentationWorkflowFeatures', true).length > 0
    ) {
      return true;
    } else {
      return false
    }
  }
  displayPostProcessingOptions() {
    if (
      !this.isOriginalMaskedSelected() &&
      this.dropDownLayer['type'] == 'post-processing' &&
      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] == true &&
      this.getBelowLayers('postprocessingWorkflowFeatures', true).length > 0
    ) {
      return true
    } else {
      return false;
    }
  }

  displaySegmentationImage(image: any, funCalledFrom: any) {
    this.segmentParamsChangeFlag = false;
    if (!('croppedImage' in image) || image['croppedImage'] == '') {
      image['croppedImage'] = image.manual_image
    }
    if (!('croppedImageShape' in image) || image['croppedImageShape'].length == 0) {
      image['croppedImageShape'] = image.manual_shape
    }
    this.segmentedImageDetails!['selectedSegmentedImage'] = {
      "shape": image.shape,
      "ImageStripSize": image.ImageStripSize,
      "image": image.image,
      "path": image.path,
      "PixelSizeX": image.PixelSizeX,
      "PixelSizeY": image.PixelSizeY,
      "workflowId": image['workflowId'],
      "appliedId": image['appliedId'],
      "resetCrop": true,
      "cropImageType": image['crop_type'],
      "manualcoordinates": {},
      "scalebarByImage": image['scalebar_options']['scalebarByImage'],
      "scalebarByPhysical": image['scalebar_options']['scalebarByPhysical'],
      "scalebarByPhysicalUnit": image['scalebar_options']['scalebarByPhysicalUnit'],
      "preprocessingWorkflowSelected": false,
      "preprocessingWorkflowFeatures": [],
      "tempPreprocessingWorkflowFeatures": [],
      "segmentationWorkflowSelected": false,
      "segmentationWorkflowFeatures": [],
      "tempSegmentationWorkflowFeatures": [],
      "postprocessingWorkflowSelected": false,
      "postprocessingWorkflowFeatures": [],
      "tempPostprocessingWorkflowFeatures": [],
      "baseImage": image['croppedImage'],
      "baseImageShape": image.croppedImageShape,
      "cropimg": image['croppedImage'],
      "cropimgShape": image.croppedImageShape,
      "scalebar": {},
      "outputDirectoryOptions": {
        "setDirectory": false,
        "defaultDirectory": true,
        "outputDirectory": ""
      },
      "image_masks": image['image_masks'],
      "manual_image": image['manual_image'],
      "category": image['category'],
      "masked_image": (image['masked_image']) ? image['masked_image'] : ""
    };
    this.segmentedImageDetails['inputImageForSegmentation'] = image['croppedImage'];
    this.segmentedImageDetails['displayInputImage'] = image['croppedImage'];
    this.segmentedImageDetails['segmentedImage'] = image['croppedImage'];
    this.previewImage = image['croppedImage'];

    this.selectedMask = this.segmentedImageDetails['selectedSegmentedImage']['image_masks'] ? this.segmentedImageDetails['selectedSegmentedImage']['image_masks'].find((mask: { apply: any; }) => mask.apply) : null;
    if (this.selectedMask) {
      this.selectedMask['old_coordinates'] = { ...this.selectedMask.coordinates };
      if (!image['masked_image'] && image['masked_image'] == '') {
        this.getMaskedImage();
      } else {
        this.segmentedImageDetails['selectedSegmentedImage']['cropimg'] = image['masked_image'];
      }
    }


    if (
      (this.selectedMask && this.segmentedImageDetails!['selectedSegmentedImage']['workflowId'] != '' &&
        this.segmentedImageDetails!['selectedSegmentedImage']['appliedId'] == 0) || (this.selectedMask && this.segmentedImageDetails!['selectedSegmentedImage']['workflowId'] == '')
    ) {
      setTimeout(() => {
        if (funCalledFrom == "image") {
          this.checkWorkflow();
        }
      }, 300);
    } else {
      setTimeout(() => {
        if (funCalledFrom == "image") {
          this.checkWorkflow();
          this.getImageContent(this.segmentedImageDetails, 'inputImageForSegmentation')
          this.getImageContent(this.segmentedImageDetails['selectedSegmentedImage'], 'baseImage')
          this.getImageContent(this.segmentedImageDetails, 'displayInputImage')
          this.originalImagedropDownLayer = { "type": "", "mainVal": "", "val": "" };

          if (image['masked_image'] && image['masked_image'] != '') {
            this.dropDownLayer = { "type": "masked", "mainVal": "masked", "val": "masked" };
          } else {
            this.dropDownLayer = { "type": "original", "mainVal": "original", "val": "original" };
          }
        }
        // this.magnifierCall()

      }, 300);
    }

    this.magnifierCall()
    if (this.selectedMask) {
      return { "type": "masked", "mainVal": "masked", "val": "masked" }
    } else {
      return { "type": "original", "mainVal": "original", "val": "original" }
    }

    // this.dropDownLayer = this.getLatestLayerData();
    // this.setOriginalImageDropDown(true);
  }
  magnifierCall() {
    this.createOverElement();

    // let originalImageContainer = this.elementRef.nativeElement.querySelector('.original_image div.ngxImageZoomContainer');
    // let filteredImageContainer = this.elementRef.nativeElement.querySelector('.filtered_image div.ngxImageZoomContainer');
    // let previewImageContainer = this.elementRef.nativeElement.querySelector('.preview_image div.ngxImageZoomContainer');
    // if (originalImageContainer) {
    //   originalImageContainer.addEventListener('mouseenter', this.showOriginalScrollZoomMsg.bind(this));
    //   originalImageContainer.addEventListener('mouseleave', this.showOriginalScrollZoomMsg.bind(this));
    // }

    // if (filteredImageContainer) {
    //   filteredImageContainer.addEventListener('mouseenter', this.showFilterScrollZoomMsg.bind(this));
    //   filteredImageContainer.addEventListener('mouseleave', this.showFilterScrollZoomMsg.bind(this));
    // }

    // if (previewImageContainer) {
    //   previewImageContainer.addEventListener('mouseenter', this.showPreviewScrollZoomMsg.bind(this));
    //   previewImageContainer.addEventListener('mouseleave', this.showPreviewScrollZoomMsg.bind(this));
    // }

  }

  getMaskedImage() {
    if (this.selectedMask) {
      let detail: any = {
        'base_image': this.segmentedImageDetails['selectedSegmentedImage']['image'],
        'image': this.segmentedImageDetails['selectedSegmentedImage']['baseImage'],
        'coordinates': this.selectedMask['coordinates']
      }
      let coordinates = detail['coordinates'];
      detail['ymax'] = 0;
      detail['path'] = true;

      this.apiCall = true;

      this.imageAnalysisService.getMaskImage(detail).then((response) => {
        this.apiCall = false;
        if (response) {
          this.segmentedImageDetails['selectedSegmentedImage']['masked_image'] = response['cropimg'];
          this.segmentedImageDetails['selectedSegmentedImage']['cropimg'] = response['cropimg'];
        }
      });
    }
  }
  createOverElement() {
    let originalImageContainer = this.elementRef.nativeElement.querySelector('.original_image div.ngxImageZoomContainer');
    let filteredImageContainer = this.elementRef.nativeElement.querySelector('.filtered_image div.ngxImageZoomContainer');
    let previewImageContainer = this.elementRef.nativeElement.querySelector('.preview_image div.ngxImageZoomContainer');

    if (originalImageContainer) {
      let hoverElem = this.renderer.createElement('span');
      let text = this.renderer.createText("Scroll to Zoom In/Out");
      this.renderer.addClass(hoverElem, 'hoverScrollMsg');
      this.renderer.appendChild(hoverElem, text);
      this.renderer.appendChild(this.elementRef.nativeElement.querySelector('.original_image div.ngxImageZoomFullContainer'), hoverElem);
    }

    if (filteredImageContainer) {
      let hoverElem2 = this.renderer.createElement('span');
      let text2 = this.renderer.createText("Scroll to Zoom In/Out");
      this.renderer.addClass(hoverElem2, 'hoverScrollMsg2');
      this.renderer.appendChild(hoverElem2, text2);
      this.renderer.appendChild(this.elementRef.nativeElement.querySelector('.filtered_image div.ngxImageZoomFullContainer'), hoverElem2);
    }

    if (previewImageContainer) {
      let hoverElem3 = this.renderer.createElement('span');
      let text3 = this.renderer.createText("Scroll to Zoom In/Out");
      this.renderer.addClass(hoverElem3, 'hoverScrollMsg3');
      this.renderer.appendChild(hoverElem3, text3);
      this.renderer.appendChild(this.elementRef.nativeElement.querySelector('.preview_image div.ngxImageZoomFullContainer'), hoverElem3);
    }

  }

  showOriginalScrollZoomMsg(event: Event) {
    clearTimeout(this.mouseHoverTime);

    // Cache your element selections
    const filteredImageContainer = this.elementRef.nativeElement.querySelector('.filtered_image div.ngxImageZoomFullContainer');
    const previewImageContainer = this.elementRef.nativeElement.querySelector('.preview_image div.ngxImageZoomFullContainer');
    const originalImageContainer = this.elementRef.nativeElement.querySelector('.original_image div.ngxImageZoomFullContainer');

    const hoverScrollMsg = this.elementRef.nativeElement.querySelector('span.hoverScrollMsg');
    const hoverScrollMsg2 = this.elementRef.nativeElement.querySelector('span.hoverScrollMsg2');
    const hoverScrollMsg3 = this.elementRef.nativeElement.querySelector('span.hoverScrollMsg3');
    if (event.type === 'mouseenter') {

      if (originalImageContainer) {
        filteredImageContainer.style.display = 'block';
      }

      if (filteredImageContainer) {
        filteredImageContainer.style.display = 'block';
      }

      if (previewImageContainer) {
        previewImageContainer.style.display = 'block';
      }

      if (hoverScrollMsg) {
        hoverScrollMsg.style.display = 'block';
      }

      if (hoverScrollMsg2) {
        hoverScrollMsg2.style.display = 'none';
      }

      if (hoverScrollMsg3) {
        hoverScrollMsg3.style.display = 'none';
      }

      this.mouseHoverTime = setTimeout(() => {
        if (hoverScrollMsg) {
          hoverScrollMsg.style.display = 'none';
        }
      }, 3500);
    } else {
      if (hoverScrollMsg) {
        hoverScrollMsg.style.display = 'none';
      }

      if (hoverScrollMsg2) {
        hoverScrollMsg2.style.display = 'none';
      }

      if (hoverScrollMsg3) {
        hoverScrollMsg3.style.display = 'none';
      }

      if (originalImageContainer) {
        originalImageContainer.style.display = 'none';
      }

      if (filteredImageContainer) {
        filteredImageContainer.style.display = 'none';
      }

      if (previewImageContainer) {
        previewImageContainer.style.display = 'none';
      }
    }
  }

  showFilterScrollZoomMsg(event: Event) {
    clearTimeout(this.mouseHoverTime);
    let originalImageContainer = this.elementRef.nativeElement.querySelector('.original_image div.ngxImageZoomFullContainer');
    let filteredImageContainer = this.elementRef.nativeElement.querySelector('.filtered_image div.ngxImageZoomFullContainer');
    let previewImageContainer = this.elementRef.nativeElement.querySelector('.preview_image div.ngxImageZoomFullContainer');
    let hoverScrollMsg = this.elementRef.nativeElement.querySelector('span.hoverScrollMsg');
    let hoverScrollMsg2 = this.elementRef.nativeElement.querySelector('span.hoverScrollMsg2');
    let hoverScrollMsg3 = this.elementRef.nativeElement.querySelector('span.hoverScrollMsg3');
    if (event.type === 'mouseenter') {
      if (originalImageContainer) {
        originalImageContainer.style.display = 'block';
      }

      if (filteredImageContainer) {
        filteredImageContainer.style.display = 'block';
      }

      if (previewImageContainer) {
        previewImageContainer.style.display = 'block';
      }

      if (hoverScrollMsg) {
        hoverScrollMsg.style.display = 'none';
      }

      if (hoverScrollMsg2) {
        hoverScrollMsg2.style.display = 'block';
      }

      if (hoverScrollMsg3) {
        hoverScrollMsg3.style.display = 'none';
      }

      this.mouseHoverTime = setTimeout(() => {
        if (hoverScrollMsg2) {
          hoverScrollMsg2.style.display = 'none';
        }
      }, 3500);
    } else {
      if (hoverScrollMsg) {
        hoverScrollMsg.style.display = 'none';
      }
      if (hoverScrollMsg2) {
        hoverScrollMsg2.style.display = 'none';
      }
      if (hoverScrollMsg3) {
        hoverScrollMsg3.style.display = 'none';
      }
      if (originalImageContainer) {
        originalImageContainer.style.display = 'none';
      }
      if (filteredImageContainer) {
        filteredImageContainer.style.display = 'none';
      }
      if (previewImageContainer) {
        previewImageContainer.style.display = 'none';
      }
    }
  }


  showPreviewScrollZoomMsg(event: Event) {
    clearTimeout(this.mouseHoverTime);

    // Cache your element selections
    let originalImageContainer = this.elementRef.nativeElement.querySelector('.original_image div.ngxImageZoomFullContainer');
    let filteredImageContainer = this.elementRef.nativeElement.querySelector('.filtered_image div.ngxImageZoomFullContainer');
    let previewImageContainer = this.elementRef.nativeElement.querySelector('.preview_image div.ngxImageZoomFullContainer');

    let hoverScrollMsg = this.elementRef.nativeElement.querySelector('span.hoverScrollMsg');
    let hoverScrollMsg2 = this.elementRef.nativeElement.querySelector('span.hoverScrollMsg2');
    let hoverScrollMsg3 = this.elementRef.nativeElement.querySelector('span.hoverScrollMsg3');

    if (event.type === 'mouseenter') {
      if (originalImageContainer) {
        originalImageContainer.style.display = 'block';
      }

      if (filteredImageContainer) {
        filteredImageContainer.style.display = 'block';
      }

      if (hoverScrollMsg) {
        hoverScrollMsg.style.display = 'none';
      }

      if (hoverScrollMsg2) {
        hoverScrollMsg2.style.display = 'none';
      }

      if (hoverScrollMsg3) {
        hoverScrollMsg3.style.display = 'block';
      }

      this.mouseHoverTime = setTimeout(() => {
        if (hoverScrollMsg3) {
          hoverScrollMsg3.style.display = 'none';
        }
      }, 3500);
    } else {
      if (hoverScrollMsg) {
        hoverScrollMsg.style.display = 'none';
      }

      if (hoverScrollMsg2) {
        hoverScrollMsg2.style.display = 'none';
      }

      if (hoverScrollMsg3) {
        hoverScrollMsg3.style.display = 'none';
      }

      if (originalImageContainer) {
        originalImageContainer.style.display = 'none';
      }

      if (filteredImageContainer) {
        filteredImageContainer.style.display = 'none';
      }

      if (previewImageContainer) {
        previewImageContainer.style.display = 'none';
      }
    }
  }
  zoomImageLoaded(event: boolean, type: string) {
    if (event) {
      if (type == 'segmented') {
        this.segmentedLoading = true;
        let filteredImageContainer = this.elementRef.nativeElement.querySelector('.filtered_image div.ngxImageZoomContainer');
        if (filteredImageContainer) {
          filteredImageContainer.addEventListener('mouseenter', this.showFilterScrollZoomMsg.bind(this));
          filteredImageContainer.addEventListener('mouseleave', this.showFilterScrollZoomMsg.bind(this));
        }
      } else if (type == 'original') {
        this.originalLoading = true;
        let originalImageContainer = this.elementRef.nativeElement.querySelector('.original_image div.ngxImageZoomContainer');
        if (originalImageContainer) {
          originalImageContainer.addEventListener('mouseenter', this.showOriginalScrollZoomMsg.bind(this));
          originalImageContainer.addEventListener('mouseleave', this.showOriginalScrollZoomMsg.bind(this));
        }
      } else if (type == 'preview') {
        this.previewLoading = true;
        let previewImageContainer = this.elementRef.nativeElement.querySelector('.preview_image div.ngxImageZoomContainer');
        if (previewImageContainer) {
          previewImageContainer.addEventListener('mouseenter', this.showPreviewScrollZoomMsg.bind(this));
          previewImageContainer.addEventListener('mouseleave', this.showPreviewScrollZoomMsg.bind(this));
        }
      }
      clearTimeout(this.mouseHoverTime);
    }
  }


  checkImageLoaded() {
    if ((this.segmentedLoading && this.originalLoading) || (this.segmentedLoading && this.previewLoading)) {
      return true;
    } else {
      return false;
    }
  }

  checkPosition(_event: any, element: string, targetElements: string[]) {
    let elementQuery = this.elementRef.nativeElement.querySelector(`.${element} div.ngxImageZoomFullContainer.ngxImageZoomLensEnabled`);
    let elementImageQuery = this.elementRef.nativeElement.querySelector(`.${element} div.ngxImageZoomFullContainer.ngxImageZoomLensEnabled .ngxImageZoomFull`);

    // Check if the element queries exist
    if (!elementQuery || !elementImageQuery) {
      return; // Exit if the elements do not exist
    }
    targetElements.forEach((indElement: string) => {
      const targetElementQuery = this.elementRef.nativeElement.querySelector(
        `.${indElement} div.ngxImageZoomFullContainer.ngxImageZoomLensEnabled`
      );
      const targetElementImageQuery = this.elementRef.nativeElement.querySelector(
        `.${indElement} div.ngxImageZoomFullContainer.ngxImageZoomLensEnabled .ngxImageZoomFull`
      );

      if (targetElementQuery) {
        targetElementQuery.style.display = "block";
        if (elementQuery) {
          targetElementQuery.style.top = window.getComputedStyle(elementQuery).getPropertyValue('top');
          targetElementQuery.style.left = window.getComputedStyle(elementQuery).getPropertyValue('left');
        }
      }

      if (targetElementImageQuery) {
        targetElementImageQuery.style.display = "block";
        if (elementImageQuery) {
          targetElementImageQuery.style.top = window.getComputedStyle(elementImageQuery).getPropertyValue('top');
          targetElementImageQuery.style.left = window.getComputedStyle(elementImageQuery).getPropertyValue('left');
          targetElementImageQuery.style.width = window.getComputedStyle(elementImageQuery).getPropertyValue('width');
          targetElementImageQuery.style.height = window.getComputedStyle(elementImageQuery).getPropertyValue('height');
        }
      }
    });

    clearTimeout(this.mouseHoverTime);
  }
  checkWorkflow() {
    if (this.segmentedImageDetails['selectedSegmentedImage']['workflowId'] != "" &&
      this.segmentedImageDetails['selectedSegmentedImage']['workflowId'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['workflowId'] != 0) {
      this.newWorkflow = false;
      this.editWorkflowId = this.segmentedImageDetails['selectedSegmentedImage']['workflowId'];
      let workflowData = this.allWorkFlows.find((val: any) => (val['_id'] == this.editWorkflowId));
      if (workflowData != undefined && workflowData['_id'] != "") {
        this.carryForwardOptions(workflowData);
        this.workflowLoading = true;
        if (typeof workflowData['modification'] === 'object' && workflowData['modification'] !== null) {
          this.segmentedImageDetails['selectedSegmentedImage']['cropImageType'] = "manual";
          this.segmentedImageDetails['selectedSegmentedImage']["manualcoordinates"] = workflowData['modification'];
        }
        this.editWorkflowName = workflowData['Wname'];
        this.segmentedImageDetails['selectedSegmentedImage']["outputDirectoryOptions"] = workflowData['output_directory_options'];
        this.currentLayerData['type'] = 'scratch';
        if (this.segmentedImageDetails['selectedSegmentedImage']['appliedId'] != "" &&
          this.segmentedImageDetails['selectedSegmentedImage']['appliedId'] != undefined &&
          this.segmentedImageDetails['selectedSegmentedImage']['appliedId'] != 0) {
          this.retrieveWorkflow = true;
          this.cropApplied = false;
        } else {
          this.retrieveWorkflow = false;
          if (this.carryForwardCrop) {
            this.cropApplied = true;
          } else {
            this.cropApplied = false;
          }
          this.saveWorkflowBtnEvent.emit(true);
        }
        this.assignWorkflowFeatures(workflowData);
        // setTimeout(() => {
        //   this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
        // }, 1000);

      } else {
        this.newWorkflow = true;
        this.retrieveWorkflow = false;
        this.cropApplied = true;
        this.editWorkflowId = "";
        this.editWorkflowName = "";
        this.currentLayerData['type'] = "";
        this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
      }
    } else {
      this.newWorkflow = true;
      this.retrieveWorkflow = false;
      this.cropApplied = true;
      this.editWorkflowId = "";
      this.editWorkflowName = "";
      this.currentLayerData['type'] = "";
      this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
    }
  }

  editworkflow(editWorkflowData: any) {
    let type = editWorkflowData['type'];
    let workflowData = editWorkflowData['workflowData'];
    let selectedSegmentImages = editWorkflowData['selectedSegmentImages'];
    if (type == 'edit') {
      // this.carryForwardOptions(workflowData);
      let imageForworkflow = editWorkflowData['imageForWorkflow'];
      let copyWorkflow = editWorkflowData['copyWorkflow'];
      if (copyWorkflow) {
        this.editWorkflowId = workflowData['_id'];
        this.editWorkflowName = workflowData['Wname'];
        this.newWorkflow = true;
        this.saveWorkflowBtnEvent.emit(true);
      } else {
        this.editWorkflowId = workflowData['_id'];
        this.editWorkflowName = workflowData['Wname'];
        this.newWorkflow = false;
        this.saveWorkflowBtnEvent.emit(false);
        this.workflowLoading = true;
      }
      this.displaySegmentationImage(imageForworkflow, 'workflow');
      this.segmentedImageDetails['selectedSegmentedImage']["outputDirectoryOptions"] = workflowData['output_directory_options']
      if (typeof workflowData['modification'] === 'object' && workflowData['modification'] !== null) {
        this.segmentedImageDetails['selectedSegmentedImage']['cropImageType'] = "manual";
        this.segmentedImageDetails['selectedSegmentedImage']["manualcoordinates"] = workflowData['modification'];
      }
      this.currentLayerData['type'] = 'scratch';
      if (imageForworkflow['workflowId'] != undefined &&
        imageForworkflow['workflowId'] != "" &&
        imageForworkflow['workflowId'] != 0 &&
        imageForworkflow['workflowId'] == workflowData['_id'] &&
        imageForworkflow['appliedId'] != undefined &&
        imageForworkflow['appliedId'] != "" &&
        imageForworkflow['appliedId'] != 0
      ) {
        this.retrieveWorkflow = true;
        this.cropApplied = false;
      } else {
        this.retrieveWorkflow = false;
        if (this.carryForwardCrop) {
          this.cropApplied = true;
        } else {
          this.cropApplied = false;
        }
        this.saveWorkflowBtnEvent.emit(true);
      }
      // this.assignWorkflowFeatures(workflowData);
      // this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
    } else if (type == 'new' && selectedSegmentImages.length > 0) {
      // this.carryForwardOptions(workflowData);
      this.editWorkflowId = "";
      this.editWorkflowName = "";
      this.newWorkflow = true;
      this.displaySegmentationImage(selectedSegmentImages[0], 'workflow');
    }
  }

  getLastSegmentedImage(type: any, checkLayerwise: any, layerInd: any) {
    let lastSegmentedImage: any = {
      "filtered_image": this.segmentedImageDetails['inputImageForSegmentation'],
      "filtered_image_url": this.segmentedImageDetails['inputImageForSegmentation_url']
    };
    let preProcessingData: any[] = [];
    let segmentationData = [];
    let postProcessingData = [];
    if (checkLayerwise) {
      if (type == 'pre-processing') {
        if (
          this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] != undefined &&
          this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] == true &&
          this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'] != undefined
        ) {
          preProcessingData = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].filter((val: any, index: number) => (index < layerInd && val['selected'] == true));
        }
        if (preProcessingData.length > 0) {
          lastSegmentedImage["filtered_image"] = preProcessingData[preProcessingData.length - 1]['result']['filtered_image'];
          lastSegmentedImage["filtered_image_url"] = preProcessingData[preProcessingData.length - 1]['result']['filtered_image_url'];
        }
      } else if (type == 'segmentation') {
        if (
          this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] != undefined &&
          this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] == true &&
          this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'] != undefined
        ) {
          segmentationData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any, index: number) => (index < layerInd && val['selected'] == true));
        }
        if (segmentationData.length > 0) {
          lastSegmentedImage["filtered_image"] = segmentationData[segmentationData.length - 1]['result']['filtered_image'];
          lastSegmentedImage["filtered_image_url"] = segmentationData[segmentationData.length - 1]['result']['filtered_image_url'];
          if (segmentationData[segmentationData.length - 1]['result']['region_properties'] != undefined) {
            lastSegmentedImage['region_properties'] = segmentationData[segmentationData.length - 1]['result']['region_properties'];
          }
        } else {
          lastSegmentedImage = this.getLastSegmentedImage('pre-processing', false, "");
        }
      } else if (type == 'post-processing') {
        if (
          this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] != undefined &&
          this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] == true &&
          this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'] != undefined
        ) {
          postProcessingData = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].filter((val: any, index: number) => (index < layerInd && val['selected'] == true));
        }
        if (postProcessingData.length > 0) {
          lastSegmentedImage["filtered_image"] = postProcessingData[postProcessingData.length - 1]['result']['filtered_image'];
          lastSegmentedImage["black&white"] = postProcessingData[postProcessingData.length - 1]['result']['black&white'];
          lastSegmentedImage["filtered_image_url"] = postProcessingData[postProcessingData.length - 1]['result']['filtered_image_url'];
          lastSegmentedImage["black&white_url"] = postProcessingData[postProcessingData.length - 1]['result']['black&white_url'];
          if (postProcessingData[postProcessingData.length - 1]['result']['region_properties'] != undefined) {
            lastSegmentedImage['region_properties'] = postProcessingData[postProcessingData.length - 1]['result']['region_properties'];
          }
        } else {
          lastSegmentedImage = this.getLastSegmentedImage('segmentation', false, "");
        }
      }
    } else {
      if (
        this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] == true &&
        this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'] != undefined
      ) {
        preProcessingData = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
      }
      if (
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] == true &&
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'] != undefined
      ) {
        segmentationData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
      }
      if (
        this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] == true &&
        this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'] != undefined
      ) {
        postProcessingData = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
      }
      if (type == "pre-processing") {
        if (preProcessingData.length > 0) {
          lastSegmentedImage["filtered_image"] = preProcessingData[preProcessingData.length - 1]['result']['filtered_image'];
          lastSegmentedImage["filtered_image_url"] = preProcessingData[preProcessingData.length - 1]['result']['filtered_image_url'];
        }
      } else if (type == "segmentation") {
        if (segmentationData.length > 0) {
          lastSegmentedImage["filtered_image"] = segmentationData[segmentationData.length - 1]['result']['filtered_image'];
          lastSegmentedImage["black&white"] = segmentationData[segmentationData.length - 1]['result']['black&white'];

          lastSegmentedImage["filtered_image_url"] = segmentationData[segmentationData.length - 1]['result']['filtered_image_url'];
          lastSegmentedImage["black&white_url"] = segmentationData[segmentationData.length - 1]['result']['black&white_url'];

          if (segmentationData[segmentationData.length - 1]['result']['region_properties'] != undefined) {
            lastSegmentedImage['region_properties'] = segmentationData[segmentationData.length - 1]['result']['region_properties'];
          }
        } else if (preProcessingData.length > 0) {
          lastSegmentedImage["filtered_image"] = preProcessingData[preProcessingData.length - 1]['result']['filtered_image'];
          lastSegmentedImage["filtered_image_url"] = segmentationData[segmentationData.length - 1]['result']['filtered_image_url'];
        }
      } else if (type == "post-processing") {
        if (postProcessingData.length > 0) {
          if (postProcessingData[postProcessingData.length - 1]['result']['filtered_image'] != undefined) {
            lastSegmentedImage["filtered_image"] = postProcessingData[postProcessingData.length - 1]['result']['filtered_image'];
            lastSegmentedImage["filtered_image_url"] = postProcessingData[postProcessingData.length - 1]['result']['filtered_image_url'];
          }
          lastSegmentedImage["black&white"] = postProcessingData[postProcessingData.length - 1]['result']['black&white'];
          lastSegmentedImage["black&white_url"] = postProcessingData[postProcessingData.length - 1]['result']['black&white_url'];
          if (postProcessingData[postProcessingData.length - 1]['result']['region_properties'] != undefined) {
            lastSegmentedImage['region_properties'] = postProcessingData[postProcessingData.length - 1]['result']['region_properties'];
          }
        } else if (segmentationData.length > 0) {
          lastSegmentedImage["filtered_image"] = segmentationData[segmentationData.length - 1]['result']['filtered_image'];
          lastSegmentedImage["black&white"] = segmentationData[segmentationData.length - 1]['result']['black&white'];

          lastSegmentedImage["filtered_image_url"] = segmentationData[segmentationData.length - 1]['result']['filtered_image_url'];
          lastSegmentedImage["black&white_url"] = segmentationData[segmentationData.length - 1]['result']['black&white_url'];

          if (segmentationData[segmentationData.length - 1]['result']['region_properties'] != undefined) {
            lastSegmentedImage['region_properties'] = segmentationData[segmentationData.length - 1]['result']['region_properties'];
          }
        } else if (preProcessingData.length > 0) {
          lastSegmentedImage["filtered_image"] = preProcessingData[preProcessingData.length - 1]['result']['filtered_image'];
          lastSegmentedImage["filtered_image_url"] = preProcessingData[preProcessingData.length - 1]['result']['filtered_image_url'];
        }
      }
    }
    return lastSegmentedImage;
  }

  getBelowLayers(type: string, checkSelected: boolean) {
    return this.segmentedImageDetails['selectedSegmentedImage'][type].filter((val: any, index: number) => {
      // Check if the condition on `checkSelected` is satisfied
      if ((checkSelected && val['selected'] === true) || !checkSelected) {
        // Pre-processing
        if (this.dropDownLayer['type'] === 'pre-processing' && type === "preprocessingWorkflowFeatures") {
          return index < (this.dropDownLayer['val'] - 1);
        }
        // Segmentation
        else if (this.dropDownLayer['type'] === 'segmentation' && type === "segmentationWorkflowFeatures") {
          return index < (this.dropDownLayer['val'] - 1);
        }
        // Post-processing
        else if (this.dropDownLayer['type'] === 'post-processing' && type === "postprocessingWorkflowFeatures") {
          return index < (this.dropDownLayer['val'] - 1);
        }
        // Default case
        return true;
      }
      return false;  // Explicitly return false for other cases
    });
  }


  setLatestLayerForBaseLayer() {
    let preprocessingLayers = this.getBelowLayers('preprocessingWorkflowFeatures', false)
    let segmentedLayers = this.getBelowLayers('segmentationWorkflowFeatures', false)
    let postprocessingLayers = this.getBelowLayers('postprocessingWorkflowFeatures', false)

    let type = this.dropDownLayer.type;
    if (type == 'masked' || type == 'original') {
      this.changeLayerView('', 'original_image');
    }
    if (type == 'pre-processing') {
      if (preprocessingLayers.length > 0) {
        let mainVal = 'pre-processing_' + (preprocessingLayers.length - 1).toString();
        this.changeLayerView(mainVal, 'original_image');
      } else {
        if (this.selectedMask) {
          this.changeLayerView('masked_image', 'original_image');
        } else {
          this.changeLayerView('', 'original_image');
        }
      }
    } else if (type == 'segmentation') {
      let mainVal = 'pre-processing_' + (preprocessingLayers.length - 1).toString();
      this.changeLayerView(mainVal, 'original_image');
    } else if (type == 'post-processing') {
      if (postprocessingLayers.length > 0) {
        let mainVal = 'post-processing_' + (postprocessingLayers.length - 1).toString();
        this.changeLayerView(mainVal, 'original_image');
      } else {
        var index = segmentedLayers.findIndex((val: any) => val.selected === true)
        let mainVal = 'segmentation_' + index.toString();
        // let mainVal = 'segmentation_'+(segmentedLayers.length-1).toString();
        this.changeLayerView(mainVal, 'original_image');
      }
    }
    this.apiCall = false;
  }


  setWorkflowFeaturesToApply(workflowFeatures: any, type: string) {
    let preProcessingData = [];
    let segmentationData = [];
    let postProcessingData = [];
    if (type == 'pre-processing') {
      if (
        this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] == true &&
        this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'] != undefined
      ) {
        preProcessingData = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
      }
      if (preProcessingData.length > 0) {
        workflowFeatures = workflowFeatures.concat(preProcessingData);
      }
    } else if (type == 'segmentation') {
      if (
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] == true &&
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'] != undefined
      ) {
        segmentationData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
      }
      if (segmentationData.length > 0) {
        workflowFeatures = workflowFeatures.concat(segmentationData);
      }
    } else if (type == 'post-processing') {
      if (
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] == true &&
        this.getFeaturesCount('segmentationWorkflowFeatures') > 0 &&
        this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] == true &&
        this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'] != undefined
      ) {
        postProcessingData = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
      }
      if (postProcessingData.length > 0) {
        workflowFeatures = workflowFeatures.concat(postProcessingData);
      }
    }
    return workflowFeatures;
  }

  getUnitValue(unit: string) {
    return this.unitValues.find((val: any) => val['unit'] == unit);
  }

  getFinalScaleValueAfterAdjusting() {
    let firstVal = parseInt(this.segmentedImageDetails['selectedSegmentedImage']['scalebarByPhysical']) / parseInt(this.segmentedImageDetails['selectedSegmentedImage']['scalebarByImage']);
    let secondVal = parseInt(this.getUnitValue(this.segmentedImageDetails['selectedSegmentedImage']['scalebarByPhysicalUnit'])['value']);
    let finalVal = firstVal * secondVal;
    return parseFloat(finalVal.toFixed(4));
  }

  calculateScalbarForModifiedImage() {
    if (this.segmentedImageDetails['selectedSegmentedImage']['scalebarByImage'] != '' && this.segmentedImageDetails['selectedSegmentedImage']['scalebarByPhysical'] != '') {
      setTimeout((_val: any) => {
        let imageContainer;
        if (this.segmentedImageDetails['selectedSegmentedImage']['shape'][1] > this.segInputImageSizeLimit) {
          imageContainer = (document.querySelector('.modified-image .original_image_block img.ngxImageZoomThumbnail'));
        } else {
          imageContainer = (document.querySelector('.modified-image .original_image_block img.originalImageTag'));
        }

        var data = {
          "client_width": imageContainer!.clientWidth,
          "PixelSizeX": this.segmentedImageDetails['selectedSegmentedImage']["PixelSizeX"],
          "modified_image": this.segmentedImageDetails['inputImageForSegmentation'],
          "px_scale": this.getFinalScaleValueAfterAdjusting(),
          "scale_unit": this.segmentedImageDetails['selectedSegmentedImage']['scalebarByPhysicalUnit']
        };
        this.imageAnalysisService
          .getScalebarForModifiedImage(data)
          .then((response) => {
            if (response) {
              this.segmentedImageDetails['selectedSegmentedImage']['scalebar'] = response;
            }
          });
        // this.imageAnalysisService.getScalebarForModifiedImage(data).subscribe(response => {
        //   var parsedData = response;
        //   if (parsedData['status'] == 200) {
        //     this.segmentedImageDetails['selectedSegmentedImage']['scalebar'] = parsedData['data'];
        //   }
        // });
      }, 500);
    }
  }

  getFeaturesCount(type: any) {
    return this.segmentedImageDetails['selectedSegmentedImage'][type].filter((val: any) => val['selected'] == true).length;
  }

  getSegmentedFeatures() {
    return this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => val['selected'] == true);
  }

  getOriginalImageUrl() {
    let baseLayer = this.getBaseLayerImage(this.originalImagedropDownLayer.mainVal);
    return `${this.imageDisplayUrl}?file_path=${baseLayer}&&file_name=${this.getImageName(baseLayer)}`;
    // if (this.editBinarization &&
    //   this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] &&
    //   this.getSegmentedFeatures().length > 0 &&
    //   this.getSegmentedFeatures()[0]['result'] != undefined &&
    //   this.getSegmentedFeatures()[0]['result']['perula'] != undefined &&
    //   this.getSegmentedFeatures()[0]['result']['perula'] != '') {
    //   return this.getSegmentedFeatures()[0]['result']['perula_url'];
    // } else {
    //   return this.segmentedImageDetails['displayInputImage_url'];
    // }
  }

  getPreviewImage() {
    let imageUrl = (this.showPreviewImage && this.getLatesPreviewImage() != '') ? this.getLatesPreviewImage() : this.previewImage_url
    return imageUrl;
  }


  getSegmentatedImageRegionProperties() {
    let returnProps = {};
    if (this.newInnerLayer &&
      (this.newInnerLayerDetails['fid'] == 14 || this.newInnerLayerDetails['fid'] == 15) &&
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['result'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['result']['perula'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['result']['perula'] != '') {
      if (this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['result']['region_properties'] != undefined) {
        returnProps = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['result']['region_properties'];
      }
    } else {
      if (this.newInnerLayer) {
        let type = '';
        if (this.newLayerFor == 'pre-processing' || this.newLayerFor == 'segmentation') {
          type = 'pre-processing';
        } else if (this.newLayerFor == 'post-processing') {
          type = 'post-processing';
        }
        let disImage = this.getLastSegmentedImage(type, '', '');
        if (type != 'pre-processing') {
          if (disImage['region_properties'] != undefined) {
            returnProps = disImage['region_properties']
          }
        }
      } else {
        returnProps = this.segmentedImageDetails['region_properties'];
      }
    }
    return { 'properties': this.convertRegionPropertes(returnProps) };
  }
  getScalebarUnit() {
    if (this.segmentedImageDetails['selectedSegmentedImage']['scalebarByPhysicalUnit'] == "") {
      return "px"
    } else {
      return this.segmentedImageDetails['selectedSegmentedImage']['scalebarByPhysicalUnit'];
    }
  }
  isymUnit() {
    return this.segmentedImageDetails['selectedSegmentedImage']['scalebarByPhysicalUnit'] == "μm" ? true : false;
  }
  getSegmentatedImageURL() {

    let returnurl = '';
    let returnProps = {};


    if (this.newInnerLayer &&
      (this.newInnerLayerDetails['fid'] == 14 || this.newInnerLayerDetails['fid'] == 15) &&
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['result'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['result']['perula'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['result']['perula'] != '') {
      returnurl = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['result']['perula_url'];
      if (this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['result']['region_properties'] != undefined) {
        returnProps = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['result']['region_properties'];
      }
    } else {
      if (this.newInnerLayer) {
        let type = '';
        if (this.newLayerFor == 'pre-processing' || this.newLayerFor == 'segmentation') {
          type = 'pre-processing';
        } else if (this.newLayerFor == 'post-processing') {
          type = 'post-processing';
        }

        let disImage = this.getLastSegmentedImage(type, '', '');
        if (type == 'pre-processing') {
          if (disImage['filtered_image_url']) {
            returnurl = disImage['filtered_image_url'];
          } else {
            returnurl = `${this.imageDisplayUrl}?file_path=${disImage['filtered_image']}&&file_name=${this.getImageName(disImage['filtered_image'])}`;
          }
        } else {
          let segmentationData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => val['selected'] == true);
          if (segmentationData.length > 0 && segmentationData[0]['Params']['visualization'] == 'Black/white (default)') {
            if (disImage['black&white_url']) {
              returnurl = disImage['black&white_url'];
            } else {
              returnurl = `${this.imageDisplayUrl}?file_path=${disImage['black&white']}&&file_name=${this.getImageName(disImage['black&white'])}`;
            }
          } else {
            if (disImage['filtered_image_url']) {
              returnurl = disImage['filtered_image_url'];
            } else {
              returnurl = `${this.imageDisplayUrl}?file_path=${disImage['filtered_image']}&&file_name=${this.getImageName(disImage['filtered_image'])}`;
            }
          }
          if (disImage['region_properties'] != undefined) {
            returnProps = disImage['region_properties'];
          }
        }
      } else {
        let imagePath = this.getSegmentedImage(this.dropDownLayer.mainVal);
        returnurl = `${this.imageDisplayUrl}?file_path=${imagePath}&&file_name=${this.getImageName(imagePath)}`;
        returnProps = this.segmentedImageDetails['region_properties'];
      }
    }
    return { 'url': returnurl, 'region_properties': returnProps };
  }


  getTempRegionProps() {
    let region_properties: any = {};
    if (this.newInnerLayer && this.newLayerFor != "") {
      let layer: any = {};
      if (this.newLayerFor == 'pre-processing') {
        layer = this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][0];
      } else if (this.newLayerFor == 'segmentation') {
        layer = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0];
      } else if (this.newLayerFor == 'post-processing') {
        layer = this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][0];
      }
      if (layer['result'] != undefined && layer['result']['region_properties'] != undefined && this.returnKeysFromObject(layer['result']['region_properties']).length > 0) {
        region_properties = layer['result']['region_properties'];
      }
    }
    return region_properties;
  }
  getTempRegionPropsFormatted() {
    return { 'properties': this.convertRegionPropertes(this.getTempRegionProps()) };
  }
  convertRegionPropertes(region_properties: any) {
    var unit = this.segmentedImageDetails['selectedSegmentedImage']['scalebarByPhysicalUnit'];
    if (unit == "") {
      unit = "px";
    }
    // Validate region_properties
    if (region_properties == null || typeof region_properties !== 'object') {
      return {}; // Return an empty object if region_properties is null or not an object
    }
    var unit = this.segmentedImageDetails['selectedSegmentedImage']['scalebarByPhysicalUnit'] || "px";
    let modifiedObj: any = {
      "fraction": region_properties["Fraction:"] || "",
      "no_of_objects": region_properties["No of objects:"] || "",
      "avg_object_area": region_properties["Average object area (" + unit + "):"] || "",
      "min_object_area": region_properties["Min object area (" + unit + "):"] || "",
      "max_object_area": region_properties["Max object area (" + unit + "):"] || "",
      "avg_object_length": region_properties["Average object length (" + unit + "):"] || "",
      "min_object_length": region_properties["Min object length (" + unit + "):"] || "",
      "max_object_length": region_properties["Max object length (" + unit + "):"] || "",
      "avg_object_aspect_ratio": region_properties["Average object aspect ratio:"] || "",
      "min_object_aspect_ratio": region_properties["Min object aspect ratio:"] || "",
      "max_object_aspect_ratio": region_properties["Max object aspect ratio:"] || ""
    };

    return modifiedObj;
  }

  setRegionProps() {
    this.segmentedImageDetails['region_properties'] = {};
    let getLastSeg = this.getLastSegmentedImage('post-processing', '', '');
    if (
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] == true &&
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => val['selected'] == true).length > 0 &&
      getLastSeg['region_properties'] != undefined) {
      this.segmentedImageDetails['region_properties'] = getLastSeg['region_properties'];
    }
  }

  splitRegionProps(region_props: any) {
    var index = 0;
    var arrayLength = region_props.length;
    var tempArray = [];

    for (index = 0; index < arrayLength; index += 2) {
      let myChunk = region_props.slice(index, index + 2);
      tempArray.push(myChunk);
    }

    return tempArray;
  }

  showPrevImage(event: any) {
    this.showPreviewImage = event.checked;
  }

  getLatesPreviewImage() {
    if (this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'].length > 0
    ) {
      return this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][0]['result']['previewchanges_url'];
      // return this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][0]['result']['previewchanges'];
    } else if (this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'] != undefined &&
      this.getFeaturesCount('postprocessingWorkflowFeatures') > 0
    ) {
      let getPostData = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].filter((val: any) => val['selected'] == true)
      if (getPostData.length > 0) {
        const lastItem = getPostData[getPostData.length - 1];
        if (lastItem.result && lastItem.result.previewchanges_url) {
          return lastItem.result.previewchanges_url;
        } else {
          return '';
        }
      } else {
        return '';
      }
    } else if (this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'] != undefined &&
      this.getFeaturesCount('segmentationWorkflowFeatures') > 0
    ) {
      let getPostData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => val['selected'] == true)
      return getPostData[getPostData.length - 1]['result']['previewchanges_url'];

      // return getPostData[getPostData.length - 1]['result']['previewchanges'];
    }
  }

  changeNoOflayers(workflowType: string, index: number, value: any) {
    let param = this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['selected_layers'];
    if (param['local_state_0'].length > 0) {
      let getLastValOfState0 = param['local_state_0'][param['local_state_0'].length - 1];
      if (getLastValOfState0 > value - 1) {
        this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['selected_layers']['local_state_0'].splice((param['local_state_0'].length - 1), 1);
        this.changeNoOflayers(workflowType, index, value)
      }
    }
    if (param['local_state_1'].length > 0) {
      let getLastValOfState0 = param['local_state_1'][param['local_state_1'].length - 1];
      if (getLastValOfState0 > value - 1) {
        this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['selected_layers']['local_state_1'].splice((param['local_state_1'].length - 1), 1);
        this.changeNoOflayers(workflowType, index, value)
      }
    }
  }

  applyinnerLayerSettings() {
    this.apiCall = true;
    if (this.newLayerFor == 'pre-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] = true;
      this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'] = clone(this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].concat(this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures']));
    } else if (this.newLayerFor == 'segmentation') {
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] = true;
      if (this.templateMatchingId >= 0) {
        if (this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].length > 1) {
          this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].splice(this.templateMatchingId, 1);
        } else {
          this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'] = [];
        }
      }
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].map((val: any) => { val["selected"] = false });
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'] = clone(this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].concat(this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures']));
    } else if (this.newLayerFor == 'post-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] = true;
      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'] = clone(this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].concat(this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures']));
    }
    this.segmentedImageDetails['segmentedImage'] = this.previewImage;
    this.setRegionProps();
    this.dropDownLayer = this.getLatestLayerData();
    // this.setOriginalImageDropDown(true);
    if (this.newLayerFor == 'segmentation') {
      this.dropDownVisualization = this.getLatestVisualizationData();
    }
    this.setLatestLayerForBaseLayer();


    this.closeLayerSettings();
    this.segmentationUsingThresholding = false;
    this.saveWorkflowBtnEvent.emit(true);
    this.workflowChanged = true;
  }

  onEnterSliderInput(obj: any, ind: any, objkey: any, type: any, value: any) {
    value = +value.target.value;
    if (obj['slider'][objkey]['name'] == 'Subregion size (px)') {
      value = this.enterOddNumbersOnly(value, obj['slider'][objkey])
      obj['Params'][objkey] = value;
      this.slideWorkflow(value, ind, objkey, type);
    } else {
      obj['Params'][objkey] = +value;
      this.slideWorkflow(value, ind, objkey, type);
    }
  }

  enterOddNumbersOnly(value: number, slider: any): number {
    // const input = (event.target as HTMLInputElement);
    // let value = Number(value);

    // Check if the value is within range and odd
    if (value < slider.range.min) {
      value = slider.range.min;
    } else if (value > slider.range.max) {
      value = slider.range.max;
    }

    // Ensure the value is odd
    if (value % 2 === 0) {
      // value = (value < slider.range.max) ? value + 1 : value - 1;
      value = (value + 1 <= slider.range.max) ? value + 1 : value - 1;

    }

    // Update the input value if necessary
    return value;
  }


  onEnterTempSliderInput(obj: any, ind: any, objkey: any, type: any, value: any) {
    value = +value.target.value;
    if (obj['slider'][objkey]['name'] == 'Subregion size (px)') {
      value = this.enterOddNumbersOnly(value, obj['slider'][objkey])
    }
    obj['Params'][objkey] = +value;
    this.slideTempWorkflow(value, ind, objkey, type);
  }
  slideFilterWorkflow(event: any, ind: any, objkey: any, type: any) {
    let value = +event.target.value;
    this.slideWorkflow(value, ind, objkey, type)
  }
  slideWorkflow(event: any, ind: any, objkey: any, type: any) {
    this.currentLayerData['type'] = type;
    this.currentLayerData['layer'] = ind;
    this.currentLayerData['actionType'] = 'edit';
    this.currentLayerData['subActionType'] = 'slider';
    this.currentLayerData["changedObj"]['key'] = objkey;
    this.currentLayerData["changedObj"]['val'] = event;
    this.currentLayerData['inputImage'] = "";
    if (type == 'pre-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][ind]['Params'][objkey] = event;
      this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][ind]['slider'][objkey]['start'] = event;
    } else if (type == 'segmentation') {
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][ind]['Params'][objkey] = event;
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][ind]['slider'][objkey]['start'] = event;
      if (objkey == 'classes' || objkey == 'n_segments') {
        this.changeNoOflayers('segmentationWorkflowFeatures', ind, event);
      }
    } else if (type == 'post-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][ind]['Params'][objkey] = event;
      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][ind]['slider'][objkey]['start'] = event;
    }
    this.saveWorkflowBtnEvent.emit(true);
    this.dropDownLayer = this.getLatestLayerData();
    this.setOriginalImageDropDown(true);
    this.workflowChanged = true;
    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
  }

  slideTempFilterWorkflow(event: any, ind: any, objkey: any, type: any) {
    let value = +event.target.value;
    this.slideTempWorkflow(value, ind, objkey, type)
  }

  slideTempWorkflow(event: any, ind: any, objkey: any, type: any) {
    this.currentLayerData['type'] = type;
    this.currentLayerData['layer'] = "";
    this.currentLayerData['actionType'] = 'add';
    this.currentLayerData['subActionType'] = 'slider';
    this.currentLayerData["changedObj"]['key'] = objkey;
    this.currentLayerData["changedObj"]['val'] = event;
    this.currentLayerData['inputImage'] = "";
    if (type == 'pre-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][ind]['Params'][objkey] = event;
      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][ind]['slider'][objkey]['start'] = event;
    } else if (type == 'segmentation') {
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][ind]['Params'][objkey] = event;
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][ind]['slider'][objkey]['start'] = event;
      if (objkey == 'classes' || objkey == 'n_segments') {
        this.changeNoOflayers('tempSegmentationWorkflowFeatures', ind, event);
      }
      delete this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][ind]['result'];
    } else if (type == 'post-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][ind]['Params'][objkey] = event;
      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][ind]['slider'][objkey]['start'] = event;

      delete this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][ind]['result'];
    }
    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
  }

  getLocalStates(inpClass: any) {
    let returnState = [];
    for (let i = 0; i < inpClass; i++) {
      returnState.push(i);
    }
    return returnState;
  }
  getValue(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }


  onEditBinarization(layIndex: number, objKey: any) {
    this.binarization = clone(this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][layIndex]['Params'][objKey]);
    this.editBinarization = true;
  }

  onEditTempBinarization(layIndex: number, objKey: any) {
    this.tempBinarization = clone(this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params'][objKey]);
    this.editTempBinarization = true;
  }

  binarySelection($event: any, layIndex: any, state_type: any) {
    let oppStateType = (state_type == 'local_state_0') ? 'local_state_1' : 'local_state_0';
    let binaryVal = $event.source.value;
    let workFlowFeat = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'];
    let valExist = workFlowFeat[state_type].findIndex((val: any) => val == binaryVal);
    let oppStateExist = workFlowFeat[oppStateType].findIndex((val: any) => val == binaryVal);
    if ($event.checked) {
      if (valExist == -1 || valExist < 0) {
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][state_type].push(binaryVal);
        if (oppStateExist >= 0) {
          this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][oppStateType].splice(oppStateExist, 1);
        }
      }
    } else {
      if (valExist >= 0) {
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][state_type].splice(valExist, 1);
        if (oppStateExist == -1 || oppStateExist < 0) {
          this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][oppStateType].push(binaryVal);
        }
      }
    }
    this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][state_type] = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][state_type].sort();
    this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][oppStateType] = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][oppStateType].sort();
  }

  tempBinarySelection($event: any, layIndex: any, state_type: any) {
    let oppStateType = (state_type == 'local_state_0') ? 'local_state_1' : 'local_state_0';
    let binaryVal = $event.source.value;
    let workFlowFeat = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'];
    let valExist = workFlowFeat[state_type].findIndex((val: any) => val == binaryVal);
    let oppStateExist = workFlowFeat[oppStateType].findIndex((val: any) => val == binaryVal);
    if ($event.checked) {
      if (valExist == -1 || valExist < 0) {
        this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][state_type].push(binaryVal);
        if (oppStateExist >= 0) {
          this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][oppStateType].splice(oppStateExist, 1);
        }
      }
    } else {
      if (valExist >= 0) {
        this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][state_type].splice(valExist, 1);
        if (oppStateExist == -1 || oppStateExist < 0) {
          this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][oppStateType].push(binaryVal);
        }
      }
    }
    this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][state_type] = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][state_type].sort();
    this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][oppStateType] = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params']['selected_layers'][oppStateType].sort();
  }

  applyBinarization(layIndex: any, objkey: any, type: any) {
    this.editBinarization = false;
    this.currentLayerData['type'] = type;
    this.currentLayerData['layer'] = layIndex;
    this.currentLayerData['actionType'] = 'edit';
    this.currentLayerData['subActionType'] = 'local_state';
    this.currentLayerData["changedObj"]['key'] = objkey;
    this.currentLayerData["changedObj"]['val'] = '';
    this.currentLayerData['inputImage'] = "";
    this.dropDownVisualization = this.getLatestVisualizationData();
    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
  }

  applyTempBinarization(_layIndex: any, objkey: any, type: any) {
    this.editTempBinarization = false;
    this.currentLayerData['type'] = type;
    this.currentLayerData['layer'] = "";
    this.currentLayerData['actionType'] = 'add';
    this.currentLayerData['subActionType'] = 'local_state';
    this.currentLayerData["changedObj"]['key'] = objkey;
    this.currentLayerData["changedObj"]['val'] = '';
    this.currentLayerData['inputImage'] = "";
    this.dropDownVisualization = this.getLatestVisualizationData();
    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
  }

  changeVisualization(event: any) {
    let val = event.value;
    if (val != "") {
      let split_val = val.split(',');
      this.dropDownVisualization = { "type": split_val[0], "val": split_val[1], "disVal": split_val[2], "mainVal": val };
      let ind = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].findIndex((val: any) => val['selected'] == true);
      if (ind != undefined && ind >= 0) {
        let visualization_val = "";
        let colorVal = "";
        if (this.dropDownVisualization['type'] == 'solid') {
          visualization_val = this.dropDownVisualization['val'];
        } else if (this.dropDownVisualization['type'] == 'outline_segmented') {
          visualization_val = this.dropDownVisualization['type'];
          colorVal = this.dropDownVisualization['val'];
        } else {
          if (this.dropDownVisualization['val'] == 'label segmented') {
            visualization_val = this.dropDownVisualization['val'];
          } else {
            visualization_val = this.dropDownVisualization['type'];
            colorVal = this.dropDownVisualization['val'];
          }
        }
        this.currentLayerData['type'] = 'segmentation';
        this.currentLayerData['layer'] = ind;
        this.currentLayerData['actionType'] = 'edit';
        this.currentLayerData['subActionType'] = 'dropdown';
        this.currentLayerData["changedObj"]['key'] = 'visualization';
        this.currentLayerData["changedObj"]['val'] = visualization_val;
        this.currentLayerData['inputImage'] = "";
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][ind]['Params']['visualization'] = visualization_val;
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][ind]['Params']['color'] = colorVal;
        let checkVAndC = this.checkSegmenVisualizationAndColor('segmentationWorkflowFeatures', ind);
        if (!checkVAndC) {
          return false;
        }
        this.dropDownLayer = this.getLatestLayerData();
        this.setOriginalImageDropDown(true);
        this.saveWorkflowBtn = true;
        this.workflowChanged = true;
        this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
      }
    } else {
      this.dropDownVisualization = { "type": 'solid', "val": 'Black/white (default)', "disVal": 'Black/white (default)', "mainVal": 'solid,Black/white (default),Black/white (default)' };
    }
    return true;
  }

  checkSegmenVisualizationAndColor(workflowType: any, index: any) {
    let selected_layers = this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['selected_layers'];
    let visualization = this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['visualization'];

    this.currentLayerData['inputImage'] = "";
    if (this.currentLayerData["changedObj"]['key'] == 'selected_layers' || this.currentLayerData["changedObj"]['key'] == 'visualization' || this.currentLayerData["changedObj"]['key'] == 'color') {
      if (this.currentLayerData["changedObj"]['key'] == 'selected_layers') {
        if (selected_layers.length > 0) {
          this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['visualization'] = "outline_segmented";
        } else {
          this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['visualization'] = "";
        }
        visualization = this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['visualization'];
      }
      if (visualization == 'outline_segmented' || visualization == 'overlay_segmented' || visualization == 'label segmented') {
        // this.currentLayerData['inputImage'] = this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['result']['black&white'];
      }
    }

    // if(visualization=='Black/white (default)'){
    //   this.segmentedImageDetails['segmentedImage'] = this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['result']['black&white'];
    //   return false;
    // }
    return true;
  }

  checkAllLayers(type: any, event: any) {
    let ApiCallNeeded = true;
    if (type == 'pre-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] = event.checked;
      if (event.checked) {
        let selectedPreprocessingFeatures = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].filter((val: any, index: number) => (val['selected'] == true))
        if (selectedPreprocessingFeatures.length == 0) {
          let selectedPreprocessingFeatures = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].filter((val: any, index: number) => (val['selected'] == true))
          if (selectedPreprocessingFeatures.length == 0) {
            type = 'scratch'
            ApiCallNeeded = false;
          }
        }
      }
    } else if (type == 'segmentation') {
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] = event.checked;
      if (event.checked) {
        let selectedSegmentationFeatures = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any, index: number) => (val['selected'] == true))
        if (selectedSegmentationFeatures.length == 0) {
          type = 'pre-processing'
          let selectedPreprocessingFeatures = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].filter((val: any, index: number) => (val['selected'] == true))
          if (selectedPreprocessingFeatures.length == 0) {
            type = 'scratch'
            ApiCallNeeded = false;
          }
        }
      }
    } else if (type == 'post-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] = event.checked;
      if (event.checked) {
        let selectedPostProcessingFeatures = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].filter((val: any, index: number) => (val['selected'] == true))
        if (selectedPostProcessingFeatures.length == 0) {
          type = 'segmentation'
        }
      }
    }

    this.currentLayerData['type'] = type;
    this.currentLayerData['layer'] = 0;
    this.currentLayerData['actionType'] = 'edit';
    this.currentLayerData['subActionType'] = 'checkbox';
    this.currentLayerData["changedObj"] = {};
    this.currentLayerData['inputImage'] = "";

    this.saveWorkflowBtn = true;
    this.workflowChanged = true;

    this.segmentedLoading = false;
    this.originalLoading = false;

    if (!event.checked || !ApiCallNeeded) {
      this.apiCall = false;
      this.segmentedLoading = true;
      this.originalLoading = true;

      this.dropDownLayer = this.getLatestLayerData();
      this.setOriginalImageDropDown(false);
      this.setRegionProps();

      setTimeout(() => {
        this.setLastSegmentedImageOnuncheck();
        this.setLatestLayerForBaseLayer()
      }, 1);
    }

    this.apiCall = true;
    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
  }

  setLastSegmentedImageOnuncheck() {
    let split_val = this.dropDownLayer.mainVal.split('_')
    let returnurl = '';
    if (split_val[0] == 'pre-processing') {
      returnurl = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][+split_val[1]]['result']['filtered_image'];
    } else if (split_val[0] == 'segmentation') {
      if (this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][split_val[1]]['Params']['visualization'] == 'Black/white (default)') {
        returnurl = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][+split_val[1]]['result']['black&white'];
      } else {
        returnurl = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][+split_val[1]]['result']['filtered_image'];
      }
    } else if (split_val[0] == 'post-processing') {

      let segmentationData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
      if (segmentationData[0]['Params']['visualization'] == 'Black/white (default)') {
        returnurl = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][+split_val[1]]['result']['black&white'];
      } else {
        returnurl = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][+split_val[1]]['result']['filtered_image'];
      }
    }
    if (returnurl != '') {
      this.apiCall = true;
      this.segmentedImageDetails.segmentedimage = returnurl;
      this.getImageContent(this.segmentedImageDetails, 'segmentedImage')
    }
  }

  layerSelection(event: any, ind: any, type: any) {
    this.currentLayerData['type'] = type;
    this.currentLayerData['layer'] = ind;
    this.currentLayerData['actionType'] = 'edit';
    this.currentLayerData['subActionType'] = 'checkbox';
    this.currentLayerData["changedObj"] = {};
    this.currentLayerData['inputImage'] = "";
    if (type == 'pre-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][ind]['selected'] = event.checked;
      let prepF = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].filter((feature: any) => feature.selected == true);
      if (prepF.length == 0) {
        this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected'] = false;
      }
    } else if (type == 'segmentation') {
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].map((val: any) => { val["selected"] = false });
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][ind]['selected'] = event.checked;

      let segF = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((feature: any) => feature.selected == true);
      if (segF.length == 0) {
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] = false;
      }
    } else if (type == 'post-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][ind]['selected'] = event.checked;

      let posF = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].filter((feature: any) => feature.selected == true);
      if (posF.length == 0) {
        this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] = false;
      }
    }
    this.segmentedLoading = false;
    this.originalLoading = false;

    this.dropDownLayer = this.getLatestLayerData();

    // this.setOriginalImageDropDown(true);
    // if (type == 'segmentation') {
    //   this.dropDownVisualization = this.getLatestVisualizationData();
    // }
    // this.setRegionProps();
    this.saveWorkflowBtn = true;
    this.workflowChanged = true;

    if (!event.checked) {
      this.setLastSegmentedImageOnuncheck()
      this.setLatestLayerForBaseLayer();
    }

    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
  }

  changeWorkflowOnDropDown(event: any, ind: number, objkey: string, type: string) {
    this.currentLayerData['type'] = type;
    this.currentLayerData['layer'] = ind;
    this.currentLayerData['actionType'] = 'edit';
    this.currentLayerData['subActionType'] = 'dropdown';
    this.currentLayerData["changedObj"]['key'] = objkey;
    this.currentLayerData["changedObj"]['val'] = event.value;
    this.currentLayerData['inputImage'] = "";
    if (type == 'segmentation') {
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][ind]['Params'][objkey] = event.value;
      this.dropDownVisualization = this.getLatestVisualizationData();
      let checkVAndC = this.checkSegmenVisualizationAndColor('segmentationWorkflowFeatures', ind);
      if (!checkVAndC) {
        return false;
      }
    }
    if (type == "post-processing") {
      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][ind]['Params'][objkey] = event.value;
      this.changeElementShape('postprocessingWorkflowFeatures', ind);
      this.dropDownLayer = this.getLatestLayerData();
      this.setOriginalImageDropDown(true);
    }
    this.saveWorkflowBtnEvent.emit(true);
    this.workflowChanged = true;
    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
    return true;
  }

  changeTempWorkflowOnDropDown(event: any, ind: number, objkey: string, type: string) {
    this.currentLayerData['type'] = type;
    this.currentLayerData['layer'] = "";
    this.currentLayerData['actionType'] = 'add';
    this.currentLayerData['subActionType'] = 'dropdown';
    this.currentLayerData["changedObj"]['key'] = objkey;
    this.currentLayerData["changedObj"]['val'] = event.value;
    this.currentLayerData['inputImage'] = "";
    if (type == 'segmentation') {
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][ind]['Params'][objkey] = event.value;
      this.dropDownVisualization = this.getLatestVisualizationData();
      let checkVAndC = this.checkSegmenVisualizationAndColor('tempSegmentationWorkflowFeatures', ind);
      if (!checkVAndC) {
        return false;
      }
      delete this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][ind]['result'];
    }
    if (type == "post-processing") {
      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][ind]['Params'][objkey] = event.value;
      this.changeElementShape('tempPostprocessingWorkflowFeatures', ind);

      delete this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'][ind]['result'];
    }
    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);

    return true;
  }

  changeElementShape(workflowType: any, index: any) {
    let element = this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['structure_element'];
    if (element == 'rectangle') {
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['width'] = 3;
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['slider']['width']['start'] = 3;
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['height'] = 10;
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['slider']['height']['start'] = 10;
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['radius'] = "";
    } else if (element == 'square') {
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['width'] = "";
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['height'] = 10;
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['slider']['height']['start'] = 10;
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['radius'] = "";
    } else if (element == 'disk') {
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['width'] = "";
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['height'] = "";
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['Params']['radius'] = 5;
      this.segmentedImageDetails['selectedSegmentedImage'][workflowType][index]['slider']['radius']['start'] = 5;
    }
  }

  checkAnalysisExists() {
    if (
      this.segmentedImageDetails['selectedSegmentedImage']['pillar-pattern-analysis']['data'].length > 0 ||
      this.segmentedImageDetails['selectedSegmentedImage']['feature-profile-analysis']['data'].length > 0 ||
      this.segmentedImageDetails['selectedSegmentedImage']['tier-analysis']['data'].length > 0 ||
      this.segmentedImageDetails['selectedSegmentedImage']['metal-recess-analysis']['data'].length > 0 ||
      this.segmentedImageDetails['selectedSegmentedImage']['bubble-analysis']['data'].length > 0 ||
      this.segmentedImageDetails['selectedSegmentedImage']['pillar-anomaly-analysis']['data'].length > 0 ||
      this.segmentedImageDetails['selectedSegmentedImage']['pillar-c2c-analysis']['data'].length > 0 ||
      this.segmentedImageDetails['selectedSegmentedImage']['metal-voids-analysis']['data'].length > 0
    ) {
      this.isAnalysisExists = true;
    } else {
      this.isAnalysisExists = false;
    }
  }

  assignWorkflowFeatures(workflowData: any) {
    this.segmentedImageDetails['selectedSegmentedImage']["preprocessingWorkflowSelected"] = clone(workflowData['workflow']['preprocessingWorkflowSelected']);
    this.segmentedImageDetails['selectedSegmentedImage']["preprocessingWorkflowFeatures"] = clone(workflowData['workflow']['preprocessingWorkflowFeatures']);
    this.segmentedImageDetails['selectedSegmentedImage']["preprocessingWorkflowFeatures"].forEach((element: any, ind: number) => {
      this.segmentedImageDetails['selectedSegmentedImage']["preprocessingWorkflowFeatures"][ind] = this.changeFeatureDynamicValues(element);
    });

    this.segmentedImageDetails['selectedSegmentedImage']["segmentationWorkflowSelected"] = clone(workflowData['workflow']['segmentationWorkflowSelected']);
    this.segmentedImageDetails['selectedSegmentedImage']["segmentationWorkflowFeatures"] = clone(workflowData['workflow']['segmentationWorkflowFeatures']);
    this.segmentedImageDetails['selectedSegmentedImage']["segmentationWorkflowFeatures"].forEach((element: any, ind: number) => {
      this.segmentedImageDetails['selectedSegmentedImage']["segmentationWorkflowFeatures"][ind] = this.changeFeatureDynamicValues(element);
    });

    this.segmentedImageDetails['selectedSegmentedImage']["postprocessingWorkflowSelected"] = clone(workflowData['workflow']['postprocessingWorkflowSelected']);
    this.segmentedImageDetails['selectedSegmentedImage']["postprocessingWorkflowFeatures"] = clone(workflowData['workflow']['postprocessingWorkflowFeatures']);
    this.segmentedImageDetails['selectedSegmentedImage']["postprocessingWorkflowFeatures"].forEach((element: any, ind: number) => {
      this.segmentedImageDetails['selectedSegmentedImage']["postprocessingWorkflowFeatures"][ind] = this.changeFeatureDynamicValues(element);
    });
    this.dropDownLayer = this.getLatestLayerData();
    this.setOriginalImageDropDown(true);
    this.dropDownVisualization = this.getLatestVisualizationData();
    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
  }

  carryForwardOptions(workflowData: any) {
    if (workflowData['carrycrop'] != undefined) {
      this.carryForwardCrop = workflowData['carrycrop'];
    } else {
      this.carryForwardCrop = false;
    }
    if (workflowData['carryanalysis'] != undefined) {
      this.carryForwardAnalysis = workflowData['carryanalysis'];
    } else {
      this.carryForwardAnalysis = false;
    }
    if (workflowData['carryscalebar'] != undefined) {
      this.carryForwardScalebar = workflowData['carryscalebar'];
    } else {
      this.carryForwardScalebar = false;
    }
  }

  changeFeatureDynamicValues(featuresdata: any) {
    if (featuresdata['fid'] == 9) {
      let minVal = Math.min(...this.segmentedImageDetails['selectedSegmentedImage']['shape']);
      featuresdata["slider"]["kernel_size"]["range"]["max"] = minVal;
      let stepSize = featuresdata["slider"]["kernel_size"]['step'];
      let k_size = stepSize * Math.floor(minVal / 8 / stepSize);
      featuresdata["Params"]["kernel_size"] = k_size;
      featuresdata["slider"]["kernel_size"]["start"] = k_size;
    }
    if (featuresdata['fid'] == 12) {
      let minVal = Math.min(...this.segmentedImageDetails['selectedSegmentedImage']['shape']);
      featuresdata["slider"]["block_size"]["range"]["max"] = (this.checkOddInteger(minVal)) ? minVal : minVal - 1;
    }
    return featuresdata;
  }

  getLatestLayerData() {
    let returnData = clone(this.dropDownLayersDefaultValues);
    returnData = this.getlastWorlflowFeature('postprocessingWorkflow', 'post-processing', returnData);
    if (returnData['mainVal'] != "") {
      let subreturnData = clone(this.dropDownLayersDefaultValues);
      subreturnData = this.getlastWorlflowFeature('segmentationWorkflow', 'segmentation', subreturnData);
      if (subreturnData['mainVal'] != "") {
        return returnData;
      } else {
        returnData = clone(this.dropDownLayersDefaultValues);
        returnData = this.getlastWorlflowFeature('preprocessingWorkflow', 'pre-processing', returnData);
        return returnData;
      }
    } else {
      returnData = this.getlastWorlflowFeature('segmentationWorkflow', 'segmentation', returnData);
      if (returnData['mainVal'] != "") {
        return returnData;
      } else {
        returnData = this.getlastWorlflowFeature('preprocessingWorkflow', 'pre-processing', returnData);
        if (returnData['mainVal'] != "") {
          return returnData;
        } else {
          if (this.selectedMask) {
            return { "type": "masked", "mainVal": "masked", "val": "masked" }
          } else {
            return { "type": "original", "mainVal": "original", "val": "original" }
          }
        }
      }
    }
  }

  getlastWorlflowFeature(feature: string, type: string, returnData: any) {
    let workflowSelected = this.segmentedImageDetails['selectedSegmentedImage'][feature + 'Selected'];
    let workflow = this.segmentedImageDetails['selectedSegmentedImage'][feature + 'Features'];
    if (workflowSelected != undefined && workflowSelected == true && workflow != undefined && workflow.length > 0) {
      for (let i = workflow.length - 1; i >= 0; i--) {
        if (workflow[i]['selected'] == true) {
          returnData['type'] = type;
          returnData['mainVal'] = type + '_' + i;
          returnData['val'] = (i + 1).toString();
          break;
        }
      }
    }
    return returnData;
  }

  setOriginalImageDropDown(checkOriginalImage: boolean) {
    if (checkOriginalImage) {
      this.originalImagedropDownLayer = clone(this.dropDownLayersDefaultValues);
      // this.segmentedImageDetails['displayInputImage'] = this.segmentedImageDetails['inputImageForSegmentation'];
      // this.getImageContent(this.segmentedImageDetails, 'displayInputImage')
    } else {
      if (this.originalImagedropDownLayer['mainVal'] != "") {
        if (this.originalImagedropDownLayer['type'] != this.dropDownLayer['type']) {
          let filterTypeArray = ['pre-processing', 'segmentation', 'post-processing'];
          let originalImageIndex = filterTypeArray.findIndex(val => val == this.originalImagedropDownLayer['type']);
          let segmentedImageIndex = filterTypeArray.findIndex(val => val == this.dropDownLayer['type']);
          if (originalImageIndex > segmentedImageIndex) {
            this.setOriginalImageDropDown(true);
          }
        } else {
          let originalVal = +this.originalImagedropDownLayer['val'] - 1;
          let segmentedVal = +this.dropDownLayer['val'] - 1;
          if (originalVal >= segmentedVal) {
            this.setOriginalImageDropDown(true);
          }
        }
      }
    }
  }

  getLatestVisualizationData() {
    let returnData: any = { "type": 'solid', "val": 'Black/white (default)', "disVal": 'Black/white (default)', "mainVal": 'solid,Black/white (default),Black/white (default)' };

    returnData = this.getActiveSegmentationWorlflowFeature('segmentationWorkflowFeatures', returnData);
    if (returnData['mainVal'] != "") {
      return returnData;
    }
  }

  getVisualiztionAnalysisOptions() {
    let type = this.dropDownLayer['type'];
    let split_val = this.dropDownLayer['mainVal'].split('_');
    let analysisData = this.segmentedImageDetails['selectedSegmentedImage'][type]['data'][split_val[1]];
    return analysisData;
  }

  getLatestAnalysisVisualizationData() {
    let val = this.dropDownLayer['type'] + '_0';
    let split_val = val.split('_');
    return { "type": split_val[0], "mainVal": val, "val": split_val[1] };
  }

  changeAnalysisVisualization(event: any) {
    let val = event.value;
    let opImage = "";
    if (val != "") {
      let split_val = val.split('_');
      let layerInfo = { "type": split_val[0], "mainVal": val, "val": split_val[1] };
      this.dropDownAnalysisVisualization = layerInfo;
      let dropDownLayerIndex = this.dropDownLayer['val'] - 1;
      let indexVal = parseInt(split_val[1]);
      if (indexVal > 0) {
        indexVal = indexVal - 1;
        let analysisData = this.segmentedImageDetails['selectedSegmentedImage'][split_val[0]]['data'][dropDownLayerIndex]['otherannotated'][indexVal];
        opImage = analysisData[this.returnKeysFromObject(analysisData)[0]];
      } else {
        opImage = this.segmentedImageDetails['selectedSegmentedImage'][split_val[0]]['data'][dropDownLayerIndex]['annotate_img'];
      }
      this.segmentedImageDetails['segmentedImage'] = opImage;
    }
  }
  changeOriginalLayerView: boolean = false;
  changeFilterLayerView: boolean = false;

  getImageContentSpecialCase(obj: any, key: string, type: string) {
    let path = obj[key];
    if (path && path != '') {
      if (type == 'left') {
        this.changeOriginalLayerView = true;
      } else {
        this.changeFilterLayerView = true;
      }
      this.imageAnalysisService
        .getIndividualImageContent({ path: path, name: this.getImageName(path) })
        .subscribe(
          (result) => {
            this.apiCall = false
            if (key == 'previewImage') {
              this.previewImage_url = result;
            } else {
              let newPathKey = key + '_url'
              obj[newPathKey] = '';
              obj[newPathKey] = result;
              if (type == 'left') {
                this.changeOriginalLayerView = false;
              } else {
                this.changeFilterLayerView = false;
              }
            }
          },
          (error) => {
            this.apiCall = false
            console.error('Error fetching image content:', error);
          },
        );
    }
  }

  changeLayerView(event: any, dropdown_type: any) {
    let val = event;
    let opImage = "";
    let region_properties = {};
    if (val != "" && val != 'masked_image') {
      let layerInfo: any = {};
      let split_val: any = []
      if (val == 'masked' || val == 'original') {
        layerInfo = { "type": val, "mainVal": val, "val": val };
      } else {
        split_val = val.split('_');
        layerInfo = { "type": split_val[0], "mainVal": val, "val": parseInt(split_val[1]) + 1 };
      }
      if (dropdown_type == 'original_image') {
        this.originalImagedropDownLayer = layerInfo;
      } else {
        this.selectedSegmentedValue = val;
        this.dropDownLayer = layerInfo;
      }
      if (val != 'masked' && val != 'original') {
        if (split_val[0] == 'pre-processing') {
          opImage = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][+split_val[1]]['result']['filtered_image'];
        } else if (split_val[0] == 'segmentation') {
          let segmentationData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
          if (this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][split_val[1]]['Params']['visualization'] == 'Black/white (default)') {
            opImage = segmentationData[0]['result']['black&white'];
          } else {
            opImage = segmentationData[0]['result']['filtered_image'];
          }
          region_properties = segmentationData[0]['result']['region_properties'];
        } else if (split_val[0] == 'post-processing') {
          let segmentationData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
          if (segmentationData[0]['Params']['visualization'] == 'Black/white (default)') {
            opImage = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][+split_val[1]]['result']['black&white'];
          } else {
            opImage = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][+split_val[1]]['result']['filtered_image'];
          }
          region_properties = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][+split_val[1]]['result']['region_properties'];
        }
      } else {
        if (val == 'masked') {
          opImage = this.segmentedImageDetails['selectedSegmentedImage']['masked_image'];
          this.originalImagedropDownLayer = { "type": "", "mainVal": "", "val": "" };
          let manualImage = this.segmentedImageDetails['selectedSegmentedImage']['manual_image']
          this.segmentedImageDetails['displayInputImage'] = manualImage;
          this.getImageContentSpecialCase(this.segmentedImageDetails, 'displayInputImage', 'left')
        } else if (val == 'original') {
          opImage = this.segmentedImageDetails['selectedSegmentedImage']['manual_image'];
        }
      }

    } else {
      if (dropdown_type == 'original_image') {
        if (val == 'masked_image') {
          this.originalImagedropDownLayer = { "type": "masked_image", "mainVal": "masked_image", "val": "masked_image" };
          opImage = this.segmentedImageDetails['selectedSegmentedImage']['masked_image'];

        } else {
          this.originalImagedropDownLayer = { "type": "", "mainVal": "", "val": "" };
          opImage = this.segmentedImageDetails!['selectedSegmentedImage']['manual_image']
        }
      } else {
        // this.dropDownLayer = {};
        let getLastseg = this.getLastSegmentedImage('post-processing', false, "");
        opImage = getLastseg['filtered_image'];
        region_properties = getLastseg['region_properties'];
      }
    }

    if (dropdown_type == 'original_image') {
      this.segmentedImageDetails['displayInputImage'] = opImage;
      this.getImageContentSpecialCase(this.segmentedImageDetails, 'displayInputImage', 'left')
    } else {
      this.selectedSegmentedValue = val;
      this.segmentedImageDetails['segmentedImage'] = opImage;
      // this.getImageContent(this.segmentedImageDetails, 'segmentedImage')
      this.getImageContentSpecialCase(this.segmentedImageDetails, 'segmentedImage', 'right')
      this.segmentedImageDetails['region_properties'] = region_properties;
      this.setOriginalImageDropDown(true);
      this.setLatestLayerForBaseLayer()
    }
  }

  getImageName(filePath: string): string {
    if (filePath) {
      const parts = filePath.split('/');
      return parts.pop() || ''; // Returns the last part or an empty string if the path is empty
    } else {
      return 'viewimage';
    }
  }

  getActiveSegmentationWorlflowFeature(feature: any, returnData: any) {
    let workflow = this.segmentedImageDetails['selectedSegmentedImage'][feature].filter((val: any) => val['selected'] == true);
    if (workflow != undefined && workflow.length > 0) {
      workflow = workflow[0];
      returnData['val'] = workflow['Params']['visualization'];
      if (workflow['Params']['visualization'] == 'Black/white (default)' || workflow['Params']['visualization'] == '') {
        returnData['type'] = 'solid';
        if (workflow['Params']['visualization'] == 'Black/white (default)') {
          returnData['disVal'] = 'Black/white (default)';
        } else {
          returnData['disVal'] = 'Blue & Yellow';
        }
      } else if (workflow['Params']['visualization'] == 'outline_segmented') {
        returnData['type'] = 'outline_segmented';
        if (workflow['Params']['color'] != "") {
          if (workflow['Params']['color'] == 'magenta') {
            returnData['disVal'] = 'Magenta';
            returnData['val'] = 'magenta';
          } else if (workflow['Params']['color'] == 'red') {
            returnData['disVal'] = 'Red';
            returnData['val'] = 'red';
          } else {
            returnData['disVal'] = 'Yellow';
            returnData['val'] = 'yellow';
          }
        } else {
          returnData['disVal'] = 'Magenta';
          returnData['val'] = 'magenta';
        }
      } else if (workflow['Params']['visualization'] == 'label segmented' || workflow['Params']['visualization'] == 'overlay_segmented') {
        returnData['type'] = 'overlay_segmented';
        if (workflow['Params']['visualization'] == 'label segmented') {
          returnData['disVal'] = 'Label segmented';
        } else {
          if (workflow['Params']['color'] != "") {
            if (workflow['Params']['color'] == 'magenta') {
              returnData['disVal'] = 'Magenta';
              returnData['val'] = 'magenta';
            } else if (workflow['Params']['color'] == 'red') {
              returnData['disVal'] = 'Red';
              returnData['val'] = 'red';
            } else {
              returnData['disVal'] = 'Yellow';
              returnData['val'] = 'yellow';
            }
          } else {
            returnData['disVal'] = 'Magenta';
            returnData['val'] = 'magenta';
          }
        }
      }
      returnData['mainVal'] = returnData['type'] + ',' + returnData['val'] + ',' + returnData['disVal'];
    }
    return returnData;
  }

  selectSegmentationUsingThresholding() {
    this.segmentationUsingThresholding = true;
    this.newInnerLayer = false;
  }

  closeSegmentationThreshold() {
    this.segmentationUsingThresholding = false;
  }

  resetToDefaultGuasian(index: any, object: any) {
    object["Params"]["sigma"] = object['default_value'];
    object["slider"]["sigma"]["start"] = object['default_value'];
    if (this.currentLayerData["actionType"] == "add") {
      this.currentLayerData['type'] = "pre-processing";
      this.currentLayerData['layer'] = index;
      this.currentLayerData['actionType'] = 'add';
      this.currentLayerData['subActionType'] = 'slider';
      this.currentLayerData["changedObj"]['key'] = "sigma";
      this.currentLayerData["changedObj"]['val'] = object['default_value'];
      this.currentLayerData['inputImage'] = "";
      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][index]['Params']["sigma"] = object['default_value'];
      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'][index]['slider']["sigma"]['start'] = object['default_value'];
    } else {
      this.currentLayerData['type'] = "pre-processing";
      this.currentLayerData['layer'] = index;
      this.currentLayerData['actionType'] = 'edit';
      this.currentLayerData['subActionType'] = 'slider';
      this.currentLayerData["changedObj"]['key'] = "sigma";
      this.currentLayerData["changedObj"]['val'] = object['default_value'];
      this.currentLayerData['inputImage'] = "";
      this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][index]['Params']["sigma"] = object['default_value'];
      this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][index]['slider']["sigma"]['start'] = object['default_value'];
    }
    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
  }

  selectManualThreshold(feature: any) {
    var tempSegments = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'];
    var featuresdata: any = {};
    if (feature.fid == 11) {
      var index = tempSegments.findIndex((val: any) => val['fid'] == 11);
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'].splice(index, 1);
      featuresdata = JSON.parse(JSON.stringify(this.features["13"]));
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'].push(featuresdata);
      featuresdata["manual"] = true;
    } else {
      var index = tempSegments.findIndex((val: any) => val['fid'] == 13);
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'].splice(index, 1);
      featuresdata = JSON.parse(JSON.stringify(this.features["11"]));
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'].push(featuresdata);
      featuresdata["manual"] = false;
    }
    this.newInnerLayerDetails = featuresdata;
    featuresdata = this.changeFeatureDynamicValues(featuresdata);
    this.dropDownLayer = this.getLatestLayerData();
    this.setLastSegmentedImage();
    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
  }

  checkFidExists() {
    if (this.newInnerLayerDetails.hasOwnProperty("fid")) {
      return true;
    } else {
      return false;
    }
  }

  checkFidIsValid(fid: any) {
    let layerType = "";
    if (this.preprocessingLayers['total'].includes(fid)) {
      layerType = 'pre-processing';
    } else if (this.segmentationLayers['total'].includes(fid)) {
      layerType = 'segmentation';
    } else if (this.postprocessingLayers['total'].includes(fid)) {
      layerType = 'post-processing';
    }
    if (layerType == 'pre-processing') {
      if (this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].length > 0 && !this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected']) {
        return false;
      }
    } else if (layerType == 'segmentation') {
      if (this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].length > 0 && !this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected']) {
        return false;
      }
      // if(fid==13){
      //   return false;
      // }
    } else if (layerType == 'post-processing') {
      if (this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].length > 0 && !this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected']) {
        return false;
      }
      let segmentationWorkflow = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => val['selected'] == true);
      if (segmentationWorkflow == undefined || segmentationWorkflow.length <= 0 || !this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected']) {
        return false;
      }
    }
    return true;
  }

  searchFilters(searchStr: any) {
    this.searchFiltersList = [];
    searchStr = searchStr.target.value.trim().toLowerCase();
    if (searchStr != "") {
      this.showSearchFilters = true;
      if (searchStr.length >= 3) {
        Object.values(this.features).forEach((val: any, _index: number) => {
          if (val['Name'].toLowerCase().includes(searchStr) || val['info'].toLowerCase().includes(searchStr)) {
            if (this.checkFidIsValid(val['fid'])) {
              this.searchFiltersList.push((val['fid'] == 13) ? 11 : val['fid']);
            }
          }
        });
        this.searchKeywords.forEach((val: any, _index: number) => {
          if (val['word'].includes(searchStr)) {
            val['fids'].forEach((innerval: any) => {
              if (this.checkFidIsValid(innerval)) {
                this.searchFiltersList.push(innerval);
              }
            });
          }
        });
      }
      if (this.searchFiltersList.length > 0) {
        this.searchFiltersList = this.searchFiltersList.filter((val: any, index: number) => {
          return this.searchFiltersList.indexOf(val) === index;
        });
        this.searchFiltersList = this.searchFiltersList.sort();
      }
    } else {
      this.showSearchFilters = false;
    }
  }

  checkFiltersInSearch(checkArray: any) {
    return checkArray.filter((item: any) => this.searchFiltersList.indexOf(item) >= 0).length;
  }

  showMsg(type: string) {
    if (type == 'pre-processing') {
      this.toastr.error('Please enable Pre-processing.', '', {
        positionClass: 'custom-toast-position',
      });
    } else if (type == 'segmentation') {
      this.toastr.error('Please enable Segmentation.', '', {
        positionClass: 'custom-toast-position',
      });
    } else if (type == 'post-processing') {
      this.toastr.error('Please enable Post-processing.', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }

  backupLayers() {
    this.backupWorkflow["preprocessingWorkflowFeatures"] = clone(this.segmentedImageDetails['selectedSegmentedImage']["preprocessingWorkflowFeatures"]);
    this.backupWorkflow["segmentationWorkflowFeatures"] = clone(this.segmentedImageDetails['selectedSegmentedImage']["segmentationWorkflowFeatures"]);
    this.backupWorkflow["postprocessingWorkflowFeatures"] = clone(this.segmentedImageDetails['selectedSegmentedImage']["postprocessingWorkflowFeatures"]);
  }

  changeLayerSettings(settingType: string, layerType: string) {
    this.segmentationUsingThresholding = false;

    const selectedSegment = this.segmentedImageDetails['selectedSegmentedImage'];

    // Utility function for showing messages
    const checkAndShowMsg = (layer: string, workflowSelected: boolean) => {
      if (selectedSegment[layer].length > 0 && !workflowSelected) {
        this.showMsg(layer);
        return true; // Indicates failure
      }
      return false; // Indicates success
    };

    // Check pre-processing layer conditions
    if (layerType === 'pre-processing' && checkAndShowMsg('preprocessingWorkflowFeatures', selectedSegment['preprocessingWorkflowSelected'])) {
      return false;
    }

    // Check segmentation layer conditions
    if (layerType === 'segmentation' && checkAndShowMsg('segmentationWorkflowFeatures', selectedSegment['segmentationWorkflowSelected'])) {
      return false;
    }

    // Check post-processing layer conditions
    if (layerType === 'post-processing') {
      if (checkAndShowMsg('postprocessingWorkflowFeatures', selectedSegment['postprocessingWorkflowSelected'])) {
        return false;
      }

      const segmentationWorkflow = selectedSegment['segmentationWorkflowFeatures'].filter((val: any) => val['selected'] === true);
      if (!segmentationWorkflow.length || !selectedSegment['segmentationWorkflowSelected']) {
        this.toastr.error('Please add segmentation layer.', '', {
          positionClass: 'custom-toast-position',
        });
        return false;
      }
    }

    // Set new layer configuration
    this.addNewWorkflowLayer = true;
    this.newLayerFor = layerType;
    this.currentLayerData = {
      type: layerType,
      actionType: settingType,
      subActionType: (settingType === 'add') ? 'addlayer' : 'editlayer',
      changedObj: {},
      layer: "",
      inputImage: ""
    };

    // Backup existing layers
    this.backupLayers();
    return true;
  }


  selectSearchedlayer(layerType: string, featuredata: any) {
    this.showSearchFilters = false;
    this.addNewWorkflowLayer = true;
    this.newLayerFor = layerType;
    this.currentLayerData['type'] = layerType;
    this.currentLayerData['actionType'] = 'add';
    this.currentLayerData['subActionType'] = 'addlayer';
    this.currentLayerData["changedObj"] = {};
    this.currentLayerData['layer'] = "";
    this.currentLayerData['inputImage'] = "";
    this.backupLayers();
    this.selectNewlayer(featuredata, true);
  }

  selectNewlayer(feature: any, runApi: boolean) {
    let fid = feature['fid'];
    this.newInnerLayer = true;
    this.newInnerLayerDetails = feature;
    this.segmentationUsingThresholding = false;
    if (fid == 11 || fid == 12) {
      this.segmentationUsingThresholding = true;
    }
    this.editTempBinarization = false;
    if (fid == 14 || fid == 15) {
      this.editTempBinarization = true;
    }
    let featuresdata = JSON.parse(JSON.stringify(this.features[fid]));
    featuresdata = this.changeFeatureDynamicValues(featuresdata);
    if (this.newLayerFor == 'pre-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'].push(featuresdata);
    } else if (this.newLayerFor == 'segmentation') {
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'].push(featuresdata);
    } else if (this.newLayerFor == 'post-processing') {
      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'].push(featuresdata);
    }
    this.dropDownLayer = this.getLatestLayerData();
    this.setLastSegmentedImage();
    if (runApi) {
      this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
    }
  }

  deleteLayer(ind: any, type: string) {
    this.currentLayerData['type'] = type;
    this.currentLayerData['layer'] = ind;
    this.currentLayerData['actionType'] = 'edit';
    this.currentLayerData['subActionType'] = 'delete';
    this.currentLayerData["changedObj"] = {};
    this.currentLayerData['inputImage'] = "";
    let checkValidFeature: boolean = true;
    if (type == 'pre-processing') {
      checkValidFeature = this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'][ind]['selected'];
      this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures'].splice(ind, 1);
      this.WorkflowOnOffByType('preprocessingWorkflow');
    } else if (type == 'segmentation') {
      checkValidFeature = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][ind]['selected'];
      this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].splice(ind, 1);
      this.WorkflowOnOffByType('segmentationWorkflow');
    } else if (type == 'post-processing') {
      checkValidFeature = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'][ind]['selected'];
      this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].splice(ind, 1);
      this.WorkflowOnOffByType('postprocessingWorkflow');
    }
    this.dropDownLayer = this.getLatestLayerData();
    this.setOriginalImageDropDown(true);
    if (type == 'segmentation') {
      this.dropDownVisualization = this.getLatestVisualizationData();
    }
    this.setRegionProps();
    this.saveWorkflowBtnEvent.emit(true);
    this.workflowChanged = true;
    if (checkValidFeature) {
      this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
    }
  }

  WorkflowOnOffByType(type: any) {
    if (this.segmentedImageDetails['selectedSegmentedImage'][type + 'Features'].length == 0) {
      this.segmentedImageDetails['selectedSegmentedImage'][type + 'Selected'] = false;
    }
  }

  getSampleImage() {
    if ((this.segmentedImageDetails['cropimg'])) {
      return this.segmentedImageDetails['cropimg'];
    } else {
      return this.segmentedImageDetails['selectedSegmentedImage']['baseImage'];
    }
  }



  checkExportAnalysisLink() {
    let returnStatus = false;
    if (
      ((this.segmentedImageDetails['selectedSegmentedImage']['pillar-pattern-analysis']['excel_path'] == '' &&
        this.segmentedImageDetails['selectedSegmentedImage']['pillar-pattern-analysis']['pdf_path'] == '') ||
        this.updateAnalysis['pillar-pattern-analysis']) &&
      (this.segmentedImageDetails['selectedSegmentedImage']['feature-profile-analysis']['data'].length == 0 ||
        this.updateAnalysis['feature-profile-analysis']) &&
      (this.segmentedImageDetails['selectedSegmentedImage']['metal-recess-analysis']['data'].length == 0 ||
        this.updateAnalysis['metal-recess-analysis'])
    ) {
      returnStatus = true;
    }
    return returnStatus;
  }

  downloadFile(link: any) {
    window.location.assign(link);
  }

  downloadMultipleFiles(baseLink: any, files: any) {
    let timer = 0;
    files.forEach((val: any) => {
      setTimeout((_: any) => {
        this.downloadFile(baseLink + val);
      }, timer);
      timer = ((timer == 0) ? timer + 800 : timer) * 2;
    });
  }

  checkUpdateAnalysis(analysis_type: any) {
    if (this.segmentedImageDetails['selectedSegmentedImage'][analysis_type]['data'].length > 0 && this.updateAnalysis[analysis_type]) {
      // this.toastr.error('Please update the analysis');

      return false;
    } else {
      return true;
    }
  }

  getAnalysisNameFromKey(analysis_type: any, analysis_key: any) {
    return this.segmentation_analysis_list[analysis_type].find((val: any) => val['key'] == analysis_key)['name'];
  }

  checkTraceBoundaries(analysis: any, analysis_type: any) {
    if (analysis_type == 'feature-profile-analysis' && analysis['analysis_type'] == "fpo") {
      let checkpostFeat = this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures'].find((val: any) => (val['fid'] == 24 && val['selected'] == true));
      if (
        checkpostFeat != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected'] &&
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected'] &&
        this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => val['selected'] == true).length > 0
      ) {
        return true;
      } else {
        return false;
      }
    } else {
      return true;
    }
  }

  checkAnalysis(analysis: any, analysis_type: any) {
    return this.segmentation_analysis_list[analysis_type].find((val: any) => val['key'] == analysis['analysis_type']);
  }

  checkAnalysisIsAlreadyAdded(analysis: any, analysis_type: any) {
    return this.segmentedImageDetails['selectedSegmentedImage'][analysis_type]['data'].find((val: any) => val['analysis_type'] == analysis['key']);
  }

  deleteAnalysis(layIndex: any, type: any) {
    this.segmentedImageDetails['selectedSegmentedImage'][type]['data'].splice(layIndex, 1);
    if (type == 'pillar-pattern-analysis' && this.segmentedImageDetails['selectedSegmentedImage'][type]['data'].length == 0) {
      this.segmentedImageDetails['selectedSegmentedImage']['pillar-pattern-analysis']['pdf_path'] = "";
      this.segmentedImageDetails['selectedSegmentedImage']['pillar-pattern-analysis']['excel_path'] = "";
    }
    this.dropDownLayer = this.getLatestLayerData();
    let lastImg = this.getLastSegmentedImage('post-processing', '', '');
    let segmentationData = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'].filter((val: any) => (val['selected'] == true));
    let disImage = "";
    let returnProps = {};
    if (segmentationData.length > 0 && segmentationData[0]['Params']['visualization'] == 'Black/white (default)') {
      disImage = lastImg['black&white'];
    } else {
      disImage = lastImg['filtered_image'];
    }
    if (lastImg['region_properties'] != undefined) {
      returnProps = lastImg['region_properties']
    } else {
      returnProps = {};
    }
    this.segmentedImageDetails['segmentedImage'] = disImage;
    this.segmentedImageDetails['region_properties'] = returnProps;
    this.setOriginalImageDropDown(false);
  }


  getCurrentWorkFlow() {
    let preprocessingWorkflow = clone(this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowFeatures']);
    preprocessingWorkflow.forEach((element: any, index: number) => {
      // delete preprocessingWorkflow[index]['result'];
      if (this.returnKeysFromObject(element['slider']).length > 0) {
        this.returnKeysFromObject(element['slider']).forEach(val => {
          delete preprocessingWorkflow[index]['slider'][val]['format'];
          delete preprocessingWorkflow[index]['slider'][val]['ariaFormat'];
        });
      }
    });
    let segmentationWorkflow = clone(this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures']);
    segmentationWorkflow['forEach']((element: any, index: number) => {
      // delete segmentationWorkflow[index]['result'];
      if (this.returnKeysFromObject(element['slider']).length > 0) {
        this.returnKeysFromObject(element['slider']).forEach(val => {
          delete segmentationWorkflow[index]['slider'][val]['format'];
          delete segmentationWorkflow[index]['slider'][val]['ariaFormat'];
        });
      }
    });
    let postprocessingWorkflow = clone(this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowFeatures']);
    postprocessingWorkflow.forEach((element: any, index: number) => {
      // delete postprocessingWorkflow[index]['result'];
      if (this.returnKeysFromObject(element['slider']).length > 0) {
        this.returnKeysFromObject(element['slider']).forEach(val => {
          delete postprocessingWorkflow[index]['slider'][val]['format'];
          delete postprocessingWorkflow[index]['slider'][val]['ariaFormat'];
        });
      }
    });
    return {
      "preprocessingWorkflowSelected": clone(this.segmentedImageDetails['selectedSegmentedImage']['preprocessingWorkflowSelected']),
      "preprocessingWorkflowFeatures": preprocessingWorkflow,
      "segmentationWorkflowSelected": clone(this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowSelected']),
      "segmentationWorkflowFeatures": segmentationWorkflow,
      "postprocessingWorkflowSelected": clone(this.segmentedImageDetails['selectedSegmentedImage']['postprocessingWorkflowSelected']),
      "postprocessingWorkflowFeatures": postprocessingWorkflow
    }
  }

  /************************************crop and scale bar ******************/
  checkCropAndScaleChanges() {
    let manualCoordinates = {};
    if (this.returnKeysFromObject(this.segmentedImageDetails['selectedSegmentedImage']["manualcoordinates"]).length > 0) {
      manualCoordinates = this.segmentedImageDetails['selectedSegmentedImage']["manualcoordinates"];
    } else {
      manualCoordinates = this.imageCropTabObj['defaultCoordinates'];
    }
    if (
      JSON.stringify(manualCoordinates) !== JSON.stringify(this.imageCropTabObj['manualCoordinates'])
    ) {
      this.imageCropTabObj['imageCropChanged'] = true;
    } else {
      this.imageCropTabObj['imageCropChanged'] = false;
    }
  }

  imageLoaded() {
    this.imageCropTabObj['imageLoaded'] = true;
  }

  getDisplayedImageSize() {
    let img = document.getElementsByClassName('source-image');
    return { "width": img[0].clientWidth, "height": img[0].clientHeight };
  }

  cropperReady(event: any) {
    this.imageCropTabObj['cropImageShape'] = event;
    if (this.returnKeysFromObject(this.imageCropTabObj['manualCoordinates']).length > 1) {
      this.imageCropTabObj['cropperPosition'] = {
        "x1": (this.imageCropTabObj['manualCoordinates']['x1'] / 100) * event['width'],
        "y1": (this.imageCropTabObj['manualCoordinates']['y1'] / 100) * event['height'],
        "x2": (this.imageCropTabObj['manualCoordinates']['x2'] / 100) * event['width'],
        "y2": (this.imageCropTabObj['manualCoordinates']['y2'] / 100) * event['height']
      };
    } else {
      this.imageCropTabObj['cropperPosition'] = {
        "x1": 0,
        "y1": 0,
        "x2": event['width'],
        "y2": event['height']
      };
    }
    this.imageCropTabObj['imageCropperLoaded'] = true;
    this.apiCall = false;
  }

  imageCropped(event: any) {
    let imageToBeApplyOnCanvas = this.segmentedImageDetails['selectedSegmentedImage'];
    // this.imageCropTabObj['cropImageShape'] = this.getDisplayedImageSize();
    let disWidth = this.imageCropTabObj['cropImageShape']['width'];
    let disHeight = this.imageCropTabObj['cropImageShape']['height'];
    let width = (event['cropperPosition']['x2'] - event['cropperPosition']['x1']);
    let height = (event['cropperPosition']['y2'] - event['cropperPosition']['y1']);
    var x1Percentage = (event['cropperPosition']['x1'] / disWidth) * 100;
    var y1Percentage = (event['cropperPosition']['y1'] / disHeight) * 100;
    var x2Percentage = (event['cropperPosition']['x2'] / disWidth) * 100;
    var y2Percentage = (event['cropperPosition']['y2'] / disHeight) * 100;
    var widthPercentage = (width / disWidth) * 100;
    var heightPercentage = (height / disHeight) * 100;

    let coordinates = {
      x1: x1Percentage,
      y1: y1Percentage,
      x2: x2Percentage,
      y2: y2Percentage,
      w: widthPercentage,
      h: heightPercentage
    };
    if (this.imageCropTabObj['imageCropperLoaded']) {
      if (this.imageCropTabObj["imageCropped"]) {
        this.imageCropTabObj['manualCoordinates'] = coordinates;
        this.checkCropAndScaleChanges();
      }
      this.imageCropTabObj['tempImage'] = event['base64'];
      this.imageCropTabObj['tempImage_url'] = event['base64'];
      this.imageCropTabObj["croppedImageWidth"] = Math.round((widthPercentage / 100) * imageToBeApplyOnCanvas['baseImageShape'][1]);
      this.imageCropTabObj["croppedImageHeight"] = Math.round((heightPercentage / 100) * imageToBeApplyOnCanvas['baseImageShape'][0]);
      this.imageCropTabObj["imageCropped"] = true;
    }
  }

  getSelectedCropImage(flag: boolean) {
    this.updateOldCoordinates();
    if (this.selectedMask) {
      let detail: any = {
        'base_image': this.segmentedImageDetails['selectedSegmentedImage']['image'],
        'image': this.segmentedImageDetails['selectedSegmentedImage']['baseImage'],
        'coordinates': this.selectedMask['coordinates']
      }
      let coordinates = detail['coordinates'];
      detail['ymax'] = 0;
      detail['path'] = true;

      this.apiCall = true;

      this.imageAnalysisService.getMaskImage(detail).then((response) => {
        if (response) {
          var parsedData = response;
          this.imageCropTabObj["tempImage"] = parsedData['cropimg'];
          this.getImageContent(this.imageCropTabObj, 'tempImage')
          this.segmentedImageDetails['selectedSegmentedImage']['cropimgShape'] = response['cropimg_shape'];
          this.segmentedImageDetails['selectedSegmentedImage']['masked_image'] = parsedData['cropimg'];
          this.imageCropTabObj['manualCoordinates'] = coordinates;
          if (flag) {
            this.apiCall = true;
            this.applyCropChanges();
          } else {
            this.apiCall = false;
          }
        }
      });
    }
  }

  updateOldCoordinates() {
    if (this.selectedMask && this.selectedMask['old_coordinates'] && this.selectedMask['new_coordinates']) {
      this.selectedMask['old_coordinates'] = { ...this.selectedMask.new_coordinates };
    }
  }


  applyCropChanges() {
    this.checkCropAndScaleChanges();
    this.segmentedImageDetails['inputImageForSegmentation'] = this.imageCropTabObj["tempImage"];
    this.segmentedImageDetails['segmentedImage'] = this.imageCropTabObj["tempImage"];
    this.previewImage = this.imageCropTabObj["tempImage"];

    this.getImageContent(this.segmentedImageDetails, 'segmentedImage')

    this.segmentedImageDetails['selectedSegmentedImage']['cropimg'] = this.imageCropTabObj["tempImage"];
    this.getImageContent(this.segmentedImageDetails, 'displayInputImage')
    this.currentLayerData['type'] = 'scratch';
    this.segmentedImageDetails['selectedSegmentedImage']["manualcoordinates"] = this.imageCropTabObj['manualCoordinates'];

    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
    this.closeCropTab(false);
  }
  /************************************crop and scale bar ******************/

  saveWorkFlow(action: string) {
    if (this.newWorkflow) {
      this.openWorkflowNameDialog('new', action);
    } else {

      let imageData = this.segmentationworkflow['images'].filter((val: any) => (val['workflowId'] == this.editWorkflowId && val['path'] != this.segmentedImageDetails['selectedSegmentedImage']['path']));

      if (this.workflowChanged && imageData != undefined && imageData.length > 0) {
        this.maskApplied = false;
        this.openWorkflowSaveOrSaveAsConfirmation(action);
      }

      else if (!this.workflowChanged && this.maskApplied) {
        this.maskApplied = true;
        this.openWorkflowSaveOrSaveAsConfirmation(action);
      } else {
        // this.checkCarryAnalysis('existing', action, false);
        this.callSaveWorkflowApi('existing', action, false);
      }
    }
    let project_id = this.configService.SelectedProjectId;
    // this.imageAnalysisService.updateLastAccess({ "dataset_id": this.datasetId , 'project_id' : project_id}).subscribe();
  }

  openWorkflowNameDialog(type: string, action: string) {
    let name = this.editWorkflowName;
    let manual = this.carryForwardCrop;

    let onlyMaskApplied = this.maskApplied;
    let checkanalysis = false;

    if (type == 'new') {
      let image_count = this.fetchImageIndex(this.segmentedImageDetails['selectedSegmentedImage']['path']) + 1;
      let workflow_count = this.allWorkFlows.length + 1
      name = this.selectedFolderName + " - Image " + image_count + " workflow - " + workflow_count;
      manual = (this.returnKeysFromObject(this.segmentedImageDetails['selectedSegmentedImage']["manualcoordinates"]).length > 0) ? true : false;
    }
    checkanalysis = false;

    const dialogRef = this.dialog.open(SaveWorkflowDialogBox, {
      width: '30%',
      disableClose: true,
      panelClass: "add-data-set-panel-class",
      data: { "type": type, "action": action, "name": name, "manual": manual, "checkanalysis": checkanalysis }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result != undefined && result['name'] != undefined && result['name'] != "") {
        this.saveWorkflowBtnEvent.emit(true);
        this.editWorkflowName = result['name'];
        this.defaultWorkflow = result['default_workflow'];
        this.applyToAll = result['apply_all'];
        this.carryForwardCrop = result['manual'];
        this.carryForwardAnalysis = result['analysis'];
        this.wf_for_incomingimages = result['wf_for_incomingimages']

        this.callSaveWorkflowApi(type, action, false);
        // if (type == 'new') {
        //   this.callSaveWorkflowApi(type, action, false);
        // }
      } else if (action == 'save&close' && result['closeWorkflow']) {
        // this.resetSegmentedPage();
        this.saveWorkflowBtnEvent.emit(false);
        this.invokeAllWorkflowsFuncEvent.emit({ callCroppedImages: false, imagesData: this.segmentationworkflow['images'] });
        let closeType = (this.closeType) ? this.closeType : 'backToFolders';
        this.imageAnalysisService.triggerCloseManageWorkflow(closeType);
      }
    });
    let project_id = this.configService.SelectedProjectId;
    // this.imageAnalysisService.updateLastAccess({ "dataset_id": this.datasetId, "project_id": project_id }).subscribe();
  }

  checkCarryAnalysis(type: string, action: string, removeApppliedStatus: boolean) {
    if (this.carryForwardAnalysis) {
      this.callSaveWorkflowApi(type, action, removeApppliedStatus);
    } else {
      if (
        !this.isAnalysisExists &&
        (this.segmentedImageDetails['selectedSegmentedImage']['pillar-pattern-analysis']['data'].length > 0 && !this.updateAnalysis["pillar-pattern-analysis"]) ||
        (this.segmentedImageDetails['selectedSegmentedImage']['feature-profile-analysis']['data'].length > 0 && !this.updateAnalysis["feature-profile-analysis"]) ||
        (this.segmentedImageDetails['selectedSegmentedImage']['tier-analysis']['data'].length > 0 && !this.updateAnalysis["tier-analysis"]) ||
        (this.segmentedImageDetails['selectedSegmentedImage']['metal-recess-analysis']['data'].length > 0 && !this.updateAnalysis["metal-recess-analysis"]) ||
        (this.segmentedImageDetails['selectedSegmentedImage']['bubble-analysis']['data'].length > 0 && !this.updateAnalysis["bubble-analysis"]) ||
        (this.segmentedImageDetails['selectedSegmentedImage']['pillar-anomaly-analysis']['data'].length > 0 && !this.updateAnalysis["pillar-anomaly-analysis"]) ||
        (this.segmentedImageDetails['selectedSegmentedImage']['pillar-c2c-analysis']['data'].length > 0 && !this.updateAnalysis["pillar-c2c-analysis"]) ||
        (this.segmentedImageDetails['selectedSegmentedImage']['metal-voids-analysis']['data'].length > 0 && !this.updateAnalysis["metal-voids-analysis"])
      ) {
        const dialogRef = this.dialog.open(SaveAnalysisConfirmationDialogComponent, {
          maxWidth: "650px",
          data: { "analyisData": this.segmentedImageDetails['selectedSegmentedImage'], "analysisList": this.segmentation_analysis_list }
        });
        dialogRef.afterClosed().subscribe(dialogResult => {
          if (dialogResult != undefined) {
            if (dialogResult['save'] === true) {
              this.carryForwardAnalysis = dialogResult['analysis'];
              if (this.carryForwardAnalysis) {
                this.carryForwardScalebar = true;
              }
            }
            this.callSaveWorkflowApi(type, action, removeApppliedStatus);
          }
        });
      } else {
        this.callSaveWorkflowApi(type, action, removeApppliedStatus);
      }
    }
  }

  callSaveWorkflowApi(type: string, action: string, removeApppliedStatus: boolean) {
    let split_img = this.segmentedImageDetails['segmentedImage'].split('/');
    split_img = split_img.filter((_val: any, index: number) => (index != split_img.length - 1));

    let workflowData: any = {
      "type": type,
      "dirpath": split_img.join('/'),
      "username": this.currentUser.name,
      "project_id": this.configService.SelectedProjectId,
      "dataset_id": this.datasetId,
      "foldername": this.selectedFolderName,
      "name": this.editWorkflowName,
      "image_path": this.segmentedImageDetails['selectedSegmentedImage']['path'],
      "cropimg": this.segmentedImageDetails['selectedSegmentedImage']['cropimg'],
      "wf_sample_image": this.segmentedImageDetails['selectedSegmentedImage']['baseImage'],
      "_id": this.editWorkflowId,
      "workflow": this.getCurrentWorkFlow(),
      "default": this.defaultWorkflow,
      "applyToAll": this.applyToAll,
      "carrycrop": this.carryForwardCrop,
      "carryanalysis": this.carryForwardAnalysis,
      "wf_for_incomingimages": this.wf_for_incomingimages,
      "output_directory_options": this.segmentedImageDetails['selectedSegmentedImage']['outputDirectoryOptions'],
    };
    if (this.returnKeysFromObject(this.segmentedImageDetails['selectedSegmentedImage']["manualcoordinates"]).length > 0) {
      workflowData["manualcoordinates"] = this.segmentedImageDetails['selectedSegmentedImage']["manualcoordinates"];
      workflowData["applyCropping"] = true;
    } else {
      workflowData["applyCropping"] = false;
    }
    workflowData['removeconnection'] = false;
    if (this.editWorkflowId != '' && type != 'new') {
      let currPath = this.segmentedImageDetails['selectedSegmentedImage']['path'];
      let linkedImages = this.segmentationworkflow['images'].filter((val: any) => (val['path'] != currPath && val['workflowId'] == this.editWorkflowId));
      if (linkedImages.length > 0 && this.workflowChanged) {
        workflowData['removeconnection'] = true;
      }
    }
    this.imageAnalysisService
      .saveWorkflow(workflowData)
      .then((response) => {
        if (response) {
          if (response['workflow_id']) {
            this.saveWorkflowBtnEvent.emit(false);
            this.workflowChanged = false;
            this.editWorkflowId = response['workflow_id'];
            this.newWorkflow = false;
            this.maskApplied = false;
            this.saveWorkflowBtn = false;
            this.assignWorkflowToAllImagesOfFolder(removeApppliedStatus, action, type);
            if (action == 'save&close' || action == 'saveas&close') {
              // this.resetSegmentedPage();
              this.invokeAllWorkflowsFuncEvent.emit({ callCroppedImages: false, imagesData: this.segmentationworkflow['images'] });
              let closeType = (this.closeType) ? this.closeType : 'backToFolders';
              this.imageAnalysisService.triggerCloseManageWorkflow(closeType);
            } else if (type == 'new') {
              this.invokeAllWorkflowsFuncEvent.emit({ callCroppedImages: false, imagesData: this.segmentationworkflow['images'] });
            }
          } else {
            this.toastr.error('Failed to create the workflow', '', {
              positionClass: 'custom-toast-position',
            });

          }
        }
      })

  }

  afterSaveWorkflow(action: string, type: string) {
    if (action == 'save&close' || action == 'saveas&close') {
      // this.resetSegmentedPage();
      // this.invokeAllWorkflowsFuncEvent.emit({ callCroppedImages: false, imagesData: this.segmentationworkflow['images'] });
      let closeType = (this.closeType) ? this.closeType : 'backToFolders';
      this.imageAnalysisService.triggerCloseManageWorkflow(closeType);
    } else if (type == 'new') {
      // this.invokeAllWorkflowsFuncEvent.emit({ callCroppedImages: false, imagesData: this.segmentationworkflow['images'] });
    }
  }

  assignWorkflowToAllImagesOfFolder(removeApppliedStatus: boolean, action: string, type: string) {
    if (this.applyToAll) {
      let reqData: any = {
        "_id": this.editWorkflowId,
        "image_path": [],
        "aftersavingwf": false,
        "applied_workflow": this.segmentedImageDetails['selectedSegmentedImage']['path'],
        "duplicate": false,
        "dataset_id": this.datasetId,
        "project_id": this.configService.SelectedProjectId
      }
      for (var i = 0; i < this.segmentationworkflow['images'].length; i++) {
        reqData["image_path"].push({ "image": this.segmentationworkflow['images'][i]['path'], "PixelSizeX": this.segmentationworkflow['images'][i]['PixelSizeX'], "PixelSizeY": this.segmentationworkflow['images'][i]['PixelSizeY'] });
      }

      this.imageAnalysisService
        .assignWorflowToImages(reqData)
        .then((response) => {
          if (response) {
            var parsedData = response;
            let segmentationworkflow: any;
            segmentationworkflow = clone(this.segmentationworkflow);
            reqData["image_path"].forEach((val: any) => {
              let getRow = segmentationworkflow['images'].findIndex((innerval: any) => innerval['path'] == val['image']);
              if (getRow >= 0) {
                segmentationworkflow['images'][getRow]['workflowId'] = reqData["_id"];
              }
            });
            parsedData['applieddata'].forEach((appliedImage: any) => {
              let getRow = this.segmentationworkflow['images'].findIndex((innerval: any) => innerval['path'] == appliedImage['appliedpath']);
              if (getRow >= 0) {
                segmentationworkflow['images'][getRow]['appliedId'] = appliedImage["applied_id"];
              }
            });
            this.updateSegementationEvent.emit(segmentationworkflow);
            this.afterSaveWorkflow(action, type);

            this.toastr.success('Assigned workflow to all images. Processed workflow on parent image', '', {
              positionClass: 'custom-toast-position',
            });

            this.applyToAll = false;

          }
        })
    } else {
      this.assignWorkflowToImages(
        { "_id": this.editWorkflowId },
        [
          {
            "path": this.segmentedImageDetails['selectedSegmentedImage']['path'],
            "PixelSizeX": this.segmentedImageDetails['selectedSegmentedImage']['PixelSizeX'],
            "PixelSizeY": this.segmentedImageDetails['selectedSegmentedImage']['PixelSizeY'],
            "appliedId": this.segmentedImageDetails['selectedSegmentedImage']['appliedId'],
            "workflowId": this.segmentedImageDetails['selectedSegmentedImage']['workflowId']
          }
        ],
        true,
        false,
        removeApppliedStatus,
        action,
        type
      );
    }
  }

  assignWorkflowToImages(workflow: any, selectedImages: any, aftersavingwf: boolean, fromOtherFolder: boolean, removeApppliedStatus: boolean, action: string, type: string) {
    let reqData: any = {
      "_id": workflow['_id'],
      "image_path": [],
      "aftersavingwf": aftersavingwf,
      "duplicate": false,
      "dataset_id": this.datasetId,
      "project_id": this.configService.SelectedProjectId
    };
    if (fromOtherFolder) {
      reqData["duplicate"] = true;
      reqData["username"] = this.currentUser["firstName"] + " " + this.currentUser["lastName"];
      reqData["foldername"] = this.selectedFolderName;
      reqData["dataset_id"] = this.datasetId
    }
    selectedImages.forEach((val: any) => {
      let applied_id = 0;
      if (val['appliedId'] != "" && val['appliedId'] != undefined && val['appliedId'] != 0) {
        applied_id = val['workflowId'];
      }
      reqData["image_path"].push({
        "image": val['path'],
        "PixelSizeX": val['PixelSizeX'],
        "PixelSizeY": val['PixelSizeY'],
        "workflow_applied": applied_id
      });
    });
    this.activiateApiCall(true);

    this.imageAnalysisService
      .assignWorflowToImages(reqData)
      .then((response) => {
        if (response) {
          var parsedData = response;
          let segmentationworkflow = clone(this.segmentationworkflow);
          if (removeApppliedStatus) {
            segmentationworkflow['images'].forEach((indImg: any, imgInd: number) => {
              if (indImg['workflowId'] == reqData["_id"]) {
                segmentationworkflow['images'][imgInd]['appliedId'] = 0;
              }
            });
            this.updateSegementationEvent.emit(segmentationworkflow);
          }
          reqData["image_path"].forEach((val: any) => {
            let getRow = segmentationworkflow['images'].findIndex((innerval: any) => innerval['path'] == val['image']);
            if (getRow >= 0) {
              segmentationworkflow['images'][getRow]['workflowId'] = reqData["_id"];
            }
          });
          parsedData['applieddata'].forEach((appliedImage: any) => {
            let getRow = segmentationworkflow['images'].findIndex((innerval: any) => innerval['path'] == appliedImage['appliedpath']);
            if (getRow >= 0) {
              segmentationworkflow['images'][getRow]['workflowId'] = appliedImage["workflow_id"];
              segmentationworkflow['images'][getRow]['appliedId'] = appliedImage["applied_id"];
            }
          });
          this.updateSegementationEvent.emit(segmentationworkflow);
          this.afterSaveWorkflow(action, type);
          if (parsedData['applieddata'].length > 0) {
            this.toastr.success('Assigned workflow to selected image(s)', '', {
              positionClass: 'custom-toast-position',
            });
          } else {
            this.toastr.success('Assigned workflow to selected image(s)', '', {
              positionClass: 'custom-toast-position',
            });
          }
          if (fromOtherFolder) {
            this.invokeAllWorkflowsFuncEvent.emit({ callCroppedImages: true, imagesData: this.segmentationworkflow['images'] });
          }
        }
        this.activiateApiCall(false);
      })
  }

  closeAddWorkflow() {
    if (this.saveWorkflowBtn) {
      if (this.newWorkflow) {
        this.openWorkflowNameDialog('new', "save&close");
      } else {
        const dialogRef = this.dialog.open(SaveWorkflowConfirmationDialogboxComponent, {
          maxWidth: "400px",
          data: { "title": "Save this Workflow", "message": "Do you want to save changes made to this workflow?" }
        });
        dialogRef.afterClosed().subscribe(dialogResult => {
          if (dialogResult != undefined && dialogResult['save']) {
            this.saveWorkFlow("save&close");
          } else {
            if (dialogResult != undefined && dialogResult['closeWorkflow']) {
              // this.resetSegmentedPage();
              this.saveWorkflowBtnEvent.emit(false);
              this.invokeAllWorkflowsFuncEvent.emit({ callCroppedImages: false, imagesData: this.segmentationworkflow['images'] });
              this.imageAnalysisService.triggerCloseManageWorkflow(this.closeType);
            }
          }
        });
      }
    } else {
      this.resetSegmentedPage();
      this.invokeAllWorkflowsFuncEvent.emit({ callCroppedImages: false, imagesData: this.segmentationworkflow['images'] });
    }
  }

  openWorkflowSaveOrSaveAsConfirmation(action: string) {
    let data = {}
    if (this.workflowChanged) {
      data = { "assignedtoOtherImages": true, "title": "Save this workflow", "message": "Other images are also assigned to this workflow. Would you like to save changes for all images assigned to this workflow or save changes only for this image?" }
    } else {
      data = { "assignedtoOtherImages": true, "title": "Save this image", "message": "The mask for this image has been changed / modified. Do you want to save this result?", "maskApplied": true }
    }
    const dialogRef = this.dialog.open(SaveWorkflowConfirmationDialogboxComponent, {
      maxWidth: "650px",
      data: data
    });
    dialogRef.afterClosed().subscribe(dialogResult => {
      if (dialogResult != undefined) {
        if (dialogResult['save'] == 'save_anyway') {
          // this.checkCarryAnalysis('existing', action, true);
          this.callSaveWorkflowApi('existing', action, true);
        } else if (dialogResult['save'] == 'save_as_new' && !this.maskApplied) {
          this.openWorkflowNameDialog('new', 'saveas&close');
        } else if (dialogResult['save'] == 'save_as_new' && this.maskApplied) {
          this.callSaveWorkflowApi('existing', action, false);
          this.maskApplied = false;
        }
      }
    });
  }

  setLastSegmentedImage() {
    let segWorkflow = this.segmentedImageDetails['selectedSegmentedImage']["segmentationWorkflowFeatures"].filter((val: any) => val['selected'] == true);
    let lastSegmentedImage = this.getLastSegmentedImage('post-processing', false, "");
    if (segWorkflow != undefined && segWorkflow.length > 0) {
      if (segWorkflow[segWorkflow.length - 1]['Params']['visualization'] == 'Black/white (default)' && lastSegmentedImage['black&white'] != undefined && lastSegmentedImage['black&white'] != "") {
        this.segmentedImageDetails['segmentedImage'] = lastSegmentedImage['black&white'];
      } else {
        this.segmentedImageDetails['segmentedImage'] = lastSegmentedImage['filtered_image'];
      }
    } else {
      this.segmentedImageDetails['segmentedImage'] = lastSegmentedImage['filtered_image'];
    }
  }

  editTemplateImage(layIndex: any) {
    let featuresdata = this.segmentedImageDetails['selectedSegmentedImage']['segmentationWorkflowFeatures'][layIndex];
    let layerType = 'segmentation';
    this.templateMatchingId = layIndex;
    this.addNewWorkflowLayer = true;
    this.newLayerFor = layerType;
    this.currentLayerData['type'] = layerType;
    this.currentLayerData['actionType'] = 'add';
    this.currentLayerData['subActionType'] = 'addlayer';
    this.currentLayerData["changedObj"] = {};
    this.currentLayerData['layer'] = "";
    this.currentLayerData['inputImage'] = "";
    this.backupLayers();
    this.newInnerLayer = true;
    this.newInnerLayerDetails = featuresdata;
    this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'].push(featuresdata);
    this.dropDownLayer = this.getLatestLayerData();
    this.setLastSegmentedImage();
    this.openTemplateImage(0);
  }

  openTemplateImage(layIndex: any) {
    this.editTemplateMatching = true;
    this.matchingCoords = this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params']["template_cord"];
  }

  applyTemplateMatching(layIndex: any) {
    this.editTemplateMatching = false;
    let objkey = 'template_cord';
    this.currentLayerData['type'] = 'segmentation';
    this.currentLayerData['layer'] = "";
    this.currentLayerData['actionType'] = 'add';
    this.currentLayerData['subActionType'] = 'template';
    this.currentLayerData["changedObj"]['key'] = objkey;
    this.currentLayerData["changedObj"]['val'] = this.matchingCoords;
    this.currentLayerData['inputImage'] = "";
    this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['Params']["template_cord"] = this.matchingCoords;
    delete this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][layIndex]['result'];
    this.matchingCoords = {};
    this.processInputImageSegmentation(this.segmentedImageDetails['selectedSegmentedImage']);
  }

  loadTemplateCanvas() {
    let _scope = this;
    // code for image aspectRatio
    let height = this.templateCanvasWrap.nativeElement.offsetHeight;
    let width = this.templateCanvasWrap.nativeElement.offsetWidth;

    let canvas: HTMLCanvasElement = this.templateCanvas.nativeElement;
    let ctx: any = canvas.getContext('2d');

    var image = new Image();
    image.src = this.getSegmentatedImageURL()['url'];
    image.onload = function () {
      canvas.width = width;
      canvas.height = height;
      ctx.drawImage(image, 0, 0, width, height);
      if (_scope.returnKeysFromObject(_scope.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['Params']["template_cord"]).length > 0) {
        let coordinates = _scope.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'][0]['Params']["template_cord"];
        let getX1 = (coordinates['x1'] / 100) * width;
        let getY1 = (coordinates['y1'] / 100) * height;
        let getW = (coordinates['w'] / 100) * width;
        let getH = (coordinates['h'] / 100) * height;
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.strokeRect(getX1, getY1, getW, getH);
        _scope.matchingCoords = coordinates;
      }
    }

    this.templateCanvas.nativeElement.removeEventListener("mousedown", function (_event: any) { });
    this.templateCanvas.nativeElement.removeEventListener("mouseup", function (_event: any) { });
    this.templateCanvas.nativeElement.removeEventListener("mousemove", function (_event: any) { });
    this.templateCanvas.nativeElement.removeEventListener("mouseout", function (_event: any) { });

    let startX = 0;
    let startY = 0;
    let x2 = 0;
    let y2 = 0;
    let w = 0;
    let h = 3;
    let drag = false;
    this.templateCanvas.nativeElement.addEventListener('mousedown', function (e: any) {
      drag = true;
      startX = e.offsetX;
      startY = e.offsetY;
    }, false);
    this.templateCanvas.nativeElement.addEventListener('mousemove', function (e: any) {
      if (drag) {
        ctx.drawImage(image, 0, 0, width, height);
        x2 = e.offsetX;
        y2 = e.offsetY;
        w = (e.offsetX) - startX;
        h = (e.offsetY) - startY;
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.strokeRect(startX, startY, w, h);
      }
    }, false);
    this.templateCanvas.nativeElement.addEventListener('mouseup', function (_e: any) {
      drag = false;
      var coordinates = {};
      var x1Percentage = (startX * 100) / width;
      var y1Percentage = (startY * 100) / height;
      var x2Percentage = (x2 * 100) / width;
      var y2Percentage = (y2 * 100) / height;
      var widthPercentage = (w * 100) / width;
      var heightPercentage = (h * 100) / height;
      coordinates = {
        x1: x1Percentage,
        y1: y1Percentage,
        x2: x2Percentage,
        y2: y2Percentage,
        w: widthPercentage,
        h: heightPercentage
      };
      _scope.matchingCoords = coordinates;
    }, false);
    this.templateCanvas.nativeElement.addEventListener("mouseout", function (_e: any) {
      if (drag) {
        drag = false;
      }
    }, false);
  }

  cancelTemplateMatching(_layIndex: any) {
    this.editTemplateMatching = false;
    this.matchingCoords = {};
  }

  clearTempImages() {
    let reqData: any = {};
    if (
      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'].length > 0
    ) {
      this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'].forEach((element: any) => {
        if (element['result'] != undefined) {
          if (element['result']['filtered_image'] != undefined && element['result']['filtered_image'] != "") {
            reqData['segmentedimage'] = element['result']['filtered_image'];
          }
          if (element['result']['histogram_path'] != undefined && element['result']['histogram_path'] != "") {
            reqData['histimage'] = element['result']['histogram_path'];
          }
          if (element['result']['black&white'] != undefined && element['result']['black&white'] != "") {
            reqData['binaryimage'] = element['result']['black&white'];
          }
        }
      });
    } else if (
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'].length > 0
    ) {
      this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'].forEach((element: any) => {
        if (element['result'] != undefined) {
          if (element['result']['filtered_image'] != undefined && element['result']['filtered_image'] != "") {
            reqData['segmentedimage'] = element['result']['filtered_image'];
          }
          if (element['result']['histogram_path'] != undefined && element['result']['histogram_path'] != "") {
            reqData['histimage'] = element['result']['histogram_path'];
          }
          if (element['result']['black&white'] != undefined && element['result']['black&white'] != "") {
            reqData['binaryimage'] = element['result']['black&white'];
          }
        }
      });
    } else if (
      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'] != undefined &&
      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'].length > 0
    ) {
      this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'].forEach((element: any) => {
        if (element['result'] != undefined) {
          if (element['result']['filtered_image'] != undefined && element['result']['filtered_image'] != "") {
            reqData['segmentedimage'] = element['result']['filtered_image'];
          }
          if (element['result']['histogram_path'] != undefined && element['result']['histogram_path'] != "") {
            reqData['histimage'] = element['result']['histogram_path'];
          }
          if (element['result']['black&white'] != undefined && element['result']['black&white'] != "") {
            reqData['binaryimage'] = element['result']['black&white'];
          }
        }
      });
    }
    if (this.returnKeysFromObject(reqData).length > 0) {
      // this.imageAnalysisService.deleteUnusedWfImages(reqData).subscribe(res => {
      //   var parsedData = JSON.parse(res['_body']);
      //   if (typeof parsedData.data != 'undefined') {

      //   }else{
      //     // this.toastr.error('Failed to delete workflow');
      //   }
      // });
    }
  }

  closeLayerSettings() {
    this.addNewWorkflowLayer = false;
    this.newLayerFor = "";
    this.resetCurrentLayerData();
    this.closeinnerLayerSettings(false);
  }

  closeinnerLayerSettings(backup: boolean) {
    this.newInnerLayer = false;
    this.newInnerLayerDetails = {};
    this.editTempBinarization = false;
    this.tempBinarization = {};
    this.showPreviewImage = false;
    if (backup) {
      this.clearTempImages();
      this.segmentedImageDetails['selectedSegmentedImage']["preprocessingWorkflowFeatures"] = clone(this.backupWorkflow["preprocessingWorkflowFeatures"]);
      this.segmentedImageDetails['selectedSegmentedImage']["segmentationWorkflowFeatures"] = clone(this.backupWorkflow["segmentationWorkflowFeatures"]);
      this.segmentedImageDetails['selectedSegmentedImage']["postprocessingWorkflowFeatures"] = clone(this.backupWorkflow["postprocessingWorkflowFeatures"]);
      this.setLastSegmentedImage();
    }
    this.segmentedImageDetails['selectedSegmentedImage']['tempPreprocessingWorkflowFeatures'] = [];
    this.segmentedImageDetails['selectedSegmentedImage']['tempSegmentationWorkflowFeatures'] = [];
    this.segmentedImageDetails['selectedSegmentedImage']['tempPostprocessingWorkflowFeatures'] = [];

    this.cancelTemplateMatching(0);
    this.templateMatchingId = -1;
  }

  closeSearchInnerLayerSettings() {
    this.searchFiltersList = [];
    this.showSearchFilters = false;
    this.segmentationUsingThresholding = false;
    this.closeinnerLayerSettings(true);
    this.closeLayerSettings();
  }

  closeCropTab(callApi: boolean) {
    if (callApi) {
      if (this.imageCropTabObj["tempImage"] != "") {
        // this.imageAnalysisService.deleteUnusedWfImages({ "segmentedimage": this.imageCropTabObj["tempImage"] }).subscribe(res => {
        //   var parsedData = res;
        //   if (typeof parsedData['data'] != 'undefined') {

        //   } else {
        //     this.toastr.error('Failed to delete workflow');
        //   }
        // });
      }
    }
    this.segAndCropTabSelected = 0;
    this.imageCropTabObj = {
      "defaultCoordinates": {
        "x1": 0,
        "y1": 0,
        "x2": 100,
        "y2": 100,
        "w": 100,
        "h": 100
      },
      "manualCoordinates": {},
      "imageCropperLoaded": false,
      "imageLoaded": false,
      "cropperPosition": {},
      "cropImageShape": {},
      "imageCropChanged": false,
      "tempImage": "",
      "croppedImageWidth": 0,
      "croppedImageHeight": 0,
      "imageCropped": false,
    };
  }

  resetSegmentedImageDetailsVariable() {
    this.segmentedImageDetails!['selectedSegmentedImage'] = {
      "shape": [],
      "ImageStripSize": "",
      "image": "",
      "path": "",
      "baseImage": "",
      "baseImageShape": "",
      "PixelSizeX": "",
      "PixelSizeY": "",
      "workflowId": "",
      "appliedId": "",
      "resetCrop": true,
      "cropImageType": "auto",
      "manualcoordinates": {},
      "scalebarByImage": "",
      "scalebarByPhysical": "",
      "scalebarByPhysicalUnit": "",
      "preprocessingWorkflowSelected": false,
      "preprocessingWorkflowFeatures": [],
      "tempPreprocessingWorkflowFeatures": [],
      "segmentationWorkflowSelected": false,
      "segmentationWorkflowFeatures": [],
      "tempSegmentationWorkflowFeatures": [],
      "postprocessingWorkflowSelected": false,
      "postprocessingWorkflowFeatures": [],
      "tempPostprocessingWorkflowFeatures": [],
      "cropimg": "",
      "cropimgShape": [],
      "scalebar": {},
      "outputDirectoryOptions": {
        "setDirectory": false,
        "defaultDirectory": false,
        "outputDirectory": ""
      }
    };
  }

  resetSegmentedPage() {
    this.resetInnerSegmentation();
    this.closeLayerSettings();
  }

  resetInnerSegmentation() {
    this.segmentedImageDetails['selectedSegmentedImage'] = {};
    this.segmentedImageDetails['inputImageForSegmentation'] = "";
    this.segmentedImageDetails['displayInputImage'] = "";
    this.segmentedImageDetails['segmentedImage'] = "";
    this.previewImage = "";
    this.apiCall = false;
    this.analysisData = {
      "pillar-pattern-analysis": {
        "analysisExploreBtn": false,
        "analysisExplored": false,
        "analysisExpandedId": -1
      },
      "feature-profile-analysis": {
        "analysisExploreBtn": false,
        "analysisExplored": false,
        "analysisExpandedId": -1
      },
      "tier-analysis": {
        "analysisExploreBtn": false,
        "analysisExplored": false,
        "analysisExpandedId": -1
      },
      "metal-recess-analysis": {
        "analysisExploreBtn": false,
        "analysisExplored": false,
        "analysisExpandedId": -1
      },
      "bubble-analysis": {
        "analysisExploreBtn": false,
        "analysisExplored": false,
        "analysisExpandedId": -1
      },
      "pillar-anomaly-analysis": {
        "analysisExploreBtn": false,
        "analysisExplored": false,
        "analysisExpandedId": -1
      },
      "pillar-c2c-analysis": {
        "analysisExploreBtn": false,
        "analysisExplored": false,
        "analysisExpandedId": -1
      },
      "metal-voids-analysis": {
        "analysisExploreBtn": false,
        "analysisExplored": false,
        "analysisExpandedId": -1
      }
    };
    this.resetCurrentLayerData();
    this.originalImagedropDownLayer = clone(this.dropDownLayersDefaultValues);
    this.dropDownLayer = {};
    this.dropDownVisualization = { "type": 'solid', "val": 'Black/white (default)', "disVal": 'Black/white (default)', "mainVal": 'solid,Black/white (default),Black/white (default)' };
    this.dropDownAnalysisVisualization = { "type": '', "val": '', "mainVal": '' };
    this.saveWorkflowBtnEvent.emit(false);
    this.workflowChanged = false;
    this.updateAnalysis = {
      "pillar-pattern-analysis": false,
      "feature-profile-analysis": false,
      "tier-analysis": false,
      "metal-recess-analysis": false,
      "bubble-analysis": false,
      "pillar-anomaly-analysis": false,
      "pillar-c2c-analysis": false,
      "metal-voids-analysis": false
    };
    this.newWorkflow = false;
    this.retrieveWorkflow = false;
    this.cropApplied = false;
    this.editWorkflowId = "";
    this.editWorkflowName = "";
    this.workflowLoading = false;
    this.addNewWorkflowLayer = false;
    this.newLayerFor = "";
    this.newInnerLayer = false;
    this.newInnerLayerDetails = {};
    this.editBinarization = false;
    this.binarization = {};
    this.editTempBinarization = false;
    this.tempBinarization = {};
    this.editTemplateMatching = false;
    this.matchingCoords = {};
    this.templateMatchingId = -1;
    this.showPreviewImage = false;
    this.imageCropTabObj = {
      "defaultCoordinates": {
        "x1": 0,
        "y1": 0,
        "x2": 100,
        "y2": 100,
        "w": 100,
        "h": 100
      },
      "manualCoordinates": {},
      "imageCropperLoaded": false,
      "imageLoaded": false,
      "cropperPosition": {},
      "cropImageShape": {},
      "imageCropChanged": false,
      "tempImage": "",
      "croppedImageWidth": 0,
      "croppedImageHeight": 0,
      "imageCropped": false
    };

    this.defaultWorkflow = false;
    this.applyToAll = false;
    this.defaultGuasionValue = -1;
    this.carryForwardCrop = false;
    this.carryForwardScalebar = false;
    this.carryForwardAnalysis = false;
    this.wf_for_incomingimages = false;
    this.isAnalysisExists = false;
    this.segmentationUsingThresholding = false;
    this.cropApplied = false;
    this.segAndCropTabSelected = 0;
  }

  resetCurrentLayerData() {
    this.currentLayerData['type'] = "";
    this.currentLayerData['actionType'] = "";
    this.currentLayerData['subActionType'] = "";
    this.currentLayerData['layer'] = "";
    this.currentLayerData["changedObj"] = {};
    this.currentLayerData['inputImage'] = "";
    this.resetBackupLayers();
  }

  isCropImageView() {
    return (this.segAndCropTabSelected == 1) ? true : false;
  }

  resetAnalysisVariables() {
    this.updateAnalysis = {
      "pillar-pattern-analysis": true,
      "feature-profile-analysis": true,
      "tier-analysis": true,
      "metal-recess-analysis": true,
      "bubble-analysis": true,
      "pillar-anomaly-analysis": true,
      "pillar-c2c-analysis": true,
      "metal-voids-analysis": true
    };
    let pillar = 'pillar-pattern-analysis';
    let feature = 'feature-profile-analysis';
    let tier = 'tier-analysis';
    let metal = 'metal-recess-analysis';
    let bubble = 'bubble-analysis';
    let pillaranomaly = 'pillar-anomaly-analysis';
    let pillarc2c = 'pillar-c2c-analysis';
    let metalvoids = 'metal-voids-analysis'
    if (
      this.segmentedImageDetails['selectedSegmentedImage'][pillar]['data'] == undefined ||
      (this.segmentedImageDetails['selectedSegmentedImage'][pillar]['data'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage'][pillar]['data'].length == 0)
    ) {
      this.analysisData[pillar]['analysisExplored'] = false;
    }
    if (
      this.segmentedImageDetails['selectedSegmentedImage'][feature]['data'] == undefined ||
      (this.segmentedImageDetails['selectedSegmentedImage'][feature]['data'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage'][feature]['data'].length == 0)
    ) {
      this.analysisData[feature]['analysisExplored'] = false;
    }
    if (
      this.segmentedImageDetails['selectedSegmentedImage'][tier]['data'] == undefined ||
      (this.segmentedImageDetails['selectedSegmentedImage'][tier]['data'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage'][tier]['data'].length == 0)
    ) {
      this.analysisData[tier]['analysisExplored'] = false;
    }
    if (
      this.segmentedImageDetails['selectedSegmentedImage'][metal]['data'] == undefined ||
      (this.segmentedImageDetails['selectedSegmentedImage'][metal]['data'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage'][metal]['data'].length == 0)
    ) {
      this.analysisData[metal]['analysisExplored'] = false;
    }
    if (
      this.segmentedImageDetails['selectedSegmentedImage'][bubble]['data'] == undefined ||
      (this.segmentedImageDetails['selectedSegmentedImage'][bubble]['data'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage'][bubble]['data'].length == 0)
    ) {
      this.analysisData[bubble]['analysisExplored'] = false;
    }
    if (
      this.segmentedImageDetails['selectedSegmentedImage'][pillaranomaly]['data'] == undefined ||
      (this.segmentedImageDetails['selectedSegmentedImage'][pillaranomaly]['data'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage'][pillaranomaly]['data'].length == 0)
    ) {
      this.analysisData[pillaranomaly]['analysisExplored'] = false;
    }
    if (
      this.segmentedImageDetails['selectedSegmentedImage'][pillarc2c]['data'] == undefined ||
      (this.segmentedImageDetails['selectedSegmentedImage'][pillarc2c]['data'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage'][pillarc2c]['data'].length == 0)
    ) {
      this.analysisData[pillarc2c]['analysisExplored'] = false;
    }
    if (
      this.segmentedImageDetails['selectedSegmentedImage'][metalvoids]['data'] == undefined ||
      (this.segmentedImageDetails['selectedSegmentedImage'][metalvoids]['data'] != undefined &&
        this.segmentedImageDetails['selectedSegmentedImage'][metalvoids]['data'].length == 0)
    ) {
      this.analysisData[metalvoids]['analysisExplored'] = false;
    }
  }

  resetBackupLayers() {
    this.backupWorkflow["preprocessingWorkflowFeatures"] = [];
    this.backupWorkflow["segmentationWorkflowFeatures"] = [];
    this.backupWorkflow["postprocessingWorkflowFeatures"] = [];
  }

  ngOnDestroy() {
    // prevent memory leak when component destroyed
    this.preProcessingLayerSubscription.unsubscribe();
    this.segmentaionLayerSubscription.unsubscribe();
    this.postProcessingLayerSubscription.unsubscribe();
    this.triggerCloseWorkflowSubcription.unsubscribe();
  }

  backToFolders() {
    let Obj = {
      "callCroppedImages": true,
      "tab": 0
    }
    this.selectedFirstTab.emit(Obj)
  }

  updateImageMasking(flag: boolean) {

    var payload = {
      "categorized_data_id": this.selectedFolderId,
      "image": this.segmentedImageDetails['selectedSegmentedImage']['path'],
      "category": this.segmentedImageDetails['selectedSegmentedImage']['category'],
      "old_coordinates": this.selectedMask['old_coordinates'],
      "new_coordinates": this.selectedMask['new_coordinates'],
      "apply_change": flag,
      "mask_name": this.selectedMask.mask_name
    }
    this.apiCall = true;
    this.imageAnalysisService.updateImageMasking(payload).then((response) => {
      if (response) {
        this.redrawMasks();
        this.applySelectedMask = false;
        this.maskApplied = true;
        this.toaster.success('Image masking updated successfully', '', {
          positionClass: 'custom-toast-position',
        });

        this.closeCropTab(false);
        if (this.cropImageExp) {
          this.cropImageExp.close();
        }

        this.getSelectedCropImage(true);

      } else {
        this.apiCall = false;
        this.toaster.error('Failed to create image masking', '', {
          positionClass: 'custom-toast-position',
        });
      }
    })
      .catch((error) => {
        this.apiCall = false;
        console.error('An error occurred while creating image masking', error);
        this.toaster.error(error, '', {
          positionClass: 'custom-toast-position',
        });
      });
  }



  openCropImageTab(cropChanged: boolean) {
    this.segAndCropTabSelected = 1;
    setTimeout(() => {
      this.initializeCanvas();
    }, 100);
    this.getSelectedCropImage(false);
  }

  changeSelectedMask(mask: any) {
    this.selectedMask = mask;

    if (this.selectedMask['old_coordinates']) {
      this.selectedMask['new_coordinates'] = { ...this.selectedMask['old_coordinates'] };
    } else {
      this.selectedMask['old_coordinates'] = { ...mask.coordinates };
      this.selectedMask['new_coordinates'] = { ...mask.coordinates };
    }

    this.applySelectedMask = true;
    this.redrawCanvas();
    this.cropImageBasedOnMask();
  }



  initializeCanvas() {
    const canvas = this.maskCanvasElement.nativeElement;
    this.ctx = canvas.getContext('2d');

    if (!this.ctx) {
      console.error('Failed to get canvas context');
    }

    canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
    canvas.addEventListener('mouseleave', this.handleMouseLeave.bind(this));
    canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
    document.addEventListener('click', this.handleOutsideClick.bind(this));
    this.loadImage();
    this.redrawCanvas();
  }

  loadImage() {
    if (!this.segmentedImageDetails['selectedSegmentedImage']['manual_image']) return;

    let path = this.segmentedImageDetails['selectedSegmentedImage']['manual_image'];
    this.imageAnalysisService
      .getIndividualImageContent({ path: path, name: this.getImageName(path) })
      .subscribe(
        (result) => {
          this.apiCall = false
          this.imageCache = new Image();
          this.imageCache.src = result;
          this.imageCache.onload = () => {
            const canvas = this.maskCanvasElement.nativeElement;
            canvas.width = 700;
            canvas.height = 700;
            this.redrawCanvas();
          };

          this.imageCache.onerror = (error: any) => {
            console.error('Failed to load image:', error);
          };
        },
        (error) => {
          this.apiCall = false
          console.error('Error fetching image content:', error);
        },
      );

  }

  handleMouseDown(event: MouseEvent) {
    const { clickX, clickY } = this.calculateClickCoordinates(event);

    if (this.selectedMask) {
      const { x1, y1, x2, y2 } = this.getMaskCoordinates(this.selectedMask);

      this.resizingSide = this.getResizingSide(clickX, clickY, x1, y1, x2, y2);

      if (this.resizingSide) {
        this.resizing = true;
        this.applySelectedMask = true;
      } else if (this.isInsideMask(clickX, clickY, x1, y1, x2, y2)) {
        this.dragging = true;
        this.offsetX = clickX - x1;
        this.offsetY = clickY - y1;
        this.highlightMask();
      }
      window.addEventListener('mousemove', this.handleMouseMove);
      window.addEventListener('mouseup', this.handleMouseUp);
    }
  }


  handleMouseMove = (event: MouseEvent) => {
    const canvas = this.maskCanvasElement.nativeElement;
    const { clickX, clickY } = this.calculateClickCoordinates(event);

    if (this.selectedMask) {
      const { x1, y1, x2, y2 } = this.getMaskCoordinates(this.selectedMask);

      if (this.dragging || this.resizing) {
        // Existing functionality for moving or resizing the mask
        if (this.resizing) {
          this.resizeMask(clickX, clickY, canvas);
          // Update the cursor during resizing
          this.updateCursor(this.resizingSide, canvas);
        } else if (this.dragging) {
          let newX1 = ((clickX - this.offsetX) / canvas.width) * 100;
          let newY1 = ((clickY - this.offsetY) / canvas.height) * 100;

          newX1 = Math.max(0, Math.min(newX1, 100 - this.selectedMask.coordinates.w));
          newY1 = Math.max(0, Math.min(newY1, 100 - this.selectedMask.coordinates.h));

          // Continue using coordinates for moving the mask
          this.selectedMask.coordinates.x1 = newX1;
          this.selectedMask.coordinates.y1 = newY1;
          this.selectedMask.coordinates.x2 = newX1 + this.selectedMask.coordinates.w;
          this.selectedMask.coordinates.y2 = newY1 + this.selectedMask.coordinates.h;

          // Update new_coordinates independently without affecting the original coordinates
          this.selectedMask.new_coordinates = {
            x1: newX1,
            y1: newY1,
            x2: newX1 + this.selectedMask.coordinates.w,
            y2: newY1 + this.selectedMask.coordinates.h,
            w: this.selectedMask.coordinates.w,
            h: this.selectedMask.coordinates.h
          };

          // Set the cursor to move during dragging
          canvas.style.cursor = 'move';
        }

        this.redrawCanvas();
        this.cropImageBasedOnMask();
      } else {
        // Update the cursor when not dragging or resizing
        const resizingSide = this.getResizingSide(clickX, clickY, x1, y1, x2, y2);

        if (resizingSide) {
          // Cursor is over a resize handle
          this.updateCursor(resizingSide, canvas);
        } else if (this.isInsideMask(clickX, clickY, x1, y1, x2, y2)) {
          // Cursor is inside the mask
          canvas.style.cursor = 'move';
        } else {
          // Cursor is outside the mask
          canvas.style.cursor = 'default';
        }
      }
    } else {
      // No mask is selected
      canvas.style.cursor = 'default';
    }
  };

  updateCursor(resizingSide: string | null, canvas: HTMLCanvasElement) {
    switch (resizingSide) {
      case 'top-left':
      case 'bottom-right':
        canvas.style.cursor = 'nwse-resize';
        break;
      case 'top-right':
      case 'bottom-left':
        canvas.style.cursor = 'nesw-resize';
        break;
      case 'top':
      case 'bottom':
        canvas.style.cursor = 'ns-resize';
        break;
      case 'left':
      case 'right':
        canvas.style.cursor = 'ew-resize';
        break;
      default:
        canvas.style.cursor = 'default';
        break;
    }
  }








  handleMouseUp = () => {
    this.dragging = false;
    this.resizing = false;
    this.resizingSide = null;
    const canvas = this.maskCanvasElement.nativeElement;
    canvas.style.cursor = 'default';

    if (this.maskCanvasElement) {
      window.removeEventListener('mousemove', this.handleMouseMove);
      window.removeEventListener('mouseup', this.handleMouseUp);
    }
  };


  handleMouseLeave(event: MouseEvent) {
    this.handleMouseUp();
    const canvas = this.maskCanvasElement.nativeElement;
    canvas.style.cursor = 'default';
  }


  handleOutsideClick(event: MouseEvent) {
    if (this.maskCanvasElement && this.maskCanvasElement.nativeElement) {
      const canvas = this.maskCanvasElement.nativeElement;
      if (!canvas.contains(event.target as Node)) {
        this.handleMouseUp();
      }
    }
  }

  resizeMask(clickX: number, clickY: number, canvas: HTMLCanvasElement) {
    const mask = this.selectedMask;

    // Resize the mask using original coordinates
    switch (this.resizingSide) {
      case 'top':
        mask.coordinates.y1 = (clickY / canvas.height) * 100;
        break;
      case 'bottom':
        mask.coordinates.y2 = (clickY / canvas.height) * 100;
        mask.coordinates.h = mask.coordinates.y2 - mask.coordinates.y1;
        break;
      case 'left':
        mask.coordinates.x1 = (clickX / canvas.width) * 100;
        break;
      case 'right':
        mask.coordinates.x2 = (clickX / canvas.width) * 100;
        mask.coordinates.w = mask.coordinates.x2 - mask.coordinates.x1;
        break;
      case 'top-left':
        mask.coordinates.x1 = (clickX / canvas.width) * 100;
        mask.coordinates.y1 = (clickY / canvas.height) * 100;
        break;
      case 'top-right':
        mask.coordinates.x2 = (clickX / canvas.width) * 100;
        mask.coordinates.y1 = (clickY / canvas.height) * 100;
        mask.coordinates.w = mask.coordinates.x2 - mask.coordinates.x1;
        break;
      case 'bottom-left':
        mask.coordinates.x1 = (clickX / canvas.width) * 100;
        mask.coordinates.y2 = (clickY / canvas.height) * 100;
        mask.coordinates.h = mask.coordinates.y2 - mask.coordinates.y1;
        break;
      case 'bottom-right':
        mask.coordinates.x2 = (clickX / canvas.width) * 100;
        mask.coordinates.y2 = (clickY / canvas.height) * 100;
        mask.coordinates.w = mask.coordinates.x2 - mask.coordinates.x1;
        mask.coordinates.h = mask.coordinates.y2 - mask.coordinates.y1;
        break;
    }

    // Ensure the mask stays within canvas bounds
    mask.coordinates.x1 = Math.max(0, mask.coordinates.x1);
    mask.coordinates.y1 = Math.max(0, mask.coordinates.y1);
    mask.coordinates.x2 = Math.min(100, mask.coordinates.x2);
    mask.coordinates.y2 = Math.min(100, mask.coordinates.y2);
    mask.coordinates.w = mask.coordinates.x2 - mask.coordinates.x1;
    mask.coordinates.h = mask.coordinates.y2 - mask.coordinates.y1;

    // Update new_coordinates with the resized values without affecting original coordinates
    mask.new_coordinates = {
      x1: mask.coordinates.x1,
      y1: mask.coordinates.y1,
      x2: mask.coordinates.x2,
      y2: mask.coordinates.y2,
      w: mask.coordinates.w,
      h: mask.coordinates.h
    };
  }



  getResizingSide(clickX: number, clickY: number, x1: number, y1: number, x2: number, y2: number): string | null {
    if (Math.abs(clickX - x1) < this.RESIZE_MARGIN && Math.abs(clickY - y1) < this.RESIZE_MARGIN) {
      return 'top-left';
    } else if (Math.abs(clickX - x2) < this.RESIZE_MARGIN && Math.abs(clickY - y1) < this.RESIZE_MARGIN) {
      return 'top-right';
    } else if (Math.abs(clickX - x1) < this.RESIZE_MARGIN && Math.abs(clickY - y2) < this.RESIZE_MARGIN) {
      return 'bottom-left';
    } else if (Math.abs(clickX - x2) < this.RESIZE_MARGIN && Math.abs(clickY - y2) < this.RESIZE_MARGIN) {
      return 'bottom-right';
    } else if (Math.abs(clickY - y1) < this.RESIZE_MARGIN && clickX > x1 && clickX < x2) {
      return 'top';
    } else if (Math.abs(clickY - y2) < this.RESIZE_MARGIN && clickX > x1 && clickX < x2) {
      return 'bottom';
    } else if (Math.abs(clickX - x1) < this.RESIZE_MARGIN && clickY > y1 && clickY < y2) {
      return 'left';
    } else if (Math.abs(clickX - x2) < this.RESIZE_MARGIN && clickY > y1 && clickY < y2) {
      return 'right';
    }
    return null;
  }

  isInsideMask(clickX: number, clickY: number, x1: number, y1: number, x2: number, y2: number): boolean {
    const isInside = clickX >= x1 && clickX <= x2 && clickY >= y1 && clickY <= y2;
    return isInside;
  }

  calculateClickCoordinates(event: MouseEvent) {
    const canvas = this.maskCanvasElement.nativeElement;
    const rect = canvas.getBoundingClientRect();

    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const clickX = (event.clientX - rect.left) * scaleX;
    const clickY = (event.clientY - rect.top) * scaleY;

    return { clickX, clickY };
  }

  redrawCanvas() {
    const canvas = this.maskCanvasElement.nativeElement;
    this.ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (this.imageCache) {
      this.ctx.drawImage(this.imageCache, 0, 0, canvas.width, canvas.height);
    }
    this.redrawMasks();
  }

  drawCorners(x1: number, y1: number, width: number, height: number) {
    const cornerLength = 10;
    this.ctx.save();
    this.ctx.strokeStyle = 'red';
    this.ctx.lineWidth = 4;
    this.ctx.beginPath();
    this.ctx.moveTo(x1, y1);
    this.ctx.lineTo(x1 + cornerLength, y1);
    this.ctx.lineTo(x1, y1 + cornerLength);
    this.ctx.stroke();

    this.ctx.moveTo(x1 + width, y1);
    this.ctx.lineTo(x1 + width - cornerLength, y1);
    this.ctx.lineTo(x1 + width, y1 + cornerLength);
    this.ctx.stroke();

    this.ctx.moveTo(x1, y1 + height);
    this.ctx.lineTo(x1 + cornerLength, y1 + height);
    this.ctx.lineTo(x1, y1 + height - cornerLength);
    this.ctx.stroke();

    this.ctx.moveTo(x1 + width, y1 + height);
    this.ctx.lineTo(x1 + width - cornerLength, y1 + height);
    this.ctx.lineTo(x1 + width, y1 + height - cornerLength);
    this.ctx.stroke();

    this.ctx.restore();
  }

  drawMaskLabel(x: number, y: number, label: string) {
    this.ctx.save();
    this.ctx.fillStyle = '#000000';
    this.ctx.font = '16px Arial';
    this.ctx.fillText(label, x + 5, y + 20);
    this.ctx.restore();
  }

  addAlpha(hex: string, alpha: number): string {
    hex = hex.replace(/^#/, '');
    let r = parseInt(hex.substring(0, 2), 16);
    let g = parseInt(hex.substring(2, 4), 16);
    let b = parseInt(hex.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  highlightMask() {
    this.applySelectedMask = true;
    this.redrawCanvas();
  }

  clearHighlight() {
    this.applySelectedMask = false;
    this.redrawCanvas();
  }

  redrawMasks() {
    const canvas = this.maskCanvasElement.nativeElement;
    if (!this.ctx) return;

    this.ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (this.imageCache) {
      this.ctx.drawImage(this.imageCache, 0, 0, canvas.width, canvas.height);
    }

    if (this.selectedMask) {
      const { x1, y1, width, height } = this.getMaskCoordinates(this.selectedMask);

      this.ctx.fillStyle = this.addAlpha('#1A7A7F', 0.3);
      this.ctx.fillRect(x1, y1, width, height);

      if (this.applySelectedMask) {
        this.ctx.save();
        this.ctx.strokeStyle = 'red';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 3]);
        this.ctx.strokeRect(x1, y1, width, height);
        this.ctx.restore();
      }

      this.drawCorners(x1, y1, width, height);
      this.drawMaskLabel(x1, y1, this.selectedMask.mask_name);
    }
  }
  cropImageBasedOnMask() {
    if (!this.selectedMask || !this.imageCache) return;
    const { x1, y1, width, height } = this.getMaskCoordinates(this.selectedMask);
    const canvas = this.maskCanvasElement.nativeElement;

    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');

    if (!tempCtx) {
      console.error('Failed to get 2D context for cropping.');
      return;
    }

    tempCanvas.width = width;
    tempCanvas.height = height;
    tempCtx.drawImage(
      this.imageCache,
      (x1 / canvas.width) * this.imageCache.width,
      (y1 / canvas.height) * this.imageCache.height,
      (width / canvas.width) * this.imageCache.width,
      (height / canvas.height) * this.imageCache.height,
      0,
      0,
      tempCanvas.width,
      tempCanvas.height
    );
    const croppedImageUrl = tempCanvas.toDataURL();
    this.imageCropTabObj['tempImage_url'] = croppedImageUrl;
    this.redrawMaskedImage();
  }

  redrawMaskedImage() {
    const maskedImageElement = document.querySelector('.masked-image') as HTMLImageElement;
    if (maskedImageElement && this.imageCropTabObj['tempImage_url']) {
      maskedImageElement.src = this.imageCropTabObj['tempImage_url'];
    }
  }

  getMaskCoordinates(mask: any) {
    const canvas = this.maskCanvasElement.nativeElement;

    const x1 = (mask!.coordinates.x1 / 100) * canvas.width;
    const y1 = (mask!.coordinates.y1 / 100) * canvas.height;
    const width = (mask!.coordinates.w / 100) * canvas.width;
    const height = (mask!.coordinates.h / 100) * canvas.height;

    const x2 = x1 + width;
    const y2 = y1 + height;

    return { x1, y1, x2, y2, width, height };
  }

  ngAfterViewInit() {
    // Trigger change detection after view initialization
    this.cdr.detectChanges();
  }

  goToCleanUpPage() {
    this.activatedRoute.queryParams.subscribe((params) => {
      this.datasetName = params['datasetName']
    });
    let queryParams = {
      datasetName: this.datasetName,
      folderId: this.selectedFolderId,
      imagePath: this.segmentedImageDetails['selectedSegmentedImage']['path']
    };
    let imageFeatureLink = `sites/${this.configService.SelectedSiteId}/projects/${this.configService.SelectedProjectId}/image-analysis/${this.datasetId}/cleanup`;
    this.router.navigate([imageFeatureLink], {
      queryParams,
    });
  }

  toggleLayer(index: number) {
    if (this.expandedPanelIndex === index) {
      this.expandedPanelIndex = null;
    } else {
      this.expandedPanelIndex = index;
    }
    this.cdr.detectChanges();
  }
}
