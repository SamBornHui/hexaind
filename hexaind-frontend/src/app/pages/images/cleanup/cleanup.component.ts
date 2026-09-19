import {
  Component,
  OnInit,
  Output,
  OnDestroy,
  AfterViewInit,
  ElementRef,
  ViewChild,
  Renderer2,
  TemplateRef,
  EventEmitter
} from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { ImageAnalysisService } from '../services/image-analysis.service';
import { ToastrService } from 'ngx-toastr';
import { HttpErrorResponse } from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { ViewCleanFullImageDialogBox } from 'src/app/pages/images/cleanup/view-cleanup-image-dialog-box/view-cleanup-image-dialog-box.component';
import { MatDialog, MatDialogConfig, MatDialogRef } from '@angular/material/dialog';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';
import clone from 'clone';

import { ImagePreviewComponent } from 'src/app/dialogs/image-preview/image-preview.component';
import { ConfirmationImagePrompComponent } from 'src/app/dialogs/confirmation-image-promp/confirmation-image-promp.component';
import { Title } from '@angular/platform-browser';
import { interval, of } from 'rxjs';
import { filter, first, switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-image-cleanup',
  templateUrl: './cleanup.component.html',
  styleUrls: ['./cleanup.component.less'],
})
export class ImageCleanupComponent implements OnInit {
  editMode = true;
  editModeType: string = 'rotation';
  showImagesPreview = true;
  showImageCleanup = false;
  datasetDetails: object = {};
  rotation: number = 0;
  sliderRotation: number = 0;
  appliedRotation: number = 0;

  projectId: string = '';
  siteId: string = '1';
  datasetId: string = '';
  datasetName: string = '';
  imageData: any
  folderId: any
  imagePath: any

  foldersList: any[] = [];
  [originalImage: string]: any;
  modifiedImage: any = '';

  imageBlobs: any = {
    originalImage: '',
    modifiedImage: '',
  };
  selectedFolder: any;
  imageDetail: any;
  scalebarObj: any = {};
  unitValues: any = [
    { unit: 'nm', value: '1e-9' },
    { unit: 'μm', value: '1e-6' },
    { unit: 'mm', value: '1e-3' },
  ];
  allWorkFlows: any = [];
  @ViewChild('scalecanvas') public scalecanvas!: ElementRef;
  apiCall: boolean = false;
  applyAllImageScale: boolean = false;
  secondDropDownVal: string = '';
  secondImagePath: any;
  sizeOfImage: any;
  currentUser: any;

  cropObj: any = {};
  autoCrop: boolean = false;

  zoomLevel = 1;
  zoomStep = 0.1;
  maxZoom = 3;
  minZoom = 0.5;

  @ViewChild('image') public imageElement!: ElementRef;
  @ViewChild('annotationCanvas') public maskCanvasElement!: ElementRef;
  private ctx!: CanvasRenderingContext2D;
  // Define new variables
  private isDrawing = false;
  private isDragging = false;
  private startX = 0;
  private startY = 0;
  private lastX = 0;
  private lastY = 0;
  offsetX: number = 0;
  offsetY: number = 0;

  imageLoaded: boolean = false;
  filteredAnnotations: any = [];
  closeEnough: any;
  private eventListeners: Array<() => void> = [];
  image_masking: any[] = []; // Array to store mask data
  deleteMaskingIndex: number | null = null;
  MaskingObj: any;
  currentEditMask: any = null;
  originalName: string = ''
  selectedMask: any;
  isMaskModified: boolean = false;
  loading: boolean = false;
  applyType: string = '';

  callWorkflowApiImageMask: boolean = false;
  private cachedImage!: HTMLImageElement;

  @Output() panelOpened = new EventEmitter<void>();
  @Output() panelClosed = new EventEmitter<void>();


  constructor(
    private toaster: ToastrService,
    private imageAnalysisService: ImageAnalysisService,
    private activatedRoute: ActivatedRoute,
    private configService: ConfigService,
    private dialog: MatDialog,
    private renderer: Renderer2
  ) { }

  ngOnInit(): void {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    if (this.activatedRoute) {
      this.activatedRoute.params.subscribe((params) => {
        this.datasetId = params['datasetId'];
      });
      this.activatedRoute.queryParams.subscribe((params) => {
        this.datasetName = params['datasetName'];
        this.imageData = (params['imageData'] != undefined) ? JSON.parse(params['imageData']) : undefined;
        this.folderId = (params['folderId'] != undefined) ? params['folderId'] : undefined;
        this.imagePath = (params['imagePath'] != undefined) ? params['imagePath'] : undefined;
      });
      this.processExpirementalData();
    }
    this.resetScalebarOptions();
    this.getAllWorkflows();
  }

  changeCleanupType(type: string) {
    this.editModeType = type;
  }
  hasMasked(image:any){
    return (image.image_masks && image.image_masks.length > 0)?true:false
  }
  hasScalebar(image:any){
    return (image.scalebar_options && image.scalebar_options.scalebar_type !== '')?true:false;
  }
  getAllWorkflows() {
    this.allWorkFlows = [];
    this.imageAnalysisService.getAllWorkflows({}).then((response) => {
      if (response) {
        let workflowData = response;
        if (workflowData.length > 0) {
          workflowData.forEach((element: any) => {
            element['recommended'] = false;
          });
          this.allWorkFlows = workflowData;
        }
      }
    });
  }

  resetScalebarOptions() {
    this.scalebarObj = {
      scaleCtx: '',
      scalebar_type: 'manual',
      activateReadScalebar: false,
      scalebarByImage: '',
      scalebarByImageTemp: '',
      scalebarImageOptions: {
        loaded: false,
        imageLoaded: false,
        tempImage: '',
        imgWidth: 0,
        imgHeight: 0,
      },
      auto_scale: '',
      auto_scale_unit: '',
      scalebarByPhysical: '',
      scalebarByPhysicalUnit: 'nm',
      scalebarChanged: false,
    };
  }

