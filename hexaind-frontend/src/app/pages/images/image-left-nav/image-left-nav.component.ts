import {
  Component,
  EventEmitter,
  Input,
  Output,
  HostListener,
  ElementRef,
  SimpleChanges,
  OnInit,
  OnChanges,
} from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { ApiService } from 'src/app/services/api.service';
import { Router, ActivatedRoute } from '@angular/router';
import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';

@Component({
  selector: 'app-image-left-nav',
  templateUrl: './image-left-nav.component.html',
  styleUrls: ['./image-left-nav.component.less'],
})
export class ImageLeftNavComponent implements OnInit, OnChanges {
  @Output() navigateEvent: EventEmitter<any> = new EventEmitter();
  leftNavToggle: boolean = false;
  activeContainerIndex: number | null = 0;
  activeRowIndex: number | null = null;
  containers: { leftNavExpanded: boolean; innerRows: any[] }[] = [
    { leftNavExpanded: false, innerRows: [1, 2, 3] },
    { leftNavExpanded: false, innerRows: [1, 2, 3] },
    { leftNavExpanded: false, innerRows: [1, 2, 3] },
  ];
  @Output() headerClicked = new EventEmitter<void>();
  @Output() contentClicked = new EventEmitter<void>();
  @Input() foldersList: any = [];
  @Input() data: any;
  @Input() featureName: any;
  @Input() updateImage: boolean = true;
  selectedFolder:any;
  searchImagesName:string = '';
  datasetId: string = '';
  datasetName: string = '';

  constructor(
    private imageAnalysisService:ImageAnalysisService,
    private activatedRoute:ActivatedRoute
  ) {}

