import { Component, ViewChild, ElementRef } from '@angular/core';
import { Connector } from 'src/app/models/connector-models';
import {
  Widget,
  TextWidgetConfig,
  LocalTextConfiguration,
  SourceTextConfig,
  SourceType,
  SinkTextWidget,
} from 'src/app/models/workflow-models';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { DataService } from 'src/app/pages/data/services/data.service';
import { MatDialog } from '@angular/material/dialog';
import { MountedDriveDataPreviewComponent } from '../../../dialogs/mounted-drive-data-preview/mounted-drive-data-preview.component';
import { ApiService } from 'src/app/services/api.service';
import { SettingsComponent } from '../settings/settings.component';
import { ThemePalette } from '@angular/material/core';
import { ProgressBarMode } from '@angular/material/progress-bar';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { ShowDatasetDialogComponent } from 'src/app/dialogs/show-dataset-dialog/show-dataset-dialog.component';
import { WorkflowDesignerComponent } from 'src/app/pages/workflow-designer/workflow-designer.component';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-text-widget-config',
  templateUrl: './text-widget-config.component.html',
  styleUrls: ['./text-widget-config.component.less']
})
export class TextWidgetConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  // @ViewChild('workflowDesigner')
  // workflowDesigner!: WorkflowDesignerComponent;
  @ViewChild('fileInput')
  fileInput!: ElementRef;
  selectedOption: string | undefined = undefined;
  connectors: Connector[] = [];
  textDescription: string = '';
  textName: string = '';
  files: any;
  isUpload: boolean = false;
  changeMade: boolean = false;
  config: TextWidgetConfig | undefined = undefined;
  configCache: TextWidgetConfig | undefined = undefined;
  outputName: string | undefined = undefined;

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
  uploadedFiles: any[] = [];
  datasetsFiles: any[] = [];
  isWorkflowDesignerVisible = false;

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private dataService: DataService,
    public dialog: MatDialog,
    private apiService: ApiService,
    public sharedDataService: SharedDataService,
    public toaster: ToastrService,
    private workflowDesigner: WorkflowDesignerComponent,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.activeWidget = this.widgetControl?.Widget;
    this.config = this.widgetControl.Widget.config as TextWidgetConfig;
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
      type: this.config?.widget_type,
      description: 'retrieves Text data for further processing upstream',
      version: "1.0",
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


  showMountedDriveDialog() {
    const dialogRef = this.dialog.open(MountedDriveDataPreviewComponent, {
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: {
        type: 'text',
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
          // this.configCache.source.type = SourceType.MOUNTED_DRIVE;
          // this.configCache.source.configuration = new MountedDriveConfiguration(
          //   result.dataset_id,
          // );
          this.fileName = result.path;
        }
      }
    });
  }


  async onFileSelected(event: any): Promise<void> {
    const files: FileList = event.target.files;
    if (files && files.length > 0) {
      try {
        const siteId = "1";
        const projectId = this.workflowCanvasService.SelectedWorkflow?.project_id;
        const workflowId = this.workflowCanvasService.SelectedWorkflow?._id;

        if (!siteId || !projectId || !workflowId) {
          throw new Error('Required IDs are missing.');
        }

        const name = this.activeWidget?.name || 'DefaultWidgetName';
        const description = 'default_widget_description';

        this.apiService
          .UploadMultipleFiles(
            files,
            siteId,
            projectId,
            workflowId,
            name,
            description,
            'EXTERNAL',
            'TEXT',
            (progress) => {
              this.progress = progress;
            }
          )
          .subscribe(
            (response) => {
              if (response) {
                if (!this.configCache) this.configCache = new TextWidgetConfig();
                if (!this.configCache.source) this.configCache.source = [];
                if (!this.configCache.sink) this.configCache.sink = [];

                if (files.length !== response.length) {
                  console.error('Mismatch between number of files and dataset IDs returned.');
                  return;
                }

                const currentLength = this.configCache!.source.length;

                response.forEach((element: any, ind: number) => {
                  const newIndex = currentLength + ind;

                  this.configCache!.source[newIndex] = new SourceTextConfig(SourceType.LOCAL, new LocalTextConfiguration());
                  (this.configCache!.source[newIndex].configuration as LocalTextConfiguration).dataset_id = element.dataset_id;

                  this.configCache!.sink[newIndex] = new SinkTextWidget();
                  this.configCache!.sink[newIndex].dataset_name = files[ind]?.name || 'Unknown file';
                  this.configCache!.sink[newIndex].dataset_description = 'dataset description';
                });

                this.loadDatasets();
                this.fileUploaded = true;
                this.changeMade = true;
                this.isUpload = true;
                this.progress = 100;
              }
            },
            (error) => {
              console.error('Error during file upload:', error);
              this.resetUploadState();
            }
          );
      } catch (error) {
        console.error('Error during file selection or upload:', error);
      }
    } else {
      console.warn('No files selected for upload.');
    }
  }


  private resetUploadState(): void {
    this.fileUploaded = false;
    this.changeMade = false;
    this.isUpload = false;
    this.progress = 0;
  }

  async loadDatasets() {
    if (this.configCache) {
      for (let index = 0; index < this.configCache.source.length; index++) {
        const source = this.configCache.source[index].configuration as LocalTextConfiguration;

        if (source?.dataset_id) {
          // Ensure dataset_id is treated as an array
          const datasetIds = Array.isArray(source.dataset_id) ? source.dataset_id : [source.dataset_id];
          if (datasetIds.length > 0) {
            try {
              const datasetDetails = await Promise.all(
                datasetIds.map((id) => this.dataService.getDataset(id))
              );

              this.datasetsFiles = datasetDetails
                .filter((details: any) => details.name && details._id)
                .map((details: any) => ({
                  dataset_id: details._id,
                  dataset_name: details.name,
                }));

              this.fileUploaded = this.datasetsFiles.length > 0;
            } catch (error) {
              console.error('Error loading datasets:', error);
              this.fileUploaded = false;
            }
          } else {
            console.warn('No valid dataset IDs found in the configuration.');
          }
        } else {
          console.warn('No dataset_id property found in the configuration.');
        }
      }
    } else {
      console.warn('Config cache is not defined.');
    }
  }




  onContinue() {
    if (this.selectedOption === 'local') {
      this.fileInput.nativeElement.click();
    }
    if (this.selectedOption === 'mounted') {
      // this.showMountedDriveDialog();
    }
    if (this.selectedOption === 'platform') {
      this.showPlatformDatasetsDialog();
    }
  }

  showPlatformDatasetsDialog() {
    const dialogRef = this.dialog.open(ShowDatasetDialogComponent, {
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: { type: 'text' }
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.setDataset(result.dataset);
        this.fileUploaded = true;
        this.progress = 100;
        this.fileName = result.dataset.name;
      }
    });
  }

  setDataset(dataset: any) {
    if (this.configCache) {
      this.changeMade = true;
      this.configCache.source[0].type = SourceType.MOUNTED_DRIVE;

      if (
        this.configCache.source[0].configuration &&
        'dataset_id' in this.configCache.source[0].configuration
      ) {
        const config = this.configCache.source[0].configuration as LocalTextConfiguration;
        config.dataset_id = dataset._id || "";
        if (!this.configCache.sink[0].dataset_name || this.configCache.sink[0].dataset_name) {
          this.configCache.sink[0].dataset_name = "";
        }
        if (!this.configCache.sink[0].dataset_description || this.configCache.sink[0].dataset_description) {
          this.configCache.sink[0].dataset_description = "";
        }

        this.configCache.sink[0].dataset_name = dataset.name;
        this.configCache.sink[0].dataset_description = dataset.description;
        this.fileUploaded = true;
        this.changeMade = true;
        this.isUpload = true;
        this.progress = 100;
      } else {
        console.error('Source configuration is not defined or is not of type LocalTextConfiguration.');
      }
    }
  }


  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
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
    if (this.configCache) {
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
    this.configCache = JSON.parse(JSON.stringify(this.config));
    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
    }
    this.changeMade = false;
    this.fileUploaded = false;
  }

  isDatasetEmpty(): boolean {
    if ((this.configCache?.sink?.[0]?.dataset_name ?? "") === "" &&
      (this.configCache?.sink?.[0]?.dataset_description ?? "") === "" ||
      (this.configCache?.sink?.length ?? 0) === 0) {
      return false;
    } else {
      return true;
    }
  }

  deleteTextFile(index: any) {
    try {
      let configuration = this.configCache?.source[index]['configuration'] as LocalTextConfiguration;
      if (!configuration || !configuration.dataset_id) {
        throw new Error('Invalid configuration or dataset_id');
      }

      const payload = {
        dataset_ids: [configuration.dataset_id],
        dataset_type: "TABULAR",
      };

      this.dataService.DeleteDataset(payload).subscribe({
        next: (res: any) => {
          if (res.response?.[0]?.status === 'SUCCESS') {
            this.toaster.success('Dataset deleted successfully', '', {
              positionClass: 'custom-toast-position'
            });
            this.configCache?.source.splice(index, 1);
            this.configCache?.sink.splice(index, 1);
            this.onSave();
            this.workflowDesigner.saveWorkflow(false);
          } else {
            console.error('Dataset deletion failed:', res);
          }
        },
        error: (err: any) => {
          console.error('Error during dataset deletion:', err);
        },
      });
    } catch (error) {
      console.error('Error in deleteTextFile method:', error);
    }
  }

}
