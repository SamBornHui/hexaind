import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';
import { ImagePreviewComponent } from 'src/app/dialogs/image-preview/image-preview.component';
import { MatDialog, MatDialogConfig, MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'images-grid',
  templateUrl: './images-grid.component.html',
  styleUrls: ['./images-grid.component.less'],
})
export class ImagesGridComponent implements OnInit {
  @Input() image: any;
  @Input() imgIndex: any;
  @Input() unassigned: any;
  @Input() workflow: any;
  @Input() selectedSegmentImages: any;
  @Input() expandedWorkflowData: any;
  @Input() isBatchProcessingStarted: boolean = false;
  @Input() imageType: string = 'raw';

  @Output() selectSegImagesEvent = new EventEmitter();
  @Output() deassignWorkflowEvent = new EventEmitter();
  @Output() displaySegmentationImageEvent = new EventEmitter();

  currentUser: any = {};
  unassignedWorkflow: boolean = false;

  imageDisplayUrl = '/imageAnalysis/showImage?file=';

  constructor(
    private imageAnalysisService: ImageAnalysisService,
    private dialog: MatDialog
  ) { }

  ngOnInit() {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    this.updateImagesBlob();
  }

  imageFullView(image: any) {
    if (image.segmented_img && image.segmented_img != '') {
      let inputData = {
        view: 'segmented',
        manual_image: (image.croppedImage && image.croppedImage != '') ? image.croppedImage : image.manual_image,
        segmented_image: image.segmented_img,
        image: this.image,
        workflow: this.workflow
      }
      const dialogRef = this.dialog.open(ImagePreviewComponent, {
        width: '90%',
        height: '90%',
        data: inputData,
      });

      // this.imageAnalysisService
      // .getIndividualImageContent({ path: image.segmented_img, name: image.imagename })
      // .subscribe(
      //   (o_result) => {
      //     let segImage = o_result
      //     let manual_imagePath = (image.croppedImage && image.croppedImage !='')?image.croppedImage:image.manual_image;
      //     this.imageAnalysisService
      //       .getIndividualImageContent({ path: manual_imagePath, name: image.imagename })
      //       .subscribe(
      //         (m_result) => {
      //           const dialogRef = this.dialog.open(ImagePreviewComponent, {
      //             width: '90%',
      //             height: '90%',
      //             data: { view:'segmented', manual_image: m_result, segmented_image: segImage },
      //           });
      //         },
      //         (error) => {
      //           console.error('Error fetching image content:', error);
      //         },
      //       );
      //   },
      //   (error) => {
      //     console.error('Error fetching image content:', error);
      //   },
      // );
    }
  }

  showRawImage() {
    return this.imageType == 'raw' || this.imageType == 'combine'
      ? true
      : false;
  }
  showSegmentedImage() {
    return this.imageType == 'segmented' || this.imageType == 'combine'
      ? true
      : false;
  }

  updateImagesBlob() {
    if (
      !('croppedimage_thumb' in this.image) ||
      this.image['croppedimage_thumb'] == ''
    ) {
      this.image['croppedimage_thumb'] = this.image['manual_thumbnail'];
      this.getImageContent(this.image, 'croppedimage_thumb');
    }
    if (this.imageType != 'raw') {
      if (
        !('segmented_imgthumb' in this.image) ||
        this.image['segmented_imgthumb'] != ''
      ) {
        this.getImageContent(this.image, 'segmented_imgthumb');
      }
    }
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
  checkWorkflowAssigned() {
    return this.image &&
      'workflowId' in this.image &&
      this.image.workflowId != '' &&
      this.image.workflowId != 0
      ? true
      : false;
  }

  checkWorkflowApplied() {
    return this.image &&
      'appliedId' in this.image &&
      this.image.appliedId != '' &&
      this.image.appliedId != 0
      ? true
      : false;
  }

  selectSegImages(checked: any, image: any, unassigned: any, workflow: any) {
    this.selectSegImagesEvent.emit({
      checked: checked,
      image: image,
      unassigned: unassigned,
      workflow: workflow,
    });
  }

  checkImageSelected(imagePath: any) {
    let ind = this.selectedSegmentImages.findIndex(
      (val: any) => val['path'] == imagePath,
    );
    if (ind >= 0) {
      return true;
    } else {
      return false;
    }
  }

  deassignWorkflow(image: any) {
    this.deassignWorkflowEvent.emit(image);
  }

  displaySegmentationImage(image: any, editType: string) {
    this.displaySegmentationImageEvent.emit({
      image: image,
      editType: editType,
    });
  }
}
