import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  Input,
  OnInit,
  ViewChild,
} from '@angular/core';
import { WidgetControl } from '../../widget-control/widget-control';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ApiService } from 'src/app/services/api.service';
import { MatDialog } from '@angular/material/dialog';
import { ConfigService } from 'src/app/services/config.service';
import { ToastrService } from 'ngx-toastr';

import {
  SaveWidgetConfig,
  Widget,
  InputOutputConfig,
  DestinationTypes,
  FileFormatOptions,
  FileSaveOptions,
  ReplaceConfig,
  SaveAsConfig,
  DatasetConfiguration,
  SaveOptionConfig,
  WidgetType,
  RequestType,
} from 'src/app/models/workflow-models';
import { SettingsComponent } from '../settings/settings.component';
import { Connector, ConnectorType } from 'src/app/models/connector-models';
import { SaveConfigService } from './services/save-config.service';
import { AssetsListResponse, DatasetType } from 'src/app/models/data-models';
import { MountedDriveDataPreviewComponent } from 'src/app/dialogs/mounted-drive-data-preview/mounted-drive-data-preview.component';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { PromptSaveComponent } from 'src/app/dialogs/prompt-save/prompt-save.component';
@Component({
  selector: 'app-save-config',
  templateUrl: './save-config.component.html',
  styleUrls: ['./save-config.component.less'],
})
export class SaveConfigComponent implements OnInit, AfterViewInit {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  private settingsComponentReady!: Promise<void>;
  private settingsComponentResolve!: () => void;

  connectors: Connector[] = [];
  widgetControl: WidgetControl | undefined = undefined;
  connectorId: any;
  parentItems: any = [];
  TableNames: any = [];
  datasets: any;
  mountedDatasets: any;
  dataset_name: any;
  selectedChildIndex: number = -1;
  inputWidgets: Widget[] = [];
  path: any;
  selectedDatasetName: any;
  selectedTableName: any;
  input_column_name: string = '';
  saveFlag: boolean = false;
  overwriteChecked: boolean = false;

  localDrivePath: string = '';
  mountedDriveFullPath: any;

  changeMade: boolean = false;
  outputTabFlag: boolean = false;
  parametersTabClicked = true;
  overrideButton = false;
  inputDataButton = false;
  config: SaveWidgetConfig | undefined = undefined;
  configCache: SaveWidgetConfig | undefined = undefined;

  allOutputs: InputOutputConfig[] = [];
  selectedInputOutputConfigs: InputOutputConfig[] = [];

  destinationTypes: string[] = ['Mounted Drive', 'Hexaind Platform'];

  data = {
    type: 'Save Widget',
    description:
      'The Save Widget simplifies data preservation by providing an intuitive interface for users to securely save and manage their content, enhancing the overall user experience.',
    version: '1.0',
  };

