import {
  Component,
  ChangeDetectorRef,
  ViewChild,
  ElementRef,
  OnInit,
} from '@angular/core';
import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';
import { ImageAnnotationService } from 'src/app/pages/images/annotate/services/image-annotation.service';
import { ToastrService } from 'ngx-toastr';
import { Router, ActivatedRoute } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { WebSocketService } from 'src/app/services/web-sockets.service';
import { ConfigService } from 'src/app/services/config.service';
import Plotly from 'plotly.js-dist-min';
const plotlyFx = (Plotly as any).Fx;
import { MatSelectChange } from '@angular/material/select';

@Component({
  selector: 'app-image-annotate',
  templateUrl: './annotate.component.html',
  styleUrls: ['./annotate.component.less'],
})
export class ImageAnnotateComponent implements OnInit {
  hasUnsavedChanges: boolean = false;
  noAnnotations: boolean = false;
  SegmentedPanel: boolean = false;
  imageSelectContainerExpanded: boolean = false;
  Editing: boolean = false;
  drawAnnotaion: boolean = false;

  opacitySlider: any = {
    connect: 'lower',
    start: 100,
    step: 1,
    tooltips: false,
    range: {
      min: 1,
      max: 100,
    },
    behaviour: 'tap',
  };
  opacityValue = 100;
  selectedTool: string = 'bounding-box';
  colors: any = '';
  test: any;
  oldAnnotationName: any;
  selectObject: any = {};
  imageDisplayUrl = '/imageAnnotation/showImage?file=';
  serviceUrlToShowHTMLFIle = '/imageAnnotation/loadInteractiveFile?file=';
  annotations: any = [];
  labeloptionList: any = [
    {
      title: 'View All',
      selected: false,
      labelOptions: [
        {
          title: 'Pillar',
          color: 'text-blue',
          style: '#1BBEE5',
          selected: false,
        },
        {
          title: 'Bubble',
          color: 'text-pink',
          style: '#EF1CCD',
          selected: false,
        },
        {
          title: 'Tier',
          color: 'text-green',
          style: '#08b90f',
          selected: false,
        },
        {
          title: 'Metal',
          color: 'text-orange',
          style: '#fe640d',
          selected: false,
        },
        {
          title: 'Scalebar',
          color: 'text-red',
          style: '#CB1313',
          selected: false,
        },
        { title: 'Custom', color: '', style: '#eaeaea', selected: false },
      ],
    },
  ];
  objectTypeIcons: any = {
    circle: 'select-elipse-alt',
    'scale-bar': 'scale-bar',
    polygon: 'select-polygon-alt',
    'bounding-box': 'select-box-alt',
    point: 'select-point-alt',
  };
  selectedAnnotation: any = {};
  selectedShape: any = {};
  currentProject: any;
  currentUser: any;
  dataset_id: any;
  apiCall = false;
  datasetDetails: any;
  selectedFolder: any = {};
  displayImages: any;
  selectedImage: any = {};
  @ViewChild('annotatecanvas') public annotatecanvas!: ElementRef;
  @ViewChild('imageContainer') imageContainer!: ElementRef;
  datasetName: string = '';
  resizing: boolean = false;
  scope_canvas: any = {
    rect: {
      x1: 0,
      y1: 0,
      x2: 0,
      y2: 0,
    },
    index: 0,
    drag: false,
    multipleRectangle: [],
    height: 500,
    width: 500,
    last: {},
  };
  datasetAnnotations: any = [];
  foldersList: any = [];
  current_shape_index: any = null;
  is_dragging: boolean = false;
  buttonEnabled: boolean = false;
  annotationVisible: boolean = true;
  menuItem: any;
  startX: any;
  startY: any;
  offsetX: any;
  offsetY: any;
  ShapeAxis: any;
  clickedFlag: boolean = false;
  canvasElement: any;
  image: any;
  showSpinner: boolean = false;
  mouseX: any;
  mouseY: any;
  dragTL = false;
  dragTR = false;
  dragBL = false;
  dragBR = false;
  drag = false;
  filteredAnnotations: any = [];
  // display_folder_type = 0;
  segmentVisSelected = 'solid,Black/white (default),Black/white (default)';
  segmentedLabelsList: any = [];
  segmentedLabelsFilterList: any = [];
  @ViewChild('segmentedinteractive') public segmentedinteractive!: ElementRef;
  visualization: any = {};
  assignLabel: string = '';
  selectBoxView: boolean = false;
  selectedBoxObjects: any = [];
  customNewLabel: string = '';
  drawSegmentBoxRange: any = {};
  changeSegmentationType: boolean = false;
  assignLabelPositionParams: any = { left: '0px', top: '0px' };
  filteredSegmentedObjects: any = [];
  datasetId: string = '';
  closeEnough: any;
  isCollapsed: boolean = false;
  annotation_type: string = 'raw';
  filteredSegmentationData: any;

  constructor(
    private router: Router,
    private activatedRoute: ActivatedRoute,
    private imageAnalysisService: ImageAnalysisService,
    private toaster: ToastrService,
    private dialog: MatDialog,
    public webSocketService: WebSocketService,
    private configService: ConfigService,
    private imageAnnotationService: ImageAnnotationService,
    private changeDetectorRef: ChangeDetectorRef,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    if (this.activatedRoute) {
      this.activatedRoute.queryParams.subscribe((params) => {
        this.datasetName = params['datasetName'];
      });

      this.activatedRoute.params.subscribe((params) => {
        this.datasetId = params['datasetId'];
      });
      this.getDistinctLabels();
      this.getSavedAnnotations();
      this.processExpirementalData();
    }
  }

  goToCleanUpPage() {
    if(this.image && this.image['path']){
      let queryParams = {
        datasetName: this.datasetName,
        folderId: this.selectedFolder._id,
        imagePath: this.image['path']
      };
      let imageFeatureLink = `sites/${this.configService.SelectedSiteId}/projects/${this.configService.SelectedProjectId}/image-analysis/${this.datasetId}/cleanup`;
      this.router.navigate([imageFeatureLink], {
        queryParams,
      });
    }
  }

  collapseFolderPanel() {
    this.isCollapsed = !this.isCollapsed;
  }
  checkSegmentedAndGetAnnotations() {
    if (this.image && this.image['segmented_img'] != '') {
      this.getSegmentedImageAnnotations();
    }
  }

  processExpirementalData() {
    this.apiCall = true;
    this.imageAnalysisService
      .getCategorizationData(this.datasetId)
      .then((response) => {
        this.apiCall = false;
        if (response) {
          if (response && response['categorization_data']) {
            this.foldersList = response['categorization_data'];
            if (this.foldersList.length) {
              this.foldersList.forEach((element: any, index: number) => {
                this.foldersList[index]['selectedimages'] = element.img_details;
              });
              this.foldersList[0]['leftNavExpanded'] = true;

              this.setSelectedFolder(
                this.foldersList[0]['img_details'][0],
                this.foldersList[0],
              );
            }
          }
        } else {
          this.toaster.error('Failed to fetch the images data', '', {
            positionClass: 'custom-toast-position',
          });
        }
      })
      .catch((error) => {
        console.error('Error fetching mounted drive data:', error);
      });
  }
  selectImage(image: any, folder: any) {
    this.clickedFlag = true;
    this.selectBoxView = false;
    this.image = image;
    this.selectedImage = image;
    this.getImageContent(this.selectedImage, 'image');
    if (this.selectedFolder['folderId'] != folder['folderId']) {
      this.selectedFolder = folder;
    }

    // for (var i = 0; i < folder['selectedimages'].length; i++) {
    //   if(folder['selectedimages'][i]['image'] === image['image']){
    //     folder['selectedimages'][i]['selected'] = true;
    //   }else{
    //     folder['selectedimages'][i]['selected'] = false;
    //   }
    // }
    if (!this.SegmentedPanel) {
      setTimeout((val: any) => {
        this.setImageForAnnotation();
        this.showSelectedImageAnnotations();
        this.changeParentEvent(true);
        this.showSpinner = false;
      }, 2000);
    } else {
      this.getSegmentedImageAnnotations();
    }
  }
  leftMenuImageClick(event: any) {
    this.selectedFolder = event.folder;
    this.image = event.image;
    this.selectImage(this.image, this.selectedFolder);
  }
  setSelectedFolder(image: any, folder: any) {
    this.selectedFolder = folder;
    this.selectedFolder['img_details'][0]['selected'] = true;
    this.image = image;
    this.selectImage(this.image, this.selectedFolder);
  }
  ngAfterViewInit() { }

