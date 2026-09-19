import {
  ChangeDetectorRef,
  Component,
  ElementRef,
  Input,
  ViewChild,
} from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { PageEvent } from '@angular/material/paginator';
import { DomSanitizer } from '@angular/platform-browser';
import { DownloadRescaleVisualizeDataComponent } from 'src/app/dialogs/data-preview/download-rescale-vizualize-data/download-rescale-vizualize-data.component';
import { DataPreviewService } from 'src/app/dialogs/data-preview/services/data-preview.service';
import { ApiService } from 'src/app/services/api.service';
import { ConfigService } from '../workflow-designer/workflow-canvas.service';
import { ActivatedRoute, Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { MatTabGroup } from '@angular/material/tabs';
import { PieChartComponent } from 'src/app/util-components/pie-chart/pie-chart.component';
@Component({
  selector: 'app-uc2-results-new',
  templateUrl: './uc2-results-new.component.html',
  styleUrls: ['./uc2-results-new.component.less'],
})
export class Uc2ResultsNewComponent {
  [x: string]: any;
  form: FormGroup;
  projectNames: any | undefined;
  projectNamesFanout: any | undefined;
  selectedPreviewType = 'Tables';
  selectedPreviewTypeFanout = 'Tables';
  modelsComparisonDfPreview: any | undefined;
  chambersComparisonDfPreview: any | undefined;
  modelsComparisonDfPreviewColumns: any = [];
  chambersComparisonDfPreviewColumns: any = [];
  modelsComparisonDfPreviewFanout: any | undefined;
  modelsComparisonDfPreviewFanouttable2: any | undefined;
  chambersComparisonDfPreviewFanout: any | undefined;
  displayedColumnsFanout: any = [];
  modelsComparisonDfPreviewColumnsFanout: any | undefined;
  modelsComparisonDfPreviewColumnsFanouttable2: any | undefined;
  chambersComparisonDfPreviewColumnsFanout: any | undefined;
  responseData: any | undefined;
  responseDataFanout: any | undefined;
  rgtNavToggle: boolean = false;
  flexValue = 'calc(100% - 334px)';
  @Input() dataset_id!: string;
  isLoading: boolean = false;

  dataSource: any[] = [];
  filteredData: any[] = [];
  totalRows: number = 0;
  editableColumnName: string | null = null;
  currentEditValue: string = '';
  roundValue = '0';
  convertval: any;
  enableVisButton: boolean = false;
  vizTrialsData: any[] = [];
  sliderValue: any;
  currentPage: number = 1;
  sliderIncreamentValue: any | undefined;
  rowCountPerPage: any = 50;
  isDataBeingFetchedWhenScrolling = false;
  isDataLoaded: boolean = false;
  excludedColumns: string[] = [
    'Pareto-optimal_num',
    'generation_method',
    'trial_index',
    'visual_dir',
    'arm_name',
  ];
  @ViewChild('scrollableDiv') scrollableDiv!: ElementRef;
  listOfStepNames: any;
  listOfTechNodes: any;
  listOfStepNamesFanout: any;
  listOfTechNodesFanout: any;
  currentListOfDateRanges: any;
  currentListOfDateRangesFanout: any;
  stepNameTechNodePairForDateDropdown: any;
  stepNameTechNodePairForDateDropdownFanout: any;
  stepNameTechNodeMap: any;
  stepNameTechNodeMapFanout: any;
  currentStepName: any;
  currentTechNode: any;
  currentStepNameFanout: any;
  currentTechNodeFanout: any;
  currentSelectedDateRange: any;
  currentProjectName: any;
  currentSelectedDateRangeFanout: any;
  currentProjectNameFanout: any;
  currentWorkWeekFolderName: any;
  currentWorkWeekFolderNameFanout: any;
  toggleHeaderButton: string = 'expand_more';
  showMainHeader: boolean = true;
  workWeekFolderNamePairForOutputColumnDropdown: any;
  workWeekFolderNamePairForOutputColumnDropdownFanout: any;
  currentSelectedOutputColumnFanout: any;
  currentOutputColumnListFanout: any;
  currentSelectedOutputColumn: any;
  currentOutputColumnList: any;
  dropdownPairForOptimization: any;
  dropdownPairForOptimizationFanout: any;
  currentOptimizationListFanout: any;
  currentSelectedOptimizationFanout: any;
  currentOptimizationList: any;
  currentSelectedOptimization: any;
  isDisabled = false;
  table1Title: string = '';
  table2Title: string = '';
  table3Title: string = '';
  piechartTitle: string = '';
  modelRefreshtable1Title: string = '';
  modelRefreshtable2Title: string = '';
  chamberCountFanout: any;
  chamberCountRefresh: any;
  startDate: any;
  endDate: any;
  hasStatusColumn: boolean = false;
  // Declare the columns array, initialize with the default columns
  displayedColumns: string[] = [
    'Chamber Id',
    'Status',
    'Valid Wafer Runs',
    'CPK Actual',
    'CONV Model',
    'Actual Popul mean',
    'Pred Popul mean',
    'VPM Model',
    'Improvement (%)',
    'Gauge',
  ];
  intervalValues: number[] = [];
  staticGaugeValue: number = 90;
  isLineChartFanoutPlot: boolean = false;
  selectedFanoutChamberId: any;
  selectedSpcFanoutChamberId: string[] = [];
  plotStatusMsg: string = 'Please select a Chamber ID';

  Math = Math;
  cloneChamberLineChartFanout: any | undefined;
  masterHtmlForUC2Download: string = '';
  clonedSpcFanoutTable: any | undefined;
  isSpcSelectAll: boolean = false;
  isSpcSubmitClicked: boolean = false;
  plotResult: any;
  isPlotLoaded: boolean = false;
  pathList: any;
  selectedPlotTabs: any = 'Exploratory Data Analysis';
  isOptimizationColumnValue: boolean = true;
  constructor(
    fb: FormBuilder,
    private apiService: ApiService,
    private dataPreviewService: DataPreviewService,
    public dialog: MatDialog,
    private cdr: ChangeDetectorRef,
    private sanitizer: DomSanitizer,
    private router: Router,
    private configService: ConfigService,
    public toaster: ToastrService,
    private route: ActivatedRoute,
  ) {
    this.form = fb.group({
      projectName: [''],
      stepName: [''],
      techNode: [''],
      dateRange: fb.group({
        startDate: [''],
        endDate: [''],
      }),
    });
  }

  // calculateMeans() {
  //   this.meanFirstY = this.calculateMean(this.firstYGroup);
  //   this.meanSecondY = this.calculateMean(this.secondYGroup);
  // }

  // calculateMean(data: number[]): number {
  //   return data.length ? data.reduce((sum, value) => sum + value, 0) / data.length : 0;
  // }

  ngOnInit() {
    this.getProjectData();
    this.getProjectDataFanout();
    this.loadHtmlFile();
  }

  async loadHtmlFile(): Promise<void> {
    try {
      const response = await fetch('../../assets/UC2IndexHtml.html');
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      this.masterHtmlForUC2Download = await response.text();
    } catch (error) {
      console.error('There was an error loading the HTML file:', error);
    }
  }

  onTabClick(tab: string) {
    if (tab === 'Modal Fanout') {
      this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { tab: 'ModalFanout' },
        queryParamsHandling: 'merge', // Preserves other query parameters
      });
    } else {
      this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { tab: 'ModalRefresh' },
        queryParamsHandling: 'merge', // Preserves other query parameters
      });
    }
  }
  async getProjectData() {
    let response: any = await this.apiService.getUC2ProjectNames();
    this.projectNames = response.project_names;
  }
  async getProjectDataFanout() {
    let response: any = await this.apiService.getUC2ProjectNames();
    this.projectNamesFanout = response.project_names;
  }
  async onProjectChange(projectName: any) {
    this.onProjectChangeFanoutStep(projectName);
    try {
      let response: any =
        await this.apiService.getUC2ProjectMetaData(projectName);
      this.currentProjectName = projectName;
      if (!response.project_metadata) {
        this.toaster.error('Project meta data is not present', '', {
          positionClass: 'custom-toast-position',
        });
        return;
      }
      this.processProjectData(response.project_metadata);
    } catch (e: any) {
      this.toaster.error('Error while fetching project metadata', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }
  processProjectData(projectData: any) {
    this.stepNameTechNodeMap = new Map();
    this.stepNameTechNodePairForDateDropdown = new Map();
    this.listOfStepNames = [];
    this.listOfTechNodes = [];
    this.currentListOfDateRanges = [];
    this.currentStepName = '';
    this.currentTechNode = '';
    this.currentSelectedDateRange = '';
    this.currentWorkWeekFolderName = '';
    this.workWeekFolderNamePairForOutputColumnDropdown = new Map();
    this.dropdownPairForOptimization = new Map();
    this.currentOutputColumnList = [];
    this.currentSelectedOptimization = '';

    projectData.forEach((element: any) => {
      let stepName = element.step_name;
      let techNode = element.tech_node;
      if (element.interval !== undefined) {
        this.intervalValues.push(element.interval);
      }
      if (!this.stepNameTechNodeMap.has(stepName)) {
        this.stepNameTechNodeMap.set(stepName, new Set());
      }
      this.stepNameTechNodeMap.get(stepName).add(techNode);
      let key = stepName + '--' + techNode;
      if (!this.stepNameTechNodePairForDateDropdown.has(key)) {
        this.stepNameTechNodePairForDateDropdown.set(key, []);
      }
      this.stepNameTechNodePairForDateDropdown.get(key).push({
        dateRange: element.start_date + '   to   ' + element.end_date,
        workWeekFolderName: element.work_week_folder_name,
      });
      this.workWeekFolderNamePairForOutputColumnDropdown.set(
        element.work_week_folder_name,
        element.output_column_names,
      );

      for (let value of element.output_column_names) {
        this.dropdownPairForOptimization.set(
          element.work_week_folder_name,
          element.optimization_folders[value],
        );
      }
    });

    this.isOptimizationColumnValue = this.dropdownPairForOptimization
      ? true
      : false;
    this.listOfStepNames = Array.from(this.stepNameTechNodeMap.keys());
  }

  onStepNameChange(stepName: any) {
    this.listOfTechNodes = [];
    this.currentListOfDateRanges = [];
    this.currentStepName = stepName;
    this.currentTechNode = '';
    this.currentSelectedDateRange = '';
    this.currentWorkWeekFolderName = '';
    this.listOfTechNodes = Array.from(
      this.stepNameTechNodeMap.get(this.currentStepName),
    );
    this.currentSelectedOutputColumn = '';
    this.currentOutputColumnList = [];
    this.listOfTechNodesFanout = [];
    this.currentListOfDateRangesFanout = [];
    this.currentStepNameFanout = stepName;
    this.currentTechNodeFanout = '';
    this.currentSelectedDateRangeFanout = '';
    this.currentWorkWeekFolderNameFanout = '';
    this.listOfTechNodesFanout = Array.from(
      this.stepNameTechNodeMapFanout.get(this.currentStepNameFanout),
    );
    this.currentSelectedOutputColumnFanout = '';
    this.currentOutputColumnListFanout = [];
    this.currentSelectedOptimization = '';
  }
  onTechNodeChange(techNode: any) {
    this.currentListOfDateRanges = [];
    this.currentTechNode = techNode;
    this.currentTechNodeFanout = techNode;
    this.currentSelectedDateRange = '';
    let key = this.currentStepName + '--' + this.currentTechNode;
    this.currentListOfDateRanges =
      this.stepNameTechNodePairForDateDropdown.get(key);
    this.currentSelectedOutputColumn = '';
    this.currentListOfDateRangesFanout = [];
    this.currentTechNodeFanout = techNode;
    this.currentSelectedDateRangeFanout = '';
    let key1 = this.currentStepNameFanout + '--' + this.currentTechNodeFanout;
    this.currentListOfDateRangesFanout =
      this.stepNameTechNodePairForDateDropdownFanout.get(key1);
    this.currentSelectedOutputColumnFanout = '';
    this.currentOutputColumnListFanout = [];
    this.currentSelectedOptimization = '';
  }
  onDateRangeChange(element: any) {
    this.currentSelectedDateRange = element.dateRange;
    this.currentWorkWeekFolderName = element.workWeekFolderName;
    if (
      this.workWeekFolderNamePairForOutputColumnDropdown &&
      element.workWeekFolderName
    ) {
      this.currentOutputColumnList =
        this.workWeekFolderNamePairForOutputColumnDropdown.get(
          element.workWeekFolderName,
        );
    } else {
      console.warn(
        'workWeekFolderNamePairForOutputColumnDropdown or workWeekFolderName is undefined',
      );
      this.currentOutputColumnList = [];
    }
    this.currentSelectedOutputColumn = '';
    this.currentSelectedDateRangeFanout = element.dateRange;
    this.currentWorkWeekFolderNameFanout = element.workWeekFolderName;
    this.currentOutputColumnListFanout =
      this.workWeekFolderNamePairForOutputColumnDropdownFanout.get(
        element.workWeekFolderName,
      );
    this.currentSelectedOutputColumnFanout = '';
    this.currentSelectedOptimization = '';
    this.currentSelectedOptimizationFanout = '';
  }

  onOutputColumnChange(element: any) {
    this.currentSelectedOutputColumn = element;
    this.currentSelectedOutputColumnFanout = element;
    this.currentSelectedOptimization = '';
    this.currentSelectedOptimizationFanout = '';
    if (this.dropdownPairForOptimization) {
      this.currentOptimizationList = this.dropdownPairForOptimization.get(
        this.currentWorkWeekFolderName,
      );
      this.currentOptimizationListFanout = this.dropdownPairForOptimization.get(
        this.currentWorkWeekFolderName,
      );
    }
  }

  onPlotsColumnChange(element: any) {
    this.currentSelectedOptimization = element;
    this.currentSelectedOptimizationFanout = element;
  }

  async submit() {
    try {
      this.responseData = await this.apiService.getUC2ProjectResultData(
        this.currentProjectName,
        this.currentWorkWeekFolderName,
        this.currentSelectedOutputColumn,
        this.currentSelectedOptimization,
      );
      if (
        Object.keys(this.responseData).length === 0 ||
        this.responseData.model_refresh.table1.data.total_rows === 0
      ) {
        this.toaster.error('Project data is not present', '', {
          positionClass: 'custom-toast-position',
        });
      } else {
        this.isDataLoaded = true;
        // Titles for the tables
        this.modelRefreshtable1Title =
          this.responseData.model_refresh?.table1?.title || '';
        this.modelRefreshtable2Title =
          this.responseData.model_refresh?.table2?.title || '';

        // Extract table data for models
        const modelTableData = this.responseData.model_refresh.table1.data;
        this.modelsComparisonDfPreview = modelTableData.data;
        this.modelsComparisonDfPreviewColumns = modelTableData.column_names;

        // Fetch chamber table data
        const chamberTableData = this.responseData.model_refresh.table2.data;

        // Dynamically map data rows to column names
        this.chambersComparisonDfPreview = chamberTableData.data.map(
          (row: any[]) => {
            const rowData = chamberTableData.column_names.reduce(
              (acc: any, column: string, index: number) => {
                acc[column] = row[index];
                return acc;
              },
              {},
            );

            // Combine "Improved", "Same", and "Degraded" columns into a "Flag" column
            const flag = [];
            if (rowData['Improved'] === 1) flag.push('Improved');
            if (rowData['Same'] === 1) flag.push('Same');
            if (rowData['Degraded'] === 1) flag.push('Degraded');

            // Calculate Gauge Value
            const actualCpk = parseFloat(rowData['Actual CPK']) || 0;
            const currentModelCpk = parseFloat(rowData['Current Model']) || 0;
            const gaugeValue =
              actualCpk !== 0
                ? ((actualCpk - currentModelCpk) / actualCpk) * 100
                : 0;

            return {
              ...rowData,
              Flag: flag.join(', ') || '',
              Gauge: gaugeValue.toFixed(2), // Allow negative values
            };
          },
        );

        // Rearrange and filter columns in the desired order
        // const desiredOrder = [
        //   'Chamber Id',
        //   'Valid Wafer Runs',
        //   'Actual CPK',
        //   'Current Model',
        //   'New Optimized Model',
        //   'Actual Popul mean',
        //   'Pred Popul mean',
        //   'Improvement (%)',
        //   'Guage'
        // ];
        const desiredOrder =
          this.responseData.model_refresh.table2.data.column_names;
        this.chambersComparisonDfPreviewColumns = desiredOrder
          .concat(['Gauge'])
          .filter(
            (column: string) =>
              column !== 'Improved' &&
              column !== 'Same' &&
              column !== 'Degraded',
          );
        // console.log("desiredOrder : ", desiredOrder);
        // console.log(this.chambersComparisonDfPreview,"test",this.chambersComparisonDfPreviewColumns);

        this.chamberCountRefresh =
          this.responseData?.unique_chamber_count_Refresh;
        // Change viewer type to 'Tables'
        this.changeViewer('Tables');
      }
    } catch (e: any) {
      // Log the error for debugging (optional)
      console.error('Error while fetching project data:', e);
      // Show error message to the user
      this.toaster.error('Error while fetching the project data', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }
  onStatusChange(element: any) {
    // You can update the backend or do any necessary actions here when the status changes
    const dateRange = this.currentSelectedDateRangeFanout.split(' to ');
    const start_date = dateRange[0]; // Extract start date
    const end_date = dateRange[1]; // Extract end date
    // Assign to variables or use as needed
    this.startDate = start_date;
    this.endDate = end_date;
    // Find interval based on the current selection (if applicable)
    const interval =
      this.intervalValues.length > 0 ? this.intervalValues[0] : null; // Replace this with the correct interval logic
    try {
      // Send API request with interval and chamber ID
      const response: any = this.apiService.updateStatusModal(
        '1',
        element['Status'],
        this.currentProjectNameFanout,
        this.currentWorkWeekFolderNameFanout,
        this.currentSelectedOutputColumnFanout,
        this.startDate,
        this.endDate,
        interval, // Pass the interval value
        element['Chamber Id'], // Pass the chamber ID from the element
        this.currentSelectedOptimizationFanout,
      );
      // Uncomment if you want to show success feedback
      // this.toaster.success('Status Successfully changed', '', {
      //   positionClass: 'custom-toast-position',
      // });
    } catch (e: any) {
      this.toaster.error('Error while fetching project metadata', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }

  // Added Modal Fanout
  async onProjectChangeFanout(projectName: any) {
    try {
      let response: any =
        await this.apiService.getUC2ProjectMetaData(projectName);
      this.currentProjectNameFanout = projectName;
      this.currentProjectName = projectName;
      if (!response.project_metadata) {
        this.toaster.error('Project meta data is not present', '', {
          positionClass: 'custom-toast-position',
        });
        return;
      }
      this.onProjectChange(projectName);
      this.processProjectDataFanout(response.project_metadata);
    } catch (e: any) {
      this.toaster.error('Error while fetching project metadata', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }
  async onProjectChangeFanoutStep(projectName: any) {
    try {
      let response: any =
        await this.apiService.getUC2ProjectMetaData(projectName);
      this.currentProjectNameFanout = projectName;
      this.currentProjectName = projectName;
      if (!response.project_metadata) {
        this.toaster.error('Project meta data is not present', '', {
          positionClass: 'custom-toast-position',
        });
        return;
      }
      this.processProjectDataFanout(response.project_metadata);
    } catch (e: any) {
      this.toaster.error('Error while fetching project metadata', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }
  reset() {
    this.currentProjectName = [];
    this.currentStepNameFanout = '';
    this.currentTechNodeFanout = '';
    this.currentSelectedDateRangeFanout = '';
    this.currentSelectedOutputColumnFanout = '';
    this.currentOutputColumnListFanout = [];
    this.currentStepName = '';
    this.currentTechNode = '';
    this.currentSelectedDateRange = '';
    this.currentSelectedOutputColumn = '';
    this.currentOutputColumnList = [];
    this.currentSelectedOptimization = '';
    this.currentSelectedOptimizationFanout = '';
    // "hide" table/plot containers on reset
    this.isDataLoaded = false;
  }
  processProjectDataFanout(projectData: any) {
    this.stepNameTechNodeMapFanout = new Map();
    this.stepNameTechNodePairForDateDropdownFanout = new Map();
    this.listOfStepNamesFanout = [];
    this.listOfTechNodesFanout = [];
    this.currentListOfDateRangesFanout = [];
    this.currentStepNameFanout = '';
    this.currentTechNodeFanout = '';
    this.currentSelectedDateRangeFanout = '';
    this.currentWorkWeekFolderNameFanout = '';
    this.currentSelectedOutputColumnFanout = '';
    this.currentSelectedOptimizationFanout = '';
    this.workWeekFolderNamePairForOutputColumnDropdownFanout = new Map();
    this.dropdownPairForOptimizationFanout = new Map();
    this.currentOutputColumnList = [];
    this.currentOutputColumnListFanout = [];
    projectData.forEach((element: any) => {
      let stepName = element.step_name;
      let techNode = element.tech_node;
      if (!this.stepNameTechNodeMapFanout.has(stepName)) {
        this.stepNameTechNodeMapFanout.set(stepName, new Set());
      }
      this.stepNameTechNodeMapFanout.get(stepName).add(techNode);
      let key = stepName + '--' + techNode;
      if (!this.stepNameTechNodePairForDateDropdownFanout.has(key)) {
        this.stepNameTechNodePairForDateDropdownFanout.set(key, []);
      }
      this.stepNameTechNodePairForDateDropdownFanout.get(key).push({
        dateRange: element.start_date + '   to   ' + element.end_date,
        workWeekFolderName: element.work_week_folder_name,
      });
      this.workWeekFolderNamePairForOutputColumnDropdownFanout.set(
        element.work_week_folder_name,
        element.output_column_names,
      );
      // this.dropdownPairForOptimization.set(element.output_column_names[0], element.optimization_folders[element.output_column_names[0]]);
      for (let value of element.output_column_names) {
        this.dropdownPairForOptimizationFanout.set(
          element.work_week_folder_name,
          element.optimization_folders[value],
        );
      }
    });
    console.log('value : ', this.dropdownPairForOptimizationFanout[0]);
    this.isOptimizationColumnValue = this.dropdownPairForOptimizationFanout
      ? true
      : false;

    this.listOfStepNamesFanout = Array.from(
      this.stepNameTechNodeMapFanout.keys(),
    );
    this.stepNameTechNodeMap = new Map();
    this.stepNameTechNodePairForDateDropdown = new Map();
    this.listOfStepNames = [];
    this.listOfTechNodes = [];
    this.currentListOfDateRanges = [];
    this.currentStepName = '';
    this.currentTechNode = '';
    this.currentSelectedDateRange = '';
    this.currentWorkWeekFolderName = '';
    projectData.forEach((element: any) => {
      let stepName = element.step_name;
      let techNode = element.tech_node;
      if (!this.stepNameTechNodeMap.has(stepName)) {
        this.stepNameTechNodeMap.set(stepName, new Set());
      }
      this.stepNameTechNodeMap.get(stepName).add(techNode);
      let key = stepName + '--' + techNode;
      if (!this.stepNameTechNodePairForDateDropdown.has(key)) {
        this.stepNameTechNodePairForDateDropdown.set(key, []);
      }
      this.stepNameTechNodePairForDateDropdown.get(key).push({
        dateRange: element.start_date + '   to   ' + element.end_date,
        workWeekFolderName: element.work_week_folder_name,
      });
    });
    this.listOfStepNames = Array.from(this.stepNameTechNodeMap.keys());
  }
  onStepNameChangeFanout(stepName: any) {
    this.listOfTechNodesFanout = [];
    this.currentListOfDateRangesFanout = [];
    this.currentStepNameFanout = stepName;
    this.currentTechNodeFanout = '';
    this.currentSelectedDateRangeFanout = '';
    this.currentWorkWeekFolderNameFanout = '';
    this.listOfTechNodesFanout = Array.from(
      this.stepNameTechNodeMapFanout.get(this.currentStepNameFanout),
    );
    this.currentSelectedOutputColumnFanout = '';
    this.currentOutputColumnListFanout = [];
    this.listOfTechNodes = [];
    this.currentListOfDateRanges = [];
    this.currentStepName = stepName;
    this.currentTechNode = '';
    this.currentSelectedDateRange = '';
    this.currentWorkWeekFolderName = '';
    this.listOfTechNodes = Array.from(
      this.stepNameTechNodeMap.get(this.currentStepName),
    );
    this.currentSelectedOutputColumn = '';
    this.currentOutputColumnList = [];
    this.currentSelectedOptimizationFanout = '';
  }
  onTechNodeChangeFanout(techNode: any) {
    this.currentListOfDateRangesFanout = [];
    this.currentTechNodeFanout = techNode;
    this.currentSelectedDateRangeFanout = '';
    let key = this.currentStepNameFanout + '--' + this.currentTechNodeFanout;
    this.currentListOfDateRangesFanout =
      this.stepNameTechNodePairForDateDropdownFanout.get(key);
    this.currentSelectedOutputColumnFanout = '';
    this.currentOutputColumnListFanout = [];
    this.currentListOfDateRanges = [];
    this.currentTechNode = techNode;
    this.currentSelectedDateRange = '';
    let key1 = this.currentStepName + '--' + this.currentTechNode;
    this.currentListOfDateRanges =
      this.stepNameTechNodePairForDateDropdown.get(key1);
    this.currentSelectedOutputColumn = '';
    this.currentOutputColumnList = [];
    this.currentSelectedOptimizationFanout = '';
  }
  onDateRangeChangeFanout(element: any) {
    this.currentSelectedDateRangeFanout = element.dateRange;
    this.currentWorkWeekFolderNameFanout = element.workWeekFolderName;
    this.currentSelectedDateRange = element.dateRange;
    this.currentWorkWeekFolderName = element.workWeekFolderName;
    this.onDateRangeChange(element);
    this.currentOutputColumnListFanout =
      this.workWeekFolderNamePairForOutputColumnDropdownFanout.get(
        element.workWeekFolderName,
      );
    this.currentSelectedOutputColumnFanout = '';
    this.currentSelectedOptimizationFanout = '';
  }

  onOutputColumnChangeFanout(element: any) {
    this.currentSelectedOutputColumnFanout = element;
    this.currentSelectedOutputColumn = element;
    if (this.dropdownPairForOptimizationFanout) {
      this.currentOptimizationListFanout =
        this.dropdownPairForOptimizationFanout.get(
          this.currentWorkWeekFolderNameFanout,
        );
      this.currentOptimizationList = this.dropdownPairForOptimization.get(
        this.currentWorkWeekFolderName,
      );
    }
  }
  isImprovementFlagColumn(column: string): boolean {
    return column === 'Improved' || column === 'Same' || column === 'Degraded';
  }

  getImprovementFlag(element: any): string {
    if (element['Improved'] === 1) {
      return 'green'; // Green check mark for improved
    } else if (element['Same'] === 1) {
      return 'yellow'; // Yellow circle for same
    } else if (element['Degraded'] === 1) {
      return 'red'; // Red cross for degraded
    }
    return ''; // No flag if none of the conditions are met
  }

  async submitFanout() {
    // Reset isDataLoaded flag before making the API call
    this.isDataLoaded = false;
    try {
      this.responseDataFanout = await this.apiService.getUC2ProjectResultData(
        this.currentProjectNameFanout,
        this.currentWorkWeekFolderNameFanout,
        this.currentSelectedOutputColumnFanout,
        this.currentSelectedOptimizationFanout,
      );

      console.log('this.responseDataFanout : ', this.responseDataFanout);
      // Check if response data is empty or undefined
      if (
        !this.responseDataFanout ||
        Object.keys(this.responseDataFanout).length === 0
      ) {
        this.toaster.error('Project data is not present', '', {
          positionClass: 'custom-toast-position',
        });
        return;
      }
      // Set data loaded flag
      this.isDataLoaded = true;
      // Update table titles
      this.table1Title =
        this.responseDataFanout.model_fanout?.table1?.title || '';
      this.table2Title =
        this.responseDataFanout.model_fanout?.table2?.title || '';
      this.table3Title =
        this.responseDataFanout.model_fanout?.table3?.title || '';
      this.piechartTitle =
        this.responseDataFanout.model_fanout?.pie_chart?.title || '';
      this.chamberCountFanout =
        this.responseDataFanout?.unique_chamber_count_Fanout || '';
      // Update data and columns for model comparison
      if (this.responseDataFanout.model_fanout?.table1?.data) {
        this.modelsComparisonDfPreviewFanout =
          this.responseDataFanout.model_fanout.table1.data.data;
        this.modelsComparisonDfPreviewColumnsFanout =
          this.responseDataFanout.model_fanout.table1.data.column_names;
      }
      if (this.responseDataFanout.model_fanout?.table2?.data) {
        this.modelsComparisonDfPreviewFanouttable2 =
          this.responseDataFanout.model_fanout.table2.data.data;
        this.modelsComparisonDfPreviewColumnsFanouttable2 =
          this.responseDataFanout.model_fanout.table2.data.column_names;
      }

      if (this.responseDataFanout.model_fanout?.table3?.data) {
        const columns =
          this.responseDataFanout.model_fanout.table3.data.column_names || [];
        const hasStatusColumn = columns.includes('Status');

        // Ensure 'Status' is conditionally added after 'Chamber Id'
        if (hasStatusColumn) {
          const chamberIndex = this.displayedColumns.indexOf('Chamber Id');
          if (
            chamberIndex !== -1 &&
            !this.displayedColumns.includes('Status')
          ) {
            this.displayedColumns.splice(chamberIndex + 1, 0, 'Status'); // Insert 'Status' after 'Chamber Id'
          }
        } else if (this.displayedColumns.includes('Status')) {
          this.displayedColumns = this.displayedColumns.filter(
            (column) => column !== 'Status',
          );
        }

        // Map the data rows to include 'Flag' and 'Status' columns
        this.chambersComparisonDfPreviewFanout =
          this.responseDataFanout.model_fanout.table3.data.data.map(
            (row: any[]) => {
              const rowData = columns.reduce(
                (acc: any, column: string, index: number) => {
                  acc[column] = row[index];
                  return acc;
                },
                {},
              );

              // Combine the "Improved ?", "Same ?", and "Degraded ?" columns into the "Flag" column
              const flag = [];
              if (rowData['Improved'] === 1) flag.push('Improved');
              if (rowData['Same'] === 1) flag.push('Same');
              if (rowData['Degraded'] === 1) flag.push('Degraded');

              // Add 'status' field if "Status" column exists, safely handle data
              if (hasStatusColumn) {
                const statusValue = rowData['Status'];
                rowData['Status'] =
                  typeof statusValue === 'string' &&
                  statusValue.toLowerCase() === 'active'
                    ? true // Set as boolean for toggle binding
                    : false;
              }
              console.log(
                'this.chambersComparisonDfPreviewFanout) : ',
                this.chambersComparisonDfPreviewFanout,
              );
              console.log('rowData :', rowData);

              const actualCpk = parseFloat(rowData['CPK Actual']) || 0;
              const currentModelCpk = parseFloat(rowData['CONV Model']) || 0;
              const gaugeValue =
                actualCpk !== 0
                  ? ((actualCpk - currentModelCpk) / actualCpk) * 100
                  : 0;

              return {
                ...rowData,
                Flag: flag.join(', ') || '',
                Gauge: gaugeValue.toFixed(2), // Allow negative values
              };
            },
          );
        this.cloneChamberLineChartFanout = JSON.parse(
          JSON.stringify(this.chambersComparisonDfPreviewFanout),
        );
        this.clonedSpcFanoutTable = JSON.parse(
          JSON.stringify(this.chambersComparisonDfPreviewFanout),
        );

        // Update the columns array to reflect the changes
        this.chambersComparisonDfPreviewColumnsFanout = columns.filter(
          (column: string) =>
            column !== 'Improved' && column !== 'Same' && column !== 'Degraded', // Remove old columns
        );

        // Ensure 'Status' is reflected in the columns array if it exists
        if (
          hasStatusColumn &&
          !this.chambersComparisonDfPreviewColumnsFanout.includes('Status')
        ) {
          this.chambersComparisonDfPreviewColumnsFanout.push('Status');
        }

        // Update the chart data
        //this.calculatePercentagesForPieChart(this.responseDataFanout.model_fanout.table3.data?.data);
        this.calculatePercentagesForPieChart(
          this.responseDataFanout.model_fanout.table3.data?.data,
          this.responseDataFanout.model_fanout.table3.data?.column_names,
        );
      }

      // Change viewer type to 'Tables' for Fanout
      this.changeViewerFanout('Tables');
      this.submit();
      // Handle Pie Chart Data
      if (this.responseDataFanout.model_fanout?.pie_chart?.file_paths?.length) {
        let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
          `${this.configService.getAppAuxApiURL}/eda/file?path=${this.responseDataFanout.model_fanout.pie_chart.file_paths[0]}`,
        );
        this.PieChartDataFanout = {
          completeUrl,
          isLoaded: false,
        };
        console.log(this.PieChartDataFanout, 'pie chart');
      }

      // Manually trigger change detection if necessary
      // this.cdr.detectChanges();
    } catch (e: any) {
      // Reset isDataLoaded flag on error
      this.isDataLoaded = false;
      // Log the error for debugging
      // Show error message to the user
      this.toaster.error('Error while fetching the project data', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }
  improvementMetrics: any = [];

  calculatePercentagesForPieChart(data: any, columnNames: string[]) {
    if (!data) return;

    let improvement = 0;
    let noImprovement = 0;
    let negativeImprovement = 0;

    this.improvementMetrics = [];

    // Check if columnNames includes the improvement column (e.g., 'ImprovementValue' or similar)
    const improvementColumnIndex = columnNames.indexOf('Improvement (%)'); // Replace with actual column name

    if (improvementColumnIndex === -1) {
      return;
    }

    data.forEach((element: any) => {
      const improvementValue = element[improvementColumnIndex]; // Get the value from the improvement column

      // Check for improvement, no improvement, or negative improvement
      if (improvementValue > 0) improvement++;
      else if (improvementValue === 0) noImprovement++;
      else if (improvementValue < 0) negativeImprovement++;
    });

    const totalItems = data.length;

    // Calculate percentages and store in metrics array
    this.improvementMetrics.push(
      ((negativeImprovement / totalItems) * 100).toFixed(1),
    ); // Negative improvement
    this.improvementMetrics.push(((improvement / totalItems) * 100).toFixed(1)); // Positive improvement
    this.improvementMetrics.push(
      ((noImprovement / totalItems) * 100).toFixed(1),
    ); // No improvement
  }

  removeSpaceInStringsInanArray(arrayOfStrings: any) {
    return arrayOfStrings.map((element: any) => {
      return element.replace(/\s+/g, '');
    });
  }
  //End Modal Fanout
  getData() {
    this.isLoading = true;
    this.dataPreviewService
      .getData(this.dataset_id, this.currentPage, this.rowCountPerPage)
      .then((response) => {
        this.displayedColumns = this.removeSpaceInStringsInanArray(
          response.column_names,
        );
        this.dataSource = response.data;
        this.filteredData = this.dataSource;
        this.totalRows = response.total_rows;
        this.isLoading = false;
        this.checkVisulazData();
      })
      .catch((error) => {
        console.error('Error:', error);
      });
  }
  getDataWhenScrolled() {
    this.isDataBeingFetchedWhenScrolling = true;
    this.apiService
      .getUC2DataAggregationPaginatedData(
        this.responseData.models_comparison_df,
        this.currentPage,
      )
      .then((response: any) => {
        this.modelsComparisonDfPreview = this.modelsComparisonDfPreview.concat(
          response.data,
        );
        this.isDataBeingFetchedWhenScrolling = false;
        this.cdr.detectChanges();
      })
      .catch((error) => {
        console.error('Error:', error);
      });
  }
  checkVisulazData() {
    var vis_dir_index = this.displayedColumns.indexOf('visual_dir');
    if (vis_dir_index != -1) {
      let filteredVizData = this.dataSource.filter((item) => {
        return item[vis_dir_index] !== null && item[vis_dir_index] !== '';
      });
      if (filteredVizData.length) {
        this.enableVisButton = true;
        let dataToSend = [];
        var vis_dir_index = this.displayedColumns.indexOf('visual_dir');
        var vis_trial_index = this.displayedColumns.indexOf('trial_index');
        var job_id_index = this.displayedColumns.indexOf('job_id');
        var batch_index = this.displayedColumns.indexOf('batch');
        var status_index = this.displayedColumns.indexOf('trial_status');
        var trial_index_visual =
          this.displayedColumns.indexOf('trial_index_visual');
        for (var i = 0; i < filteredVizData.length; i++) {
          let Obj = {
            visual_dir: filteredVizData[i][vis_dir_index],
            trial_index: filteredVizData[i][vis_trial_index],
            job_id: filteredVizData[i][job_id_index],
            batch: filteredVizData[i][batch_index],
            trial_status: filteredVizData[i][status_index],
            trial_index_visual: filteredVizData[i][trial_index_visual],
            selected: false,
          };
          dataToSend.push(Obj);
          if (i == filteredVizData.length - 1) {
            this.vizTrialsData = dataToSend;
          }
        }
      }
    }
  }
  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value.toLowerCase();
    this.filteredData = this.dataSource.filter((row) => {
      return row.some((cell: any) => {
        if (typeof cell === 'number') {
          return cell.toString().toLowerCase().includes(filterValue);
        }
        return cell.toLowerCase().includes(filterValue);
      });
    });
  }
  setEditableColumnName(columnName: string) {
    this.editableColumnName = columnName;
    this.currentEditValue = columnName;
  }
  updateColumnName(newName: string, oldName: string) {
    if (newName) {
      this.displayedColumns = this.displayedColumns.map((name) =>
        name === oldName ? newName : name,
      );
      this.dataPreviewService
        .renameColumn(this.dataset_id, { oldName: newName })
        .then((response) => {
          this.getData();
        })
        .catch((error) => {
          console.error('Error:', error);
        });
    }
    this.closeEdit();
  }
  closeEdit() {
    this.editableColumnName = null;
  }
  formatLabel(value: number): string {
    return `${value}`;
  }
  convertscientific(number: any, roundValue: any): any {
    let expValue = 1;
    if (roundValue > 1) {
      expValue = roundValue;
    }
    if (typeof number === 'number' && !isNaN(number)) {
      if (number === 0) {
        this.convertval = 0;
      } else if (number >= 100000) {
        this.convertval = Number(number.toFixed(0)).toExponential(expValue);
      } else if (number <= 0.0001) {
        this.convertval = Number(number).toExponential(expValue);
      } else if (number <= 1000) {
        this.convertval = Number(number.toFixed(4));
      } else {
        this.convertval = Number(number.toFixed(2));
      }
    } else {
      this.convertval = number;
    }
    return this.convertval;
  }
  showDowloadDataDialog() {
    const dialogRef = this.dialog.open(DownloadRescaleVisualizeDataComponent, {
      maxWidth: '30vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: {
        trialsData: this.vizTrialsData,
      },
    });
    dialogRef.afterClosed().subscribe((result) => {});
  }
  onSliderChange(event: any) {
    this.fetchPagedDataUsingSliderPercentage(event.target.value);
  }
  /**
   * This method calculates the required page to be fetched from the backend using the sliderValue which is in percentage.
   * (this.totalRows * sliderPercentage)/100 gives the starting row number at that particular percentage
   * when the starting row number was divided by rowCountPerpage it gives the repective page in which this row is present
   * If scroll bar is at 100 show last page which is at 99th percentage
   */
  fetchPagedDataUsingSliderPercentage(sliderPercentage: number) {
    if (sliderPercentage == 100) sliderPercentage = 99;
    let pageNumber: number =
      Math.floor(
        (this.totalRows * sliderPercentage) / (100 * this.rowCountPerPage),
      ) + 1;
    this.currentPage = pageNumber;
    if (this.totalRows < this.rowCountPerPage) {
      const scrollableHeight =
        this.scrollableDiv.nativeElement.scrollHeight -
        this.scrollableDiv.nativeElement.clientHeight;
      const relativePosition = (sliderPercentage / 100) * scrollableHeight;
      this.scrollableDiv.nativeElement.scrollTop = relativePosition;
    } else {
      this.getData();
    }
  }
  onScroll(): void {
    const element = this.scrollableDiv.nativeElement;
    const scrollPosition = element.scrollTop;
    const maxScroll = element.scrollHeight - element.clientHeight;
    const scrollPercentage = (scrollPosition / maxScroll) * 100;
    if (scrollPercentage > 50 && !this.isDataBeingFetchedWhenScrolling) {
      this.currentPage += 1;
      this.getDataWhenScrolled();
    }
  }
  onPageChange($event: PageEvent) {
    this.currentPage = $event.pageIndex + 1;
    this.getData();
  }
  getDisplayColumns() {
    return this.modelsComparisonDfPreviewColumns;
  }
  getDisplayColumnsFanout() {
    return this.modelsComparisonDfPreviewColumnsFanout;
  }
  barChartPlotData: any;
  lineChartData: any;
  barChartPlotDataFanout: any;
  PieChartDataFanout: any;
  lineChartDataFanout: any;
  spcChartDataFanout: any;
  async changeViewer(viewerType: any, isSavingInHtml: boolean = false) {
    this.selectedPreviewType = viewerType;
    if (viewerType === 'Line Charts') {
      this.lineChartData = [];
      // Check if line_plot exists in responseData and has file_paths
      if (
        this.responseData.model_refresh.line_plot &&
        this.responseData.model_refresh.line_plot.file_paths
      ) {
        this.responseData.model_refresh.line_plot.file_paths.forEach(
          (path: string) => {
            let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
              `${this.configService.getAppAuxApiURL}/eda/file?path=${path}`,
            );
            this.lineChartData.push({
              completeUrl,
              isLoaded: isSavingInHtml,
            });
          },
        );
      }
    }
    if (viewerType === 'CpK Bar Chart') {
      // Check if bar_plot exists in responseData and has file_paths
      if (
        this.responseData.model_refresh.bar_plot &&
        this.responseData.model_refresh.bar_plot.file_paths
      ) {
        let path = this.responseData.model_refresh.bar_plot.file_paths[0]; // Assuming you only want the first file path for bar chart
        let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
          `${this.configService.getAppAuxApiURL}/eda/file?path=${path}`,
        );
        this.barChartPlotData = {
          completeUrl,
          isLoaded: isSavingInHtml,
        };
      }
    }

    if (viewerType === 'Plots') {
      this.plotResult = [];

      this.pathList = await this.apiService.getUC2PlotsData(
        this.currentProjectName,
        this.currentWorkWeekFolderName,
        this.currentSelectedOutputColumn,
        this.currentSelectedOptimization,
        this.selectedPlotTabs,
      );

      this.pathList.forEach((path: string) => {
        let url = this.sanitizer.bypassSecurityTrustResourceUrl(
          `${this.configService.getAppAuxApiURL}/eda/file?path=${path}`,
        );
        this.plotResult.push({
          url,
        });
        this.isPlotLoaded = false;
      });
    }
  }
  async changeViewerFanout(viewerType: any) {
    this.selectedPreviewTypeFanout = viewerType;
    if (viewerType === 'Line Charts') {
      this.displayedColumns = ['Chamber Id', 'Status'];
      this.lineChartDataFanout = [];
    }
    if (viewerType === 'CpK Bar Chart') {
      let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
        `${this.configService.getAppAuxApiURL}/eda/file?path=${this.responseDataFanout.fan_out_bar_plot}`,
      );
      this.barChartPlotDataFanout = {
        completeUrl,
        isLoaded: false,
      };
    }
    if (viewerType === 'Tables') {
      const fanoutColumnResult =
        this.responseDataFanout.model_fanout.table3.data.column_names;
      this.displayedColumnsFanout = fanoutColumnResult
        .concat(['Gauge'])
        .filter(
          (column: string) =>
            column !== 'Improved' &&
            column !== 'Same' &&
            column !== 'same' &&
            column !== 'Degraded',
        );
      // console.log("fanoutColumnResult : ",fanoutColumnResult)
      // this.displayedColumnsFanout.splice(1, 0, 'Status');  remove improved same degrades
      // this.displayedColumnsFanout.push('Status');
      // console.log("displayedColumnsFanout : ",this.displayedColumnsFanout);
      // this.displayedColumns = ['Chamber Id', 'Valid Wafer Runs', 'CPK Actual', 'CONV Model', 'VPM Model', 'Actual Popul mean', 'Pred Popul mean','Improvement (%)','Gauge']
    }
    if (viewerType === 'SPC Charts') {
      this.displayedColumns = ['Chamber_ID'];
      this.spcChartDataFanout = [];
    }
  }
  onBarPlotLoadFanout() {
    this.barChartPlotDataFanout.isLoaded = true;
  }
  onPieChartLoadFanout() {
    this.PieChartDataFanout.isLoaded = true;
  }
  onLinePathLoadFanout(currentPath: any) {
    this.lineChartDataFanout.forEach((path: any) => {
      if (currentPath.completeUrl == path.completeUrl) path.isLoaded = true;
    });
  }
  onBarPlotLoad() {
    this.barChartPlotData.isLoaded = true;
  }
  onLinePathLoad(currentPath: any) {
    this.lineChartData.forEach((path: any) => {
      if (currentPath.completeUrl == path.completeUrl) path.isLoaded = true;
    });
  }
  navigate(pageName: string) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const projectId = selectedProjectId;
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([`sites/${siteId}/projects/${projectId}/${pageName}`]);
  }
  toggleMainHeader() {
    this.showMainHeader = !this.showMainHeader;
    this.toggleHeaderButton = this.showMainHeader
      ? 'expand_less'
      : 'expand_more';
  }
  toggleRgtNav() {
    this.rgtNavToggle = !this.rgtNavToggle;
    this.flexValue =
      this.flexValue === 'calc(100% - 334px)'
        ? 'calc(100% - 58px)'
        : 'calc(100% - 334px)';
  }

  getGaugeColor(value: number): string {
    if (value > 0) {
      if (value >= 75) {
        return '#4caf50'; // Green for high positive values
      } else if (value >= 50) {
        return '#ffeb3b'; // Yellow for medium positive values
      } else {
        return '#ff9800'; // Orange for low positive values
      }
    } else {
      return '#f44336'; // Red for negative values
    }
  }

  chamberSelect(event: any) {
    if (event) {
      this.selectedFanoutChamberId = event['Chamber Id'];
      this.isLineChartFanoutPlot = true;
      if (!this.currentProjectNameFanout) {
        this.toaster.error('Project name not available');
        return;
      }
      if (!this.currentWorkWeekFolderNameFanout) {
        this.toaster.error('Work Week Folder Name is missing');
        return;
      }
      if (!this.currentSelectedOutputColumnFanout) {
        this.toaster.error('Output Column is missing');
        return;
      }
      let filePaths = this.plotPath(this.selectedFanoutChamberId);
      this.lineChartDataFanout = [];
      if (filePaths[0] === 'noPlot') {
        this.toaster.error('No plot available for the selected chamber');
        return;
      }
      if (filePaths[0] === 'noChamber') {
        this.toaster.error('No plots available for any chamber id');
        return;
      } else {
        filePaths.forEach((path: any) => {
          let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
            `${this.configService.getAppAuxApiURL}/eda/file?path=${path}`,
          );
          this.lineChartDataFanout.push({
            completeUrl,
            isLoaded: false,
          });
        });
      }
    }
  }

  plotPath(plotId: string): string[] {
    if (this.responseData && this.responseData.chamber_plot_paths) {
      const chamberPlotPaths = this.responseData.chamber_plot_paths;

      if (
        chamberPlotPaths[plotId] &&
        typeof chamberPlotPaths[plotId] === 'object'
      ) {
        const paths = chamberPlotPaths[plotId] as Record<string, string>;
        return Object.values(paths);
      }

      return ['noPlot'];
    }

    return ['noChamber'];
  }

  captureBlobs: {
    folderName: string;
    indexHtml: string;
    arrayOfBlobs: { name: string; blob: Blob }[];
  }[] = [];
  async capturePage(nameOfTheFolder: string) {
    let htmlContent = document.documentElement.outerHTML;
    const assetPromises: Promise<void>[] = [];
    const fileContents: {
      folderName: string;
      indexHtml: string;
      arrayOfBlobs: { name: string; blob: Blob }[];
    } = {
      folderName: nameOfTheFolder,
      arrayOfBlobs: [],
      indexHtml: '',
    };
    htmlContent = htmlContent.replace(/<base href="\/">/, '');

    const fetchAndSave = async (
      url: string,
      fileName: string,
      orginalRef: string,
    ) => {
      try {
        const response = await fetch(url);
        const blob = await response.blob();
        fileContents.arrayOfBlobs.push({ name: fileName, blob });
        const escapedRef = orginalRef.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // Escape special characters
        htmlContent = htmlContent.replace(
          new RegExp(escapedRef, 'g'),
          './assests/' + fileName,
        );
      } catch (error) {
        console.error(`Failed to fetch: ${url}`, error);
      }
    };

    document
      .querySelectorAll<HTMLImageElement>('img')
      .forEach((img: any, index: any) => {
        const originalHref = img.getAttribute('src') || '';
        const url = new URL(originalHref, window.location.origin).href;
        const ext = 'png';
        const fileName = `image_${index}.${ext}`;
        assetPromises.push(fetchAndSave(url, fileName, originalHref));
      });

    // Fetch CSS files
    document
      .querySelectorAll<HTMLLinkElement>('link[rel="stylesheet"]')
      .forEach((link, index) => {
        const originalHref = link.getAttribute('href') || '';
        const url = new URL(originalHref, window.location.origin).href;
        const fileName = `style_${index}.css`;
        assetPromises.push(fetchAndSave(url, fileName, originalHref));
      });

    // Fetch embedded HTML inside <object> tags
    document
      .querySelectorAll<HTMLObjectElement>('object[data]')
      .forEach((obj, index) => {
        const originalHref = obj.getAttribute('data') || '';
        const url = new URL(originalHref, window.location.origin).href;
        const ext = url.split('.').pop()?.split('?')[0] || 'html';
        const fileName = `embedded_${index}.${ext}`;
        assetPromises.push(fetchAndSave(url, fileName, originalHref));
      });

    // Fetch JS files
    // document.querySelectorAll<HTMLScriptElement>('script[src]').forEach((script, index) => {
    //   const url = script.src;
    //   const fileName = `script_${index}.js`;
    //   assetPromises.push(fetchAndSave(url, fileName));
    // });

    // Fetch embedded content inside <embed> (e.g., PDFs, SVGs)
    // document.querySelectorAll<HTMLEmbedElement>('embed[src]').forEach((embed, index) => {
    //   const url = embed.src;
    //   const ext = url.split('.').pop()?.split('?')[0] || 'bin';
    //   const fileName = `embed_${index}.${ext}`;
    //   assetPromises.push(fetchAndSave(url, fileName));
    // });

    // Fetch fonts inside CSS
    // document.querySelectorAll<HTMLStyleElement>('style').forEach((styleTag, index) => {
    //   const cssText = styleTag.innerHTML;
    //   const fontUrls = cssText.match(/url\(["']?(.*?)["']?\)/g) || [];

    //   fontUrls.forEach((match, fontIndex) => {
    //     const url = match.replace(/url\(["']?|["']?\)/g, '');
    //     const ext = url.split('.').pop()?.split('?')[0] || 'woff';
    //     const fileName = `font_${index}_${fontIndex}.${ext}`;
    //     assetPromises.push(fetchAndSave(url, fileName));
    //   });
    // });

    await Promise.all(assetPromises);

    let scriptForWindowMessaging = `<script> document.addEventListener("click", function(event) {
    window.parent.postMessage({id: event.target.id, innerText: event.target.innerText}, "*");
    })</script>`;

    htmlContent = htmlContent.replace(
      '</body>',
      `${scriptForWindowMessaging}</body>`,
    );

    fileContents.indexHtml = htmlContent;

    this.captureBlobs.push(fileContents);
  }

  @ViewChild('mainTabGroup') tabGroup: MatTabGroup | undefined;
  @ViewChild(PieChartComponent) pieChart!: PieChartComponent;
  isHTMLSnapshotDownloadInprogress = false;
  pieChartStaticImageUrl: any = '';

  async processAndDownloadHTML() {
    this.toggleRgtNav();
    this.showMainHeader = false;
    this.toggleHeaderButton = this.showMainHeader
      ? 'expand_less'
      : 'expand_more';
    await new Promise((resolve) => setTimeout(resolve, 1000));
    try {
      this.pieChartStaticImageUrl =
        await this.pieChart.savePieChartAsImageAndGetTheUrl();
    } catch (error) {
      console.error('Unable to conver pie chart', error);
    }
    this.isHTMLSnapshotDownloadInprogress = true;
    try {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      this.captureBlobs = [];
      await this.capturePage('ModelFanout');
      if (this.tabGroup) {
        this.tabGroup.selectedIndex = 1;
      }
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await this.changeViewer('Tables', true);
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await this.capturePage('ModelRefreshTable');
      await this.changeViewer('CpK Bar Chart', true);
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await this.capturePage('CpkBarChartModelRefresh');
      await this.changeViewer('Line Charts', true);
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await this.capturePage('LineChartModelRefresh');

      const finalZip = new JSZip();

      const indexHtmlForMain = this.masterHtmlForUC2Download;

      this.captureBlobs.forEach(
        (element: {
          folderName: string;
          indexHtml: string;
          arrayOfBlobs: { name: string; blob: Blob }[];
        }) => {
          const pageFolder = finalZip.folder(element.folderName);
          const assestsFolder = pageFolder?.folder('assests');

          element.arrayOfBlobs.forEach((e: any) => {
            assestsFolder?.file(e.name, e.blob);
          });

          pageFolder?.file(
            'index.html',
            new Blob([element.indexHtml], { type: 'text/html' }),
          );
        },
      );

      finalZip.file(
        'index.html',
        new Blob([indexHtmlForMain], { type: 'text/html' }),
      );

      const finalBlob = await finalZip.generateAsync({ type: 'blob' });
      let folderNameForFinalDownload =
        this.currentTechNodeFanout +
        '-' +
        this.currentSelectedDateRangeFanout +
        '-' +
        this.currentSelectedOutputColumnFanout +
        '.zip';
      saveAs(finalBlob, folderNameForFinalDownload);
      this.toaster.success('HTML is generate successfully', '', {
        positionClass: 'custom-toast-position',
      });
    } catch (error) {
      console.error(error);
    } finally {
      this.isHTMLSnapshotDownloadInprogress = false;
      this.showMainHeader = true;
      this.toggleHeaderButton = this.showMainHeader
        ? 'expand_less'
        : 'expand_more';
      this.toggleRgtNav();
    }
  }

  spcChamberSelect(event: any) {
    if (event) {
      const index = this.selectedSpcFanoutChamberId.indexOf(
        event['Chamber Id'],
      );
      if (index === -1) {
        this.selectedSpcFanoutChamberId.push(event['Chamber Id']);
      } else {
        this.selectedSpcFanoutChamberId.splice(index, 1);
        this.isSpcSelectAll = false;
      }
      if (
        this.selectedSpcFanoutChamberId.length ===
        this.clonedSpcFanoutTable.length
      ) {
        this.isSpcSelectAll = true;
      }
      this.isSpcSubmitClicked = false;
    }
  }

  spcSelectAllCheck(event: any) {
    if (this.isSpcSelectAll) {
      this.selectedSpcFanoutChamberId = this.clonedSpcFanoutTable.map(
        (chamber: any) => chamber['Chamber Id'],
      );
    } else {
      this.selectedSpcFanoutChamberId = [];
    }
  }

  async spcGeneratePlot() {
    this.isSpcSubmitClicked = true;
    // console.log("selectedSpcFanoutChamberId: 000 : ", this.selectedSpcFanoutChamberId)
  }

  async selectedPlotTab(selectedTab: any) {
    this.plotResult = [];
    this.isPlotLoaded = false;
    this.selectedPlotTabs = selectedTab.tab.textLabel;

    this.pathList = await this.apiService.getUC2PlotsData(
      this.currentProjectName,
      this.currentWorkWeekFolderName,
      this.currentSelectedOutputColumn,
      this.currentSelectedOptimization,
      this.selectedPlotTabs,
    );
    this.pathList.forEach((path: string) => {
      let url = this.sanitizer.bypassSecurityTrustResourceUrl(
        `${this.configService.getAppAuxApiURL}/eda/file?path=${path}`,
      );
      this.plotResult.push({
        url,
      });
      this.isPlotLoaded = false;
    });
  }

  loadPloturl() {
    this.isPlotLoaded = true;
    // let path  = "/hexaind-data/UC2_LR_FORECAST/F10 B58R 21L HMO DE R2R/Y2024WW45/ADD2/cpk_model_comparison.html"
    // this.plotResult = this.sanitizer.bypassSecurityTrustResourceUrl(
    //   `${this.configService.getAppAuxApiURL}/eda/file?path=${path}`
    // );
  }
}
