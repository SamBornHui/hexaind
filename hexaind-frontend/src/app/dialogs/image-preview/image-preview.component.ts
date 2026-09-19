import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { image } from 'd3';
import { ImageAnalysisService } from 'src/app/pages/images/services/image-analysis.service';

@Component({
  selector: 'app-image-preview',
  templateUrl: './image-preview.component.html',
  styleUrls: ['./image-preview.component.less'],
})
export class ImagePreviewComponent implements OnInit {
  segImageLoader: boolean = false;

  dropDownVisualization = {
    type: 'solid',
    val: 'Black/white (default)',
    disVal: 'Black/white (default)',
    mainVal: 'solid,Black/white (default),Black/white (default)'
  };

  segImage: any = {
    segImageBlob: '',
    manImageBlob: '',
    segImageLoader: false,
    manImageLoader: false
  };

  originalImageSize: { width: number; height: number; sizeKB?: number } | null = null;
  modifiedImageSize: { width: number; height: number; sizeKB?: number } | null = null;
  SegmentedImageResponse: any;

  constructor(@Inject(MAT_DIALOG_DATA) public data: any,
    public imageAnalysisService: ImageAnalysisService) { }

  ngOnInit() {
    if (this.data.view === 'segmented') {
      this.fetchSegmentedImagePath();
      this.getSegmentedImages();
    }
  }

  async fetchSegmentedImagePath(): Promise<void> {
    try {
      const payload = { path: this.data.image.path };
      this.SegmentedImageResponse = await this.imageAnalysisService.segmentedImagePath(payload);
    } catch (error) {
      this.SegmentedImageResponse = ''
      console.error('Error fetching segmented image path:', error);
    }
  }

  getImageName(filePath: string): string {
    return filePath ? filePath.split('/').pop() || '' : '';
  }

  isSegmentedImageAvailable(): boolean {
    const img = this.data?.image?.segmented_img;
    return this.data?.view === 'segmented' && !!(img && img.trim().length > 0);
  }

  isVisualizationDisabled(): boolean {
    return (
      this.SegmentedImageResponse?.data?.preprocessedlayers?.length === 0 &&
      this.SegmentedImageResponse?.data?.segmentationlayers?.length === 0
    );
  }

  getSegmentedImages() {
    this.segImage.manImageLoader = true;
    this.segImage.segImageLoader = true;

    this.imageAnalysisService
      .getIndividualImageContent({ path: this.data.segmented_image, name: this.getImageName(this.data.segmented_image) })
      .subscribe(
        async (o_result: string) => {
          this.segImage.segImageBlob = o_result;
          this.segImage.segImageLoader = false;
          this.imageAnalysisService
            .getIndividualImageContent({ path: this.data.manual_image, name: this.getImageName(this.data.manual_image) })
            .subscribe(
              async (m_result: string) => {
                this.segImage.manImageLoader = false;
                this.segImage.manImageBlob = m_result;
              },
              (error) => {
                console.error('Error fetching modified image content:', error);
              }
            );
        },
        (error) => {
          console.error('Error fetching segmented image content:', error);
        }
      );
  }

  changeVisualization(event: any) {
    this.segImage.segImageLoader = true;
    let val = event.value;
    if (val !== "") {
      let split_val = val.split(',');
      this.dropDownVisualization = {
        type: split_val[0],
        val: split_val[1],
        disVal: split_val[2],
        mainVal: val
      };
      let visualization_val = "";
      let colorVal = "";

      if (this.dropDownVisualization.type === 'solid') {
        visualization_val = this.dropDownVisualization.val;
        if (this.dropDownVisualization.disVal == undefined) {
          colorVal = "";
          visualization_val = ""
        }
      }
      else if (this.dropDownVisualization.type === 'outline_segmented') {
        visualization_val = this.dropDownVisualization.type;
        colorVal = this.dropDownVisualization.val;
      }
      else {
        visualization_val = this.dropDownVisualization.type;
        colorVal = this.dropDownVisualization.val;
        if (this.dropDownVisualization.val == "label segmented") {
          visualization_val = "label segmented"
          colorVal = "";
        }
      }

      this.updateSegmentedImage(visualization_val, colorVal);
    } else {
      this.dropDownVisualization = {
        type: 'solid',
        val: 'Black/white (default)',
        disVal: 'Black/white (default)',
        mainVal: 'solid,Black/white (default),Black/white (default)'
      };
    }
  }

  async updateSegmentedImage(visualization: string, color: string): Promise<void> {
    this.segImage.segImageLoader = true;
    try {
      const generatedPayload = this.generatePayload(
        this.data.image,
        this.data.workflow,
        visualization,
        color
      );
      const segmentedResponse = await this.imageAnalysisService.getCroppedAndSegmentedImage(generatedPayload);
      const segmentedImgPath = segmentedResponse?.imagedata?.segmented_img;
      if (!segmentedImgPath) {
        return;
      }

      this.imageAnalysisService.getIndividualImageContent({
        path: segmentedImgPath,
        name: this.getImageName(segmentedImgPath),
      }).subscribe(
        (o_result: string) => {
          this.segImage.segImageBlob = o_result;
          this.segImage.segImageLoader = false;
        },
        (error) => {
          console.error('Error fetching segmented image content:', error);
          this.segImage.segImageLoader = false;
        }
      );

    } catch (error) {
      console.error('Unexpected error in updateSegmentedImage:', error);
      this.segImage.segImageLoader = false;
    }
  }

  generatePayload(imageData: any, workflowData: any, visualization: any, color: any,) {
    const imagePath = this.getFilteredImage(this.SegmentedImageResponse.data);
    return {
      PixleX: imageData.PixelSizeX,
      PixleY: imageData.PixelSizeY,
      applied: false,
      path: true,
      draw_val: imageData.scalebar_options.scalebarByImage,
      popup_val: imageData.scalebar_options.scalebarByPhysical,
      popup_unit: imageData.scalebar_options.scalebarByPhysicalUnit,
      images_names: ['test'],
      image: imagePath,
      original_image: imageData.image,
      orignalpath: imageData.path,
      sample_image: imageData.croppedImage,
      workflow: [
        {
          _id: workflowData._id,
          retrieve: false,
          features: workflowData.workflow.segmentationWorkflowFeatures.concat(
            workflowData.workflow.postprocessingWorkflowFeatures
          ),
          post_visualization: {
            visualization: visualization,
            color: color
          }
        }
      ],
      user_id: workflowData.user_id
    };
  }
  getFilteredImage(data: any): string {
    if (data.preprocessedlayers?.length) {
      return data.preprocessedlayers[data.preprocessedlayers.length - 1].filterd_image;
    } else if (data.segmentationlayers?.length) {
      return data.segmentationlayers[data.segmentationlayers.length - 1].filterd_image;
    }
    return '';
  }
}