  ngOnDestroy() { }

  onResize(event?: Event) { }
  zoomInPlot() {
    let zoomInBtn = document.querySelector(
      'a[data-attr="zoom"][data-val="in"]',
    ) as HTMLElement;
    zoomInBtn.click();
  }
  zoomOutPlot() {
    let zoomOutBtn = document.querySelector(
      'a[data-attr="zoom"][data-val="out"]',
    ) as HTMLElement;
    zoomOutBtn.click();
  }

  changeVisualization(event: any) {
    this.changeSegmentationType = true;
    this.getSegmentedImageAnnotations();
  }
  getAnnotationObjectIcon(type: any) {
    return '#' + this.objectTypeIcons[type];
  }

  getAnnotationObjectLabelColor(title: string, annotation_id: string) {
    if (title && title != '') {
      for (var i = 0; i < this.annotations.length; i++) {
        if (this.annotations[i]['annotation_id'] == annotation_id) {
          return this.annotations[i]['color'];
        }
      }
    } else {
      return '';
    }
  }

  setSelectedTool(value: string) {
    this.selectedTool = value;
  }

  changeAnnotationObject(option: any) {
    for (var i = 0; i < this.annotations.length; i++) {
      if (
        this.annotations[i].annotation_id == this.selectObject.annotation_id
      ) {
        this.annotations[i].label = option.title;
        this.annotations[i].color = option.style;
        let reqData = {
          annotation_id: this.annotations[i]._id,
          label: this.annotations[i].label,
          color: this.annotations[i].color,
        };
        this.imageAnnotationService.changeAnnotationLabel(reqData).then((response) => {
          if (response) {
            if (response['status']) {
              this.toaster.success('Updated successfully', '', {
                positionClass: 'custom-toast-position',
              });
              this.redrawAnnotations(true)
              this.changeDetectorRef.detectChanges();
            }
          } else {
            this.toaster.error('Failed to update label', '', {
              positionClass: 'custom-toast-position',
            });
          }
        })
          .catch((error) => {
            console.error('Error fetching mounted drive data:', error);
            this.toaster.error('Failed to update label', '', {
              positionClass: 'custom-toast-position',
            });
          });
      }
    }
    ;
  }

  expandImageSelector() {
    this.imageSelectContainerExpanded = !this.imageSelectContainerExpanded;
  }

  goToPreview() {
    let viewPage = '/curation/dataset-preview';
    this.router.navigate([viewPage]);
  }

  changeAnnotationName(
    _event: any,
    annotation_name: string,
    annotation_id: string,
  ) {
    let reqData = {
      annotation_id: annotation_id,
      annotation_name: annotation_name,
    };
    this.imageAnnotationService
      .changeAnnotationName(reqData)
      .then((response) => {
        if (response) {
          this.Editing = false;
          this.toaster.success(response['msg'], '', {
            positionClass: 'custom-toast-position',
          });

          this.redrawAnnotations(true);
        } else {
          this.toaster.error('Failed to update name', '', {
            positionClass: 'custom-toast-position',
          });
        }
        this.apiCall = false;
      })
      .catch((error) => {
        this.apiCall = false;
        console.error('Failed to update name:', error);
        this.toaster.error('Failed to update name', '', {
          positionClass: 'custom-toast-position',
        });
      });
  }

  onChangeColor(color: any) {
    let index = this.labeloptionList[0].labelOptions.findIndex(
      (x: any) => x.title === 'Custom',
    );
    this.labeloptionList[0].labelOptions[index]['style'] = color;
  }

  changeParentEvent(flag: boolean) {
    for (var i = 0; i < this.labeloptionList.length; i++) {
      if (flag) {
        this.labeloptionList[i].selected = false;
      }
      for (var j = 0; j < this.labeloptionList[i].labelOptions.length; j++) {
        if (flag) {
          this.labeloptionList[i].labelOptions[j].selected = false;
        } else {
          if (this.labeloptionList[i].selected) {
            this.labeloptionList[i].labelOptions[j].selected = true;
          } else {
            this.labeloptionList[i].labelOptions[j].selected = false;
          }
        }
        if (
          i == this.labeloptionList.length - 1 &&
          j == this.labeloptionList[i].labelOptions.length - 1
        ) {
          this.changeType();
        }
      }
    }
  }
  changeType() {
    var selectedOptionList = this.labeloptionList[0].labelOptions
      .filter((option: any) => option.selected)
      .map((opt: any) => opt['title']);
    let filterArray: any = [];
    if (selectedOptionList.length > 0) {
      for (var i = 0; i < this.annotations.length; i++) {
        if (selectedOptionList.indexOf(this.annotations[i]['label']) != -1) {
          filterArray.push(this.annotations[i]);
        }
        if (i == this.annotations.length - 1) {
          this.filteredAnnotations = filterArray;
        }
      }
    } else {
      this.filteredAnnotations = this.annotations;
    }
    setTimeout(() => {
      this.redrawAnnotations(true);
    }, 100);
  }

  showSelectedImageAnnotations() {
    const ctx = this.scope_canvas['ctx'];
    if (ctx) {
      ctx.clearRect(0, 0, this.scope_canvas['canvas'].width, this.scope_canvas['canvas'].height);
      ctx.drawImage(this.scope_canvas['image'], 0, 0, this.scope_canvas['width'], this.scope_canvas['height']);
    }

    const imageAnnotations = this.datasetAnnotations.filter(
      (val: any) =>
        val['sample_id'] === this.selectedFolder['folderId'] &&
        val['image_path'] === this.selectedImage['image'],
    );

    this.annotations.length = 0;
    this.filteredAnnotations.length = 0;

    if (imageAnnotations.length > 0) {
      this.annotations.push(...imageAnnotations);
      this.annotations.sort((a: any, b: any) => a.annotation_id - b.annotation_id);
      let maxId = 0;
      for (let annotation of this.annotations) {
        if (annotation.annotation_id > maxId) {
          maxId = annotation.annotation_id;
        }
      }
      this.scope_canvas['index'] = maxId;
      this.filteredAnnotations = [...this.annotations];
      this.redrawAnnotations(true);

    } else {
      this.scope_canvas['index'] = 0;
    }
    this.changeDetectorRef.detectChanges();
  }


