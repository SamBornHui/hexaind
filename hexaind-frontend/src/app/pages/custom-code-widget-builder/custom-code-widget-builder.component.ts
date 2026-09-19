import {
  Component,
  ViewChild,
  ChangeDetectorRef,
  TemplateRef,
} from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { ConfigService } from 'src/app/services/config.service';
import { ActivatedRoute, Router } from '@angular/router';
import { MatMenuTrigger } from '@angular/material/menu';
import { ToastrService } from 'ngx-toastr';
import { MatTabGroup } from '@angular/material/tabs';
import { ColorPickerService, Cmyk } from 'ngx-color-picker';
import { NotificationComponent } from 'src/app/controls/notification/notification.component';
import { v4 as uuidv4 } from 'uuid';
import { MountedDriveDataPreviewComponent } from 'src/app/dialogs/mounted-drive-data-preview/mounted-drive-data-preview.component';
import {
  MatDialog,
  MatDialogConfig,
  MatDialogRef,
} from '@angular/material/dialog';
import { catchError, finalize, tap } from 'rxjs/operators';
import { Subscription } from 'rxjs';
import { CustomCodeConfigComponent } from 'src/app/controls/configs/custom-code-config/custom-code-config.component';
import JSZip from 'jszip';
import { EnlargedTextEditorComponent } from 'src/app/util-components/enlarged-text-editor/enlarged-text-editor.component';
import { CpwCodeEditorComponent } from 'src/app/util-components/cpw-code-editor/cpw-code-editor.component';
@Component({
  selector: 'app-custom-code-widget-builder',
  templateUrl: './custom-code-widget-builder.component.html',
  styleUrls: ['./custom-code-widget-builder.component.less'],
})
export class CustomCodeWidgetBuilderComponent {
  onEventLog(event: { input: string; value: string | number; color: string }) {}
  @ViewChild('notification') notificationComponent!: NotificationComponent;
  @ViewChild(MatMenuTrigger)
  menuTrigger!: MatMenuTrigger;
  @ViewChild(MatTabGroup)
  tabGroup!: MatTabGroup;
  public color1: string = '#2889e9';
  private _colorCode: string = '#2889e9';
  showInfoTab: boolean = true;
  showExcute: boolean = false;
  showExecuteNxtab: boolean = false;
  showPreviewTab: boolean = false;
  showInformationTab: boolean = true;
  showInputsTab: boolean = false;
  showOutputsTab: boolean = false;
  showParametersTab: boolean = false;
  showSettingsTab: boolean = false;
  is_execute: boolean = false;
  is_preview: boolean = false;
  is_Publish: boolean = false;
  is_continue1: boolean = false;
  is_InformationTab: boolean = true;
  is_inputTab: boolean = false;
  is_outputTab: boolean = false;
  is_parametersTab: boolean = false;
  is_settingsTab: boolean = false;
  continue_button: boolean = false;
  fileinput: boolean = false;
  is_ContinueDone: boolean = false;
  is_MandatoryValue: boolean = true;
  showLoader: boolean = false;
  correlationId: any;
  responseValues: any;
  options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
  selectedNumberOfInputs: number = 0;
  inputs: number[] = [];
  inputNumber: any;
  selectedNumberOfOutputs: number = 0;
  outputs: number[] = [];
  selectedFiles: File[] = [];
  selectedFileName: string = '';
  finalresponse: any;
  firstresponse: any;
  finalresponse_help_details: any;
  isDisabled: boolean = true;
  inputValues: { [key: string]: any } = {};
  selectedOutputs: { [key: string]: string } = {};
  isInitialized: boolean = false;
  validationInputs: any[] = [];
  validationOutputs: any[] = [];
  formValues: any;
  defaultColor: any = 'var(--primary)';
  module_id: any;
  mountdrivePathName: any;
  customPythonWidgetRecipeId: any;
  showActivityLog = false;
  activityLogs: any[] = [];
  isValidationLogError: boolean | undefined;
  validationLogWebSocket: Subscription | undefined;
  defaultValuePath: any;
  defaultValueText: any;
  widgetColor: any;
  displayString: any = [];
  showSuccessfulValidationTab = false;
  isInputOutputMappingCompleted: boolean = false;
  formData: any = {};
  inputs_map: any[] = [];
  outputs_map: any[] = [];
  widget_inputs_rules: any;
  widget_outputs_rules: any;
  isMandatory: { [key: string]: boolean } = {};
  get_input: any[] = [
    { label: 'input1', placeholder: 'Input 1', type: 'text' },
    { label: 'input2', placeholder: 'Input 2', type: 'text' },
  ];
  noofinputs: number = this.get_input.length;
  get_output: any[] = [
    { label: 'output1', placeholder: 'Output 1', type: 'text' },
    { label: 'output2', placeholder: 'Output 2', type: 'text' },
  ];
  inputTextValues: { [key: string]: string } = {};
  noofoutputs: number = this.get_output.length;
  getFiles: any;
  executionStatus: boolean = false;
  executionMsg: string = '';
  allowUsersToModifyConfigurations: boolean = true;
  allowUsersToModifyConfigurationstype: boolean = false;
  public rgbaText: string = 'rgba(165, 26, 214, 0.2)';
  public selectedColor: string = 'color1';
  public color2: string = '#e920e9';
  public color3: string = '#fff500';
  public color4: string = 'rgb(236,64,64)';
  public color5: string = 'rgba(45,208,45,1)';
  public color6: string = '#1973c0';
  public color7: string = '#f200bd';
  public color8: string = '#a8ff00';
  public color9: string = '#278ce2';
  public color10: string = '#0a6211';
  public color11: string = '#f2ff00';
  public color12: string = '#f200bd';
  public color13: string = 'rgba(0,255,0,0.5)';
  public color14: string = 'rgb(0,255,255)';
  public color15: string = 'rgb(255,0,0)';
  public color16: string = '#a51ad633';
  public color17: string = '#666666';
  public color18: string = '#ff0000';
  public cmykValue: string = '';
  public cmykColor: Cmyk = new Cmyk(0, 0, 0, 0);
  showMainHeader: boolean = false;
  toggleHeaderButton: string = 'expand_more';
  showLeftPanel: boolean = false;
  toggleLeftButton: string = 'chevron_left';
  filesExtracted: boolean = false;
  filesExtractedResponse: string = '';
  isValidationInProgress: boolean = false;
  isValidationFailed: boolean = false;
  validationMessage: string = 'Validating the custom code...';
  widgetId: string | undefined; // currentWidget of the recipe
  widgetVersion: string | undefined;
  @ViewChild('popupTemplate') popupTemplate: TemplateRef<any> | undefined;
  @ViewChild('validationTemplate') validationTemplate:
    | TemplateRef<any>
    | undefined;
  dialogRef: MatDialogRef<any> | undefined;
  workFlowInWhichWidgetIsUsed: any;
  isPublishingInProgress: boolean = false;
  isCodeValidationEnabled: boolean = false;
  isContinueToConfiguration: boolean = false;
  isPythonCodeUpdatedWhileEditing: boolean = false;
  functionSignature: string = '';
  isWidgetInDraftState: boolean = false;
  isEditing: boolean = false;
  isViewing: boolean = false;
  isWidgetInPublishedState: boolean = false;
  isLocalDriveUpload: boolean = true;
  selectedUploadSource = '1';
  manuallyEnteredInputs = new Set<string>();
  uploadedType: string = 'PY';
  optiontypes = [
    'TABULAR',
    'STRING',
    'IMAGE',
    'DOCUMENT',
    'NUMERICAL',
    'JSON',
    'MODEL',
  ];
  public arrayColors: any = {
    color1: '#2883e9',
    color2: '#e920e9',
    color3: 'rgb(255,245,0)',
    color4: 'rgb(236,64,64)',
    color5: 'rgba(45,208,45,1)',
  };