  setDefaultInput: boolean = false;

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private apiService: ApiService,
    private saveConfigService: SaveConfigService,
    public dialog: MatDialog,
    private configService: ConfigService,
    public sharedDataService: SharedDataService,
    private toaster: ToastrService,
    private changeDetectorRef: ChangeDetectorRef,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.config = this.widgetControl.Widget.config as SaveWidgetConfig;
    this.config.widget_type = WidgetType.SAVE;
    this.configCache = JSON.parse(JSON.stringify(this.config));
    //this.setOverwriteOption(0, false);
  }

  ngOnInit() {
    this.settingsComponentReady = new Promise<void>((resolve) => {
      this.settingsComponentResolve = resolve;
    });

    this.loadDatasets();
    this.loadMountedDatasets();
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.workflowCanvasService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );
      const urnsInWidgets =
        this.workflowCanvasService.SelectedWorkflow?.widgets.map(
          (widget) => widget.urn,
        ) || [];
      this.inputWidgets = this.inputWidgets.filter((widget) =>
        urnsInWidgets.includes(widget.outputs[0]['urn']),
      );
    }
    this.loadConnectors();
    this.loadSelectedInputOutputConfigs();
  }

  ngAfterViewInit() {
    if (this.settingsComponent) {
      this.settingsComponentResolve();
    } else {
      console.error('SettingsComponent initialization failed.');
    }
  }

  onWidgetClick() {
    if (this.checkInputsWidgets()) {
      if (this.inputWidgets.length > 1) {
        const dialogRef = this.dialog.open(PromptSaveComponent, {
          width: '300px',
        });

        dialogRef.afterClosed().subscribe((result) => {
          if (result) {
            this.populateLatestConnectedWidget();
            this.onSave();
          }
        });
      } else if (this.inputWidgets.length === 1) {
        this.populateLatestConnectedWidget();
        this.onSave();
      }
    }
    this.workflowCanvasService.IsMovingWidget = true;
  }

  checkInputsWidgets(): boolean {
    return this.configCache?.datasetConfig?.length !== this.inputWidgets.length;
  }

  populateLatestConnectedWidget() {
    if (this.inputWidgets.length > 0) {
      let nextIndex = this.selectedInputOutputConfigs.length;
      this.inputWidgets.forEach((widget, index) => {
        const alreadyConnected = this.selectedInputOutputConfigs.some(
          (config) => config.urn === widget.urn,
        );
        if (!alreadyConnected && widget.outputs.length > 0) {
          this.setSelectedInputOutputConfig(widget.outputs[0], nextIndex);
          nextIndex++;
        }
      });
    }
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  onTabChange(event: any): void {
    if (event === 2 && this.parametersTabClicked && this.outputTabFlag) {
      this.changeMade = true;
    }
  }

  getSelectedInputOutputConfig(index: number) {
    if (index !== -1 && index < this.selectedInputOutputConfigs.length) {
      return this.selectedInputOutputConfigs[index];
    }
    return undefined;
  }

  getWidgetOutputName(inputOutputConfig: InputOutputConfig): string {
    return inputOutputConfig.name ?? '';
  }

  setSelectedInputOutputConfig(
    inputOutputConfig: InputOutputConfig,
    index: number,
  ) {
    for (let i = 0; i < this.allOutputs.length; i++) {
      if (i === index) {
        if (i < this.selectedInputOutputConfigs.length) {
          this.selectedInputOutputConfigs[i] = inputOutputConfig;
        } else {
          this.selectedInputOutputConfigs.push(inputOutputConfig);
        }
        this.changeMade = true;
        this.outputTabFlag = true;
        break;
      }
    }

    if (this.selectedInputOutputConfigs.length === 1) {
      this.changeMade = true;
      this.triggerSave();
      this.changeMade = false;
    }

    if (this.setDefaultInput) {
      this.onSave();
    }
  }

  loadSelectedInputOutputConfigs() {
    this.inputWidgets = this.inputWidgets.map((widget: any) => {
      if (widget.type === 'CUSTOM_CODE') {
        widget.outputs = widget.outputs.map((output: any) => {
          if (output.name.includes('Tabular')) {
            return {
              ...output,
              name: output.name.replace(/Tabular\d*/, output.type),
            };
          }
          return output;
        });
      }
      return widget;
    });
    this.allOutputs = this.inputWidgets.flatMap((widget) => widget.outputs);
    if (this.allOutputs.length == 0) {
      if (this.widgetControl) {
        this.widgetControl.Widget.inputs = [];
      }
    }

    if (!this.widgetControl || !this.widgetControl.Widget) {
      return;
    }
    this.selectedInputOutputConfigs = [];
    for (let i = 0; i < this.widgetControl.Widget.inputs.length; i++) {
      if (this.widgetControl.Widget.inputs[i]) {
        let config: InputOutputConfig | undefined = this.allOutputs.find(
          (t) =>
            t.name === this.widgetControl!.Widget.inputs[i].name &&
            t.urn === this.widgetControl!.Widget.inputs[i].urn,
        );
        if (config) {
          this.selectedInputOutputConfigs[i] = config;
        }
      }
    }
    this.selectedInputOutputConfigs = this.selectedInputOutputConfigs.filter(
      (config, index) => this.widgetControl!.Widget.inputs[index] !== null,
    );
    if (this.allOutputs.length == 1) {
      this.setDefaultInput = false;
      this.setSelectedInputOutputConfig(this.allOutputs[0], 0);
    }

    this.getTheExportData();
  }

  getTheExportData() {
    if (this.selectedInputOutputConfigs) {
      const numInputs = this.selectedInputOutputConfigs.length;
      this.configCache!.datasetConfig.length = numInputs;

      this.selectedInputOutputConfigs.forEach((config, index) => {
        const inputName = config.name;
        const datasetIndex = index;

        if (!this.configCache?.datasetConfig[datasetIndex]) {
          const datasetConfig: DatasetConfiguration = {
            dataset_name: inputName || '',
            destination_type: DestinationTypes.HEXAIND_PLATFORM,
            destination_config: new SaveOptionConfig(),
            doNotSaveFlag: undefined,
          };
          if (this.configCache && this.configCache.datasetConfig) {
            this.configCache.datasetConfig[datasetIndex] = datasetConfig;
          }
          if (config.type == RequestType.DICTIONARY) {
            this.setFileFormatoptions(index, FileFormatOptions.EXCEL);
          }
        } else {
          if (inputName != undefined) {
            this.configCache!.datasetConfig[datasetIndex].dataset_name =
              inputName;
          }
        }
      });
    }
  }

  async loadDatasets() {
    let response: AssetsListResponse =
      await this.saveConfigService.GetDatasets(undefined);
    this.datasets = response['datasets'];
  }

  async loadMountedDatasets() {
    const filetype = '';
    this.apiService
      .getMountedDriveDirectoryList(filetype)
      .then((response) => {
        if (response) {
          this.mountedDatasets = response.children;
          this.mountedDriveFullPath = response.full_path;
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
  }

  getSaveWidgetConfig(): SaveWidgetConfig | null {
    let saveWidgetConfig: SaveWidgetConfig = this.widgetControl?.Widget
      .config as SaveWidgetConfig;
    return saveWidgetConfig;
  }

  // MOUNTED-HEXAIND or PLATFORM-DATASTORE
  getDestinationOption(index: number): DestinationTypes | undefined {
    if (
      !this.configCache ||
      !this.configCache.datasetConfig ||
      index >= this.configCache.datasetConfig.length
    ) {
      return undefined;
    }
    return this.configCache.datasetConfig[index].destination_type;
  }

  getDestinationSelectionType(index: number) {
    if (
      !this.configCache ||
      !this.configCache.datasetConfig ||
      index >= this.configCache.datasetConfig.length
    ) {
      return undefined;
    }
    if (
      this.configCache.datasetConfig[index].destination_type ===
      DestinationTypes.MOUNTED_DRIVE
    ) {
      return this.destinationTypes[0];
    }
    return this.destinationTypes[1];
  }

  onLocationTypeSelection(index: number, selectedValue: string) {
    this.changeMade = true;
    this.outputTabFlag = true;
    if (selectedValue === 'Mounted Drive') {
      this.setDestinationOption(index, 'MOUNTED_DRIVE' as DestinationTypes);
    } else {
      this.setDestinationOption(index, 'HEXAIND_PLATFORM' as DestinationTypes);
    }
  }

  isMountedDriveSelected(index: number): boolean {
    let isMountedDrive: boolean =
      this.getDestinationOption(index) === 'MOUNTED_DRIVE';
    return isMountedDrive;
  }

  setDestinationOption(index: number, value: DestinationTypes) {
    if (
      !this.configCache ||
      !this.configCache.datasetConfig ||
      index >= this.configCache.datasetConfig.length
    ) {
      console.error('Config is not initialized or index is out of bounds.');
      return;
    }

    switch (value) {
      case DestinationTypes.MOUNTED_DRIVE:
        this.configCache.datasetConfig[index].destination_type =
          DestinationTypes.MOUNTED_DRIVE;
        break;
      case DestinationTypes.HEXAIND_PLATFORM:
        this.configCache.datasetConfig[index].destination_type =
          DestinationTypes.HEXAIND_PLATFORM;
        break;
      default:
        console.error('Invalid destination type:', value);
        return;
    }
    this.configCache.datasetConfig[index].destination_type = value;
  }

  setSaveFlag(index: number, flag: boolean) {
    if (
      !this.configCache ||
      !this.configCache.datasetConfig ||
      index >= this.configCache.datasetConfig.length
    ) {
      console.error('Config is not initialized or index is out of bounds.');
      return;
    }
    this.configCache.datasetConfig[index].doNotSaveFlag = flag;
    this.changeMade = true;
    this.outputTabFlag = true;
  }

  isOverwriteChecked(index: number): boolean {
    this.overwriteChecked = this.getSaveOptions(index) === 'REPLACE';
    return this.overwriteChecked;
  }

  setOverwriteOption(index: number, isChecked: boolean) {
    if (isChecked) {
      this.setSaveOptions(index, 'REPLACE' as FileSaveOptions);
    } else {
      this.setSaveOptions(index, 'SAVE_AS' as FileSaveOptions);
    }
    this.overwriteChecked = isChecked;
  }

  getFileFormatoptions(index: number): FileFormatOptions | string | undefined {
    if (
      !this.configCache ||
      !this.configCache.datasetConfig ||
      index >= this.configCache.datasetConfig.length
    ) {
      return 'CSV';
    }
    const format =
      this.configCache.datasetConfig[index].destination_config?.file_Format;
    if (!format) {
      this.overrideButton = false;
      this.setFileFormatoptions(index, 'CSV' as FileFormatOptions);
      return 'CSV';
    }

    return format;
  }

  setFileFormatoptions(index: number, value: FileFormatOptions) {
    this.setOverwriteOption(index, false);
    if (!this.configCache?.datasetConfig?.[index]?.destination_config) {
      console.error('Config is not initialized or index is out of bounds.');
      return;
    }
    this.configCache.datasetConfig[index].destination_config!.file_Format =
      value;
    if (this.parametersTabClicked) {
      this.changeMade = true;
      this.outputTabFlag = true;
    }
    this.parametersTabClicked = true;
    this.changeMade = true;
  }

  getSaveOptions(index: number): FileSaveOptions | undefined {
    return this.configCache?.datasetConfig?.[index]?.destination_config
      ?.save_options;
  }

  setSaveOptions(index: number, value: FileSaveOptions) {
    if (!this.configCache?.datasetConfig?.[index]?.destination_config) {
      console.error('Config is not initialized or index is out of bounds.');
      return;
    }
    this.configCache.datasetConfig[index].destination_config!.save_options =
      value;
    if (
      this.configCache.datasetConfig[index].destination_config!.save_options ===
      'REPLACE'
    ) {
      this.configCache.datasetConfig[
        index
      ].destination_config!.save_option_config = new ReplaceConfig();
    } else {
      this.configCache.datasetConfig[
        index
      ].destination_config!.save_option_config = new SaveAsConfig();
      let save_option_config: SaveAsConfig | undefined = this.configCache
        .datasetConfig[index].destination_config!
        .save_option_config as SaveAsConfig;
      save_option_config.file_name = this.generateFilename();
    }
    if (this.overrideButton) {
      this.changeMade = true;
      this.outputTabFlag = true;
    }
    this.overrideButton = true;
  }

  generateFilename(): string | undefined {
    let selectedProjectName: string | undefined =
      this.configService.SelectedProjectName;
    if (!selectedProjectName) {
      return;
    }
    const baseName = `${selectedProjectName}_${this.widgetControl?.Widget
      .name}_${this.generateRandomString(3)}`;
    return baseName;
  }

  generateRandomString(length: number): string {
    const characters = '0123456789';
    let randomString = '';

    for (let i = 0; i < length; i++) {
      const randomIndex = Math.floor(Math.random() * characters.length);
      randomString += characters.charAt(randomIndex);
    }

    return randomString;
  }

  getDatasetId(index: number): string | undefined {
    const destinationConfig =
      this.configCache?.datasetConfig?.[index]?.destination_config;
    const replaceConfig = destinationConfig?.save_option_config as
      | ReplaceConfig
      | undefined;
    return replaceConfig?.existing_dataset_id;
  }

  setDatasetId(index: number, value: string) {
    if (
      this.configCache &&
      this.configCache.datasetConfig &&
      this.configCache.datasetConfig[index].destination_config
    ) {
      let save_option_config: ReplaceConfig | undefined = this.configCache
        .datasetConfig[index].destination_config
        ?.save_option_config as ReplaceConfig;

      save_option_config.existing_dataset_id = value;
      save_option_config.destination_path = '';
      this.changeMade = true;
      this.outputTabFlag = true;
    }
  }

  getDatasetFullPath(index: number): string | undefined {
    const destinationConfig =
      this.configCache?.datasetConfig?.[index]?.destination_config;
    const replaceConfig = destinationConfig?.save_option_config as
      | ReplaceConfig
      | undefined;
    return replaceConfig?.destination_path;
  }

  setDatasetFullPath(index: number, value: string) {
    if (
      this.configCache &&
      this.configCache.datasetConfig &&
      this.configCache.datasetConfig[index].destination_config
    ) {
      let save_option_config: ReplaceConfig | undefined = this.configCache
        .datasetConfig[index].destination_config
        ?.save_option_config as ReplaceConfig;

      save_option_config.destination_path = value;
      save_option_config.existing_dataset_id = '';
      this.changeMade = true;
      this.outputTabFlag = true;
    }
  }

  getFileName(index: number): string | undefined {
    const saveoptionconfig =
      this.configCache?.datasetConfig?.[index]?.destination_config;
    const replaceConfig = saveoptionconfig?.save_option_config as
      | SaveAsConfig
      | undefined;
    return replaceConfig?.file_name;
  }

  setFileName(index: number, value: string) {
    if (
      this.configCache &&
      this.configCache.datasetConfig &&
      this.configCache.datasetConfig[index].destination_config
    ) {
      let save_option_config: SaveAsConfig | undefined = this.configCache
        ?.datasetConfig[index].destination_config
        ?.save_option_config as SaveAsConfig;

      save_option_config.file_name = value;
      this.changeMade = true;
      this.outputTabFlag = true;
    }
  }

  showMountedDriveDialog(index: number): void {
    const dialogConfig = {
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: {
        type: 'save',
      },
    };

    const dialogRef = this.dialog.open(
      MountedDriveDataPreviewComponent,
      dialogConfig,
    );

    dialogRef.afterClosed().subscribe(
      (result: any) => {
        if (result && result.success) {
          if (this.configCache) {
            const datasetConfig = this.configCache.datasetConfig[index];
            if (
              datasetConfig !== undefined &&
              datasetConfig.destination_config !== undefined &&
              datasetConfig.destination_config.destination_folder_path !==
                undefined
            ) {
              datasetConfig.destination_config.destination_folder_path =
                result.path;
              this.changeMade = true;
              this.outputTabFlag = true;
            }
          }
        } else {
        }
      },
      (error: any) => {
        console.error('Error closing dialog:', error);
      },
    );
  }

  getMountedPath(index: number): string | undefined {
    if (
      this.configCache &&
      this.configCache.datasetConfig &&
      this.configCache.datasetConfig[index]?.destination_config
    ) {
      const mountedDriveDestConfig = this.configCache.datasetConfig[index]
        .destination_config as SaveOptionConfig;
      if (mountedDriveDestConfig.destination_folder_path) {
        return mountedDriveDestConfig.destination_folder_path;
      }
    }
    return undefined;
  }

  async loadConnectors() {
    let allConnectors = await this.apiService.GetConnectors(
      '1',
      this.configService.SelectedProjectId!,
    );
    if (allConnectors) {
      this.connectors = allConnectors.filter(
        (t) => t.type === ConnectorType.BIGQUERY,
      );
    }
  }

  onAppSettingsUpdated() {
    this.changeMade = true;
    this.outputTabFlag = true;
  }

  triggerSave() {
    this.settingsComponentReady
      .then(() => {
        this.onSave();
      })
      .catch(() => {
        console.error('Failed to initialize settingsComponent before saving.');
      });
  }

  onSave() {
    this.workflowCanvasService.changeMadeToWorkflow = true;

    if (this.settingsComponent) {
      this.settingsComponent.SaveAppSettings();
    }

    if (!this.widgetControl) {
      return;
    }

    if (this.configCache) {
      this.widgetControl.Widget.inputs = [];
      for (let i = 0; i < this.selectedInputOutputConfigs.length; i++) {
        let selectedInputOutputConfig: InputOutputConfig =
          this.selectedInputOutputConfigs[i];

        let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
        inputOutputConfig.name = selectedInputOutputConfig.name;
        inputOutputConfig.urn = selectedInputOutputConfig.urn;

        this.widgetControl.Widget.inputs.push(inputOutputConfig);
      }

      this.widgetControl.Widget.config = this.configCache;
      this.config = this.widgetControl.Widget.config;
      this.configCache = JSON.parse(JSON.stringify(this.config));
    }

    this.selectedInputOutputConfigs = this.selectedInputOutputConfigs.filter(
      (item) => item.urn !== undefined && item.name !== undefined,
    );

    this.getTheExportData();
    this.changeMade = false;
    this.parametersTabClicked = false;
    this.setDefaultInput = false;
    this.changeDetectorRef.detectChanges();
  }

  onCancel() {
    this.settingsComponent.RevertAppSetting();
    // Deep clone to prevent updates from modifying original
    this.configCache = JSON.parse(JSON.stringify(this.config));
    this.changeMade = false;
    this.outputTabFlag = false;
    this.loadSelectedInputOutputConfigs();
  }

  trackByFn(index: any, item: { id: any }) {
    return item.id; // or any unique identifier of your items
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

  isSaveDisabled(): boolean {
    return this.configCache?.datasetConfig?.length === this.inputWidgets.length;
  }
}