  getSegmentedImageAnnotations() {
    if (this.image) {
      this.filteredSegmentedObjects = [];
      let segmented_opt = this.segmentVisSelected.split(',');
      let imagePath = this.image['path'].split('.')[0];
      var objectTobeSent = {
        name: imagePath,
        visualization_details: {
          visualization: segmented_opt[0],
          color: segmented_opt[1],
        },
      };
      this.showSpinner = true;

      this.imageAnnotationService.getSegmentedAnnotations(objectTobeSent).then((response) => {
        this.showSpinner = false;
        this.changeSegmentationType = false;
        if (response) {
          if (response['data']) {
            let segmented_annotation = JSON.parse(response['data']);
            this.image['segmented_annotation'] = {
              object_labels: JSON.parse(segmented_annotation['object_labels']),
              interactive_fig_json_data: JSON.parse(
                segmented_annotation['interactive_fig_json_data'],
              ),
              image_annotation_document_id:
                segmented_annotation['image_annotation_document_id'],
            };
            this.image['segmented_annotation']['object_labels'].forEach(
              (label: any) => {
                label['original_name'] = label['Object'];
              },
            );
            this.filteredSegmentationData = this.image['segmented_annotation']['object_labels']

            for (
              var j = 0;
              j <
              this.image['segmented_annotation']['interactive_fig_json_data'][
                'data'
              ].length;
              j++
            ) {
              delete this.image['segmented_annotation'][
                'interactive_fig_json_data'
              ]['data'][j]['name'];
            }
            this.filteredSegmentedObjects =
              this.image['segmented_annotation']['object_labels'];
            setTimeout(() => {
              this.drawInteractiveVisualization();
            }, 100);
          } else {
            this.toaster.error(
              'Unable to generate annotated image. Please try re-applying workflow for this image.',
              '',
              {
                positionClass: 'custom-toast-position',
              },
            );
          }
        } else {
          this.toaster.error('Failed to fetch segmented annotations', '', {
            positionClass: 'custom-toast-position',
          });
        }
        this.apiCall = false;
      })
        .catch((error) => {
          this.apiCall = false;
          this.toaster.error('Failed to fetch segmented annotations', '', {
            positionClass: 'custom-toast-position',
          });
        });
    }
  }
  checkLabelExistsInFilter(label: string) {
    // var exists = this.segmentedLabelsFilterList.filter((option:any) => option.selected).map((opt:any) => opt['title'].toLowerCase()).filter((val:any)=>val==label.toLowerCase());
    // if(exists.length>0){
    //   return true;
    // }else{
    //   return false;
    // }
    return true;
  }
  enableEditAnnotaion(annotation: any) {
    this.selectedAnnotation = annotation;
    this.oldAnnotationName = this.selectedAnnotation.Object;
    this.Editing = true;
  }
  undoChangeAnnotationName(annotation: any) {
    annotation.annotation_name = this.oldAnnotationName;
    this.selectedAnnotation = null;
    this.oldAnnotationName = null;
    this.Editing = false;
  }
  updateAnnotationName(row: any, index: number) {
    this.image['segmented_annotation']['object_labels'][index]['Object'] =
      row['Object'];
    this.updateSegmentedImageAnnotations();
  }

  showToolTipOnHover(event: any, index: number) {
    plotlyFx.hover(this.segmentedinteractive.nativeElement, [
      { curveNumber: index + 1, pointNumber: 0 },
    ]);
  }
  mouseOutRowHideTooltip(event: any) {
    plotlyFx.unhover(this.segmentedinteractive.nativeElement);
  }

  drawInteractiveVisualization() {
    var myPlot = this.segmentedinteractive.nativeElement;
    var config = {
      responsive: true,
      displaylogo: false,
    };
    var plotData = {
      data: [
        this.image['segmented_annotation']['interactive_fig_json_data'][
        'data'
        ][0],
      ],
      layout:
        this.image['segmented_annotation']['interactive_fig_json_data'][
        'layout'
        ],
    };
    var filteredLabels = this.segmentedLabelsFilterList
      .filter((option: any) => option.selected)
      .map((opt: any) => opt['title'].toLowerCase());
    for (
      var i = 0;
      i < this.image['segmented_annotation']['object_labels'].length;
      i++
    ) {
      if (
        filteredLabels.indexOf(
          this.image['segmented_annotation']['object_labels'][i][
            'Label'
          ].toLowerCase(),
        ) != -1
      ) {
        plotData.data.push(
          this.image['segmented_annotation']['interactive_fig_json_data'][
          'data'
          ][i + 1],
        );
      }
    }
    for (var n = 0; n < plotData['data'].length; n++) {
      if (!plotData['data'][n]['hovertemplate'].includes('<extra></extra>')) {
        plotData['data'][n]['hovertemplate'] =
          plotData['data'][n]['hovertemplate'] + '<extra></extra>';
      }
    }
    plotData['layout']['dragmode'] = 'select';
    plotData['layout']['xaxis'] = { visible: false, linewidth: 0 };
    plotData['layout']['yaxis'] = { visible: false, linewidth: 0 };
    plotData['layout']['autosize'] = true;
    plotData['layout']['margin'] = { t: 0, b: 0, r: 0 };
    plotData['layout']['plot_bgcolor'] = 'white';
    this.visualization = Plotly.newPlot(
      myPlot,
      plotData['data'],
      plotData['layout'],
      config,
    );
    myPlot.on('plotly_selected', (e: any) => {
      if (e && e.range) {
        this.objectsLiesUnderBox(e);
      }
    });

    setTimeout(() => { }, 100);
  }
  objectsLiesUnderBox(event: any) {
    var range = event.range;
    var data =
      this.image['segmented_annotation']['interactive_fig_json_data']['data'];
    this.selectedBoxObjects = [];
    for (var i = 0; i < data.length; i++) {
      if (i > 0) {
        var x = this.filterNumbers(data[i]['x'], range.x[0], range.x[1]);
        var y = this.filterNumbers(data[i]['y'], range.y[0], range.y[1]);
        let xPercent = (x!.length / data[i]['x'].length) * 100;
        let yPercent = (y!.length / data[i]['y'].length) * 100;
        if (x!.length > 0 && y!.length > 0 && x!.length == y!.length) {
          this.selectedBoxObjects.push(i - 1);
        } else if (
          x!.length > 0 &&
          y!.length > 0 &&
          xPercent >= 95 &&
          yPercent >= 95
        ) {
          this.selectedBoxObjects.push(i - 1);
        }
      }
      if (i == data.length - 1) {
        if (this.selectedBoxObjects.length > 0) {
          this.selectBoxView = true;
        } else {
          this.selectBoxView = false;
          this.toaster.info('No object found', '', {
            positionClass: 'custom-toast-position',
          });
        }
      }
    }
  }
  onSelectionChange(event: MatSelectChange): void {
    // event.source._element.nativeElement.click(); // Optional: Click on the mat-select to trigger any actions
    // Perform other actions or logic as needed
  }

  addAndAssignCustome() {
    if (this.customNewLabel != '') {
      this.assignLabel = this.customNewLabel;
      this.segmentedLabelsList.push(this.customNewLabel);
      this.segmentedLabelsFilterList.push({
        title: this.assignLabel,
        value: this.assignLabel,
        selected: true,
      });
    }
  }

  assignLabelToSelectedObjects() {
    if (this.selectedBoxObjects.length > 0 && this.assignLabel != '') {
      for (var i = 0; i < this.selectedBoxObjects.length; i++) {
        this.image['segmented_annotation']['object_labels'][
          this.selectedBoxObjects[i]
        ]['Label'] = this.assignLabel;
        var vizLabel =
          this.image['segmented_annotation']['interactive_fig_json_data'][
          'data'
          ][this.selectedBoxObjects[i] + 1];
        var hoverTemplate = vizLabel['hovertemplate'].split('<br>');
        var newHoverTemplate = '';
        for (var n = 0; n < hoverTemplate.length; n++) {
          if (hoverTemplate[n].includes('Label:')) {
            newHoverTemplate =
              newHoverTemplate +
              '<b>Label:' +
              this.image['segmented_annotation']['object_labels'][
              this.selectedBoxObjects[i]
              ]['Label'] +
              '</b><br>';
          } else if (hoverTemplate[n].includes('Object:')) {
            newHoverTemplate =
              newHoverTemplate +
              '<b>Object:' +
              this.image['segmented_annotation']['object_labels'][i]['Object'] +
              '</b><br>';
          } else {
            newHoverTemplate = newHoverTemplate + hoverTemplate[n] + '<br>';
          }
          if (n == hoverTemplate.length - 1) {
            newHoverTemplate = newHoverTemplate.substring(
              0,
              newHoverTemplate.length - 4,
            );
            this.image['segmented_annotation']['interactive_fig_json_data'][
              'data'
            ][this.selectedBoxObjects[i] + 1]['hovertemplate'] =
              newHoverTemplate;
          }
          if (
            i == this.selectedBoxObjects.length - 1 &&
            n == hoverTemplate.length - 1
          ) {
            setTimeout(() => {
              this.updateSegmentedImageAnnotations();
              this.selectBoxView = false; 
            }, 100);
          }
        }
      }
    }
  }

