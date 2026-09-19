import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { DataPreviewComponent } from '../data-preview/data-preview.component';
import { ConfigService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ModelsService } from 'src/app/pages/models/services/models.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';

@Component({
  selector: 'app-image-video-preview',
  templateUrl: './image-video-preview.component.html',
  styleUrls: ['./image-video-preview.component.less']
})
export class ImageVideoPreviewComponent {
  previewURL: any;
  showSpinner: boolean = true;
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<DataPreviewComponent>,
    private errorHandlerService: ErrorHandlerService,
    private configService: ConfigService,
    private modelsService: ModelsService,
  ) { }

  ngOnInit(): void {
    if (this.data.fileExtension === 'png' || this.data.fileExtension === 'mp4') {
      this.getVisulaizationPreview();
    }
  }

  getVisulaizationPreview() {
    var Json = {
      path: this.data.selectedNode.full_path,
      name: this.data.selectedNode.name,
    }
    this.modelsService
      .getConfusionMetricsFileContent(
        Json
      )
      .subscribe(
        (result) => {
          this.previewURL = result;
          setTimeout(() => {
            this.showSpinner = false;
          }, 1000);
        },
        (error) => {
          console.error('Error while previewing the file content:', error);
          this.errorHandlerService.handleError(error);
        },
      );
  }
}
