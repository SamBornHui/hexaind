import { Component, ViewChild } from '@angular/core';
import {
  DomSanitizer,
  EventManager,
  SafeResourceUrl,
} from '@angular/platform-browser';
import { ConfigService } from '../workflow-designer/workflow-canvas.service';
import { ActivatedRoute, Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from 'src/app/services/api.service';
import { DatePipe } from '@angular/common';
import { MatDialog } from '@angular/material/dialog';
import { DataCatalogService } from '../tools/data-catalog/data-catalog.service';
import { ThemeService } from 'src/app/services/theme.service';
import { MatPaginator, MatPaginatorIntl } from '@angular/material/paginator';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatSelect } from '@angular/material/select';
import { forkJoin } from 'rxjs';
import { map } from 'rxjs/operators';
import { TravelerStepsComponent } from './traveler-steps/traveler-steps.component';
import { SigmaCommonTestComponent } from './sigma-common-test/sigma-common-test.component';
import { AdvanceSearchComponent } from './advance-search/advance-search.component';
import { AdvanceSearchSigmaComponent } from './advance-search-sigma/advance-search-sigma.component';
import { MatCheckboxChange } from '@angular/material/checkbox';
import { UC2SigmaDataPreviewComponent } from './uc2-sigma-data-preview/uc2-sigma-data-preview.component';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';
import { Uc3ProbeModelPopupComponent } from './uc3-probe-model-popup/uc3-probe-model-popup.component';
import { ColumnDropDownComponent } from 'src/app/util-components/column-drop-down/column-drop-down.component';
import { WidgetType } from 'src/app/models/workflow-models';
import { Utils } from 'src/app/utils';

export interface ToolStatus {
  TOOL_ID: any;
  TOOL_NAME: string;
}

export interface Recipe {
  recipe_name: string;
}

export interface RecipeStatus {
  uniques: string;
  rows_count: string;
}

export interface GenerateToolsStatusResponse {
  tools: ToolStatus[];
}

export interface Tool {
  TOOL_ID: number;
  TOOL_NAME: string;
}

export interface GenerateToolIdsResponse {
  data: Tool[];
}
@Component({
  selector: 'app-uc7',
  templateUrl: './uc7.component.html',
  styleUrls: ['./uc7.component.less'],
})
export class Uc7Component {
  searchSensors: any;
  searchStepId: any;
  setTravelerStepId: string | undefined;

  showPolling: boolean | undefined = false;
  pollingPercentage: any;

  fabDropdownSettings = {};
  fabDropdownList: any = [];
  selectedFab: any;

  maxDate: any;
  startDate: any;
  endDate: any;

  newToolName: string = '';
  newToolId: string = '';
  newStepId: string = '';
  newSensor: string = '';
  showAddToolInput: boolean[] = [];
  showAddStepIdInput: boolean[] = [];
  showAddSensorInput: boolean[] = [];

  techDropdownSettings = {};
  techDropdownList = [];
  selectedTech: any;

  didDropdownSettings = {};
  didDropdownList = [];
  selectedDid: any;

  travelerIdDropdownSettings = {};
  travelerIdDropdownList = [];
  selectedTravelerid: any;
  searchToolId: any;

  travelerStepDropdownSettings = {};
  travelerStepDropdownList = [];
  selectedTravelerSteps: any;

  sensorDropdownSettings = {};
  sensorsDropdownList = [];
  uC2FdSelectedSensors: string[][] = [];

  spinnerVisible: boolean = false;
  fabLoadPercentage = 0;
  techLoadPercentage = 0;
  didLoadPercentage = 0;
  travelerIdLoadPercentage = 0;
  travelerLoadPercentage = 0;
  sensorLoadPercentage = 0;
  generateLoadPercentage: any;
  sensorDownloadPercentage = 0;

  isFDTraceOptions: boolean = false;
  isSigmaOptions: boolean = false;
  isSIGMADataCatalogue: boolean = false;
  isFDContextTrace: boolean = false;
  isProbeDataCatalogue: boolean = false;
  isSelectRegionLevel: boolean = false;

  tools: ToolStatus[] = [];
  filteredTools: ToolStatus[][] = [];
  filteredToolsSearchList: ToolStatus[][] = [];
  filterToolsSearchTerm: string = '';
  isUC2ToolNameSelectAll: boolean[] = [];
  uC2SelectedToolIds: string[][] = []; // To track selected tool IDs

  stepIdDropdownList: string[] = [];
  filteredStepIdDropdownList: string[][] = [];
  filteredStepIdDropdownSearchList: string[][] = []; // For search functionality
  uC2SelectedStepIds: string[][] = []; // To store selected step IDs
  isStepIdAllSelected: boolean[] = []; // For "Select All" in Step IDs

  sensorDropdownList: string[] = [];
  filteredSensorDropdownList: string[][] = [];
  filteredSensorDropdownSearchList: string[][] = []; // For search functionality
  isSensorAllSelected: boolean[] = []; // For "Select All" in Sensors

  searchSensor: string = ''; // For sensor search functionality

  config: any = {
    fd_trace: {
      file_path: '',
      selected_values: [],
    },
    sensors: {
      file_path: '',
      selected_values: [],
    },
    fd_contexts: {
      file_path: '',
      selected_values: [],
    },
    traveler_steps: {
      file_path: '',
      selected_values: [],
    },
    traveler_ids: {
      file_path: '',
      selected_values: [],
    },
    design_ids: {
      file_path: '',
      selected_values: [],
    },
    tech_nodes: {
      file_path: '',
      selected_values: [],
    },
    facilities: {
      file_path: '',
      selected_values: [],
    },
    lot_ids: {
      file_path: '',
      selected_values: [],
    },
    wafer_ids: {
      file_path: '',
      selected_values: [],
    },
    recipes: {
      file_path: '',
      selected_values: [],
    },
    tool_ids: {
      file_path: '',
      selected_values: [],
    },
    step_ids: {
      file_path: '',
      selected_values: [],
    },
    start_date: '',
    end_date: '',
    uc3_sigma_metro_steps: [],
    metro_step_common_step_ids: [],
    padding_days: 60,
    integrate_back_of_wafer_mesurement: false,
    wafer_level: false,
    point_level: false,
    regions: {
      file_path: '',
      selected_values: [],
    },
    use_probe: false,
    paretoname: {
      file_path: '',
      selected_values: [],
    },
    paretotitle: {
      file_path: '',
      selected_values: [],
    },
    die_counts_per_region: {
      A: 0,
      B: 0,
      C: 0,
      D: 0,
      E: 0,
    },
  };
  selectedSession: any;
  fabStage = 'FACILITIES';
  techStage = 'TECH_NODE';
  didStage = 'DESIGN_ID';
  travelerIdStage = 'TRAVELER_ID';
  travelerStepStage = 'TRAVELER_STEP';
  fdContextStage = 'FD_CONTEXT';
  fdSensorStage = 'FD_SENSOR';
  fdTraceStage = 'FD_TRACE';
  fdLotStage = 'LOT_ID';
  fdWafarId = 'WAFER_ID';
  fdContext = 'FD_CONTEXT';
  finalDataAggregate = 'FINAL_DATA_AGGREGATE';
  fdContextFilter = 'uc3_fd_context_apply_filters';
  highLevelSaveStage = 'SAVE_HIGH_LEVEL_DC_DETAILS';
  uc2SigmaStage = 'UC2_SIGMA_DATA';
  uc2FdStage = 'FINAL_DATA_AGGREGATE';
  uc3ProbeStage = 'PROBE_CONTEXT';
  uc3ProbeDataPullStage = 'PROBE_DATA_PULL';
  uc3SigmaStage = 'UC3_SIGMA_DATA';
  uc3LotWaferStage = 'LOT_WAFER_SAVE';
  fabQueryFilePath = '';
  techQueryFilePath = '';
  didQueryFilePath = '';
  travelerIdQueryFilePath = '';
  travelerQueryFilePath = '';
  sensorQueryFilePath = '';
  sessionData: any;
  disableGenerate = true;
  disableSensorDropdown = true;
  disableSensorDownload = true;
  fdTraceSensorPath: any;

  //table
  colWiseValues: Array<Record<string, any>> = [];
  filteredValues: Array<Record<string, any>> = [];

  colUnique: any;
  selectedColUniques = [];
  filter: Record<string, any> = {};
  selectedItems: any;
  path: any;
  getTablePath: any;
  downloadPath: any;
  tableData: any;
  displayedColumns: any;
  totalCount: any;
  flag = 0;
  fliterflag = 0;
  tableDataLoading = false;
  tableSpinner = false;
  rowsFdTable = [];
  columnFilterSettings = {};
  clickedRows = new Set<Array<Record<string, any>>>();
  originalData: any;
  pollingMsg: any;

  isTechPolling: boolean = false;
  isDidPolling: boolean = false;
  isTravelerIdPolling: boolean = false;
  isTravelerStepPolling: boolean = false;
  isGeneratePolling: boolean = false;
  isSensorPolling: boolean = false;
  isSensorDataPolling: boolean = false;
  @ViewChild(MatPaginator) paginator: any;

  searchfab: string = '';
  searchTechNode: string = '';
  searchDid: string = '';
  searchTravelerId: string = '';
  searchTravelerStep: string = '';
  // searchSensor: string = '';
  @ViewChild('matSelect1') matSelect1!: MatSelect;
  @ViewChild('matSelect2') matSelect2!: MatSelect;
  @ViewChild('matSelect3') matSelect3!: MatSelect;
  @ViewChild('matSelect4') matSelect4!: MatSelect;

  selectedUCOption: string | null = null;
  isTravelerAllSelected: boolean = false;
  isLoading: boolean = false;
  isDataAvailable: boolean = false;

  searchQueries: { [key: string]: string } = {};
  selectedItemsMap: { [key: string]: any[] } = {};
  private selectAllState: { [key: string]: boolean } = {};
  isfdTracePath: boolean = false;
  filterStartDate: any;
  filterEndDate: any;

  selectedLotIds: any = [];
  lotIdsLoadPercentage = 0;
  lotIdsDropdownList = [];
  lotIdsDropdownCount: Number = 0;
  isLotIdsPolling: boolean = false;
  lotIdsQueryFilePath = '';

  selectedWaferIds: any = [];
  WaferIdsLoadPercentage = 0;
  waferIdsDropdownList = [];
  waferIdsDropdownCount: Number = 0;
  isWaferIdsPolling: boolean = false;
  waferIdsQueryFilePath = '';

  isFDContextDownloadPath: boolean = false;
  selectedFDContext: any;
  FDContextLoadPercentage = 0;
  FDContextDropdownList = [];
  FDContextDropdownCount: Number = 0;
  isFDContextPolling: boolean = false;
  FDContextQueryFilePath = '';
  resultDataFilePath: any;
  FDContextList: any = [
    {
      processStepsList: '',
      recipeName: '',
      toolName: '',
      runID: '',
    },
  ];

  isGenerating: boolean = false;
  FDContextstartDate: any;
  previousColumnName: string = '';
  resultColumn: string = '';
  FDContextfilters: { [key: string]: any } = {};
  FDfilterApply: any = [];
  fdContexApplyFiltertLoadPercentage = 0;
  fdContextFilterApplyPath: string = '';
  fdContextFinalPath: string = '';
  FDApplyfilter: { [key: string]: any } = {};
  applyfilter: any = [];
  isFDContextFilterPolling: boolean = false;

  selectedGQLFileParquetPath: any;
  measurementStepGQLFileList: any = [];
  measurementStepGQLFileCount: any;
  runStepGQLFileList: any = [];
  waferParametersGQLFileList: any = [];
  measurementParametersGQLFileList: any = [];
  point_stepsGQLFileList: any = [];
  point_parametersGQLFileList: any = [];

  uc2SigmaRunParametersPath: any;
  isuc2SigmaRunParametersPath: boolean = false;
  uc2SigmaWaferParametersPath: any;
  isuc2SigmaWaferParametersPath: boolean = false;
  uc2SigmaMeasurementStepsPath: any;
  isuc2SigmaMeasurementStepsPath: boolean = false;
  uc2SigmaMeasurementParametersPath: any;
  isuc2SigmaMeasurementParametersPath: boolean = false;
  uc2SigmaPointStepsPath: any;
  isuc2SigmaPointStepsPath: boolean = false;
  uc2SigmaPointParametersPath: any;
  isuc2SigmaPointParametersPath: boolean = false;
  uc2SigmaLoadPercentage = 0;
  uc2SigmaSelectedData: any = {
    measurement_steps: {
      file_path: '',
      selected_values: [],
    },
    run_parameters: {
      file_path: '',
      selected_values: [],
    },
    point_steps: {
      file_path: '',
      selected_values: [],
    },
    measurement_parameters: {
      file_path: '',
      selected_values: [],
    },
    point_parameters: {
      file_path: '',
      selected_values: [],
    },
    wafer_parameters: {
      file_path: '',
      selected_values: [],
    },
    gql_file_details: {
      parquet_file_path: '',
      gql_file_path: '',
    },
  };
  uc2SigmaUploadButton: boolean = false;
  uc2SigmaGenerateButton: boolean = false;
  uc3ProbeGenerateButton: boolean = false;
  uc3ProbePreviewButton: boolean = true;
  uc2SigmaMeasumentStepsSubmitButton: boolean = true;
  uc2SigmaPointStepsSubmitButton: boolean = true;
  uc2SigmaResultPath: any;
  isuc2SigmaResultPath: boolean = false;
  isuc2SigmaResultFailed: boolean = false;
  uc2FdResultPath: any;
  isuc2FdResultPath: boolean = false;
  isuc2FdResultFailed: boolean = false;
  isUC2SigmaChecked: boolean = false;
  isUC2FdChecked: boolean = false;
  UC2SigmaStageResult: any;
  UC2FdStageResult: any = [];
  GetAdvanceUniques: any = [];
  isUC2SigmaMeasurementStepsSelectAll: boolean = false;
  UC2SigmaSelectedMeasurementSteps: any = [];
  isUC2SigmaMeasureParametersSelectAll: boolean = false;
  UC2SigmaSelectedMeasurementParameters: any = [];
  isUC2SigmaPointStepsSelectAll: boolean = false;
  isUC2SigmaPointParametersSelectAll: boolean = false;
  isUC2SigmaRunParametersSelectAll: boolean = false;
  isUC2SigmaWaferParametersSelectAll: boolean = false;
  UC2SigmaSelectedPointSteps: any = [];
  UC2SigmaSelectedPointParameters: any = [];
  UC2SigmaSelectedRunParameters: any = [];
  UC2SigmaSelectedWaferParameters: any = [];
  measurementStepGQLSearchList: any = [];
  uc2SearchTerm: string = '';
  pointStepsSearch: any;
  runParametersSearch: any;
  measumentParametersSearch: any;
  waferParametersSearch: any;
  pointParametersSearch: any;
  uc2SigmaMeasurementStepsInputValue: string = '';
  uc2SigmaMeasurementParametersInputValue: string = '';
  uc2SigmaPointStepsInputValue: string = '';
  uc2SigmaPointParametersInputValue: string = '';
  uc2SigmaRunParametersInputValue: string = '';
  uc2SigmaWaferParametersInputValue: string = '';
  isuc2SigmaDownloadPolling: boolean = false;
  isUC2SigmaDownloadCheck: boolean = false;

  metro_rows: any[] = [
    {
      selection: '',
    },
  ];

  processSteps: any;
  toolNames: any;
  runIds: any;
  FDstartDate: any;
  rows: any[] = [
    { processSteps: '', recipes: '', toolNames: '', runIds: '', startDate: '' },
  ];
  selectedDate = '';
  selectedStartDate: Date | undefined;
  isdcHighLevelSubmit: Boolean = true;

  uc3SigmaMetroStepPrefixList: any;
  uc3SigmaMetroStepPrefixListGet: any;
  // uc3SigmaMetroStepPrefixObj:any;
  uc3SigmaMetroStepsSelected: string[][] = [];
  uc3SigmaMetroStepsAddNew: string = '';
  uc3SigmaMetroStepsInputValue: string = '';
  uc3SigmaMetroStepsInputList: any;
  searchUc3SigmaMetroSteps: String = '';

  toolGroups: any[] = [];

  UC2FDTraceSelectedValue: any = {
    recipes: [],
    tools: [],
    stepIds: [],
    sensors: [],
  };

  i: number = 0;

  recipes: any;
  uC2FdselectedRecipeNames: string[][] = [];
  filteredRecipeNames: Recipe[] = [];
  isRecipeSelectAll: boolean[] = [];
  searchRecipeName: string = '';
  //recipes: Recipe[] = []; // Ensure this is populated with recipes
  showAddRecipeInput: boolean[] = [];
  newRecipeName: string = '';
  newRecipeId: string = '';
  selectedValues: any[] = [];

  isuc2FDTraceResultFailed: boolean = false;
  isuc2FDTraceDownloadPolling: boolean = false;
  isUC2FDGenerateButton: boolean = false;
  isUC2TraceToolsIdsValue: boolean = false;
  isUC2TraceStepIdsValue: boolean = false;
  isUC2TraceSensorsValue: boolean = false;

  isuc2FDGenaratePolling: boolean = false;
  uC2FdTraceAggrSelectedSensors: string[][] = [];

  allTools: any[] = [];
  baselineTravelerId: any;

  // Probe Variables
  inputProbeRegionA: any;
  inputProbeRegionB: any;
  inputProbeRegionC: any;
  inputProbeRegionD: any;
  inputProbeRegionE: any;
  selectedProbeColumns: any = [];
  isuc3ProbeDownloadPolling: boolean = false;
  uc3ProbeLoadPercentage = 0;
  isuc3ProbeResultPath: boolean = false;
  uc3ProbeResultPath: string = '';
  paritoTitle: any = [];
  paritoNames: any = [];
  uc3ProbeGenerateParitoNamesPath: any;
  uc3ProbeGenerateTitlePath: any;
  selectedParitoTitle: any;
  selectedParitoNames: any;
  probeReloadValues: any;
  isUC3ProbeChecked: boolean = false;
  isuc3ProbeReloadResultFailed: boolean = false;
  inputParitoNames: string = '';
  inputParitoTitle: string = '';
  searchParitoNames: any = [];
  searchParitoTitle: any = [];
  isUC3ProbeParitoTitleSelectAll: boolean = false;
  showAddParitoTitle: boolean = false;
  newParitoTitle: string = '';
  newparitoNames: string = '';

  isUc3SigmaMetroSelectAll: boolean[] = [];
  uc3CommonStepIds: any = [];
  uc3SigmaMetroRegionsSelected: any[] = [];
  uc3SigmaMetroRegionsList = [
    'Region A',
    'Region B',
    'Region C',
    'Region D',
    'Region E',
  ];
  isUc3SigmaMetroRegionsSelectAll: boolean = false;
  uc3SigmaCommonTestIdsSelected: any[] = [];
  isUC3DownloadDisable: boolean = true;
  isuc3SigmaDownloadPolling: boolean = false;
  uc3SigmaLoadPercentage = 0;
  isUC3SigmaResultPath: boolean = false;
  isUC3SigmaDownloadCheck: boolean = false;
  uc3SigmaResultPath: any;
  isuc3SigmaResultFailed: boolean = false;
  isUc3integrateWafer: boolean = false;
  isUc3integrateWaferInitial: boolean = false;
  isUc3WaferLevel: boolean = false;
  isUc3SelectLotidLevel: boolean = false;
  isUc3WaferLevelInitial: boolean = false;
  isUc3SelectRegionLevel: boolean = false;
  isUc3SelectRegionLevelInitial: boolean = false;
  uc3PaddingDays = 60;
  uc3PaddingDaysInitial: number = 60;
  uc3SigmaFinalSelection: any = [];
  searchUc3SigmaLotIds: string = '';
  searchUc3SigmaWaferIds: string = '';
  uc3SigmaUseProbe: boolean = false;
  uc3SigmaUseProbeInitial: boolean = false;
  isUC3SigmaLotIdsBeforeApi: boolean = false;
  isUC3SigmaCommonIdsBeforeApi: boolean = false;
  isLotWaferSave: boolean = true;

  responsePathRun: any;
  selectedNames: any;
  selected_path: any;

  selectedPathsByColumn: { [key: string]: string | null } = {};

  filepathMetro: any;
  upload_file_path: any;
  resetTravelerSteps: any;

  namesWithPrefixOne: any;
  prefixesStartingWithOne: any;

  uc3SigmaMetroStepPrefixObj: { [key: string]: string } = {};

  filtereduc3SigmaMetroStepPrefixList: string[] = [];

  cached_traveler_steps_values: any;

  uc3SigmaMetroStepPrefixListSelected: any;

  selectedCommontestidPath: any;

  commonidfilepath: any;

  constructor(
    private sanitizer: DomSanitizer,
    private configService: ConfigService,
    private router: Router,
    private apiService: ApiService,
    private datePipe: DatePipe,
    public dialog: MatDialog,
    private route: ActivatedRoute,
    private dataCatService: DataCatalogService,
    public toaster: ToastrService,
  ) {
    this.maxDate = new Date();
    this.addNewGroup(true, 0);
    this.selectedValues = [];
  }

  addNewGroup(item: boolean, i: number) {
    if (item == true && i == 0) {
      this.toolGroups.push({
        tools: [],
        stepIds: [],
        sensors: [],
        recipes: [], // Add recipes array
      });
      this.isUC2FDGenerateButton = false;
      // Add control flags for showing input fields for recipes
      this.showAddToolInput.push(false);
      this.showAddStepIdInput.push(false);
      this.showAddSensorInput.push(false);
      this.showAddRecipeInput.push(false); // Add recipe input control flag
    } else {
      if (
        this.uC2FdselectedRecipeNames[i] &&
        this.uC2SelectedToolIds[i] &&
        this.uC2SelectedStepIds[i] &&
        this.uC2FdTraceAggrSelectedSensors[i]
      ) {
        this.toolGroups.push({
          tools: [],
          stepIds: [],
          sensors: [],
          recipes: [], // Add recipes array
        });
        this.isUC2FDGenerateButton = false;
        this.showAddToolInput.push(false);
        this.showAddStepIdInput.push(false);
        this.showAddSensorInput.push(false);
        this.showAddRecipeInput.push(false);
        this.isUC2TraceToolsIdsValue = false;
        this.isUC2TraceStepIdsValue = false;
        this.isUC2TraceSensorsValue = false;
      } else {
        this.toaster.info('Please Select all the DropDowns');
      }
    }
  }

  // Remove a group
  removeGroup(index: number) {
    if (this.toolGroups.length > 1) {
      this.toolGroups.splice(index, 1);
      this.showAddToolInput.splice(index, 1);
      this.showAddStepIdInput.splice(index, 1);
      this.showAddSensorInput.splice(index, 1);
      this.showAddRecipeInput.splice(index, 1);

      if (this.uC2SelectedToolIds && this.uC2SelectedToolIds.length >= index) {
        this.uC2SelectedToolIds.splice(index, 1);
      }
      if (this.uC2SelectedStepIds && this.uC2SelectedStepIds.length >= index) {
        this.uC2SelectedStepIds.splice(index, 1);
      }
      if (
        this.uC2FdTraceAggrSelectedSensors &&
        this.uC2FdTraceAggrSelectedSensors.length >= index
      ) {
        this.uC2FdTraceAggrSelectedSensors.splice(index, 1);
      }
      if (
        this.uC2FdselectedRecipeNames &&
        this.uC2FdselectedRecipeNames.length >= index
      ) {
        // Remove recipes
        this.uC2FdselectedRecipeNames.splice(index, 1);
      }
      this.updateUC2FDTraceConfigSelectedValues();
      this.isUC2FDGenerateButton = false;
    }
  }

  updateUC2FDTraceConfigSelectedValues() {
    this.config.uC2SelectedToolIds = this.uC2SelectedToolIds;
    this.config.tool_ids.selected_values = this.uC2SelectedToolIds;
    this.config.recipes.selected_values = this.uC2FdselectedRecipeNames;
    this.config.selectedRecipeNames = this.uC2FdselectedRecipeNames;
    this.config.step_ids.selected_values = this.uC2SelectedStepIds;
    this.config.sensors.selected_values = this.uC2FdTraceAggrSelectedSensors;
  }

  addNewRecipe(index: number) {
    if (this.newRecipeName.trim()) {
      const newRecipe: Recipe = {
        recipe_name: this.newRecipeName.trim(),
      };

      this.toolGroups[index].recipes.push(newRecipe);
      this.filteredRecipeNames.push(newRecipe);

      this.newRecipeName = '';
      this.showAddRecipeInput[index] = false;
    }
  }

  async cancelPolling() {
    try {
      let cancelledStatus = await this.dataCatService.cancelPolling(
        this.sessionData.job_id,
      );
      if (cancelledStatus) {
        this.showPolling = false;
        this.toaster.success('Job Cancelled Successfully');
        this.resetPollingFlags();
      }
    } catch (error) {
      // Handle errors
      console.error('Error canceling polling:', error);
    }
  }

  resetSearch() {
    this.searchTravelerId = ''; // Reset the search field
    this.searchDid = '';
  }

  resetPollingFlags() {
    this.pollingPercentage = 0;
    this.pollingMsg = '';
    this.isTechPolling = false;
    this.isDidPolling = false;
    this.isTravelerIdPolling = false;
    this.isTravelerStepPolling = false;
    this.isLotIdsPolling = false;
    this.isFDContextFilterPolling = false;
    this.isWaferIdsPolling = false;
    this.isSensorPolling = false;
    this.isGeneratePolling = false;
    this.isuc2SigmaDownloadPolling = false;
    this.isuc2FDTraceDownloadPolling = false;
    this.isuc2FDGenaratePolling = false;

    this.fabLoadPercentage = 0;
    this.techLoadPercentage = 0;
    this.didLoadPercentage = 0;
    this.travelerIdLoadPercentage = 0;
    this.travelerLoadPercentage = 0;
    this.fdContexApplyFiltertLoadPercentage = 0;
    this.uc2SigmaLoadPercentage = 0;
    this.sensorLoadPercentage = 0;
    this.sensorDownloadPercentage = 0;
    this.generateLoadPercentage = 0;
  }