  filterNumbers(points: any, min: number, max: number) {
    var array: any = [];
    if (points.length > 0) {
      for (var m = 0; m < points.length; m++) {
        if (points[m] >= min && points[m] <= max) {
          array.push(points[m]);
        }
        if (m == points.length - 1) {
          return array;
        }
      }
    } else {
      return array;
    }

    return array;
  }
  getDistinctLabels() {
    this.imageAnnotationService
      .getDistinctLabels()
      .then((response) => {
        if (response) {
          this.segmentedLabelsList = response.filter(
            (val: any) =>
              val != 'blank' &&
              val != 'Ignore' &&
              val != 'Other' &&
              val != 'Blank',
          );
          this.segmentedLabelsFilterList = [
            { title: 'Blank', value: 'blank', selected: true },
          ];
          for (var i = 0; i < this.segmentedLabelsList.length; i++) {
            this.segmentedLabelsFilterList.push({
              title: this.segmentedLabelsList[i],
              value: this.segmentedLabelsList[i],
              selected: true,
            });
          }
          this.segmentedLabelsFilterList.push({
            title: 'Other',
            value: 'other',
            selected: true,
          });
          this.segmentedLabelsFilterList.push({
            title: 'Ignore',
            value: 'ignore',
            selected: true,
          });
        } else {
          this.toaster.error('Failed to get labels', '', {
            positionClass: 'custom-toast-position',
          });
        }
        this.apiCall = false;
      })
      .catch((error) => {
        this.apiCall = false;
        console.error('Failed to get labels:', error);
        this.toaster.error('Failed to get labels', '', {
          positionClass: 'custom-toast-position',
        });
      });
  }

  deleteAnnotation(annotation: any) {
    var index = this.filteredAnnotations.findIndex(
      (val: any) => val['annotation_id'] == annotation['annotation_id'],
    );
    if (index != -1) {
      if (this.filteredAnnotations[index]['_id']) {
        var originalIndex = this.datasetAnnotations.findIndex(
          (val: any) => val['_id'] == annotation['_id'],
        );

        this.imageAnnotationService
          .deleteAnnotation(annotation['_id'])
          .then((response) => {
            if (response) {
              this.toaster.success('Annotation Deleted', '', {
                positionClass: 'custom-toast-position',
              });
              this.filteredAnnotations.splice(index, 1);
              this.datasetAnnotations.splice(originalIndex, 1);
              this.scope_canvas['ctx'].clearRect(
                0,
                0,
                this.scope_canvas['width'],
                this.scope_canvas['height'],
              );
              this.scope_canvas['ctx'].drawImage(
                this.scope_canvas['image'],
                0,
                0,
                this.scope_canvas['width'],
                this.scope_canvas['height'],
              );
              this.redrawAnnotations(false);
            } else {
              this.toaster.error('Failed to delete the annotation', '', {
                positionClass: 'custom-toast-position',
              });
            }
            this.apiCall = false;
          })
          .catch((error) => {
            this.apiCall = false;
            console.error('Error fetching mounted drive data:', error);
            this.toaster.error('Failed to delete the annotation', '', {
              positionClass: 'custom-toast-position',
            });
          });
      } else {
        this.scope_canvas['index'] = this.scope_canvas['index'] - 1;
        this.filteredAnnotations.splice(index, 1);
        this.scope_canvas['ctx'].clearRect(
          0,
          0,
          this.scope_canvas['width'],
          this.scope_canvas['height'],
        );
        this.scope_canvas['ctx'].drawImage(
          this.scope_canvas['image'],
          0,
          0,
          this.scope_canvas['width'],
          this.scope_canvas['height'],
        );
        this.redrawAnnotations(false);
      }
    }
  }
  addAlpha(color: string, opacity: number): string {
    // coerce values so ti is between 0 and 1.
    const _opacity = Math.round(Math.min(Math.max(opacity || 1, 0), 1) * 255);
    return color + _opacity.toString(16).toUpperCase();
  }

  redrawAnnotations(_flag: boolean) {
    if (!this.scope_canvas['ctx']) return;
    this.scope_canvas['ctx'].clearRect(
      0,
      0,
      this.scope_canvas['canvas'].width,
      this.scope_canvas['canvas'].height,
    );
    this.scope_canvas['ctx'].drawImage(
      this.scope_canvas['image'],
      0,
      0,
      this.scope_canvas['width'],
      this.scope_canvas['height'],
    );
    for (var i = 0; i < this.filteredAnnotations.length; i++) {
      var coordinates = this.filteredAnnotations[i]['coordinates'];
      if (this.filteredAnnotations[i]['label'] == 'Pillar') {
        this.scope_canvas['ctx'].strokeStyle =
          this.filteredAnnotations[i]['color'];
        this.scope_canvas['ctx'].fillStyle = this.addAlpha(
          this.filteredAnnotations[i]['color'],
          0.2,
        );
      } else if (this.filteredAnnotations[i]['label'] == 'Bubble') {
        this.scope_canvas['ctx'].strokeStyle =
          this.filteredAnnotations[i]['color'];
        this.scope_canvas['ctx'].fillStyle = this.addAlpha(
          this.filteredAnnotations[i]['color'],
          0.3,
        );
      } else if (this.filteredAnnotations[i]['label'] == 'Tier') {
        this.scope_canvas['ctx'].strokeStyle =
          this.filteredAnnotations[i]['color'];
        this.scope_canvas['ctx'].fillStyle = this.addAlpha(
          this.filteredAnnotations[i]['color'],
          0.4,
        );
      } else if (this.filteredAnnotations[i]['label'] == 'Metal') {
        this.scope_canvas['ctx'].strokeStyle =
          this.filteredAnnotations[i]['color'];
        this.scope_canvas['ctx'].fillStyle = this.addAlpha(
          this.filteredAnnotations[i]['color'],
          0.3,
        );
      } else if (this.filteredAnnotations[i]['label'] == 'Scalebar') {
        this.scope_canvas['ctx'].strokeStyle =
          this.filteredAnnotations[i]['color'];
        this.scope_canvas['ctx'].fillStyle = this.addAlpha(
          this.filteredAnnotations[i]['color'],
          0.3,
        );
      } else if (this.filteredAnnotations[i]['label'] == 'Custom') {
        this.scope_canvas['ctx'].strokeStyle =
          this.filteredAnnotations[i]['color'];
        this.scope_canvas['ctx'].fillStyle = this.addAlpha(
          this.filteredAnnotations[i]['color'],
          0.4,
        );
      } else {
        this.scope_canvas['ctx'].strokeStyle = '#ffffff';
        this.scope_canvas['ctx'].fillStyle = 'rgba(255, 255, 255, 0.66)';
      }
      this.scope_canvas['ctx'].fillRect(
        coordinates['x1'],
        coordinates['y1'],
        coordinates['x2'],
        coordinates['y2'],
      );
      this.scope_canvas['ctx'].strokeRect(
        coordinates['x1'],
        coordinates['y1'],
        coordinates['x2'],
        coordinates['y2'],
      );
      this.scope_canvas['ctx'].font = '16px Comic Sans MS';
      this.scope_canvas['ctx'].fillStyle = 'white';
      this.scope_canvas['ctx'].textAlign = 'middle';
      this.scope_canvas['ctx'].textBaseline = 'bottom';
      this.scope_canvas['ctx'].fillText(
        this.filteredAnnotations[i]['annotation_name'],
        coordinates['x1'],
        coordinates['y1'],
        coordinates['x2'],
        coordinates['y2'],
      );
      this.drawHandles(
        coordinates['x1'],
        coordinates['y1'],
        coordinates['x2'],
        coordinates['y2'],
        this.closeEnough,
      );
    }
  }

  drawHandles(
    startX: number,
    startY: number,
    w: number,
    h: number,
    closeEnough: number,
  ) {
    this.drawCircle(startX, startY, closeEnough);
    this.drawCircle(startX + w, startY, closeEnough);
    this.drawCircle(startX + w, startY + h, closeEnough);
    this.drawCircle(startX, startY + h, closeEnough);
  }

