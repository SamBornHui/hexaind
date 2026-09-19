import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  OnInit,
  Output,
  QueryList,
  SimpleChanges
} from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import clone from 'clone';

import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';
import { DragulaService } from 'ng2-dragula';
import {
  ImageAnalysisDialogBoxComponent,
  ImageAnalysisDialogBoxModel,
} from '../../image-analysis-dialog-box/image-analysis-dialog-box.component';
import { ApplyWorkflowsDialogboxComponent } from './apply-workflows-dialogbox/apply-workflows-dialogbox.component';
import { ConfigService } from 'src/app/services/config.service';
import { ViewSubfolderWorkflowsComponent } from '../view-subfolder-workflows.component';
import { ImagesGridComponent } from './images-grid/images-grid.component';
import { ImageSegmentComponent } from '../../segment.component';
import { Router, ActivatedRoute } from '@angular/router';

interface Image {
  workflowId?: string | number; // Define an interface for image objects
  // Add other properties as needed
}

@Component({
  selector: 'view-images-and-workflows',
  templateUrl: './view-images-and-workflows.component.html',
  styleUrls: ['./view-images-and-workflows.component.less'],
})
export class ViewImagesAndWorkflowsComponent implements OnInit, OnChanges {
  @Input() selectedWorkflowTab: any;
  @Input() datasetId: any;
  @Input() datasetName: any;
  @Input() apiCall: boolean;
  @Input() segmentationworkflow: any;
  @Input() selectedFolderId: any;
  @Input() selectedFolderName: any;
  @Input() allWorkFlows: any;
  @Input() isBatchProcessingStarted: any;
  @Input() workflowProgress: number = 0;
  @Input() foldersList: any;

  @Output() activiateApiCallEvent = new EventEmitter();
  @Output() changeFavoriteEvent = new EventEmitter();
  @Output() updateSegementationEvent = new EventEmitter();
  @Output() invokeAllWorkflowsFuncEvent = new EventEmitter();
  @Output() editWorkflowEvent = new EventEmitter();
  @Output() changeOutputDirectoryEvent = new EventEmitter();
  @Output() batchProcessingEvent = new EventEmitter();
  @Output() applyWorkflowToastIdEvent = new EventEmitter();
  @Output() navigateBackToSubfolder = new EventEmitter<void>();

  isCollapsedUnassigned = false;
  isWorkflowSection: boolean[] = [];

  imagesDisplayView: string = 'raw';

  currentUser: any;
  folderIds: any = [];

  expandedWorkflowData: any = {};
  selectedSegmentImages: any = [];

  imageDisplayUrl = '/imageAnalysis/showImage?file=';
  batchExposedAPI = '/imageSegmentation/processBatchImages';

  dragImagesSubscription: any;

  applyWorkflowToast: any;

  sortWorkflows: any = {
    currSubFolderWorkflows: {
      favoriteWorkflows: [],
      unfavoriteWorkflows: [],
      sortedWorkflows: [],
      initialWorkflows: [],
    },
    favoriteWorkflowsTab: {
      favoriteWorkflows: [],
      unfavoriteWorkflows: [],
      sortedWorkflows: [],
      initialWorkflows: [],
    },
    otherDirectoryWorkflows: {
      favoriteWorkflows: [],
      unfavoriteWorkflows: [],
      sortedWorkflows: [],
      initialWorkflows: [],
    },
    otherDatasetWorkflows: {
      favoriteWorkflows: [],
      unfavoriteWorkflows: [],
      sortedWorkflows: [],
      initialWorkflows: [],
    },
  };

  warningMessageVisible: boolean = false;
  missingMasksMessage: string = '';
  missingScaleBarsMessage: string = '';
  searchText: string = '';