  constructor(
    private apiService: ApiService,
    private cpService: ColorPickerService,
    private configService: ConfigService,
    private router: Router,
    public toaster: ToastrService,
    public dialog: MatDialog,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.selectedUploadSource = '1';
    if (history.state.data) {
      this.formData = history.state.data;
      this.inputNumber = 1;
    } else {
      this.formData = {};
      this.inputNumber = 0;
    }
    this.showMainHeader = !this.showMainHeader;
    this.route.paramMap.subscribe((params) => {
      this.customPythonWidgetRecipeId = params.get('customWidgetId');
      if (this.customPythonWidgetRecipeId == 0) {
        return;
      }
      this.isViewing = params.get('viewMode') == 'VIEW';
      this.isEditing = params.get('viewMode') == 'EDIT';
      this.fetchAndPopulateExistingWidget();
    });
  }

  /**
   * The purpose of this function is to fetch the existing custom widget and populate that widget data into the form for viewing. The formData is processed
   * to get the finalPayload for widgetCreation Api. So while viewing back the widgetStored in db we need to process it back to formData.
   */

  async fetchAndPopulateExistingWidget() {
    let customWidgetRecipe = await this.apiService.GetCustomPythonWidgetReceipe(
      this.customPythonWidgetRecipeId,
    );
    let moduleMetaData = await this.apiService.getCustomWidgetModuleMetaData(
      '1',
      customWidgetRecipe.project_id,
      customWidgetRecipe.module_id,
    );
    this.finalresponse = moduleMetaData.metadata;
    this.uploadedType = moduleMetaData?.module_location?.extension;
    this.finalresponse_help_details = customWidgetRecipe.help_details;
    this.copyCustomWidgetDataIntoFormDataForViewing(customWidgetRecipe);
    this.reMapInputMapInModuleAsFunctionInput(customWidgetRecipe);
    this.fillTheFormDataWithItemNameItemSource();
    this.fetchAndSetWidgetUsagesInWorkflow(customWidgetRecipe._id);
    this.setWidgetStatusFlag(customWidgetRecipe);

    const formattedFileNames = [];
    for (const fileName of this.finalresponse.file_names) {
      formattedFileNames.push({ name: fileName, path: fileName });
    }

    this.finalresponse.function_inputs.forEach(
      (item: { name: string | number }) => {
        this.isMandatory[item.name] = true;
      },
    );

    this.get_output = this.finalresponse.function_outputs.map(
      (output: string) => ({ label: 'DataFrame Type', type: output }),
    );

    this.finalresponse.file_names_path = formattedFileNames;
    this.noofoutputs = this.finalresponse.function_outputs.length;
    this.get_input = this.finalresponse.function_inputs;
    this.noofinputs = this.finalresponse.function_inputs.length;
    this.getFiles = this.finalresponse.file_names;
    this.continue_button = true;
    this.filesExtracted = true;
    this.fileinput = true;
    this.functionSignature = this.finalresponse.function_signature;
    this.selectedFileName = this.getFileName(
      moduleMetaData.module_location.path,
    );
    this.filesExtractedResponse =
      'Found 1 python file with desired method : Hexaind_Custom_Widget_Function';
    this.updateInputsMap();
    this.extractFunctionDatatypes();
    this.enableAllTabs();
    this.cdr.detectChanges();
  }

  async fetchAndSetWidgetUsagesInWorkflow(customWidgetId: any) {
    let apiResponse = await this.apiService.getworkflowsInWhichWidgetIsUsed(
      '1',
      this.configService.SelectedProjectId,
      customWidgetId,
    );
    let latestWidget = apiResponse[0];
    this.workFlowInWhichWidgetIsUsed = latestWidget.widget_usage_response;
    this.widgetId = latestWidget.widget_id;
    this.widgetVersion = latestWidget.widget_version;
  }

  private copyCustomWidgetDataIntoFormDataForViewing(customWidget: any) {
    this.formData = {
      ...this.formData,
      ...customWidget,
    };
    this.module_id = customWidget.module_id;
  }

  private fillTheFormDataWithItemNameItemSource() {
    this.finalresponse.function_inputs.forEach((item: any) => {
      this.formData[item.name + '_select'] = item.source;
    });
  }

  private reMapInputMapInModuleAsFunctionInput(customWidget: any) {
    this.finalresponse.function_inputs = customWidget.inputs_map.map(
      (inputMapFromApi: any) => {
        this.inputTextValues[inputMapFromApi.arg_name] =
          inputMapFromApi.default_value;
        let name = inputMapFromApi.arg_name;
        return { ...inputMapFromApi, name };
      },
    );
  }

  enableAllTabs() {
    this.is_InformationTab = true;
    this.is_inputTab = true;
    this.is_outputTab = true;
    this.is_settingsTab = true;
    this.is_parametersTab = true;
    this.isDisabled = false;
    this.is_Publish = false;
  }

  getFileName(filePath: any): string {
    let array = filePath.split('/');
    return array[array.length - 1];
  }

  setWidgetStatusFlag(customWidgetRecipe: any) {
    this.isWidgetInDraftState = customWidgetRecipe.recipe_status == 'DRAFT';
    this.isWidgetInPublishedState =
      customWidgetRecipe.recipe_status == 'PUBLISHED';
  }

  ngOnDestroy() {
    this.validationLogWebSocket?.unsubscribe();
  }

  // toggleMainHeader() {
  // this.showMainHeader = !this.showMainHeader;
  // this.toggleHeaderButton = this.showMainHeader
  //   ? 'expand_less'
  //   : 'expand_more';
  // }

  generateDropdowns() {
    if (this.finalresponse && this.finalresponse.file_names) {
      this.inputs = this.finalresponse.file_names
        .filter((fileName: string) => fileName.endsWith('.csv'))
        .map((fileName: any, index: number) => ({
          value: index + 1,
          label: fileName,
        }));
    } else {
      this.inputs = [];
    }
  }

  isCsvFile(fileName: string): boolean {
    return fileName.toLowerCase().endsWith('.csv');
  }

  generateOutputs() {
    this.outputs = Array.from(
      { length: this.selectedNumberOfOutputs },
      (_, i) => i + 1,
    );
  }

  toggleActivityLog(): void {
    this.showActivityLog = !this.showActivityLog;
  }

  generateRandomId(): string {
    const timestamp = new Date().getTime().toString();
    return timestamp;
  }

