import { ChangeDetectorRef, Component, Inject, ViewChild } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ConfigService, WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from 'src/app/controls/widget-control/widget-control';
import {
  Widget,
  DataCopyWidgetConfig,
  LocalFileConfiguration,
  WidgetType,
  SourceType,
  BigQueryDatasetConfiguration,
  MountedDriveConfiguration,
  DatasetModel,
} from 'src/app/models/workflow-models';
import { BigQueryConfigComponent } from 'src/app/controls/configs/big-query-config/big-query-config.component';
import { DataPreviewService } from './services/data-preview.service';
import { DomSanitizer } from '@angular/platform-browser';
import { DataPreviewDataComponent } from './data/data.component';
import { ApiService } from 'src/app/services/api.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { DataService } from 'src/app/pages/data/services/data.service';

@Component({
  selector: 'app-data-preview',
  templateUrl: './data-preview.component.html',
  styleUrls: ['./data-preview.component.less'],
})
export class DataPreviewComponent {
  @ViewChild(DataPreviewDataComponent) dataPreviewDataComponent!: DataPreviewDataComponent;

  public widgetControl: WidgetControl | undefined = undefined;
  config: DataCopyWidgetConfig | undefined = undefined;
  datasetId: string | undefined = '';
  datasetIds: DatasetModel[] = [];
  activeTab: number = 0;
  isPNG: boolean = false;
  resultPNG: any;
  UC2SigmaDataPreviewPath: any;
  isDatasetDropdown = false;
  filePath: any;
  fileName: any = "";

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<DataPreviewComponent>,
    private editWorkflowService: WorkflowCanvasService,
    private sanitizer: DomSanitizer,
    private configService: ConfigService,
    private cdr: ChangeDetectorRef,
    private apiService: ApiService,
    private errorHandlerService: ErrorHandlerService,
    private dataPreviewService: DataPreviewService
  ) {
    if (!this.editWorkflowService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.editWorkflowService.selectedWidgetControl;
    this.config = this.widgetControl.Widget.config as DataCopyWidgetConfig;
  }

  private handleBlob(
    blob: Blob,
    fileName: string
  ) {
    const blobUrl = window.URL.createObjectURL(blob);
    this.triggerDownload(blobUrl, fileName);
  }

  private triggerDownload(blobUrl: string, fileName: string) {
    const link = document.createElement('a');
    link.href = blobUrl;

    let nameWithoutExtension: string;
    if (fileName.includes('.')) {
      nameWithoutExtension = fileName.split('.').slice(0, -1).join('.');
    } else {
      nameWithoutExtension = fileName;
    }

    link.setAttribute('download', nameWithoutExtension + '.zip');
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(blobUrl);
    link.remove();
  }

  ngOnInit() {
    if (typeof this.data.datasetId === 'string') {
      this.datasetId = this.data.datasetId;
      if (this.data.fullPath || this.data.fileName) {
        const extension = this.data.fullPath.substring(this.data.fullPath.lastIndexOf('.'));
        if (this.data.fileName.includes(extension)) {
          this.fileName = this.data.fileName;

        } else {
          this.fileName = this.data.fileName + extension;
        }
      } else {
        this.getDatasetInformation(this.data.datasetId);
      }
    } else if (Array.isArray(this.data.datasetId)) {
      this.datasetIds = this.data.datasetId;
      this.datasetId = this.datasetIds[0].id;
      this.fileName = this.datasetIds[0].name;
      this.isDatasetDropdown = true;
    }

    this.checkPNG();
    if (this.data.uc2SigmaFilePath) {
      this.UC2SigmaDataPreviewPath = this.data.uc2SigmaFilePath
      this.activeTab = 1;
      this.cdr.detectChanges();
    }
  }

  onDatasetChange() {
    this.activeTab = 0;
  }

  async getDatasetInformation(datasetId: any) {
    var datasetInformation: any = await this.dataPreviewService.getMetadata(datasetId);
    this.fileName = datasetInformation.name ?? ""
  }

  checkPNG() {
    if (this.datasetId && this.data.isPNG) {
      this.isPNG = this.data.isPNG;
      this.resultPNG = this.sanitizer.bypassSecurityTrustResourceUrl(`${this.configService.getAppAuxApiURL}/eda/file?path=${this.data.full_path}`);
    }
  }

  refreshData() {
    if (this.dataPreviewDataComponent) {
      this.dataPreviewDataComponent.refreshData();
    }
  }

  async onDownloadTriggered(filePath: any) {
    this.apiService
      .downloadWorkflowResultData([{ file_path: filePath }])
      .subscribe({
        next: (blob: Blob) =>
          this.handleBlob(blob, filePath),
        error: (error: any) => {
          console.error('Download failed:', error);
          this.errorHandlerService.handleError(error);
        },
      });
  }
}