  constructor(
    public imageAnalysisService: ImageAnalysisService,
    private toastr: ToastrService,
    public dialog: MatDialog,
    private dragulaService: DragulaService,
    private configService: ConfigService,
    private router: Router, private activatedRoute: ActivatedRoute,
    private toaster: ToastrService,
  ) {
    this.apiCall = false;
    this.initializeImageLayer();
    
  }
  noSegmentationDone() {
    let segImages = this.segmentationworkflow['images'].filter(
      (imageVal: any) =>
        imageVal['workflowId'] != undefined &&
        imageVal['workflowId'] != '',
    );
    return segImages.length;

    //return this.getAssignedImagesByWorkflow(this.workflowData).length.length == 0 && this.imagesDisplayView == 'segmented'
  }
  initializeImageLayer() {
    this.dragImagesSubscription = this.dragulaService
      .dropModel('IMAGES_LAYER')
      .subscribe((args: any) => {
        const { item, target } = args;
        if (target['id'] == 'unassigned-sub-container') {
          if (item['workflowId'] != 0) {
            this.deassignWorkflowApi({
              path: item['path'],
              wid: item['workflowId'],
            });
          }
        } else {
          let split_target = target['id'].split('_');
          if (item['workflowId'] != split_target[1]) {
            this.segmentationworkflow['images'].map(
              (imageVal: any, _index: number) => {
                if (
                  imageVal['path'] == item['path'] &&
                  imageVal['workflowId'] != split_target[1]
                ) {
                  let objToPass = {
                    workflow: this.allWorkFlows.find(
                      (val: any) => val['_id'] == split_target[1],
                    ),
                    selectedSegmentImages: [item],
                    aftersavingwf: false,
                    fromOtherFolder: false,
                    removeApppliedStatus: false,
                  };
                  this.assignWorkflowToImages(objToPass);
                }
              },
            );
          }
        }
      });
    if(this.activatedRoute.snapshot.queryParams['view'] && this.activatedRoute.snapshot.queryParams['view'] !=''){
      this.imagesDisplayView = this.activatedRoute.snapshot.queryParams['view'];
    }
  }

  isCalledApi() {
    return this.apiCall === false ? this.apiCall : true;
  }

  ngOnChanges(changes: SimpleChanges) {
    if (
      (changes['segmentationworkflow'] &&
        !changes['segmentationworkflow'].isFirstChange()) ||
      (changes['selectedFolderId'] && !changes['selectedFolderId'].isFirstChange())
    ) {
      this.resetImageHighlights();
    }
  }

  ngOnInit() {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    this.closeExpandedWorkflowFolder();
    this.expandedWorkflowData['expandedFolder'] = 1;
  }

  changeImagesDisplayView(type: string) {
    this.imagesDisplayView = type;

    const currentParams = { ...this.activatedRoute.snapshot.queryParams };

    // Update query parameters without reloading the page
    this.router.navigate([], {
      relativeTo: this.activatedRoute,
      queryParams: { ...currentParams, view: this.imagesDisplayView },
      queryParamsHandling: 'merge', // Merge the new query parameter with existing ones
    });

  }

  activiateApiCall(status: any) {
    this.activiateApiCallEvent.emit(status);
  }

  getHeight() {
    if (
      this.selectedWorkflowTab == 0 &&
      document.querySelector('#workflowscontainer') != null
    ) {
      let workflowscontainerHeight = document.querySelector(
        '#workflowscontainer',
      )!.clientHeight;
      return workflowscontainerHeight - 180 + 'px';
    } else {
      return '100%';
    }
  }

  scrollImages(scrollType: any, scrollContainer: any) {
    let container = document.querySelector('#' + scrollContainer);
    let top;
    let addVal =
      document.querySelector('#' + scrollContainer + ' .image-grid-conatiner')!
        .clientHeight + 100;
    if (scrollType == 'up') {
      top = container!.scrollTop - addVal;
    } else {
      top = container!.scrollTop + addVal;
    }
    container!.scrollTo({ top: top, behavior: 'smooth' });
  }

  getImageWorkflowsByDirName(dirName: string) {
    return this.allWorkFlows.filter((workflow: any) => {
      const isFolderNameMatch = workflow['foldername'] === dirName;
      const isDatasetIdMatch = workflow['dataset_id'] === this.datasetId;
      const hasImages = this.segmentationworkflow['images'].some(
        (image: any) => image['workflowId'] === workflow['_id'],
      );

      // Ensure that we return true if all conditions are met, otherwise return false
      return isFolderNameMatch && isDatasetIdMatch && hasImages;
    });
  }

