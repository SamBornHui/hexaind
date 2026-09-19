import {
  Component,
  ChangeDetectorRef,
  ViewChild,
  ViewChildren,
  QueryList,
  Input,
} from '@angular/core';
import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';
import { ToastrService } from 'ngx-toastr';
import { Router, ActivatedRoute } from '@angular/router';
import {
  forkJoin,
  Observable,
  ObservableInput,
  of,
  Subject,
  Subscription,
} from 'rxjs';
import { ApiService } from 'src/app/services/api.service';
import { catchError, debounceTime, elementAt } from 'rxjs/operators';
import { MatDialog } from '@angular/material/dialog';
import { ViewFullImageDialogBox } from 'src/app/pages/images/segment/view-image-dialog-box/view-full-image-dialog-box.component';
import { WebSocketService } from 'src/app/services/web-sockets.service';
import { ConfigService } from 'src/app/services/config.service';

@Component({
  selector: 'app-image-segment',
  templateUrl: './segment.component.html',
  styleUrls: ['./segment.component.less'],
})
export class ImageSegmentComponent {
  @Input() featureName: any;
  currentUser: any = {};
  cssClass: boolean = false;
  spinnerFlag: boolean = false;
  applyWorkflowFalg: boolean = false;
  showSpinner: boolean = false;
  cssClass1: boolean = false;

  dataLoader: boolean = false;
  projectId: string = '';
  siteId: string = '1';
  datasetId: string = '';
  datasetName: string = '';
  datasetDetails: any = {};
  foldersList: any[] = [];
  filePath: string = '';
  selectedFolderDetails: any = {};
  imageDatasetThumbnails: {} = {};
  folderIds: string[] = [];
  socketResponse: any;

  applyWorkflowToast: any;
  contributors: any;
  currentProject: any;
  screenToDisplay: any = 'folder-view';
  defaultTabView:number = 0;

  folderViewTableHeader: any = [
    'folderName',
    'No. of Images',
    'Status',
    'Spinner',
  ];
  folderViewTableData: any = []; //new MatTableDataSource([]);

  imageGalleryDetails: any = {
    diplayedImagesType: 0,
    galleryOptions: [
      {
        imagesGutterSize: '10px',
        imagesCol: 6,
        rowHeight: '1:1',
        imageTotalCols: [2, 3, 4, 6],
      },
      {
        imagesGutterSize: '10px',
        imagesCol: 6,
        rowHeight: '1:1',
        imageTotalCols: [2, 3, 4, 6],
      },
      {
        imagesGutterSize: '10px',
        imagesCol: 3,
        rowHeight: '1:0.5',
        imageTotalCols: [1, 2, 3],
      },
    ],
  };

  imagesToDisplay: any = [];
  batchProcessedImages: any = [];
  imageDisplayUrl = '/imageAnalysis/showImage?file=';
  loadDataFromDataset: Boolean = false;
  imageLoading: boolean = false;

  constructor(
    private router: Router,
    private activatedRoute: ActivatedRoute,
    private imageAnalysisService: ImageAnalysisService,
    private toaster: ToastrService,
    private apiService: ApiService,
    private cdRef: ChangeDetectorRef,
    private dialog: MatDialog,
    public webSocketService: WebSocketService,
    private configService: ConfigService,
  ) {}

