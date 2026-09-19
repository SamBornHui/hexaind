import { Component, ViewChild, ElementRef } from '@angular/core';
import { Connector } from 'src/app/models/connector-models';
import {
  JupyterWidgetConfig,
  Widget,
  LocalFileConfiguration,
  SourceType,
  MountedDriveConfiguration,
  WidgetType,
  InputOutputConfig,
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
import { JupyterModalComponent } from 'src/app/dialogs/jupyter-modal/jupyter-modal.component';
import { ConfigService } from "src/app/services/config.service";
import { ActivatedRoute, Router, UrlTree } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { firstValueFrom } from 'rxjs'; 

@Component({
  selector: 'app-jupyter-data-config',
  templateUrl: './jupyter-data-config.component.html',
  styleUrls: ['./jupyter-data-config.component.less'],
})
export class JupyterConfigComponent {
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
  config: JupyterWidgetConfig | undefined = undefined;
  configCache: JupyterWidgetConfig | undefined = undefined;
  // outputName: string | undefined = undefined;

  datasets: Dataset[] = [];
  selectedDataset: Dataset | undefined = undefined;
  public widgetControl: WidgetControl | undefined = undefined;
  inputWidgets: Widget[] = [];
  data = {};
  public activeWidget: Widget | undefined;
  fileUploaded: boolean = false;
  // outputNameChanged: boolean = false;
  progress = 0;
  size: string = '';
  fileName: string = '';
  color: ThemePalette = 'primary';
  mode: ProgressBarMode = 'determinate';
  bufferValue = 100;
  projectId: any;
  versionedWorkflowId: string | undefined;
  workflowSessionId: any[] = [];

  displayedColumns: string[] = ['select', 'inputName', 'dataType', 'argumentName'];

  selectedInputWidgets: any[] = [];
  dataTypes: string[] = ['String', 'Number', 'Boolean', 'Date', 'Object'];

  parameterList: { key: string; label: string; value: string }[] = [
    { key: "memory_limit", label: "Memory Limit (RAM)", value: "2G" },
    { key: "cpu_limit", label: "CPU Cores", value: "2" },
    { key: "notebook_dir", label: "Notebook Directory", value: "/home/jovyan/work" },
    { key: "notebook_image", label: "Notebook Image", value: "jupyter/base-notebook:latest" }
  ];
  
  notebookList: string[] = []; 
  selectedNotebook: string = "test";

  
  memoryLimitOptions = ["2G", "4G", "6G", "8G","10G","12G","14G","16G"];
  cpuCoreOptions = [2, 3, 4, 5, 6, 7, 8];
  
  selectedMemoryLimit: string = "2G" ;  // Default memory limit
  selectedCpuCore: number = 2;         // Default CPU core count

  notebookImageOptions = [
    { label: 'Python 3.11', value: 'jupyter/base-notebook:latest' },
    { label: 'Python 3.10.11', value: 'jupyter/base-notebook:python-3.10.11' } 
  ];
  
  selectedNotebookImage: string = "";
  run_id : string = '';

  loading: boolean = false;
  

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private dataService: DataService,
    public dialog: MatDialog,
    private apiService: ApiService,
    public sharedDataService: SharedDataService,
    private configService: ConfigService,
    private route: ActivatedRoute,
    public toaster: ToastrService,
  ) { 
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    console.log(this.widgetControl, "widgetControl");

    if (!this.widgetControl || !this.widgetControl.Widget) {
      console.error("widgetControl or Widget is null!");
      return;
    }

    // Check if config is null and initialize if necessary
    if (!this.widgetControl.Widget.config) {
      console.warn("config is null, initializing with default values");
      this.widgetControl.Widget.config = new JupyterWidgetConfig(WidgetType.JUPYTER);
    }

    this.config = this.widgetControl.Widget.config as JupyterWidgetConfig;
      console.log(this.config, "config initialized");
      this.selectedMemoryLimit = this.config.memory_limit ?? "2G";
      this.selectedCpuCore = this.config.cpu_limit ?? 2;
      this.selectedNotebookImage = this.config.notebook_image ?? "jupyter/base-notebook:latest";
      this.selectedNotebook = this.config.notebook_file ?? "";
      if (this.notebookList.length > 0 && !this.notebookList.includes(this.selectedNotebook)) {
        this.notebookList.push(this.selectedNotebook);
      } else if (this.notebookList.length === 0) {
        this.notebookList = [this.selectedNotebook]; // Ensure at least "Test" is in the list
      }

    this.configCache = JSON.parse(JSON.stringify(this.config)) || {} as JupyterWidgetConfig;
      
    
    console.log(this.configCache?.memory_limit, "configCache",this.selectedNotebook);

    this.widgetControl.Widget.outputs = [];

    // this.outputName = this.widgetControl.Widget.outputs[0].name;
  }

  
  onParameterChange(paramKey: string, paramValue: any) {
    console.log(`Parameter Changed: ${paramKey} = ${paramValue}`);
  
    // Update the selected values dynamically
    switch (paramKey) {
      case 'memoryLimit':
        this.selectedMemoryLimit = paramValue;
        break;
      case 'cpuCores':
        this.selectedCpuCore = paramValue;
        break;
      case 'notebookImage':
        this.selectedNotebookImage = paramValue;
        break;
      default:
        console.warn(`Unhandled parameter change: ${paramKey}`);
    }
  
    // Enable the Save button
    this.changeMade = true;
  
    // Ensure configCache is updated
    if (!this.configCache) {
      this.configCache = new JupyterWidgetConfig(WidgetType.JUPYTER);
    }
  
    // Save the updated value in configCache
    (this.configCache as any)[paramKey] = paramValue;
  
    console.log("Updated ConfigCache:", this.configCache);
  }
  
  

  ngOnInit() {
    this.initializeInformation();
    this.projectId = this.configService.SelectedProjectId;
    console.log(this.projectId,"get data list");
    this.route.queryParams.subscribe((params) => {
      this.versionedWorkflowId = params['versionedWorkflowId'];
      this.workflowSessionId = params['workflowSessionId'];
    });
  }

  initializeInformation() {
    this.data = {
      description: 'retrieves Jupyter widget data for further processing upstream',
      version: this.config?.version,
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

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }


  onAppSettingsUpdated() {
    this.changeMade = true;
  }

  onSave() {
    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.settingsComponent.SaveAppSettings();
  
    if (!this.widgetControl || !this.widgetControl.Widget) {
      console.error("Widget control or Widget is missing!");
      return;
    }
  
    if (!this.configCache) {
      this.configCache = new JupyterWidgetConfig(WidgetType.JUPYTER);
    }
  
    // Sync parameterList values to configCache
    this.parameterList.forEach(param => {
      (this.configCache as any)[param.key] = param.value;
    });
  
    // Assign selected notebook file
    if (this.selectedNotebook) {
      this.configCache.notebook_file = this.selectedNotebook;
    }
  
    // Assign selected memory limit, CPU cores, and notebook image
    this.configCache.memory_limit = this.selectedMemoryLimit;
    this.configCache.cpu_limit = this.selectedCpuCore;
    this.configCache.notebook_image = this.selectedNotebookImage;
  
    // Assign updated config to widget
    this.widgetControl.Widget.config = { ...this.configCache };
  
    // Deep copy to track changes
    this.configCache = JSON.parse(JSON.stringify(this.widgetControl.Widget.config));
  
    console.log("Final Config Payload:", this.configCache);
  
    // Disable Save button after saving
    this.changeMade = false;
  }
  
  
  
  

  

  onCancel() {
    this.settingsComponent.RevertAppSetting();
    // Deep clone to prevent updates from modifying original
    this.configCache = JSON.parse(JSON.stringify(this.config));
    // if (this.widgetControl) {
    //   this.outputName = this.widgetControl.Widget.outputs[0].name;
    // }
    this.changeMade = false;
    this.fileUploaded = false;
  }


  async openJupyterHub(event: Event) {
    event.stopPropagation(); // Prevent unintended execution
    this.loading = true; // Show spinner
  
    try {
      const params = await firstValueFrom(this.route.queryParams);
      const viewingRunId = params['viewingRunId'];
    
      if (viewingRunId) {
        this.run_id = viewingRunId;
      }
    
      const payload = {
        memory_limit: this.selectedMemoryLimit,
        cpu_limit: this.selectedCpuCore,
        notebook_dir: "/home/jovyan/work",
        notebook_image: this.selectedNotebookImage,
        notebook_file: this.selectedNotebook
      };
    
      console.log("Launching JupyterHub with payload:", payload, "Run ID:", this.run_id);
    
      this.apiService.launchServer(payload, this.projectId, this.workflowSessionId, this.run_id)
        .subscribe(
          (response: any) => {
            console.log("Jupyter Server launched successfully", response);
            if (response?.url) {
              window.open(response.url, '_blank');
            } else {
              console.warn("JupyterHub URL not found in response");
            }
            this.loading = false; // Hide spinner after success
          },
          (error: any) => {
            console.error("Error launching Jupyter Server", error);
            this.loading = false; // Hide spinner on error
          }
        );
    } catch (error) {
      console.error("Error fetching query params", error);
      this.loading = false; // Hide spinner if an error occurs
    }
  }
  



    // getWidgetOutputName(widget: Widget): string {
    //   if (widget.outputs.length > 0) {
    //     let outputConfig: InputOutputConfig = widget.outputs[0];
    //     return outputConfig.name!;
    //   }
  
    //   return 'Not Set';
    // }


    isChecked(inputWidget: any): boolean {
      return this.selectedInputWidgets.includes(inputWidget);
    }

    toggleInputSelection(inputWidget: any, isChecked: boolean): void {
      if (isChecked) {
        this.selectedInputWidgets.push(inputWidget);
      } else {
        this.selectedInputWidgets = this.selectedInputWidgets.filter(widget => widget !== inputWidget);
      }
    }

    refreshNotebookList() { 
      console.log('Refreshing notebook list...');
      //this.notebookList = ['notebook1.ipynb', 'notebook2.ipynb', 'new_notebook.ipynb'];
      // Simulating fetching notebooks, replace with actual API call
      this.apiService.GetServerfiles(this.projectId, this.workflowSessionId)
      .subscribe(
        (response: any) => {
          console.log("Jupyter Server launched successfully", response);
          if (Array.isArray(response) && response.length === 0) {
            this.toaster.error('No Notebook Files Found!', '', {
              positionClass: 'custom-toast-position',
            });
          }
          if (response.length != 0) {
          this.notebookList = response;
          this.toaster.success('Notebook Files Found', '', {
            positionClass: 'custom-toast-position',
          });
          }
        },
        (error: any) => {
          console.error("Error launching Jupyter Server", error);
        }
      );
      
    }

    onNotebookSelectionChange(): void {
      this.changeMade = true;
    }
    
}