  drawCircle(x: number, y: number, radius: number) {
    this.scope_canvas['ctx'].fillStyle = '#FF0000';
    this.scope_canvas['ctx'].beginPath();
    this.scope_canvas['ctx'].arc(x, y, radius, 0, 2 * Math.PI);
    this.scope_canvas['ctx'].fill();
  }
  getImageContent(obj: any, key: string) {
    let path = obj[key];
    if (path && path != '') {
      this.imageAnalysisService
        .getIndividualImageContent({ path: path, name: '' })
        .subscribe(
          (result) => {
            let newPathKey = key + '_url';
            obj[newPathKey] = '';
            obj[newPathKey] = result;
          },
          (error) => {
            console.error('Error fetching image content:', error);
          },
        );
    }
  }

  changeFilterSegLabelType() {
    const filteredObjects = this.filteredSegmentationData.filter((obj: { Label: any; }) => {
      return this.segmentedLabelsFilterList.some((label: { selected: any; value: any; }) => label.selected && label.value === obj.Label);
    });

    this.image['segmented_annotation']['object_labels'] = filteredObjects.length > 0 ? filteredObjects : [];
    this.drawInteractiveVisualization();
  }

  objectLabelsExists() {
    if (
      this.image &&
      'segmented_annotation' in this.image &&
      this.image['segmented_annotation']
    ) {
      return 'object_labels' in this.image['segmented_annotation']
        ? true
        : false;
    } else {
      return false;
    }
  }
  interactivePathExists() {
    if (this.image && 'segmented_annotation' in this.image) {
      return 'interactive_fig_json_data' in this.image['segmented_annotation']
        ? true
        : false;
    } else {
      return false;
    }
  }

  setImageForAnnotation(): void {
    if (!this.SegmentedPanel && this.selectedImage['image_url']) {
      const canvas: HTMLCanvasElement = this.annotatecanvas.nativeElement;
      const ctx: any = canvas!.getContext('2d');

      this.scope_canvas['canvas'] = canvas;
      this.scope_canvas['ctx'] = ctx;

      this.cleanupCanvasEventListeners(canvas);

      const image = new Image();
      this.scope_canvas['image'] = image;
      this.scope_canvas['image'].src = this.selectedImage.image_url;

      // const width = this.imageContainer.nativeElement.offsetWidth;
      // const height = this.imageContainer.nativeElement.offsetHeight;

      const width = 500;
      const height = 500;

      this.closeEnough = 2;

      // Load the image
      this.scope_canvas['image'].onload = () => {
        canvas.width = width;
        canvas.height = height;
        ctx.drawImage(
          this.scope_canvas['image'],
          0,
          0,
          canvas.width,
          canvas.height,
        );
        this.redrawAnnotations(false);
      };

      this.scope_canvas['image'].onerror = (error: any) => {
        console.error('Failed to load image:', error);
      };

      this.addCanvasEventListeners(canvas);
    }
  }

  // Method to cleanup canvas event listeners
  private cleanupCanvasEventListeners(canvas: HTMLCanvasElement): void {
    canvas.removeEventListener('mousedown', this.mouseDownEvent);
    canvas.removeEventListener('mouseup', this.mouseUpEvent);
    canvas.removeEventListener('mousemove', this.mouseMoveEvent);
    canvas.removeEventListener('mouseout', this.mouseOutEvent);
  }

  // Method to add canvas event listeners
  private addCanvasEventListeners(canvas: HTMLCanvasElement): void {
    canvas.addEventListener(
      'mousedown',
      (e: MouseEvent) => this.mouseDownEvent(e),
      false,
    );
    canvas.addEventListener(
      'mouseout',
      (e: MouseEvent) => this.mouseOutEvent(e),
      false,
    );
    canvas.addEventListener(
      'mouseup',
      (e: MouseEvent) => this.mouseUpEvent(e),
      false,
    );
    canvas.addEventListener(
      'mousemove',
      (e: MouseEvent) => this.mouseMoveEvent(e),
      false,
    );
  }

  isMouseInShape(x: number, y: number, shape: any) {
    let shapeLeft = shape.coordinates.x1;
    let shapeRight = shape.coordinates.x1 + shape.coordinates.x2;
    let shapeTop = shape.coordinates.y1;
    let shapeBottom = shape.coordinates.y1 + shape.coordinates.y2;
    if (x > shapeLeft && x < shapeRight && y > shapeTop && y < shapeBottom) {
      return true;
    } else {
      return false;
    }
  }

  checkCloseEnough(p1: number, p2: number) {
    return Math.abs(p1 - p2) < 5;
  }

  mouseDownEvent(event: any) {
    if (this.ShapeAxis) {
      if (
        event.offsetX == parseInt(this.ShapeAxis.x1) ||
        event.offsetY == parseInt(this.ShapeAxis.y1) ||
        event.offsetX == parseInt(this.ShapeAxis.x1 + this.ShapeAxis.x2) ||
        event.offsetY == parseInt(this.ShapeAxis.y1 + this.ShapeAxis.y2)
      ) {
        this.scope_canvas['drag'] = false;
        this.is_dragging = false;
        this.resizing = true;
      }
    }

    var rect = this.scope_canvas['canvas'].getBoundingClientRect();
    this.offsetX = parseInt(rect.left);
    this.offsetY = parseInt(rect.top);

    this.startX = event.clientX - rect.left;
    this.startY = event.clientY - rect.top;
    let index = 0;
    for (var shape of this.filteredAnnotations) {
      if (this.isMouseInShape(this.startX, this.startY, shape)) {
        this.resizing = false;
        this.is_dragging = false;
        this.canvasElement = shape;
        this.ShapeAxis = shape.coordinates;
        if (
          event.offsetX == parseInt(this.ShapeAxis.x1) ||
          event.offsetY == parseInt(this.ShapeAxis.y1) ||
          event.offsetX == parseInt(this.ShapeAxis.x1 + this.ShapeAxis.x2) ||
          event.offsetY == parseInt(this.ShapeAxis.y1 + this.ShapeAxis.y2)
        ) {
          this.resizing = true;
          this.is_dragging = false;
          this.scope_canvas['drag'] = false;
        } else {
          this.current_shape_index = index;
          this.is_dragging = true;
          this.resizing = false;
          return;
        }
      }
      index++;
    }
    if (!this.is_dragging && !this.resizing) {
      this.scope_canvas['rect'] = {
        x1: parseInt(event.offsetX),
        y1: parseInt(event.offsetY),
        x2: 0,
        y2: 0,
      };
      this.scope_canvas['drag'] = true;
    } else if (this.resizing && !this.is_dragging) {
      this.mouseX = event.pageX - this.offsetX;
      this.mouseY = event.pageY - this.offsetY;

      // if there isn't a rect yet
      if (this.ShapeAxis['x2'] === undefined) {
        this.scope_canvas['rect']['x1'] = this.mouseX;
        this.scope_canvas['rect']['y1'] = this.mouseY;
        this.dragBR = true;
      }
      // 1. top left
      else if (
        this.checkCloseEnough(event.offsetX, parseInt(this.ShapeAxis['x1'])) &&
        this.checkCloseEnough(event.offsetY, parseInt(this.ShapeAxis['y1']))
      ) {
        this.dragTL = true;
      }
      // 2. top right
      else if (
        this.checkCloseEnough(
          event.offsetX,
          parseInt(this.ShapeAxis['x1'] + this.ShapeAxis['x2']),
        ) &&
        this.checkCloseEnough(event.offsetY, parseInt(this.ShapeAxis['y1']))
      ) {
        this.dragTR = true;
      }
      // 3. bottom left
      else if (
        this.checkCloseEnough(event.offsetX, parseInt(this.ShapeAxis['x1'])) &&
        this.checkCloseEnough(
          event.offsetY,
          parseInt(this.ShapeAxis['y1'] + this.ShapeAxis['y2']),
        )
      ) {
        this.dragBL = true;
      }
      // 4. bottom right
      else if (
        this.checkCloseEnough(
          event.offsetX,
          parseInt(this.ShapeAxis['x1'] + this.ShapeAxis['x2']),
        ) &&
        this.checkCloseEnough(
          event.offsetY,
          parseInt(this.ShapeAxis['y1'] + this.ShapeAxis['y2']),
        )
      ) {
        this.dragBR = true;
      }
      // (5.) none of them
      else {
      }
      this.scope_canvas['ctx'].clearRect(
        0,
        0,
        this.scope_canvas['canvas'].width,
        this.scope_canvas['canvas'].height,
      );
      this.scope_canvas['ctx'].drawImage(
        this.scope_canvas['image'],
        0,
        0,
        this.scope_canvas['width'],
        this.scope_canvas['height'],
      );
      this.redrawAnnotations(true);
    }
    this.redrawAnnotations(true);
  }