  getWorkflowsByDirName(dirName: any) {
    this.sortWorkflows.currSubFolderWorkflows.initialWorkflows = this.allWorkFlows.filter((val: any) =>
      val['foldername'] === dirName &&
      val['dataset_id'] === this.datasetId &&
      (this.searchText ? val['Wname'].includes(this.searchText) : true)
    );
    
    let data = this.setTableDataForWorkflowsTabs('curr-sub-folder');
    // this.closeExpandedWorkflowFolder();
    return data;
  }

  getOtherDirWorkflowsByDirName(dirName: any) {
    this.sortWorkflows.otherDirectoryWorkflows.initialWorkflows =
      this.allWorkFlows.filter(
        (val: any) =>
          val['foldername'] != dirName &&
          !val['default'] &&
          val['dataset_id'] == this.datasetId &&
          (this.searchText ? val['Wname'].includes(this.searchText) : true),
      );
    let data = this.setTableDataForWorkflowsTabs('other-dir-workflows');
    // this.closeExpandedWorkflowFolder();
    return data;
  }

  getOtherDatasetWorkflows() {
    this.sortWorkflows.otherDatasetWorkflows.initialWorkflows =
      this.allWorkFlows.filter(
        (val: any) => !val['default'] && val['dataset_id'] != this.datasetId &&
        (this.searchText ? val['Wname'].includes(this.searchText) : true),
      );
    let data = this.setTableDataForWorkflowsTabs('other-dataset-workflows');
    // this.closeExpandedWorkflowFolder();
    return data;
  }

  getFavoriteWorkflows(_dirName: any) {
    return this.allWorkFlows.filter((workflow:any) =>
      workflow.favorited_by.some(
        (fav:any) => fav.user_id === this.currentUser._id && fav.favorite &&
        (this.searchText ? workflow['Wname'].includes(this.searchText) : true),
      )
    );
  }

  getRecommendedWorkflows(dirName: any) {
    return this.allWorkFlows.filter(
      (val: any) =>
        val['foldername'] == dirName &&
        val['dataset_id'] == this.datasetId &&
        val['recommended'] &&
        (this.searchText ? val['Wname'].includes(this.searchText) : true),
    );
  }

  getUnassignedImages(): Image[] {
    return this.segmentationworkflow.images.filter(
      (imageVal: any) => !imageVal.workflowId, // Checks for undefined, null, or falsy values
    );
  }

  getAssignedImagesByWorkflow(workflow: any) {
    return this.segmentationworkflow['images'].filter(
      (imageVal: any) =>
        imageVal['workflowId'] != undefined &&
        imageVal['workflowId'] == workflow['_id'],
    );
  }

  changeFavorite(event: any) {
    this.changeFavoriteEvent.emit(event);
  }

  changeOutputDir(event: any) {
    this.changeOutputDirectoryEvent.emit(event);
  }

  expandWorkflowFolder(type: any) {
    setTimeout((_val: any) => {
      this.expandedWorkflowData['expandedFolder'] = type;
      if (type == 3) {
        this.manageAssignWorkflow({ expanded: true, type: 'add' });
      }
    }, 500);
  }

  manageAssignWorkflow(event: any) {
    let expanded = event['expanded'];
    let manageWorkflowType = event['type'];
    if (manageWorkflowType == 'add') {
      this.selectedSegmentImages = [];
    }
    this.expandedWorkflowData['manageWorkflow'] = expanded;
    this.expandedWorkflowData['manageWorkflowType'] = manageWorkflowType;
    if (!expanded) {
      this.selectedSegmentImages = [];
      if (manageWorkflowType == 'add') {
        this.closeExpandedWorkflowFolder();
      }
    }
  }

  closeExpandedWorkflowFolder() {
    this.expandedWorkflowData = {
      expandedFolder: -1,
      workflowExpanded: false,
      expandedWorkflowId: '',
      manageWorkflow: false,
      manageWorkflowType: '',
    };
    this.selectedSegmentImages = [];
  }

