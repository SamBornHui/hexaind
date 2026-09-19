import { Component, ElementRef, ViewChild } from '@angular/core';
import { WidgetControl } from '../../widget-control/widget-control';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';

import {
  InputOutputConfig,
  PostRescaleWidgetConfig,
  Widget,
  WidgetType,
  Workflow,
} from 'src/app/models/workflow-models';
import { ActivatedRoute } from '@angular/router';
import { PostRescaleConfigService } from './services/post-rescale-config.service';
import { ColorPickerService, Cmyk } from 'ngx-color-picker';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';

@Component({
  selector: 'app-post-rescale-config',
  templateUrl: './post-rescale-config.component.html',
  styleUrls: ['./post-rescale-config.component.less'],
})
export class PostRescaleConfigComponent {
  public config: PostRescaleWidgetConfig | undefined = undefined;
  public selectedFile: File | null = null;
  public listOfCustomFiles: any = [];

  public widgetControl: WidgetControl | undefined = undefined;
  private editingWorkflow: Workflow | undefined;
  public workflow_id: string = '';
  public project_id: string = '';
  public site_id: string = '';
  public uploadedFiles: any = [];
  public module_list: any = [];
  public file: any;
  public folder_path: any;
  public module_name: any;
  public module_description: any;
  public selectedOption = 'A';
  displayedColumns: string[] = ['name', 'type', 'actions'];
  dataSource: any[] = [];
  data = {};
  selectedInputWidget: Widget | undefined = undefined;
  inputWidgets: Widget[] = [];

  @ViewChild('customfile') customfile!: ElementRef;

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private route: ActivatedRoute,
    private PRConfigService: PostRescaleConfigService,
    public sharedDataService: SharedDataService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.config = this.widgetControl.Widget.config as PostRescaleWidgetConfig;
    this.config.widget_type = WidgetType.POST_RESCALE;
  }

  ngOnInit() {
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.workflowCanvasService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );

      // Remove any widgets that dont have outputs.
      if (this.inputWidgets && this.inputWidgets.length > 0) {
        this.inputWidgets = this.inputWidgets.filter(
          (widget) => widget.outputs.length > 0,
        );

        if (this.widgetControl.Widget.inputs.length > 0) {
          this.selectedInputWidget = this.inputWidgets.find(
            (t) => t.urn === this.widgetControl?.Widget.inputs[0].urn,
          );
        }
      }
    }

    this.assignedQueryParameters();
    this.getAllModules();
    this.data = {
      type: this.widgetControl?.Widget.type,
      description: this.widgetControl?.Widget.description,
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

  assignedQueryParameters() {
    this.route.queryParams.subscribe((params) => {
      this.workflow_id = params['workflowId'];
      this.project_id = params['projectId'];
      this.site_id = params['siteId'];
    });
  }

  getAllModules() {
    this.PRConfigService.getAllPRModules(
      this.site_id,
      this.project_id,
      10,
      1,
    ).subscribe({
      next: (response) => {
        this.module_list = response['modules'];
      },
      error: (error) => {
        console.error('Upload error', error);
      },
    });
  }

  onFileChanged(event: any) {
    this.file = event.target.files[0];
    this.validateForm();
    if (this.module_name && this.module_description) {
      this.uploadMultipleFiles();
    }
  }

  createFolder() {
    this.PRConfigService.createFolderPath(
      '1',
      '1',
      this.workflow_id,
      'experiments_files_path',
    ).subscribe({
      next: (response) => {
        this.folder_path = response.folder_path;
      },
      error: (error) => {
        console.error('error', error);
      },
    });
  }

  uploadMultipleFiles() {
    const name = this.module_name;
    const description = this.module_description;
    this.PRConfigService.uploadFiles(
      '1',
      '1',
      name,
      description,
      this.file,
    ).subscribe({
      next: (response) => {
        if (this.config) {
          this.config.post_rescale_module_id = response['module_id'];
          this.getAllModules();
        }
      },
      error: (error) => {
        console.error('Upload error', error);
      },
    });
  }

  validateForm() {
    var moduleDescriptionElement = document.getElementById(
      'moduleDescription',
    ) as HTMLInputElement;
    var moduleNameElement = document.getElementById(
      'moduleName',
    ) as HTMLInputElement;
    var errorTextName = document.getElementById('errorTextName');
    var errorTextDescription = document.getElementById('errorTextDescription');

    if (moduleDescriptionElement && moduleNameElement) {
      var moduleDescription = moduleDescriptionElement.value;
      var moduleName = moduleNameElement.value;

      if (errorTextDescription) {
        if (moduleDescription === '') {
          errorTextDescription.textContent =
            'Please fill the module description';
        } else {
          errorTextDescription.textContent = '';
        }
      }

      if (errorTextName) {
        if (moduleName === '') {
          errorTextName.textContent = 'Please fill the module Name';
        } else {
          errorTextName.textContent = '';
        }
      }
    } else {
      console.error(
        "Element with id 'moduleDescription' or 'moduleName' not found",
      );
    }
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  updateDescriptionIfEmpty() {
    // TODO Description does not exist on this config
    // if (this.config && !this.config?.description) {
    //   this.config.description = '';
    // }
  }

  updateOutputPathIfEmpty() {
    if (this.config && !this.config.post_rescale_module_id) {
      this.config.post_rescale_module_id = '';
    }
  }

  getDataCsvWidgetConfig(): Widget | null {
    let dataCsvActivityConfig: Widget = this.widgetControl?.Widget as Widget;

    return dataCsvActivityConfig;
  }

  getInputWidget(index: number): Widget | undefined {
    if (!this.config) {
      return undefined;
    }

    let urn: string | undefined = this.config.inputs[index].urn;
    if (urn) {
      return this.inputWidgets.find((t) => t.urn === urn);
    }

    return undefined;
  }

  setInputWidget(index: number, widget: Widget) {
    this.selectedInputWidget = widget;
    if (this.config) {
      this.config.inputs[index].urn = widget.urn;
    }
  }

  getSelectedInputWidget(): Widget | undefined {
    return this.selectedInputWidget;
  }

  setSelectedInputWidget(widget: Widget) {
    this.selectedInputWidget = widget;
    let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
    inputOutputConfig.name = this.selectedInputWidget.outputs[0].name;
    inputOutputConfig.urn = this.selectedInputWidget.urn;
    if (this.widgetControl) {
      this.widgetControl.Widget.inputs.length = 0;
      this.widgetControl.Widget.inputs.push(inputOutputConfig);
    }
  }

  getWidgetOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let outputConfig: InputOutputConfig = widget.outputs[0];
      return outputConfig.name!;
    }

    return 'Not Set';
  }

  get widgetOutput(): string | undefined {
    if (
      !this.widgetControl?.Widget ||
      !this.widgetControl?.Widget.outputs ||
      this.widgetControl?.Widget.outputs.length === 0
    ) {
      return undefined;
    }
    return this.widgetControl?.Widget.outputs[0].name;
  }

  set widgetOutput(value: string | undefined) {
    if (!this.widgetControl) {
      return;
    }

    if (!value) {
      if (this.widgetControl.Widget) {
        this.widgetControl.Widget.outputs = [];
      }
    } else {
      const newName = value.trim();

      if (
        this.widgetControl.Widget &&
        this.widgetControl.Widget.outputs &&
        this.widgetControl.Widget.outputs.length > 0
      ) {
        this.widgetControl.Widget.outputs[0].name = newName;
      }
    }
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }
}