  mouseMoveEvent(event: any) {
    if (this.is_dragging && !this.resizing) {
      let mouseX = event.clientX - this.offsetX;
      let mouseY = event.clientY - this.offsetY;
      let dx = mouseX - this.startX;
      let dy = mouseY - this.startY;
      let current_shape = this.filteredAnnotations[this.current_shape_index];
      let x1 = (current_shape.coordinates.x1 += dx);
      let y1 = (current_shape.coordinates.y1 += dy);

      this.filteredAnnotations[this.current_shape_index]['coordinates']['x1'] =
        x1;
      this.filteredAnnotations[this.current_shape_index]['coordinates']['y1'] =
        y1;
      this.filteredAnnotations[this.current_shape_index]['coordinates']['x2'] =
        this.ShapeAxis['x2'];
      this.filteredAnnotations[this.current_shape_index]['coordinates']['y2'] =
        this.ShapeAxis['y2'];

      this.filteredAnnotations[this.current_shape_index]['coordinates'][
        'x1_percentage'
      ] = (x1 / this.scope_canvas['width']) * 100;
      this.filteredAnnotations[this.current_shape_index]['coordinates'][
        'y1_percentage'
      ] = (y1 / this.scope_canvas['height']) * 100;
      this.filteredAnnotations[this.current_shape_index]['coordinates'][
        'x2_percentage'
      ] = (this.ShapeAxis['x2'] / this.scope_canvas['width']) * 100;
      this.filteredAnnotations[this.current_shape_index]['coordinates'][
        'y2_percentage'
      ] = (this.ShapeAxis['y2'] / this.scope_canvas['height']) * 100;

      let reqObj = {
        _id: this.filteredAnnotations[this.current_shape_index]['_id'],
        coordinates:
          this.filteredAnnotations[this.current_shape_index]['coordinates'],
      };

      this.imageAnnotationService
        .updateCoordinatesOfCanvas(reqObj)
        .then((response) => {
          if (response) {
            if (response['status']) {
              this.toaster.success(response['msg'], '', {
                positionClass: 'custom-toast-position',
              });
            } else {
              this.toaster.warning(
                'Please save annotation for drag & drop or resize',
                '',
                {
                  positionClass: 'custom-toast-position',
                },
              );
            }
          } else {
            this.toaster.error('Failed to update the annotation(s)', '', {
              positionClass: 'custom-toast-position',
            });
          }
        })
        .catch((error) => {
          console.error('Error fetching mounted drive data:', error);
          this.toaster.error('Failed to save the annotation(s)', '', {
            positionClass: 'custom-toast-position',
          });
        });
      this.scope_canvas['ctx'].clearRect(
        0,
        0,
        this.scope_canvas['width'],
        this.scope_canvas['height'],
      );
      this.scope_canvas['ctx'].drawImage(
        this.scope_canvas['image'],
        0,
        0,
        this.scope_canvas['width'],
        this.scope_canvas['height'],
      );
      this.redrawAnnotations(true);
      this.startX = mouseX;
      this.startY = mouseY;
    } else if (
      this.scope_canvas['drag'] &&
      !this.is_dragging &&
      !this.resizing &&
      ((event.offsetX > this.scope_canvas['rect']['x1'] &&
        event.offsetY > this.scope_canvas['rect']['y1']) ||
        (event.offsetX < this.scope_canvas['rect']['x1'] &&
          event.offsetY < this.scope_canvas['rect']['y1']))
    ) {
      this.scope_canvas['ctx'].drawImage(
        this.scope_canvas['image'],
        0,
        0,
        this.scope_canvas['width'],
        this.scope_canvas['height'],
      );
      this.scope_canvas['rect']['x2'] =
        event.offsetX - parseInt(this.scope_canvas['rect']['x1']);
      this.scope_canvas['rect']['y2'] =
        event.offsetY - parseInt(this.scope_canvas['rect']['y1']);
      this.scope_canvas['last'] = this.scope_canvas['rect'];
      this.scope_canvas['ctx'].strokeStyle = '#FF0000';
      this.scope_canvas['ctx'].strokeRect(
        parseInt(this.scope_canvas['rect']['x1']),
        parseInt(this.scope_canvas['rect']['y1']),
        this.scope_canvas['rect']['x2'],
        this.scope_canvas['rect']['y2'],
      );
    } else if (!this.is_dragging && this.resizing) {
      this.mouseX = event.pageX - this.offsetX;
      this.mouseY = event.pageY - this.offsetY;
      if (this.dragTL) {
        this.ShapeAxis['x2'] += this.ShapeAxis['x1'] - this.mouseX;
        this.ShapeAxis['y2'] += this.ShapeAxis['y1'] - this.mouseY;
        this.ShapeAxis['x1'] = this.mouseX;
        this.ShapeAxis['y1'] = this.mouseY;
      } else if (this.dragTR) {
        this.ShapeAxis['x2'] = Math.abs(this.ShapeAxis['x1'] - this.mouseX);
        this.ShapeAxis['y2'] += this.ShapeAxis['y1'] - this.mouseY;
        this.ShapeAxis['y1'] = this.mouseY;
      } else if (this.dragBL) {
        this.ShapeAxis['x2'] += this.ShapeAxis['x1'] - this.mouseX;
        this.ShapeAxis['y2'] = Math.abs(this.ShapeAxis['y1'] - this.mouseY);
        this.ShapeAxis['x1'] = this.mouseX;
      } else if (this.dragBR) {
        this.ShapeAxis['x2'] = Math.abs(this.ShapeAxis['x1'] - this.mouseX);
        this.ShapeAxis['y2'] = Math.abs(this.ShapeAxis['y1'] - this.mouseY);
      }

      let index = this.filteredAnnotations.findIndex(
        (x: any) =>
          x.annotation_id ===
          this.filteredAnnotations[this.current_shape_index].annotation_id,
      );
      this.filteredAnnotations[index]['coordinates']['x1'] =
        this.ShapeAxis['x1'];
      this.filteredAnnotations[index]['coordinates']['y1'] =
        this.ShapeAxis['y1'];
      this.filteredAnnotations[index]['coordinates']['x2'] =
        this.ShapeAxis['x2'];
      this.filteredAnnotations[index]['coordinates']['y2'] =
        this.ShapeAxis['y2'];

      this.filteredAnnotations[index]['coordinates']['x1_percentage'] =
        (this.ShapeAxis['x1'] / this.scope_canvas['width']) * 100;
      this.filteredAnnotations[index]['coordinates']['y1_percentage'] =
        (this.ShapeAxis['y1'] / this.scope_canvas['height']) * 100;
      this.filteredAnnotations[index]['coordinates']['x2_percentage'] =
        (this.ShapeAxis['x2'] / this.scope_canvas['width']) * 100;
      this.filteredAnnotations[index]['coordinates']['y2_percentage'] =
        (this.ShapeAxis['y2'] / this.scope_canvas['height']) * 100;
      let reqObj = {
        _id: this.filteredAnnotations[index]['_id'],
        coordinates: this.filteredAnnotations[index]['coordinates'],
      };
      this.imageAnnotationService
        .updateCoordinatesOfCanvas(reqObj)
        .then((response) => {
          if (response) {
            if (response['status']) {
              this.toaster.success(response['msg'], '', {
                positionClass: 'custom-toast-position',
              });
              this.resizing = false;
            } else {
              this.toaster.error(
                'Please save annotation for drag & drop or resize',
                '',
                {
                  positionClass: 'custom-toast-position',
                },
              );
            }
          } else {
            this.toaster.error('Failed to update the annotation(s)', '', {
              positionClass: 'custom-toast-position',
            });
          }
        })
        .catch((error) => {
          console.error('Error fetching mounted drive data:', error);
          this.toaster.error('Failed to update the annotation(s)', '', {
            positionClass: 'custom-toast-position',
          });
        });
      this.scope_canvas['ctx'].clearRect(
        0,
        0,
        this.scope_canvas['width'],
        this.scope_canvas['height'],
      );
      this.scope_canvas['ctx'].drawImage(
        this.scope_canvas['image'],
        0,
        0,
        this.scope_canvas['width'],
        this.scope_canvas['height'],
      );
      this.redrawAnnotations(true);
    }
  }