  expandedWorkflow(workflow: any) {
    if (this.expandedWorkflowData['expandedWorkflowId'] != workflow['_id']) {
      this.expandedWorkflowData['expandedWorkflowId'] = workflow['_id'];
    } else {
      this.expandedWorkflowData['expandedWorkflowId'] = '';
    }
  }

  selectSegImages(event: any) {
    let checked = event['checked'];
    let image = event['image'];
    if (checked) {
      if (this.expandedWorkflowData['manageWorkflowType'] == 'add') {
        this.selectedSegmentImages = [];
      }
      this.selectedSegmentImages.push(image);
    } else {
      this.selectedSegmentImages = this.selectedSegmentImages.filter(
        (val: any) => val['path'] != image.path,
      );
    }
  }

  selectAllSegImages(selectType: any, unassignedImage: any, workflow: any) {
    let images;
    if (unassignedImage) {
      images = this.getUnassignedImages();
    } else {
      images = this.getAssignedImagesByWorkflow(workflow);
    }
    images.forEach((imageVal: any) => {
      this.selectSegImages({
        checked: selectType,
        image: imageVal,
        unassigned: unassignedImage,
        workflow: workflow,
      });
    });
  }

  checkSelectAllButtons(unassignedImages: any, workflow: any) {
    let count = 0;
    let images = unassignedImages
      ? this.getUnassignedImages()
      : this.getAssignedImagesByWorkflow(workflow);
    images.forEach((element: any) => {
      if (
        this.selectedSegmentImages.findIndex(
          (val: any) => val['path'] == element['path'],
        ) > -1
      ) {
        count++;
      }
    });
    return count == images.length ? true : false;
  }

  assignWorkflowToImages(event: any): boolean {
    const workflow = event['workflow'];
    const selectedImages = event['selectedSegmentImages'] || [];
    const afterSavingWF = event['aftersavingwf'];
    const fromOtherFolder = event['fromOtherFolder'];
    const removeAppliedStatus = event['removeApppliedStatus'];

    // Collect images associated with the workflow
    this.segmentationworkflow['images'].forEach((img: any) => {
      if (img['workflowId'] === workflow['_id']) {
        selectedImages.push(img);
      }
    });

    // Check if any images are selected
    if (selectedImages.length === 0 && !afterSavingWF) {
      this.manageAssignWorkflow({ expanded: false, type: 'edit' });
      return false;
    }

    // Prepare the request data
    const reqData: any = {
      _id: workflow['_id'],
      image_path: [],
      aftersavingwf: afterSavingWF,
      duplicate: false,
      dataset_id: '',
      project_id: this.configService.SelectedProjectId,
      username: '',
    };

    // Set additional data if coming from another folder
    if (fromOtherFolder) {
      reqData.duplicate = true;
      reqData.username = `${this.currentUser.firstName} ${this.currentUser.lastName}`;
      reqData.foldername = this.selectedFolderName;
      reqData.dataset_id = this.datasetId;
    }

    // Populate image paths for the request
    selectedImages.forEach((val: any) => {
      const appliedId = val['appliedId'] ? val['workflowId'] : 0;
      reqData['image_path'].push({
        image: val['path'],
        PixelSizeX: val['PixelSizeX'],
        PixelSizeY: val['PixelSizeY'],
        workflow_applied: appliedId,
      });
    });

    // Make the API call to assign the workflow
    this.activiateApiCall(true);
    this.imageAnalysisService
      .assignWorflowToImages(reqData)
      .then((response) => {
        if (response) {
          const parsedData = response;
          this.handleSuccessfulAssignment(
            parsedData,
            reqData,
            removeAppliedStatus,
            fromOtherFolder,
          );

          if (!afterSavingWF) {
            this.manageAssignWorkflow({ expanded: false, type: 'edit' });
          }
          this.activiateApiCall(false);
        }
      });
    return true; // Indicate that the function has executed successfully
  }