  getPlaceHolderForPythonDataTypes(type: any) {
    switch (type) {
      case "<class 'str'>":
        return 'Please enter a string value';
      case 'list[str]':
        return 'Enter string list Eg: ["a","b","c"] ';
      case "<class 'float'>":
        return 'Enter a float Eg: 2.1 ';
      case "<class 'int'>":
        return 'Enter an Integer Eg: 5 ';
      case "<class 'pandas.core.frame.DataFrame'>":
        return 'DATASET';
      case 'list[float]':
        return 'Enter float list Eg: [1.23,2.32,4.55] ';
      case 'list[int]':
        return 'Enter integer list Eg: [1,2,3] ';
      case "<class 'dict'>":
        return 'Eg: {"name":"alpha", "isActive": True}';
      default:
        return 'Please Enter A Default Value';
    }
  }

  isFileUploadInProgress = false;
  async uploadFileToFileSystem(event: any, itemName: any): Promise<any> {
    const file = event.target.files[0];
    this.isFileUploadInProgress = true;
    if (file) {
      try {
        let response: any = await this.apiService.uploadFileWithFixedPath(file);
        this.onInputValueChanged(response?.files[0].file_path, itemName);
      } catch (error) {
        console.error('Error during file upload:', error);
      }
    }
    this.isFileUploadInProgress = false;
  }

  getFileNameFromFilePath(filePath: any) {
    try {
      return filePath.split('/').pop();
    } catch (error) {
      console.error('File name not present');
    }
    return filePath;
  }

  uploadedLocalFiles: any = undefined;
  async onFileSelected(event: any) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    this.fileinput = true;