  updateLabelObject(row: any) {
    row.original_name = row.Object;
    row.Label = row.Label;
    this.updateSegmentedImageAnnotations();
  }

  updateSegmentedImageAnnotations() {
    var annotations = this.image['segmented_annotation']['object_labels'].map(
      (val: any) => ({
        Unique_object_id: val['Unique_object_id'],
        Object: val['Object'],
        Label: val['Label'],
      }),
    );
    var objectTobeSent = {
      image_annotation_document_id:
        this.image['segmented_annotation']['image_annotation_document_id'],
      annotation_data: annotations,
    };

    this.imageAnnotationService
      .updateSegmentedImageAnnotations(objectTobeSent)
      .then((response) => {
        if (response) {
          this.toaster.success('Annotation(s) updated successfully', '', {
            positionClass: 'custom-toast-position',
          });

          this.selectBoxView = false;
          this.customNewLabel = '';
          this.selectedAnnotation = null;
          this.oldAnnotationName = '';
          this.Editing = false;
          this.updateLabelsForVisualization();
        } else {
          this.toaster.error('Failed to update the annotation(s)', '', {
            positionClass: 'custom-toast-position',
          });
        }
        this.apiCall = false;
      })
      .catch((error) => {
        this.apiCall = false;
        console.error('Error fetching mounted drive data:', error);
        this.toaster.error('Failed to update the annotation(s)', '', {
          positionClass: 'custom-toast-position',
        });
      });
  }
  updateLabelsForVisualization() {
    for (
      var i = 0;
      i < this.image['segmented_annotation']['object_labels'].length;
      i++
    ) {
      var vizLabel =
        this.image['segmented_annotation']['interactive_fig_json_data']['data'][
        i + 1
        ];
      var hoverTemplate = vizLabel['hovertemplate'].split('<br>');
      var newHoverTemplate = '';
      for (var n = 0; n < hoverTemplate.length; n++) {
        if (hoverTemplate[n].includes('Label:')) {
          newHoverTemplate =
            newHoverTemplate +
            '<b>Label:' +
            this.image['segmented_annotation']['object_labels'][i]['Label'] +
            '</b><br>';
        } else if (hoverTemplate[n].includes('Object:')) {
          newHoverTemplate =
            newHoverTemplate +
            '<b>Object:' +
            this.image['segmented_annotation']['object_labels'][i]['Object'] +
            '</b><br>';
        } else {
          newHoverTemplate = newHoverTemplate + hoverTemplate[n] + '<br>';
        }
        if (n == hoverTemplate.length - 1) {
          newHoverTemplate = newHoverTemplate.substring(
            0,
            newHoverTemplate.length - 4,
          );
          this.image['segmented_annotation']['interactive_fig_json_data'][
            'data'
          ][i + 1]['hovertemplate'] = newHoverTemplate;
        }
        if (
          i == this.image['segmented_annotation']['object_labels'].length - 1 &&
          n == hoverTemplate.length - 1
        ) {
          setTimeout(() => {
            this.drawInteractiveVisualization();
          }, 100);
        }
      }
    }
  }

  mouseUpEvent(event: any) {
    if (this.is_dragging) {
      event.preventDefault();
      this.is_dragging = false;
    } else if (this.scope_canvas['drag'] && !this.is_dragging) {
      this.scope_canvas['drag'] = false;
      if (
        event.offsetX > this.scope_canvas['rect']['x1'] &&
        event.offsetY > this.scope_canvas['rect']['y1']
      ) {
        this.scope_canvas['last']['x1_percentage'] =
          (this.scope_canvas['rect']['x1'] / this.scope_canvas['width']) * 100;
        this.scope_canvas['last']['y1_percentage'] =
          (this.scope_canvas['rect']['y1'] / this.scope_canvas['height']) * 100;
        this.scope_canvas['last']['x2_percentage'] =
          (this.scope_canvas['rect']['x2'] / this.scope_canvas['width']) * 100;
        this.scope_canvas['last']['y2_percentage'] =
          (this.scope_canvas['rect']['y2'] / this.scope_canvas['height']) * 100;

        this.scope_canvas['last']['x1_original'] =
          (this.selectedImage['shape'][1] *
            this.scope_canvas['last']['x1_percentage']) /
          100;
        this.scope_canvas['last']['y1_original'] =
          (this.selectedImage['shape'][0] *
            this.scope_canvas['last']['y1_percentage']) /
          100;
        this.scope_canvas['last']['x2_original'] =
          (this.selectedImage['shape'][1] *
            this.scope_canvas['last']['x2_percentage']) /
          100;
        this.scope_canvas['last']['y2_original'] =
          (this.selectedImage['shape'][0] *
            this.scope_canvas['last']['y2_percentage']) /
          100;
        this.scope_canvas['index'] = this.scope_canvas['index'] + 1;
        this.addNewBoundingBoxToList(null);
      }
      if (
        event.offsetX < this.scope_canvas['rect']['x1'] &&
        event.offsetY < this.scope_canvas['rect']['y1']
      ) {
        var object = {
          x1: this.scope_canvas['rect']['x2'] + this.scope_canvas['rect']['x1'],
          x2: Math.abs(this.scope_canvas['rect']['x2']),
          y1: this.scope_canvas['rect']['y2'] + this.scope_canvas['rect']['y1'],
          y2: Math.abs(this.scope_canvas['rect']['y2']),
        };
        this.scope_canvas['rect']['x1'] = object.x1;
        this.scope_canvas['rect']['x2'] = object.x2;
        this.scope_canvas['rect']['y1'] = object.y1;
        this.scope_canvas['rect']['y2'] = object.y2;
        this.scope_canvas['last']['x1_percentage'] =
          (this.scope_canvas['rect']['x1'] / this.scope_canvas['width']) * 100;
        this.scope_canvas['last']['y1_percentage'] =
          (this.scope_canvas['rect']['y1'] / this.scope_canvas['height']) * 100;
        this.scope_canvas['last']['x2_percentage'] =
          (this.scope_canvas['rect']['x2'] / this.scope_canvas['width']) * 100;
        this.scope_canvas['last']['y2_percentage'] =
          (this.scope_canvas['rect']['y2'] / this.scope_canvas['height']) * 100;

        this.scope_canvas['last']['x1_original'] =
          (this.selectedImage['shape'][1] *
            this.scope_canvas['last']['x1_percentage']) /
          100;
        this.scope_canvas['last']['y1_original'] =
          (this.selectedImage['shape'][0] *
            this.scope_canvas['last']['y1_percentage']) /
          100;
        this.scope_canvas['last']['x2_original'] =
          (this.selectedImage['shape'][1] *
            this.scope_canvas['last']['x2_percentage']) /
          100;
        this.scope_canvas['last']['y2_original'] =
          (this.selectedImage['shape'][0] *
            this.scope_canvas['last']['y2_percentage']) /
          100;

        this.scope_canvas['index'] = this.scope_canvas['index'] + 1;
        this.addNewBoundingBoxToList(null);
      }
    }
    this.dragTL = this.dragTR = this.dragBL = this.dragBR = false;
  }

  mouseOutEvent(event: any) {
    if (!this.is_dragging) {
      return;
    }
    event.preventDefault();
    this.is_dragging = false;
  }