  private handleSuccessfulAssignment(
    parsedData: any,
    reqData: any,
    removeAppliedStatus: boolean,
    fromOtherFolder: boolean,
  ): void {
    let segmentationWorkflow = clone(this.segmentationworkflow);

    // Update applied status if necessary
    if (removeAppliedStatus) {
      segmentationWorkflow['images'].forEach((indImg: any, imgInd: number) => {
        if (indImg['workflowId'] === reqData['_id']) {
          segmentationWorkflow['images'][imgInd]['appliedId'] = 0;
        }
      });
      this.updateSegementationEvent.emit(segmentationWorkflow);
    }

    // Update workflowId based on assigned image paths
    reqData['image_path'].forEach((val: any) => {
      const getRow = segmentationWorkflow['images'].findIndex(
        (innerval: any) => innerval['path'] === val['image'],
      );
      if (getRow >= 0) {
        segmentationWorkflow['images'][getRow]['workflowId'] = reqData['_id'];
      }
    });

    // Update applied data from the response
    parsedData['applieddata'].forEach((appliedImage: any) => {
      const getRow = segmentationWorkflow['images'].findIndex(
        (innerval: any) => innerval['path'] === appliedImage['appliedpath'],
      );
      if (getRow >= 0) {
        segmentationWorkflow['images'][getRow]['workflowId'] =
          appliedImage['workflow_id'];
        segmentationWorkflow['images'][getRow]['appliedId'] =
          appliedImage['applied_id'];
      }
    });

    this.updateSegementationEvent.emit(segmentationWorkflow);

    // Show success message
    this.showSuccessMessage(parsedData, reqData, fromOtherFolder);
  }

  private showSuccessMessage(
    parsedData: any,
    reqData: any,
    fromOtherFolder: boolean,
  ): void {
    this.toastr.success('Assigned workflow to selected image(s)', '', {
      positionClass: 'custom-toast-position',
    });

    if (fromOtherFolder) {
      this.invokeAllWorkflowsFuncEvent.emit({
        callCroppedImages: true,
        imagesData: this.segmentationworkflow['images'],
      });
    }
  }

  fetchImageIndex(imagePath: string) {
    return this.segmentationworkflow['images'].findIndex(
      (val: any) => val['path'] == imagePath,
    );
  }

  deassignWorkflowApi(details: any) {
    this.activiateApiCall(true);
    let index = this.fetchImageIndex(details['path']);

    this.imageAnalysisService
      .removeWorkflowForImage(details)
      .then((response) => {
        if (response) {
          var parsedData = response;
          if (parsedData['Status'] && parsedData['Status'] == 'completed') {
            let segmentationworkflow = clone(this.segmentationworkflow);
            segmentationworkflow['images'][index]['workflowId'] = 0;
            segmentationworkflow['images'][index]['appliedId'] = 0;
            this.updateSegementationEvent.emit(segmentationworkflow);
            this.toastr.success(
              'Successfully removed the workflow assigned to the image',
              '',
              {
                positionClass: 'custom-toast-position',
              },
            );
          } else {
            this.toastr.error('Failed to remove workflow', '', {
              positionClass: 'custom-toast-position',
            });
          }
        }
        this.activiateApiCall(false);
      });
  }

  deassignWorkflow(image: any) {
    let dialogInfo = {
      title: 'Remove Workflow',
      message:
        'Are you sure you want to remove the assigned workflow for this image?',
      okBtn: 'Proceed',
      closeBtn: 'Cancel',
    };
    const dialogData = new ImageAnalysisDialogBoxModel(dialogInfo);

    const dialogRef = this.dialog.open(ImageAnalysisDialogBoxComponent, {
      width: '550px',
      data: dialogData,
    });

    dialogRef.afterClosed().subscribe((dialogResult: any) => {
      if (dialogResult) {
        let index = this.fetchImageIndex(image['path']);
        if (index != undefined && index >= 0) {
          this.deassignWorkflowApi({
            path: image['path'],
            wid: image['workflowId'],
          });
        } else {
          this.toastr.error('Failed to remove workflow', '', {
            positionClass: 'custom-toast-position',
          });
        }
      }
    });
  }