  processExpirementalData() {
    this.imageAnalysisService
      .getCategorizationData(this.datasetId)
      .then((response) => {
        if (response && response['categorization_data']) {
          this.foldersList = response['categorization_data'];
          this.foldersList.forEach((element: any, index: number) => {
            this.foldersList[index]['selectedimages'] = element.img_details;
          });
          if (this.folderId && this.imagePath) {
            this.loading = true;
            let index = this.foldersList.findIndex(folder => folder._id === this.folderId);
            if (index === -1) {
              console.error(`Folder with ID ${this.folderId} not found`);
              return;
            }

            this.foldersList[index]['leftNavExpanded'] = true;
            this.showImagesPreview = true;
            this.leftmenuFolderSelection(this.foldersList[index]);
            setTimeout(async () => {
              try {
                if (Array.isArray(this.foldersList[index]['selectedimages'])) {
                  const imageIndex = await this.foldersList[index]['selectedimages'].findIndex((image: any) => image.path === this.imagePath);
                  if (imageIndex !== -1) {
                    this.onContentClicked(this.foldersList[index]['selectedimages'][imageIndex]);
                  } else {
                    console.error(`Image with name ${this.imagePath} not found`);
                    this.folderId = undefined;
                    this.imageData = undefined;
                    this.loading = false;
                  }
                } else {
                  console.error(`selectedImages is not an array or does not exist for folder ID ${this.folderId}`);
                  this.folderId = undefined;
                  this.imageData = undefined;
                  this.loading = false;
                }
              } catch (error) {
                console.error('An error occurred:', error);
                this.loading = false;
              }
            }, 1000);
          }
          else {
            this.foldersList[0]['leftNavExpanded'] = true;
            this.showImagesPreview = true;
            if (this.foldersList.length > 0) {
              this.leftmenuFolderSelection(this.foldersList[0]);
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
        this.toaster.error(error.error.detail, '', {
          positionClass: 'custom-toast-position',
        });
      });
  }

  openPanel(panelName: string) {
    this.panelOpened.emit();

    setTimeout(() => {
      switch (panelName) {
        case 'rotation':
          this.initImageRotation();
          break;
        case 'scalebar':
          this.initImageScalebar();
          break;
        case 'crop':
          this.intiateCropObj();
          break;
        case 'mask':
          this.initImageMasking()
          break;
        default:
          break;
      }

    }, 500);

  }

  closePanel(type: string) {
    switch (type) {
      case 'scalebar':
        this.resetScalebarOptions();
        break;
      case 'crop':
        this.resetCroppingOptions();
        break;
      default:
        break;
    }

  }

  setCropAndScaleOptions() {
    this.secondDropDownVal = this.imageDetail['crop_type'];
    if (this.imageDetail['crop_type'] == 'auto') {
      this.secondImagePath = this.imageDetail['modified_path'];
      this.sizeOfImage = this.imageDetail['modified_shape'];
    } else {
      this.secondImagePath = this.imageDetail['manual_image'];
      this.sizeOfImage = this.imageDetail['manual_shape'];
    }
    this.calculateScalbarForModifiedImage();
  }

  calculateScalbarForModifiedImage() {
    if (
      (this.imageDetail['scalebar_options']['scalebar_type'] == 'auto' &&
        this.imageDetail['scalebar_options']['auto_scale'] != '') ||
      (this.imageDetail['scalebar_options']['scalebarByImage'] != '' &&
        this.imageDetail['scalebar_options']['scalebarByPhysical'] != '' &&
        this.imageDetail['scalebar_options']['scalebarByPhysicalUnit'] != '')
    ) {
      setTimeout((_val: any) => {
        let imageContainer;
        imageContainer = document.querySelector('#cropped_image_id');
        var data: any = {
          client_width: imageContainer!.clientWidth,
          PixelSizeX: this.imageDetail['PixelSizeX'],
          modified_image: this.secondImagePath,
          scale_unit:
            this.imageDetail['scalebar_options']['scalebarByPhysicalUnit'],
        };
        if (this.imageDetail['scalebar_options']['scalebar_type'] == 'auto') {
          if (
            this.imageDetail['scalebar_options']['auto_scale'] != '' &&
            this.imageDetail['scalebar_options']['auto_scale'] > 0
          ) {
            data['px_scale'] =
              this.imageDetail['scalebar_options']['auto_scale'];
          } else {
            data['px_scale'] = this.getFinalScaleValueAfterAdjusting();
          }
        } else {
          data['px_scale'] = this.getFinalScaleValueAfterAdjusting();
        }
        this.imageAnalysisService
          .getScalebarForModifiedImage(data)
          .then((response) => {
            if (response) {
              this.imageDetail['calculatedScalebar'] = response;
            }
          })
          .catch((error) => { });
      }, 500);
    }
  }

  initImageScalebar() {
    this.editMode = true;
    this.editModeType = 'scalebar';
    if (this.imageDetail['scalebar_options']['scalebar_type'] != '') {
      this.imageDetail['scalebar_type'] =
        this.imageDetail['scalebar_options']['scalebar_type'];
    } else {
      this.imageDetail['scalebar_type'] = 'manual';
    }

    this.scalebarObj['auto_scale'] =
      this.imageDetail['scalebar_options']['auto_scale'];
    this.scalebarObj['auto_scale_unit'] =
      this.imageDetail['scalebar_options']['auto_scale_unit'];
    this.scalebarObj['scalebarByImage'] =
      this.imageDetail['scalebar_options']['scalebarByImage'];
    this.scalebarObj['scalebarByPhysical'] =
      this.imageDetail['scalebar_options']['scalebarByPhysical'];
    this.scalebarObj['scalebarByPhysicalUnit'] =
      this.imageDetail['scalebar_options']['scalebarByPhysicalUnit'];
    this.setCropAndScaleOptions();
  }
  confirmScalebar() {
    if (this.scalebarObj['scalebarByImageTemp'] != '') {
      this.scalebarObj['scalebarByImage'] =
        this.scalebarObj['scalebarByImageTemp'];
    }
    if (
      this.scalebarObj['scalebarByImage'] != '' &&
      this.scalebarObj['scalebarByPhysical'] != '' &&
      this.scalebarObj['scalebarByPhysicalUnit'] != ''
    ) {
      let croppedImage = document.getElementById('canvas_image');
      let height = croppedImage!.clientHeight;
      let width = croppedImage!.clientWidth;
      let _scope = this;
      let canvas: HTMLCanvasElement = this.scalecanvas.nativeElement;
      this.scalebarObj['scaleCtx'] = canvas.getContext('2d');
      var image = new Image();
      image.src = this.scalebarObj['scalebarImageOptions']['tempImage'];
      image.onload = function () {
        canvas.width = width;
        canvas.height = height;
        _scope.scalebarObj['scaleCtx'].drawImage(image, 0, 0, width, height);
        _scope.scalebarObj['activateReadScalebar'] = false;
        _scope.checkScaleChanges();
      };
    } else {
      // this.toastr.error('Please enter Scalebar values');
    }
  }

  scalebarImageCropped(event: any) {
    this.scalebarObj['scalebarImageOptions']['tempImage'] = event['objectUrl'];
    this.scalebarObj['scalebarImageOptions']['imgWidth'] = event['width'];
    this.scalebarObj['scalebarImageOptions']['imgHeight'] = event['height'];
    this.scalebarObj['scalebarByImageTemp'] = '';
    this.setScaleImageSize(event);
  }

  setScaleImageSize(event: any) {
    let canvas_image = document.getElementById('canvas_image');
    let source_image = document.getElementsByClassName('source-image')[0];
    if (canvas_image) {
      if (event['width'] >= event['height']) {
        canvas_image.style.width = source_image.clientWidth + 'px';
        canvas_image.style.height = 'auto';
      } else {
        canvas_image.style.height = source_image.clientHeight + 'px';
        canvas_image.style.width = 'auto';
      }
    }
  }
  scalebarImageloaded(_event: any) {
    this.scalebarObj['imageLoaded'] = true;
  }
  readScalebar(type: string) {
    this.scalebarObj['scalebar_type'] = type;
    this.scalebarObj['activateReadScalebar'] = true;
  }

  getResultScaleValue() {
    if (
      this.scalebarObj['scalebar_type'] == 'auto' &&
      this.scalebarObj['auto_scale'] != ''
    ) {
      return (
        this.scalebarObj['auto_scale'].toFixed(2) +
        ' ' +
        this.scalebarObj['auto_scale_unit'] +
        '/px'
      );
    } else if (
      this.scalebarObj['scalebarByImage'] != '' &&
      this.scalebarObj['scalebarByPhysical'] != '' &&
      this.scalebarObj['scalebarByPhysicalUnit'] != ''
    ) {
      return (
        this.getFinalScaleValue().toFixed(2) +
        ' ' +
        this.scalebarObj['scalebarByPhysicalUnit'] +
        '/px'
      );
    } else {
      return '';
    }
  }

  getFinalScaleValue() {
    let firstVal =
      parseInt(this.scalebarObj['scalebarByPhysical']) /
      parseInt(this.scalebarObj['scalebarByImage']);
    let secondVal = parseInt(
      this.getUnitValue(this.scalebarObj['scalebarByPhysicalUnit'])['value'],
    );
    let finalVal = firstVal * secondVal;
    return parseFloat(finalVal.toFixed(4));
  }

  getFinalScaleValueAfterAdjusting() {
    let firstVal =
      parseInt(this.imageDetail['scalebar_options']['scalebarByPhysical']) /
      parseInt(this.imageDetail['scalebar_options']['scalebarByImage']);
    let secondVal = parseInt(
      this.getUnitValue(
        this.imageDetail['scalebar_options']['scalebarByPhysicalUnit'],
      )['value'],
    );
    let finalVal = firstVal * secondVal;
    return parseFloat(finalVal.toFixed(4));
  }

  onToggleChange(event: any) {
    if (event.checked) {
      this.scalebarObj['scalebar_type'] = 'auto';
      this.autoReadScalebar();
    }
  }

  autoReadScalebar() {
    if (
      this.scalebarObj['auto_scale'] != undefined &&
      this.scalebarObj['auto_scale'] != ''
    ) {
      this.scalebarObj['scalebar_type'] = 'auto';
    } else {
      let req = {
        imgpath: this.imageDetail['path'],
        sample_image: this.imageDetail['image'],
      };
      //   const dialogRef = this.dialog.open(VerifyScalebarDialogboxComponent, {
      //     width: '32%',
      //     disableClose: true,
      //     panelClass: "add-data-set-panel-class",
      //     data: req
      //   });
      //   dialogRef.afterClosed().subscribe(result => {
      //     if (result != undefined) {
      //       if (result['scalebar'] != undefined) {
      //         this.scalebarObj['scalebar_type'] = 'auto';
      //         this.scalebarObj['scalebarByImage'] = result['scalebar_width_px'];
      //         this.scalebarObj['scalebarByPhysical'] = result['scalebar'];
      //         this.scalebarObj['scalebarByPhysicalUnit'] = result['units'];
      //         this.scalebarObj['scalebarChanged'] = true;
      //       } else if (result['error']) {
      //         this.toastr.error('Unable to read the scalebar. Please add it manually');
      //       }
      //     }
      //   });
    }
  }

  scaleBarDrawer() {
    let _scope = this;
    let croppedImage = document.getElementById('canvas_image');
    let height = croppedImage!.clientHeight;
    let width = croppedImage!.clientWidth;

    let canvas: HTMLCanvasElement = this.scalecanvas.nativeElement;
    _scope.scalebarObj['scaleCtx'] = canvas.getContext('2d');

    var image = new Image();
    image.src = this.scalebarObj['scalebarImageOptions']['tempImage'];
    image.onload = function () {
      canvas.width = width;
      canvas.height = height;
      _scope.scalebarObj['scaleCtx'].drawImage(image, 0, 0, width, height);
    };

    this.scalecanvas.nativeElement.removeEventListener(
      'mousedown',
      function (_event: any) { },
    );
    this.scalecanvas.nativeElement.removeEventListener(
      'mouseup',
      function (_event: any) { },
    );
    this.scalecanvas.nativeElement.removeEventListener(
      'mousemove',
      function (_event: any) { },
    );
    this.scalecanvas.nativeElement.removeEventListener(
      'mouseout',
      function (_event: any) { },
    );

    let startX = 0;
    let startY = 0;
    let w = 0;
    let h = 3;
    let drag = false;
    let org_imgX1 = 0;
    this.scalecanvas.nativeElement.addEventListener(
      'mousedown',
      function (e: any) {
        if (
          _scope.scalebarObj['scalebar_type'] != 'auto' &&
          _scope.scalebarObj['activateReadScalebar']
        ) {
          drag = true;
          startX = e.offsetX;
          startY = e.offsetY;

          let x1Percentage = (startX / width) * 100;
          org_imgX1 =
            (x1Percentage / 100) *
            _scope.scalebarObj['scalebarImageOptions']['imgWidth'];
        }
      },
      false,
    );
    this.scalecanvas.nativeElement.addEventListener(
      'mousemove',
      function (e: any) {
        if (drag) {
          _scope.scalebarObj['scaleCtx'].drawImage(image, 0, 0, width, height);
          _scope.scalebarObj['scaleCtx'].strokeStyle = 'red';
          _scope.scalebarObj['scaleCtx'].lineWidth = h;
          _scope.scalebarObj['scaleCtx'].beginPath();
          _scope.scalebarObj['scaleCtx'].moveTo(startX, startY);
          _scope.scalebarObj['scaleCtx'].lineTo(e.offsetX, startY);
          _scope.scalebarObj['scaleCtx'].stroke();

          let x2Percentage = (e.offsetX / width) * 100;
          let org_imgX2 =
            (x2Percentage / 100) *
            _scope.scalebarObj['scalebarImageOptions']['imgWidth'];
          if (org_imgX2 >= org_imgX1) {
            w = Math.round(org_imgX2 - org_imgX1);
          } else {
            w = Math.round(org_imgX1 - org_imgX2);
          }

          let y1Percentage = (startY / height) * 100;
          _scope.scalebarObj['scaleCtx'].strokeStyle = '#aeaba7';
          _scope.scalebarObj['scaleCtx'].lineWidth = 13;
          let adjustRectXVal;
          if (org_imgX2 >= org_imgX1) {
            adjustRectXVal = startX + 10;
          } else {
            adjustRectXVal = e.offsetX + 10;
          }
          if (y1Percentage > 30) {
            _scope.scalebarObj['scaleCtx'].strokeRect(
              adjustRectXVal,
              startY - 25,
              50,
              13,
            );
          } else {
            _scope.scalebarObj['scaleCtx'].strokeRect(
              adjustRectXVal,
              startY + 13,
              50,
              13,
            );
          }

          _scope.scalebarObj['scaleCtx'].fillStyle = '#000';
          _scope.scalebarObj['scaleCtx'].font = '11pt sans-serif';
          let adjustTextXVal;
          if (org_imgX2 >= org_imgX1) {
            adjustTextXVal = startX + 10;
          } else {
            adjustTextXVal = e.offsetX + 10;
          }
          if (y1Percentage > 30) {
            _scope.scalebarObj['scaleCtx'].fillText(
              w + ' px',
              adjustTextXVal,
              startY - 13,
            );
          } else {
            _scope.scalebarObj['scaleCtx'].fillText(
              w + ' px',
              adjustTextXVal,
              startY + 25,
            );
          }
        }
      },
      false,
    );
    this.scalecanvas.nativeElement.addEventListener(
      'mouseup',
      function (_e: any) {
        _scope.scalebarObj['scalebarByImageTemp'] = w;
        drag = false;
      },
      false,
    );
    this.scalecanvas.nativeElement.addEventListener(
      'mouseout',
      function (_e: any) {
        if (drag) {
          _scope.scalebarObj['scalebarByImageTemp'] = w;
          _scope.checkScaleChanges();
          drag = false;
        }
      },
      false,
    );
  }

  getUnitValue(unit: string) {
    return this.unitValues.find((val: any) => val['unit'] == unit);
  }

  checkScaleChanges() {
    let changed = false;
    if (
      this.imageDetail['scalebar_options']['scalebar_type'] !=
      this.scalebarObj['scalebar_type']
    ) {
      changed = true;
    } else if (this.scalebarObj['scalebar_type'] == 'manual') {
      if (
        this.imageDetail['scalebar_options']['scalebarByImage'] !=
        this.scalebarObj['scalebarByImage'] ||
        this.imageDetail['scalebar_options']['scalebarByPhysical'] !=
        this.scalebarObj['scalebarByPhysical'] ||
        this.imageDetail['scalebar_options']['scalebarByPhysicalUnit'] !=
        this.scalebarObj['scalebarByPhysicalUnit']
      ) {
        changed = true;
      }
    }
    this.scalebarObj['scalebarChanged'] = changed;
  }
  applyScalebar() {
    if (this.isSegmentedImage()) {
      const dialogRef = this.dialog.open(ConfirmationImagePrompComponent, {
        width: '400px',
        data: {
          message: 'This image is already segmented. If you proceed, the existing segmentation and annotations will be overwritten. Do you really want to proceed?',
          title: 'Reapply Workflow',
        },
      });

      dialogRef.afterClosed().subscribe(async (action) => {
        if (action && action === true) {
          this.callReadScaleApply(true);
        }
      })
    } else {
      this.callReadScaleApply(false);
    }
  }

  callReadScaleApply(applyWorkflow: boolean) {
    if (this.scalebarObj['scalebarByImageTemp'] != '') {
      this.scalebarObj['scalebarByImage'] =
        this.scalebarObj['scalebarByImageTemp'];
    }

    let detail: any = {
      scalebar_type: this.scalebarObj['scalebar_type'],
      imgpath: this.imageDetail['path'],
      image: this.imageDetail['image'],
      datasetid: this.datasetId,
      folderpath: this.selectedFolder.tempPath,
      foldername: this.selectedFolder.folderId,
      category: this.imageDetail['category'],
    };
    detail.applytoall = this.applyAllImageScale;

    detail.scalebarByImage = this.scalebarObj.scalebarByImage;
    detail.scalebarByPhysical = this.scalebarObj.scalebarByPhysical;
    detail.scalebarByPhysicalUnit = this.scalebarObj.scalebarByPhysicalUnit;
    detail.scalebarChanged = false;
    this.apiCall = true;

    this.imageAnalysisService
      .saveScalebar(detail)
      .then((response) => {
        if (response) {
          this.toaster.success('Scalebar applied successfully', '', {
            positionClass: 'custom-toast-position',
          });
          this.imageDetail.scalebar_options.scalebar_type =
            this.scalebarObj.scalebar_type;
          this.imageDetail.scalebar_options.scalebarByImage =
            this.scalebarObj.scalebarByImage;
          this.imageDetail.scalebar_options.scalebarByPhysical =
            this.scalebarObj.scalebarByPhysical;
          this.imageDetail.scalebar_options.scalebarByPhysicalUnit =
            this.scalebarObj.scalebarByPhysicalUnit;
          let folderIndex = this.foldersList.findIndex(
            (folder: any) => folder.folderId == this.selectedFolder.folderId,
          );
          if (folderIndex != -1) {
            let imgIndex = this.selectedFolder.img_details.findIndex(
              (image: any) => image.image == this.imageDetail.image,
            );
            if (imgIndex != -1) {
              this.selectedFolder.img_details[
                imgIndex
              ].scalebar_options.scalebar_type = this.scalebarObj.scalebar_type;
              this.selectedFolder.img_details[
                imgIndex
              ].scalebar_options.scalebarByImage =
                this.scalebarObj.scalebarByImage;
              this.foldersList[folderIndex].img_details[
                imgIndex
              ].scalebar_options.scalebarByPhysical =
                this.scalebarObj.scalebarByPhysical;
              this.foldersList[folderIndex].img_details[
                imgIndex
              ].scalebar_options.scalebarByPhysicalUnit =
                this.scalebarObj.scalebarByPhysicalUnit;
            }
          }
          this.updateImagesScalebarInfo(applyWorkflow);
        } else {
          this.toaster.error('Failed to apply scalebar', '', {
            positionClass: 'custom-toast-position',
          });
        }
      })
      .catch((error) => {
        console.error('An error occurred while applying scalebar', error);
        this.toaster.error(error, '', {
          positionClass: 'custom-toast-position',
        });
      });
  }

  updateImagesScalebarInfo(applyWorkflow: boolean) {
    if (!this.applyAllImageScale) {
      let folderIndex = this.foldersList.findIndex(
        (folder: any) => folder.folderId == this.selectedFolder.folderId,
      );
      if (folderIndex != -1) {
        let imgIndex = this.foldersList[folderIndex].img_details.findIndex(
          (image: any) => image.image == this.imageDetail.image,
        );
        if (imgIndex != -1) {
          this.foldersList[folderIndex].img_details[
            imgIndex
          ].scalebar_options.scalebar_type = this.scalebarObj.scalebar_type;
          this.foldersList[folderIndex].img_details[
            imgIndex
          ].scalebar_options.scalebarByImage = this.scalebarObj.scalebarByImage;
          this.foldersList[folderIndex].img_details[
            imgIndex
          ].scalebar_options.scalebarByPhysical =
            this.scalebarObj.scalebarByPhysical;
          this.foldersList[folderIndex].img_details[
            imgIndex
          ].scalebar_options.scalebarByPhysicalUnit =
            this.scalebarObj.scalebarByPhysicalUnit;
        }
      }
    } else {
      this.foldersList.forEach((element: any, index: number) => {
        element.img_details.forEach((image: any, ind: number) => {
          this.foldersList[index].img_details[
            ind
          ].scalebar_options.scalebar_type = this.scalebarObj.scalebar_type;
          this.foldersList[index].img_details[
            ind
          ].scalebar_options.scalebarByImage = this.scalebarObj.scalebarByImage;
          this.foldersList[index].img_details[
            ind
          ].scalebar_options.scalebarByPhysical =
            this.scalebarObj.scalebarByPhysical;
          this.foldersList[index].img_details[
            ind
          ].scalebar_options.scalebarByPhysicalUnit =
            this.scalebarObj.scalebarByPhysicalUnit;
        });
      });
    }
    if (applyWorkflow) {
      this.applyWorkflow(this.applyAllImageScale ? 'all' : 'individual', 'scale');
    }
  }
  getImageName(filePath: string): string {
    if (filePath) {
      const parts = filePath.split('/');
      return parts.pop() || ''; // Returns the last part or an empty string if the path is empty
    } else {
      return '';
    }
  }
  applyWorkflow(apply_type: string, view: string) {
    if (this.imageDetail.wfname != '') {
      var workflowDetail = this.allWorkFlows.filter(
        (val: any) => val['Wname'] === this.imageDetail.wfname,
      );
      if (workflowDetail.length > 0) {
        let selectedWorkflow: any = workflowDetail[0];
        var data: any = {
          original_image: this.imageDetail['image'],
          orignalpath: this.imageDetail['path'],
          image: '',
          sample_image: this.imageDetail['cropimg'],
          applied: false,
          path: true,
          draw_val: this.scalebarObj.scalebarByImage,
          popup_val: this.scalebarObj.scalebarByPhysical,
          popup_unit: this.scalebarObj.scalebarByPhysicalUnit,
          PixleX: this.imageDetail.PixelSizeX,
          PixleY: this.imageDetail.PixelSizeY,
          images_names: ['test'],
          workflow: [
            {
              _id: selectedWorkflow['_id'],
              retrieve: false,
              features: [],
            },
          ],
        };

        if (this.imageDetail['cropimg'] && this.imageDetail['cropimg'] != '') {
          data['image'] = this.imageDetail['cropimg'];
          data['sample_image'] = this.imageDetail['cropimg'];
        } else {
          if (
            this.imageDetail['manual_image'] &&
            this.imageDetail['manual_image'] != ''
          ) {
            data['image'] = this.imageDetail['manual_image'];
            data['sample_image'] = this.imageDetail['manual_image'];
          } else {
            data['image'] = this.imageDetail['image'];
            data['sample_image'] = this.imageDetail['image'];
          }
        }
        data['workflow'][0]['post_visualization'] = {};
        if (selectedWorkflow['workflow']['preprocessingWorkflowSelected']) {
          data['workflow'][0]['features'] = data['workflow'][0][
            'features'
          ].concat(
            selectedWorkflow['workflow']['preprocessingWorkflowFeatures'],
          );
        }
        if (selectedWorkflow['workflow']['segmentationWorkflowSelected']) {
          data['workflow'][0]['features'] = data['workflow'][0][
            'features'
          ].concat(
            selectedWorkflow['workflow']['segmentationWorkflowFeatures'],
          );
          if (
            selectedWorkflow['workflow']['segmentationWorkflowFeatures']
              .length > 0
          ) {
            let segWorkflow = selectedWorkflow['workflow'][
              'segmentationWorkflowFeatures'
            ].filter((val: any) => val['selected'] == true);
            data['workflow'][0]['post_visualization']['visualization'] =
              segWorkflow[segWorkflow.length - 1]['Params']['visualization'];
            data['workflow'][0]['post_visualization']['color'] =
              segWorkflow[segWorkflow.length - 1]['Params']['color'];
          }
        }
        if (selectedWorkflow['workflow']['postprocessingWorkflowSelected']) {
          data['workflow'][0]['features'] = data['workflow'][0][
            'features'
          ].concat(
            selectedWorkflow['workflow']['postprocessingWorkflowFeatures'],
          );
        }

        this.imageAnalysisService
          .getCroppedAndSegmentedImage(data)
          .then((response) => {
            if (response) {
              let resultData = response['imagedata'];
              let split_img = resultData.segmented_img.split('/');
              split_img = split_img.filter(
                (_val: any, index: number) => index != split_img.length - 1,
              );

              let updateWorkflowData: any = {
                type: 'existing',
                dirpath: split_img.join('/'),
                username:
                  this.currentUser['firstName'] +
                  ' ' +
                  this.currentUser['lastName'],
                project_id: this.configService.SelectedProjectId,
                dataset_id: this.datasetId,
                foldername: this.selectedFolder.folderId,
                name: selectedWorkflow.Wname,
                image_path: this.imageDetail['path'],
                cropimg: this.imageDetail['cropimg'],
                wf_sample_image: this.imageDetail['manual_image'],
                _id: selectedWorkflow['_id'],
                workflow: {
                  preprocessingWorkflowSelected:
                    selectedWorkflow['workflow'][
                    'preprocessingWorkflowSelected'
                    ],
                  preprocessingWorkflowFeatures:
                    selectedWorkflow['workflow'][
                    'preprocessingWorkflowFeatures'
                    ],
                  segmentationWorkflowSelected:
                    selectedWorkflow['workflow'][
                    'segmentationWorkflowSelected'
                    ],
                  segmentationWorkflowFeatures:
                    selectedWorkflow['workflow'][
                    'segmentationWorkflowFeatures'
                    ],
                  postprocessingWorkflowSelected:
                    selectedWorkflow['workflow'][
                    'segmentationWorkflowSelected'
                    ],
                  postprocessingWorkflowFeatures:
                    selectedWorkflow['workflow'][
                    'postprocessingWorkflowFeatures'
                    ],
                },
                default: false,
                applyToAll: false,
                carrycrop: true,
                carryanalysis: false,
                wf_for_incomingimages: false,
                output_directory_options: {
                  setDirectory: false,
                  defaultDirectory: true,
                  outputDirectory: '',
                },
                analysis: [],
                annotate_img: '',
                excel_path: '',
                pdf_path: '',
                profile_analysis: [],
                tier_analysis: [],
                metal_recess_analysis: [],
                bubble_analysis: [],
                pillar_anomaly_analysis: [],
                pillar_c2c_analysis: [],
                metal_voids_analysis: [],
                analysis_type: [],
                applyCropping: false,
                removeconnection: true,
                userId: this.currentUser._id,
              };

              if (view == 'scale') {
                if (selectedWorkflow['modification']) {
                  updateWorkflowData['manualcoordinates'] =
                    selectedWorkflow['modification'];
                  updateWorkflowData['applyCropping'] = true;
                }
              }

              if (view == 'crop') {
                if (this.imageDetail['manual_coordinates']) {
                  updateWorkflowData['manualcoordinates'] =
                    this.imageDetail['manual_coordinates'];
                  updateWorkflowData['applyCropping'] = true;
                }
              }
              if (apply_type == 'all') {
                updateWorkflowData.applyToAll = true;
              }
              if (resultData.preprocessedlayers.length > 0) {
                for (var i = 0; i < resultData.preprocessedlayers.length; i++) {
                  let result = {
                    filtered_image: resultData.preprocessedlayers[i][
                      'filterd_image'
                    ]
                      ? resultData.preprocessedlayers[i]['filterd_image']
                      : '',
                    histogram_path: resultData.preprocessedlayers[i][
                      'histogram_path'
                    ]
                      ? resultData.preprocessedlayers[i]['histogram_path']
                      : '',
                    previewchanges: resultData.preprocessedlayers[i][
                      'previewchanges'
                    ]
                      ? resultData.preprocessedlayers[i]['previewchanges']
                      : '',
                  };
                  var index = updateWorkflowData['workflow'][
                    'preprocessingWorkflowFeatures'
                  ].findIndex(
                    (val: any) =>
                      val['fid'] == resultData.preprocessedlayers[i]['fid'],
                  );
                  if (index != -1) {
                    updateWorkflowData['workflow'][
                      'preprocessingWorkflowFeatures'
                    ][index]['result'] = result;
                  }
                }
              }
              if (resultData.segmentationlayers.length > 0) {
                for (var i = 0; i < resultData.segmentationlayers.length; i++) {
                  let result = {
                    filtered_image: resultData.segmentationlayers[i][
                      'filterd_image'
                    ]
                      ? resultData.segmentationlayers[i]['filterd_image']
                      : '',
                    histogram_path: resultData.segmentationlayers[i][
                      'histogram_path'
                    ]
                      ? resultData.segmentationlayers[i]['histogram_path']
                      : '',
                    'black&white': resultData.segmentationlayers[i][
                      'black&white'
                    ]
                      ? resultData.segmentationlayers[i]['black&white']
                      : '',
                    region_properties: resultData.segmentationlayers[i][
                      'region_properties'
                    ]
                      ? resultData.segmentationlayers[i]['region_properties']
                      : {},
                    temp_region_properties_csv_file: resultData
                      .segmentationlayers[i]['temp_region_properties_csv_file']
                      ? resultData.segmentationlayers[i][
                      'temp_region_properties_csv_file'
                      ]
                      : '',
                    region_properties_csv_file: resultData.segmentationlayers[
                      i
                    ]['region_properties_csv_file']
                      ? resultData.segmentationlayers[i][
                      'region_properties_csv_file'
                      ]
                      : '',
                    previewchanges: resultData.segmentationlayers[i][
                      'previewchanges'
                    ]
                      ? resultData.segmentationlayers[i]['previewchanges']
                      : '',
                    perula: resultData.segmentationlayers[i]['perula']
                      ? resultData.segmentationlayers[i]['perula']
                      : '',
                  };
                  var index = updateWorkflowData['workflow'][
                    'segmentationWorkflowFeatures'
                  ].findIndex(
                    (val: any) =>
                      val['fid'] == resultData.segmentationlayers[i]['fid'],
                  );
                  if (index != -1) {
                    updateWorkflowData['workflow'][
                      'segmentationWorkflowFeatures'
                    ][index]['result'] = result;
                  }
                }
              }
              if (resultData.postprocessedlayers.length > 0) {
                for (
                  var i = 0;
                  i < resultData.postprocessedlayers.length;
                  i++
                ) {
                  let result = {
                    filtered_image: resultData.postprocessedlayers[i][
                      'filterd_image'
                    ]
                      ? resultData.postprocessedlayers[i]['filterd_image']
                      : '',
                    histogram_path: resultData.postprocessedlayers[i][
                      'histogram_path'
                    ]
                      ? resultData.postprocessedlayers[i]['histogram_path']
                      : '',
                    'black&white': resultData.postprocessedlayers[i][
                      'black&white'
                    ]
                      ? resultData.postprocessedlayers[i]['black&white']
                      : '',
                    region_properties: resultData.postprocessedlayers[i][
                      'region_properties'
                    ]
                      ? resultData.postprocessedlayers[i]['region_properties']
                      : {},
                    temp_region_properties_csv_file: resultData
                      .postprocessedlayers[i]['temp_region_properties_csv_file']
                      ? resultData.postprocessedlayers[i][
                      'temp_region_properties_csv_file'
                      ]
                      : '',
                    region_properties_csv_file: resultData.postprocessedlayers[
                      i
                    ]['region_properties_csv_file']
                      ? resultData.postprocessedlayers[i][
                      'region_properties_csv_file'
                      ]
                      : '',
                    previewchanges: resultData.postprocessedlayers[i][
                      'previewchanges'
                    ]
                      ? resultData.postprocessedlayers[i]['previewchanges']
                      : '',
                    perula: resultData.postprocessedlayers[i]['perula']
                      ? resultData.postprocessedlayers[i]['perula']
                      : '',
                  };
                  var index = updateWorkflowData['workflow'][
                    'postprocessingWorkflowFeatures'
                  ].findIndex(
                    (val: any) =>
                      val['fid'] == resultData.postprocessedlayers[i]['fid'],
                  );
                  if (index != -1) {
                    updateWorkflowData['workflow'][
                      'postprocessingWorkflowFeatures'
                    ][index]['result'] = result;
                  }
                }
              }

              this.imageAnalysisService
                .saveWorkflow(updateWorkflowData)
                .then((response) => {
                  if (response) {
                    let reqData: any = {
                      _id: selectedWorkflow['_id'],
                      image_path: [
                        {
                          image: this.imageDetail.path,
                          PixelSizeX: 0,
                          PixelSizeY: 0,
                          workflow_applied: selectedWorkflow['_id'],
                        },
                      ],
                      aftersavingwf: true,
                      duplicate: false,
                      dataset_id: this.datasetId,
                      project_id: this.configService.SelectedProjectId,
                      username:
                        this.currentUser['firstName'] +
                        ' ' +
                        this.currentUser['lastName'],
                      foldername: this.selectedFolder.folderId,
                    };
                    this.imageAnalysisService
                      .assignWorflowToImages(reqData)
                      .then((response) => {
                        if (response) {
                          this.resetScalebarOptions();
                          this.applyAllImageScale = false;
                          // this.editModeType = '';
                          if (apply_type == 'all') {
                            let applyData = {
                              folderIds: [this.selectedFolder['_id']],
                              project_id: this.configService.SelectedProjectId,
                            };
                            this.toaster.info('Applying workflows', '', {
                              positionClass: 'custom-toast-position',
                            });
                            this.imageAnalysisService
                              .applyWorkflows(applyData)
                              .then((response) => {
                                if (response) {
                                  if (response['status'] == 'completed') {
                                    if (response['status_message']) {
                                      this.toaster.success(
                                        'Workflow Applied.' +
                                        response['status_message'],
                                        '',
                                        {
                                          positionClass:
                                            'custom-toast-position',
                                        },
                                      );
                                    } else {
                                      this.toaster.success(
                                        'Workflow Applied.',
                                        '',
                                        {
                                          positionClass:
                                            'custom-toast-position',
                                        },
                                      );
                                    }
                                  }
                                } else {
                                  this.toaster.error(
                                    'Failed to apply workflow',
                                    '',
                                    {
                                      positionClass: 'custom-toast-position',
                                    },
                                  );
                                }
                              });
                          } else {
                            this.toaster.success(
                              'Workflow applied succcessfully',
                              '',
                              {
                                positionClass: 'custom-toast-position',
                              },
                            );
                          }
                        } else {
                          this.toaster.error('Failed to assign workflow', '', {
                            positionClass: 'custom-toast-position',
                          });
                        }
                      })
                      .catch((error) => {
                        console.error(
                          'Error fetching mounted drive data:',
                          error,
                        );
                        this.toaster.error(error.error.detail, '', {
                          positionClass: 'custom-toast-position',
                        });
                      });
                  } else {
                    this.toaster.error(
                      'Failed to update workflow. Try again!',
                      '',
                      {
                        positionClass: 'custom-toast-position',
                      },
                    );
                  }
                })
                .catch((error) => {
                  console.error('Error fetching mounted drive data:', error);
                  this.toaster.error(error.error.detail, '', {
                    positionClass: 'custom-toast-position',
                  });
                });
            } else {
              this.toaster.error('Failed to apply workflow. Try again!', '', {
                positionClass: 'custom-toast-position',
              });
            }
          })
          .catch((error) => {
            this.toaster.error(error.error.detail, '', {
              positionClass: 'custom-toast-position',
            });
          });
      }
    }
  }

  leftmenuFolderSelection(folder: any, showPreview: boolean = true) {
    this.showImagesPreview = showPreview;
    this.selectedFolder = folder;
    this.fetchFolderImages();
  }

  checkIfFolderImages() {
    return this.selectedFolder && 'img_details' in this.selectedFolder
      ? true
      : false;
  }
  fetchFolderImages() {
    for (let i = 0; i < this.selectedFolder.img_details.length; i++) {
      let imagePath = this.selectedFolder.img_details[i]['manual_thumbnail'];
      if (this.selectedFolder.img_details[i]['crop_type'] == 'auto') {
        if ('modified_path' in this.selectedFolder.img_details[i]) {
          imagePath = this.selectedFolder.img_details[i]['modified_path'];
        } else {
          imagePath = this.selectedFolder.img_details[i]['manual_thumbnail'];
        }
      }
      let fileName = this.selectedFolder.img_details[i].imagename;
      if (
        !this.selectedFolder.img_details[i].imagename ||
        this.selectedFolder.img_details[i].imagename.trim() === ''
      ) {
        fileName = imagePath.split('/').pop();
      }

      this.getModifiedImgeConent(imagePath, fileName, i);
    }
  }
  getModifiedImgeConent(path: string, name: string, index: number) {
    this.imageAnalysisService
      .getIndividualImageContent({ path: path, name: name })
      .subscribe(
        (result) => {
          this.selectedFolder.img_details[index]['displayImage'] = result;
        },
        (error) => {
          console.error('Error fetching image content:', error);
        },
      );
  }

  async onContentClicked(event: any) {
    this.loading = true;
    try {
      if (this.folderId != undefined && this.imagePath != undefined) {
        let index = this.foldersList.findIndex(folder => folder._id === this.folderId);
        this.selectedFolder = this.foldersList[index];
        this.imageDetail = event;
        this.folderId = undefined; this.imageData = undefined
      } else {
        this.selectedFolder = event.folder;
        this.imageDetail = event.image;
      }


      if (this.imageDetail.rotate_options.shape) {
        this.imageDetail.shape = [...this.imageDetail.rotate_options.shape];
      }


      if (this.imageDetail.image && this.imageDetail.image != '') {
        await this.ImageConent(this.imageDetail.image, this.imageDetail.imagename, 'originalImage');
      }
      if (this.imageDetail.rotate_image && this.imageDetail.rotate_image !== '') {
        await this.ImageConent(
          this.imageDetail.rotate_image,
          this.imageDetail.imagename,
          'rotatedImage',
        );
        this.appliedRotation = this.imageDetail.rotate_options?.rotateval || 0;
        this.rotation = this.appliedRotation;
        this.sliderRotation = this.appliedRotation;
      }

      if (this.imageDetail.manual_image && this.imageDetail.manual_image !== '') {
        await this.ImageConent(this.imageDetail.manual_image, this.imageDetail.imagename, 'modifiedImage');
        this.appliedRotation = this.imageDetail.rotate_options?.rotateval || 0;
        this.rotation = this.appliedRotation;
        this.sliderRotation = this.appliedRotation;
      } else {
        this.appliedRotation = 0;
        this.rotation = 0;
        this.sliderRotation = 0;
      }

      this.showImagesPreview = false;

      switch (this.editModeType) {
        case 'rotation':
          this.initImageRotation();
          break;
        case 'scalebar':
          this.initImageScalebar();
          break;
        case 'crop':
          this.intiateCropObj();
          break;
        case 'mask':
          this.initImageMasking();
          break;
        default:
          break;
      }
    } catch (error) {
      console.error('Error fetching image content:', error);
    } finally {
      this.loading = false;
    }
  }

  async ImageConent(path: string, name: string, resultImage: string): Promise<boolean> {
    try {
      const result = await this.imageAnalysisService.getIndividualImageContent({ path, name }).toPromise();
      if (result) {
        this.imageBlobs[resultImage] = result;
        return true;
      }
      return false;
    } catch (error) {
      console.error(`Error fetching ${resultImage} content:`, error);
      return false;
    }
  }

  zoomIn() {
    if (this.zoomLevel < this.maxZoom) {
      this.zoomLevel += this.zoomStep;
    }
  }

  zoomOut() {
    if (this.zoomLevel > this.minZoom) {
      this.zoomLevel -= this.zoomStep;
    }
  }

  applyFrontEndRotation(): boolean {
    return this.imageDetail.rotate_options.rotateval === 0 || !this.imageDetail.manual_image;
  }

  initImageRotation() {
    this.editModeType = 'rotation';
    this.zoomLevel = 1;
    this.appliedRotation = this.imageDetail.rotate_options?.rotateval || 0;
    this.rotation = this.appliedRotation;
    this.sliderRotation = this.appliedRotation;
  }


  async reset(type: string) {
    this.rotation = 0;
    this.sliderRotation = 0;
    this.appliedRotation = 0;
    this.zoomLevel = 1;
    const data = {
      categorized_data_id: this.selectedFolder._id,
      image: this.imageDetail.path,
      category: "NA",
      reset_from: type
    };

    try {
      const response = await this.imageAnalysisService.resetImage(data);
      if (response.updated_data) {
        if (type === 'mask') {
          this.toaster.success('Image mask(s) reset successfully', '', {
            positionClass: 'custom-toast-position',
          });
          this.getImageMasking();
        } else {
          this.toaster.success('Image reset successfully', '', {
            positionClass: 'custom-toast-position',
          });
        }

        this.imageDetail = response.updated_data;

        if (this.imageDetail.rotate_options.manual_rotate || this.imageDetail.rotate_options.manual_rotate) {
          this.imageDetail.shape = [...this.imageDetail.rotate_options.shape];
        }

        if (type === 'rotate') {
          this.imageBlobs.rotatedImage = undefined;
          this.initImageRotation();
        }
        if (type === 'crop') {
          this.cropObj['tempImage'] = undefined;
          this.intiateCropObj();
        }

        this.getImageConent(
          this.imageDetail.manual_image,
          this.imageDetail.imagename,
          'modifiedImage'
        );
      } else {
        this.toaster.error('Failed to reset the image. Please try again.', '', {
          positionClass: 'custom-toast-position',
        });
      }
    } catch (error) {
      this.toaster.error('Failed to reset the image. Please try again later.', '', {
        positionClass: 'custom-toast-position',
      });

      console.error('Error resetting the image:', error);
    }
  }

  getImageConent(path: string, name: string, resultImage: string) {
    this.imageAnalysisService.getIndividualImageContent({ path: path, name: name }).subscribe(
      (result) => {
        this.imageBlobs[resultImage] = result;
      },
      (error) => {
        console.error('Error fetching image content:', error);
      },
    );
  }

  rotateLeft() {
    this.rotation = (this.rotation - 90 + 360) % 360;
    this.sliderRotation = this.rotation;
  }

  rotateRight() {
    this.rotation = (this.rotation + 90) % 360;
    this.sliderRotation = this.rotation;
  }

  updateRotationFromSlider(event: Event) {
    const inputElement = event.target as HTMLInputElement;
    this.sliderRotation = parseInt(inputElement.value, 10);
    this.rotation = this.sliderRotation;
  }

  updateAndValidateRotation(event: Event) {
    const inputElement = event.target as HTMLInputElement;
    let value = parseInt(inputElement.value, 10);
    if (value < 0) {
      value = 0;
    } else if (value > 360) {
      value = 360;
    }

    this.sliderRotation = value;
    this.rotation = value;
    inputElement.value = value.toString();
  }
  handleFocusOut(event: Event) {
    const inputElement = event.target as HTMLInputElement;
    if (inputElement.value === '') {
      inputElement.value = '0';
      this.sliderRotation = 0;
      this.rotation = 0;
    }
  }

  isSegmentedImage() {
    if (this.imageDetail.wfname != '') {
      var workflowDetail = this.allWorkFlows.filter(
        (val: any) => val['Wname'] === this.imageDetail.wfname,
      );
      return (workflowDetail.length > 0) ? true : false;
    } else {
      return false;
    }
  }

  applyRotation(type: string) {
    if (this.isSegmentedImage()) {
      const dialogRef = this.dialog.open(ConfirmationImagePrompComponent, {
        width: '400px',
        data: {
          message: 'This image is already segmented. If you proceed, the existing segmentation and annotations will be overwritten. Do you really want to proceed?',
          title: 'Reapply Workflow',
        },
      });

      dialogRef.afterClosed().subscribe(async (action) => {
        if (action && action === true) {
          this.callApplyRotation(type, true)
        }
      })

    } else {
      this.callApplyRotation(type, false)
    }
  }

  callApplyRotation(type: string, reapplyWorkflow: boolean) {
    const degreesToApply = this.rotation;
    let detail = {
      category: this.imageDetail['category'],
      crop_type: this.imageDetail['crop_type'],
      folderpath: this.selectedFolder.tempPath,
      path: this.imageDetail['path'],
      degrees: degreesToApply,
      dataset_id: this.datasetId,
      foldername: this.selectedFolder.folderId,
      applytoall: type === 'all',
    };

    this.imageAnalysisService.applyRotation(detail)
      .then((response) => {

        if (response.status === false) {
          this.toaster.error(response.message, '', {
            positionClass: 'custom-toast-position',
          });
          return;
        }

        if (type === 'single') {
          if (response.modified_path && response.modified_thumbnail && response.modified_shape) {
            this.imageDetail['manual_image'] = response.modified_path;
            this.imageDetail['manual_thumbnail'] = response.modified_thumbnail;
            this.imageDetail['manual_shape'] = response.modified_shape;
            this.imageDetail['rotate_options']['rotateval'] = degreesToApply;
            this.imageDetail['rotate_image'] = response.rotate_image;
            this.imageDetail['rotate_options']['shape'] = response.modified_shape;


            this.appliedRotation = degreesToApply % 360;
            this.getImageConent(
              this.imageDetail['manual_image'],
              this.imageDetail['imagename'],
              'modifiedImage',
            );
            this.getImageConent(
              this.imageDetail['rotate_image'],
              this.imageDetail['imagename'],
              'rotatedImage',
            );
            this.rotation = this.appliedRotation;
            this.sliderRotation = this.appliedRotation;

            if (this.imageDetail.rotate_options.shape) {
              this.imageDetail.shape = [...this.imageDetail.rotate_options.shape];
            }
            const folderIndex = this.foldersList.findIndex(
              (folder) => folder.folderId === this.imageDetail.folderId,
            );
            if (folderIndex !== -1) {
              this.imageDetail.img_details.forEach((updatedImage: any) => {
                const imageIndex = this.foldersList[folderIndex].img_details.findIndex(
                  (img: any) => img.image === updatedImage.image,
                );
                if (imageIndex !== -1) {
                  this.foldersList[folderIndex].img_details[imageIndex]['manual_image'] = response.modified_path;
                  this.foldersList[folderIndex].img_details[imageIndex]['manual_thumbnail'] = response.modified_thumbnail;
                  this.foldersList[folderIndex].img_details[imageIndex]['manual_shape'] = response.modified_shape;
                  this.foldersList[folderIndex].img_details[imageIndex]['rotate_options']['rotateval'] = degreesToApply;
                  this.foldersList[folderIndex].img_details[imageIndex]['rotate_image'] = response.rotate_image;
                  this.foldersList[folderIndex].img_details[imageIndex]['rotate_options']['shape'] = response.modified_shape;
                  this.foldersList[folderIndex].selectedimages[imageIndex] = this.foldersList[folderIndex].img_details[imageIndex];
                  this.selectedFolder = this.foldersList[folderIndex];
                }
              });
            }

          } else {
            this.toaster.error('Failed to apply rotation. Please try again.', '', {
              positionClass: 'custom-toast-position',
            });
          }
        }

        else if (type === 'all') {
          if (Array.isArray(response)) {
            response.forEach((updatedFolder: any) => {
              const folderIndex = this.foldersList.findIndex(
                (folder) => folder.folderId === updatedFolder.folderId,
              );
              if (folderIndex !== -1) {
                updatedFolder.img_details.forEach((updatedImage: any) => {
                  const imageIndex = this.foldersList[
                    folderIndex
                  ].img_details.findIndex(
                    (img: any) => img.image === updatedImage.image,
                  );
                  if (imageIndex !== -1) {
                    this.foldersList[folderIndex].img_details[
                      imageIndex
                    ].manual_image = updatedImage.manual_image;
                    this.foldersList[folderIndex].img_details[
                      imageIndex
                    ].manual_thumbnail = updatedImage.manual_thumbnail;
                    this.foldersList[folderIndex].img_details[
                      imageIndex
                    ].manual_shape = updatedImage.manual_shape;
                    this.foldersList[folderIndex].img_details[
                      imageIndex
                    ].rotate_options.rotateval = degreesToApply;

                    this.foldersList[folderIndex].img_details[
                      imageIndex
                    ].rotate_options.shape = updatedImage.rotate_options.shape;


                    if (this.imageDetail.image === updatedImage.image) {
                      this.imageDetail =
                        this.foldersList[folderIndex].img_details[imageIndex];
                      this.appliedRotation = this.imageDetail.rotate_options.rotateval % 360;
                      this.getImageConent(
                        updatedImage.manual_image,
                        this.imageDetail.imagename,
                        'modifiedImage',
                      );
                      this.getImageConent(
                        this.imageDetail['rotate_image'],
                        this.imageDetail['imagename'],
                        'rotatedImage',
                      );
                      this.rotation = this.appliedRotation;
                      this.sliderRotation = this.appliedRotation;


                      if (this.imageDetail.rotate_options.shape) {
                        this.imageDetail.shape = [...this.imageDetail.rotate_options.shape];
                      }

                    }
                  }
                });
              }
            });
          } else {
            this.toaster.error('Expected an array of updated folders from the response.', '', {
              positionClass: 'custom-toast-position',
            });
          }
        }

        this.toaster.success('Image rotation applied successfully', '', {
          positionClass: 'custom-toast-position',
        });
        if (reapplyWorkflow) {
          this.applyWorkflow(type === 'all' ? 'all' : 'individual', 'rotate');
        }
      })
      .catch((error) => {
        console.error('An error occurred while applying rotation', error);
        this.toaster.error('Failed to apply rotation. Please try again later.', '', {
          positionClass: 'custom-toast-position',
        });
      });

  }

  imageFullView(image: any) {
    let imagePath = image['image'];
    if (image['crop_type'] == 'auto') {
      imagePath = image['modified_path'];
    }
    this.imageAnalysisService
      .getIndividualImageContent({ path: imagePath, name: image.imagename })
      .subscribe(
        (o_result) => {
          let orig_imagepath = o_result
          let manual_imagePath = image['manual_image'];
          this.imageAnalysisService
            .getIndividualImageContent({ path: manual_imagePath, name: image.imagename })
            .subscribe(
              (m_result) => {
                const dialogRef = this.dialog.open(ImagePreviewComponent, {
                  width: '90%',
                  height: '90%',
                  data: { view: 'cleanup', manual_image: m_result, image: orig_imagepath },
                });
              },
              (error) => {
                console.error('Error fetching image content:', error);
              },
            );
        },
        (error) => {
          console.error('Error fetching image content:', error);
        },
      );
  }

  intiateCropObj() {
    this.cropObj['cropperPosition'] = {
      "x1": 0,
      "y1": 0,
      "x2": this.imageDetail.shape[1],
      "y2": this.imageDetail.shape[0]
    };

    this.editModeType = 'crop';
    this.cropObj['imageLoaded'] = false;
    this.cropObj['imageCropType'] = 'auto';
    this.cropObj['imageCropChanged'] = false;
    this.cropObj['imageCropType'] = false;



    this.cropObj['croppedImageWidth'] = this.imageDetail['manual_shape'][1];
    this.cropObj['croppedImageHeight'] = this.imageDetail['manual_shape'][0];

    this.cropObj['manualCoordinates'] = this.imageDetail['manual_coordinates'];
    this.secondDropDownVal = this.imageDetail['crop_type'];
    this.cropObj['imageCropType'] = this.imageDetail['crop_type'];
    let secondImagePath = this.imageDetail['manual_image'];

    if (this.imageDetail['crop_type'] == 'auto') {
      secondImagePath = this.imageDetail['modified_path'];
    }
    this.setCropPostion();

    this.imageAnalysisService
      .getIndividualImageContent({
        path: secondImagePath,
        name: this.imageDetail.imagename ? this.imageDetail.imagename : this.getImageName(this.imageDetail['manual_image']),
      })
      .subscribe(
        (result) => {
          this.cropObj['tempImage'] = result;
        },
        (error) => {
          console.error('Error fetching image content:', error);
        },
      );


  }

  onToggleCropChange(event: MatSlideToggleChange) {
    if (this.imageDetail['category'] === "NA") {
      this.toaster.error('Metadata missing. Cannot AutoCrop this image.', 'ERROR', {
        positionClass: 'custom-toast-position',
      });
      event.source.checked = false;
      return;
    }

    if (event.checked) {
      this.changeCropImageType('auto');
    } else {
      this.changeCropImageType('manual');
    }
  }

  applyCrop(type: string) {
    if (this.isSegmentedImage()) {
      const dialogRef = this.dialog.open(ConfirmationImagePrompComponent, {
        width: '400px',
        data: {
          message: 'This image is already segmented. If you proceed, the existing segmentation and annotations will be overwritten. Do you really want to proceed?',
          title: 'Reapply Workflow',
        },
      });

      dialogRef.afterClosed().subscribe(async (action) => {
        if (action && action === true) {
          this.callApplyCrop(type, true);
        }
      })
    } else {
      this.callApplyCrop(type, false);
    }
  }

  callApplyCrop(type: string, applyWorkflow: boolean) {
    let coordinates = this.cropObj['manualCoordinates'];
    let detail: any = {
      crop_type: this.cropObj['imageCropType'],
      imgpath: this.imageDetail['path'],
      image: this.imageDetail['image'],
      ymax: 0,
      save: true,
      datasetid: this.datasetId,
      folderpath: this.selectedFolder.tempPath,
      foldername: this.selectedFolder.folderId,
      category: this.imageDetail['category'],
    };

    detail['applytoall'] = type == 'all' ? true : false;
    this.secondDropDownVal =
      this.cropObj['imageCropType'] === 'auto' ? 'auto' : 'manual';
    if (this.cropObj['imageCropType'] != 'auto') {
      detail['coordinates'] = coordinates;
      detail['coordinates']['stripsize'] = coordinates['stripsize'];
    }
    this.apiCall = true;
    this.imageAnalysisService
      .applyCropImage(detail)
      .then((response) => {

        if (response) {
          if (response.status == false) {
            this.toaster.error(response.message, '', {
              positionClass: 'custom-toast-position',
            });
            return;
          }

          this.imageDetail['manual_image'] = response.croppedimagepath;
          this.imageDetail['manual_shape'] = response.croppedshape;
          this.imageDetail['manual_coordinates'] = { ...this.cropObj['manualCoordinates'] };

          this.getImageConent(
            this.imageDetail['manual_image'],
            this.imageDetail['imagename'],
            'modifiedImage',
          );

          this.toaster.success('Image cropping applied successfully', '', {
            positionClass: 'custom-toast-position',
          });
          this.applyCropChanges(response, type, applyWorkflow);

        } else {
          this.toaster.error('Failed to apply cropping', '', {
            positionClass: 'custom-toast-position',
          });
        }
      })
      .catch((error) => {
        console.error('An error occurred while applying crop', error);
        this.toaster.error(error, '', {
          positionClass: 'custom-toast-position',
        });
      });
  }

  applyCropChanges(croppedData: any, type: string, applyWorkflow: boolean) {
    this.checkCropChanges();
    let findFolderIndex = this.foldersList.findIndex(
      (val: any) => this.selectedFolder['folderId'] == val['folderId'],
    );
    if (findFolderIndex > -1) {
      if (type == 'all') {
        this.foldersList = croppedData;
        // let index = croppedData.findIndex(
        //   (val: any) => this.selectedFolder['folderId'] == val['folderId'],
        // );
        // this.selectedFolder = croppedData[index].img_details;
      } else {
        let findImageIndex = this.foldersList[findFolderIndex][
          'selectedimages'
        ].findIndex((val: any) => this.imageDetail['path'] == val['path']);
        if (findImageIndex > -1) {
          if (this.cropObj['imageCropType'] != 'auto') {
            this.foldersList[findFolderIndex]['img_details'][findImageIndex][
              'manual_coordinates'
            ] = this.cropObj['manualCoordinates'];
            this.foldersList[findFolderIndex]['img_details'][findImageIndex][
              'manual_shape'
            ] = croppedData['croppedshape'];
            this.foldersList[findFolderIndex]['img_details'][findImageIndex][
              'manual_image'
            ] = croppedData['croppedimagepath'];
            this.foldersList[findFolderIndex]['img_details'][findImageIndex][
              'manual_thumbnail'
            ] = croppedData['croppedimagepath'];
            this.foldersList[findFolderIndex]['img_details'][findImageIndex][
              'cropimg'
            ] = croppedData['croppedimagepath'];

            this.selectedFolder['img_details'][findImageIndex][
              'manual_coordinates'
            ] = this.cropObj['manualCoordinates'];
            this.selectedFolder['img_details'][findImageIndex]['manual_shape'] =
              croppedData['croppedshape'];
            this.selectedFolder['img_details'][findImageIndex]['manual_image'] =
              croppedData['croppedimagepath'];
            this.selectedFolder['img_details'][findImageIndex][
              'manual_thumbnail'
            ] = croppedData['croppedimagepath'];
            this.selectedFolder['img_details'][findImageIndex]['cropimg'] =
              croppedData['croppedimagepath'];

            this.selectedFolder['img_details'][findImageIndex]['manual_coordinates'] = { ...this.cropObj['manualCoordinates'] };
          } else {
            this.foldersList[findFolderIndex]['img_details'][findImageIndex][
              'manual_shape'
            ] = croppedData['croppedshape'];
            this.foldersList[findFolderIndex]['img_details'][findImageIndex][
              'manual_image'
            ] = croppedData['croppedimagepath'];
            this.foldersList[findFolderIndex]['img_details'][findImageIndex][
              'manual_thumbnail'
            ] = croppedData['croppedimagepath'];
            this.foldersList[findFolderIndex]['img_details'][findImageIndex][
              'cropimg'
            ] = croppedData['croppedimagepath'];

            this.selectedFolder['img_details'][findImageIndex]['manual_shape'] =
              croppedData['croppedshape'];
            this.selectedFolder['img_details'][findImageIndex]['manual_image'] =
              croppedData['croppedimagepath'];
            this.selectedFolder['img_details'][findImageIndex]['manual_image'] =
              croppedData['croppedimagepath'];
            this.selectedFolder['img_details'][findImageIndex]['cropimg'] =
              croppedData['croppedimagepath'];

            this.selectedFolder['img_details'][findImageIndex]['manual_coordinates'] = { ...this.cropObj['manualCoordinates'] };
          }
          this.selectedFolder['selectedImages'] = this.selectedFolder['img_details'];
          this.imageDetail = this.selectedFolder['img_details'][findImageIndex];
        }
      }
      this.foldersList.forEach((element: any, index: number) => {
        this.foldersList[index]['selectedimages'] = element.img_details;
      });
      this.foldersList[findFolderIndex]['leftNavExpanded'] = true;
      if (applyWorkflow) {
        this.applyWorkflow(type, 'crop');
      }
    }
  }

  changeCropImageType(cropType: string) {
    setTimeout(() => {
      let shape = this.imageDetail.shape;

      this.cropObj['croppedImageWidth'] = shape[1];
      this.cropObj['croppedImageHeight'] = shape[0];

      if (cropType == 'auto') {
        this.autoCrop = true;
      } else {
        this.autoCrop = false;
      }
      let secondImagePath = this.imageDetail['manual_image'];

      if (this.cropObj['imageCropType'] == 'auto') {
        secondImagePath = this.imageDetail['modified_path'];
      }

      this.cropObj['croppedImageWidth'] = this.imageDetail['manual_shape'][1];
      this.cropObj['croppedImageHeight'] = this.imageDetail['manual_shape'][0];
      this.cropObj['manualCoordinates'] = this.imageDetail['manual_coordinates'];

      let cropperPosition = clone(this.cropObj['cropperPosition']);
      this.cropObj['tempCropperPoition'] = cropperPosition;

      if (this.cropObj['imageCropType'] != cropType) {
        this.cropObj['imageCropType'] = cropType;
        this.cropObj['imageCropType'] = cropType;
        this.checkCropChanges();
        let tempCropperPoition = clone(this.cropObj['tempCropperPoition']);
        this.cropObj['cropImageShape'] = this.getDisplayedImageSize();
        if (this.imageAnalysisService.returnKeysFromObject(tempCropperPoition).length > 0) {
          this.cropObj['cropperPosition'] = tempCropperPoition;
        } else {
          if (this.autoCrop) {
            if (
              this.imageDetail['ImageStripSize'] != '' &&
              this.imageDetail['ImageStripSize'] > 0
            ) {
              let stripePercentage = (this.imageDetail['ImageStripSize'] / shape[0]) * 100;
              this.cropObj['cropperPosition'] = {
                "x1": 0,
                "y1": 0,
                "x2": shape[1],
                "y2": (shape[0] - (stripePercentage / 100) * shape[0])
              };

            } else {
              this.cropObj['cropperPosition'] = {
                x1: 0,
                y1: 0,
                x2: shape[1],
                y2: shape[0],
              };

              // this.cropObj['cropperPosition'] = {};
            }

            this.imageAnalysisService
              .getIndividualImageContent({
                path: secondImagePath,
                name: this.imageDetail.imagename,
              })
              .subscribe(
                (result) => {
                  this.cropObj['tempImage'] = result;
                },
                (error) => {
                  console.error('Error fetching image content:', error);
                },
              );
          }
        }
      }
    }, 100);
  }
  cropperReady(event: any) {

    this.cropObj['cropImageShape'] = event;

    if (this.cropObj['imageCropType'] != 'auto' && this.imageAnalysisService.returnKeysFromObject(this.cropObj['manualCoordinates']).length > 0) {
      if (this.imageAnalysisService.returnKeysFromObject(this.cropObj['manualCoordinates']).length > 1) {
        this.cropObj['cropperPosition'] = {
          "x1": (this.cropObj['manualCoordinates']['x1'] / 100) * event['width'],
          "y1": (this.cropObj['manualCoordinates']['y1'] / 100) * event['height'],
          "x2": (this.cropObj['manualCoordinates']['x2'] / 100) * event['width'],
          "y2": (this.cropObj['manualCoordinates']['y2'] / 100) * event['height']
        };
      } else {
        this.cropObj['cropperPosition'] = {
          "x1": 0,
          "y1": 0,
          "x2": event['width'],
          "y2": event['height']
        };
      }
    } else if (
      this.cropObj['imageCropType'] == 'auto' &&
      this.imageDetail['ImageStripSize'] != "" &&
      this.imageDetail['ImageStripSize'] > 0
    ) {
      let stripePercentage = (this.imageDetail['ImageStripSize'] / this.imageDetail['shape'][0]) * 100;
      this.cropObj['cropperPosition'] = {
        "x1": 0,
        "y1": 0,
        "x2": event['width'],
        "y2": (event['height'] - (stripePercentage / 100) * event['height'])
      };
    } else {
      this.cropObj['cropperPosition'] = {
        "x1": 0,
        "y1": 0,
        "x2": event['width'],
        "y2": event['height']
      };
    }
    this.cropObj['imageCropperLoaded'] = true;
    this.apiCall = false;
  }

  setCropPostion() {
    let shape = this.imageDetail.shape;
    if (this.cropObj['imageCropType'] != 'auto') {
      if (this.imageAnalysisService.returnKeysFromObject(this.cropObj['manualCoordinates']).length > 1) {
        this.cropObj['cropperPosition'] = {
          "x1": (this.cropObj['manualCoordinates']['x1'] / 100) * shape[1],
          "y1": (this.cropObj['manualCoordinates']['y1'] / 100) * shape[0],
          "x2": (this.cropObj['manualCoordinates']['x2'] / 100) * shape[1],
          "y2": (this.cropObj['manualCoordinates']['y2'] / 100) * shape[0]
        };
      } else {
        this.cropObj['cropperPosition'] = {
          "x1": 0,
          "y1": 0,
          "x2": shape[1],
          "y2": shape[0]
        };
      }
    } else if (
      this.cropObj['imageCropType'] == 'auto' &&
      this.imageDetail['ImageStripSize'] != "" &&
      this.imageDetail['ImageStripSize'] > 0
    ) {
      let stripePercentage = (this.imageDetail['ImageStripSize'] / shape[0]) * 100;
      this.cropObj['cropperPosition'] = {
        "x1": 0,
        "y1": 0,
        "x2": shape[1],
        "y2": (shape[0] - (stripePercentage / 100) * shape[0])
      };
    } else {
      this.cropObj['cropperPosition'] = {
        "x1": 0,
        "y1": 0,
        "x2": shape[1],
        "y2": shape[0]
      };
    }
  }

  checkCropChanges() {
    let check = false;
    if (this.cropObj['imageCropType'] != 'auto') {
      if (
        JSON.stringify(this.imageDetail['manual_coordinates']) !==
        JSON.stringify(this.cropObj['manualCoordinates'])
      ) {
        check = true;
      }
    } else {
      if (this.imageDetail['cropImageType'] != this.cropObj['imageCropType']) {
        check = true;
      }
    }
    if (check) {
      this.cropObj['imageCropChanged'] = true;
    } else {
      this.cropObj['imageCropChanged'] = false;
    }
  }
  getDisplayedImageSize() {
    let img = document.getElementsByClassName('source-image');
    return { width: img[0].clientWidth, height: img[0].clientHeight };
  }

  cropImageCropped(event: any) {
    this.cropObj['cropImageShape'] = this.getDisplayedImageSize();
    let disWidth = this.imageDetail.shape[1];
    let disHeight = this.imageDetail.shape[0];
    let width = event['width'];
    let height = event['height'];

    var x1Percentage = (event['imagePosition']['x1'] / disWidth) * 100;
    var y1Percentage = (event['imagePosition']['y1'] / disHeight) * 100;
    var x2Percentage = (event['imagePosition']['x2'] / disWidth) * 100;
    var y2Percentage = (event['imagePosition']['y2'] / disHeight) * 100;

    var widthPercentage = (width / disWidth) * 100;
    var heightPercentage = (height / disHeight) * 100;

    let coordinates = {
      x1: x1Percentage,
      y1: y1Percentage,
      x2: x2Percentage,
      y2: y2Percentage,
      w: widthPercentage,
      h: heightPercentage,
      autoCropBar: false,
    };

    if (this.cropObj['imageCropperLoaded']) {
      if (this.cropObj['imageCropType'] == 'auto') {
        this.cropObj['tempImage'] = event['objectUrl'];
        this.cropObj['croppedImageWidth'] = event['width'];
        this.cropObj['croppedImageHeight'] = event['height'];
      } else {
        this.cropObj['tempImage'] = event['objectUrl'];
        this.cropObj['croppedImageWidth'] = width;
        this.cropObj['croppedImageHeight'] = height;
      }
      this.cropObj['manualCoordinates'] = coordinates;
      this.cropObj['cropperSetupDone'] = true;
      if (this.cropObj['cropperSetupDone']) {
        this.cropObj['imageCropChanged'] = true;
      }
    }

    // let imageToBeApplyOnCanvas = this.imageDetail;
    // this.cropObj['cropImageShape'] = this.getDisplayedImageSize();
    // let disWidth = this.cropObj['cropImageShape']['width'];
    // let disHeight = this.cropObj['cropImageShape']['height'];
    // let width = event['cropperPosition']['x2'] - event['cropperPosition']['x1'];
    // let height =
    //   event['cropperPosition']['y2'] - event['cropperPosition']['y1'];
    // var x1Percentage = (event['cropperPosition']['x1'] / disWidth) * 100;
    // var y1Percentage = (event['cropperPosition']['y1'] / disHeight) * 100;
    // var x2Percentage = (event['cropperPosition']['x2'] / disWidth) * 100;
    // var y2Percentage = (event['cropperPosition']['y2'] / disHeight) * 100;
    // var widthPercentage = (width / disWidth) * 100;
    // var heightPercentage = (height / disHeight) * 100;

    // let coordinates = {
    //   x1: x1Percentage,
    //   y1: y1Percentage,
    //   x2: x2Percentage,
    //   y2: y2Percentage,
    //   w: widthPercentage,
    //   h: heightPercentage,
    //   autoCropBar: false,
    // };

    // if (this.cropObj['imageCropperLoaded']) {
    //   if (this.cropObj['imageCropType'] == 'auto') {
    //     this.cropObj['tempImage'] = event['objectUrl'];
    //     this.cropObj['croppedImageWidth'] = event['width'];
    //     this.cropObj['croppedImageHeight'] = event['height'];
    //   } else {
    //     this.cropObj['tempImage'] = event['objectUrl'];
    //     this.cropObj['croppedImageWidth'] = Math.round(
    //       (widthPercentage / 100) * imageToBeApplyOnCanvas['shape'][1],
    //     );
    //     this.cropObj['croppedImageHeight'] = Math.round(
    //       (heightPercentage / 100) * imageToBeApplyOnCanvas['shape'][0],
    //     );
    //   }
    //   this.cropObj['manualCoordinates'] = coordinates;
    //   this.cropObj['cropperSetupDone'] = true;
    //   if (this.cropObj['cropperSetupDone']) {
    //     this.cropObj['imageCropChanged'] = true;
    //   }
    // }
  }

  reloadImageCropper() {
    const originalImage = this.imageBlobs.originalImage;
    const rotatedImage = this.imageBlobs.rotatedImage;

    // Temporarily reset the imageURL to null
    this.imageBlobs.rotatedImage = null;
    this.imageBlobs.originalImage = null;

    // Use setTimeout to delay the update back to the original value, triggering re-render
    setTimeout(() => {
      this.imageBlobs.originalImage = originalImage;
      this.imageBlobs.rotatedImage = rotatedImage;
    }, 0);
  }


  cropImageloaded(_event: any) {
    this.cropObj.imageCropperLoaded = true;
  }
  resetCroppingOptions() {
    this.cropObj = {
      imageLoaded: false,
      imageCropType: 'auto',
      imageCropperLoaded: false,
      cropperSetupDone: false,
      manualCoordinates: {},
      cropperPosition: {},
      tempCropperPoition: {},
      cropImageShape: {},
      imageCropChanged: false,
      stripSize: '',
      tempImage: '',
      croppedImageWidth: 0,
      croppedImageHeight: 0,
      readyCrop: 0,
    };
  }

  initImageMasking() {
    this.editModeType = 'mask';
    setTimeout(() => {
      this.initializeCanvas()
      this.getImageMasking();
    }, 50);

  }

  initializeCanvas() {

    if (this.imageBlobs.modifiedImage) {
      this.maskCanvasElement.nativeElement.width = this.imageDetail.manual_shape[1]
      this.maskCanvasElement.nativeElement.height = this.imageDetail.manual_shape[0]
    }
    const canvas = this.maskCanvasElement.nativeElement;
    this.ctx = canvas.getContext('2d')!;
    this.redrawImage();
  }

  getImageMasking() {
    this.isMaskModified = false;
    var payload = {
      "categorized_data_id": this.selectedFolder._id,
      "image": this.imageDetail.path,
      "category": this.imageDetail.category
    }

    this.imageAnalysisService.getImageMasking(payload).then((response) => {
      if (response) {
        this.image_masking = response.data
        setTimeout(() => {
          this.redrawMasks();
        }, 50);

        const selectedMask = this.image_masking.find(mask => mask.apply);

        if (!selectedMask && this.image_masking.length > 0) {
          this.image_masking[0].apply = true;
          this.selectedMask = this.image_masking[0]
          this.updateImageMasking(this.selectedMask, "", false);
        }
        else {
          this.selectedMask = this.image_masking.find(mask => mask.apply) || null;
        }
      }
    });
  }

  setImageForMasking(): void {
    if (this.imageBlobs.modifiedImage) {
      const canvas = this.maskCanvasElement.nativeElement;
      this.cachedImage = new Image();
      this.cachedImage.src = this.imageBlobs.modifiedImage;
      this.cachedImage.onload = () => {
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        this.ctx.drawImage(this.cachedImage, 0, 0, canvas.width, canvas.height);
        this.imageLoaded = true;
        this.redrawMasks();
      };

      this.cachedImage.onerror = (error: any) => {
        console.error('Failed to load image:', error);
      };
    }
  }

  redrawMasks() {
    const canvas = this.maskCanvasElement.nativeElement;
    this.ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (this.imageLoaded) {
      this.ctx.drawImage(this.cachedImage, 0, 0, canvas.width, canvas.height);
    }
    this.image_masking.forEach(mask => {
      let x1 = (mask.coordinates.x1 * canvas.width) / 100;
      let y1 = (mask.coordinates.y1 * canvas.height) / 100;
      let width = (mask.coordinates.w * canvas.width) / 100;
      let height = (mask.coordinates.h * canvas.height) / 100;

      this.ctx.save();
      this.ctx.fillStyle = this.addAlpha('#1A7A7F', 0.3);
      this.ctx.strokeStyle = '#1A7A7F';
      this.ctx.lineWidth = 2;

      this.ctx.fillRect(x1, y1, width, height);
      this.ctx.strokeRect(x1, y1, width, height);
      this.ctx.restore();

      this.ctx.save();
      this.ctx.fillStyle = '#000000';
      this.ctx.font = '16px Arial';
      this.ctx.fillText(mask.mask_name, x1 + 5, y1 + 20);

      this.ctx.restore();
    });
  }


  addCanvasEventListeners() {
    const canvas = this.maskCanvasElement.nativeElement;

    this.eventListeners.push(this.renderer.listen(canvas, 'mousedown', (event: MouseEvent) => {
      if (this.imageLoaded) {
        this.isDrawing = true;
        this.startX = event.offsetX;
        this.startY = event.offsetY;
        this.isDragging = false;
      }
    }));

    this.eventListeners.push(this.renderer.listen(canvas, 'mousemove', (event: MouseEvent) => {
      if (this.isDrawing && this.imageLoaded) {
        const x = event.offsetX;
        const y = event.offsetY;
        this.lastX = x;
        this.lastY = y;

        if (Math.abs(x - this.startX) > 5 || Math.abs(y - this.startY) > 5) {
          this.isDragging = true;
          this.redrawMasks();
          this.drawMask(this.startX, this.startY, x, y);
        }
      }
    }));

    this.eventListeners.push(this.renderer.listen(canvas, 'mouseup', () => {
      if (this.isDrawing) {
        this.isDrawing = false;
        if (this.isDragging) {
          const x1 = Math.min(this.startX, this.lastX);
          const y1 = Math.min(this.startY, this.lastY);
          const width = Math.abs(this.lastX - this.startX);
          const height = Math.abs(this.lastY - this.startY);
          const x2 = x1 + width;
          const y2 = y1 + height;

          const x1_percentage = (x1 / canvas.width) * 100;
          const y1_percentage = (y1 / canvas.height) * 100;
          const x2_percentage = (x2 / canvas.width) * 100;
          const y2_percentage = (y2 / canvas.height) * 100;

          const w_percentage = (width / canvas["width"]) * 100;
          const h_percentage = (height / canvas["height"]) * 100;
          // Generate a dynamic mask name
          const maskName = this.getUniqueMaskName();

          this.image_masking.push({
            coordinates: {
              x1: x1_percentage,
              y1: y1_percentage,
              x2: x2_percentage,
              y2: y2_percentage,
              w: w_percentage,
              h: h_percentage
            },
            color: '#1A7A7F',
            ymax: 0,
            path: true,
            mask_name: maskName,
            apply: false
          });
          this.isMaskModified = true;
          this.isDragging = false;
          this.redrawMasks();
        }
      }
    }));

    this.eventListeners.push(this.renderer.listen(canvas, 'mouseout', () => {
      if (this.isDrawing) {
        this.isDrawing = false;
        if (this.isDragging) {
          this.isDragging = false;
          this.redrawMasks();
        }
      }
    }));
  }


  getUniqueMaskName(): string {
    const existingNumbers = this.image_masking.map(mask => {
      const match = mask.mask_name.match(/^Mask-(\d+)$/);
      return match ? parseInt(match[1], 10) : 0;
    });

    const maxNumber = existingNumbers.length > 0 ? Math.max(...existingNumbers) : 0;
    return `Mask-${maxNumber + 1}`;
  }

  cleanupCanvasEventListeners() {
    this.eventListeners.forEach(unsubscribe => unsubscribe());
    this.eventListeners = [];
  }

  drawMask(startX: number, startY: number, endX: number, endY: number) {
    this.ctx.strokeStyle = '#1A7A7F4D';
    this.ctx.lineWidth = 2;
    this.ctx.strokeRect(startX, startY, endX - startX, endY - startY);
    this.ctx.fillStyle = 'rgba(26, 122, 127, 0.30)';
    this.ctx.fillRect(startX, startY, endX - startX, endY - startY);
  }

  redrawImage() {
    const canvas = this.maskCanvasElement.nativeElement;
    const image = new Image();
    image.src = this.imageBlobs.modifiedImage;
    image.onload = () => {
      this.ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      this.setImageForMasking();
      this.addCanvasEventListeners();
    };

  }

  addAlpha(hex: string, alpha: number): string {
    hex = hex.replace(/^#/, '');

    let r = parseInt(hex.substring(0, 2), 16);
    let g = parseInt(hex.substring(2, 4), 16);
    let b = parseInt(hex.substring(4, 6), 16);

    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  confirmDelete(MaskingObj: any): void {
    const getPayload = {
      "categorized_data_id": this.selectedFolder._id,
      "image": this.imageDetail.path,
      "category": this.imageDetail.category
    };

    this.imageAnalysisService.getImageMasking(getPayload).then((response) => {
      if (response) {
        const maskingData = response.data.filter((value: any) =>
          this.areCoordinatesEqual(value.coordinates, MaskingObj.coordinates)
        );
        if (maskingData.length > 0) {
          this.deleteMaskFromServer(MaskingObj);
        } else {
          this.removeMaskLocally(MaskingObj);
        }
        this.redrawMasks();
        this.MaskingObj = undefined;
      } else {
        this.toaster.error('Failed to fetch image masking data', '', {
          positionClass: 'custom-toast-position',
        });
      }
    }).catch((error) => {
      console.error('An error occurred while fetching image masking data', error);
      this.toaster.error('Error fetching image masking data', '', {
        positionClass: 'custom-toast-position',
      });
    });
  }

  private deleteMaskFromServer(MaskingObj: any): void {
    const payload = {
      "categorized_data_id": this.selectedFolder._id,
      "image": this.imageDetail.path,
      "category": this.imageDetail.category,
      "coordinates": MaskingObj.coordinates
    };

    this.imageAnalysisService.deleteImageMasking(payload).then((response) => {
      if (response !== null) {
        this.removeMaskLocally(MaskingObj);
      } else {
        this.toaster.error('Failed to delete image masking', '', {
          positionClass: 'custom-toast-position',
        });
      }
    }).catch((error) => {
      console.error('An error occurred while deleting image masking', error);
      this.toaster.error('Error deleting image masking', '', {
        positionClass: 'custom-toast-position',
      });
    });
  }

  private removeMaskLocally(MaskingObj: any): void {
    const index = this.image_masking.findIndex(value => this.areCoordinatesEqual(value.coordinates, MaskingObj.coordinates));
    const wasSelected = MaskingObj.apply; // Check if the deleted mask was selected

    if (index !== -1) {
      this.image_masking.splice(index, 1);
      this.toaster.success('Image masking deleted successfully', '', {
        positionClass: 'custom-toast-position',
      });

      // Auto-select the first mask if the deleted mask was the selected one
      if (wasSelected && this.image_masking.length > 0) {
        this.image_masking[0].apply = true;
        this.updateSelectedMask(this.image_masking[0]);

        // this.selectedMask = this.image_masking[0];
        // this.updateImageMasking(this.image_masking[0], "", false);
      }

      setTimeout(() => {
        this.redrawMasks();
      }, 50);
    } else {
      this.toaster.error('Masking object not found locally', 'ERROR', {
        positionClass: 'custom-toast-position',
      });
    }
  }



  areCoordinatesEqual(coords1: any, coords2: any): boolean {
    return (
      coords1.x1 === coords2.x1 &&
      coords1.y1 === coords2.y1 &&
      coords1.x2 === coords2.x2 &&
      coords1.y2 === coords2.y2 &&
      coords1.w === coords2.w &&
      coords1.h === coords2.h
    );
  }

  cancelDelete() {
    this.MaskingObj = undefined;
  }

  createImagesMasking() {
    var getpayload = {
      "categorized_data_id": this.selectedFolder._id,
      "image": this.imageDetail.path,
      "category": this.imageDetail.category
    }

    this.imageAnalysisService.getImageMasking(getpayload).then((response) => {
      if (response) {
        const responseData = response.data;
        const maskingData = [...responseData, ...this.image_masking]
        const coordinatesCount = maskingData.reduce((acc, item) => {
          const key = JSON.stringify(item.coordinates);
          acc[key] = (acc[key] || 0) + 1;
          return acc;
        }, {});
        const uniqueData = maskingData.filter(item => {
          const key = JSON.stringify(item.coordinates);
          return coordinatesCount[key] === 1;
        });

        if (uniqueData.length > 0) {
          var payload = {
            "image_masking": uniqueData,
            "categorized_data_id": this.selectedFolder._id,
            "image": this.imageDetail.path,
            "category": this.imageDetail.category,
            "base_image": this.imageDetail.image,
            "apply_all": false
          };

          this.imageAnalysisService.createImageMasking(payload).then((response) => {
            if (response) {
              // Check if any mask is currently selected
              const selectedMask = this.image_masking.find(mask => mask.apply);
              // If no mask is selected, automatically select the first mask
              if (!selectedMask && this.image_masking.length > 0) {
                this.image_masking[0].apply = true; // Set apply to true for the first mask
                // this.selectedMask = this.image_masking[0]
                this.updateSelectedMask(this.image_masking[0]);
                // this.updateImageMasking(this.selectedMask, "", false);
              }
              this.toaster.success('Image masking has been successfully created.', '', {
                positionClass: 'custom-toast-position',
              });
              this.isMaskModified = false;
            } else {
              this.toaster.error('Image masking creation failed. Please try again.', '', {
                positionClass: 'custom-toast-position',
              });
              this.isMaskModified = true;
            }
          })
            .catch((error) => {
              console.error('Error occurred while creating image masking:', error);
              this.toaster.error('An unexpected error occurred. Please try again later.', '', {
                positionClass: 'custom-toast-position',
              });
            });
        } else {
          this.toaster.error('No masking data found. Please draw the masking on the image.', '', {
            positionClass: 'custom-toast-position',
          });
        }
      }
    })
  }

  editMask(mask: any) {
    this.currentEditMask = mask;
    this.originalName = mask.mask_name || '';

  }

  cancelEdit() {
    if (this.currentEditMask) {
      this.currentEditMask.mask_name = this.originalName;
    }
    this.currentEditMask = null;
  }

  updateSelectedMaskName(maskName: string, index: number): void {
    if (index >= 0 && index < this.image_masking.length && maskName) {
      this.image_masking[index].mask_name = maskName;
      const selectedMask = this.image_masking.find(mask => mask.apply);
      if (!selectedMask) {
        this.image_masking[index].apply = true;
        this.selectedMask = this.image_masking[index];
      }
      this.currentEditMask = null;
      this.updateImageMasking(this.image_masking[index], "nameChange", false);
      setTimeout(() => {
        this.redrawMasks();
      }, 50);
    } else {
      console.warn("Invalid index or mask name.");
    }
  }


  updateSelectedMask(selectedMask: any): void {

    if (this.isSegmentedImage()) {
      const dialogRef = this.dialog.open(ConfirmationImagePrompComponent, {
        width: '400px',
        data: {
          message: 'This image is already segmented. If you proceed, the existing segmentation and annotations will be overwritten. Do you really want to proceed?',
          title: 'Reapply Workflow',
        },
      });

      dialogRef.afterClosed().subscribe(async (action) => {
        if (action && action === true) {
          this.callUpdateSelectedMask(selectedMask, true)
        }
      })
    } else {
      this.callUpdateSelectedMask(selectedMask, false)
    }

  }

  callUpdateSelectedMask(selectedMask: any, applyWorkflow: boolean): void {
    this.image_masking.forEach(mask => {
      mask.apply = (mask === selectedMask);
    });
    this.selectedMask = selectedMask;
    this.updateImageMasking(this.selectedMask, "maskUpdate", applyWorkflow)
  }

  updateImageMasking(mask: any, type: string, applyWorkflow: boolean) {
    var payload =
    {
      "categorized_data_id": this.selectedFolder._id,
      "image": this.imageDetail.path,
      "category": this.imageDetail.category,
      "old_coordinates": mask['coordinates'],
      "new_coordinates": mask['coordinates'],
      "apply_change": true,
      "mask_name": mask.mask_name
    }
    this.imageAnalysisService.updateImageMasking(payload).then((response) => {
      if (response) {
        if (type === "nameChange" && response) {
          this.toaster.success('Mask name updated successfully', '', {
            positionClass: 'custom-toast-position',
          });
        }
        else if (type === "maskUpdate" && response) {
          this.toaster.success('Mask updated successfully', '', {
            positionClass: 'custom-toast-position',
          });
          if (applyWorkflow) {
            this.applyMaskAndSegmentImage(mask)
          }
        }

      } else {
        this.toaster.error('Failed to create image masking', '', {
          positionClass: 'custom-toast-position',
        });
      }
    })
      .catch((error) => {
        console.error('An error occurred while creating image masking', error);
        this.toaster.error(error, '', {
          positionClass: 'custom-toast-position',
        });
      });
  }
  applyMaskAndSegmentImage(mask: any) {
    let detail: any = {
      'base_image': this.imageDetail.manual_image,
      'image': this.imageDetail.image,
      'coordinates': mask['coordinates']
    }
    let coordinates = detail['coordinates'];
    detail['ymax'] = 0;
    detail['path'] = true;

    // this.apiCall = true;

    this.imageAnalysisService.getMaskImage(detail).then((response) => {
      this.apiCall = false;
      if (response) {

        var parsedData = response;
        this.imageDetail['cropimgShape'] = response['cropimg_shape'];
        this.imageDetail['cropimg'] = response['cropimg'];
        this.applyWorkflow('individual', 'mask')
      }
    });
  }


  applyMaskImage(mask: any) {
    if (mask) {
      let detail: any = {
        'base_image': this.imageDetail.image,
        'image': this.imageDetail.manual_image,
        'coordinates': mask['coordinates']
      }
      detail['ymax'] = 0;
      detail['path'] = true;

      this.apiCall = true;

      this.imageAnalysisService.getMaskImage(detail).then((response) => {
        this.apiCall = false;
        if (response) {
          this.imageDetail['cropimg'] = response['cropimg'];
          this.imageDetail['manual_shape'] = response['cropimg_shape'];
          // this.applyWorkflow('individual', 'mask');
        }
      });
    }
  }

  ifCropped(manual_shape: any, shape: any): boolean {
    return manual_shape.length === shape.length &&
      manual_shape.every((val: any, index: any) => val === shape[index]);
  }

}