  ngOnInit() {
    if (this.activatedRoute) {
      this.activatedRoute.params.subscribe((params) => {
        this.datasetId = params['datasetId'];
      });
      this.activatedRoute.queryParams.subscribe((params) => {
        this.datasetName = params['datasetName'];
      });
      this.updateFoldersInfo();
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    // Detect changes in input properties
    if (
      changes['foldersList'] &&
      !changes['foldersList'].isFirstChange()
    ) {
      this.updateFoldersInfo();
    }
  }

  updateFoldersInfo() {
    if (this.foldersList.length > 0) {
      this.getfoldersImages(this.foldersList);
    }
  }
  
  getfoldersImages(foldersList: any[]) {
    let reqData = {
      dataset_id: this.datasetId,
      folders: foldersList.map(folder => ({
        foldername: folder.foldername,
        imageData: folder.img_details,
        demo: false,
      })),
    };
  
    this.imageAnalysisService.getfoldersImages(reqData).then((response) => {
      if (response) {
        response.forEach((folderResponse: any, folderIndex: number) => {
          if (folderResponse['croppedimages']) {
            folderResponse['croppedimages'].forEach((element: any) => {
              let mainImageIndex = foldersList[folderIndex].img_details.findIndex(
                (val: any) => val['path'] == element['tif_path'],
              );
              if (mainImageIndex >= 0) {
                foldersList[folderIndex].img_details[mainImageIndex]['imagename'] = element['imagename'];
                foldersList[folderIndex].img_details[mainImageIndex]['croppedImage'] = element['croppedimage'];
                foldersList[folderIndex].img_details[mainImageIndex]['croppedimage_thumb'] = element['croppedimage_thumb'];
                foldersList[folderIndex].img_details[mainImageIndex]['workflowId'] = element['workflow_id'];
                foldersList[folderIndex].img_details[mainImageIndex]['appliedId'] = element['applied_id'];
                foldersList[folderIndex].img_details[mainImageIndex]['croppedShape'] = [];
                if (element['croppedshape'] && element['croppedshape'].length > 0) {
                  foldersList[folderIndex].img_details[mainImageIndex]['croppedShape'] = element['croppedshape'];
                }
              }
            });
          }
          setTimeout(() => {
            this.foldersList[folderIndex].selectedimages = foldersList[folderIndex].img_details;
            this.foldersList[folderIndex].img_details = foldersList[folderIndex].img_details;
          }, 10);
        });
      }
    });
  }

  getCroppedImages(folder:any, folderIndex:number) {
    let reqData = {
      dataset_id: this.datasetId,
      imageData: folder.img_details,
      foldername: this.datasetName,
      demo: false,
    };
    this.imageAnalysisService.getCroppedImages(reqData).then((response) => {
      if (response) {
        var parsedData = response;
        if (parsedData['croppedimages']) {
          parsedData['croppedimages'].forEach((element: any) => {
            let mainImageIndex = folder.img_details.findIndex(
              (val: any) => val['path'] == element['tif_path'],
            );
            if (mainImageIndex >= 0) {
              folder.img_details[mainImageIndex]['imagename'] = element['imagename'];
              folder.img_details[mainImageIndex]['croppedImage'] = element['croppedimage'];
              folder.img_details[mainImageIndex]['croppedimage_thumb'] = element['croppedimage_thumb'];
              folder.img_details[mainImageIndex]['workflowId'] = element['workflow_id'];
              folder.img_details[mainImageIndex]['appliedId'] = element['applied_id'];
              folder.img_details[mainImageIndex]['croppedShape'] = [];
              if (element['croppedshape'] && element['croppedshape'].length > 0) {
                folder.img_details[mainImageIndex]['croppedShape'] = element['croppedshape'];
              }
              setTimeout(() => {
                this.foldersList[folderIndex].selectedimages = folder.img_details
                this.foldersList[folderIndex].img_details = folder.img_details
              }, 10);
            }
          });
        }
      }
    });
  }

  toggleSection(section: string): void {}

  toggleLeftNav() {
    this.leftNavToggle = !this.leftNavToggle;
  }

  displaySearched(path:string){
    if(this.searchImagesName !=''){
      let name = this.getFileName(path)
      return name.toLowerCase().includes(this.searchImagesName);
    }else{
      return true;
    }
  }

  toggleLeftNavExpand(index: number) {
    this.headerClicked.emit(this.foldersList[index]);
    // this.foldersList[index].leftNavExpanded =
    // !this.foldersList[index].leftNavExpanded;

    this.foldersList.forEach((folder: any, i: number) => {
      folder.leftNavExpanded = i === index ? !folder.leftNavExpanded : false;
    });

    // if (this.activeContainerIndex !== null) {
    //   this.foldersList[this.activeContainerIndex].leftNavExpanded = false;
    // }
    // this.headerClicked.emit(this.foldersList[index]);

    if (this.foldersList[index].leftNavExpanded) {
      this.activeContainerIndex = index;
      this.activeRowIndex = null;
    } else {
      this.activeContainerIndex = null;
    }
  }

  setActiveRow(containerIndex: number, rowIndex: number, image: any) {
    // event.stopPropagation();
    this.activeContainerIndex = containerIndex;
    this.activeRowIndex = rowIndex;
    let eventData:any = {
      folder:this.foldersList[containerIndex],
      image:image
    }
    this.contentClicked.emit(eventData);
  }

  getFileName(filePath: string): string {
    if (filePath) {
      const parts = filePath.split('/');
      return parts.pop() || ''; // Returns the last part or an empty string if the path is empty
    } else {
      return '';
    }
  }
  segmentationAppliedImages(folderData:any) {
    if(folderData && folderData.selectedimages && folderData.selectedimages.length>0){
      if(
        folderData['selectedimages'].every(
        (image:any) => (image['appliedId'] != '' && image['appliedId'] != undefined && image['appliedId'] != 0) && 
        (image['workflowId'] != undefined && image['workflowId'] != '' && image['workflowId'] != 0))
      ){
        return 'full';
      }else{
        if(
          folderData['selectedimages'].some(
          (image:any) => (image['appliedId'] != '' && image['appliedId'] != undefined && image['appliedId'] != 0) && 
          (image['workflowId'] != undefined && image['workflowId'] != '' && image['workflowId'] != 0))
        ){
          return 'partial';
        }else{
          if(
            folderData['selectedimages'].some(
            (image:any) => (image['appliedId'] == '' || image['appliedId'] == undefined || image['appliedId'] == 0) && 
            (image['workflowId'] != undefined && image['workflowId'] != '' && image['workflowId'] != 0))
          ){
            return 'assigned';
          }else{
            return  'not'
          }
        }
      }
    }else{
      return  'not'
    }
  }

}