  deleteWorkflow(workflow: any) {
    let dialogInfo = {
      title: 'Delete Workflow Confirmation',
      message:
        'Are you sure you want to delete the workflow "' +
        workflow['Wname'] +
        '"?',
      okBtn: 'Delete',
      closeBtn: 'Cancel',
    };
    const dialogData = new ImageAnalysisDialogBoxModel(dialogInfo);

    const dialogRef = this.dialog.open(ImageAnalysisDialogBoxComponent, {
      width: '550px',
      data: dialogData,
    });

    dialogRef.afterClosed().subscribe((dialogResult: any) => {
      if (dialogResult) {
        let workflowData = {
          _id: workflow['_id'],
        };
        this.activiateApiCall(true);
        this.imageAnalysisService.deleteWorkflow(workflowData).then((response) => {
          let segmentationworkflow = clone(this.segmentationworkflow);
          segmentationworkflow['images'].forEach((val: any, ind: number) => {
            if (val['workflowId'] == workflow['_id']) {
              segmentationworkflow['images'][ind]['workflowId'] = 0;
              segmentationworkflow['images'][ind]['appliedId'] = 0;
            }
          });

          this.updateSegementationEvent.emit(segmentationworkflow);
          this.allWorkFlows = this.allWorkFlows.filter(
            (val: any) => val['_id'] != workflow['_id'],
          );

          if (
            this.expandedWorkflowData['workflowExpanded'] &&
            this.expandedWorkflowData['expandedWorkflowId'] != '' &&
            workflow['_id'] == this.expandedWorkflowData['expandedWorkflowId']
          ) {
            this.closeExpandedWorkflowFolder();
          }

          this.toastr.success('Workflow Deleted Successfully.', '', {
            positionClass: 'custom-toast-position',
          });

          this.activiateApiCall(false);
        }).catch((error) => {
          console.error('Error deleting workflow:', error);
          this.toastr.error('An error occurred while deleting the workflow. Please try again.', '', {
            positionClass: 'custom-toast-position',
          });
          this.activiateApiCall(false);
        });
      }
    });
  }



  editWorkflowParams(event: any) {
    this.editWorkflow(event['type'], event['workflowData']);
  }

  editWorkflow(type: string, workflowData: any): boolean {
    // Check if a new workflow is being created without selected images
    if (type === 'new' && this.selectedSegmentImages.length === 0) {
      this.toastr.error('Please select an image to add a new workflow', '', {
        positionClass: 'custom-toast-position',
      });
      return false;
    }

    // Construct the base data object
    let data = {
      type: type,
      selectedSegmentImages: this.selectedSegmentImages,
      workflowData: workflowData,
      editType: 'workflow',
      runWorkflow: false,
      imageForWorkflow: '',
      copyWorkflow: false,
    };

    // Handle editing of an existing workflow
    if (type === 'edit') {
      let runWorkflow = false;
      let imageForWorkflow: any = '';
      let copyWorkflow = false;

      // Find the existing image that matches the workflow data
      let imageData = this.segmentationworkflow['images'].find(
        (val: any) =>
          val['path'] === workflowData['image_path'] &&
          (val['workflowId'] === workflowData['_id'] ||
            val['workflowId'] === 0),
      );

      // Determine if images are selected or if a valid image is found
      if (this.selectedSegmentImages.length > 0) {
        runWorkflow = true;
        imageForWorkflow = this.selectedSegmentImages[0]; // Use the first selected image
        if (this.selectedFolderName !== workflowData['foldername']) {
          copyWorkflow = true; // Workflow is being copied to a different folder
        }
      } else if (imageData) {
        runWorkflow = true;
        imageForWorkflow = imageData; // Use the found image data
      } else {
        // Look for any image associated with the workflow
        imageData = this.segmentationworkflow['images'].find(
          (val: any) => val['workflowId'] === workflowData['_id'],
        );
        if (imageData) {
          runWorkflow = true;
          imageForWorkflow = imageData; // Use the found image data
        }
      }

      // If no valid image is found to run the workflow, show an error
      if (!runWorkflow) {
        this.manageAssignWorkflow({ expanded: false, type: type });
        this.toastr.error('Please select an image to edit the workflow', '', {
          positionClass: 'custom-toast-position',
        });
        return false;
      }

      // Update data object with determined values
      data.runWorkflow = runWorkflow;
      data.imageForWorkflow = imageForWorkflow;
      data.copyWorkflow = copyWorkflow;
    }

    // Emit the data for further processing
    this.editWorkflowEvent.emit(data);
    this.manageAssignWorkflow({ expanded: false, type: 'add' });

    return true; // Indicate success
  }