  ngOnInit(): void {    
    if (this.activatedRoute) {
      this.activatedRoute.queryParams.subscribe((params) => {
        this.datasetName = params['datasetName'];
      });
      this.activatedRoute.params.subscribe((params) => {
        this.datasetId = params['datasetId'];
        this.projectId = params['projectId'];
        this.siteId = params['siteId'];
      });
      this.processExpirementalData();
    }
  }
  refreshOnBack(event:any){
    this.processExpirementalData(true)
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

  fetchThumbNailsForImagesInFolder() {
    this.imageLoading = true;
    this.selectedFolderDetails.selectedimages.forEach(
      (image: any, index: number) => {
        this.getImageContent(
          this.selectedFolderDetails.selectedimages[index],
          'thumpnail',
        );
        this.getImageContent(
          this.selectedFolderDetails.selectedimages[index],
          'image',
        );
        this.getImageContent(
          this.selectedFolderDetails.selectedimages[index],
          'manual_image',
        );
        this.getImageContent(
          this.selectedFolderDetails.selectedimages[index],
          'manual_thumbnail',
        );
        this.getImageContent(
          this.selectedFolderDetails.selectedimages[index],
          'segmented_img',
        );
        this.getImageContent(
          this.selectedFolderDetails.selectedimages[index],
          'segmented_imgthumb',
        );
        if (index == this.selectedFolderDetails.selectedimages.length - 1) {
          this.imageLoading = false;
        }
      },
    );
  }
  leftmenuFolderSelection(folder: any) {
    let index = this.foldersList.findIndex(
      (val: any) => val.folderId == folder.folderId,
    );
    this.selectedFolderDetails = this.foldersList[index];
    this.updateFoldersStatus();
    this.viewCategory();
  }
  leftmenuImageSelection(data: any) {}

  processExpirementalData(updateLeftMenu:boolean=false,folderSelected?:any) {
    this.imageAnalysisService
      .getCategorizationData(this.datasetId)
      .then((response) => {
        this.dataLoader = false;
        if (response) {
          if (response && response['categorization_data']) {
            this.foldersList = response['categorization_data'];
            this.foldersList.forEach((element: any, index: number) => {
              this.foldersList[index]['selectedimages'] = element.img_details;
            });
            if(!updateLeftMenu){
              this.foldersList[0]['leftNavExpanded'] = true;
              this.leftmenuFolderSelection(this.foldersList[0]);
            }else{
              let index = this.foldersList.findIndex(
                (val: any) => val.folderId == this.selectedFolderDetails.folderId,
              );
              if(index != -1){
                this.foldersList[index]['leftNavExpanded'] = true;
                this.leftmenuFolderSelection(this.foldersList[index]);
              }
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
  updateFoldersStatus() {
    var ids = [];
    this.folderIds = [];
    for (var i = 0; i < this.foldersList.length; i++) {
      ids.push({
        folderId: this.foldersList[i]['_id'],
        folderName: this.foldersList[i]['folderId'],
      });
      this.folderIds.push(this.foldersList[i]['_id']);
    }
    let reqData = {
      dataset_id: this.datasetId,
      dataset_name: this.datasetName,
      images: ids,
      demo: false,
    };
    this.imageAnalysisService
      .updateFoldersStatus(reqData)
      .then((response: any) => {
        this.dataLoader = false;
        if (response) {
          var statusData = response;
          for (var i = 0; i < statusData.length; i++) {
            let findIndex = this.foldersList.findIndex(
              (val: any) => val['folderId'] == statusData[i]['folderId'],
            );
            if (findIndex > -1) {
              this.foldersList[findIndex]['batch'] = statusData[i]['batch'];
              this.foldersList[findIndex]['workflow'] =
                statusData[i]['workflow'];
            }
          }
        } else {
          this.toaster.error('Failed to fetch the images data', '', {
            positionClass: 'custom-toast-position',
          });
        }
        this.activateTable();
      })
      .catch((error) => {
        console.error('Error fetching mounted drive data:', error);
      });
  }
  activateTable() {
    this.foldersList.forEach((element: any, index: number) => {
      this.foldersList[index]['folderName'] = element.folderId;
    });

    this.folderViewTableData = this.foldersList; // new MatTableDataSource(this.datasetDetails['foldersdata']);
    var batchData = this.folderViewTableData.filter(
      (element: any) => element.batch == 0 && element.workflow == 1,
    );
    if (batchData.length > 0) {
      this.applyWorkflowFalg = true;
    } else {
      this.applyWorkflowFalg = false;
    }
    this.viewCategory();
  }
  checkSelectedFolder() {
    return Object.keys(this.selectedFolderDetails).length > 0 &&
      !this.imageLoading
      ? true
      : false;
  }
  viewCategory() {
    this.imagesToDisplay = [];
    this.selectedFolderDetails['selectedimages'].map((val: any) => {
      if (
        this.imageGalleryDetails.diplayedImagesType == 0 ||
        (this.imageGalleryDetails.diplayedImagesType == 1 &&
          val.segmented_imgthumb != undefined &&
          val.segmented_imgthumb != '') ||
        (this.imageGalleryDetails.diplayedImagesType == 2 &&
          val.segmented_imgthumb != undefined &&
          val.segmented_imgthumb != '')
      ) {
        let imageData = {
          path: val.path,
          image: val.image,
          rawImage: '',
          rawImageThumb: '',
          segmentedImage: val.segmented_img,
          segmentedImageThumb: val.segmented_imgthumb,
          workflowName: val.wfname,
        };
        if (val.crop_type == 'auto') {
          imageData.rawImage = val.modified_path;
          imageData.rawImageThumb = val.modified_thumbnail;
        } else {
          imageData.rawImage = val.manual_image;
          imageData.rawImageThumb =
            val.manual_thumbnail != undefined && val.manual_thumbnail != ''
              ? val.manual_thumbnail
              : val.manual_image;
        }
        this.imagesToDisplay.push(imageData);
      }
    });
  }
  changeDisplayedImagesType(event: any) {
    this.imageGalleryDetails.diplayedImagesType = event.value;
    this.viewCategory();
  }

  changeImagesGridView(val: any) {
    let diplayedImagesType = this.imageGalleryDetails['diplayedImagesType'];
    let imagesCol =
      this.imageGalleryDetails['galleryOptions'][diplayedImagesType][
        'imagesCol'
      ];
    let imageTotalCols =
      this.imageGalleryDetails['galleryOptions'][diplayedImagesType][
        'imageTotalCols'
      ];
    let findIndex = imageTotalCols.findIndex((val: any) => val == imagesCol);
    if (val == 0) {
      if (findIndex > 0 && findIndex <= imageTotalCols.length - 1) {
        this.imageGalleryDetails['galleryOptions'][diplayedImagesType][
          'imagesCol'
        ] = imageTotalCols[findIndex - 1];
      }
      if (findIndex == 0) {
        this.cssClass = true;
        this.cssClass1 = false;
      } else {
        this.cssClass = false;
        this.cssClass1 = true;
      }
    } else {
      if (findIndex >= 0 && findIndex < imageTotalCols.length - 1) {
        this.imageGalleryDetails['galleryOptions'][diplayedImagesType][
          'imagesCol'
        ] = imageTotalCols[findIndex + 1];
      }
      if (findIndex == 3) {
        this.cssClass1 = true;
        this.cssClass = false;
      } else {
        this.cssClass1 = false;
        this.cssClass = true;
      }
    }
  }

  imageFullView(details: any) {
    details['diplayedImagesType'] = this.imageGalleryDetails.diplayedImagesType;
    const dialogRef = this.dialog.open(ViewFullImageDialogBox, {
      minWidth: '30%',
      maxWidth: '50%',
      height: '60%',
      backdropClass: 'add-data-set-backdrop',
      panelClass: 'add-data-set-panel-class',
      data: details,
    });

    dialogRef.afterClosed().subscribe((_dialogResult) => {});
  }

  changePageView(page: string) {
    if (this.returnKeysFromObject(this.selectedFolderDetails).length > 0) {
      this.screenToDisplay = page;
      this.processExpirementalData();
    }
  }

  returnKeysFromObject(inpObj: any) {
    return Object.keys(inpObj);
  }
  applyWorkflow() {
    this.applyWorkflowFalg = false;
    this.webSocketService.connectImagePrgressSocket();

    this.webSocketService.imagePogressSocketMessages.subscribe(
      (response) => {
        if (response.user_id == localStorage.getItem('currUserID')) {
          this.spinnerFlag = true;
          this.socketResponse = response;
          var index = this.foldersList.findIndex(
            (val: any) => val['folderId'] == this.socketResponse.folderId,
          );
          if (
            this.socketResponse.progressbar == '100.0' &&
            this.foldersList[index]['batch'] == 0 &&
            this.foldersList[index]['workflow'] == 1
          ) {
            this.foldersList[index]['batch'] = 1;
          }
          this.folderViewTableData = this.foldersList; //new MatTableDataSource(this.datasetDetails['foldersdata']);
        }
      },
      (error) => {
        console.error('WebSocket error:', error);
      },
    );

    this.folderIds = this.folderIds.toString().split(',');
    let applyData: any = {
      folderIds: this.folderIds,
      project_id: this.configService.SelectedProjectId,
    };
    this.toaster.info('Applying workflows', '', {
      positionClass: 'custom-toast-position',
    });

    this.imageAnalysisService.getCroppedImages(applyData).then(
      (response) => {
        if (response) {
          if (response['status'] && response['status'] == 'completed') {
            setTimeout(() => {
              this.processExpirementalData();
              this.spinnerFlag = false;
            }, 3000);
            if (response['status_message']) {
              this.toaster.success(
                'Applied Workflow.' + response['status_message'],
                '',
                {
                  positionClass: 'custom-toast-position',
                },
              );
            } else {
              this.toaster.info('Applied Workflow', '', {
                positionClass: 'custom-toast-position',
              });
            }
          } else {
            this.toaster.error('Failed to apply workflow. Try again!', '', {
              positionClass: 'custom-toast-position',
            });
          }
        }
      },
      (_error) => {
        this.toaster.error('Failed to apply workflow. Try again!', '', {
          positionClass: 'custom-toast-position',
        });
      },
    );
  }

  setSelectedFolder(folderData: any) {
    this.selectedFolderDetails = folderData;
  }

  ngAfterViewInit() {}

  ngOnDestroy() {
    this.webSocketService.disconnectImageSocket();
  }

  onResize(event?: Event) {}

  onNavigateBackSegment() {
    this.processExpirementalData(true);
  }
}
