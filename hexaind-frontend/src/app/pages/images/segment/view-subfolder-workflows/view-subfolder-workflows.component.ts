import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  OnInit,
  Output,
  SimpleChanges,
} from '@angular/core';
import { Router } from '@angular/router';
import clone from 'clone';
import { ToastrService } from 'ngx-toastr';
// import { SocketService } from 'src/app/services/socket-io-service';
import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';
import { WebSocketService } from 'src/app/services/web-sockets.service';

@Component({
  selector: 'view-subfolder-workflows',
  templateUrl: './view-subfolder-workflows.component.html',
  styleUrls: ['./view-subfolder-workflows.component.less'],
})
export class ViewSubfolderWorkflowsComponent implements OnInit, OnChanges {
  @Output() backButtonFunction = new EventEmitter();
  @Output() navigateBackSegment = new EventEmitter();
  @Output() refreshOnBack = new EventEmitter();

  @Input() datasetId: any;
  @Input() datasetName: any;
  @Input() foldersList: any;
  @Input() selectedFolderDetails: any;

  currentUser: any;
  public apiCall: boolean = false;
  selectedWorkflowTab: any = 0;
  editWorkflowData: any = {};
  saveWorkflowBtn: boolean = false;
  segmentationworkflow: any = {};
  selectedFolderId: any = '';
  selectedFolderName: any = '';
  allWorkFlows: any = [];

  currentProject: any;

  closeType: any = '';
  editWorkflow: boolean = false;
  isBatchProcessingStarted: boolean = false;
  applyWorkflowToastId: any;
  public workflowProgress: number = 0;
  apiFavCall: boolean= false;

  constructor(
    public imageAnalysisService: ImageAnalysisService,
    public router: Router,
    private webSocketService: WebSocketService,
    private toastr: ToastrService,
  ) { }