  displaySegmentationImageParams(event: any) {
    this.editWorkflowEvent.emit(event);
    this.manageAssignWorkflow({ expanded: false, type: 'add' });
  }

  checkAllImagesHaveWorkflowsApplied() {
    // Check if there are no images
    return this.segmentationworkflow['images'].every((val: any) => {
      return (
        val['appliedId'] !== '' &&
        val['appliedId'] !== undefined &&
        val['appliedId'] !== 0
      );
    });
  }
  enableApplyWorkflowButtone() {
    let exists = this.segmentationworkflow['images'].filter((val: any) => {
      return (
        (val['appliedId'] == '' ||
          val['appliedId'] == undefined ||
          val['appliedId'] == 0) && (val['workflowId'] != undefined && val['workflowId'] != '' && val['workflowId'] != 0)
      );
    });
    if (exists.length > 0) {
      return false
    } else {
      return true;
    }
  }

  checkAllImagesHaveWorkflows() {
    return this.segmentationworkflow['images'].filter((image: any) => {
      return image['workflowId'] && image['workflowId'] !== 0;
    });
  }

  async batchProcessingConfirmation() {
    var workflow_status: any = await this.updateFoldersStatus();
    var message: string = ''
    if (workflow_status != null && workflow_status['workflow'] == 1) {
      message = ''
    } else {
      message = 'Not all images have workflow assigned'
    }

    let dialogInfo = {
      title: 'Batch Processing Confirmation',
      message: message,
      okBtn: 'Proceed Anyway',
      closeBtn: 'Stay and Assign Workflows',
    };

    const dialogData = new ImageAnalysisDialogBoxModel(dialogInfo);

    const dialogRef = this.dialog.open(ImageAnalysisDialogBoxComponent, {
      width: '550px',
      data: dialogData,
    });

    dialogRef.afterClosed().subscribe((dialogResult: any) => {
      if (dialogResult) {
        this.applyWorkflowPopup();
      }
      else {
        this.resetImageHighlights();
      }
    });
  }

  updateFoldersStatus(): Promise<any> {
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

    return this.imageAnalysisService.updateFoldersStatus(reqData)
      .then((response: any) => {
        if (response) {
          return response.find((folder: { folderId: any; }) => folder.folderId === this.selectedFolderName);
        } else {
          this.toaster.error('Failed to fetch the images data', '', {
            positionClass: 'custom-toast-position',
          });
          return null;
        }
      })
      .catch((error) => {
        console.error('Error fetching mounted drive data:', error);
        throw error;
      });
  }

  applyWorkflows() {
    if (this.warningMessageVisible) {
      this.warningMessageVisible = false;
      this.batchProcessingConfirmation();
      return;
    }

    const batchImages = this.checkAllImagesHaveWorkflows();
    const imagesWithoutMasks = batchImages.filter(
      (image: any) => !image.image_masks || image.image_masks.length === 0
    );
    const imagesWithoutScaleBars = batchImages.filter(
      (image: any) =>
        !image.scalebar_options || image.scalebar_options.scalebar_type === ''
    );
    batchImages.forEach((image: any) => {
      image.hasMask = image.image_masks && image.image_masks.length > 0;
      image.hasScaleBar =
        image.scalebar_options && image.scalebar_options.scalebar_type !== '';
      image.highlightNoMask = imagesWithoutMasks.includes(image);
      image.highlightNoScaleBar = !image.hasScaleBar;
    });

    this.missingMasksMessage = imagesWithoutMasks.length
      ? `${imagesWithoutMasks.length} image(s) do not have masks.`
      : '';

    this.missingScaleBarsMessage = imagesWithoutScaleBars.length
      ? `${imagesWithoutScaleBars.length} image(s) do not have a scale bar.`
      : '';
    if (imagesWithoutMasks.length > 0 || imagesWithoutScaleBars.length > 0) {
      this.warningMessageVisible = true;
    } else {
      this.batchProcessingConfirmation();
    }
  }