    const siteId = this.configService.SelectedSiteId;
    this.selectedFiles = Array.from(event.target.files);
    this.selectedFileName = this.selectedFiles[0].name;
    if (
      this.selectedFileName.endsWith('.zip') ||
      this.selectedFileName.endsWith('.py')
    ) {
      this.uploadedType = this.selectedFileName.endsWith('.zip') ? 'ZIP' : 'PY';
      let file = event.target.files[0];
      this.showLoader = true;
      this.uploadedLocalFiles = file;
      this.processLocalUploadFileForViewingInEditor();
      await this.uploadTheCPWCode(file);
    } else {
      this.filesExtractedResponse =
        'Only compressed ZIP folders or python file is allowed.';
    }
  }

  async uploadTheCPWCode(file: any, fileName?: any) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    try {
      const response = await this.apiService.GetUploadFiles(
        file,
        selectedProjectId,
        1,
        this.selectedFileName.endsWith('.py'),
        fileName,
      );
      if (
        response.finalresponse !== void 0 &&
        response.finalresponse.metadata
      ) {
        if (
          this.module_id &&
          !this.isWidgetInDraftState &&
          this.customPythonWidgetRecipeId
        ) {
          if (
            this.functionSignature !=
            response.finalresponse.metadata.function_signature
          ) {
            this.filesExtracted = false;
            this.filesExtractedResponse =
              'New Function Signature is not matching with the existing one, Please create a new CPW';
            throw {
              message:
                'New Function Signature is not matching with the existing one, Please create a new CPW',
            };
          }
        }
      }

      if (this.module_id && !this.isWidgetInDraftState) {
        if (!response.finalresponse.succeeded) {
          this.filesExtracted = false;
          this.filesExtractedResponse = response.finalresponse.message;
          this.toaster.error(this.filesExtractedResponse, '', {
            positionClass: 'custom-toast-position',
          });
          return;
        }
        let pathOfTheNewlyUploadedFile =
          response.firstApiResponse.files[0].file_path;
        await this.apiService.replaceTheModuleFilePath(
          this.widgetId,
          pathOfTheNewlyUploadedFile,
        );
        this.filesExtracted = true;
        this.filesExtractedResponse = 'New code is successfully updated';
        this.toaster.success('File is succuessfuly replaced', '', {
          positionClass: 'custom-toast-position',
        });
        return;
      }

      if (response.firstApiResponse !== void 0) {
        this.firstresponse = response.firstApiResponse;
        this.showLoader = false;
      }
      if (response.secondApiResponse !== void 0) {
        this.getFiles = response.secondApiResponse;
        this.showLoader = false;
      }

      if (
        response.finalresponse !== void 0 &&
        response.finalresponse.metadata
      ) {
        this.finalresponse = response.finalresponse.metadata;
        this.finalresponse_help_details = response.finalresponse.help_details;
        this.finalresponse.function_inputs.forEach((item: any) => {
          this.formData[item.name + '_select'] =
            'INPUT_SELECTED_FROM_PRIOR_WIDGET';
        });
        const formattedFileNames = [];
        for (const fileName of this.finalresponse.file_names) {
          formattedFileNames.push({ name: fileName, path: fileName });
        }
        this.finalresponse.file_names_path = formattedFileNames;

        this.finalresponse.function_inputs.forEach(
          (item: { name: string | number }) => {
            this.isMandatory[item.name] = true;
          },
        );

        this.get_input = this.finalresponse.function_inputs;
        this.noofinputs = this.finalresponse.function_inputs.length;
        this.get_output = this.finalresponse.function_outputs.map(
          (output: string) => ({ label: 'DataFrame Type', type: output }),
        );
        this.noofoutputs = this.finalresponse.function_outputs.length;
        this.continue_button = true;
        if (response.finalresponse.succeeded) {
          this.filesExtracted = true;
          this.filesExtractedResponse =
            'Found 1 python file with desired method : Hexaind_Custom_Widget_Function';
          this.isCodeValidationEnabled = true;
          this.isContinueToConfiguration = true;
          this.isPythonCodeUpdatedWhileEditing = true;
          this.inputs_map = [
            ...this.finalresponse.function_inputs.map((item: any) => ({
              arg_name: item.name,
              type: item.type,
              default_value: '',
              is_mandatory: true,
              source: 'INPUT_SELECTED_FROM_PRIOR_WIDGET',
            })),
          ];
          this.displayString = [];
          this.extractFunctionDatatypes();
          this.isDisabled = false;
        }
      } else {
        if (!response.finalresponse.succeeded) {
          this.filesExtracted = false;
          this.filesExtractedResponse = response.finalresponse.message;
        }
      }
    } catch (error) {
      const err = error as any;
      if (err?.message) {
        this.toaster.error(err?.message, '', {
          positionClass: 'custom-toast-position',
        });
      }
      console.error('Error during file upload:', err.message);
      this.showLoader = false;
      this.isDisabled = true;
    }
  }

  diskMountDrive() {
    const dialogRef = this.dialog.open(MountedDriveDataPreviewComponent, {
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: {
        type: 'zip',
        name: '',
        description: '',
      },
    });
    dialogRef.afterClosed().subscribe(async (result) => {
      if (result.success) {
        let selectedProjectId: string | undefined =
          this.configService.SelectedProjectId;
        if (!selectedProjectId) {
          return;
        }
        this.mountdrivePathName = result.pathname;
        this.fileinput = true;
        const siteId = this.configService.SelectedSiteId;
        const file = {
          files: {
            0: {
              file_name: result.name,
              file_path: result.pathname,
            },
          },
        };
        if (result.name.endsWith('.zip')) {
          this.showLoader = true;
          if (file) {
            const response = await this.apiService.mountedUploadFiles(
              file,
              selectedProjectId,
              siteId,
            );
            if (response) {
              if (response.secondApiResponse !== void 0) {
                this.getFiles = response.secondApiResponse;
                this.showLoader = false;
              }

              if (
                response.finalresponse !== void 0 &&
                response.finalresponse.metadata
              ) {
                this.showLoader = false;
                this.finalresponse = response.finalresponse.metadata;
                this.finalresponse_help_details =
                  response.finalresponse.help_details;
                this.finalresponse.function_inputs.forEach((item: any) => {
                  this.formData[item.name + '_select'] =
                    'INPUT_SELECTED_FROM_PRIOR_WIDGET';
                });
                const formattedFileNames = [];
                for (const fileName of this.finalresponse.file_names) {
                  formattedFileNames.push({ name: fileName, path: fileName });
                }
                this.finalresponse.file_names_path = formattedFileNames;

                this.finalresponse.function_inputs.forEach(
                  (item: { name: string | number }) => {
                    this.isMandatory[item.name] = true;
                  },
                );

                this.get_input = this.finalresponse.function_inputs;
                this.noofinputs = this.finalresponse.function_inputs.length;
                this.get_output = this.finalresponse.function_outputs.map(
                  (output: string) => ({
                    label: 'DataFrame Type',
                    type: output,
                  }),
                );
                this.noofoutputs = this.finalresponse.function_outputs.length;
                this.continue_button = true;
                if (response.finalresponse.succeeded) {
                  this.filesExtracted = true;
                  this.filesExtractedResponse =
                    'Found 1 python file with desired method : Hexaind_Custom_Widget_Function';
                }
              } else {
                if (!response.finalresponse.succeeded) {
                  this.filesExtracted = false;
                  this.filesExtractedResponse = response.finalresponse.message;
                }
              }
            }
          }
        } else {
          this.fileinput = true;
          this.filesExtractedResponse =
            'Imported Mounted file is not a zip file';
        }
      }
    });
  }

  async onFileSelectedValue(event: any) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    this.fileinput = true;
    const siteId = this.configService.SelectedSiteId;
    const file = event.target.files[0];

    if (file) {
      try {
        const response = await this.apiService.getFileNames(
          file,
          selectedProjectId,
          siteId,
        );
        if (
          response &&
          response.firstApiResponse &&
          response.firstApiResponse.files
        ) {
          const files = response.firstApiResponse.files;

          files.forEach((fileInfo: any) => {
            this.finalresponse.file_names.push(fileInfo.file_path);
          });

          files.forEach((fileInfo: any) => {
            this.finalresponse.file_names_path.push({
              name: fileInfo.file_name,
              path: fileInfo.file_path,
            });
          });
        }
      } catch (error) {
        const err = error as any;
        console.error('Error during file upload:', err.message);
      }
    }
  }

  async onFileSelectedparameterValue(event: any) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    this.fileinput = true;
    const siteId = this.configService.SelectedSiteId;
    const file = event.target.files[0];

    if (file) {
      try {
        const response = await this.apiService.getFileNames(
          file,
          selectedProjectId,
          siteId,
        );
        if (
          response &&
          response.firstApiResponse &&
          response.firstApiResponse.files
        ) {
          this.defaultValuePath = response.firstApiResponse.files[0].file_path;
          this.updateInputsMap();
        }
      } catch (error) {
        const err = error as any;
        console.error('Error during file upload:', err.message);
      }
    }
  }

  removeFile(index: number) {
    this.selectedFiles.splice(index, 1);
  }

  showInfo() {
    this.showExcute = false;
    this.showInfoTab = true;
    this.showExecuteNxtab = false;
    this.showPreviewTab = false;
    this.dialogRef?.close();
  }

  backExecute() {
    this.showExcute = true;
    this.showExecuteNxtab = false;
    this.showPreviewTab = false;
  }

  areAllFieldsSelected(): boolean {
    if (
      Object.keys(this.inputValues).length === 0 ||
      Object.keys(this.selectedOutputs).length === 0
    ) {
      return false;
    }
    const allInputsSelected = Object.values(this.inputValues).every(
      (value) => !!value,
    );

    const allOutputsSelected = Object.values(this.selectedOutputs).every(
      (value) => !!value,
    );

    return allInputsSelected && allOutputsSelected;
  }

  async execute() {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    const validations = this.assignInputOutputMap();
    this.showExcute = false;
    this.showExecuteNxtab = true;
    this.showPreviewTab = false;
    this.showLoader = true;
    if (validations) {
      try {
        this.correlationId = uuidv4();
        const response = await this.apiService.executeValidation(
          siteId,
          selectedProjectId,
          validations,
          this.correlationId,
        );
        this.activityLogs = [];
        this.isValidationLogError = false;
        if (response) {
          this.apiService.connect(
            this.correlationId,
            siteId,
            selectedProjectId,
          );

          this.validationLogWebSocket = this.apiService
            .onMessage()
            .pipe(
              tap((message: string) => {
                let socketMessage = JSON.parse(message);
                this.checkIfMessageContainsEntryFileName(socketMessage);
                this.activityLogs.push({
                  isMainErrorMessage: this.isValidationLogError,
                  message: socketMessage,
                });
              }),
              catchError((error: any) => {
                console.log(error);
                return error;
              }),
              finalize(() => {
                () => console.log('Socket closed');
              }),
            )
            .subscribe();

          await this.createModule(siteId, selectedProjectId);
          this.is_preview = true;
          if (response.succeeded) {
            this.executionStatus = true;
            this.showLoader = false;
            this.executionMsg =
              'Validation successful for custom Python code widget.';
          } else {
            this.executionStatus = false;
            this.showLoader = false;
            this.executionMsg =
              'Validation failed for this custom python code widget.';
          }
        } else {
          if (!response.succeeded) {
            this.executionStatus = false;
            this.showLoader = false;
            this.executionMsg =
              'Validation failed for this custom python code widget.';
          }
          this.is_preview = false;
        }
      } catch (error) {
        const err = error as any;
        console.error('Error during file upload:', err.message);
      }
    }
  }

  private async createModule(siteId: string, selectedProjectId: string) {
    const validation_request_id = this.generateRandomId();
    const validations_module = {
      metadata: this.finalresponse,
      file_path: this.firstresponse
        ? this.firstresponse.files[0].file_path
        : this.mountdrivePathName,
    };
    (validations_module as any).name = 'test';
    const updatedMetadata = {
      ...validations_module.metadata,
      validation_request_id: validation_request_id,
      is_validated: true,
    };
    const updatedPayload = {
      ...validations_module,
      metadata: updatedMetadata,
    };
    const module_response = await this.apiService.createModuleId(
      siteId,
      selectedProjectId,
      updatedPayload,
    );
    this.module_id = module_response.module_id;
    this.formData.module_id = this.module_id;
    this.isPythonCodeUpdatedWhileEditing = false;
  }

  private assignInputOutputMap() {
    const validationInputs: any = [];
    for (const input of this.finalresponse.function_inputs) {
      if (input.type === "<class 'pandas.core.frame.DataFrame'>") {
        validationInputs.push({
          param_name: input.name,
          type: "<class 'pandas.core.frame.DataFrame'>",
          value: this.inputValues[input.name],
        });
      } else if (input.type === "<class 'str'>") {
        validationInputs.push({
          param_name: input.name,
          type: "<class 'str'>",
          value: this.inputValues[input.name],
        });
      }
    }

    const validationOutputs = [];
    for (const [
      index,
      output,
    ] of this.finalresponse.function_outputs.entries()) {
      if (output === "<class 'pandas.core.frame.DataFrame'>") {
        validationOutputs.push({
          param_name: 'Output' + (index + 1),
          type: "<class 'pandas.core.frame.DataFrame'>",
          value: this.selectedOutputs['output' + (index + 1)],
        });
      } else if (
        output ===
        "<class 'app.services.data.assets.custom_python_support.service.TextCPWDataset'>"
      ) {
        validationOutputs.push({
          param_name: 'Output' + (index + 1),
          type: "<class 'app.services.data.assets.custom_python_support.service.TextCPWDataset'>",
          value: this.selectedOutputs['output' + (index + 1)],
        });
      } else {
        validationOutputs.push({
          param_name: 'Output' + (index + 1),
          type: output,
          value: this.selectedOutputs['output' + (index + 1)],
        });
      }
    }
    const validations = {
      validation_inputs: validationInputs,
      validation_outputs: validationOutputs,
      metadata: this.finalresponse,
      file_path: this.firstresponse
        ? this.firstresponse.files[0].file_path
        : this.mountdrivePathName,
    };
    this.formValues = validations;
    this.isInputOutputMappingCompleted = true;
    return validations;
  }

  checkIfMessageContainsEntryFileName(socketMessage: string) {
    let entryFile: string = '/' + this.formValues.metadata.entry_file;
    if (socketMessage.match(entryFile)) this.isValidationLogError = true;
  }

  gobackPreview() {
    this.showExcute = false;
    this.showInfoTab = true;
    this.showExecuteNxtab = false;
    this.showPreviewTab = false;
    this.switchToValidationTab();
  }

  preview() {
    this.showExcute = false;
    this.showExecuteNxtab = false;
    this.showInfoTab = true;
    this.dialogRef?.close();
    this.switchToInputsTab();
  }

  isFormValid() {
    if (
      this.formData.name &&
      typeof this.formData.name === 'string' &&
      this.formData.name.trim() !== '' &&
      this.formData.description &&
      typeof this.formData.description === 'string' &&
      this.formData.description.trim() !== '' &&
      this.formData.reference_links &&
      this.formData.reference_links !== '' &&
      this.formData.tags &&
      this.formData.tags !== ''
    ) {
      return true;
    } else {
      return false;
    }
  }

  getSubType(type: any) {
    switch (type) {
      case "<class 'pandas.core.frame.DataFrame'>":
        return 'TABULAR';
      default:
        return 'TEXT';
    }
  }

  getActionResultType(expectedType: any) {
    switch (expectedType) {
      case "<class 'str'>":
        return 'STRING';
      case 'list[str]':
        return 'STRINGS_LIST';
      case "<class 'float'>":
        return 'FLOAT';
      case "<class 'int'>":
        return 'INTEGER';
      case "<class 'pandas.core.frame.DataFrame'>":
        return 'DATASET';
      case 'list[float]':
        return 'FLOATS_LIST';
      case 'list[int]':
        return 'INTEGERS_LIST';
      case "<class 'dict'>":
        return 'DICTIONARY';
      default:
        return expectedType;
    }
  }

  onInputValueChanged(value: string, itemName: string): void {
    // if (!value || value.trim() === '') {
    //   this.toaster.error(`Default value for ${itemName} cannot be empty!`);
    //   this.inputTextValues[itemName] = ''; // Reset invalid input
    // } else {
    this.inputTextValues[itemName] = value;
    this.updateInputsMap(); // Update mapping
  }

  createDefaultDropDownDetails(item: any) {
    item.drop_down_details = {
      is_dropdown: true,
      drop_down_type: 'SINGLE_SELECT',
      drop_down_source_details: {
        drop_down_source_type: 'STATIC',
        drop_down_values: [],
        drop_down_selected_values: [],
      },
    };
  }

  onIsDropDownChange(event: any, item: any) {
    if (event.target.checked) {
      this.createDefaultDropDownDetails(item);
    } else {
      item.drop_down_details = {};
    }
  }

  onDropDownTypeChange(event: any, item: any) {
    item.drop_down_details.drop_down_type = event;
  }

  onParameterTextInputChange(event: any, item: any) {
    item.drop_down_details.drop_down_source_details.drop_down_values =
      this.convertStringToArray(event);
  }

  onParameterDropDownChange(event: any, item: any) {
    item.drop_down_details.drop_down_source_details.dynamic_sub_type = event;
  }

  convertStringToArray(string: any) {
    return string.split(',');
  }

  updateInputsMap() {
    this.defaultValueText = this.inputTextValues;
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    this.inputs_map = this.finalresponse.function_inputs.map((item: any) => {
      let defaultValue = '';
      if (
        this.formData[item.name + '_select'] ===
        'INPUT_ENTERED_MANUALLY_ON_WIDGET'
      ) {
        if (
          this.defaultValueText === null ||
          this.defaultValueText === undefined
        ) {
          defaultValue = this.defaultValuePath;
        } else if (
          typeof this.defaultValueText === 'object' &&
          this.defaultValueText !== null
        ) {
          const defaultValueObj = this.defaultValueText[item.name];
          if (item.type === "<class 'pandas.core.frame.DataFrame'>") {
            defaultValue = this.defaultValuePath;
          } else {
            defaultValue = defaultValueObj ? defaultValueObj : '';
          }
        } else {
          console.error('defaultValueText is not an object');
        }
      } else if (
        this.formData[item.name + '_select'] ===
        'INPUT_SELECTED_FROM_PRIOR_WIDGET'
      ) {
        defaultValue = '';
      }
      if (item.drop_down_details?.drop_down_source_details) {
        if (
          this.formData[item.name + '_select'] ===
          'INPUT_ENTERED_MANUALLY_ON_WIDGET'
        ) {
          item.drop_down_details.drop_down_source_details.drop_down_source_type =
            'STATIC';
        } else {
          item.drop_down_details.drop_down_source_details.drop_down_source_type =
            'DYNAMIC';
        }
      }

      return {
        arg_name: item.name,
        type: item.type,
        default_value: defaultValue,
        is_mandatory:
          this.isMandatory[item.name] !== undefined
            ? this.isMandatory[item.name]
            : false,
        source: this.formData[item.name + '_select'],
        drop_down_details: item.drop_down_details,
      };
    });
    const countInputSelected = this.inputs_map.filter(
      (item) => item.source === 'INPUT_SELECTED_FROM_PRIOR_WIDGET',
    ).length;

    this.noofinputs = countInputSelected;
    const count = this.inputs_map.filter(
      (item: any) => item.source === 'INPUT_SELECTED_FROM_PRIOR_WIDGET',
    ).length;
    this.widget_inputs_rules = {
      count: count,
      config: this.inputs_map
        .filter(
          (item: any) => item.source === 'INPUT_SELECTED_FROM_PRIOR_WIDGET',
        )
        .map((item: any) => ({
          count: 1,
          expected_type: this.getActionResultType(item.type),
          expected_type_constraints: { sub_type: this.getSubType(item.type) },
        })),
    };

    this.widget_outputs_rules = {
      count: this.outputs_map.length,
      config: this.outputs_map
        .filter(
          (item: any) =>
            item.type === "<class 'pandas.core.frame.DataFrame'>" ||
            item.type === "<class 'str'>",
        )
        .map((item: any) => ({
          count: 1,
          expected_type: this.getActionResultType(item.type),
          ...(item.type !== "<class 'str'>" && {
            expected_type_constraints: { sub_type: this.getSubType(item.type) },
          }),
        })),
    };

    this.formData = {
      ...this.formData,
      inputs_map: this.inputs_map,
      outputs_map: this.outputs_map,
      module_id: this.module_id,
      project_id: selectedProjectId,
      site_id: siteId,
      access_mode: 'EXTERNAL',
      version: '1.0',
      widget_inputs_rules: this.widget_inputs_rules,
      widget_outputs_rules: this.widget_outputs_rules,
      help_details: this.finalresponse_help_details,
      settings: {
        color_code: '#121312',
        allow_users_to_modify_configurations: true,
      },
    };
  }

  validate() {
    this.showExcute = true;
    this.showInfoTab = false;
    this.showExecuteNxtab = false;
    this.showPreviewTab = false;
  }

  continue() {
    this.switchToInfoTab();
  }

  async continue1() {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    this.stringToArray();
    if (!this.isInputOutputMappingCompleted) {
      this.assignInputOutputMap();
    }

    this.inputs_map = [
      ...this.finalresponse.function_inputs.map((item: any) => ({
        arg_name: item.name,
        type: item.type,
        default_value: item.default_value ? item.default_value : '',
        is_mandatory: true,
        source: 'INPUT_SELECTED_FROM_PRIOR_WIDGET',
        drop_down_details: item.drop_down_details,
      })),
    ];
    this.displayString = [];
    this.extractFunctionDatatypes();
    if (this.inputs_map.some((item) => item.source)) {
      this.noofinputs = this.inputs_map.length;
    }
    this.outputs_map = [
      ...this.formValues.validation_outputs
        .map((item: any) => {
          if (item.type === "<class 'pandas.core.frame.DataFrame'>") {
            return {
              type: item.type,
              mapped_output: {
                reference_name: item.param_name,
                type: this.getActionResultType(item.type),
                sub_type: this.getSubType(item.type),
              },
            };
          } else if (
            item.type ===
            "<class 'app.services.data.assets.custom_python_support.service.TextCPWDataset'>"
          ) {
            return {
              type: item.type,
              mapped_output: {
                reference_name: item.param_name,
                type: this.getActionResultType(item.type),
                sub_type: 'TEXT',
              },
            };
          } else if (
            item.type === "<class 'str'>" ||
            item.type === "<class 'int'>" ||
            item.type === "<class 'float'>" ||
            item.type === "<class 'dict'>"
          ) {
            return {
              type: item.type,
              mapped_output: {
                reference_name: item.param_name,
                type: this.getActionResultType(item.type),
              },
            };
          } else if (
            item.type === 'list[float]' ||
            item.type === 'list[int]' ||
            item.type === 'list[str]'
          ) {
            return {
              type: item.type,
              mapped_output: {
                reference_name: item.param_name,
                type: this.getActionResultType(item.type),
              },
            };
          } else {
            return {
              type: item.type,
              mapped_output: {
                reference_name: item.param_name,
                type: 'STRING',
              },
            };
          }
        })
        .filter((output: any) => output !== null),
    ];

    if (this.outputs_map.some((item) => item.source)) {
      this.noofoutputs = this.outputs_map.length;
    }
    const count = this.inputs_map.filter(
      (item: any) => item.source === 'INPUT_SELECTED_FROM_PRIOR_WIDGET',
    ).length;

    this.widget_inputs_rules = {
      count: count,
      config: this.inputs_map
        .filter(
          (item: any) => item.source === 'INPUT_SELECTED_FROM_PRIOR_WIDGET',
        )
        .map((item: any) => ({
          count: 1,
          expected_type: this.getActionResultType(item.type),
          ...(item.type !== "<class 'str'>" && {
            expected_type_constraints: { sub_type: this.getSubType(item.type) },
          }),
        })),
    };

    this.widget_outputs_rules = {
      count: this.outputs_map.length,
      config: this.outputs_map
        .filter(
          (item: any) =>
            item.type === "<class 'pandas.core.frame.DataFrame'>" ||
            item.type === "<class 'str'>",
        )
        .map((item: any) => ({
          count: 1,
          expected_type: this.getActionResultType(item.type),
          ...(item.type !== "<class 'str'>" && {
            expected_type_constraints: { sub_type: this.getSubType(item.type) },
          }),
        })),
    };

    this.formData = {
      ...this.formData,
      inputs_map: this.inputs_map,
      outputs_map: this.outputs_map,
      module_id: this.module_id,
      project_id: selectedProjectId,
      site_id: siteId,
      access_mode: 'EXTERNAL',
      version: '1.0',
      widget_inputs_rules: this.widget_inputs_rules,
      widget_outputs_rules: this.widget_outputs_rules,
      help_details: this.finalresponse_help_details,
      settings: {
        color_code: '#121312',
        allow_users_to_modify_configurations: true,
      },
    };
    if (this.isFormValid()) {
      this.isDisabled = false;
    } else {
      this.isDisabled = true;
    }
    this.is_ContinueDone = true;
    this.updateInputsMap();
    // this.switchToParametersTab();
  }

  private extractFunctionDatatypes() {
    this.inputs_map.map((event) => {
      if (event.type === "<class 'pandas.core.frame.DataFrame'>") {
        this.displayString.push('Pandas');
      } else if (event.type === "<class 'int'>") {
        this.displayString.push('Integer');
      } else if (event.type === "<class 'float'>") {
        this.displayString.push('Float');
      } else if (event.type === "<class 'str'>") {
        this.displayString.push('String');
      } else if (event.type === "<class 'dict'>") {
        this.displayString.push('Python Dictionary');
      } else if (event.type == "<class 'pathlib.Path'>") {
        this.displayString.push('File Upload');
      } else {
        this.displayString.push(event.type);
      }
    });
  }

  private stringToArray() {
    if (this.formData.tags && typeof this.formData.tags === 'string') {
      this.formData.tags = this.formData.tags
        .split(',')
        .map((tag: string) => tag.trim());
    }
    if (
      this.formData.reference_links &&
      typeof this.formData.reference_links === 'string'
    ) {
      this.formData.reference_links = this.formData.reference_links
        .split(',')
        .map((tag: string) => tag.trim());
    }
    this.assignEmptyTagsArrayIfTagsUndefined();
    this.assingEmpytTagsIfRefrenceLinksUndefined();
  }

  assignEmptyTagsArrayIfTagsUndefined() {
    if (!this.formData.tags) {
      this.formData.tags = [];
    }
  }
  assingEmpytTagsIfRefrenceLinksUndefined() {
    if (!this.formData.reference_links) {
      this.formData.reference_links = [];
    }
  }

  continue11() {
    this.switchToParametersTab();
  }

  continue2() {
    this.isDisabled = false;
    this.switchToInputsTab();
  }

  continue3() {
    this.switchToOutputsTab();
  }

  continue4() {
    this.switchToSettingsTab();
  }

  switchToValidationTab() {
    if (this.tabGroup) {
      this.tabGroup.selectedIndex = 0;
    }
  }

  switchToInfoTab() {
    if (this.tabGroup) {
      this.tabGroup.selectedIndex = 1;
      this.is_InformationTab = true;
    }
  }

  switchToParametersTab() {
    if (this.tabGroup) {
      this.tabGroup.selectedIndex = 2;
      this.is_parametersTab = true;
    }
  }

  switchToInputsTab() {
    if (this.tabGroup) {
      this.tabGroup.selectedIndex = 3;
      this.is_inputTab = true;
    }
  }

  switchToOutputsTab() {
    if (this.tabGroup) {
      this.tabGroup.selectedIndex = 4;
      this.is_outputTab = true;
    }
  }

  switchToSettingsTab() {
    if (this.tabGroup) {
      this.tabGroup.selectedIndex = 5;
      this.is_settingsTab = true;
    }
  }

  async publish() {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    if (this.isWidgetInPublishedState) {
      await this.save();
    }
    const siteId = this.configService.SelectedSiteId;

    const payload = {
      custom_python_widget_recipe_id: this.customPythonWidgetRecipeId,
      custom_python_widget_id: this.widgetId,
      widget_version: this.widgetVersion,
      user_id: '123',
      project_ids: [selectedProjectId],
      site_ids: [siteId],
      access_mode: 'EXTERNAL',
    };

    try {
      const publishResponse = await this.apiService.publishRecipe(
        siteId,
        selectedProjectId,
        payload,
      );
      if (publishResponse.succeeded) {
        this.toaster.success(
          'Successfully Published custom python recipe',
          '',
          {
            positionClass: 'custom-toast-position',
          },
        );
      } else {
        this.toaster.error(publishResponse.message, '', {
          positionClass: 'custom-toast-position',
        });
      }
      this.router.navigate([
        '/sites',
        siteId,
        'projects',
        selectedProjectId,
        'custom-python-recipe',
      ]);
    } catch (error: any) {
      console.error('Error during recipe publishing:', error.message);
    }
  }

  navigate(pageName: string, assetType: string | undefined = undefined) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    const projectId = selectedProjectId;
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([`sites/${siteId}/projects/${projectId}/${pageName}`]);
  }

  async openValidationDialog(): Promise<any> {
    if (!this.popupTemplate) return;

    const isPublishingForFirstTime = !this.workFlowInWhichWidgetIsUsed;
    if (isPublishingForFirstTime) {
      this.publish();
      return;
    }

    const dialogConfig = new MatDialogConfig();
    dialogConfig.panelClass = 'custom-dialog-container';
    dialogConfig.backdropClass = 'custom-dialog-backdrop';
    dialogConfig.autoFocus = true;
    this.dialogRef = this.dialog.open(this.popupTemplate, dialogConfig);
  }

  async openCustomCodeValidationDialog() {
    if (!this.validationTemplate) return;
    const dialogConfig = new MatDialogConfig();
    dialogConfig.panelClass = 'validation-dialog-container';
    dialogConfig.backdropClass = 'custom-dialog-backdrop';
    dialogConfig.autoFocus = true;
    this.showExcute = true;
    this.dialogRef = this.dialog.open(this.validationTemplate, dialogConfig);
  }

  async proceedToValidationAndPublish(
    doProceedToValidation: boolean,
  ): Promise<void> {
    if (!doProceedToValidation) {
      this.dialogRef?.close();
      return;
    }
    this.isValidationInProgress = true;
    let validationResponse = await this.apiService.validateCustomWidget(
      '1',
      this.configService.SelectedProjectId,
      this.customPythonWidgetRecipeId,
    );
    this.validationMessage = validationResponse.validation_message;
    this.isValidationInProgress = false;
    if (!validationResponse.validation_status) {
      this.isValidationFailed = true;
    } else {
      this.isPublishingInProgress = true;
      validationResponse = 'Publishing the widget.....';
      await this.publish();
      this.dialogRef?.close();
      this.isPublishingInProgress = false;
    }
  }

  async save() {
    // const invalidInputs = this.formData.inputs_map.filter(
    //   (input: { arg_name: any; default_value: string }) => {
    //     const selectKey = `${input.arg_name}_select`;
    //     console.log(selectKey, 'select keyś', input.default_value);
    //     return (
    //       this.formData[selectKey] === 'INPUT_ENTERED_MANUALLY_ON_WIDGET' &&
    //       (!input.default_value || input.default_value.trim() === '')
    //     );
    //   },
    // );
    // console.log(this.formData,"invalid manula inputs",invalidInputs); return false;
    // if (invalidInputs.length > 0) {
    //   this.toaster.error(
    //     'Please fill all Default Values for manually entered inputs!',
    //   );
    //   throw "Default value Error"
    //   return; // Stop further execution if validation fails
    // }
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    if (this.showErrorMessageIfNameAndDescriptionAreNotPresent()) return;
    const siteId = this.configService.SelectedSiteId;
    try {
      this.stringToArray();
      if (!this.module_id || this.isPythonCodeUpdatedWhileEditing)
        await this.createModule(
          this.configService.SelectedSiteId,
          selectedProjectId,
        );
      if (!this.is_ContinueDone) {
        await this.continue1();
      }
      this.updateInputsMap();
      const save_response = await this.apiService.saveRecipe(
        siteId,
        selectedProjectId,
        this.formData,
      );
      this.customPythonWidgetRecipeId =
        save_response.custom_python_widget_recipe_id;
      if (save_response.succeeded) {
        this.toaster.success(save_response.message, '', {
          positionClass: 'custom-toast-position',
        });
        this.is_Publish = true;
      } else {
        this.is_Publish = false;
        this.toaster.error(save_response.message, '', {
          positionClass: 'custom-toast-position',
        });
      }
    } catch (error) {
      const err = error as any;
      console.error('Error during file upload:', err.message);
    }
  }

  public onChangeColorCmyk(color: string): Cmyk {
    const hsva = this.cpService.stringToHsva(color);

    if (hsva) {
      const rgba = this.cpService.hsvaToRgba(hsva);

      return this.cpService.rgbaToCmyk(rgba);
    }

    return new Cmyk(0, 0, 0, 0);
  }

  public onChangeColorHex8(color: string): string {
    const hsva = this.cpService.stringToHsva(color, true);

    if (hsva) {
      return this.cpService.outputFormat(hsva, 'rgba', null);
    }

    return '';
  }

  get colorCode(): string {
    return this._colorCode;
  }

  set colorCode(value: string) {
    this._colorCode = value;
    this.updateColor(value);
  }

  updateColor(color: string) {
    if (color !== this.widgetColor) {
      this.widgetColor = color;
      this.defaultColor = color;
      this.updateSettings();
    }
  }

  updateAllowUser() {
    if (this.allowUsersToModifyConfigurations == false) {
      this.allowUsersToModifyConfigurationstype = true;
    } else {
      this.allowUsersToModifyConfigurationstype = false;
    }
    this.updateSettings();
  }

  updateSettings() {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    const siteId = this.configService.SelectedSiteId;
    this.formData = {
      ...this.formData,
      inputs_map: this.inputs_map,
      outputs_map: this.outputs_map,
      module_id: this.module_id,
      project_id: selectedProjectId,
      site_id: siteId,
      access_mode: 'EXTERNAL',
      version: '1.0',
      widget_inputs_rules: this.widget_inputs_rules,
      widget_outputs_rules: this.widget_outputs_rules,
      help_details: this.finalresponse_help_details,
      settings: {
        color_code: this.widgetColor,
        allow_users_to_modify_configurations:
          this.allowUsersToModifyConfigurationstype,
      },
    };
  }

  onBlur(key: any, newValue: any): void {
    this.finalresponse_help_details[key] = newValue;
    this.updateInputsMap();
  }

  showMountedDriveDialog() {
    const dialogRef = this.dialog.open(MountedDriveDataPreviewComponent, {
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: {
        type: 'dataset',
        name: '',
        description: '',
      },
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        // this.getData();
      }
    });
  }

  async openCustomWidgetPreview(): Promise<void> {
    if (this.showErrorMessageIfNameAndDescriptionAreNotPresent()) return;

    await this.continue1();
    const previewData = {
      ...this.formData,
      created_at: Date.now(),
      created_by: '',
      module_id: '',
      recipe_id: '',
    };

    try {
      const widgetPreviewData = await this.apiService.viewRecipeAsCustomWidget(
        '1',
        this.configService.SelectedProjectId,
        previewData,
      );

      const dialogRef = this.dialog.open(CustomCodeConfigComponent, {
        width: '80vw',
        height: '60vh',
        data: { widgetPreviewData },
      });

      dialogRef.afterClosed().subscribe(async (result) => {
        if (result?.isPublish) {
          try {
            await this.save();
            if (this.is_Publish) {
              await this.publish();
            }
          } catch (error) {
            return;
          }
        }
      });
    } catch (error) {
      console.error('Failed to load widget preview:', error);
      this.toaster.error(
        'Preview failed, please re-check default values for type errors',
        '',
        {
          positionClass: 'custom-toast-position',
        },
      );
    }
  }

  showErrorMessageIfNameAndDescriptionAreNotPresent(): any {
    if (this.formData.name === '' || !this.formData.name) {
      this.toaster.error('Widget Name is Mandatory', '', {
        positionClass: 'custom-toast-position',
      });
      return true;
    }
    if (this.formData.description === '' || !this.formData.description) {
      this.toaster.error('Widget Description is Mandatory', '', {
        positionClass: 'custom-toast-position',
      });
      return true;
    }
    return false;
  }

  async openDatasetDownload() {
    let projectId: any = this.configService.SelectedProjectId;

    const downloadUrl = await this.apiService.DownloadDatset(
      '1',
      projectId,
      this.module_id,
      'PYTHON',
    );

    const link = document.createElement('a');
    link.href = downloadUrl; // Set the href to the download URL
    link.download = ''; // If you want a specific filename, set it here
    link.style.display = 'none'; // Hide the element

    document.body.appendChild(link); // Append to the DOM
    link.click(); // Programmatically trigger the click event
    document.body.removeChild(link); // Clean up the DOM by removing the link
  }

  extractedPythonFilesForEditing: any;
  isCPWCodeEditButtonDisabled = false;
  async processCPWCodeFilesAndOpenCodeEditor() {
    try {
      this.isCPWCodeEditButtonDisabled = true;
      if (this.uploadedLocalFiles) {
        this.openCPWCodeEditor();
        return;
      }
      let projectId: any = this.configService.SelectedProjectId;
      let files = [];
      const downloadUrl = await this.apiService.DownloadDatset(
        '1',
        projectId,
        this.module_id,
        'PYTHON',
      );
      const response = await fetch(downloadUrl, {
        method: 'GET',
        cache: 'no-store',
      });
      if (this.uploadedType == 'ZIP') {
        const zipBlob = await response.blob();
        const zip = await JSZip.loadAsync(zipBlob);
        for (const fileName of Object.keys(zip.files)) {
          // if(fileName.endsWith('.py')) {
          const content = await zip.files[fileName].async('string');
          files.push({ name: fileName, content });
        }
      }

      if (this.uploadedType == 'PY') {
        let fileName = this.selectedFileName;
        const pythonFileAsString = await response.text();
        files.push({ name: fileName, content: pythonFileAsString });
      }

      this.extractedPythonFilesForEditing = files;
      this.openCPWCodeEditor();
    } catch (error) {
      console.log(error);
    } finally {
      this.isCPWCodeEditButtonDisabled = false;
    }
  }

  async processLocalUploadFileForViewingInEditor() {
    const files = [];

    if (this.uploadedLocalFiles.name.endsWith('.zip')) {
      const zipBlob = this.uploadedLocalFiles;
      const zip = await JSZip.loadAsync(zipBlob);

      for (const fileName of Object.keys(zip.files)) {
        const content = await zip.files[fileName].async('string');
        files.push({ name: fileName, content });
      }
    } else if (this.uploadedLocalFiles.name.endsWith('.py')) {
      const pythonFileAsString = await this.uploadedLocalFiles.text();
      files.push({
        name: this.uploadedLocalFiles.name,
        content: pythonFileAsString,
      });
    }

    this.extractedPythonFilesForEditing = files;
  }

  async saveAndPushTheChanges() {
    if (this.uploadedType == 'ZIP') {
      const zip = new JSZip();
      this.extractedPythonFilesForEditing.forEach((file: any) => {
        zip.file(file.name, file.content);
      });
      let zippedContent = await zip.generateAsync({ type: 'blob' });
      await this.uploadTheCPWCode(zippedContent, this.selectedFileName);
    }
    if (this.uploadedType == 'PY') {
      const blob = new Blob([this.extractedPythonFilesForEditing[0].content], {
        type: 'text/x-python',
      });

      // Step 2: Create a File from the Blob with a .py extension
      const file = new File([blob], 'script.py', { type: 'text/x-python' });
      await this.uploadTheCPWCode(file, this.selectedFileName);
    }
  }

  originalFilesCache: any = undefined;
  openCPWCodeEditor() {
    this.originalFilesCache = this.extractedPythonFilesForEditing.map(
      (element: any) => {
        return { ...element };
      },
    );
    const dialogRef = this.dialog.open(CpwCodeEditorComponent, {
      disableClose: true,
      data: {
        arrayOfFiles: this.extractedPythonFilesForEditing,
      },
    });

    dialogRef.componentInstance.saveEvent.subscribe(async () => {
      try {
        dialogRef.componentInstance.isSavingInProgress = true;
        await this.saveAndPushTheChanges();
        if (this.filesExtracted == false) {
          dialogRef.componentInstance.updateBackendLogs(
            this.filesExtractedResponse,
          );
          return;
        }
        this.updateTheCacheWithTheSavedChanges();
        dialogRef?.close({ isSaved: true });
      } catch (error) {
        console.error(error);
      } finally {
        dialogRef.componentInstance.isSavingInProgress = false;
      }
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result?.isSaved == false) {
        this.revertTheFileChangesInEditor();
      }
    });
  }

  revertTheFileChangesInEditor() {
    this.extractedPythonFilesForEditing = this.originalFilesCache.map(
      (element: any) => {
        return { ...element };
      },
    );
  }

  updateTheCacheWithTheSavedChanges() {
    this.originalFilesCache = this.extractedPythonFilesForEditing.map(
      (element: any) => {
        return { ...element };
      },
    );
  }

  onRadioButtonChange(event: any) {
    this.isLocalDriveUpload = event.value == '1' ? true : false;
  }
}
