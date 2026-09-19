import { Component, ViewChild } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import {
  Connector,
  ConnectorType,
  RescaleConnectorConfiguration,
} from 'src/app/models/connector-models';
import {
  InputOutputConfig,
  MOBOWidgetConfig,
  RescaleWidgetConfig,
  Widget,
  WidgetType,
} from 'src/app/models/workflow-models';
import { ActivatedRoute } from '@angular/router';
import { RescaleWidgetService } from './services/rescale-widget.service';
import { MatDialog } from '@angular/material/dialog';
import { FileEditorDialogComponent } from 'src/app/dialogs/file-editor-view/file-editor-view-dialog.component';
import { SettingsComponent } from '../settings/settings.component';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { ToastrService } from 'ngx-toastr';
import { HttpClient } from '@angular/common/http';

interface inputFilesObject {
  file_name: any;
  file_path: string;
  upload_rescale: boolean;
  rescale_id: string | undefined;
}

@Component({
  selector: 'app-rescale-config',
  templateUrl: './rescale-config.component.html',
  styleUrls: ['./rescale-config.component.less'],
})
export class RescaleConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  changeMade: boolean = false;
  config: RescaleWidgetConfig | undefined = undefined;
  configCache: RescaleWidgetConfig | undefined = undefined;
  outputName: string | undefined = undefined;
  inputName: string | undefined = undefined;

  public widgetControl: WidgetControl | undefined = undefined;
  private projectId: string = '';
  private siteId: string = '';
  private workflowId: string = '';
  connectors: Connector[] = [];
  isAuthenticationFailed: boolean = false;
  isAuthenticationSuccessful: boolean = false;
  spinner: boolean = false;
  data = {};
  selectedFiles: File[] = [];
  selectedInputWidget: Widget | undefined = undefined;
  inputWidgets: Widget[] = [];

  rescaleSriptFiles: [] = [];
  uploadScriptFlag: boolean = false;

  setDefaultInput: boolean = false;
  // changeInputMade: boolean = false;
  // changeSettingMade: boolean = false;
  selectedMOBOWidget: Widget[] = [];

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private apiService: ApiService,
    private route: ActivatedRoute,
    private rescaleService: RescaleWidgetService,
    private dialog: MatDialog,
    public sharedDataService: SharedDataService,
    private toaster: ToastrService,
    private http: HttpClient,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.config = this.widgetControl.Widget.config as RescaleWidgetConfig;
    this.config.widget_type = WidgetType.RESCALE;
    this.configCache = JSON.parse(JSON.stringify(this.config));
    this.route.queryParams.subscribe((params) => {
      this.projectId = params['projectId'];
      this.siteId = params['siteId'];
      this.workflowId = params['workflowId']
        ? params['workflowId']
        : params['workflowSessionId'];
    });
  }

  ngOnInit() {
    this.loadConnectors();

    this.data = {
      type: this.widgetControl?.Widget.type,
      description:
        'Rescale Widget allows supported HEXAIND 3.0 users to access Rescale accounts for performing cloud-based HPC simulations (for version 1.0)',
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

      if (this.widgetControl.Widget.outputs.length) {
        this.outputName = this.widgetControl.Widget.outputs[0].name;
      }

      // Remove any widgets that dont have outputs.
      if (this.inputWidgets && this.inputWidgets.length > 0) {
        this.selectedMOBOWidget =
          this.workflowCanvasService.findConnectedMLWidget(
            this.inputWidgets[0].inputs[0]?.urn ?? '',
          );

        this.inputWidgets = this.inputWidgets.filter(
          (widget) => widget.outputs.length > 0,
        );

        if (this.widgetControl.Widget.inputs.length > 0) {
          this.selectedInputWidget = this.inputWidgets.find(
            (t) => t.urn === this.widgetControl?.Widget.inputs[0].urn,
          );
        } else {
          if (this.inputWidgets.length === 1) {
            this.setDefaultInput = true;
            this.setSelectedInputWidget(this.inputWidgets[0]);
          }
        }
      }
      if (this.widgetControl.Widget.outputs.length) {
        this.outputName = this.widgetControl.Widget.outputs[0].name;
      }
    }
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  getUploadedFiles() {
    if (this.config) {
      this.rescaleService
        .getUploadedFiles(
          this.siteId,
          this.projectId,
          this.config.rescale_connector_id,
        )
        .subscribe({
          next: (response) => {
            this.rescaleSriptFiles = response.platform_files.concat(
              response.rescale_files.rescale_files,
            );
          },
          error: (error) => {
            const errorMessage =
              error?.error?.message ||
              error?.message ||
              'An unexpected error occurred';
            this.toaster.error(errorMessage, 'ERROR', {
              positionClass: 'custom-toast-position',
            });
          },
        });
    }
  }
  selectExistingFile(input_file: any) {
    if (this.config) {
      let files = this.rescaleSriptFiles.filter(
        (file: any) => file.file_name === input_file.file_name,
      );
      if (files.length > 0) {
        input_file.file_path = files[0]['file_path'];
        input_file.rescale_id = files[0]['rescale_id']
          ? files[0]['rescale_id']
          : '';
      }
    }
  }

  checkFileNameExists(fileName: string) {
    if (this.rescaleSriptFiles.length > 0) {
      let files = this.rescaleSriptFiles.filter(
        (file: any) => file.file_name === fileName,
      );
      if (files.length > 0) {
        return true;
      } else {
        return false;
      }
    } else {
      return false;
    }
  }
  onDeleteFile(fileID: string) {}

  onUploadJSONFile(event: any) {
    const file: File | undefined = event?.target?.files?.[0]; // Use optional chaining and a fallback

    if (file) {
      this.rescaleService
        .readJsonFile(file)
        .then((jsonData) => {
          if (jsonData && this.configCache && this.widgetControl) {
            this.configCache.input_file_name =
              file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
            this.widgetControl.Widget.config = this.configCache;
            this.config = this.widgetControl?.Widget.config;
            this.configCache = JSON.parse(JSON.stringify(this.config));
            this.setRescaleSoftware(JSON.stringify(jsonData));
            this.inputFilesList();
          }
        })
        .catch((error) => {
          const errorMessage =
            error?.error?.message ||
            error?.message ||
            'An unexpected error occurred';
          this.toaster.error(errorMessage, 'ERROR', {
            positionClass: 'custom-toast-position',
          });
        });
    } else {
      this.toaster.error('No file selected', 'ERROR', {
        positionClass: 'custom-toast-position',
      });
    }
  }

  viewFileContent(content: string, file_name: string) {
    const dialogRef = this.dialog.open(FileEditorDialogComponent, {
      width: '900px',
      data: {
        mode: 'python',
        content: content,
        file_name: file_name,
      },
      disableClose: true,
    });
    dialogRef.afterClosed().subscribe((result: any) => {});
  }
  getFileContent(file: any) {
    if (this.config) {
      if (this.rescaleSriptFiles.length > 0) {
        let files = this.rescaleSriptFiles.filter(
          (file: any) => file.file_name === file.file_name,
        );
        if (files.length > 0) {
          this.rescaleService
            .getFileContent(this.siteId, this.projectId, files[0])
            .subscribe({
              next: (response) => {
                this.viewFileContent(response.content, file.file_name);
              },
              error: (error) => {
                const errorMessage =
                  error?.error?.message ||
                  error?.message ||
                  'An unexpected error occurred';
                this.toaster.error(errorMessage, 'ERROR', {
                  positionClass: 'custom-toast-position',
                });
              },
            });
        }
      }
    }
  }
  rescaleSoftware(): string | undefined {
    if (!this.configCache) {
      return undefined;
    }
    return JSON.stringify(this.configCache.rescale_configs, null, 2);
  }

  setRescaleSoftware(value: string) {
    if (!this.configCache) {
      return;
    }
    if (this.configCache) {
      try {
        if (Object.keys(value).length === 0) {
          this.configCache.rescale_configs.files_detail = [];
        }

        var exactedJSON = JSON.parse(value);
        var fileType =
          exactedJSON.software.analysis.code === 'abaqus-dsls'
            ? 'abaqus-json-file.json'
            : 'ls-dyna-json-file.json';
        this.http
          .get<any>(`assets/json-files/${fileType}`)
          .subscribe((data) => {
            const abaqus_file = data;
            if (exactedJSON) {
              const abaqusKeys = Object.keys(abaqus_file);
              const rescaleKeys = Object.keys(exactedJSON);
              const missingKeys = abaqusKeys.filter(
                (key) => !rescaleKeys.includes(key),
              );
              if (missingKeys.length > 0) {
                this.toaster.warning(
                  `The following keys are missing: ${missingKeys.join(', ')}`,
                  'WARNING',
                  {
                    positionClass: 'custom-toast-position',
                  },
                );
                this.changeMade = false;
                return;
              } else {
                this.configCache!.rescale_configs = JSON.parse(value);
                this.filterInputFiles();
              }
            } else {
              console.error('Rescale configs are not defined.');
            }
          });
      } catch (error) {
        this.changeMade = false;
        // this.toaster.error("JSON file content is invalid", '', {
        //   positionClass: 'custom-toast-position',
        // });
      }
    }
  }
  checkSoftware() {
    if (this.configCache && this.configCache.rescale_configs) {
      let obj = this.configCache.rescale_configs;
      return Object.keys(obj).length > 0 || obj == '' ? true : false;
    } else {
      return false;
    }
  }

  getInputFiles() {
    if (this.configCache) {
      let rescaleConnectorConfig = this.configCache?.rescale_configs;
      return rescaleConnectorConfig?.files_detail;
    }
  }
  getDynamicJobText() {
    if (this.config) {
      let rescaleConnectorConfig = this.config?.rescale_configs;
      return rescaleConnectorConfig?.software?.dynamic_job_file;
    }
  }
  getReuseableJobText() {
    if (this.config) {
      let rescaleConnectorConfig = this.config?.rescale_configs;
      return rescaleConnectorConfig?.software?.reusable_job_file;
    }
  }
  inputFilesList(): any | undefined {
    if (this.configCache) {
      let rescaleConnectorConfig = this.configCache?.rescale_configs;
      let filesString = rescaleConnectorConfig?.software?.reusable_job_file;
      if (filesString) {
        let reuseableFiles = filesString.split(',');
        let filesList = [];
        for (var i = 0; i < reuseableFiles.length; i++) {
          filesList.push({
            file_name: reuseableFiles[i],
            file_path: '',
            upload_rescale: false,
            rescale_id: '',
          });
        }
        if (this.configCache && this.configCache.rescale_configs) {
          this.configCache.rescale_configs.files_detail = filesList;
        }
        this.changeState();
      }
    }
  }
  checkUploadInProgress(scriptLfile: any) {
    const fileExis = this.selectedFiles.filter(
      (file: any) => file.name === scriptLfile.file_name,
    );
    if (this.uploadScriptFlag && fileExis.length > 0) {
      return true;
    } else {
      return false;
    }
  }
  onFilesSelected(event: any, fileName: string, index: number) {
    if (this.getConnectorId() != '' && this.getConnectorId() != undefined) {
      const selectedFiles = event.target.files;
      if (selectedFiles.length == 1) {
        this.selectedFiles = Array.from(event.target.files);
        if (
          this.selectedFiles[0]['name'] ===
          this.getInputFiles()[index].file_name
        ) {
          this.uploadScriptFlag = true;
          let data = {
            siteId: this.siteId,
            projectId: this.projectId,
            folder_name: 'connection',
            connectorId: this.getConnectorId(),
            files: this.selectedFiles,
            workflowId: this.workflowId,
            post_python:
              this.configCache?.rescale_configs?.software.post_python ||
              this.configCache!.rescale_configs.software.post_python != ''
                ? this.configCache?.rescale_configs?.software.post_python
                : null,
          };
          this.rescaleService.uploadRescaleFilesToPlatform(data).subscribe({
            next: (response) => {
              this.uploadScriptFlag = false;
              if (this.configCache) {
                let rescaleConnectorConfig = this.configCache?.rescale_configs;
                let configFiles = rescaleConnectorConfig.files_detail;
                if (configFiles) {
                  let index = configFiles.findIndex(
                    (val: any) => val.file_name === fileName,
                  );
                  configFiles[index].file_path = response.files[0].file_path;
                  configFiles[index].upload_rescale = true;
                  rescaleConnectorConfig.files_detail = configFiles;
                  this.changeState();
                }
              }
            },
            error: (error) => {
              this.uploadScriptFlag = false;
              console.error('Upload error', error);
            },
          });
        } else {
          this.getInputFiles()[index].success = '';
          this.getInputFiles()[index].error = 'Please upload the correct file';
        }
      } else {
        this.selectedFiles = [];
        for (let i = 0; i < selectedFiles.length; i++) {
          const file = selectedFiles[i];
          if (file) {
            // Ensure the filename matches with 'file_name' from getConnectorId()
            var fileMatch = this.getInputFiles().filter(
              (val: any) => val.file_name === selectedFiles[i].name,
            );
            if (fileMatch.length > 0) {
              this.selectedFiles.push(selectedFiles[i]);
            }
          }
          if (i == selectedFiles.length - 1) {
            if (this.selectedFiles.length > 0) {
              let data = {
                siteId: this.siteId,
                projectId: this.projectId,
                folder_name: 'connection',
                connectorId: this.getConnectorId(),
                files: this.selectedFiles,
                workflowId: this.workflowId,
                post_python:
                  this.configCache?.rescale_configs?.software.post_python ||
                  this.configCache!.rescale_configs.software.post_python != ''
                    ? this.configCache?.rescale_configs?.software.post_python
                    : null,
              };
              this.uploadScriptFlag = true;
              this.rescaleService.uploadRescaleFilesToPlatform(data).subscribe({
                next: (response) => {
                  this.uploadScriptFlag = false;
                  if (this.configCache) {
                    let rescaleConnectorConfig =
                      this.configCache?.rescale_configs;
                    let configFiles = rescaleConnectorConfig.files_detail;
                    if (configFiles) {
                      for (var j = 0; j < response.files.length; j++) {
                        let index = configFiles.findIndex(
                          (val: any) =>
                            val.file_name === response.files[j].file_name,
                        );
                        configFiles[index].file_path =
                          response.files[j].file_path;
                        configFiles[index].upload_rescale = true;
                      }
                      rescaleConnectorConfig.files_detail = configFiles;
                      this.changeState();
                    }
                  }
                },
                error: (error) => {
                  this.uploadScriptFlag = false;
                  console.error('Upload error', error);
                },
              });
            } else {
              this.toaster.error(
                'No file(s) matched with required files',
                'ERROR',
                {
                  positionClass: 'custom-toast-position',
                },
              );
            }
          }
        }
      }
    }
  }

  onChanageConnector() {
    this.isAuthenticationFailed = false;
    this.isAuthenticationSuccessful = false;
  }

  isRescaleConnectorSelected() {
    return this.configCache?.rescale_connector_id ? false : true;
  }

  authentication() {
    this.onChanageConnector();
    if (this.configCache?.rescale_connector_id) {
      let connection = this.connectors.filter(
        (val) => val._id == this.configCache?.rescale_connector_id,
      );
      if (connection.length > 0) {
        let configuration = connection[0]
          .configuration as RescaleConnectorConfiguration;
        this.spinner = true;
        this.rescaleService
          .authenticate(this.siteId, this.projectId, {
            token: configuration.token,
          })
          .subscribe({
            next: (response: any) => {
              this.spinner = false;
              this.isAuthenticationFailed = false;
              this.isAuthenticationSuccessful = true;
            },
            error: (error: any) => {
              this.spinner = false;
              this.isAuthenticationSuccessful = false;
              this.isAuthenticationFailed = true;
            },
          });
      }
    }
  }

  async loadConnectors() {
    let allConnectors = await this.apiService.GetConnectors(
      this.siteId,
      this.projectId,
    );
    if (allConnectors) {
      var connectors = allConnectors.filter(
        (t) => t.type === ConnectorType.RESCALE,
      );
      this.connectors = connectors;
    }
  }

  setConnectorId(connectorId: string | undefined) {
    if (!this.configCache) {
      return;
    }
    if (this.configCache) {
      this.configCache.rescale_connector_id = connectorId;
      this.onChanageConnector();
      this.changeState();
    }
  }

  getConnectorId() {
    if (!this.configCache) {
      return undefined;
    }
    return this.configCache.rescale_connector_id;
  }

  connectionIdActive() {
    if (this.getConnectorId() != '' && this.getConnectorId() != undefined) {
      return true;
    } else {
      return false;
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
    this.changeMade = true;
    if (this.setDefaultInput) {
      this.changeMade = false;
      this.onSave();
    }
  }
  // onInputSave() {
  //   this.workflowCanvasService.changeMadeToWorkflow = true;
  //   this.changeInputMade = false;
  //   this.setDefaultInput = false;
  // }

  // onInputCancel() {
  //   this.changeInputMade = false;
  //   this.setDefaultInput = false;
  //   this.inputName = undefined;

  //   if (this.widgetControl) {
  //     this.outputName = this.widgetControl.Widget.outputs[0].name;
  //     if (this.widgetControl.Widget.inputs.length) {
  //       this.inputName = this.widgetControl.Widget.inputs[0].name;
  //     }
  //   }
  // }

  getWidgetOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let outputConfig: InputOutputConfig = widget.outputs[0];
      return outputConfig.name!;
    }

    return 'Not Set';
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
    this.settingsComponent.SaveAppSettings();

    if (!this.widgetControl) {
      return;
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

    if (this.configCache) {
      if (
        this.configCache.rescale_configs?.software?.command.startsWith(
          'ls-dyna',
        ) &&
        this.selectedMOBOWidget?.length > 0
      ) {
        const moboConfig = this.selectedMOBOWidget[0]
          .config as MOBOWidgetConfig;
        if (moboConfig?.constraints_module_id === null) {
          this.toaster.error('Please select MOBO constraints module', 'ERROR', {
            positionClass: 'custom-toast-position',
          });
          return;
        }
      }
      this.widgetControl.Widget.config = this.configCache;
      this.config = this.widgetControl?.Widget.config;
      this.configCache = JSON.parse(JSON.stringify(this.config));
    }

    this.changeMade = false;
    this.setDefaultInput = false;
  }

  onCancel() {
    this.inputName = undefined;
    this.outputName = undefined;

    this.settingsComponent.RevertAppSetting();
    this.configCache = JSON.parse(JSON.stringify(this.config));

    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
      if (this.widgetControl.Widget.inputs.length) {
        this.inputName = this.widgetControl.Widget.inputs[0].name;
      }
    }

    this.changeMade = false;
  }
  changeState() {
    this.changeMade = true;
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

  filterInputFiles(): any | undefined {
    if (this.configCache) {
      let rescaleConnectorConfig = this.configCache?.rescale_configs;
      let filesString = rescaleConnectorConfig?.software?.reusable_job_file;
      if (filesString) {
        let reuseableFiles = filesString.split(',');
        let filesList = [];

        for (let i = 0; i < reuseableFiles.length; i++) {
          const fileName = reuseableFiles[i];
          const existingFile =
            this.configCache?.rescale_configs?.files_detail?.find(
              (file: { file_name: any }) => file.file_name === fileName,
            );

          if (existingFile) {
            filesList.push(existingFile);
          } else {
            filesList.push({
              file_name: fileName,
              file_path: '',
              upload_rescale: false,
              rescale_id: '',
            });
          }
        }

        if (this.configCache && this.configCache.rescale_configs) {
          this.configCache.rescale_configs.files_detail = filesList;
        }
        this.changeState();
      } else {
        this.configCache.rescale_configs.files_detail = [];
      }
    }
  }
}