  // get filteredSensorDropdownList(): string[] {
  //   return this.sensorsDropdownList.filter((item: any) =>
  //     item.toLowerCase().includes(this.searchSensor.toLowerCase()),
  //   );
  // }
  get filteredFabDropdownList(): string[] {
    return this.fabDropdownList.filter((item: any) =>
      item.toLowerCase().includes(this.searchfab.toLowerCase()),
    );
  }

  get filteredTechNodeDropdownList(): string[] {
    return this.techDropdownList.filter((item: any) =>
      item.toLowerCase().includes(this.searchTechNode.toLowerCase()),
    );
  }

  get filteredDidDropdownList(): string[] {
    return this.didDropdownList.filter((item: any) =>
      item.toLowerCase().includes(this.searchDid.toLowerCase()),
    );
  }

  get filteredTravelerIdDropdownList(): string[] {
    return this.travelerIdDropdownList.filter((item: any) =>
      item.toLowerCase().includes(this.searchTravelerId.toLowerCase()),
    );
  }

  get filteredTravelerStepDropdownList(): string[] {
    return this.travelerStepDropdownList.filter((item: any) =>
      item.toLowerCase().includes(this.searchTravelerStep.toLowerCase()),
    );
  }

  // get filtereduc3SigmaMetroStepPrefixList(): string[] {
  //   if (this.uc3SigmaMetroStepPrefixList && this.uc3SigmaMetroStepPrefixList.length > 0) {
  //     return this.uc3SigmaMetroStepPrefixList.filter((item: any) =>
  //       item
  //         .toLowerCase()
  //         .includes(this.searchUc3SigmaMetroSteps.toLowerCase()),
  //     );
  //   }
  //   return [];
  // }

  get filteredUc3LotIdsList(): string[] {
    if (this.lotIdsDropdownList && this.lotIdsDropdownList.length > 0) {
      return this.lotIdsDropdownList.filter((item: any) =>
        item.toLowerCase().includes(this.searchUc3SigmaLotIds.toLowerCase()),
      );
    }
    return [];
  }
  get filteredUc3WaferIdsList(): string[] {
    if (this.waferIdsDropdownList && this.waferIdsDropdownList.length > 0) {
      return this.waferIdsDropdownList.filter((item: any) =>
        item.toLowerCase().includes(this.searchUc3SigmaWaferIds.toLowerCase()),
      );
    }
    return [];
  }

  ngOnInit(): void {
    this.uc3SigmaMetroStepPrefixObj = {
      '1210': 'SEM CD',
      '1235': 'SHAPE',
      '1250': 'WEIGHT DELTA',
      '1220': 'SCATTER',
      '1230': 'THK',
      '1200': 'REG',
      '1213': 'REG',
    };
    if (this.uc3ProbeResultPath != '') {
      this.uc3ProbePreviewButton = true;
    } else {
      this.uc3ProbePreviewButton = false;
    }
    this.sessionData = this.dataCatService.getData();
    this.highLevelDataCatalog();
    // const savedPaths = localStorage.getItem('selectedPathsByColumn');
    const savedPaths = JSON.parse(
      localStorage.getItem('selectedPathsByJobId') || '{}',
    );
    const jobId = this.sessionData.job_id;
    if (savedPaths[jobId]) {
      this.selectedPathsByColumn = savedPaths[jobId];
    } else {
      this.selectedPathsByColumn = {};
      console.log('No saved paths found for jobId:', jobId);
    }
    //this.selectedPathsByColumn = savedPaths;

    if (this.sessionData) {
      this.selectedSession = this.sessionData.name;
    }
    this.fabDropdownSettings = {
      singleSelection: true,
      idField: 'item_id',
      textField: 'item_text',
      allowSearchFilter: true,
      itemsShowLimit: 3,
    };
    this.didDropdownSettings = {
      singleSelection: true,
      allowSearchFilter: true,
      itemsShowLimit: 2,
    };
    this.sensorDropdownSettings = {
      allowSearchFilter: true,
      itemsShowLimit: 2,
    };
    this.techDropdownSettings = {
      singleSelection: true,
      allowSearchFilter: true,
      itemsShowLimit: 2,
    };
    this.travelerIdDropdownSettings = {
      singleSelection: true,
      allowSearchFilter: true,
      itemsShowLimit: 2,
    };
    this.travelerStepDropdownSettings = {
      allowSearchFilter: true,
      itemsShowLimit: 1,
    };
    this.sensorDropdownSettings = {
      singleSelection: false,
      idField: 'item_id',
      textField: 'item_text',
      allowSearchFilter: false,
      itemsShowLimit: 3,
    };
    this.columnFilterSettings = {
      singleSelection: false,
      idField: 'id',
      textField: 'item_text',
      allowSearchFilter: true,
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      enableCheckAll: true,
      itemsShowLimit: 1,
    };
    this.fetchAllResults();
    this.onFabClick();
  }

  async highLevelDataCatalog() {
    try {
      let status = await this.dataCatService.dataPullStatus(
        this.sessionData.job_id,
        this.highLevelSaveStage,
      );
      if (status.current_stage_status === 'SUCCESS') {
        this.dataCatService
          .saveHighLevelResponseResult(
            this.sessionData.job_id,
            this.highLevelSaveStage,
          )
          .subscribe((res: any) => {
            if (
              res.current_stage_inputs?.start_date &&
              res.current_stage_inputs?.end_date
            ) {
              this.startDate = this.parseDate(
                res.current_stage_inputs?.start_date,
              );
              this.endDate = this.parseDate(res.current_stage_inputs?.end_date);
              this.config['start_date'] = res.current_stage_inputs?.start_date;
              this.config['end_date'] = res.current_stage_inputs?.end_date;
            }
          });
      }
    } catch (error: any) {
      this.toaster.error('Error in fetching data');
    }
  }

  initializeFilteredList(): void {
    if (
      this.uc3SigmaMetroStepPrefixList &&
      this.uc3SigmaMetroStepPrefixList.length > 0
    ) {
      this.filtereduc3SigmaMetroStepPrefixList =
        this.uc3SigmaMetroStepPrefixList.filter((item: string) =>
          item
            .toLowerCase()
            .includes(this.searchUc3SigmaMetroSteps.toLowerCase()),
        );
      if (this.uc3SigmaMetroStepPrefixListSelected != '') {
        this.uc3SigmaMetroStepPrefixListSelected.forEach((step: string) => {
          if (!this.filtereduc3SigmaMetroStepPrefixList.includes(step)) {
            this.uc3SigmaMetroStepPrefixList = Array.from(
              new Set(
                this.cached_traveler_steps_values.map((step: any) => {
                  const prefix = step.split('-')[0]; // Extract prefix from step ID
                  const description =
                    this.uc3SigmaMetroStepPrefixObj[prefix] || 'Unknown'; // Check if prefix exists in the object
                  return `${prefix} (${description})`;
                }),
              ),
            );
            this.filtereduc3SigmaMetroStepPrefixList =
              this.uc3SigmaMetroStepPrefixList.filter((item: string) =>
                item
                  .toLowerCase()
                  .includes(this.searchUc3SigmaMetroSteps.toLowerCase()),
              );
          }
        });
      }
    } else {
      this.filtereduc3SigmaMetroStepPrefixList = [];
    }
  }