  ngOnInit() {
    this.selectedWorkflowTab = 0;
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!) as any;
    this.triggerBackButton();
    this.intiImageAnalysisSocket();
    this.viewSegmentedCategory(this.selectedFolderDetails);
  }

  ngOnChanges(changes: SimpleChanges) {
    // Detect changes in input properties
    if (
      changes['selectedFolderDetails'] &&
      !changes['selectedFolderDetails'].isFirstChange()
    ) {
      this.viewSegmentedCategory(this['selectedFolderDetails']);
    }
  }


  intiImageAnalysisSocket() {
    this.webSocketService.connectImageSocket();
    this.webSocketService.imageSocketMessages.subscribe(
      (response) => {
        if (response.user_id == localStorage.getItem('currUserID')) {
          if (response.progressbar !== undefined) {
            this.workflowProgress = response.progressbar;
          }

          let getRow = this.segmentationworkflow['images'].findIndex(
            (innerval: any) => innerval['path'] == response['path'],
          );
          if (getRow >= 0) {
            if (
              this.segmentationworkflow['images'][getRow]['workflowId'] != '' &&
              this.segmentationworkflow['images'][getRow]['workflowId'] != 0 &&
              this.segmentationworkflow['images'][getRow]['workflowId'] != undefined
            ) {
              this.segmentationworkflow['images'][getRow]['appliedId'] =
                response['appliedid'] == 0
                  ? parseInt(response['appliedid'])
                  : response['appliedid'];
            } else {
              this.segmentationworkflow['images'][getRow]['appliedId'] = 0;
            }
          }
        }
      },
      (error) => {
        console.error('WebSocket error:', error);
      },
    );
  }

  viewSegmentedCategory(category: any) {
    let imageData = clone(category.selectedimages);
    this.segmentationworkflow = {
      confirmSegmentedWorkflow: false,
      collectionId: category.folderId,
      workflow: {},
      name: '',
      localStatesBlack: 'Y-Ni',
      localStatesWhite: 'Y-Ni',
      selectedCategory: category.category,
      selectedSegmentedImage: {},
      segmentedImage: '',
      paramsModification: false,
      inputImageForSegmentation: '',
      displayInputImage: '',
      region_properties: {},
      segmentedOutput: {},
      images: imageData,
      scalebar: {},
      temperature: '',
      time: '',
      category: category['category'],
    };
    this.selectedFolderId = category['_id'];
    this.selectedFolderName = category.folderId;

    this.getAllWorkflows(true, this.segmentationworkflow['images']);
    // this.fetchThumbNailsForImagesInFolder()
    this.selectedWorkflowTab = 0;
  }

  fetchThumbNailsForImagesInFolder() {
    this.segmentationworkflow['images'].forEach((image: any, index: number) => {
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
      if (index == this.segmentationworkflow['images'].length - 1) {
        this.getAllWorkflows(true, this.segmentationworkflow['images']);
      }
    });
  }

  getAllWorkflows(callCroppedImages: any, imagesData: any) {
    this.apiCall = true;
    this.allWorkFlows = [];
    this.imageAnalysisService.getAllWorkflows({}).then((response) => {
      this.apiCall = false;
      if (response) {
        let workflowData = response;
        if (workflowData.length > 0) {
          this.allWorkFlows = workflowData;
          this.apiCall = false;
        }

        if (callCroppedImages) {
          this.getCroppedImages(imagesData);
        }
      } else {
        this.toastr.error('Failed to get workflows', '', {
          positionClass: 'custom-toast-position',
        });
      }
    });
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

  getCroppedImages(data: any) {
    this.apiCall = true;
    let reqData = {
      dataset_id: this.datasetId,
      imageData: data,
      foldername: this.datasetName,
      demo: false,
    };
    this.imageAnalysisService.getCroppedImages(reqData).then((response) => {
      if (response) {
        var parsedData = response;
        if (parsedData['croppedimages']) {
          parsedData['croppedimages'].forEach((element: any) => {
            let mainImageIndex = this.segmentationworkflow['images'].findIndex(
              (val: any) => val['path'] == element['tif_path'],
            );
            if (mainImageIndex >= 0) {
              this.segmentationworkflow['images'][mainImageIndex]['imagename'] =
                element['imagename'];
              this.segmentationworkflow['images'][mainImageIndex][
                'croppedImage'
              ] = element['croppedimage'];
              this.segmentationworkflow['images'][mainImageIndex][
                'croppedimage_thumb'
              ] = element['croppedimage_thumb'];
              this.segmentationworkflow['images'][mainImageIndex][
                'workflowId'
              ] = element['workflow_id'];
              this.segmentationworkflow['images'][mainImageIndex]['appliedId'] =
                element['applied_id'];
              this.segmentationworkflow['images'][mainImageIndex][
                'croppedShape'
              ] = [];
              if (
                element['croppedshape'] &&
                element['croppedshape'].length > 0
              ) {
                this.segmentationworkflow['images'][mainImageIndex][
                  'croppedShape'
                ] = element['croppedshape'];
              }
              this.getImageContent(
                this.segmentationworkflow['images'][mainImageIndex],
                'croppedimage_thumb',
              );
            }
          });

          this.segmentationworkflow['images'].forEach(
            (element: any, index: number) => {
              if (element.croppedImage == '') {
                this.getImageContent(
                  this.segmentationworkflow['images'][index],
                  'croppedImage',
                );
                this.getImageContent(
                  this.segmentationworkflow['images'][index],
                  'croppedimage_thumb',
                );
              }
            },
          );
          this.apiCall = false;
        }
      }
      this.apiCall = false;
    });
  }

  invokeAllWorkflowsFunc(event: any) {
    this.getAllWorkflows(event['callCroppedImages'], event['imagesData']);
  }

  changeFavorite(event: any) {
    let obj = {
      workflow_id: event['workflow']['_id'],
      favorite: event['favType'],
    };
    this.apiFavCall = true;
    this.imageAnalysisService.updateFavoriteWorkflow(obj).then((response) => {
      if (response) {
        this.apiFavCall = false
        let workflowIndex = this.allWorkFlows.findIndex((workflow:any)=>workflow._id === event['workflow']['_id']);
        this.allWorkFlows[workflowIndex]['favorite'] = event['favType'];
        let favoriteIndex = this.allWorkFlows[workflowIndex].favorited_by.findIndex((item:any) => item.user_id == this.currentUser._id);
        if(favoriteIndex != -1){
          this.allWorkFlows[workflowIndex].favorited_by[favoriteIndex].favorite = event['favType']
        }else{
          this.allWorkFlows[workflowIndex].favorited_by.push({user_id:this.currentUser._id,favorite:event['favType']})
        }
      }
    });
  }

  changeOutputDirectory(event: any) {
    let obj = {
      workflow_id: event['workflow']['_id'],
      output_directory_options: event['outputDirOptions'],
    };

    this.imageAnalysisService.updateOutputDirectory(obj).then((response) => {
      if (response) {
        this.allWorkFlows.map((val: any) => {
          if (val['_id'] == event['workflow']['_id']) {
            val['output_directory_options'] = event['outputDirOptions'];
          }
        });
      }
    });
  }

  updateSegementation(event: any) {
    this.segmentationworkflow = event;
  }

  resetSegementationCategory() {
    this.segmentationworkflow = {
      confirmSegmentedWorkflow: false,
      collectionId: '',
      workflow: {},
      name: '',
      localStatesBlack: 'Y-Ni',
      localStatesWhite: 'Y-Ni',
      selectedCategory: '',
      selectedSegmentedImage: {},
      segmentedImage: '',
      paramsModification: false,
      inputImageForSegmentation: '',
      displayInputImage: '',
      region_properties: {},
      segmentedOutput: {},
      images: [],
      scalebar: {},
      temperature: '',
      time: '',
      category: '',
    };
    this.selectedFolderId = '';
    this.allWorkFlows = [];
  }

  editWorkflowEvent(event: any) {
    this.editWorkflowData = event;
    this.selectedWorkflowTab = 1;
  }

  activiateApiCall(status: any) {
    this.apiCall = status;
  }

  saveWorkflowBtnEvent(event: any) {
    this.saveWorkflowBtn = event;
    this.updateWorkflowData();
  }


  triggerBackButton() {
    this.imageAnalysisService.closeManageWorkflowChange.subscribe(
      (type: any) => {
        // this[type]();
      },
    );
  }

  startBatchProcessing(event: any) {
    this.isBatchProcessingStarted = event as boolean;
  }

  changeApplyWorkflowToastId(event: any) {
    this.applyWorkflowToastId = event;
  }

  closeBatchToast() {
    if (
      this.applyWorkflowToastId != undefined &&
      this.applyWorkflowToastId != ''
    ) {
      this.toastr.clear(this.applyWorkflowToastId.ToastId);
    }
  }
  updateWorkflowData() {
    this.getAllWorkflows(false, this.segmentationworkflow['images']);
  }
  backToFolders() {
    this.closeType = '';
    if (this.selectedWorkflowTab == 1) {
      if (this.saveWorkflowBtn) {
        this.closeType = 'backToFolders';
        this.imageAnalysisService.triggerSaveWorkfloBtn('backToFolders');
      } else {
        this.editWorkflowData = {};
        this.selectedWorkflowTab = 0;
        this.getAllWorkflows(false, this.segmentationworkflow['images']);
      }
    } else {
      this.closeBatchToast();
      // don't remove this commented line
      // this.backButtonFunction.emit('folder-view');
    }
  }

  backButtonView() {
    this.closeType = '';
    if (this.saveWorkflowBtn) {
      this.closeType = 'backButtonView';
      this.imageAnalysisService.triggerSaveWorkfloBtn('backButtonView');
    } else {
      this.editWorkflowData = {};
      this.selectedWorkflowTab = 0;
      this.closeBatchToast();
      this.router.navigate(['/assets']);
    }
  }

  goToPreview() {
    let viewPage = '/curation/dataset-preview';
    this.router.navigate([viewPage]);
  }

  selectedFirstTabEvent(event: any) {
    this.selectedWorkflowTab = event.tab;
    if (event.callCroppedImages) {
      this.refreshOnBack.emit();
    }
  }

  onNavigateBackToSubfolder() {
    this.navigateBackSegment.emit(this.selectedFolderDetails);
  }
}