  addNewBoundingBoxToList(label: any) {
    var annotationObject = {
      annotation_name: 'object_' + this.getIndex(),
      label: label ? label.title : '',
      color: this.colors,
      object_type: this.selectedTool,
      annotation_id: this.scope_canvas['index'],
      coordinates: this.scope_canvas['last'],
      sample_id: this.selectedFolder['folderId'],
      project_id: this.configService.SelectedProjectId,
      dataset_id: this.datasetId,
      image_path: this.selectedImage['image'],
      image_name: '',
      annotated_image_path: '',
      annotated_image_name: '',
      image_dimensions: this.selectedImage['shape'],
      created_by: this.currentUser['_id'],
    };
    this.annotations.push(annotationObject);
    this.redrawAnnotations(false);
    this.hasUnsavedChanges = true;
  }

  getIndex() {
    var filterAnnotations = this.annotations.filter((val: any) =>
      val['annotation_name'].includes('object_'),
    );
    if (filterAnnotations.length > 0) {
      var indexed: any = 0;
      for (var i = 0; i < filterAnnotations.length; i++) {
        if (
          indexed <
          filterAnnotations[i]['annotation_name'].replace('object_', '')
        ) {
          indexed = +filterAnnotations[i]['annotation_name'].replace(
            'object_',
            '',
          );
        }
        if (i == filterAnnotations.length - 1) {
          return indexed + 1;
        }
      }
    } else {
      return 1;
    }
  }

  checkAnnotationExists(annotation: any) {
    var index = this.filteredAnnotations.findIndex(
      (data: any) => data['label'] == annotation['label'],
    );
    if (index != -1) {
      return true;
    } else {
      return false;
    }
  }

  changeClickName(annotation: any) {
    if (annotation['_id']) {
      this.selectedAnnotation = annotation;
      this.oldAnnotationName = this.selectedAnnotation.annotation_name;
      this.Editing = true;
    } else {
      this.Editing = false;
      this.toaster.warning('Please save the annotation before editing the object', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }

  changeAnnotationLabel(annotation: any) {
    if (!annotation['_id']) {
      this.toaster.warning(
        'Please save the annotation before editing the label',
        '',
        {
          positionClass: 'custom-toast-position',
        },
      );
    }
  }

  checkNameLength(annotation: any) {
    if (annotation['annotation_name'].length !== 0) {
      return true;
    } else {
      return false;
    }
  }

  undoChangeName(annotation: any) {
    annotation.annotation_name = this.oldAnnotationName;
    this.Editing = false;
  }

  saveAnnotationsForSelectedImage() {
    if (this.annotations.length > 0) {
      this.hasUnsavedChanges = false;
      var annotationsToSave: any = [];
      for (var i = 0; i < this.annotations.length; i++) {
        if (!this.annotations[i]['_id']) {
          var obj = { ...this.annotations[i] };
          var coordinates = {
            x1: parseInt(this.annotations[i]['coordinates']['x1_original']),
            y1: parseInt(this.annotations[i]['coordinates']['y1_original']),
            x2: parseInt(this.annotations[i]['coordinates']['x2_original']),
            y2: parseInt(this.annotations[i]['coordinates']['y2_original']),
            x1_percentage: this.annotations[i]['coordinates']['x1_percentage'],
            y1_percentage: this.annotations[i]['coordinates']['y1_percentage'],
            x2_percentage: this.annotations[i]['coordinates']['x2_percentage'],
            y2_percentage: this.annotations[i]['coordinates']['y2_percentage'],
          };
          obj['coordinates'] = coordinates;
          annotationsToSave.push(obj);
        }

        if (i === this.annotations.length - 1) {
          this.imageAnnotationService
            .saveAnnotations(annotationsToSave)
            .then((response) => {
              if (response) {
                this.getSavedAnnotations();
                this.toaster.success('Annotation(s) saved successfully.', '', {
                  positionClass: 'custom-toast-position',
                });
                this.hasUnsavedChanges = false;
              } else {
                this.toaster.error('Failed to save the annotation(s)', '', {
                  positionClass: 'custom-toast-position',
                });
                this.hasUnsavedChanges = true;
              }
            })
            .catch((error) => {
              console.error('Error fetching mounted drive data:', error);
              this.toaster.error('Failed to save the annotation(s)', '', {
                positionClass: 'custom-toast-position',
              });
              this.hasUnsavedChanges = true;
            });
        }
      }
    }
  }

  getSavedAnnotations() {
    this.apiCall = true;
    this.datasetAnnotations = [];
    this.imageAnnotationService
      .getSavedAnnotationsByDatasetId(this.datasetId)
      .then((response) => {
        if (response) {
          var data = response['data'];
          var dataToDisplay: any = [];
          if (data.length > 0) {
            for (var i = 0; i < data.length; i++) {
              var obj = { ...data[i] };
              obj['coordinates']['x1'] =
                (this.scope_canvas['width'] *
                  data[i]['coordinates']['x1_percentage']) /
                100;
              obj['coordinates']['y1'] =
                (this.scope_canvas['height'] *
                  data[i]['coordinates']['y1_percentage']) /
                100;
              obj['coordinates']['x2'] =
                (this.scope_canvas['width'] *
                  data[i]['coordinates']['x2_percentage']) /
                100;
              obj['coordinates']['y2'] =
                (this.scope_canvas['width'] *
                  data[i]['coordinates']['y2_percentage']) /
                100;
              dataToDisplay.push(obj);
              if (i == data.length - 1) {
                this.datasetAnnotations = dataToDisplay;
                this.showSelectedImageAnnotations()
              }
            }
          }
        } else {
          this.toaster.error('Failed to save the annotation(s)', '', {
            positionClass: 'custom-toast-position',
          });
        }
        this.apiCall = false;
      })
      .catch((error) => {
        this.apiCall = false;
        console.error('Error fetching mounted drive data:', error);
        this.toaster.error('Failed to save the annotation(s)', '', {
          positionClass: 'custom-toast-position',
        });
      });
  }

  resetAnnotations(_menuItem: any) {
    this.getSavedAnnotations();
  }

  annotationVisiblility(annotation: any) {
    var index = this.filteredAnnotations.findIndex(
      (val: any) => val['annotation_id'] == annotation['annotation_id'],
    );
    if (index != -1) {
      // this.annotationVisible = !this.annotationVisible
    }
  }

  noSegmentationDone() {
    if (this.image && this.image['segmented_img'] == '') {
      return true
    } else {
      return false;
    }
  }


  pendingAnnotations(): boolean {
    var findUnsavedAnnotations = this.annotations.filter(
      (annotation: any) => annotation['_id'] === undefined,
    );
    if (findUnsavedAnnotations.length > 0) {
      return false;
    } else return true;
  }

  toggleSegmentedPanel(type: string) {
    this.annotation_type = type;
    if (type == 'raw') {
      this.SegmentedPanel = false;
    } else {
      this.SegmentedPanel = true;
    }
    if (this.image) {
      if (!this.SegmentedPanel) {
        setTimeout((val: any) => {
          this.setImageForAnnotation();
          this.showSelectedImageAnnotations();
          this.changeParentEvent(true);
          this.showSpinner = false;
        }, 2000);
      } else {
        this.checkSegmentedAndGetAnnotations();
      }
    }
  }

  checkSegImageExists() {
    return this.image['segmented_img'] != '' ? true : false;
  }

  deleteSegmentedImageLabel(item: any) {
    var payload: any = {
      "label_name": item
    }
    this.imageAnnotationService
      .deleteSegmentedImageAnnotationLabel(payload)
      .then((response) => {
        if (response['status']) {
          const index = this.segmentedLabelsList.indexOf(payload['label_name']);
          if (index > -1) {
            this.segmentedLabelsList.splice(index, 1);
          }
          this.image['segmented_annotation']['object_labels'].forEach((item: any) => {
            if (!item.Label || item.Label.trim() === payload['label_name']) {
              item.Label = "blank";
            }
          });
          this.cdr.detectChanges();
          this.toaster.success('Annotation label deleted for segmented image', '', {
            positionClass: 'custom-toast-position',
          });
        } else {
          this.toaster.error('Failed to delete the annotation label for segmented image', '', {
            positionClass: 'custom-toast-position',
          });
        }
      })
      .catch((error) => {
        this.apiCall = false;
        console.error('Error during annotation deletion:', error);
        this.toaster.error('Failed to delete the annotation label for segmented image', '', {
          positionClass: 'custom-toast-position',
        });
      });
  }
}