  applyWorkflowPopup() {
    let dialogInfo = {};
    const dialogRef = this.dialog.open(ApplyWorkflowsDialogboxComponent, {
      width: '30%',
      disableClose: true,
      panelClass: 'add-data-set-panel-class',
      data: dialogInfo,
    });

    dialogRef.afterClosed().subscribe((dialogResult: any) => {
      if (dialogResult) {
        let data = {
          folderIds: [this.selectedFolderId],
          project_id: this.configService.SelectedProjectId,
        };
        this.batchProcessingEvent.emit(true);

        this.applyWorkflowToast = this.toastr.info(
          'Applying workflows now',
          '',
          {
            positionClass: 'custom-toast-position',
            disableTimeOut: true,
            tapToDismiss: false,
          },
        );
        this.applyWorkflowToastIdEvent.emit(this.applyWorkflowToast);

        this.imageAnalysisService.applyWorkflows(data).then((response) => {
          if (response) {
            if (response['status'] == 'completed') {
              this.navigateBackToSubfolder.emit();
              if (response['status_message']) {
                this.toastr.success(
                  'Applied Workflows.' + response['status_message'],
                  '',
                  {
                    positionClass: 'custom-toast-position',
                  },
                );
              } else {
                this.toastr.success('Applied Workflows', '', {
                  positionClass: 'custom-toast-position',
                });
              }
            } else {
              this.toastr.error('Failed to apply workflow. Try again!', '', {
                positionClass: 'custom-toast-position',
              });
            }
            this.toastr.clear(this.applyWorkflowToast.ToastId);
          } else {
            this.toastr.error('Failed to apply workflow. Try again!', '', {
              positionClass: 'custom-toast-position',
            });
          }
          this.batchProcessingEvent.emit(false);
        });
      }
      else {
        this.resetImageHighlights();
      }
    });
  }

  resetImageHighlights() {
    this.segmentationworkflow.images.forEach((image: any) => {
      delete image.highlightNoMask;
      delete image.highlightNoScaleBar;
    });
    this.warningMessageVisible = false;
  }

  ngOnDestroy() {
    // prevent memory leak when component destroyed
    this.dragImagesSubscription.unsubscribe();
  }

  setTableDataForWorkflowsTabs(type: string): any[] {
    const workflowsMap: any = {
      'curr-sub-folder': this.sortWorkflows.currSubFolderWorkflows,
      'other-dir-workflows': this.sortWorkflows.otherDirectoryWorkflows,
      'other-dataset-workflows': this.sortWorkflows.otherDatasetWorkflows,
    };

    const selectedWorkflows = workflowsMap[type];

    if (!selectedWorkflows) {
      // Return an empty array if the type is not recognized
      return [];
    }

    // Reset favorite and unfavorite arrays
    selectedWorkflows.favoriteWorkflows = [];
    selectedWorkflows.unfavoriteWorkflows = [];

    selectedWorkflows.initialWorkflows.forEach((workflow: any) => {
      if (workflow["favorite"]) {
        selectedWorkflows.favoriteWorkflows.push(workflow);
      } else {
        selectedWorkflows.unfavoriteWorkflows.push(workflow);
      }

    });

    // Combine the favorite and unfavorite workflows
    selectedWorkflows.sortedWorkflows = [
      ...selectedWorkflows.favoriteWorkflows,
      ...selectedWorkflows.unfavoriteWorkflows,
    ];

    return selectedWorkflows.sortedWorkflows;
  }

  toggleCollapse(): void {
    this.isCollapsedUnassigned = !this.isCollapsedUnassigned;
  }

  toggleDiv(index: number): void {
    this.isWorkflowSection[index] = !this.isWorkflowSection[index];
  }

  goToCleanUpPage() {
    this.activatedRoute.queryParams.subscribe((params) => {
      this.datasetName = params['datasetName']
    });
    let queryParams = { datasetName: this.datasetName };
    let imageFeatureLink = `sites/${this.configService.SelectedSiteId}/projects/${this.configService.SelectedProjectId}/image-analysis/${this.datasetId}/cleanup`;
    this.router.navigate([imageFeatureLink], {
      queryParams,
    });
  }
}