  advanceSearchModal(dropdown: string): void {
    let data: any;
    let list: any;
    if (dropdown == 'traveler_id') {
      data = this.travelerIdDropdownList;
      list = data.map((item: any) => ({
        name: item,
        selected:
          this.selectedTravelerid &&
          Array.isArray(this.selectedTravelerid) &&
          this.selectedTravelerid.indexOf(item) !== -1
            ? true
            : false,
      }));
    }
    if (dropdown == 'design_id') {
      list = this.getAdvancedSearchList(this.didDropdownList, this.selectedDid);
    }
    if (dropdown == 'tech_nodes') {
      list = this.getAdvancedSearchList(
        this.techDropdownList,
        this.selectedTech,
      );
    }
    if (dropdown == 'fab') {
      list = this.getAdvancedSearchList(this.fabDropdownList, this.selectedFab);
    }
    const dialogRef = this.dialog.open(AdvanceSearchComponent, {
      width: '90%',
      height: '90%',
      disableClose: true,
      data: { list: list, dropdown: dropdown },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result && result.dataSelected && result.dataSelected.length > 0) {
        if (result.dropdown == 'traveler_id') {
          this.selectedTravelerid = [...result.dataSelected];
          this.onTravelerIdSelect();
          this.onTravelerClick();
        }
        if (result.dropdown == 'design_id') {
          this.selectedDid = result.dataSelected[0];
          this.onDidSelect();
          this.onTravelerIdClick();
        }
        if (result.dropdown == 'tech_nodes') {
          this.selectedTech = result.dataSelected[0];
          this.onTechSelect();
          this.onDidClick();
        }
        if (result.dropdown == 'fab') {
          this.selectedFab = result.dataSelected[0];
          this.onFabSelect();
          this.onTechClick();
        }
      }
    });
  }

  advanceSearcSigmahModal(
    dropdown: string,
    selectedList: any,
    selectedPath: string | null,
  ): void {
    // Retrieve list based on the dropdown (e.g., 'run_parameters')
    let list =
      dropdown === 'run_parameters'
        ? this.getAdvancedSearchList(this.runStepGQLFileList, this.selectedFab)
        : [];

    // Set the selectedPath from the global store if available, otherwise use passed value
    const initialSelectedPath =
      this.getSelectedPathForColumn(dropdown) || selectedPath;

    // Open the dialog and pass selected path and other data
    const dialogRef = this.dialog.open(AdvanceSearchSigmaComponent, {
      width: '90%',
      height: '90%',
      disableClose: true,
      data: {
        list: list,
        dropdown: dropdown,
        path: this.responsePathRun,
        selectedList: selectedList,
        selectedPath: initialSelectedPath,
      },
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result && result.dataSelected) {
        this.setSelectedPathForColumn(dropdown, result.dataSelected);
        this.uc2SigmaSelectedData.run_parameters.selected_path =
          result.dataSelected;
        this.uc2SigmaSelectedData.run_parameters.selected_column = dropdown;
      }
    });
  }

  // Set selected_path for a specific dropdown in the global store and save to localStorage
  // setSelectedPathForColumn(dropdown: string, selectedPath: string): void {
  //     this.selectedPathsByColumn[dropdown] = selectedPath;
  //     this.sessionData.job_id
  //     localStorage.setItem('selectedPathsByColumn', JSON.stringify(this.selectedPathsByColumn));
  // }

  setSelectedPathForColumn(dropdown: string, selectedPath: string): void {
    const jobId = this.sessionData.job_id;

    // Ensure `selectedPathsByJobId` exists in localStorage or initialize it
    let selectedPathsByJobId = JSON.parse(
      localStorage.getItem('selectedPathsByJobId') || '{}',
    );

    // Initialize `selectedPathsByColumn` for the current jobId if not present
    if (!selectedPathsByJobId[jobId]) {
      selectedPathsByJobId[jobId] = {};
    }

    // Update the path for the specific dropdown under the current jobId
    selectedPathsByJobId[jobId][dropdown] = selectedPath;

    // Save updated object back to localStorage
    localStorage.setItem(
      'selectedPathsByJobId',
      JSON.stringify(selectedPathsByJobId),
    );

    // Optionally, update the component's state if needed
    this.selectedPathsByColumn = selectedPathsByJobId[jobId];
  }

  // Get the selected path for a specific dropdown
  getSelectedPathForColumn(dropdown: string): string | null {
    return this.selectedPathsByColumn[dropdown] || null;
  }

  // Use case example for getting and using selected_path
  useSelectedPathForDropdown(dropdown: string): void {
    const selectedPath = this.getSelectedPathForColumn(dropdown);
  }

  getAdvancedSearchList(data: any, selectedItem: any) {
    return data.map((item: any) => ({
      name: item,
      selected: selectedItem && selectedItem === item ? true : false,
    }));
  }

  toggleTravelerSteps() {
    if (this.isTravelerAllSelected) {
      this.selectedTravelerSteps = this.selectedTravelerSteps.concat(
        this.filteredTravelerStepDropdownList,
      );
    } else {
      this.selectedTravelerSteps = this.selectedTravelerSteps.filter(
        (step: any) => !this.filteredTravelerStepDropdownList.includes(step),
      );
    }
  }

  disableSensorDownloadButton() {
    return this.uC2FdSelectedSensors.length > 0 ? false : true;
  }

  async fetchAllResults() {
    try {
      this.fabResultFetch();
    } catch (error) {
      console.error('Error in fetching results:', error);
    }
  }

  createJob(job_id: any, type: String): void {
    this.dataCatService.createJob(this.config, job_id, type).subscribe({
      next: async (id: any) => {
        try {
          this.toaster.success('Job created successfully');
          if (type === 'facilities') {
            this.onFabClick();
          }
          if (type === 'tech_nodes') {
            this.onTechClick();
          }
          if (type === 'design_ids') {
            this.onDidClick();
          }
          if (type === 'traveler_ids') {
            this.onTravelerIdClick();
          }
          if (type === 'traveler_steps') {
            this.onTravelerClick();
          }
          if (type === 'fd_sensors') {
            this.onSensorClick();
          }
          if (type === 'fd_context') {
            this.generateData();
          }
          if (type === 'fd_trace') {
            this.downloadSensorData();
          }
          if (type === 'uc3_fd_context') {
            this.GeneteFDContext();
          }
          if (type === 'UC3_FD_CONTEXT_APPLY_FILTERS') {
            this.fdContextApplyFilter();
          }
        } catch (err: any) {
          this.toaster.error('Job failed to create');
        }
      },
      error: (err: any) => {
        this.toaster.error('Job failed to create');
        // this.navigate('tools');
      },
    });
  }

  async dataPullStatus(job_id: any, retryInterval: number = 5000) {
    try {
      const status = await this.dataCatService.dataPullStatus(job_id);
      if (status) {
        if (status.current_stage_status === 'FAILED') {
          this.toaster.error('FabList fetching failed');
        }
        if (status.current_stage_status === 'RUNNING') {
          this.toaster.info('Data pull in progress');
          setTimeout(
            () => this.dataPullStatus(job_id, retryInterval),
            retryInterval,
          );
        }
      }
    } catch (err: any) {
      this.toaster.error('Job status failed');
    }
  }

  navigate(pageName: string) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const projectId = selectedProjectId;
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${projectId}/data-catalog`,
    ]);
  }

  onFabSelect() {
    this.fabChanged();
  }
  onFabDeSelect() {
    this.fabChanged();
  }
  fabChanged() {
    this.selectedTech = '';
    this.techDropdownList = [];
    this.techLoadPercentage = 0;
    this.selectedDid = '';
    this.didDropdownList = [];
    this.didLoadPercentage = 0;
    this.selectedTravelerid = '';
    this.travelerIdDropdownList = [];
    this.travelerIdLoadPercentage = 0;
    this.selectedTravelerSteps = [];
    this.travelerStepDropdownList = [];
    this.travelerLoadPercentage = 0;
    this.startDate = '';
    this.endDate = '';
    this.flag = 0;
    this.uC2FdSelectedSensors = [];
    this.sensorsDropdownList = [];
    this.isfdTracePath = false;
    this.fdTraceSensorPath = '';
  }

  onTechSelect() {
    this.techChanged();
  }
  onTechDeSelect() {
    this.techChanged();
  }
  techChanged() {
    this.selectedDid = '';
    this.didDropdownList = [];
    this.didLoadPercentage = 0;
    this.selectedTravelerid = '';
    this.travelerIdDropdownList = [];
    this.travelerIdLoadPercentage = 0;
    this.selectedTravelerSteps = [];
    this.travelerStepDropdownList = [];
    this.travelerLoadPercentage = 0;
    this.startDate = '';
    this.endDate = '';
    this.flag = 0;
    this.uC2FdSelectedSensors = [];
    this.sensorsDropdownList = [];
    this.isfdTracePath = false;
    this.fdTraceSensorPath = '';
  }

  onDidSelect() {
    this.didChanged();
  }
  onDidDeSelect() {
    this.didChanged();
  }

  didChanged() {
    this.selectedTravelerid = '';
    this.travelerIdDropdownList = [];
    this.travelerIdLoadPercentage = 0;
    this.selectedTravelerSteps = [];
    this.travelerStepDropdownList = [];
    this.travelerLoadPercentage = 0;
    this.startDate = '';
    this.endDate = '';
    this.flag = 0;
    this.uC2FdSelectedSensors = [];
    this.sensorsDropdownList = [];
    this.isfdTracePath = false;
    this.fdTraceSensorPath = '';
  }
  // onSelectionChange(matSelect: MatSelect) {
  //   // Prevent the dropdown from closing on option select
  //   matSelect.open();
  //   // setTimeout(() => {
  //   //   matSelect.open(); // Reopen the dropdown
  //   // });
  // }

  onTravelerIdSelect() {
    this.travelerIdChanged();
  }
  onTravelerIdDeSelect() {
    this.travelerIdChanged();
  }

  travelerIdChanged() {
    this.selectedTravelerSteps = [];
    this.travelerStepDropdownList = [];
    this.travelerLoadPercentage = 0;
    this.flag = 0;
    this.uC2FdSelectedSensors = [];
    this.sensorsDropdownList = [];
    this.isfdTracePath = false;
    this.fdTraceSensorPath = '';
  }

  onTravelerSelect() {
    this.startDate = '';
    this.endDate = '';
    this.generateEnable();
    this.uC2FdSelectedSensors = [];
    this.sensorsDropdownList = [];
    this.isfdTracePath = false;
    this.fdTraceSensorPath = '';
    this.flag = 0;
  }

  onTravelerDeSelect() {
    this.generateEnable();
  }

  startChange(event: any) {
    this.clearSensors();
  }
  async endChange(event: any) {
    this.clearSensors();
    this.config['start_date'] = this.datePipe.transform(
      this.startDate,
      'yyyy-MM-dd',
    );
    this.config['end_date'] = this.datePipe.transform(
      this.endDate,
      'yyyy-MM-dd',
    );
    this.flag = 0;
    if (this.endDate) {
      this.isdcHighLevelSubmit = false;
    } else {
      this.isdcHighLevelSubmit = true;
    }
  }

  clearSensors() {
    this.uC2FdSelectedSensors = [];
    this.sensorsDropdownList = [];
    this.isfdTracePath = false;
    this.fdTraceSensorPath = '';
    this.flag = 0;
  }

  parseDate(dateStr: any): Date {
    const dateParts = dateStr.split('-');
    const year = parseInt(dateParts[0], 10);
    const month = parseInt(dateParts[1], 10) - 1;
    const day = parseInt(dateParts[2], 10);

    return new Date(year, month, day);
  }

  onSelectAll(column: any) {
    column.selectedItems = [...column.colValues];
    this.onColfilterSelect(column);
  }
  onDeSelectAll(column: any) {
    column.selectedItems = [];
    this.onColfilterSelect(column);
  }

  async onSensorClick() {
    if (!this.isSensorPolling && this.sensorsDropdownList.length == 0) {
      const status = await this.dataCatService.dataPullStatus(
        this.sessionData.job_id,
      );
      this.config['fd_contexts']['file_path'] = this.downloadPath;
      this.config['fd_contexts']['selected_values'] = [...this.clickedRows];
      if (status.fd_data_pull_job_status !== 'RUNNING') {
        this.createJob(this.sessionData.job_id, 'fd_sensors');
        this.isSensorPolling = true;
        setTimeout(() => {
          this.sensorStatus();
        }, 2000);
      }
    }
  }

  async sensorStatus() {
    const status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.sensorLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.sensorLoadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.sensorLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
        setTimeout(() => {
          this.sensorStatus();
        }, 2000);
      }
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.sensorFetchResult();
    }
  }

  async sensorFetchResult() {
    const sensorList = await this.dataCatService.sensorsPullResult(
      this.config,
      this.sessionData.job_id,
      this.fdSensorStage,
    );
    if (sensorList) {
      this.sensorQueryFilePath =
        sensorList?.current_stage_results?.sensors?.file_path;
      let pageDetails = {
        pageIndex: 0,
        pageSize: 10,
      };
      let list: any =
        sensorList?.current_stage_inputs?.fd_contexts?.selected_values;
      if (list.length > 0 && this.sensorsDropdownList.length == 0) {
        this.clickedRows.clear();
        list.forEach((num: any) => this.clickedRows.add(num));
        this.disableSensorDropdown = false;
        this.sensorFetchResult();
      }
      this.config['sensors']['file_path'] = this.sensorQueryFilePath;
      this.showPolling = false;
      const sensorsQueryCheck = await this.dataCatService
        .getQueryUniques(this.sensorQueryFilePath, 'sensors', pageDetails)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              this.sensorsDropdownList = res.body['uniques'];
              this.isSensorPolling = false;
            }
            let status = await this.dataCatService.dataPullStatus(
              this.sessionData.job_id,
            );
            if (
              status.current_stage === this.fdTraceStage &&
              status.current_stage_status === 'SUCCESS'
            ) {
              this.sensorDownloadFetchResult();
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
            // this.navigate('tools');
          },
        });
    }
  }

  onSensorSelect() {
    this.sensorGenerateToggle();
  }

  onSensorDeSelect(event: any) {
    this.sensorGenerateToggle();
  }

  sensorGenerateToggle() {
    if (this.uC2FdSelectedSensors.length === 0) {
      this.disableSensorDownload = true;
    } else {
      this.disableSensorDownload = false;
    }
  }

  generateEnable() {
    if (this.selectedTravelerSteps.length === 0 && this.endDate) {
      this.disableGenerate = true;
    } else {
      this.disableGenerate = false;
    }
  }

  async downloadSensorData() {
    if (!this.isSensorDataPolling) {
      // this.clearWhenSensorsGenerateClicked();
      this.disableSensorDownload = false;
      const status = await this.dataCatService.dataPullStatus(
        this.sessionData.job_id,
      );
      if (status.fd_data_pull_job_status !== 'RUNNING') {
        this.config['sensors']['selected_values'] = [
          ...this.uC2FdSelectedSensors,
        ];
        if (!this.config['fd_contexts']['selected_values'])
          this.config['fd_contexts']['selected_values'] = [...this.clickedRows];
        this.createJob(this.sessionData.job_id, 'fd_trace');
        this.isSensorDataPolling = true;
        setTimeout(() => {
          this.sensorDownloadStatus();
        }, 2000);
      }
    } else {
      this.disableSensorDownload = true;
    }
  }

  async sensorDownloadStatus() {
    const status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.sensorDownloadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.sensorDownloadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.sensorDownloadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
        setTimeout(() => {
          this.sensorDownloadStatus();
        }, 2000);
      }
    }

    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.sensorDownloadFetchResult();
    }
    if (status.current_stage_status === 'FAILED') {
      this.isSensorDataPolling = false;
    }
  }

  async sensorDownloadFetchResult() {
    const fdTraceResult = await this.dataCatService.fdTracePullResult(
      this.config,
      this.sessionData.job_id,
      this.fdTraceStage,
    );
    if (fdTraceResult) {
      this.fdTraceSensorPath =
        fdTraceResult?.current_stage_results?.fd_trace?.file_path;
      let sensorInputs: any =
        fdTraceResult?.current_stage_inputs?.sensors?.selected_values;
      if (sensorInputs && Array.isArray(sensorInputs)) {
        this.uC2FdSelectedSensors = sensorInputs;
      }
      if (this.fdTraceSensorPath) {
        this.config['fd_trace']['file_path'] = this.fdTraceSensorPath;
        this.isfdTracePath = true;
        this.showPolling = false;
        this.isSensorDataPolling = false;
      }
    }
  }

  clearWhenSensorsGenerateClicked() {
    this.isfdTracePath = false;
    this.fdTraceSensorPath = '';
    this.flag = 0;
  }

  async generateData() {
    this.isLoading = true;
    this.clearWhenGenerateClicked();
    if (!this.isGeneratePolling) {
      this.flag = 0;
      this.config['traveler_steps']['selected_values'] =
        this.selectedTravelerSteps.map(String);
      let status = await this.dataCatService.dataPullStatus(
        this.sessionData.job_id,
      );
      if (status.fd_data_pull_job_status !== 'RUNNING') {
        this.createJob(this.sessionData.job_id, 'fd_context');
        this.isGeneratePolling = true;
        setTimeout(() => {
          this.generateDataStatus();
        }, 2000);
      }
    }
  }

  async generateDataStatus() {
    let status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.generateLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.generateLoadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.generateLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
        setTimeout(() => {
          this.generateDataStatus();
        }, 2000);
      }
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.generateDataResultFetch();
    }
    if (status.current_stage_status === 'FAILED') {
      this.isGeneratePolling = false;
      this.isLoading = false;
    }
  }

  async generateDataResultFetch() {
    this.isDataAvailable = false;
    const generateData = await this.dataCatService.downloadDataResult(
      this.config,
      this.sessionData.job_id,
      this.fdContextStage,
    );
    if (generateData) {
      this.downloadPath =
        generateData?.current_stage_results?.fd_contexts?.file_path;

      let pageDetails = {
        pageIndex: 0,
        pageSize: 10,
      };
      this.config['traveler_steps']['file_path'] = this.downloadPath;
      this.showPolling = false;
      this.rowsFdTable = [];
      this.dataCatService
        .getQueryResponse(this.downloadPath, {}, [], [], pageDetails)
        .subscribe({
          next: async (id: any) => {
            try {
              let result = id.body;
              this.tableSpinner = false;
              this.flag = 1;
              this.rowsFdTable = result['data'];
              this.colUnique = result['uniques'];
              this.totalCount = result['rows_count'];
              if (this.paginator) this.paginator.pageIndex = 0;
              this.createDropdowns({});
              this.tableData = new MatTableDataSource(this.rowsFdTable);
              if (this.tableData.filteredData.length == 0) {
                this.isDataAvailable = true;
              }
              this.displayedColumns = result['columns'];
              this.toaster.success('Data fetched successfully');
              this.isGeneratePolling = false;
              let generateInputs = generateData?.current_stage_inputs;
              if (generateInputs) {
                //this.startDate = generateInputs?.start_date;
                this.startDate = this.parseDate(generateInputs?.start_date);
                this.endDate = this.parseDate(generateInputs?.end_date);
                this.config['start_date'] = generateInputs?.start_date;
                this.config['end_date'] = generateInputs?.end_date;
              }
              let status = await this.dataCatService.dataPullStatus(
                this.sessionData.job_id,
              );
              if (
                (status.current_stage === this.fdSensorStage ||
                  status.current_stage === this.fdTraceStage) &&
                status.current_stage_status === 'SUCCESS'
              ) {
                this.sensorFetchResult();
              }
            } catch (err: any) {
              this.toaster.error('Data fetching failed');
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
            // this.navigate('tools');
          },
        });
      this.isLoading = false;
    }
  }

  clearWhenGenerateClicked() {
    this.uC2FdSelectedSensors = [];
    this.sensorsDropdownList = [];
    this.isfdTracePath = false;
    this.fdTraceSensorPath = '';
    this.flag = 0;
  }

  resetTable() {
    window.location.reload();
  }
  async onFabClick() {
    try {
      if (this.fabDropdownList.length === 0) {
        const status = await this.dataCatService.dataPullStatus(
          this.sessionData.job_id,
        );

        if (
          status?.job_status?.job_stage_status?.hasOwnProperty(
            'progress_percentage',
          )
        ) {
          this.fabLoadPercentage =
            status?.job_status?.job_stage_status?.progress_percentage;
          if (this.fabLoadPercentage !== 100) {
            this.showPolling = true;
            this.pollingMsg =
              status?.job_status?.job_stage_status?.progress_message;
            this.pollingPercentage = this.fabLoadPercentage;
          } else {
            this.showPolling = false;
          }
        }
        if (status.current_stage === 'IDLE') {
          this.createJob(this.sessionData.job_id, 'facilities');
        }
        if (
          status.current_stage === this.fabStage ||
          status.current_stage !== 'IDLE'
        ) {
          if (this.fabDropdownList.length === 0) {
            this.fabResultFetch();
          }
        }
        if (
          status.current_stage === this.fabStage &&
          status.fd_data_pull_job_status === 'RUNNING'
        ) {
          this.callFabAgain();
        }
      } else {
        this.showPolling = false;
      }
    } catch (err: any) {
      this.toaster.error('Job failed to create');
    }
  }

  async fabResultFetch() {
    const fabList = await this.dataCatService.fabPullResult(
      this.sessionData.job_id,
      this.fabStage,
    );
    if (fabList) {
      this.fabQueryFilePath =
        fabList?.current_stage_results?.facilities?.file_path;
      let pageDetails = {
        pageIndex: 0,
        pageSize: 10,
      };
      this.config['facilities']['file_path'] = this.fabQueryFilePath;
      this.showPolling = false;
      const fabQueryCheck = await this.dataCatService
        .getQueryUniques(this.fabQueryFilePath, 'facilities', pageDetails)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              this.fabDropdownList = res.body['uniques'];
              let fabInputs: any =
                fabList?.current_stage_results?.facilities?.selected_values;
              if (fabInputs) {
                this.selectedFab =
                  fabInputs && Array.isArray(fabInputs) && fabInputs.length > 0
                    ? fabInputs[0]
                    : '';
                this.config['facilities']['selected_values'] = fabInputs;
                if (this.selectedFab != '') {
                  this.techResultFetch();
                }
              }
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
            // this.navigate('tools');
          },
        });
    }
  }

  async onTechClick() {
    try {
      if (!this.isTechPolling && this.techDropdownList.length == 0) {
        if (this.selectedFab) {
          // this.config['facilities']['selected_values'] =
          //   this.selectedFab.map(String);
          this.config['facilities']['selected_values'] = [this.selectedFab].map(
            String,
          );
        }
        let status = await this.dataCatService.dataPullStatus(
          this.sessionData.job_id,
          this.techStage,
        );
        if (status.fd_data_pull_job_status !== 'RUNNING') {
          this.createJob(this.sessionData.job_id, 'tech_nodes');
          this.isTechPolling = true;
          setTimeout(() => {
            this.techStatus();
          }, 2000);
        }
      }
    } catch (err: any) {
      this.toaster.error('Job failed to create');
    }
  }

  async getRecipesOnGenerate(path: any) {
    try {
      const response = await this.dataCatService.generateRecipes(
        this.sessionData.job_id,
        this.config,
        '',
      );
      if (response.body) {
        this.recipes = response.body;
        this.filteredRecipeNames = this.recipes;
        // this.updateSelectAllState(); // Update the select all state
        this.onGeneratePathClick();
        this.isLoading = false;
      } else {
        this.recipes = [];
        this.filteredRecipeNames = [];
      }
    } catch (error) {
      console.error('Error fetching tools:', error);
      this.recipes = [];
      this.filteredRecipeNames = [];
    }
  }

  async onGenerateClick(event: MouseEvent) {
    this.isLoading = true;
    this.isGenerating = true;
    event.stopPropagation(); // Prevent the accordion from expanding/collapsing
    await this.getRecipesOnGenerate('');
  }

  async onGeneratePathClick() {
    this.isLoading = true;
    this.isGenerating = true;

    try {
      const response = await this.dataCatService.onGeneratePathClick(
        this.sessionData.job_id,
        this.config,
      );

      if (response.body) {
        const { recipes, tool_ids, step_ids, sensors } = response.body;

        // Initialize objects if undefined
        this.config.recipes = this.config.recipes || {};
        this.config.tool_ids = this.config.tool_ids || {};
        this.config.step_ids = this.config.step_ids || {};
        this.config.sensors = this.config.sensors || {};

        // Set the file paths
        if (recipes?.file_path) {
          this.config.recipes.file_path = recipes.file_path;
        }

        if (tool_ids?.file_path) {
          this.config.tool_ids.file_path = tool_ids.file_path;
        }

        if (step_ids?.file_path) {
          this.config.step_ids.file_path = step_ids.file_path;
        }

        if (sensors?.file_path) {
          this.config.sensors.file_path = sensors.file_path;
        }
      } else {
        this.recipes = [];
        this.filteredRecipeNames = [];
      }
    } catch (error) {
      console.error('Error fetching tools:', error);
      this.recipes = [];
      this.filteredRecipeNames = [];
    } finally {
      this.isLoading = false;
      this.isGenerating = false;
    }
  }

  // toggleSelectAll(matSelectTool: MatSelect) {
  //   if (this.isSelectAll) {
  //     // Deselect all options
  //     this.uC2SelectedToolIds = [];
  //     matSelectTool.options.forEach((option: MatOption) => option.deselect());
  //   }
  //   this.updateSelectAllState();
  // }

  updateSelectAllState(index: number) {
    this.isUC2ToolNameSelectAll[index] =
      this.uC2SelectedToolIds && this.uC2SelectedToolIds[index]
        ? this.uC2SelectedToolIds[index].length ===
          this.filteredTools[index].length
        : false;
    // this.isUC2ToolNameSelectAll[index] = this.uC2SelectedToolIds[index].length === this.filteredTools[index].length;
  }

  toggleSelectAll(matSelectTool: MatSelect, index: number) {
    if (this.isUC2ToolNameSelectAll[index]) {
      this.uC2SelectedToolIds[index] = this.filteredTools[index].map(
        (tool: any) => tool.TOOL_ID,
      );
    } else {
      this.uC2SelectedToolIds[index] = [];
    }
    this.updateSelectAllState(index);
  }

  // updateSelectAllState() {
  //   const allSelected = this.filteredTools.every(tool =>
  //     this.uC2SelectedToolIds.includes(tool.TOOL_NAME)
  //   );

  //   this.isSelectAll = allSelected;
  // }

  onUC2ToolNameSelectionChange(uC2SelectedToolIds: string[], index: number) {
    this.config.tool_ids.selected_values = this.uC2SelectedToolIds;
    // this.uC2SelectedToolIds[index] = Array.from(
    //   new Set([...this.uC2SelectedToolIds[index]]),
    // );

    this.isUC2ToolNameSelectAll[index] =
      this.uC2SelectedToolIds[index].length === this.filteredTools.length;
    this.updateSelectAllState(index);
    this.updateConfigWithSelectedTools();
  }

  updateConfigWithSelectedTools() {
    this.config.uC2SelectedToolIds = this.uC2SelectedToolIds;
  }

  async techStatus() {
    let status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
      this.techStage,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.techLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.techLoadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.techLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
      }
      setTimeout(() => {
        this.techStatus();
      }, 5000);
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.techResultFetch();
    }
  }

  async techResultFetch() {
    const techList = await this.dataCatService.techPullResult(
      this.config,
      this.sessionData.job_id,
      this.techStage,
    );
    if (techList) {
      this.techQueryFilePath =
        techList?.current_stage_results?.tech_nodes?.file_path;
      let pageDetails = {
        pageIndex: 0,
        pageSize: 10,
      };
      this.config['tech_nodes']['file_path'] = this.techQueryFilePath;
      this.showPolling = false;
      const techQueryCheck = await this.dataCatService
        .getQueryUniques(this.techQueryFilePath, 'tech_nodes', pageDetails)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              this.techDropdownList = res.body['uniques'];
              let techInputs: any =
                techList?.current_stage_results?.tech_nodes?.selected_values;
              if (techInputs) {
                this.selectedTech =
                  techInputs &&
                  Array.isArray(techInputs) &&
                  techInputs.length > 0
                    ? techInputs[0]
                    : '';
                this.config['tech_nodes']['selected_values'] = techInputs;
                if (this.selectedTech != '') {
                  this.didResultFetch();
                }
              }
            }
            this.isTechPolling = false;
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
            // this.navigate('tools');
          },
        });
    }
  }
  async onDidClick() {
    try {
      if (!this.isDidPolling && this.didDropdownList.length == 0) {
        if (this.selectedTech) {
          // this.config['tech_nodes']['selected_values'] =
          //   this.selectedTech.map(String);
          this.config['tech_nodes']['selected_values'] = [
            this.selectedTech,
          ].map(String);
        }
        let status = await this.dataCatService.dataPullStatus(
          this.sessionData.job_id,
          this.didStage,
        );

        if (status.fd_data_pull_job_status !== 'RUNNING') {
          this.createJob(this.sessionData.job_id, 'design_ids');
          this.isDidPolling = true;
          setTimeout(() => {
            this.didStatus();
          }, 2000);
        }
      }
    } catch (err: any) {
      this.toaster.error('Job failed to create');
    }
  }

  async didStatus() {
    let status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
      this.didStage,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.didLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.didLoadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.didLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
      }
      setTimeout(() => {
        this.didStatus();
      }, 5000);
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.didResultFetch();
    }
  }

  async didResultFetch() {
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    const didList = await this.dataCatService.didPullResult(
      this.config,
      this.sessionData.job_id,
      this.didStage,
    );
    if (didList) {
      this.didQueryFilePath =
        didList?.current_stage_results?.design_ids?.file_path;
      this.config['design_ids']['file_path'] = this.didQueryFilePath;
      this.showPolling = false;
      const didQueryCheck = await this.dataCatService
        .getQueryUniques(this.didQueryFilePath, 'design_ids', pageDetails)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              this.didDropdownList = res.body['uniques'];
              if (this.didDropdownList.length > 0) {
                let didInputs: any =
                  didList?.current_stage_results?.design_ids?.selected_values;
                if (didInputs) {
                  this.selectedDid =
                    didInputs &&
                    Array.isArray(didInputs) &&
                    didInputs.length > 0
                      ? didInputs[0]
                      : '';
                  this.config['design_ids']['selected_values'] = didInputs;
                  if (this.selectedDid != '') {
                    this.travelerIdResultFetch();
                  }
                }
              }
            }
            this.isDidPolling = false;
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
          },
        });
    }
  }
  async onTravelerIdClick() {
    try {
      if (
        !this.isTravelerIdPolling &&
        this.travelerIdDropdownList.length == 0
      ) {
        if (this.selectedDid) {
          this.config['design_ids']['selected_values'] = [this.selectedDid].map(
            String,
          );
          // this.config['design_ids']['selected_values'] = this.selectedDid.map(String);
        }
        let status = await this.dataCatService.dataPullStatus(
          this.sessionData.job_id,
          this.travelerIdStage,
        );
        if (status.fd_data_pull_job_status !== 'RUNNING') {
          this.createJob(this.sessionData.job_id, 'traveler_ids');
          this.isTravelerIdPolling = true;
          setTimeout(() => {
            this.travelerIdStatus();
          }, 2000);
        }
      }
    } catch (err: any) {
      this.toaster.error('Job failed to create');
    }
  }

  async travelerIdStatus() {
    let status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
      this.travelerIdStage,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.travelerIdLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.travelerIdLoadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.travelerIdLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
      }
      setTimeout(() => {
        this.travelerIdStatus();
      }, 5000);
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.travelerIdResultFetch();
    }
  }

  async travelerIdResultFetch() {
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    const travelerIdList = await this.dataCatService.travelerIdPullResult(
      this.config,
      this.sessionData.job_id,
      this.travelerIdStage,
    );
    if (travelerIdList) {
      this.travelerIdQueryFilePath =
        travelerIdList?.current_stage_results?.traveler_ids?.file_path;
      this.config['traveler_ids']['file_path'] = this.travelerIdQueryFilePath;
      this.showPolling = false;
      const travelerIdQueryCheck = await this.dataCatService
        .getQueryUniques(
          this.travelerIdQueryFilePath,
          'traveler_ids',
          pageDetails,
        )
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              this.travelerIdDropdownList = res.body['uniques'];
              let travelerIdsInputs: any =
                travelerIdList?.current_stage_results?.traveler_ids
                  ?.selected_values;
              if (travelerIdsInputs) {
                this.selectedTravelerid =
                  travelerIdsInputs &&
                  Array.isArray(travelerIdsInputs) &&
                  travelerIdsInputs.length > 0
                    ? travelerIdsInputs
                    : '';
                this.config['traveler_ids']['selected_values'] =
                  travelerIdsInputs;

                if (this.selectedTravelerid != '') {
                  this.travelerResultFetch();
                }
              }
              this.isTravelerIdPolling = false;
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
          },
        });
    }
  }

  async onTravelerClick() {
    try {
      if (this.startDate && this.endDate) {
        this.isdcHighLevelSubmit = false;
      }
      if (!this.isTravelerStepPolling) {
        if (this.selectedTravelerid) {
          // this.selectedTravelerid.map((ids: any)=>{
          //   this.config['traveler_ids']['selected_values'] = ids;
          // })
          this.config['traveler_ids']['selected_values'] = [
            ...this.selectedTravelerid,
          ];
          // this.config['traveler_ids']['selected_values'] = [
          //   this.selectedTravelerid,
          // ].map(String);
        }

        let status = await this.dataCatService.dataPullStatus(
          this.sessionData.job_id,
        );

        this.setTravelerStepId = 'travelerid';

        if (status.fd_data_pull_job_status !== 'RUNNING') {
          this.createJob(this.sessionData.job_id, 'traveler_steps');
          this.isTravelerStepPolling = true;
          setTimeout(() => {
            this.travelerStatus();
          }, 2000);
        }
      }
    } catch (err: any) {
      this.toaster.error('Job failed to create');
    }
  }

  async travelerStatus() {
    let status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.travelerLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.travelerLoadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.travelerLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
      }
      setTimeout(() => {
        this.travelerStatus();
      }, 5000);
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.travelerResultFetch();
    }
  }

  async travelerResultFetch() {
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    const travelerStepList = await this.dataCatService.travelerPullResult(
      this.config,
      this.sessionData.job_id,
      this.travelerStepStage,
    );
    if (travelerStepList) {
      this.travelerQueryFilePath =
        travelerStepList?.current_stage_results?.traveler_steps?.file_path;
      this.baselineTravelerId =
        travelerStepList?.current_stage_results?.baseline_line_traveler_id;
      this.config['traveler_steps']['file_path'] = this.travelerQueryFilePath;
      this.showPolling = false;
      let travelerRes = await this.dataCatService.travelerStepsResponse(
        this.travelerQueryFilePath,
      );
      if (travelerRes) {
        try {
          this.travelerStepDropdownList = travelerRes;
          let status = await this.dataCatService.dataPullStatus(
            this.sessionData.job_id,
            this.highLevelSaveStage,
          );
          if (
            // status.fd_data_pull_job_status === 'IDLE' &&
            status.current_stage_status === 'SUCCESS'
          ) {
            this.dataCatService
              .saveHighLevelResponseResult(
                this.sessionData.job_id,
                this.highLevelSaveStage,
              )
              .subscribe((res: any) => {
                if (res.current_stage_inputs?.traveler_steps?.selected_values) {
                  this.selectedTravelerSteps =
                    res.current_stage_inputs?.traveler_steps?.selected_values;
                  this.config['traveler_steps']['selected_values'] =
                    this.selectedTravelerSteps;
                }
                if (
                  res.current_stage_inputs?.start_date &&
                  res.current_stage_inputs?.end_date
                ) {
                  this.startDate = this.parseDate(
                    res.current_stage_inputs?.start_date,
                  );
                  this.endDate = this.parseDate(
                    res.current_stage_inputs?.end_date,
                  );
                  this.config['start_date'] =
                    res.current_stage_inputs?.start_date;
                  this.config['end_date'] = res.current_stage_inputs?.end_date;
                }
                this.isTravelerStepPolling = false;
              });
          }
        } catch (error: any) {
          this.toaster.error('Error in fetching data');
        }
      }
    }
  }

  callFabAgain() {
    setTimeout(() => {
      this.onFabClick();
    }, 5000);
  }

  //table
  updateFilter() {
    this.filter = {};
    for (let i in this.colWiseValues) {
      let col = this.colWiseValues[i];
      if (col['selectedItems'].length > 0) {
        let tmp = [];
        let selectedItems = col['selectedItems'];
        for (let val in selectedItems) {
          tmp.push(selectedItems[val]);
        }
        this.filter[col['colName']] = tmp;
      }
    }
  }
  getFilteredOptions(column: any): any[] {
    return column['colValues'] || [];
  }

  getAllSelected(column: any): boolean {
    const options = column['colValues'];
    const selectedItems = this.selectedItemsMap[column['colName']] || [];
    return options.every((option: any) => selectedItems.includes(option));
  }

  // toggleSelectAll(column: any, isChecked: boolean) {
  //   const options = column['colValues'];
  //   this.selectedItemsMap[column['colName']] = isChecked ? options : [];
  //   this.selectAllState[column['colName']] = isChecked;
  // }
  tableDropdownSubmit(column: any) {
    const columnName = column['colName'];
    const selectedOptions = this.selectedItemsMap[columnName] || [];
    const selectAllClicked = this.selectAllState[columnName];
    if (column) {
      column['selectedItems'] = this.selectedItemsMap[columnName];
      let index = this.colWiseValues.findIndex(
        (item: any) => item.colName === column.colName,
      );
      if (index !== -1) {
        this.colWiseValues[index] = column;
      }
      this.onColfilterSelect(column);
    }
  }

  onColfilterSelect(column: any) {
    this.tableDataLoading = true;
    this.flag = 0;
    this.tableSpinner = true;
    let index = this.colWiseValues.findIndex(
      (item: any) => item.colName === column.colName,
    );
    if (index !== -1) {
      this.colWiseValues[index] = column;
    }
    this.updateFilter();
    this.filterData(column);
  }

  async filterEndChange(event: any) {
    this.filterStartDate = this.datePipe.transform(
      this.filterStartDate,
      'yyyy-MM-dd',
    );
    this.filterEndDate = this.datePipe.transform(
      this.filterEndDate,
      'yyyy-MM-dd',
    );
    let column = event;
    if (this.filterEndDate) {
      column['colValues'] = [
        { id: 0, item_text: this.filterStartDate },
        { id: 1, item_text: this.filterEndDate },
      ];
      column['selectedItems'] = column['colValues'];
      this.onColfilterSelect(column);
    }
  }

  createDropdowns(columnForFilter: any) {
    let tempColValues: Array<Record<string, any>> = [];
    for (let i in this.colUnique) {
      let colDict: Record<string, any> = {};
      colDict['colValues'] = [];

      if (columnForFilter.colName && columnForFilter.colName == i) {
        colDict['colValues'] = columnForFilter.colValues;
      } else {
        let col = this.colUnique[i];
        for (let j in col) {
          let colValue: Record<string, any> = {};
          colValue['id'] = j;
          colValue['item_text'] = col[j];

          colDict['colValues'].push(colValue);
        }
      }
      colDict['colName'] = i;

      if (this.filter[i] && this.filter[i].length > 0) {
        colDict['selectedItems'] = [];
        let selectedItem: Record<string, any> = {};
        let colVals = this.filter[i];
        for (let val in colVals) {
          selectedItem = {};
          selectedItem['id'] = colVals[val]['id'];
          selectedItem['item_text'] = colVals[val]['item_text'];
          colDict['selectedItems'].push(selectedItem);
        }
      } else {
        colDict['selectedItems'] = [];
      }
      tempColValues.push(colDict);
    }
    this.flag = 0;
    this.isLoading = true;
    setTimeout(() => {
      this.colWiseValues = new Array<Record<string, any>>();
      this.colWiseValues = tempColValues;
      for (let i = 0; i < this.colWiseValues.length; i++) {
        if (
          this.colWiseValues[i]['colName'] !== 'index' &&
          this.colWiseValues[i]['selectedItems']
        ) {
          for (let j = 0; j < this.colWiseValues[i]['colValues'].length; j++) {
            for (
              let k = 0;
              k < this.colWiseValues[i]['selectedItems'].length;
              k++
            ) {
              if (
                this.colWiseValues[i]['selectedItems'][k]?.item_text &&
                this.colWiseValues[i]['selectedItems'][k]['item_text'] ===
                  this.colWiseValues[i]['colValues'][j]['item_text']
              ) {
                this.colWiseValues[i]['selectedItems'][k]['id'] =
                  this.colWiseValues[i]['colValues'][j]['id']; // Update id
              }
            }
          }
        }
      }
      this.flag = 1;
      this.isLoading = false;
    });
  }

  filterData(column: any) {
    let filteredData: any = {};
    for (let key in this.filter) {
      filteredData[key] = {
        operation: key === 'START_DATE' ? 'BW' : 'EQ',
        value: this.filter[key].map((item: any) => item.item_text || item),
      };
    }
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    this.flag = 1;
    this.dataCatService
      .getQueryResponse(this.downloadPath, filteredData, [], [], pageDetails)
      .subscribe(async (result: any) => {
        let res = result?.body;
        if (res['data']) {
          this.rowsFdTable = res['data'];
          this.colUnique = res['uniques'];
          this.tableData = new MatTableDataSource(res['data']);
          this.displayedColumns = res['columns'];
          this.totalCount = res['rows_count'];
          await this.createDropdowns(column);
          this.tableDataLoading = false;
        }
      });
  }

  onPageChange(event: any) {
    let pageDetails = event;
    let filteredData: any = {};
    for (let key in this.filter) {
      filteredData[key] = {
        operation: key === 'START_DATE' ? 'BW' : 'EQ',
        value: this.filter[key].map((item: any) => item.item_text || item),
      };
    }
    this.dataCatService
      .getQueryResponse(this.downloadPath, filteredData, [], [], pageDetails)
      .subscribe((downloadList: any) => {
        let result = downloadList.body;
        // this.tableSpinner = false;
        this.rowsFdTable = result['data'];
        this.tableData = new MatTableDataSource(this.rowsFdTable);
        this.displayedColumns = result['columns'];
        this.totalCount = result['rows_count'];
        // this.setTableData(result);
      });
  }

  setTableData(result: any) {
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    this.tableData = new MatTableDataSource(this.rowsFdTable);
    this.displayedColumns = result['columns'];
    let uniquesList: { [key: string]: any[] } = {};
    let observables = result['columns'].map((e: any) =>
      this.dataCatService
        .getQueryUniques(this.downloadPath, e, pageDetails)
        .pipe(
          map((res: any) => ({ key: e, value: res.body.uniques })), // Map each result to its key and value
        ),
    );

    // Wait for all observables to complete
    forkJoin(observables).subscribe((results: any) => {
      results.forEach((result: any) => {
        uniquesList[result.key] = result.value;
      });

      this.colUnique = result['unique'];
      this.totalCount = result['rows_count'];
      if (this.paginator) this.paginator.pageIndex = 0;
      this.createDropdowns({});
    });
  }

  onRowClick(row: any) {
    this.isSensorPolling = false;
    this.sensorsDropdownList = [];
    if (this.clickedRows.has(row['index'])) {
      this.clickedRows.delete(row['index']);
    } else {
      this.clickedRows.add(row['index']);
    }
    this.dataCatService.runs = this.clickedRows;
    if (this.clickedRows.size > 0) {
      this.disableSensorDropdown = false;
      this.isSensorPolling = false;
      // this.setSensorResult();
    } else {
      this.disableSensorDropdown = true;
    }
  }

  setSensorResult() {
    // this.isSensorAllSelected = false;
    this.sensorsDropdownList = [];
    this.uC2FdSelectedSensors = [];
  }

  unselectAllRows() {
    this.clickedRows.clear();
    this.setSensorResult();
    this.disableSensorDropdown = true;
  }

  displayClear() {
    return this.clickedRows.size != 0 && this.clickedRows.size < this.totalCount
      ? true
      : false;
  }

  selectAllRows() {
    if (this.colUnique['index'].length == this.clickedRows.size) {
      this.clickedRows.clear();
      this.setSensorResult();
      this.disableSensorDropdown = true;
    } else {
      this.colUnique['index'].forEach((run: any) => {
        this.clickedRows.add(run);
      });
      this.disableSensorDropdown = false;
    }
  }

  async lotIdsDataPullStatus() {
    let status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      this.isLotIdsPolling = true;
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.lotIdsLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage; //travelerLoadPercentage =
        if (this.lotIdsLoadPercentage !== 100) {
          this.showPolling = true;

          this.pollingPercentage = this.lotIdsLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
          this.isLotIdsPolling = false;
        }
        this.isUC3SigmaLotIdsBeforeApi = false;
      }
      setTimeout(() => {
        this.lotIdsDataPullStatus();
      }, 2000);
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.lotResultFetch(true);
    }
  }

  // calllotIdsDataPullStatus() {
  //   setTimeout(() => {
  //     this.lotIdsDataPullStatus();
  //   }, 5000);
  // }

  async lotResultFetch(
    openSelectionComponentAfterLoadingLotIds: boolean = false,
  ) {
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    let lotIdList = await this.dataCatService.getLotsIdsStatus(
      this.sessionData.job_id,
      this.fdLotStage,
    );
    this.showPolling = false;

    if (lotIdList) {
      this.lotIdsQueryFilePath =
        lotIdList.current_stage_results?.lot_ids?.file_path;
      //this.config['traveler_ids']['file_path'] = this.travelerIdQueryFilePath;
      const travelerIdQueryCheck = await this.dataCatService
        .getQueryUniques(this.lotIdsQueryFilePath, 'lot_ids', pageDetails)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              this.isUC3SigmaLotIdsBeforeApi = false;
              this.lotIdsDropdownList = res.body['uniques'];
              this.lotIdsDropdownCount = res.body['rows_count'];
              this.checkLotIds();
              if (openSelectionComponentAfterLoadingLotIds)
                this.openLotIdSelectionComponent();
            }
          },
          error: (err: any) => {
            this.isUC3SigmaLotIdsBeforeApi = false;
            this.toaster.error('Error in fetching data');
          },
        });
    }
  }

  async getLotIds() {
    try {
      if (!this.isLotIdsPolling && this.lotIdsDropdownList.length == 0) {
        this.isUC3SigmaLotIdsBeforeApi = true;
        let response = await this.dataCatService
          .lotIdsResponse(this.sessionData.job_id, this.config)
          .subscribe({
            next: async (res: any) => {
              this.lotIdsDataPullStatus();
            },
            error: (err: any) => {
              if (err.status === 422) {
                this.toaster.error(
                  'Please fill and save High Level Data Catalog',
                );
              } else {
                this.toaster.error('Error in fetching data');
              }
              this.isUC3SigmaLotIdsBeforeApi = false;
            },
          });
      } else {
        this.openLotIdSelectionComponent();
      }
    } catch (err: any) {
      this.isUC3SigmaLotIdsBeforeApi = false;
      this.toaster.error('Job failed to create');
    }
  }

  openLotIdSelectionComponent() {
    let { columnsList, selectedColumnsList } =
      Utils.convertDataToIncludeBooleanFlagsForCheckboxFuctionality(
        this.lotIdsDropdownList,
        this.selectedLotIds,
      );

    const dialogRef = this.dialog.open(ColumnDropDownComponent, {
      width: '70vw',
      height: '90vh',
      data: {
        columnsList: columnsList,
        selectedColumnsList: selectedColumnsList,
        infoRegardingTheColumns: '',
        widgetType: WidgetType.DROP_COLUMNS,
      },
    });

    dialogRef.afterClosed().subscribe((result: any) => {
      if (result.isSaved) {
        this.selectedLotIds = result.selectedColumnList.map(
          (element: any) => element.name,
        );
        this.checkLotIds();
      }
    });
  }

  openWaferIdSelectionComponent() {
    let { columnsList, selectedColumnsList } =
      Utils.convertDataToIncludeBooleanFlagsForCheckboxFuctionality(
        this.waferIdsDropdownList,
        this.selectedWaferIds,
      );

    const dialogRef = this.dialog.open(ColumnDropDownComponent, {
      width: '70vw',
      height: '90vh',
      data: {
        columnsList: columnsList,
        selectedColumnsList: selectedColumnsList,
        infoRegardingTheColumns: '',
        widgetType: WidgetType.DROP_COLUMNS,
      },
    });

    dialogRef.afterClosed().subscribe((result: any) => {
      if (result.isSaved) {
        this.selectedWaferIds = result.selectedColumnList.map(
          (element: any) => element.name,
        );
        this.setWaferIds();
      }
    });
  }

  async dcHighLevelSubmit() {
    if (this.endDate) {
      this.isdcHighLevelSubmit = false;
      await this.dataCatService
        .saveHighLevelDc(this.config, this.sessionData.job_id)
        .subscribe((res: any) => {
          if (res.body === 'saved') {
            this.isdcHighLevelSubmit = true;
            this.toaster.success('Data Saved Successfully');
          }
        });
    } else {
      this.isdcHighLevelSubmit = true;
    }
  }

  async getWaferIds() {
    try {
      // if (!this.isWaferIdsPolling && this.waferIdsDropdownList.length == 0) {
      //   this.config['lot_ids']['selected_values'] = this.selectedLotIds;
      //   let response = await this.dataCatService
      //     .waferIdsResponse(this.sessionData.job_id, this.config)
      //     .subscribe({
      //       next: async (res: any) => {
      //         this.waferIdsDataPullStatus();
      //       },
      //       error: (err: any) => {
      //         this.toaster.error('Error in fetching data');
      //       },
      //     });
      // }
    } catch (err: any) {
      this.toaster.error('Job failed to create');
    }
  }

  setWaferIds() {
    this.config['wafer_ids']['selected_values'] = this.selectedWaferIds;
    this.checkDownloadDisable();
  }

  async waferIdsDataPullStatus() {
    let status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.WaferIdsLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.WaferIdsLoadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.WaferIdsLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
      }
      setTimeout(() => {
        this.waferIdsDataPullStatus();
      }, 2000);
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.waferResultFetch();
    }
  }

  async waferResultFetch() {
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    let waferIdList = await this.dataCatService.getWaferIdsStatus(
      this.sessionData.job_id,
      this.fdWafarId,
    );
    this.showPolling = false;
    if (waferIdList) {
      this.lotIdsQueryFilePath =
        waferIdList.current_stage_results?.wafer_ids?.file_path;
      const travelerIdQueryCheck = await this.dataCatService
        .getQueryUniques(this.lotIdsQueryFilePath, 'wafer_ids', pageDetails)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              this.waferIdsDropdownList = res.body['uniques'];
              this.waferIdsDropdownCount = res.body['rows_count'];
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
          },
        });
    }
  }

  travelerStepsModal(getStepId: any): void {
    try {
      const dialogRef = this.dialog.open(TravelerStepsComponent, {
        width: '90%',
        height: '90%',
        disableClose: true,
        data: {
          update: false,
          list: this.travelerStepDropdownList,
          selectedList: this.selectedTravelerSteps,
          selectDropDown: getStepId,
        },
      });
      dialogRef.afterClosed().subscribe((result) => {
        if (result && result.selectedTravelerStep) {
          if (this.startDate && this.endDate) {
            this.isdcHighLevelSubmit = false;
          }
          this.selectedTravelerSteps = [...result.selectedTravelerStep];
          this.config['traveler_steps']['selected_values'] =
            this.selectedTravelerSteps.map(String);
        }
      });
    } catch (error: any) {
      this.toaster.error('Error occurred while opening Traveler Steps Modal.');
    }
  }

  async sigmaCommonTestIds(index: number) {
    this.isUC3SigmaCommonIdsBeforeApi = true;
    try {
      //await this.getCommonIds(index, true);
      this.isUC3SigmaCommonIdsBeforeApi = false;
      if (
        this.uc3SigmaFinalSelection?.[index]?.['uc3_sigma_metro_steps']?.[
          'selected_values'
        ] &&
        this.uc3SigmaFinalSelection[index]['uc3_sigma_metro_steps'][
          'selected_values'
        ].every((arr: any[]) => arr.length === 0)
      ) {
        this.isUC3SigmaCommonIdsBeforeApi = false;
        this.toaster.error(
          'Please select Metro Steps first or no Common Step IDs available.',
        );
      } else {
        const dialogRef = this.dialog.open(SigmaCommonTestComponent, {
          width: '960px',
          height: '90%',
          disableClose: true,
          data: {
            update: false,
            list: this.uc3CommonStepIds,
            row: index,
            globalList: this.uc3SigmaFinalSelection,
            filePath: this.selectedCommontestidPath,
          },
        });
        dialogRef.afterClosed().subscribe((result) => {
          if (result) {
            this.uc3SigmaFinalSelection[index]['common_test_ids'][
              'selected_values'
            ] = result;
            this.uc3SigmaFinalSelection[index]['common_test_ids']['file_path'] =
              this.selectedCommontestidPath;
            this.uc3SigmaCommonTestIdsSelected = result;
            this.isUC3DownloadDisable = false;
          }
        });
      }
    } catch (error) {
      this.toaster.error('Error occurred while fetching common test IDs.');
    }
  }

  onCloseTravelerStepsModal() {}

  addRow(index: number) {
    if (
      this.rows[index].processSteps ||
      this.rows[index].recipes ||
      this.rows[index].toolNames ||
      this.rows[index].runIds ||
      this.rows[index].startDate
    ) {
      this.rows.push({
        processSteps: '',
        recipes: '',
        toolNames: '',
        runIds: '',
        startDate: '',
      });
      this.FDfilterApply.push(this.FDContextfilters);
      this.FDContextfilters = {};
      this.previousColumnName = '';
    }
  }

  removeRow(index: number) {
    this.rows.splice(index, 1);
    this.FDContextfilters = {};
    this.previousColumnName = '';
  }

  onStartDateChange(event: any, index: number): void {
    const selectedDate = event.value;
    this.rows[index].startDate = selectedDate;
  }

  addMetroStepsRow() {
    this.metro_rows.push({ selection: '' });
  }

  removeMetroStepsRow(index: number) {
    this.uc3SigmaMetroStepsSelected.splice(index, 1);
    this.metro_rows.splice(index, 1);
    this.isUC3DownloadDisable = false;
  }

  GeneteFDContext() {
    this.createJob(this.sessionData.job_id, 'uc3_fd_context');
    this.isSensorPolling = true;
    setTimeout(() => {
      this.FDContextDataPullStatus();
    }, 2000);
  }

  async onGenerate(event: Event): Promise<void> {
    event.stopPropagation();
    this.isFDContextDownloadPath = true;
    this.GeneteFDContext();

    // try {
    //   if (
    //     !this.isLotIdsPolling &&
    //     this.lotIdsDropdownList.length == 0
    //   ) {
    //     let response = await this.dataCatService.FDContextResponse(
    //       this.sessionData.job_id,
    //       this.config,
    //     )
    //     .subscribe({
    //       next: async (res: any) => {
    //         this.FDContextDataPullStatus();
    //       }
    //       ,
    //       error: (err: any) => {
    //         this.toaster.error('Error in fetching data');
    //       },})

    //   }} catch (err: any) {
    //     this.toaster.error('Job failed to create');
    //   }
  }

  async FDContextDataPullStatus() {
    let status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.FDContextLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.FDContextLoadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.FDContextLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
      }
      setTimeout(() => {
        this.FDContextDataPullStatus();
      }, 2000);
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.FDContextResultFetch();
    }
  }

  async FinalDataContextDataPullStatus() {
    if (!this.isuc2FDTraceDownloadPolling) {
      let status = await this.dataCatService.dataPullStatus(
        this.sessionData.job_id,
      );
      if (
        status.current_stage_status !== 'SUCCESS' &&
        status.current_stage_status !== 'FAILED'
      ) {
        if (
          status?.job_status?.job_stage_status?.hasOwnProperty(
            'progress_percentage',
          )
        ) {
          this.FDContextLoadPercentage =
            status?.job_status?.job_stage_status?.progress_percentage;
          if (this.FDContextLoadPercentage !== 100) {
            this.showPolling = true;
            this.pollingPercentage = this.FDContextLoadPercentage;
            this.pollingMsg =
              status?.job_status?.job_stage_status?.progress_message;
          } else {
            this.showPolling = false;
          }
        }
        setTimeout(() => {
          this.FinalDataContextDataPullStatus();
        }, 2000);
      }
      if (
        status.fd_data_pull_job_status === 'IDLE' &&
        status.current_stage_status === 'SUCCESS'
      ) {
        this.FinalDataContextResultFetch();
      }
    }
  }

  async FinalDataContextResultFetch() {
    let FDContextList = await this.dataCatService.getLotsIdsStatus(
      this.sessionData.job_id,
      this.finalDataAggregate,
    );
    this.showPolling = false;
    this.isuc2FDTraceDownloadPolling = false;
    if (FDContextList) {
      this.resultDataFilePath =
        FDContextList.current_stage_results?.final_data?.file_path;
      this.isuc2FDTraceResultFailed = false;
      //this.config['traveler_ids']['file_path'] = this.travelerIdQueryFilePath;
    }
  }

  async FDContextResultFetch() {
    let FDContextList = await this.dataCatService.getLotsIdsStatus(
      this.sessionData.job_id,
      this.fdContext,
    );
    this.showPolling = false;
    if (FDContextList) {
      this.FDContextQueryFilePath =
        FDContextList.current_stage_results?.lot_ids?.file_path;
      //this.config['traveler_ids']['file_path'] = this.travelerIdQueryFilePath;
    }
  }

  async getProcessSteps(columnName: string, index: number) {
    //let FDContextfilter = {filters: [key: string]: string[] }

    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    //let path = "/workflow_service/app/services/micron/data_catalog/fd_trace/dummy_files/contexts.parquet";
    let path = '/hexaind-data/uc3_fd_context.parquet';
    if (this.previousColumnName !== columnName) {
      if (this.previousColumnName) {
        let previousresult = this.rows[index][this.resultColumn];
        let childObject = {
          value: previousresult,
          operation: 'EQ',
        };

        this.FDContextfilters[this.previousColumnName] = childObject;
        // this.FDContextfilters = {
        //   'TRAVELER_STEP': {
        //     value: previousresult,
        //     operation: "EQ"
        //   }};
      }

      const travelerIdQueryCheck = await this.dataCatService
        .getQueryUniques(path, columnName, pageDetails, this.FDContextfilters)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              if (columnName === 'TRAVELER_STEP') {
                this.FDContextList.processStepsList = res.body['uniques'];
                this.resultColumn = 'processSteps';
              }
              if (columnName === 'RECIPE_NAME') {
                this.FDContextList.recipeName = res.body['uniques'];
                this.resultColumn = 'recipes';
              }
              if (columnName === 'TOOL_NAME') {
                this.FDContextList.toolName = res.body['uniques'];
                this.resultColumn = 'toolNames';
              }
              if (columnName === 'RUN_ID') {
                this.FDContextList.runID = res.body['uniques'];
                this.resultColumn = 'runIds';
              }
              this.previousColumnName = columnName;
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
          },
        });
    }
  }

  getProcessStepsFilterApply() {
    let functionCall = false;
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    let path = '/hexaind-data/uc3_fd_context.parquet';
    if (this.FDContextfilters) {
      this.FDfilterApply.push(this.FDContextfilters);
    }
    let save = true;
    let do_not_send_data = true; // wont't get the result data  for true
    let ignore_pagination = true;
    for (let filter of this.FDfilterApply) {
      this.dataCatService
        .getFDContextQueryResponse(
          path,
          save,
          do_not_send_data,
          ignore_pagination,
          filter,
          pageDetails,
        )
        .subscribe(async (result: any) => {
          this.fdContextFilterApplyPath = result['body']['saved_path'];
          functionCall = true;
          this.fdContextApplyFilter();
        });
    }
    // if(functionCall){
    //   this.fdContextApplyFilter();
    // }
    //this.FDfilterApply=[];
  }

  async fdContextApplyFilter() {
    for (let item of this.FDfilterApply) {
      let childObject = {
        filters: item,
        path: this.fdContextFilterApplyPath,
      };
      this.applyfilter.push(childObject);
    }

    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    try {
      if (!this.isFDContextFilterPolling) {
        let response = await this.dataCatService
          .fdContextFilterApplyResponse(
            this.sessionData.job_id,
            this.config,
            this.applyfilter,
            this.fdContextFilterApplyPath,
            pageDetails,
          )
          .subscribe({
            next: async (res: any) => {
              this.fdContextStatus();
            },
            error: (err: any) => {
              this.toaster.error('Error in fetching data');
            },
          });
      }
    } catch (err: any) {
      this.toaster.error('Job failed to create');
    }
  }

  async fdContextStatus() {
    let status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.fdContexApplyFiltertLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.fdContexApplyFiltertLoadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.fdContexApplyFiltertLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
      }
      setTimeout(() => {
        this.fdContextStatus();
      }, 2000);
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.fdContextResultFetch();
    }
  }

  async fdContextResultFetch() {
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    let applyFilterResult =
      await this.dataCatService.getFDContextApplyFilterStatus(
        this.sessionData.job_id,
        this.fdContextFilter,
      );
    this.showPolling = false;
    if (applyFilterResult) {
      this.fdContextFinalPath =
        applyFilterResult.current_stage_results?.aggregated_file_path;
      //this.config['traveler_ids']['file_path'] = this.travelerIdQueryFilePath;
    }
  }

  travelerIdSelectAll(event: MatCheckboxChange) {
    if (event.checked) {
      this.selectedTravelerid = [...this.filteredTravelerIdDropdownList];
    } else {
      // Clear all selections
      this.selectedTravelerid = [];
    }
  }

  getResetFilterApply(event: Event) {
    this.resetTravelerSteps = this.selectedTravelerSteps;
    this.filteredTools = [];
    this.filteredToolsSearchList = [];
    this.filteredStepIdDropdownList = [];
    this.filteredStepIdDropdownSearchList = [];
    this.filteredSensorDropdownList = [];
    this.filteredSensorDropdownSearchList = [];
    this.isGenerating = false;
    this.resultDataFilePath = '';
    this.isuc2FDTraceResultFailed = false;
    this.uC2SelectedToolIds = [];
    this.uC2FdselectedRecipeNames = [];
    this.uC2SelectedStepIds = [];
    this.uC2FdTraceAggrSelectedSensors = [];
    this.isGenerating = false;
    this.isUC2FDGenerateButton = false;
    this.updateUC2FDTraceConfigSelectedValues();
    this.isUC2TraceStepIdsValue = false;
    this.isUC2TraceSensorsValue = false;
    this.isUC2TraceToolsIdsValue = false;
    this.toolGroups = [];
    this.addNewGroup(true, 0);
    event.stopPropagation();
  }

  disableGenerateButton(): boolean {
    return this.isGenerating; // Return true to disable when fetching
  }

  areTravelerIdsAllSelected(): boolean {
    return (
      this.filteredTravelerIdDropdownList.length > 0 &&
      this.filteredTravelerIdDropdownList.every((traveler) =>
        this.selectedTravelerid
          ? this.selectedTravelerid.includes(traveler)
          : false,
      )
    );
  }

  async UC2SigmaClicked(event: any) {
    this.isUC2SigmaChecked = event.checked;

    if (this.isUC2SigmaChecked) {
      this.UC2SigmaStageResult =
        await this.dataCatService.getFDContextApplyFilterStatus(
          this.sessionData.job_id,
          this.uc2SigmaStage,
        );
      if (this.UC2SigmaStageResult.current_stage_status === 'NOT_CONFIGURED') {
        console.log('not configured...');
      } else {
        this.uc2SigmaReloadResultFetch();
        if (this.UC2SigmaStageResult.current_stage_status === 'SUCCESS') {
          this.isuc2SigmaResultPath = true;
          this.uc2SigmaResultPath =
            this.UC2SigmaStageResult.current_stage_results.uc2_sigma_data.file_path;
          this.toaster.success('Data fetched successfully');
        } else if (this.UC2SigmaStageResult.current_stage_status === 'FAILED') {
          this.toaster.error('UC2 Sigma Job Failed');
          this.isuc2SigmaResultFailed = true;
        } else {
          this.uc2SigmaReloadStatusCheck();
        }
      }
    }
  }

  async populateDropdown() {
    let i = 0;
    // Generate Recipes Values
    let recipe_response = await this.dataCatService.fetchRecipesNamesAndIds(
      this.UC2FdStageResult.current_stage_inputs.recipes.file_path,
    );
    this.recipes = recipe_response.body;
    this.filteredRecipeNames = this.recipes;
    let uc2_fd_selected_values_recipes =
      this.UC2FdStageResult.current_stage_inputs.recipes.selected_values;
    // let manually_entered_recipes = []

    // Assigning the Selected Values into the config
    this.config.selectedRecipeNames =
      this.UC2FdStageResult.current_stage_inputs.recipes.selected_values;
    this.config.uC2SelectedToolIds = [];
    this.config.step_ids.selected_values =
      this.UC2FdStageResult.current_stage_inputs.step_ids.selected_values;
    this.config.recipes.selected_values =
      this.UC2FdStageResult.current_stage_inputs.recipes.selected_values;

    this.config.recipes.file_path =
      this.UC2FdStageResult.current_stage_inputs.recipes.file_path;
    this.config.tool_ids.file_path =
      this.UC2FdStageResult.current_stage_inputs.tool_ids.file_path;
    this.config.step_ids.file_path =
      this.UC2FdStageResult.current_stage_inputs.step_ids.file_path;
    this.config.sensors.file_path =
      this.UC2FdStageResult.current_stage_inputs.sensors.file_path;

    this.uC2FdselectedRecipeNames =
      this.UC2FdStageResult.current_stage_inputs.recipes.selected_values;
    this.uC2SelectedStepIds =
      this.UC2FdStageResult.current_stage_inputs.step_ids.selected_values;
    this.uC2FdTraceAggrSelectedSensors =
      this.UC2FdStageResult.current_stage_inputs.sensors.selected_values;

    // Papulating the rows based on recipes selected Length
    let recipeLength =
      this.UC2FdStageResult.current_stage_inputs.recipes.selected_values.length;
    // let rowAddLength = 1;
    while (recipeLength > 1 && this.toolGroups.length < recipeLength) {
      this.addNewGroup(true, 0);
      // rowAddLength++;
      // recipeLength = recipeLength-1;
    }

    // Iterating the Selected Recipe Values
    for (let item of uc2_fd_selected_values_recipes) {
      if (item) {
        for (let element of item) {
          let find_r = this.filteredRecipeNames.find(
            (x: any) => x.recipe_name.toString() == element.toString(),
          );
          if (!find_r) {
            this.filteredRecipeNames.push({ recipe_name: element.toString() });
          }
        }
        let tool_file_path =
          this.UC2FdStageResult.current_stage_inputs.tool_ids.file_path;
        // Generating Tool Ids
        await this.onRecipeClickHelpFunc(tool_file_path, item, i, true);
        if (
          this.UC2FdStageResult.current_stage_inputs.tool_ids.selected_values[i]
        ) {
          let flated_r = this.filteredTools[i];
          //handling case to show manually input tools
          let manually_input_ids: any = [];
          this.UC2FdStageResult.current_stage_inputs.tool_ids.selected_values[
            i
          ].forEach((element: any) => {
            if (!flated_r.find((input: any) => input.TOOL_ID === element)) {
              manually_input_ids.push(element);
            }
          });
          for (let manually_entered_tool_id of manually_input_ids) {
            this.filteredTools[i].push({
              TOOL_ID: manually_entered_tool_id,
              TOOL_NAME: '[ManuallyEntered]' + manually_entered_tool_id,
            });
          }
          flated_r = this.filteredTools[i];
          this.filteredToolsSearchList[i] = this.filteredTools[i];
          //update filtered tools

          let temp_variable: string[] = [];

          let fetched_tool_ids =
            this.UC2FdStageResult.current_stage_inputs.tool_ids.selected_values[
              i
            ];
          // Finding the Tool_Name because not getting from Apis
          for (let selected_tool_id of fetched_tool_ids) {
            let itemm = flated_r.find(
              (input: any) => input.TOOL_ID === selected_tool_id,
            );
            if (itemm) {
              temp_variable.push(itemm.TOOL_ID);
            }
          }
          this.uC2SelectedToolIds[i] = temp_variable;
          this.config.uC2SelectedToolIds[i] = temp_variable;
          this.config.tool_ids.selected_values[i] = temp_variable;

          if (this.uC2SelectedToolIds[i]) {
            // Generating Step Ids
            await this.onStepIdClick(
              i,
              true,
              this.UC2FdStageResult.current_stage_inputs.step_ids.file_path,
            );
            for (let element of this.UC2FdStageResult.current_stage_inputs
              .step_ids.selected_values[i]) {
              let find_r = this.filteredStepIdDropdownList[i].find(
                (x: any) => x == element,
              );
              if (!find_r) {
                this.filteredStepIdDropdownList[i].push(element.toString());
              }
            }
            this.filteredStepIdDropdownSearchList[i] =
              this.filteredStepIdDropdownList[i]; //Step Id Search functionality

            if (this.filteredStepIdDropdownList[i]) {
              // Generating Sensors values
              await this.onStepIdbtnClick(
                i,
                true,
                this.UC2FdStageResult.current_stage_inputs.sensors.file_path,
              );
              for (let element of this.UC2FdStageResult.current_stage_inputs
                .sensors.selected_values[i]) {
                let find_r = this.filteredSensorDropdownList[i].find(
                  (x: any) => x == element,
                );
                if (!find_r) {
                  this.filteredSensorDropdownList[i].push(element.toString());
                }
              }
              this.filteredSensorDropdownSearchList[i] =
                this.filteredSensorDropdownList[i]; // Sensor Search Functionality
              // if (this.filteredSensorDropdownList[i]){
              //   this.uC2FdTraceAggrSelectedSensors[i] = [...this.filteredSensorDropdownList[i]]
              // }
            }
          }
        }
        this.updateSelectAllState(i); // Select All For Tools
        this.updateRecipeSelectAllState(i); // SelectAll for Recipes
        this.updateSelectAllStepIds(i); // SelectAll for StepIds
        this.updateSelectAllSensors(i); // SelectAll for Sensors

        i++;
      }
      this.isUC2FDGenerateButton = true;
    }
  }

  async UC2FdClicked(event: any) {
    this.isUC2FdChecked = event.checked;

    if (this.isUC2FdChecked) {
      this.UC2FdStageResult =
        await this.dataCatService.getFDContextApplyFilterStatus(
          this.sessionData.job_id,
          this.uc2FdStage,
        );
      if (this.UC2FdStageResult.current_stage_status === 'NOT_CONFIGURED') {
        this.isGenerating = false;
        this.isUC2FDGenerateButton = false;
      } else {
        //this.uc2FdReloadResultFetch();
        await this.populateDropdown();
        if (this.UC2FdStageResult.current_stage_status === 'SUCCESS') {
          this.isuc2FdResultPath = true;
          this.isGenerating = true;
          this.isUC2FDGenerateButton = true;
          this.uc2FdResultPath =
            this.UC2FdStageResult.current_stage_results.final_data.file_path;
          this.resultDataFilePath =
            this.UC2FdStageResult.current_stage_results.final_data.file_path;
          //await this.getRecipesOnGenerate(this.uc2FdResultPath)
          // await this.populateDropdown()
          this.toaster.success('Data fetched successfully');
        } else if (this.UC2FdStageResult.current_stage_status === 'FAILED') {
          this.toaster.error('UC2 FD Job Failed');
          this.isuc2FDTraceResultFailed = true;
          this.isuc2FdResultFailed = true;
          this.isUC2FDGenerateButton = false;
        } else {
          await this.uc2FDTraceReloadStatusCheck();
        }
      }
    }
  }

  async uc2FDTraceReloadStatusCheck() {
    if (!this.isuc2FDGenaratePolling) {
      let status = await this.dataCatService.dataPullStatus(
        this.sessionData.job_id,
      );
      if (
        status.current_stage_status !== 'SUCCESS' &&
        status.current_stage_status !== 'FAILED'
      ) {
        if (
          status?.job_status?.job_stage_status?.hasOwnProperty(
            'progress_percentage',
          )
        ) {
          this.FDContextLoadPercentage =
            status?.job_status?.job_stage_status?.progress_percentage;
          if (this.FDContextLoadPercentage !== 100) {
            this.showPolling = true;
            this.isuc2FDGenaratePolling = false;
            this.pollingPercentage = this.FDContextLoadPercentage;
            this.pollingMsg =
              status?.job_status?.job_stage_status?.progress_message;
          } else {
            this.showPolling = false;
            //this.isuc2FDTraceDownloadPolling = true;
          }
        }
        setTimeout(() => {
          this.uc2FDTraceReloadStatusCheck();
        }, 2000);
      }
      if (status.current_stage_status === 'SUCCESS') {
        //this.isuc2SigmaResultPath = true;
        this.resultDataFilePath =
          this.UC2SigmaStageResult.current_stage_results.final_data.file_path;
        this.toaster.success('Data fetched successfully');
        this.isuc2FDTraceDownloadPolling = false;
        this.isuc2FDTraceResultFailed = false;
        this.showPolling = false;
        this.isGenerating = true;
        this.isUC2FDGenerateButton = true;
      }
    }
  }

  async uc2SigmaReloadResultFetch() {
    // Fetching Measure Steps
    this.measurementStepGQLFileList = this.UC2SigmaStageResult
      .current_stage_inputs['measurement_steps']
      ? this.UC2SigmaStageResult.current_stage_inputs['measurement_steps'][
          'selected_values'
        ]
      : '';
    this.UC2SigmaSelectedMeasurementSteps = this.measurementStepGQLFileList;
    this.measurementStepGQLSearchList = this.measurementStepGQLFileList;
    this.isUC2SigmaMeasurementStepsSelectAll =
      this.measurementStepGQLFileList.length ===
      this.UC2SigmaSelectedMeasurementSteps.length;
    if (this.UC2SigmaSelectedMeasurementSteps.length > 0) {
      this.uc2SigmaSelectedData.measurement_steps.selected_values =
        this.UC2SigmaSelectedMeasurementSteps;
    }

    // Fetching Measure Parameters
    this.measurementParametersGQLFileList = this.UC2SigmaStageResult
      .current_stage_inputs['measurement_parameters']
      ? this.UC2SigmaStageResult.current_stage_inputs['measurement_parameters'][
          'selected_values'
        ]
      : '';
    this.UC2SigmaSelectedMeasurementParameters =
      this.measurementParametersGQLFileList;
    this.measumentParametersSearch = this.measurementParametersGQLFileList;
    this.isUC2SigmaMeasureParametersSelectAll =
      this.measurementParametersGQLFileList.length ===
      this.UC2SigmaSelectedMeasurementParameters.length;
    if (this.UC2SigmaSelectedMeasurementParameters.length > 0) {
      this.uc2SigmaSelectedData.measurement_parameters.selected_values =
        this.UC2SigmaSelectedMeasurementParameters;
    }

    // Fetching Point Steps
    this.point_stepsGQLFileList = this.UC2SigmaStageResult.current_stage_inputs[
      'point_steps'
    ]
      ? this.UC2SigmaStageResult.current_stage_inputs['point_steps'][
          'selected_values'
        ]
      : '';
    this.UC2SigmaSelectedPointSteps = this.point_stepsGQLFileList;
    this.pointStepsSearch = this.point_stepsGQLFileList;
    this.isUC2SigmaPointStepsSelectAll =
      this.point_stepsGQLFileList.length ===
      this.UC2SigmaSelectedPointSteps.length;
    if (this.UC2SigmaSelectedPointSteps.length > 0) {
      this.uc2SigmaSelectedData.point_steps.selected_values =
        this.UC2SigmaSelectedPointSteps;
    }

    this.point_parametersGQLFileList = this.UC2SigmaStageResult
      .current_stage_inputs['point_parameters']
      ? this.UC2SigmaStageResult.current_stage_inputs['point_parameters'][
          'selected_values'
        ]
      : '';
    this.UC2SigmaSelectedPointParameters = this.point_parametersGQLFileList;
    this.pointParametersSearch = this.point_parametersGQLFileList;
    this.isUC2SigmaPointParametersSelectAll =
      this.point_parametersGQLFileList.length ===
      this.UC2SigmaSelectedPointParameters.length;
    if (this.UC2SigmaSelectedPointParameters.length > 0) {
      this.uc2SigmaSelectedData.point_parameters.selected_values =
        this.UC2SigmaSelectedPointParameters;
    }

    this.runStepGQLFileList = this.UC2SigmaStageResult.current_stage_inputs[
      'run_parameters'
    ]
      ? this.UC2SigmaStageResult.current_stage_inputs['run_parameters'][
          'selected_path'
        ]
      : '';

    const pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    this.UC2SigmaSelectedRunParameters = this.runStepGQLFileList;
    // this.GetAdvanceUniques =
    // await this.dataCatService.getQueryAdvanced(
    //   this.runStepGQLFileList, 'run_parameters', pageDetails, '','', ''
    // );
    //console.log(this.GetAdvanceUniques,"get status nw");
    // this.UC2SigmaSelectedRunParameters = this.runStepGQLFileList;
    // this.runParametersSearch = this.runStepGQLFileList;
    // this.isUC2SigmaRunParametersSelectAll =
    //   this.runStepGQLFileList.length ===
    //   this.UC2SigmaSelectedRunParameters.length;
    // if (this.UC2SigmaSelectedRunParameters.length > 0) {
    //   this.uc2SigmaSelectedData.run_parameters.selected_values =
    //     this.UC2SigmaSelectedRunParameters;
    // }

    // if (this.UC2SigmaSelectedRunParameters.length > 0) {
    //   const selectedPathsByColumn = localStorage.getItem('selectedPathsByColumn');

    //   let runParametersPath = '';

    //   // Parse the JSON and get the value of run_parameters
    //   if (selectedPathsByColumn) {
    //     const parsedData = JSON.parse(selectedPathsByColumn);
    //     runParametersPath = parsedData.run_parameters || ''; // Access `run_parameters` key
    //   }

    //   this.uc2SigmaSelectedData.run_parameters.selected_values =
    //   runParametersPath;
    // }

    this.waferParametersGQLFileList = this.UC2SigmaStageResult
      .current_stage_inputs['wafer_parameters']
      ? this.UC2SigmaStageResult.current_stage_inputs['wafer_parameters'][
          'selected_values'
        ]
      : '';
    this.UC2SigmaSelectedWaferParameters = this.waferParametersGQLFileList;
    this.waferParametersSearch = this.waferParametersGQLFileList;
    this.isUC2SigmaWaferParametersSelectAll =
      this.waferParametersGQLFileList.length ===
      this.UC2SigmaSelectedWaferParameters.length;
    if (this.UC2SigmaSelectedWaferParameters.length > 0) {
      this.uc2SigmaSelectedData.wafer_parameters.selected_values =
        this.UC2SigmaSelectedWaferParameters;
    }
  }

  async uc2SigmaReloadStatusCheck() {
    if (!this.isuc2SigmaDownloadPolling) {
      let status = await this.dataCatService.dataPullStatus(
        this.sessionData.job_id,
      );
      if (
        status.current_stage_status !== 'SUCCESS' &&
        status.current_stage_status !== 'FAILED'
      ) {
        if (
          status?.job_status?.job_stage_status?.hasOwnProperty(
            'progress_percentage',
          )
        ) {
          this.uc2SigmaLoadPercentage =
            status?.job_status?.job_stage_status?.progress_percentage;
          if (this.uc2SigmaLoadPercentage !== 100) {
            this.showPolling = true;
            this.pollingPercentage = this.uc2SigmaLoadPercentage;
            this.pollingMsg =
              status?.job_status?.job_stage_status?.progress_message;
          } else {
            this.showPolling = false;
          }
        }
        setTimeout(() => {
          this.uc2SigmaReloadStatusCheck();
        }, 2000);
      }
      if (status.current_stage_status === 'SUCCESS') {
        this.isuc2SigmaResultPath = true;
        this.uc2SigmaResultPath =
          this.UC2SigmaStageResult.current_stage_results.uc2_sigma_data.file_path;
        this.toaster.success('Data fetched successfully');
        this.isuc2SigmaDownloadPolling = false;
        this.isuc2SigmaResultFailed = false;
      }
    }
  }

  browseGQLInputClick(fileInput: HTMLInputElement) {
    fileInput.click();
  }

  async onGQLFileSelected(event: any) {
    const formData = new FormData();
    let selectedFile = event.target.files[0];
    formData.append('file', selectedFile);
    let file = this.dataCatService.getGQLFileData(formData).subscribe({
      next: async (res: any) => {
        this.selectedGQLFileParquetPath = res.parquet_file_path;
        this.responsePathRun = this.selectedGQLFileParquetPath;
        this.uc2SigmaSelectedData.gql_file_details.parquet_file_path =
          res.parquet_file_path;
        this.uc2SigmaSelectedData.gql_file_details.gql_file_path =
          res.gql_file_path;
        this.toaster.success('Data Uploaded Sucessfully');
        this.onUC2GQLUploadFileUniques();
        this.isUC2SigmaDownloadCheck = true;
      },
      error: (err: any) => {
        this.toaster.error('Error in fetching data');
      },
    });
    this.uc2SigmaUploadButton = true;
  }

  async onUC2GQLUploadFileUniques() {
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };

    await this.dataCatService
      .getQueryUniques(
        this.selectedGQLFileParquetPath,
        'measurement_steps',
        pageDetails,
      )
      .subscribe({
        next: async (res: any) => {
          if (res.body['uniques']) {
            let response = res.body['uniques'];
            if (!this.measurementStepGQLFileList) {
              this.measurementStepGQLFileList = res.body['uniques'];
            } else {
              this.measurementStepGQLFileList = [
                ...new Set([
                  ...res.body['uniques'],
                  ...this.measurementStepGQLFileList,
                ]),
              ];
            }
            this.uc2SigmaSelectedData.measurement_steps.selected_values =
              this.measurementStepGQLFileList;
            this.measurementStepGQLSearchList = this.measurementStepGQLFileList;
            // upload all data checkbox enable checked option.
            this.UC2SigmaSelectedMeasurementSteps = [
              ...new Set([
                ...response,
                ...this.UC2SigmaSelectedMeasurementSteps,
              ]),
            ];
            this.isUC2SigmaMeasurementStepsSelectAll =
              this.measurementStepGQLFileList.length ===
              this.UC2SigmaSelectedMeasurementSteps.length;
            this.measurementStepGQLFileCount = res.body['rows_count'];
          }
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });
    await this.dataCatService
      .getQueryUniques(
        this.selectedGQLFileParquetPath,
        'run_parameters',
        pageDetails,
      )
      .subscribe({
        next: async (res: any) => {
          if (res.body['uniques']) {
            let response = res.body['uniques'];
            if (!this.runStepGQLFileList) {
              this.runStepGQLFileList = res.body['uniques'];
            } else {
              this.runStepGQLFileList = [
                ...new Set([
                  ...res.body['uniques'],
                  ...this.runStepGQLFileList,
                ]),
              ];
            }
            this.uc2SigmaSelectedData.run_parameters.selected_values =
              this.runStepGQLFileList;
            this.runParametersSearch = this.runStepGQLFileList;
            this.UC2SigmaSelectedRunParameters = [
              ...new Set([...response, ...this.UC2SigmaSelectedRunParameters]),
            ];
            this.isUC2SigmaRunParametersSelectAll =
              this.runStepGQLFileList.length ===
              this.UC2SigmaSelectedRunParameters.length;
          }
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });

    await this.dataCatService
      .getQueryUniques(
        this.selectedGQLFileParquetPath,
        'wafer_parameters',
        pageDetails,
      )
      .subscribe({
        next: async (res: any) => {
          if (res.body['uniques']) {
            let response = res.body['uniques'];
            if (!this.waferParametersGQLFileList) {
              this.waferParametersGQLFileList = res.body['uniques'];
            } else {
              this.waferParametersGQLFileList = [
                ...new Set([
                  ...res.body['uniques'],
                  ...this.waferParametersGQLFileList,
                ]),
              ];
            }
            this.uc2SigmaSelectedData.wafer_parameters.selected_values =
              this.waferParametersGQLFileList;
            this.waferParametersSearch = this.waferParametersGQLFileList;
            this.UC2SigmaSelectedWaferParameters = [
              ...new Set([
                ...response,
                ...this.UC2SigmaSelectedWaferParameters,
              ]),
            ];
            this.isUC2SigmaWaferParametersSelectAll =
              this.waferParametersGQLFileList.length ===
              this.UC2SigmaSelectedWaferParameters.length;
          }
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });

    await this.dataCatService
      .getQueryUniques(
        this.selectedGQLFileParquetPath,
        'measurement_parameters',
        pageDetails,
      )
      .subscribe({
        next: async (res: any) => {
          if (res.body['uniques']) {
            let response = res.body['uniques'];
            if (!this.measurementParametersGQLFileList) {
              this.measurementParametersGQLFileList = res.body['uniques'];
            } else {
              this.measurementParametersGQLFileList = [
                ...new Set([
                  ...res.body['uniques'],
                  ...this.measurementParametersGQLFileList,
                ]),
              ];
            }
            this.uc2SigmaSelectedData.measurement_parameters.selected_values =
              this.measurementParametersGQLFileList;
            this.measumentParametersSearch =
              this.measurementParametersGQLFileList;
            this.UC2SigmaSelectedMeasurementParameters = [
              ...new Set([
                ...response,
                ...this.UC2SigmaSelectedMeasurementParameters,
              ]),
            ];
            this.isUC2SigmaMeasureParametersSelectAll =
              this.measurementParametersGQLFileList.length ===
              this.UC2SigmaSelectedMeasurementParameters.length;
          }
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });

    await this.dataCatService
      .getQueryUniques(
        this.selectedGQLFileParquetPath,
        'point_steps',
        pageDetails,
      )
      .subscribe({
        next: async (res: any) => {
          if (res.body['uniques']) {
            let response = res.body['uniques'];
            if (!this.point_stepsGQLFileList) {
              this.point_stepsGQLFileList = res.body['uniques'];
            } else {
              this.point_stepsGQLFileList = [
                ...new Set([
                  ...res.body['uniques'],
                  ...this.point_stepsGQLFileList,
                ]),
              ];
            }
            this.uc2SigmaSelectedData.point_steps.selected_values =
              this.point_stepsGQLFileList;
            this.pointStepsSearch = this.point_stepsGQLFileList;
            this.UC2SigmaSelectedPointSteps = [
              ...new Set([...response, ...this.UC2SigmaSelectedPointSteps]),
            ];
            this.isUC2SigmaPointStepsSelectAll =
              this.point_stepsGQLFileList.length ===
              this.UC2SigmaSelectedPointSteps.length;
          }
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });

    await this.dataCatService
      .getQueryUniques(
        this.selectedGQLFileParquetPath,
        'point_parameters',
        pageDetails,
      )
      .subscribe({
        next: async (res: any) => {
          if (res.body['uniques']) {
            let response = res.body['uniques'];
            if (!this.point_parametersGQLFileList) {
              this.point_parametersGQLFileList = res.body['uniques'];
            } else {
              this.point_parametersGQLFileList = [
                ...new Set([
                  ...res.body['uniques'],
                  ...this.point_parametersGQLFileList,
                ]),
              ];
            }
            this.uc2SigmaSelectedData.point_parameters.selected_values =
              this.point_parametersGQLFileList;
            this.pointParametersSearch = this.point_parametersGQLFileList;
            this.UC2SigmaSelectedPointParameters = [
              ...new Set([
                ...response,
                ...this.UC2SigmaSelectedPointParameters,
              ]),
            ];
            this.isUC2SigmaPointParametersSelectAll =
              this.point_parametersGQLFileList.length ===
              this.UC2SigmaSelectedPointParameters.length;
            //this.measurementStepGQLFileCount = res.body['rows_count'];
          }
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });
  }

  async FDTraceSigmaGenerateData() {
    await this.dataCatService
      .sigmaGenerateData(this.sessionData.job_id, this.config)
      .subscribe({
        next: async (res: any) => {
          this.uc2SigmaGenerateButton = true;
          this.uc2SigmaMeasumentStepsSubmitButton = false;
          this.uc2SigmaPointStepsSubmitButton = false;
          if (res.body['measurement_steps']) {
            let responsePath = res.body['measurement_steps'].file_path;
            this.onUC2GenerateUniques(responsePath, 'measurement_steps');
          }
          if (res.body['point_steps']) {
            let responsePath = res.body['point_steps'].file_path;
            this.onUC2GenerateUniques(responsePath, 'point_steps');
          }
          if (res.body['run_parameters']) {
            let responsePath = res.body['run_parameters'].file_path;
            this.responsePathRun = responsePath;

            this.onUC2GenerateUniques(responsePath, 'run_parameters');
          }
          this.toaster.success(
            'Measurement Steps, Point Steps and Run Parameters data fetched successfully',
          );
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });
  }

  async onUC2GenerateUniques(onUC2UniquesPath: any, parameter: any) {
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };

    if (parameter === 'measurement_steps') {
      await this.dataCatService
        .getQueryUniques(onUC2UniquesPath, 'measurement_steps', pageDetails)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              if (!this.measurementStepGQLFileList) {
                this.measurementStepGQLFileList = res.body['uniques'];
              } else {
                this.measurementStepGQLFileList = [
                  ...new Set([
                    ...res.body['uniques'],
                    ...this.measurementStepGQLFileList,
                  ]),
                ];
              }
              this.uc2SigmaSelectedData.measurement_steps.file_path =
                onUC2UniquesPath;
              this.measurementStepGQLSearchList =
                this.measurementStepGQLFileList;
              this.isUC2SigmaMeasurementStepsSelectAll =
                this.measurementStepGQLFileList.length ===
                this.UC2SigmaSelectedMeasurementSteps.length;
              //this.uc2SigmaSelectedData.measurement_steps.selected_values = this.measurementStepGQLFileList;
              this.measurementStepGQLFileCount = res.body['rows_count'];
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
          },
        });
    }

    if (parameter === 'run_parameters') {
      await this.dataCatService
        .getQueryUniques(onUC2UniquesPath, 'run_parameters', pageDetails)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              if (!this.runStepGQLFileList) {
                this.runStepGQLFileList = res.body['uniques'];
              } else {
                this.runStepGQLFileList = [
                  ...new Set([
                    ...res.body['uniques'],
                    ...this.runStepGQLFileList,
                  ]),
                ];
              }
              this.uc2SigmaSelectedData.run_parameters.file_path =
                onUC2UniquesPath;
              this.runParametersSearch = this.runStepGQLFileList;
              this.isUC2SigmaRunParametersSelectAll =
                this.runStepGQLFileList.length;
              //this.uc2SigmaSelectedData.run_parameters.selected_values = this.runStepGQLFileList;
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
          },
        });
    }

    if (parameter === 'point_steps') {
      await this.dataCatService
        .getQueryUniques(onUC2UniquesPath, 'point_steps', pageDetails)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              if (!this.point_stepsGQLFileList) {
                this.point_stepsGQLFileList = res.body['uniques'];
              } else {
                this.point_stepsGQLFileList = [
                  ...new Set([
                    ...res.body['uniques'],
                    ...this.point_stepsGQLFileList,
                  ]),
                ];
              }
              this.uc2SigmaSelectedData.point_steps.file_path =
                onUC2UniquesPath;
              this.pointStepsSearch = this.point_stepsGQLFileList;
              this.isUC2SigmaPointStepsSelectAll =
                this.point_stepsGQLFileList.length ===
                this.UC2SigmaSelectedPointSteps.length;
              //this.uc2SigmaSelectedData.point_steps.selected_values = this.point_stepsGQLFileList;
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
          },
        });
    }
    if (parameter === 'wafer_parameters') {
      await this.dataCatService
        .getQueryUniques(onUC2UniquesPath, 'wafer_parameters', pageDetails)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              if (!this.waferParametersGQLFileList) {
                this.waferParametersGQLFileList = res.body['uniques'];
              } else {
                this.waferParametersGQLFileList = [
                  ...new Set([
                    ...res.body['uniques'],
                    ...this.waferParametersGQLFileList,
                  ]),
                ];
              }
              this.uc2SigmaSelectedData.wafer_parameters.file_path =
                onUC2UniquesPath;
              this.waferParametersSearch = this.waferParametersGQLFileList;
              this.isUC2SigmaWaferParametersSelectAll =
                this.waferParametersGQLFileList.length ===
                this.UC2SigmaSelectedWaferParameters.length;
              //this.uc2SigmaSelectedData.wafer_parameters.selected_values = this.waferParametersGQLFileList;
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
          },
        });
    }

    if (parameter === 'measurement_parameters') {
      await this.dataCatService
        .getQueryUniques(
          onUC2UniquesPath,
          'measurement_parameters',
          pageDetails,
        )
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              if (!this.measurementParametersGQLFileList) {
                this.measurementParametersGQLFileList = res.body['uniques'];
              } else {
                this.measurementParametersGQLFileList = [
                  ...new Set([
                    ...res.body['uniques'],
                    ...this.measurementParametersGQLFileList,
                  ]),
                ];
              }
              this.uc2SigmaSelectedData.measurement_parameters.file_path =
                onUC2UniquesPath;
              this.measumentParametersSearch =
                this.measurementParametersGQLFileList;
              this.isUC2SigmaMeasureParametersSelectAll =
                this.measurementParametersGQLFileList.length ===
                this.UC2SigmaSelectedMeasurementParameters.length;
              //this.uc2SigmaSelectedData.measurement_parameters.selected_values = this.measurementParametersGQLFileList;
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
          },
        });
    }

    if (parameter === 'point_parameters') {
      await this.dataCatService
        .getQueryUniques(onUC2UniquesPath, 'point_parameters', pageDetails)
        .subscribe({
          next: async (res: any) => {
            if (res.body['uniques']) {
              if (!this.point_parametersGQLFileList) {
                this.point_parametersGQLFileList = res.body['uniques'];
              } else {
                this.point_parametersGQLFileList = [
                  ...new Set([
                    ...res.body['uniques'],
                    ...this.point_parametersGQLFileList,
                  ]),
                ];
              }
              this.uc2SigmaSelectedData.point_parameters.file_path =
                onUC2UniquesPath;
              this.pointParametersSearch = this.point_parametersGQLFileList;
              this.isUC2SigmaPointParametersSelectAll =
                this.point_parametersGQLFileList.length ===
                this.UC2SigmaSelectedPointParameters.length;
              //this.uc2SigmaSelectedData.point_parameters.selected_values = this.point_parametersGQLFileList;
              //this.measurementStepGQLFileCount = res.body['rows_count'];
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
          },
        });
    }
  }

  async onUC2GenerateUniquesPagination(pageIndex: any) {
    // Ensure that pageIndex is valid (not empty or null)
    if (!pageIndex || pageIndex < 1) {
      console.error('Invalid page number:', pageIndex);
      return;
    }

    const pageDetails = {
      pageIndex: pageIndex - 1, // assuming your backend uses zero-indexed pages
      pageSize: 10, // Fixed page size
    };

    try {
      const res = await this.dataCatService
        .getQueryUniques(this.responsePathRun, 'run_parameters', pageDetails)
        .toPromise(); // Ensure it's only called once

      if (res.body['uniques']) {
        // Overwrite the existing data instead of appending
        this.runStepGQLFileList = res.body['uniques'];

        // Update other properties accordingly
        this.uc2SigmaSelectedData.run_parameters.file_path =
          this.responsePathRun;
        this.runParametersSearch = this.runStepGQLFileList;

        // Check if Select All should be enabled
        this.isUC2SigmaRunParametersSelectAll =
          this.runStepGQLFileList.length ===
          this.UC2SigmaSelectedRunParameters.length;
      }
    } catch (error) {
      this.toaster.error('Error in fetching data');
    }
  }

  async fdTraceSigmaUniques() {
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    await this.dataCatService
      .getQueryUniques(
        this.uc2SigmaMeasurementParametersPath,
        'point_parameters',
        pageDetails,
      )
      .subscribe({
        next: async (res: any) => {
          if (res.body['uniques']) {
            this.point_parametersGQLFileList = res.body['uniques'];
            //this.measurementStepGQLFileCount = res.body['rows_count'];
          }
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });
  }

  async UC2SigmaDownload() {
    this.isUC2SigmaDownloadCheck =
      this.uc2SigmaSelectedData.measurement_steps.selected_values.length > 0 ||
      this.uc2SigmaSelectedData.point_steps.selected_values.length > 0 ||
      this.uc2SigmaSelectedData.point_parameters.selected_values.length > 0 ||
      this.uc2SigmaSelectedData.measurement_parameters.selected_values.length >
        0 ||
      this.uc2SigmaSelectedData.wafer_parameters.selected_values.length > 0;
    if (this.isUC2SigmaDownloadCheck) {
      await this.dataCatService
        .sigmaDownloadData(
          this.sessionData.job_id,
          this.config,
          this.uc2SigmaSelectedData,
        )
        .subscribe({
          next: async (res: any) => {
            this.UC2SigmaDataPullStatus();
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching data');
          },
        });
    } else {
      this.toaster.error('Select Any One of Mandatory Values');
    }
  }

  UC2SigmaClearOptions() {
    this.uc2SigmaGenerateButton = false;
    this.UC2SigmaSelectedPointSteps = [];
    this.UC2SigmaSelectedPointParameters = [];
    this.UC2SigmaSelectedMeasurementParameters = [];
    this.UC2SigmaSelectedMeasurementSteps = [];
    this.UC2SigmaSelectedRunParameters = [];
    this.UC2SigmaSelectedWaferParameters = [];
    this.uc2SigmaSelectedData.measurement_steps.selected_values = [];
    this.uc2SigmaSelectedData.run_parameters.selected_values = [];
    this.uc2SigmaSelectedData.point_steps.selected_values = [];
    this.uc2SigmaSelectedData.point_parameters.selected_values = [];
    this.uc2SigmaSelectedData.measurement_parameters.selected_values = [];
    this.uc2SigmaSelectedData.wafer_parameters.selected_values = [];
    this.uc2SigmaSelectedData.gql_file_details.parquet_file_path = '';
    this.uc2SigmaSelectedData.gql_file_details.gql_file_path = '';
    this.uc2SigmaMeasumentStepsSubmitButton = true;
    this.uc2SigmaPointStepsSubmitButton = true;
    this.isUC2SigmaDownloadCheck = false;
    this.isUC2SigmaWaferParametersSelectAll = false;
    this.isUC2SigmaRunParametersSelectAll = false;
    this.isUC2SigmaPointParametersSelectAll = false;
    this.isUC2SigmaPointStepsSelectAll = false;
    this.isUC2SigmaMeasureParametersSelectAll = false;
    this.isUC2SigmaMeasurementStepsSelectAll = false;
    // this.uc2SigmaUploadButton = false;
    // this.isuc2SigmaResultPath = false;
  }

  UC2SigmaReset(fileInput: HTMLInputElement) {
    fileInput.value = '';
    this.uc2SigmaGenerateButton = false;
    this.UC2SigmaSelectedPointSteps = [];
    this.UC2SigmaSelectedPointParameters = [];
    this.UC2SigmaSelectedMeasurementParameters = [];
    this.UC2SigmaSelectedMeasurementSteps = [];
    this.UC2SigmaSelectedRunParameters = [];
    this.UC2SigmaSelectedWaferParameters = [];
    this.uc2SigmaSelectedData.measurement_steps.selected_values = [];
    this.uc2SigmaSelectedData.run_parameters.selected_values = [];
    this.uc2SigmaSelectedData.point_steps.selected_values = [];
    this.uc2SigmaSelectedData.point_parameters.selected_values = [];
    this.uc2SigmaSelectedData.measurement_parameters.selected_values = [];
    this.uc2SigmaSelectedData.wafer_parameters.selected_values = [];
    this.measurementStepGQLSearchList = [];
    this.measumentParametersSearch = [];
    this.pointStepsSearch = [];
    this.pointParametersSearch = [];
    this.runParametersSearch = [];
    this.waferParametersSearch = [];
    this.uc2SigmaSelectedData.gql_file_details.parquet_file_path = '';
    this.uc2SigmaSelectedData.gql_file_details.gql_file_path = '';
    this.measurementStepGQLFileList = [];
    this.measurementParametersGQLFileList = [];
    this.point_stepsGQLFileList = [];
    this.point_parametersGQLFileList = [];
    this.runStepGQLFileList = [];
    this.waferParametersGQLFileList = [];
    this.uc2SigmaMeasumentStepsSubmitButton = true;
    this.uc2SigmaPointStepsSubmitButton = true;
    this.uc2SigmaUploadButton = false;
    this.isuc2SigmaResultPath = false;
    this.isuc2SigmaResultFailed = false;
    this.isUC2SigmaDownloadCheck = false;
  }

  blockMatSelectSpace(event: KeyboardEvent) {
    if (event.key === ' ') {
      event.stopPropagation();
    }
  }

  async UC2SigmaDataPullStatus() {
    if (!this.isuc2SigmaDownloadPolling) {
      let status = await this.dataCatService.dataPullStatus(
        this.sessionData.job_id,
      );
      if (
        status.current_stage_status !== 'SUCCESS' &&
        status.current_stage_status !== 'FAILED'
      ) {
        if (
          status?.job_status?.job_stage_status?.hasOwnProperty(
            'progress_percentage',
          )
        ) {
          this.uc2SigmaLoadPercentage =
            status?.job_status?.job_stage_status?.progress_percentage;
          if (this.uc2SigmaLoadPercentage !== 100) {
            this.showPolling = true;
            this.pollingPercentage = this.uc2SigmaLoadPercentage;
            this.pollingMsg =
              status?.job_status?.job_stage_status?.progress_message;
          } else {
            this.showPolling = false;
          }
        }
        setTimeout(() => {
          this.UC2SigmaDataPullStatus();
        }, 2000);
      }
      if (
        status.fd_data_pull_job_status === 'IDLE' &&
        status.current_stage_status === 'SUCCESS'
      ) {
        this.UC2SigmaResultFetch();
      }
    }
  }

  async UC2SigmaResultFetch() {
    //We can use getFDContextApplyFilterStatus, No need to change
    let applyUC2SigmaResult =
      await this.dataCatService.getFDContextApplyFilterStatus(
        this.sessionData.job_id,
        this.uc2SigmaStage,
      );
    this.showPolling = false;
    if (applyUC2SigmaResult) {
      this.isuc2SigmaResultPath = true;
      this.uc2SigmaResultPath =
        applyUC2SigmaResult.current_stage_results?.uc2_sigma_data.file_path;
      this.isUC2SigmaDownloadCheck = false;
      this.isuc2SigmaResultFailed = false;
      //this.config['traveler_ids']['file_path'] = this.travelerIdQueryFilePath;
    }
  }

  uc2SigmaDataChange(event: Event, parameter: any) {
    if (parameter === 'point_parameters') {
      this.uc2SigmaSelectedData.point_parameters.selected_values = event;
      this.UC2SigmaSelectedPointParameters = event;
      this.isUC2SigmaPointParametersSelectAll =
        this.point_parametersGQLFileList.length ===
        this.UC2SigmaSelectedPointParameters.length;
      this.isUC2SigmaDownloadCheck = true;
    }
    if (parameter === 'point_steps') {
      this.isUC2SigmaDownloadCheck = true;
      this.uc2SigmaPointStepsSubmitButton = false;
      this.uc2SigmaSelectedData.point_steps.selected_values = event;
      this.UC2SigmaSelectedPointSteps = event;
      this.isUC2SigmaPointStepsSelectAll =
        this.point_stepsGQLFileList.length ===
        this.UC2SigmaSelectedPointSteps.length;
    }
    if (parameter === 'measurement_parameters') {
      this.isUC2SigmaDownloadCheck = true;
      this.uc2SigmaSelectedData.measurement_parameters.selected_values = event;
      this.UC2SigmaSelectedMeasurementParameters = event;
      this.isUC2SigmaMeasureParametersSelectAll =
        this.measurementParametersGQLFileList.length ===
        this.UC2SigmaSelectedMeasurementParameters.length;
    }
    if (parameter === 'measurement_steps') {
      this.isUC2SigmaDownloadCheck = true;
      this.uc2SigmaMeasumentStepsSubmitButton = false;
      this.uc2SigmaSelectedData.measurement_steps.selected_values = event;
      this.UC2SigmaSelectedMeasurementSteps = event;
      this.isUC2SigmaMeasurementStepsSelectAll =
        this.measurementStepGQLFileList.length ===
        this.UC2SigmaSelectedMeasurementSteps.length;
    }
    if (parameter === 'run_parameters') {
      this.uc2SigmaSelectedData.run_parameters.selected_values = event;
      this.UC2SigmaSelectedRunParameters = event;
      this.isUC2SigmaRunParametersSelectAll =
        this.runStepGQLFileList.length ===
        this.UC2SigmaSelectedRunParameters.length;
    }
    if (parameter === 'wafer_parameters') {
      this.isUC2SigmaDownloadCheck = true;
      this.uc2SigmaSelectedData.wafer_parameters.selected_values = event;
      this.UC2SigmaSelectedWaferParameters = event;
      this.isUC2SigmaWaferParametersSelectAll =
        this.waferParametersGQLFileList.length ===
        this.UC2SigmaSelectedWaferParameters.length;
    }
  }

  async onUC2SigmaMeasurementStepsSubmit() {
    await this.dataCatService
      .onUC2SigmaMeasurementSteps(
        this.sessionData.job_id,
        this.config,
        this.uc2SigmaSelectedData,
      )
      .subscribe({
        next: async (res: any) => {
          let responseMeasurePath =
            res.body['measurement_parameters'].file_path;
          let responseWaferPath = res.body['wafer_parameters'].file_path;
          this.onUC2GenerateUniques(
            responseMeasurePath,
            'measurement_parameters',
          );
          this.onUC2GenerateUniques(responseWaferPath, 'wafer_parameters');
          this.toaster.success(
            'Measurement Parameters and Wafer Parameters data fetched successfully',
          );
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });
  }

  async onUC2SigmaPointStepsSubmit() {
    await this.dataCatService
      .onUC2SigmaPointParameters(
        this.sessionData.job_id,
        this.config,
        this.uc2SigmaSelectedData,
      )
      .subscribe({
        next: async (res: any) => {
          let responsePointPath = res.body['point_parameters'].file_path;
          this.onUC2GenerateUniques(responsePointPath, 'point_parameters');
          this.toaster.success('Point Parameters data fetched successfully');
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });
  }

  UC2MeasumentStepSearch(event: any) {
    let searchTerm = event.trim();
    let searchResults = [];
    if (searchTerm) {
      // this.measurementStepGQLFileList = this.measurementStepGQLFileList.filter((session: any) => {
      //   console.log("the session is : ", session);
      //   if (session.toLowerCase() == this.UC2SigmaMeasurementStepsSearchTerm.toLowerCase()) {
      //     return session;
      //   }
      // });
      searchResults = this.measurementStepGQLSearchList.filter(
        (measureStep: any) => {
          let input = measureStep.toLowerCase();
          if (input.includes(searchTerm.toLowerCase())) {
            return input.includes(searchTerm.toLowerCase());
          } else {
            return false;
          }
        },
      );
      this.measurementStepGQLFileList = searchResults;
    } else {
      this.measurementStepGQLFileList = this.measurementStepGQLSearchList;
    }
  }

  UC2MeasumentParametersSearch(event: any) {
    let searchTerm = event.trim();
    let searchResults = [];
    if (searchTerm) {
      searchResults = this.measumentParametersSearch.filter(
        (parameter: any) => {
          let input = parameter.toLowerCase();
          if (input.includes(searchTerm.toLowerCase())) {
            return input.includes(searchTerm.toLowerCase());
          } else {
            return false;
          }
        },
      );
      this.measurementParametersGQLFileList = searchResults;
    } else {
      this.measurementParametersGQLFileList = this.measumentParametersSearch;
    }
  }

  UC2PointStepsSearch(event: any) {
    let searchTerm = event.trim();
    let searchResults = [];
    if (searchTerm) {
      searchResults = this.pointStepsSearch.filter((pointStep: any) => {
        let input = pointStep.toLowerCase();
        if (input.includes(searchTerm.toLowerCase())) {
          return input.includes(searchTerm.toLowerCase());
        } else {
          return false;
        }
      });
      this.point_stepsGQLFileList = searchResults;
    } else {
      this.point_stepsGQLFileList = this.pointStepsSearch;
    }
  }

  UC2RunParametersSearch(event: any) {
    let searchTerm = event.trim();
    let searchResults = [];
    if (searchTerm) {
      searchResults = this.runParametersSearch.filter((parameter: any) => {
        let input = parameter.toLowerCase();
        if (input.includes(searchTerm.toLowerCase())) {
          return input.includes(searchTerm.toLowerCase());
        } else {
          return false;
        }
      });
      this.runStepGQLFileList = searchResults;
    } else {
      this.runStepGQLFileList = this.runParametersSearch;
    }
  }

  UC2PointParametersSearch(event: any) {
    let searchTerm = event.trim();
    let searchResults = [];
    if (searchTerm) {
      searchResults = this.pointParametersSearch.filter((parameter: any) => {
        let input = parameter.toLowerCase();
        if (input.includes(searchTerm.toLowerCase())) {
          return input.includes(searchTerm.toLowerCase());
        } else {
          return false;
        }
      });
      this.point_parametersGQLFileList = searchResults;
    } else {
      this.point_parametersGQLFileList = this.pointParametersSearch;
    }
  }

  UC2WaferParametersSearch(event: any) {
    let searchTerm = event.trim();
    let searchResults = [];
    if (searchTerm) {
      searchResults = this.waferParametersSearch.filter((parameter: any) => {
        let input = parameter.toLowerCase();
        if (input.includes(searchTerm.toLowerCase())) {
          return input.includes(searchTerm.toLowerCase());
        } else {
          return false;
        }
      });
      this.waferParametersGQLFileList = searchResults;
    } else {
      this.waferParametersGQLFileList = this.waferParametersSearch;
    }
  }

  UC2SigmaMeasureStepsAddInput() {
    if (this.uc2SigmaMeasurementStepsInputValue) {
      this.measurementStepGQLFileList = [
        ...new Set([
          ...this.measurementStepGQLFileList,
          this.uc2SigmaMeasurementStepsInputValue,
        ]),
      ];
      if (
        this.measurementStepGQLFileList.length >
        this.measurementStepGQLSearchList.length
      ) {
        this.UC2SigmaSelectedMeasurementSteps = [
          ...this.UC2SigmaSelectedMeasurementSteps,
          this.uc2SigmaMeasurementStepsInputValue,
        ];
        this.toaster.success('Input Added Succussfully');
        this.uc2SigmaSelectedData.measurement_steps.selected_values =
          this.UC2SigmaSelectedMeasurementSteps;
        this.isUC2SigmaDownloadCheck = true;
      }
      this.measurementStepGQLSearchList = [
        ...new Set([
          ...this.measurementStepGQLSearchList,
          this.uc2SigmaMeasurementStepsInputValue,
        ]),
      ];
      this.uc2SigmaMeasurementStepsInputValue = '';
    }
  }

  UC2SigmaMeasureStepsClearSearch() {
    this.uc2SigmaMeasurementStepsInputValue = '';
  }

  UC2SigmaMeasureParametersAddInput() {
    if (this.uc2SigmaMeasurementParametersInputValue) {
      this.measurementParametersGQLFileList = [
        ...new Set([
          ...this.measurementParametersGQLFileList,
          this.uc2SigmaMeasurementParametersInputValue,
        ]),
      ];
      if (
        this.measurementParametersGQLFileList.length >
        this.measumentParametersSearch.length
      ) {
        this.UC2SigmaSelectedMeasurementParameters = [
          ...this.UC2SigmaSelectedMeasurementParameters,
          this.uc2SigmaMeasurementParametersInputValue,
        ];
        this.toaster.success('Input Added Succussfully');
        this.uc2SigmaSelectedData.measurement_parameters.selected_values =
          this.UC2SigmaSelectedMeasurementParameters;
        this.isUC2SigmaDownloadCheck = true;
      }
      this.measumentParametersSearch = [
        ...new Set([
          ...this.measumentParametersSearch,
          this.uc2SigmaMeasurementParametersInputValue,
        ]),
      ];
      this.uc2SigmaMeasurementParametersInputValue = '';
    }
  }

  UC2SigmaMeasureParametersClearSearch() {
    this.uc2SigmaMeasurementParametersInputValue = '';
  }

  UC2SigmaPointStepsAddInput() {
    if (this.uc2SigmaPointStepsInputValue) {
      this.point_stepsGQLFileList = [
        ...new Set([
          ...this.point_stepsGQLFileList,
          this.uc2SigmaPointStepsInputValue,
        ]),
      ];
      if (this.point_stepsGQLFileList.length > this.pointStepsSearch.length) {
        this.UC2SigmaSelectedPointSteps = [
          ...this.UC2SigmaSelectedPointSteps,
          this.uc2SigmaPointStepsInputValue,
        ];
        this.toaster.success('Input Added Succussfully');
        this.uc2SigmaSelectedData.point_steps.selected_values =
          this.UC2SigmaSelectedPointSteps;
        this.isUC2SigmaDownloadCheck = true;
      }
      this.pointStepsSearch = [
        ...new Set([
          ...this.pointStepsSearch,
          this.uc2SigmaPointStepsInputValue,
        ]),
      ];
      this.uc2SigmaPointStepsInputValue = '';
    }
  }

  UC2SigmaPointStepsClearSearch() {
    this.uc2SigmaPointStepsInputValue = '';
  }

  UC2SigmaPointParametersAddInput() {
    if (this.uc2SigmaPointParametersInputValue) {
      this.point_parametersGQLFileList = [
        ...new Set([
          ...this.point_parametersGQLFileList,
          this.uc2SigmaPointParametersInputValue,
        ]),
      ];
      if (
        this.point_parametersGQLFileList.length >
        this.pointParametersSearch.length
      ) {
        this.UC2SigmaSelectedPointParameters = [
          ...this.UC2SigmaSelectedPointParameters,
          this.uc2SigmaPointParametersInputValue,
        ];
        this.toaster.success('Input Added Succussfully');
        //Adding data into payload
        this.uc2SigmaSelectedData.point_parameters.selected_values =
          this.UC2SigmaSelectedPointParameters;
        this.isUC2SigmaDownloadCheck = true;
      }
      this.pointParametersSearch = [
        ...new Set([
          ...this.pointParametersSearch,
          this.uc2SigmaPointParametersInputValue,
        ]),
      ];
      this.uc2SigmaPointParametersInputValue = '';
    }
  }

  UC2SigmaPointParametersClearSearch() {
    this.uc2SigmaPointParametersInputValue = '';
  }

  UC2SigmaRunParametersAddInput() {
    if (this.uc2SigmaRunParametersInputValue) {
      this.runStepGQLFileList = [
        ...new Set([
          ...this.runStepGQLFileList,
          this.uc2SigmaRunParametersInputValue,
        ]),
      ];
      if (this.runStepGQLFileList.length > this.runParametersSearch.length) {
        this.UC2SigmaSelectedRunParameters = [
          ...this.UC2SigmaSelectedRunParameters,
          this.uc2SigmaRunParametersInputValue,
        ];
        this.toaster.success('Input Added Succussfully');
        //Adding data into payload
        this.uc2SigmaSelectedData.run_parameters.selected_values =
          this.UC2SigmaSelectedRunParameters;
      }
      this.runParametersSearch = [
        ...new Set([
          ...this.runParametersSearch,
          this.uc2SigmaRunParametersInputValue,
        ]),
      ];
      this.uc2SigmaRunParametersInputValue = '';
    }
  }

  UC2SigmaRunParametersClearSearch() {
    this.uc2SigmaRunParametersInputValue = '';
  }

  UC2SigmaWaferParametersAddInput() {
    if (this.uc2SigmaWaferParametersInputValue) {
      this.waferParametersGQLFileList = [
        ...new Set([
          ...this.waferParametersGQLFileList,
          this.uc2SigmaWaferParametersInputValue,
        ]),
      ];
      if (
        this.waferParametersGQLFileList.length >
        this.waferParametersSearch.length
      ) {
        this.UC2SigmaSelectedWaferParameters = [
          ...this.UC2SigmaSelectedWaferParameters,
          this.uc2SigmaWaferParametersInputValue,
        ];
        this.toaster.success('Input Added Succussfully');
        //Adding data into payload
        this.uc2SigmaSelectedData.wafer_parameters.selected_values =
          this.UC2SigmaSelectedWaferParameters;
        this.isUC2SigmaDownloadCheck = true;
      }
      this.waferParametersSearch = [
        ...new Set([
          ...this.waferParametersSearch,
          this.uc2SigmaWaferParametersInputValue,
        ]),
      ];
      this.uc2SigmaWaferParametersInputValue = '';
    }
  }

  UC2SigmaWaferParametersClearSearch() {
    this.uc2SigmaWaferParametersInputValue = '';
  }

  UC2SigmaMeasurementStepsSelectAll() {
    if (this.isUC2SigmaMeasurementStepsSelectAll) {
      this.UC2SigmaSelectedMeasurementSteps = [
        ...this.measurementStepGQLFileList,
      ];
    } else {
      this.UC2SigmaSelectedMeasurementSteps = [];
    }
  }

  UC2SigmaMeasurementParametersSelectAll() {
    if (this.isUC2SigmaMeasureParametersSelectAll) {
      this.UC2SigmaSelectedMeasurementParameters = [
        ...this.measurementParametersGQLFileList,
      ];
    } else {
      this.UC2SigmaSelectedMeasurementParameters = [];
    }
  }

  UC2SigmaPointStepsSelectAll() {
    if (this.isUC2SigmaPointStepsSelectAll) {
      this.UC2SigmaSelectedPointSteps = [...this.point_stepsGQLFileList];
    } else {
      this.UC2SigmaSelectedPointSteps = [];
    }
  }

  UC2SigmaPointParametersSelectAll() {
    if (this.isUC2SigmaPointParametersSelectAll) {
      this.UC2SigmaSelectedPointParameters = [
        ...this.point_parametersGQLFileList,
      ];
    } else {
      this.UC2SigmaSelectedPointParameters = [];
    }
  }

  UC2SigmaRunParametersSelectAll() {
    if (this.isUC2SigmaRunParametersSelectAll) {
      this.UC2SigmaSelectedRunParameters = [...this.runStepGQLFileList];
    } else {
      this.UC2SigmaSelectedRunParameters = [];
    }
  }

  UC2SigmaWaferParametersSelectAll() {
    if (this.isUC2SigmaWaferParametersSelectAll) {
      this.UC2SigmaSelectedWaferParameters = [
        ...this.waferParametersGQLFileList,
      ];
    } else {
      this.UC2SigmaSelectedWaferParameters = [];
    }
  }

  async onStepIdClick(
    index: number,
    repopulate: boolean,
    override_file_path: any,
  ) {
    this.isLoading = true;
    let file_path = repopulate
      ? override_file_path
      : this.config.step_ids.file_path;
    let selected_recipe_names = this.config.selectedRecipeNames[index];
    let selected_tool_ids = this.config.uC2SelectedToolIds[index];

    try {
      const response = await this.dataCatService.generateStepIds(
        file_path,
        selected_recipe_names,
        selected_tool_ids,
      );
      if (response && response.body) {
        const fetchedStepIds = response.body.uniques || [];

        // Merge with existing filteredStepIdDropdownList to avoid duplicates
        this.filteredStepIdDropdownList[index] = [...fetchedStepIds];
        this.filteredStepIdDropdownSearchList[index] =
          this.filteredStepIdDropdownList[index];
        if (repopulate == false) {
          this.uC2SelectedStepIds[index] = [];
          this.isStepIdAllSelected[index] = false;
          this.uC2FdTraceAggrSelectedSensors[index] = [];
          this.isSensorAllSelected[index] = false;
        }
        this.isUC2TraceStepIdsValue = true;
      } else {
        this.filteredStepIdDropdownList[index] = [];
        this.filteredStepIdDropdownSearchList[index] = [];
      }
    } catch (error) {
      console.error('Error fetching Step IDs:', error);
      this.filteredStepIdDropdownList = [];
      this.filteredStepIdDropdownSearchList = [];
    } finally {
      this.isLoading = false;
    }
  }

  onStepIdSelectionChange(index: number) {
    this.config.step_ids.selected_values = this.uC2SelectedStepIds;
    if (
      this.uC2SelectedStepIds[index].length ===
      this.filteredStepIdDropdownList[index].length
    ) {
      this.isStepIdAllSelected[index] = true;
    } else {
      this.isStepIdAllSelected[index] = false;
    }
    this.updateSelectAllStepIds(index);
  }

  updateSelectAllStepIds(index: number) {
    this.isStepIdAllSelected[index] =
      this.uC2SelectedStepIds[index].length ===
      this.filteredStepIdDropdownList[index].length;
  }

  toggleStepIdsSelectAll(index: number) {
    if (this.isStepIdAllSelected[index]) {
      this.uC2SelectedStepIds[index] = [
        ...this.filteredStepIdDropdownList[index],
      ];
    } else {
      this.uC2SelectedStepIds = [];
    }
    this.config.step_ids.selected_values = this.uC2SelectedStepIds;
    this.updateSelectAllStepIds(index);
  }

  onSensorSelectionChange(index: number) {
    this.config.sensors.selected_values = this.uC2FdTraceAggrSelectedSensors;
    if (
      this.uC2FdTraceAggrSelectedSensors[index].length ===
      this.filteredSensorDropdownList.length
    ) {
      this.isSensorAllSelected[index] = true;
    } else {
      this.isSensorAllSelected[index] = false;
    }
  }

  // Toggle Select All for sensors
  toggleSensorsSelectAll(index: number) {
    if (this.isSensorAllSelected[index]) {
      this.uC2FdTraceAggrSelectedSensors[index] = [
        ...this.filteredSensorDropdownList[index],
      ];
    } else {
      this.uC2FdTraceAggrSelectedSensors[index] = [];
    }
    this.config.sensors.selected_values = this.uC2FdTraceAggrSelectedSensors; // Update config when toggling select all
  }

  updateSelectAllSensors(index: number) {
    this.isSensorAllSelected[index] =
      this.uC2FdTraceAggrSelectedSensors[index].length ===
      this.filteredSensorDropdownList[index].length;
  }

  // Method to filter sensors based on search
  filterSensors(index: number) {
    let result = [];
    if (this.searchSensor) {
      result = this.filteredSensorDropdownSearchList[index].filter(
        (stepSensor: any) => {
          let sensor = stepSensor.toLowerCase();
          let searchTerm = this.searchSensor.toLowerCase();
          if (sensor.includes(searchTerm)) {
            return sensor.includes(searchTerm);
          } else {
            return false;
          }
        },
      );
      this.filteredSensorDropdownList[index] = result;
    } else {
      this.filteredSensorDropdownList[index] =
        this.filteredSensorDropdownSearchList[index];
    }
  }

  async onStepIdbtnClick(
    index: any,
    repopulate: boolean,
    override_file_path: any,
  ) {
    this.isLoading = true;

    let file_path = repopulate
      ? override_file_path
      : this.config.step_ids.file_path;
    let selected_recipe_names = this.config.selectedRecipeNames[index];
    let selected_tool_ids = this.config.uC2SelectedToolIds[index];
    let selected_step_ids = this.config.step_ids.selected_values[index];

    try {
      const response = await this.dataCatService.generateSensors(
        file_path,
        selected_recipe_names,
        selected_tool_ids,
        selected_step_ids,
      );
      if (response && response.body) {
        const fetchedSensors = response.body.uniques || [];

        // Merge fetched sensors with existing filteredSensorDropdownList to avoid duplicates
        this.filteredSensorDropdownList[index] = [
          ...fetchedSensors.filter(
            (sensor: any) => !this.filteredSensorDropdownList.includes(sensor),
          ),
        ];
        this.filteredSensorDropdownSearchList[index] =
          this.filteredSensorDropdownList[index];
        if (repopulate == false) {
          this.uC2FdTraceAggrSelectedSensors[index] = [];
          this.isSensorAllSelected[index] = false;
        }
        this.isUC2TraceSensorsValue = true;
      } else {
        this.filteredSensorDropdownList[index] = [];
        this.filteredSensorDropdownSearchList[index] = [];
      }
    } catch (error) {
      console.error('Error fetching Sensors:', error);
      this.filteredSensorDropdownList = [];
      this.filteredSensorDropdownSearchList = [];
    } finally {
      this.isLoading = false;
    }
  }

  checkLotIds() {
    let generatedList: any = [];
    this.selectedLotIds.forEach((lotId: any) => {
      let patterns = this.generateWaferIds(lotId);
      generatedList = [...generatedList, ...patterns];
    });
    this.waferIdsDropdownList = generatedList;
    this.waferIdsDropdownCount = generatedList.length;
  }

  generateWaferIds(input: string) {
    let parts = input.split('.');
    let xxxx = parts[0].slice(-4); // Extract the last 4 digits before the period
    let patternArray = [];

    // Generate the pattern xxxx-01, xxxx-02, ..., xxxx-25
    for (let i = 1; i <= 25; i++) {
      let formattedNumber = i.toString().padStart(2, '0');
      patternArray.push(`${xxxx}-${formattedNumber}`);
    }

    return patternArray;
  }

  async UC2FDAggSourceDataPreview(sourceName: any): Promise<void> {
    let filePaths = await this.dataCatService.getUC2SigmaTabularFiles(
      this.resultDataFilePath,
    );
    const dialogRef = this.dialog.open(UC2SigmaDataPreviewComponent, {
      width: '90%',
      height: '90%',
      data: { paths: filePaths, dataSourceName: sourceName },
    });

    dialogRef.afterClosed().subscribe(async (result) => {});
  }

  async UC2DataSourceDataPreview(sourceName: any, type: string): Promise<void> {
    let path;
    if (type === 'uc2') {
      path = this.uc2SigmaResultPath;
    }
    if (type === 'uc3') {
      path = this.uc3SigmaResultPath;
    }
    let filePaths = await this.dataCatService.getUC2SigmaTabularFiles(path);
    const dialogRef = this.dialog.open(UC2SigmaDataPreviewComponent, {
      width: '90%',
      height: '90%',
      data: { paths: filePaths, dataSourceName: sourceName },
    });

    dialogRef.afterClosed().subscribe(async (result) => {});
  }

  async UC3ProbeDataPreview(sourceName: any): Promise<void> {
    let filePaths = await this.dataCatService.getUC2SigmaTabularFiles(
      this.uc3ProbeResultPath,
    );
    const dialogRef = this.dialog.open(UC2SigmaDataPreviewComponent, {
      width: '90%',
      height: '90%',
      data: { paths: filePaths, dataSourceName: sourceName },
    });

    dialogRef.afterClosed().subscribe(async (result) => {});
  }

  uc3SigmaMetroStepsClick(index: number) {
    if (this.selectedTravelerSteps) {
      this.uc3SigmaMetroStepPrefixList = Array.from(
        new Set(
          this.uc3SigmaMetroStepPrefixListGet.map((step: any) => {
            const prefix = step.split('-')[0]; // Extract prefix from step ID
            const description =
              this.uc3SigmaMetroStepPrefixObj[prefix] || 'Unknown'; // Check if prefix exists in the object
            return `${prefix} (${description})`;
          }),
        ),
      );
      // this.uc3SigmaMetroStepPrefixList = Object.keys(this.uc3SigmaMetroStepPrefixObj);
      this.uc3SigmaMetroStepsOptionsClicked(index);
    } else this.toaster.error('Please select Traveler Steps first');
  }

  addNewMetroStepsInput(index: number) {
    if (this.uc3SigmaMetroStepsAddNew.trim()) {
      this.uc3SigmaMetroStepsInputValue = this.uc3SigmaMetroStepsAddNew;
      this.uc3SigmaMetroStepPrefixList.push(this.uc3SigmaMetroStepsAddNew);
      this.uc3SigmaMetroStepsInputList = [...this.uc3SigmaMetroStepPrefixList]; //Storing input values
      this.uc3SigmaMetroStepsAddNew = '';
    }
  }

  clearMetroStepsInput() {
    this.uc3SigmaMetroStepsAddNew = '';
  }

  uc3SigmaMetroStepsSelectAll(event: MatCheckboxChange, index: number) {
    if (event.checked) {
      this.uc3SigmaMetroStepsSelected[index] = [
        ...this.filtereduc3SigmaMetroStepPrefixList.map(
          (item) => item.split(' ')[0],
        ),
      ];
    } else {
      this.uc3SigmaMetroStepsSelected[index] = [];
    }
  }

  onSensorsClick() {
    this.config.sensors.selected_values = this.uC2FdTraceAggrSelectedSensors;
  }

  async finalAggregateData() {
    try {
      const response = await this.dataCatService.finalaggregateData(
        this.sessionData.job_id,
        this.config,
      );
      if (response.status == 201) {
        setTimeout(() => {
          this.FinalDataContextDataPullStatus();
        }, 2000);
        this.isUC2FDGenerateButton = true;
        this.isGenerating = true;
      }
    } catch (error) {
      console.error('Error fetching step IDs and sensors:', error);
      this.sensorDropdownList = [];
      this.stepIdDropdownList = [];
    }
  }

  toggleAddToolInput(index: number) {
    this.showAddToolInput[index] = !this.showAddToolInput[index];
  }

  // Toggle Add Step ID Input
  toggleAddStepIdInput(index: number) {
    this.showAddStepIdInput[index] = !this.showAddStepIdInput[index];
  }

  // Toggle Add Sensor Input
  toggleAddSensorInput(index: number) {
    this.showAddSensorInput[index] = !this.showAddSensorInput[index];
  }

  // Add new tool
  addNewTool(index: number) {
    if (this.newToolName.trim() && this.newToolId.trim()) {
      const newTool = {
        TOOL_NAME: this.newToolName.trim(),
        TOOL_ID: Number(this.newToolId.trim()),
      };

      // Add the new tool to the specific group and allTools
      this.toolGroups[index].tools.push(newTool);
      this.allTools.push(newTool);
      // Also add the new tool to filteredTools if it doesn't already exist
      if (
        !this.filteredTools[index].some(
          (tool: any) => tool.TOOL_ID === newTool.TOOL_ID,
        )
      ) {
        this.filteredTools[index].push(newTool);
      }

      this.newToolName = '';
      this.newToolId = '';
      this.showAddToolInput[index] = false;
    }
  }

  // Add new Step ID
  addNewStepId(index: number) {
    if (this.newStepId.trim()) {
      const newStepId = this.newStepId.trim();

      // Add the new Step ID to the stepIds array for the specific tool group
      this.toolGroups[index].stepIds.push(newStepId);

      // Add the new Step ID to filteredStepIdDropdownList if it doesn't already exist
      if (!this.filteredStepIdDropdownList[index].includes(newStepId)) {
        this.filteredStepIdDropdownList[index].push(newStepId);
      }

      // Clear the input field and hide the input form
      this.newStepId = '';
      this.showAddStepIdInput[index] = false;
    }
  }

  // Add new Sensor
  addNewSensor(index: number) {
    if (this.newSensor.trim()) {
      const newSensor = this.newSensor.trim();

      // Add the new sensor to the sensors array for the specific tool group
      this.toolGroups[index].sensors.push(newSensor);

      // Add the new sensor to filteredSensorDropdownList if it doesn't already exist
      if (!this.filteredSensorDropdownList[index].includes(newSensor)) {
        this.filteredSensorDropdownList[index].push(newSensor);
      }

      // Clear the input field and hide the input form
      this.newSensor = '';
      this.showAddSensorInput[index] = false;
    }
  }

  generateToolId(): string {
    return Math.floor(Math.random() * 10000).toString();
  }

  onUC2RecipeSelectionChange(selectedRecipeIds: string[], index: number) {
    this.uC2FdselectedRecipeNames[index] = Array.from(
      new Set(this.uC2FdselectedRecipeNames[index]),
    );
    const allRecipesSelected = this.filteredRecipeNames.every((recipe) =>
      this.uC2FdselectedRecipeNames[index].includes(recipe.recipe_name),
    );
    this.isRecipeSelectAll[index] = allRecipesSelected;
    if (this.uC2FdselectedRecipeNames[index].length === 0) {
      this.isRecipeSelectAll[index] = false;
    } else if (
      this.uC2FdselectedRecipeNames[index].length > 0 &&
      !allRecipesSelected
    ) {
      this.isRecipeSelectAll[index] = false;
    }

    this.updateConfigWithSelectedRecipes();
  }

  filterRecipes(index: number) {
    let result = [];
    if (this.searchRecipeName) {
      result = this.recipes.filter((recipe: { recipe_name: string }) => {
        let recipeName = recipe.recipe_name.toLowerCase();
        let searchTerm = this.searchRecipeName.toLowerCase();
        if (recipeName.includes(searchTerm)) {
          return recipeName.includes(searchTerm);
        } else {
          return false;
        }
      });
      this.filteredRecipeNames = result;
    } else {
      this.filteredRecipeNames = this.recipes;
    }
    //this.updateRecipeSelectAllState(index);
  }

  toggleRecipeSelectAll(index: number) {
    if (this.isRecipeSelectAll[index]) {
      this.uC2FdselectedRecipeNames[index] = this.filteredRecipeNames.map(
        (recipe) => recipe.recipe_name,
      );
    } else {
      this.uC2FdselectedRecipeNames[index] = [];
    }
    this.updateRecipeSelectAllState(index);
    this.updateConfigWithSelectedRecipes();
  }

  updateRecipeSelectAllState(index: number) {
    const allSelected =
      Array.isArray(this.uC2FdselectedRecipeNames[index]) &&
      this.filteredRecipeNames.every((recipe) =>
        this.uC2FdselectedRecipeNames[index].includes(recipe.recipe_name),
      );
    this.isRecipeSelectAll[index] = allSelected;
  }

  updateConfigWithSelectedRecipes() {
    this.config.selectedRecipeNames = this.uC2FdselectedRecipeNames;
  }

  toggleAddRecipeInput(index: number) {
    this.showAddRecipeInput[index] = !this.showAddRecipeInput[index];
  }

  async onRecipeClickHelpFunc(
    file_path: any,
    selected_recipe_names: any,
    index: number,
    repopulate: boolean,
  ) {
    try {
      const response = await this.dataCatService.generateToolIds(
        file_path,
        selected_recipe_names,
      );
      if (response && response.body) {
        this.allTools = response.body.data || [];

        // Merge with existing filteredTools, ensuring no duplicates
        this.filteredTools[index] = [
          ...this.allTools.filter(
            (tool) =>
              !this.filteredTools.some(
                (existingTool: any) => existingTool.TOOL_ID === tool.TOOL_ID,
              ),
          ),
        ];
        this.filteredToolsSearchList[index] = this.filteredTools[index];
        //this.updateSelectAllState(index);
        this.isUC2TraceToolsIdsValue = true;
        if (repopulate == false) {
          //this.uC2SelectedToolIds[index] = []
          this.isUC2ToolNameSelectAll[index] = false;
          this.uC2SelectedStepIds[index] = [];
          this.isStepIdAllSelected[index] = false;
          this.uC2FdTraceAggrSelectedSensors[index] = [];
          this.isSensorAllSelected[index] = false;
        } else {
          this.uC2SelectedToolIds[index] = [];
        }
        this.updateSelectAllState(index);
      } else {
        this.allTools = [];
        this.filteredTools[index] = [];
        this.filteredToolsSearchList[index] = [];
      }
    } catch (error) {
      this.allTools = [];
      this.filteredTools = [];
      this.filteredToolsSearchList = [];
    } finally {
      this.isLoading = false;
    }
  }

  async onRecipeClick(index: number) {
    this.isLoading = true;
    let file_path = this.config.tool_ids.file_path;
    let selected_recipe_names = this.config.selectedRecipeNames[index];
    await this.onRecipeClickHelpFunc(
      file_path,
      selected_recipe_names,
      index,
      false,
    );
  }

  filterTools(index: number) {
    let result = [];
    if (this.filterToolsSearchTerm) {
      result = this.filteredToolsSearchList[index].filter(
        (tool: { TOOL_NAME: any; TOOL_ID: any }) => {
          let toolName = tool.TOOL_NAME.toLowerCase();
          let toolID = tool.TOOL_ID.toString();
          let searchTerm = this.filterToolsSearchTerm;
          if (toolName.includes(searchTerm) || toolID.includes(searchTerm)) {
            return toolName.includes(searchTerm) || toolID.includes(searchTerm);
          } else {
            return false;
          }
        },
      );
      this.filteredTools[index] = result;
    } else {
      this.filteredTools[index] = this.filteredToolsSearchList[index];
    }
  }

  filterStepIds(index: number) {
    let result = [];
    if (this.searchStepId) {
      result = this.filteredStepIdDropdownSearchList[index].filter(
        (stepId: any) => {
          let searchTerm = this.searchStepId.toLowerCase();
          let filterStepId = stepId.toString();
          if (filterStepId.includes(searchTerm)) {
            return filterStepId.includes(searchTerm);
          } else {
            return false;
          }
        },
      );
      this.filteredStepIdDropdownList[index] = result;
    } else {
      this.filteredStepIdDropdownList[index] =
        this.filteredStepIdDropdownSearchList[index];
    }
  }

  saveMetroSteps(index: number) {
    let job_id = this.sessionData.job_id;
    this.config.uc3_sigma_metro_steps = this.uc3SigmaMetroStepsSelected;
    this.dataCatService
      .saveMetroSteps(this.config, job_id)
      .subscribe((res: any) => {
        try {
          if (res.body?.common_test_ids?.file_path) {
            let filePath = res.body?.common_test_ids?.file_path;
            this.filepathMetro = filePath;
            this.selectedCommontestidPath = filePath;

            let obj = {
              uc3_sigma_metro_steps: {
                file_path: '',
                selected_values: [],
              },
              common_test_ids: {
                file_path: filePath,
                selected_values: [],
              },
            };
            this.uc3SigmaFinalSelection[index] = obj;
            this.uc3SigmaFinalSelection[index]['uc3_sigma_metro_steps'][
              'selected_values'
            ].push(this.uc3SigmaMetroStepsSelected[index]);
            // this.dataCatService.getQueryUniques(
            //   filePath,
            //   'COMMON_TEST_ID', // TODO need to finalise the name
            //   pageDetails,
            // )
            // .subscribe({
            //   next: async (res: any) => {
            //     if (res.body['uniques']) {
            //       this.uc3CommonStepIds = res.body['uniques'];

            //     }
            //   },
            //   error: (err: any) => {
            //     this.toaster.error('Error in fetching data');
            //   },
            // });
          }
        } catch (error: any) {
          this.toaster.error(error);
        }
      });
  }

  uc3SigmaMetroStepsOptionsClicked(index: number) {
    if (this.uc3SigmaMetroStepsSelected[index]?.length > 0) {
      this.isUc3SigmaMetroSelectAll[index] =
        this.filtereduc3SigmaMetroStepPrefixList
          .map((item: any) => item.split(' ')[0])
          .every((step: any) =>
            this.uc3SigmaMetroStepsSelected[index].includes(step),
          );
    } else {
      this.isUc3SigmaMetroSelectAll[index] = false;
    }
  }

  uc3SigmaMetroRegionsClicked() {
    this.isUc3SigmaMetroRegionsSelectAll = this.uc3SigmaMetroRegionsList.every(
      (region: any) => this.uc3SigmaMetroRegionsSelected.includes(region),
    );
  }

  uc3SigmaMetroRegionsSelectAll(event: MatCheckboxChange) {
    this.uc3SigmaMetroRegionsSelected = event.checked
      ? this.uc3SigmaMetroRegionsList
      : [];
  }

  uc3SigmaDownload() {
    this.uc3SigmaSetDataSource();
    let job_id = this.sessionData.job_id;
    this.dataCatService
      .uc3DownloadPath(this.config, job_id)
      .subscribe(async (res: any) => {
        try {
          if (res.body) {
            this.UC3SigmaDataPullStatus();
          }
        } catch (error: any) {
          this.isUC3DownloadDisable = false;
          this.toaster.error(error);
        }
      });
  }

  async UC3ProbeModelPopUp() {
    // let filePaths = await this.dataCatService.getUC2SigmaTabularFiles(
    //   this.resultDataFilePath,
    // );
    let filePaths = '';
    const dialogRef = this.dialog.open(Uc3ProbeModelPopupComponent, {
      width: '80%',
      height: '90%',
      data: { paths: filePaths },
    });

    dialogRef.afterClosed().subscribe(async (result) => {
      if (result) {
        if (Array.isArray(result['selectedProbeValues'])) {
          this.selectedProbeColumns = [...result['selectedProbeValues']];
        } else {
          console.error(
            'selectedProbeValues is not iterable or not an array:',
            result['selectedProbeValues'],
          );
          this.selectedProbeColumns = []; // Default to an empty array if the value is invalid
        }

        this.upload_file_path = result['upload_file_path'] || ''; // Provide a fallback if upload_file_path is undefined or null
        this.config.uploaded_probe_data = {
          uploaded_file_path: this.upload_file_path,
        };
      }
    });
  }

  async uc3ProbeCheck(event: MatCheckboxChange) {
    this.isUC3ProbeChecked = event.checked;
    if (this.isUC3ProbeChecked) {
      this.probeReloadValues =
        await this.dataCatService.getFDContextApplyFilterStatus(
          this.sessionData.job_id,
          this.uc3ProbeDataPullStage,
        );
      if (this.probeReloadValues.current_stage_status === 'NOT_CONFIGURED') {
        console.log('not configured...');
      } else {
        this.UC3ProbeReloadResultFetch();
        if (this.probeReloadValues.current_stage_status === 'SUCCESS') {
          this.isuc3ProbeResultPath = true;
          this.uc3ProbeResultPath =
            this.probeReloadValues.current_stage_results?.probe_data.file_path;
          this.toaster.success('Data fetched successfully');
        } else if (this.probeReloadValues.current_stage_status === 'FAILED') {
          this.toaster.error('UC3 Probe Job Failed');
          this.isuc3ProbeReloadResultFailed = true;
        } else {
          this.ProboGenerateReloadDataPull();
        }
      }
    }
  }

  UC3ProbeReloadResultFetch() {
    if (this.probeReloadValues) {
      this.selectedParitoNames =
        this.probeReloadValues.current_stage_inputs?.paretoname.selected_values;
      this.paritoNames =
        this.probeReloadValues.current_stage_inputs?.paretoname.selected_values;
      this.searchParitoNames =
        this.probeReloadValues.current_stage_inputs?.paretoname.selected_values;
      this.selectedParitoTitle =
        this.probeReloadValues.current_stage_inputs?.paretotitle
          .selected_values;
      this.searchParitoTitle =
        this.probeReloadValues.current_stage_inputs?.paretotitle
          .selected_values;
      this.paritoTitle =
        this.probeReloadValues.current_stage_inputs?.paretotitle
          .selected_values;
      this.inputProbeRegionA =
        this.probeReloadValues.current_stage_inputs?.die_counts_per_region.A;
      this.inputProbeRegionB =
        this.probeReloadValues.current_stage_inputs?.die_counts_per_region.B;
      this.inputProbeRegionC =
        this.probeReloadValues.current_stage_inputs?.die_counts_per_region.C;
      this.inputProbeRegionD =
        this.probeReloadValues.current_stage_inputs?.die_counts_per_region.D;
      this.inputProbeRegionE =
        this.probeReloadValues.current_stage_inputs?.die_counts_per_region.E;

      this.config.paretotitle.selected_values =
        this.probeReloadValues.current_stage_inputs?.paretotitle
          .selected_values;
      this.config.paretoname.selected_values =
        this.probeReloadValues.current_stage_inputs?.paretoname.selected_values;
      this.config.die_counts_per_region.A =
        this.probeReloadValues.current_stage_inputs?.die_counts_per_region.A;
      this.config.die_counts_per_region.B =
        this.probeReloadValues.current_stage_inputs?.die_counts_per_region.B;
      this.config.die_counts_per_region.C =
        this.probeReloadValues.current_stage_inputs?.die_counts_per_region.C;
      this.config.die_counts_per_region.D =
        this.probeReloadValues.current_stage_inputs?.die_counts_per_region.D;
      this.config.die_counts_per_region.E =
        this.probeReloadValues.current_stage_inputs?.die_counts_per_region.E;
      this.config.paretotitle.file_path =
        this.probeReloadValues.current_stage_inputs?.paretotitle.file_path;
      this.config.paretoname.file_path =
        this.probeReloadValues.current_stage_inputs?.paretoname.file_path;
    }
  }

  async ProboGenerateReloadDataPull() {
    let status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.uc3ProbeLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.uc3ProbeLoadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.uc3ProbeLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
      }
      setTimeout(() => {
        this.ProboGenerateDataPull();
      }, 2000);
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.isuc3ProbeResultPath = true;
      this.uc3ProbeResultPath =
        this.probeReloadValues.current_stage_results?.probe_data.file_path;
      this.toaster.success('Data fetched successfully');
      this.isuc3ProbeReloadResultFailed = false;
      // let applyUC3ProbeaResult =
      // await this.dataCatService.getFDContextApplyFilterStatus(
      //   this.sessionData.job_id,
      //   this.uc3ProbeStage
      // );
      // this.showPolling = false;
      // if (applyUC3ProbeaResult) {
      //   this.uc3ProbeGenerateTitlePath = applyUC3ProbeaResult.current_stage_results?.paretotitle.file_path;
      //   this.config.paretotitle.file_path = applyUC3ProbeaResult.current_stage_results?.paretotitle.file_path;
      //   this.config.paretoname.file_path = applyUC3ProbeaResult.current_stage_results?.paretoname.file_path;
      //   this.uc3ProbeGenerateParitoNamesPath = applyUC3ProbeaResult.current_stage_results?.paretoname.file_path;
      // }
    }
  }

  async getProbeGenarate(event: Event) {
    event.stopPropagation();
    this.uc3ProbeGenerateButton = true;
    let response = await this.dataCatService.UC3ProbedataPullStatus(
      this.sessionData.job_id,
      this.config,
    );
    this.ProboGenerateDataPull();
  }

  async ProboGenerateDataPull() {
    let status = await this.dataCatService.dataPullStatus(
      this.sessionData.job_id,
    );
    if (
      status.current_stage_status !== 'SUCCESS' &&
      status.current_stage_status !== 'FAILED'
    ) {
      if (
        status?.job_status?.job_stage_status?.hasOwnProperty(
          'progress_percentage',
        )
      ) {
        this.uc3ProbeLoadPercentage =
          status?.job_status?.job_stage_status?.progress_percentage;
        if (this.uc3ProbeLoadPercentage !== 100) {
          this.showPolling = true;
          this.pollingPercentage = this.uc3ProbeLoadPercentage;
          this.pollingMsg =
            status?.job_status?.job_stage_status?.progress_message;
        } else {
          this.showPolling = false;
        }
      }
      setTimeout(() => {
        this.ProboGenerateDataPull();
      }, 2000);
    }
    if (
      status.fd_data_pull_job_status === 'IDLE' &&
      status.current_stage_status === 'SUCCESS'
    ) {
      this.GenarateParitoResultPath();
    }
  }

  async GenarateParitoResultPath() {
    let applyUC3ProbeaResult =
      await this.dataCatService.getFDContextApplyFilterStatus(
        this.sessionData.job_id,
        this.uc3ProbeStage,
      );
    this.showPolling = false;
    if (applyUC3ProbeaResult) {
      this.uc3ProbeGenerateTitlePath =
        applyUC3ProbeaResult.current_stage_results?.paretotitle.file_path;
      this.config.paretotitle.file_path =
        applyUC3ProbeaResult.current_stage_results?.paretotitle.file_path;
      this.config.paretoname.file_path =
        applyUC3ProbeaResult.current_stage_results?.paretoname.file_path;
      this.uc3ProbeGenerateParitoNamesPath =
        applyUC3ProbeaResult.current_stage_results?.paretoname.file_path;
      this.isuc3ProbeReloadResultFailed = false;
      this.UC3ProbeGenerateUniques();
    }
  }

  async UC3ProbeGenerateUniques() {
    let pageDetails = {
      pageIndex: 0,
      pageSize: 10,
    };
    const name = await this.dataCatService
      .getQueryUniques(
        this.uc3ProbeGenerateParitoNamesPath,
        'paretoname',
        pageDetails,
      )
      .subscribe({
        next: async (res: any) => {
          if (res.body['uniques']) {
            this.paritoNames = res.body['uniques'];
            this.searchParitoNames = res.body['uniques'];
          }
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });

    const title = await this.dataCatService
      .getQueryUniques(
        this.uc3ProbeGenerateTitlePath,
        'paretotitle',
        pageDetails,
      )
      .subscribe({
        next: async (res: any) => {
          if (res.body['uniques']) {
            this.paritoTitle = res.body['uniques'];
            this.searchParitoTitle = res.body['uniques'];
          }
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });
  }

  updateRegionA(event: Event) {
    this.config.die_counts_per_region.A = this.inputProbeRegionA;
  }
  updateRegionB(event: Event) {
    this.config.die_counts_per_region.B = this.inputProbeRegionB;
  }
  updateRegionC(event: Event) {
    this.config.die_counts_per_region.C = this.inputProbeRegionC;
  }
  updateRegionD(event: Event) {
    this.config.die_counts_per_region.D = this.inputProbeRegionD;
  }
  updateRegionE(event: Event) {
    this.config.die_counts_per_region.E = this.inputProbeRegionE;
  }

  updateParitoTitle(event: Event) {
    this.config.paretotitle.selected_values = this.selectedParitoTitle;
  }

  updateParitoNames(event: Event) {
    this.config.paretoname.selected_values = this.selectedParitoNames;
  }

  inputSearchParitoNames() {
    let result = [];
    if (this.inputParitoNames) {
      result = this.searchParitoNames.filter((item: any) => {
        let pName = item.toLowerCase();
        let searchTerm = this.inputParitoNames.toLowerCase();
        if (pName.includes(searchTerm)) {
          return pName.includes(searchTerm);
        } else {
          return false;
        }
      });
      this.paritoNames = result;
    } else {
      this.paritoNames = this.searchParitoNames;
    }
  }

  inputSearchParitoTitle() {
    let result = [];
    if (this.inputParitoTitle) {
      result = this.searchParitoTitle.filter((item: any) => {
        let tName = item.toLowerCase();
        let searchTerm = this.inputParitoTitle.toLowerCase();
        if (tName.includes(searchTerm)) {
          return tName.includes(searchTerm);
        } else {
          return false;
        }
      });
      this.paritoTitle = result;
    } else {
      this.paritoTitle = this.searchParitoTitle;
    }
  }

  ParitoTitleSelectAllChecked() {
    if (this.paritoTitle.length > 0 && this.selectedParitoTitle)
      return this.paritoTitle.every((id: any) =>
        this.selectedParitoTitle.includes(id),
      );
    return false;
  }

  UC3ProbeParitoTitleSelectAll(event: any) {
    if (event.checked) {
      this.selectedParitoTitle = this.paritoTitle.map((title: any) => title);
    } else {
      this.selectedParitoTitle = [];
    }
    this.config.paretotitle.selected_values = this.selectedParitoTitle;
  }

  ParitoTNamesSelectAllChecked() {
    if (this.paritoNames.length > 0 && this.selectedParitoNames)
      return this.paritoNames.every((id: any) =>
        this.selectedParitoNames.includes(id),
      );
    return false;
  }

  UC3ProbeParitoNamesSelectAll(event: any) {
    if (event.checked) {
      this.selectedParitoNames = this.paritoNames.map((title: any) => title);
    } else {
      this.selectedParitoNames = [];
    }
    this.config.paretoname.selected_values = this.selectedParitoNames;
  }

  toggleAddParitoNamesInput() {
    this.showAddParitoTitle = !this.showAddParitoTitle;
  }

  addNewParitoTitle() {
    if (this.newParitoTitle.trim()) {
      this.paritoTitle.push(this.newParitoTitle);

      this.newParitoTitle = '';
    }
  }
  clearParitoTitle() {
    this.newParitoTitle = '';
  }

  addNewParitoNames() {
    if (this.newparitoNames.trim()) {
      this.paritoNames.push(this.newparitoNames);
      this.newparitoNames = '';
    }
  }
  clearParitoNames() {
    this.newparitoNames = '';
  }

  /* Probe Download  */

  async getProbeDownload() {
    await this.dataCatService
      .ProbeDownloadData(this.sessionData.job_id, this.config)
      .subscribe({
        next: async (res: any) => {
          this.UC3ProbeDataPullStatus();
        },
        error: (err: any) => {
          this.toaster.error('Error in fetching data');
        },
      });

    // if (this.selectedProbeColumns) {
    //   await this.dataCatService
    //     .ProbeDownloadData(
    //       this.sessionData.job_id,
    //       this.config,

    //     )
    //     .subscribe({
    //       next: async (res: any) => {
    //         this.UC3ProbeDataPullStatus();
    //       },
    //       error: (err: any) => {
    //         this.toaster.error('Error in fetching data');
    //       },
    //     });
    // } else {
    //   this.toaster.error('Select Any One of Mandatory Values');
    // }
  }

  async UC3ProbeDataPullStatus() {
    if (!this.isuc3ProbeDownloadPolling) {
      let status = await this.dataCatService.dataPullStatus(
        this.sessionData.job_id,
      );
      if (
        status.current_stage_status !== 'SUCCESS' &&
        status.current_stage_status !== 'FAILED'
      ) {
        if (
          status?.job_status?.job_stage_status?.hasOwnProperty(
            'progress_percentage',
          )
        ) {
          this.uc3ProbeLoadPercentage =
            status?.job_status?.job_stage_status?.progress_percentage;
          if (this.uc3ProbeLoadPercentage !== 100) {
            this.showPolling = true;
            this.pollingPercentage = this.uc3ProbeLoadPercentage;
            this.pollingMsg =
              status?.job_status?.job_stage_status?.progress_message;
          } else {
            this.showPolling = false;
          }
        }
        setTimeout(() => {
          this.UC3ProbeDataPullStatus();
        }, 2000);
      }
      if (
        status.fd_data_pull_job_status === 'IDLE' &&
        status.current_stage_status === 'SUCCESS'
      ) {
        this.UC3ProbeResultFetch();
      }
    }
  }

  async UC3ProbeResultFetch() {
    let applyUC3ProbeaResult =
      await this.dataCatService.getFDContextApplyFilterStatus(
        this.sessionData.job_id,
        this.uc3ProbeDataPullStage,
      );
    this.showPolling = false;
    if (applyUC3ProbeaResult) {
      this.isuc3ProbeResultPath = true;
      this.uc3ProbeResultPath =
        applyUC3ProbeaResult.current_stage_results?.probe_data.file_path;
      this.uc3ProbePreviewButton = false;
    }
  }

  UC3ProbeReset() {
    this.inputProbeRegionA = 0;
    this.inputProbeRegionB = 0;
    this.inputProbeRegionC = 0;
    this.inputProbeRegionD = 0;
    this.inputProbeRegionE = 0;
    this.selectedParitoNames = '';
    this.selectedParitoTitle = '';
    this.config.die_counts_per_region.A = 0;
    this.config.die_counts_per_region.B = 0;
    this.config.die_counts_per_region.C = 0;
    this.config.die_counts_per_region.D = 0;
    this.config.die_counts_per_region.E = 0;
    this.config.paretoname.file_path = '';
    this.config.paretotitle.file_path = '';
    this.config.paretotitle.selected_values = [];
    this.config.paretoname.selected_values = [];
    this.config.uploaded_probe_data = { uploaded_file_path: '' };
    this.upload_file_path = '';
    this.uc3ProbeResultPath = '';
    this.isuc3ProbeResultPath = false;
    this.paritoTitle = [];
    this.paritoNames = [];
    this.uc3ProbeGenerateButton = false;
    this.uc3ProbePreviewButton = true;
  }

  async UC3SigmaDataPullStatus() {
    if (!this.isuc3SigmaDownloadPolling) {
      let status = await this.dataCatService.dataPullStatus(
        this.sessionData.job_id,
      );
      if (
        status.current_stage_status !== 'SUCCESS' &&
        status.current_stage_status !== 'FAILED'
      ) {
        if (
          status?.job_status?.job_stage_status?.hasOwnProperty(
            'progress_percentage',
          )
        ) {
          this.uc3SigmaLoadPercentage =
            status?.job_status?.job_stage_status?.progress_percentage;
          if (this.uc3SigmaLoadPercentage !== 100) {
            this.showPolling = true;
            this.pollingPercentage = this.uc3SigmaLoadPercentage;
            this.pollingMsg =
              status?.job_status?.job_stage_status?.progress_message;
          } else {
            this.showPolling = false;
          }
        }
        setTimeout(() => {
          this.UC3SigmaDataPullStatus();
        }, 2000);
      }
      if (
        status.fd_data_pull_job_status === 'IDLE' &&
        status.current_stage_status === 'SUCCESS'
      ) {
        this.UC3SigmaResultFetch();
      }
    }
  }

  async UC3SigmaResultFetch() {
    let applyUC3SigmaResult =
      await this.dataCatService.getFDContextApplyFilterStatus(
        this.sessionData.job_id,
        this.uc3SigmaStage,
      );
    this.showPolling = false;
    if (applyUC3SigmaResult) {
      this.isUC3SigmaResultPath = true;
      this.uc3SigmaResultPath =
        applyUC3SigmaResult.current_stage_results?.uc3_sigma_data?.file_path;
      this.isUC3SigmaDownloadCheck = false;
      this.isuc3SigmaResultFailed = false;
    }
  }

  extractPrefixesStartingWithOne(travelerSteps: string[]): string[] {
    const prefixes = travelerSteps
      .map((step) => step.split('-')[0]) // Extract the prefix before the hyphen
      .filter((prefix) => prefix.startsWith('1')); // Filter prefixes starting with '1'

    const uniquePrefixes = [...new Set(prefixes)]; // Remove duplicates
    return uniquePrefixes;
  }

  filterNamesWithPrefixOne(travelerSteps: string[]): string[] {
    return travelerSteps.filter((step) => step.startsWith('1'));
  }

  async uc3SigmaCheckReset() {
    if (this.selectedTravelerSteps && this.selectedTravelerSteps.length > 0) {
      this.prefixesStartingWithOne = this.extractPrefixesStartingWithOne(
        this.selectedTravelerSteps,
      );
      this.namesWithPrefixOne = this.filterNamesWithPrefixOne(
        this.selectedTravelerSteps,
      );
      this.config.cached_traveler_steps = this.namesWithPrefixOne;

      // this.uc3SigmaMetroStepPrefixListGet = this.namesWithPrefixOne;

      // this.uc3SigmaMetroStepPrefixList = Array.from(
      //   new Set(
      //     this.uc3SigmaMetroStepPrefixListGet.map((step: any) => {
      //       const prefix = step.split('-')[0]; // Extract prefix from step ID
      //       return `${prefix}`; // Return only the prefix without mapping to a description
      //     })
      //   )
      // );

      this.uc3SigmaMetroStepPrefixListGet = this.namesWithPrefixOne;
      this.uc3SigmaMetroStepPrefixList = Array.from(
        new Set(
          this.uc3SigmaMetroStepPrefixListGet.map((step: any) => {
            const prefix = step.split('-')[0]; // Extract prefix from step ID
            const description =
              this.uc3SigmaMetroStepPrefixObj[prefix] || 'Unknown'; // Get description or "Unknown"
            return `${prefix} (${description})`; // Format with description
          }),
        ),
      );

      //this.uc3SigmaMetroStepPrefixObj = await this.getUC3SimgaMetroStepsPrefixWithNames(this.sessionData.job_id, true)
      //this.uc3SigmaMetroStepPrefixList = Object.keys(this.uc3SigmaMetroStepPrefixObj);
      // this.uc3SigmaMetroStepPrefixListGet = this.selectedTravelerSteps.filter((step:any) => {
      //   const prefix = step.split('-')[0]; // Extract the prefix before the first '-'
      //   return Object.keys(this.uc3SigmaMetroStepPrefixObj).includes(prefix); // Check if prefix exists in the object keys
      // });

      // this.uc3SigmaMetroStepPrefixList = Array.from(
      //   new Set(
      //     this.uc3SigmaMetroStepPrefixListGet.map((step: any) => {
      //       const prefix = step.split('-')[0]; // Extract prefix from step ID
      //       const description = this.uc3SigmaMetroStepPrefixObj[prefix] || "Unknown"; // Check if prefix exists in the object
      //       return `${prefix} (${description})`;
      //     })
      //   )
      // );
    } else {
      this.toaster.error('Please select Traveler Steps first');
      this.isSIGMADataCatalogue = false;
    }
  }

  async uc3SigmaCheck() {
    if (this.selectedTravelerSteps && this.selectedTravelerSteps.length > 0) {
      this.prefixesStartingWithOne = this.extractPrefixesStartingWithOne(
        this.selectedTravelerSteps,
      );
      this.namesWithPrefixOne = this.filterNamesWithPrefixOne(
        this.selectedTravelerSteps,
      );
      this.config.cached_traveler_steps = this.namesWithPrefixOne;
      //this.uc3SigmaMetroStepPrefixObj = await this.getUC3SimgaMetroStepsPrefixWithNames(this.sessionData.job_id, true)
      //this.uc3SigmaMetroStepPrefixList = Object.keys(this.uc3SigmaMetroStepPrefixObj);

      this.uc3SigmaMetroStepPrefixListGet = this.namesWithPrefixOne;

      // this.uc3SigmaMetroStepPrefixListGet = this.selectedTravelerSteps.filter((step:any) => {
      //   const prefix = step.split('-')[0]; // Extract the prefix before the first '-'
      //   return Object.keys(this.uc3SigmaMetroStepPrefixObj).includes(prefix); // Check if prefix exists in the object keys
      // });
      this.uc3SigmaMetroStepPrefixList = Array.from(
        new Set(
          this.uc3SigmaMetroStepPrefixListGet.map((step: any) => {
            const prefix = step.split('-')[0]; // Extract prefix from step ID
            const description =
              this.uc3SigmaMetroStepPrefixObj[prefix] || 'Unknown'; // Check if prefix exists in the object
            return `${prefix} (${description})`;
          }),
        ),
      );
    } else {
      this.toaster.error('Please select Traveler Steps first');
      this.isSIGMADataCatalogue = false;
    }
    if (this.isSIGMADataCatalogue) {
      let uc3 = await this.dataCatService.getFDContextApplyFilterStatus(
        this.sessionData.job_id,
        this.uc3SigmaStage,
      );
      if (uc3.current_stage_status === 'NOT_CONFIGURED') {
        console.log('not configured...');
      } else {
        this.UC3SigmaResultFetch();
        if (uc3.current_stage_status === 'SUCCESS') {
          this.UC3SigmaResultFetch();
          this.isUC3SigmaResultPath = true;
          this.uc3SigmaResultPath =
            uc3.current_stage_results?.uc3_sigma_data.file_path;
          this.setUC3SigmaInputs(uc3);
          this.toaster.success('Data fetched successfully');
        } else if (uc3.current_stage_status === 'FAILED') {
          this.uc3SigmaResultPath =
            uc3.current_stage_results?.uc3_sigma_data.file_path;
          this.setUC3SigmaInputs(uc3);
          this.toaster.error('UC3 Sigma Job Failed');
          this.isuc3SigmaResultFailed = true;
        } else if (uc3.current_stage_status === 'RUNNING') {
          this.uc3SigmaResultPath =
            uc3.current_stage_results?.uc3_sigma_data.file_path;
          this.setUC3SigmaInputs(uc3);
        } else if (uc3.current_stage_status === 'SAVED') {
          this.setUC3SigmaInputs(uc3);
        } else {
          this.UC3SigmaDataPullStatus();
        }
      }
    } else {
      this.isUC3DownloadDisable = true;
    }
    this.initializeFilteredList();
  }

  getCommonIds(index: number, isItATotalDatFetch?: any): Promise<void> {
    return new Promise((resolve, reject) => {
      let pageDetails = {
        pageIndex: 0,
        pageSize: 10,
      };
      if (this.filepathMetro == '' || this.filepathMetro == undefined) {
        this.commonidfilepath = this.selectedCommontestidPath;
      } else {
        this.commonidfilepath = this.filepathMetro;
      }
      this.dataCatService
        .getQueryUniques(
          this.commonidfilepath,
          'COMMON_TEST_ID',
          pageDetails,
          {},
          undefined,
          isItATotalDatFetch,
        )
        .subscribe({
          next: (res: any) => {
            if (res.body['uniques']) {
              this.uc3CommonStepIds = res.body['uniques'];
              resolve();
            } else {
              this.toaster.error('No unique common test IDs found.');
              reject();
            }
          },
          error: (err: any) => {
            this.toaster.error('Error in fetching common ids');
            reject(err);
          },
        });
    });
  }
  onUC3ToggleChange(event: MatSlideToggleChange) {
    this.checkDownloadDisable();
    this.config.wafer_level = this.isUc3WaferLevel;
  }

  onToggleLotidLevel(event: MatSlideToggleChange) {
    this.checkDownloadDisable();
  }
  onTogglePointLevel(event: MatSlideToggleChange) {
    if (!event.checked) {
      this.uc3SigmaMetroRegionsSelected = [];
    }
    this.checkDownloadDisable();
    this.config.point_level = this.isUc3SelectRegionLevel;
  }

  uc3PaddingDaysChange(event: any) {
    this.checkDownloadDisable();
  }
  checkDownloadDisable(): void {
    const areTogglesInitial =
      this.selectedLotIds.length > 0 &&
      this.selectedWaferIds.length > 0 &&
      this.isUc3integrateWafer === this.isUc3integrateWaferInitial &&
      this.isUc3WaferLevel === this.isUc3WaferLevelInitial &&
      this.isUc3SelectRegionLevel === this.isUc3SelectRegionLevelInitial &&
      this.uc3SigmaUseProbe === this.uc3SigmaUseProbeInitial;
    const isInputChanged =
      this.uc3PaddingDays && this.uc3PaddingDays !== this.uc3PaddingDaysInitial;
    const metroRowSelected = this.uc3SigmaFinalSelection.length > 0;
    this.isUC3DownloadDisable =
      (areTogglesInitial && !isInputChanged) || !metroRowSelected;
  }
  uc3SigmaReset() {
    this.metro_rows = [];
    this.metro_rows.push({ selection: '' });
    this.uc3CommonStepIds = [];
    this.uc3SigmaMetroStepsSelected = [];
    this.uc3SigmaFinalSelection = [];
    this.isUc3integrateWafer = false;
    this.isUc3WaferLevel = false;
    this.isUC3SigmaResultPath = false;
    this.isUc3SelectRegionLevel = false;
    this.uc3SigmaMetroRegionsSelected = [];
    this.uc3SigmaMetroStepPrefixListSelected = '';
    this.uc3PaddingDays = 60;
    this.uc3SigmaCheckReset();
    this.initializeFilteredList();
    // this.uc3SigmaMetroStepPrefixList = Array.from(
    //   new Set(
    //     this.selectedTravelerSteps.map((step: any) => {
    //       const prefix = step.split('-')[0]; // Extract prefix from step ID
    //       const description = this.uc3SigmaMetroStepPrefixObj[prefix] || "Unknown"; // Check if prefix exists in the object
    //       return `${prefix} (${description})`;
    //     })
    //   )
    // );
    // this.filtereduc3SigmaMetroStepPrefixList = this.uc3SigmaMetroStepPrefixList.filter((item: string) =>
    //   item.toLowerCase().includes(this.searchUc3SigmaMetroSteps.toLowerCase())
    // );
  }
  areUC3LotIdsAllSelected() {
    if (this.filteredUc3LotIdsList.length > 0 && this.selectedLotIds)
      return this.filteredUc3LotIdsList.every((id: any) =>
        this.selectedLotIds.includes(id),
      );
    return false;
  }
  areUC3WaferIdsAllSelected() {
    if (this.filteredUc3WaferIdsList.length > 0 && this.selectedWaferIds)
      return this.filteredUc3WaferIdsList.every((id: any) =>
        this.selectedWaferIds.includes(id),
      );
    return false;
  }
  uc3LotIdsSelectAll(event: any) {
    if (event.checked) {
      this.selectedLotIds = this.filteredUc3LotIdsList.map((lot: any) => lot);
    } else {
      this.selectedLotIds = [];
    }
    this.checkLotIds();
  }
  uc3WaferIdsSelectAll(event: any) {
    if (event.checked) {
      this.selectedWaferIds = this.filteredUc3WaferIdsList.map(
        (lot: any) => lot,
      );
    } else {
      this.selectedWaferIds = [];
    }
    this.checkLotIds();
  }

  uc3LotWaferReset() {
    this.selectedLotIds = [];
    this.selectedWaferIds = [];
  }

  async uc3LotWaferSave() {
    try {
      if (this.selectedLotIds.length > 0 && this.selectedWaferIds.length > 0) {
        this.config['lot_ids']['selected_values'] = this.selectedLotIds;
        this.config['wafer_ids']['selected_values'] = this.selectedWaferIds;
        await this.dataCatService
          .saveLotWaferIds(this.config, this.sessionData.job_id)
          .subscribe((res: any) => {
            if (res.body === 'saved') {
              this.toaster.success('Data Saved Successfully');
            }
          });
      } else {
        this.toaster.error('Please select Lot and Wafer Ids');
      }
    } catch (error: any) {
      this.toaster.error('Error while saving Lot and Wafer Ids');
    }
  }

  async getSelectedLotWaferIds() {
    try {
      let status = await this.dataCatService.dataPullStatus(
        this.sessionData.job_id,
        this.uc3LotWaferStage,
      );
      if (
        status.fd_data_pull_job_status === 'IDLE' &&
        status.current_stage_status === 'SUCCESS'
      ) {
        this.dataCatService
          .saveLotWaferIdsResponseResult(
            this.sessionData.job_id,
            this.uc3LotWaferStage,
          )
          .subscribe((res: any) => {
            if (res) {
              this.selectedLotIds =
                res?.current_stage_inputs?.lot_ids?.selected_values || [];
              this.selectedWaferIds =
                res?.current_stage_inputs?.wafer_ids?.selected_values || [];
              this.lotResultFetch();
              if (this.filteredUc3LotIdsList.length > 0) this.checkLotIds();
            }
          });
      }
    } catch (error: any) {
      this.toaster.error('Error in fetching data');
    }
  }

  async useCaseChange() {
    if (this.selectedUCOption === 'UC3') {
      try {
        await this.getSelectedLotWaferIds();
        // await this.getLotIds();
      } catch (error) {
        return;
      }
    }
  }

  uc3SigmaMetroStepPrefixObject(item: any): any {
    return this.uc3SigmaMetroStepPrefixObj[item];
  }

  async getUC3SimgaMetroStepsPrefixWithNames(job_id: any, reset: boolean) {
    let applyUC3SigmaResult =
      await this.dataCatService.getUC3SimgaMetroStepsPrefixWithNames(
        job_id,
        reset,
      );
    return applyUC3SigmaResult;
  }

  uc3SigmaSetDataSource() {
    // this.isUC3SigmaResultPath = false;
    // this.isuc3SigmaResultFailed = false
    this.isUC3DownloadDisable = true;
    this.config.metro_step_common_step_ids = [...this.uc3SigmaFinalSelection];
    this.config.integrate_back_of_wafer_mesurement = this.isUc3integrateWafer;
    this.config.wafer_level = this.isUc3WaferLevel;
    this.config.point_level = this.isUc3SelectRegionLevel;
    this.config.use_probe = this.uc3SigmaUseProbe;
    this.config.regions.selected_values = this.uc3SigmaMetroRegionsSelected;
    this.config['lot_ids']['selected_values'] = this.selectedLotIds;
    this.config.padding_days = this.uc3PaddingDays;
  }

  uc3ProbeSave() {
    this.saveDataSource(this.uc3ProbeDataPullStage);
  }
  uc3SigmaSave() {
    this.uc3SigmaSetDataSource();
    this.saveDataSource(this.uc3SigmaStage);
  }
  saveDataSource(stage: any) {
    this.dataCatService
      .saveDataSource(this.config, this.sessionData.job_id, stage)
      .subscribe({
        next: (data) => {
          if (data) {
            this.toaster.success('Saved Successfully');
          } else {
            this.toaster.error('Save Failed');
          }
        },
        error: (err) => {
          console.error('Error while saving data:', err);
          this.toaster.error(
            'An error occurred while saving. Please try again.',
          );
        },
      });
  }
  uc2SigmaSave() {}

  setUC3SigmaInputs(uc3: any) {
    this.isUc3integrateWafer =
      uc3.current_stage_inputs?.integrate_back_of_wafer_mesurement;
    this.isUc3integrateWaferInitial = this.isUc3integrateWafer;
    this.isUc3WaferLevel = uc3.current_stage_inputs?.wafer_level;
    this.isUc3WaferLevelInitial = this.isUc3WaferLevel;
    this.uc3PaddingDaysInitial = uc3.current_stage_inputs?.padding_days;
    this.uc3PaddingDays = uc3.current_stage_inputs?.padding_days;
    this.uc3SigmaMetroRegionsSelected =
      uc3.current_stage_inputs?.regions.selected_values;

    let setUC3SigmaMetroStepsSelected =
      uc3.current_stage_inputs?.metro_step_common_step_ids;
    this.selectedCommontestidPath =
      uc3.current_stage_inputs?.metro_step_common_step_ids[0]?.common_test_ids
        ?.file_path;
    this.cached_traveler_steps_values =
      uc3.current_stage_inputs?.cached_traveler_steps;
    this.isUc3SelectRegionLevel = uc3.current_stage_inputs?.point_level;
    this.isUc3SelectRegionLevelInitial = this.isUc3SelectRegionLevel;

    if (uc3.current_stage_inputs?.use_probe) {
      this.uc3SigmaUseProbe = uc3.current_stage_inputs?.use_probe;
      this.uc3SigmaUseProbeInitial = this.uc3SigmaUseProbe;
    }

    this.uc3SigmaFinalSelection = [...(setUC3SigmaMetroStepsSelected || [])];

    if (setUC3SigmaMetroStepsSelected?.length > 0) {
      this.metro_rows = setUC3SigmaMetroStepsSelected.map(() => ({
        selection: '',
      }));
      setUC3SigmaMetroStepsSelected.forEach((mSteps: any) => {
        this.uc3SigmaMetroStepsSelected.push(
          mSteps['uc3_sigma_metro_steps']?.['selected_values'][0],
        );
      });
    }

    this.uc3SigmaMetroStepPrefixListSelected = this.uc3SigmaMetroStepsSelected;
  }
}
