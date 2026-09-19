import { Component, ViewChild, ElementRef } from '@angular/core';
import { Connector } from 'src/app/models/connector-models';
import {
  DataCopyWidgetConfig,
  Widget,
  LocalFileConfiguration,
  SourceType,
  MountedDriveConfiguration,
  WidgetType,
} from 'src/app/models/workflow-models';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { DataService } from 'src/app/pages/data/services/data.service';
import { AssetsListResponse, Dataset } from 'src/app/models/data-models';
import { MatDialog } from '@angular/material/dialog';
import { ShowDatasetDialogComponent } from '../../../dialogs/show-dataset-dialog/show-dataset-dialog.component';
import { MountedDriveDataPreviewComponent } from '../../../dialogs/mounted-drive-data-preview/mounted-drive-data-preview.component';
import { DataPreviewComponent } from 'src/app/dialogs/data-preview/data-preview.component';
import { ApiService } from 'src/app/services/api.service';
import { SettingsComponent } from '../settings/settings.component';
import { ThemePalette } from '@angular/material/core';
import { ProgressBarMode } from '@angular/material/progress-bar';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';

@Component({
  selector: 'app-csv-data-config',
  templateUrl: './csv-data-config.component.html',
  styleUrls: ['./csv-data-config.component.less'],
})
export class CsvDataConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  @ViewChild('fileInput')
  fileInput!: ElementRef;
  selectedOption: string | undefined = undefined;
  connectors: Connector[] = [];
  csvDescription: string = '';
  csvName: string = '';
  files: any;
  isUpload: boolean = false;
  changeMade: boolean = false;
  config: DataCopyWidgetConfig | undefined = undefined;
  configCache: DataCopyWidgetConfig | undefined = undefined;
  outputName: string | undefined = undefined;

  datasets: Dataset[] = [];
  selectedDataset: Dataset | undefined = undefined;
  public widgetControl: WidgetControl | undefined = undefined;
  inputWidgets: Widget[] = [];
  data = {};
  public activeWidget: Widget | undefined;
  fileUploaded: boolean = false;
  outputNameChanged: boolean = false;
  progress = 0;
  size: string = '';
  fileName: string = '';
  color: ThemePalette = 'primary';
  mode: ProgressBarMode = 'determinate';
  bufferValue = 100;

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private dataService: DataService,
    public dialog: MatDialog,
    private apiService: ApiService,
    public sharedDataService: SharedDataService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.activeWidget = this.widgetControl?.Widget;
    this.config = this.widgetControl.Widget.config as DataCopyWidgetConfig;
    this.config.widget_type = WidgetType.DATA_COPY;
    // Deep clone to prevent updates from modifying original
    this.configCache = JSON.parse(JSON.stringify(this.config));
    this.outputName = this.widgetControl.Widget.outputs[0].name;
  }

  ngOnInit() {
    this.loadDatasets();
    this.initializeInformation();
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

  initializeInformation() {
    this.data = {
      type: this.config?.source.type,
      description: 'retrieves CSV data for further processing upstream',
      version: this.config?.source.configuration.version,
    };
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.workflowCanvasService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );
    }
  }

  getDatasetName() {
    return this.configCache?.sink?.dataset_name;
  }

  setDatasetDescription(description: string) {
    if (this.configCache && this.configCache.sink) {
      this.changeMade = true;
      this.configCache.sink.dataset_description = description;
    }
  }

  getDatasetDescription() {
    return this.configCache?.sink?.dataset_description;
  }

  setDatasetName(name: string) {
    if (this.configCache && this.configCache.sink) {
      this.changeMade = true;
      this.configCache.sink.dataset_name = name;
    }
  }

  setDatasetID(name: string) {
    if (this.configCache && this.configCache.sink) {
      this.configCache.sink.dataset_name = name;
    }
  }

  setDataset(dataset: Dataset) {
    this.selectedDataset = dataset;
    if (this.configCache) {
      this.changeMade = true;
      this.configCache.source.type = SourceType.LOCAL;
      let source = this.configCache.source
        .configuration as LocalFileConfiguration;
      source.dataset_id = dataset._id ?? '';
    }
  }

  async loadDatasets() {

    if (this.configCache) {
      let source = this.configCache.source
        .configuration as LocalFileConfiguration;
      if(source.dataset_id) {
        let datasetDetails : any = await this.dataService.getDataset(source.dataset_id)
        if(datasetDetails?.name)
          this.fileName = datasetDetails.name + datasetDetails?.dataset_location[0]?.extension
        if (datasetDetails) {
          this.fileUploaded = true;
        }
      }
    }
  }

  showPlatformDatasetsDialog() {
    const dialogRef = this.dialog.open(ShowDatasetDialogComponent, {
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: {type: 'csv'}
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result && result.success) {
        this.setDataset(result.dataset);
        this.selectedDataset = result.dataset;
        this.fileUploaded = true;
        this.progress = 100;
        this.fileName = result.dataset.name;
      }
    });
  }

  showMountedDriveDialog() {
    const dialogRef = this.dialog.open(MountedDriveDataPreviewComponent, {
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: {
        type: 'csv',
        name: this.activeWidget?.name || '',
        description: this.activeWidget?.description || '',
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        if (this.configCache) {
          this.fileUploaded = true;
          this.progress = 100;
          this.changeMade = true;
          this.configCache.source.type = SourceType.MOUNTED_DRIVE;
          this.configCache.source.configuration = new MountedDriveConfiguration(
            result.dataset_id,
          );
          this.fileName = result.path;
        }
      }
    });
  }

  async onFileSelected(event: any): Promise<void> {
    const file = event.target.files[0];
    console.log(file, 'get file name moun ted');
    if (file) {
      try {
        const name = this.activeWidget?.name || '';
        const description = this.activeWidget?.description || '';
        this.size = this.transform(file.size, 1);
        this.fileName = file.name;

        var workflow_d = this.workflowCanvasService.SelectedWorkflow?._id;
        var project_id =
          this.workflowCanvasService.SelectedWorkflow?.project_id;
        let destination_folder = `p_${project_id}/wf_${workflow_d}`;

        this.apiService
          .UploadCsvFileDestinationFolder(
            file,
            name,
            description,
            'INTERNAL',
            destination_folder,
            workflow_d,
            (progress) => {
              this.progress = progress;
            },
          )
          .subscribe({
            next: (response) => {
              if (response && this.configCache) {
                this.fileUploaded = true;
                this.changeMade = true;
                this.configCache.source.type = SourceType.LOCAL;
                let source = this.configCache.source
                  .configuration as LocalFileConfiguration;
                source.dataset_id = response.dataset_id;
              }
            },
            error: (error) => {
              console.error('Upload failed:', error);
            },
          });
      } catch (error) {
        console.error('Error during file selection:', error);
      }
    }
    this.isUpload = true;
  }

  onContinue() {
    if (this.selectedOption === 'local') {
      this.fileInput.nativeElement.click();
    }
    if (this.selectedOption === 'mounted') {
      this.showMountedDriveDialog();
    }
    if (this.selectedOption === 'platform') {
      this.showPlatformDatasetsDialog();
    }
  }

  getDatasetID() {
    if (this.configCache) {
      if (this.configCache.source.type === SourceType.LOCAL) {
        let source = this.configCache.source
          .configuration as LocalFileConfiguration;
        return source.dataset_id;
      } else if (this.configCache.source.type === SourceType.MOUNTED_DRIVE) {
        let source = this.configCache.source
          .configuration as MountedDriveConfiguration;
        return source.dataset_id;
      }
    }
    return undefined;
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  openDataPreviewDialog() {
    if (this.getDatasetID()) {
      const dialogRef = this.dialog.open(DataPreviewComponent, {
        width: '95vw',
        maxWidth: '95vw',
        height: '95%',
        data: {
          datasetId: this.getDatasetID(),
        },
      });
      dialogRef.afterClosed().subscribe((result) => {});
    }
  }

  transform(bytes: number, decimalPoint: number) {
    if (bytes == 0) return '0 Bytes';
    const k = 1000;
    const dm = decimalPoint;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  get widgetOutput(): string | undefined {
    return this.outputName;
  }

  set widgetOutput(value: string | undefined) {
    this.outputName = value;
    this.changeMade = true;
  }

  onAppSettingsUpdated() {
    this.changeMade = true;
  }

  onSave() {
    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.settingsComponent.SaveAppSettings();

    if (!this.widgetControl) {
      return;
    }

    if (this.configCache && this.configCache.sink) {
      this.configCache.sink.dataset_name = 'csv_dataset';
      this.configCache.sink.dataset_description = 'csv_dataset_description';
      this.widgetControl.Widget.config = this.configCache;
      this.config = this.widgetControl?.Widget.config;
      this.configCache = JSON.parse(JSON.stringify(this.config));
    }

    if (this.outputName) {
      this.outputName = this.outputName.trim();
      if (
        this.widgetControl.Widget.outputs &&
        this.widgetControl.Widget.outputs.length > 0
      ) {
        this.widgetControl.Widget.outputs[0].name = this.outputName;
      }
    }

    this.changeMade = false;
  }

  onCancel() {
    this.settingsComponent.RevertAppSetting();
    // Deep clone to prevent updates from modifying original
    this.configCache = JSON.parse(JSON.stringify(this.config));
    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
    }
    this.changeMade = false;
    this.fileUploaded = false;
  }
}
