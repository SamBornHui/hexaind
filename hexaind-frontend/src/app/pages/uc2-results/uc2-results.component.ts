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

@Component({
  selector: 'app-uc2-results',
  templateUrl: './uc2-results.component.html',
  styleUrls: ['./uc2-results.component.less'],
})
export class Uc2ResultsComponent {
  form: FormGroup;
  projectNames: any | undefined;
  projectNamesFanout: any | undefined;
  selectedPreviewType = 'Tables';
  selectedPreviewTypeFanout = 'Tables';
  modelsComparisonDfPreview: any | undefined;
  chambersComparisonDfPreview: any | undefined;
  modelsComparisonDfPreviewColumns: any | undefined;
  chambersComparisonDfPreviewColumns: any | undefined;

  modelsComparisonDfPreviewFanout: any | undefined;
  modelsComparisonDfPreviewFanouttable2: any | undefined;
  chambersComparisonDfPreviewFanout: any | undefined;
  modelsComparisonDfPreviewColumnsFanout: any | undefined;
  modelsComparisonDfPreviewColumnsFanouttable2: any | undefined;
  chambersComparisonDfPreviewColumnsFanout: any | undefined;


  responseData: any | undefined;
  responseDataFanout: any | undefined;

  rgtNavToggle: boolean = false;
  flexValue = 'calc(100% - 334px)';

  @Input() dataset_id!: string;
  isLoading: boolean = false;
  displayedColumns: string[] = [];
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

  isDisabled = false;

  table1Title: string = '';
  table2Title: string = '';
  table3Title: string = '';
  piechartTitle: string = '';

  modelRefreshtable1Title: string = '';
  modelRefreshtable2Title: string = '';

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
    private route: ActivatedRoute
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

  ngOnInit() {
    this.getProjectData();
    this.getProjectDataFanout();
  }

  onTabClick(tab: string) {
    if (tab === 'Modal Fanout') {
      this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { tab: 'ModalFanout' },
        queryParamsHandling: 'merge', // Preserves other query parameters
      });
    }
    else{
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
      if(!response.project_metadata) {
        this.toaster.error('Project meta data is not present', '', {
          positionClass: 'custom-toast-position',
        });
        return
      }
      this.processProjectData(response.project_metadata);
    }
    catch(e:any) {
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
    this.currentOutputColumnList = [];

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
      this.workWeekFolderNamePairForOutputColumnDropdown.set(element.work_week_folder_name, element.output_column_names);
    });

    this.listOfStepNames = Array.from(this.stepNameTechNodeMap.keys());
    
  }

  // onStepNameChange(stepName: any) {
  //   this.listOfTechNodes = [];
  //   this.currentListOfDateRanges = [];
  //   this.currentStepName = stepName;
  //   this.currentStepNameFanout = stepName;
  //   console.log(this.currentStepNameFanout,"step name fanout");
  //   this.currentTechNode = '';
  //   this.currentSelectedDateRange = '';
  //   this.currentWorkWeekFolderName = '';
  //   this.listOfTechNodes = Array.from(
  //     this.stepNameTechNodeMap.get(this.currentStepName),
  //   );
  //   this.currentSelectedOutputColumn = '';
  //   this.currentOutputColumnList = [];
  // }

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
  }

  onDateRangeChange(element: any) {
    this.currentSelectedDateRange = element.dateRange;
    this.currentWorkWeekFolderName = element.workWeekFolderName;
    if (this.workWeekFolderNamePairForOutputColumnDropdown && element.workWeekFolderName) {
      this.currentOutputColumnList = this.workWeekFolderNamePairForOutputColumnDropdown.get(element.workWeekFolderName);
    } else {
      console.warn("workWeekFolderNamePairForOutputColumnDropdown or workWeekFolderName is undefined");
      this.currentOutputColumnList = [];
    }
    this.currentSelectedOutputColumn = '';

    this.currentSelectedDateRangeFanout = element.dateRange;
    this.currentWorkWeekFolderNameFanout = element.workWeekFolderName;
    this.currentOutputColumnListFanout = this.workWeekFolderNamePairForOutputColumnDropdownFanout.get(element.workWeekFolderName);
    this.currentSelectedOutputColumnFanout = '';
  }
  

  onOutputColumnChange(element: any) {
    this.currentSelectedOutputColumn = element;
    this.currentSelectedOutputColumnFanout = element;
  }

  async submit() {
    try {
      this.responseData = await this.apiService.getUC2ProjectData(
        this.currentProjectName,
        this.currentWorkWeekFolderName,
        this.currentSelectedOutputColumn
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

        this.modelRefreshtable1Title = this.responseData.model_refresh?.table1?.title || '';
        this.modelRefreshtable2Title = this.responseData.model_refresh?.table2?.title || '';
        const modelTableData = this.responseData.model_refresh.table1.data;
        this.modelsComparisonDfPreview = modelTableData.data;
        this.modelsComparisonDfPreviewColumns = this.removeSpaceInStringsInanArray(modelTableData.column_names);
        const chamberTableData = this.responseData.model_refresh.table2.data;
        this.chambersComparisonDfPreview = chamberTableData.data;
        this.chambersComparisonDfPreviewColumns = this.removeSpaceInStringsInanArray(chamberTableData.column_names);

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


  // Added Modal Fanout


  async onProjectChangeFanout(projectName: any) {
    try {
      let response: any =
      await this.apiService.getUC2ProjectMetaData(projectName);
      this.currentProjectNameFanout = projectName;
      this.currentProjectName = projectName;
      if(!response.project_metadata) {
        this.toaster.error('Project meta data is not present', '', {
          positionClass: 'custom-toast-position',
        });
        return
      }
      this.onProjectChange(projectName);
      this.processProjectDataFanout(response.project_metadata);
    }
    catch(e:any) {
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
      if(!response.project_metadata) {
        this.toaster.error('Project meta data is not present', '', {
          positionClass: 'custom-toast-position',
        });
        return
      }
      this.processProjectDataFanout(response.project_metadata);
    }
    catch(e:any) {
      this.toaster.error('Error while fetching project metadata', '', {
        positionClass: 'custom-toast-position',
      });
    }

  }

  reset(){
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
    this.workWeekFolderNamePairForOutputColumnDropdownFanout = new Map();
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
      this.workWeekFolderNamePairForOutputColumnDropdownFanout.set(element.work_week_folder_name, element.output_column_names);
    });

    this.listOfStepNamesFanout = Array.from(this.stepNameTechNodeMapFanout.keys());

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
  }

  onDateRangeChangeFanout(element: any) {
    this.currentSelectedDateRangeFanout = element.dateRange;
    this.currentWorkWeekFolderNameFanout = element.workWeekFolderName;

    this.currentSelectedDateRange = element.dateRange;
    this.currentWorkWeekFolderName = element.workWeekFolderName;
    this.onDateRangeChange(element);
    this.currentOutputColumnListFanout = this.workWeekFolderNamePairForOutputColumnDropdownFanout.get(element.workWeekFolderName);
    this.currentSelectedOutputColumnFanout = '';
  }

  onOutputColumnChangeFanout(element: any) { console.log(element,"element value");
    this.currentSelectedOutputColumnFanout = element;
    this.currentSelectedOutputColumn = element;
    console.log(this.currentSelectedOutputColumn,"current outpt");
  }

  async submitFanout() {
    // Reset isDataLoaded flag before making the API call
    this.isDataLoaded = false;

    try {
      this.responseDataFanout = await this.apiService.getUC2ProjectData(
        this.currentProjectNameFanout,
        this.currentWorkWeekFolderNameFanout,
        this.currentSelectedOutputColumnFanout
      );

      // Check if response data is empty or undefined
      if (!this.responseDataFanout || Object.keys(this.responseDataFanout).length === 0) {
        this.toaster.error('Project data is not present', '', {
          positionClass: 'custom-toast-position',
        });
        return;
      }

      // Set data loaded flag
      this.isDataLoaded = true; 


      // Update table titles
      this.table1Title = this.responseDataFanout.model_fanout?.table1?.title || '';
      this.table2Title = this.responseDataFanout.model_fanout?.table2?.title || '';
      this.table3Title = this.responseDataFanout.model_fanout?.table3?.title || '';
      this.piechartTitle = this.responseDataFanout.model_fanout?.pie_chart?.title || '';

      // Update data and columns for model comparison
      if (this.responseDataFanout.model_fanout?.table1?.data) {
        this.modelsComparisonDfPreviewFanout = this.responseDataFanout.model_fanout.table1.data.data;
        this.modelsComparisonDfPreviewColumnsFanout = this.removeSpaceInStringsInanArray(this.responseDataFanout.model_fanout.table1.data.column_names);
      }

      if (this.responseDataFanout.model_fanout?.table2?.data) {
        this.modelsComparisonDfPreviewFanouttable2 = this.responseDataFanout.model_fanout.table2.data.data;
        this.modelsComparisonDfPreviewColumnsFanouttable2 = this.removeSpaceInStringsInanArray(this.responseDataFanout.model_fanout.table2.data.column_names);
      }

      // Update data and columns for chamber comparison
      if (this.responseDataFanout.model_fanout?.table3?.data) {
        this.chambersComparisonDfPreviewFanout = this.responseDataFanout.model_fanout.table3.data.data;
        this.chambersComparisonDfPreviewColumnsFanout = this.removeSpaceInStringsInanArray(this.responseDataFanout.model_fanout.table3.data.column_names);
      }

      // Change viewer type to 'Tables' for Fanout
      this.changeViewerFanout('Tables');
      this.submit();

      // Handle Pie Chart Data
      if (this.responseDataFanout.model_fanout?.pie_chart?.file_paths?.length) {
        let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
          `${this.configService.getAppAuxApiURL}/eda/file?path=${this.responseDataFanout.model_fanout.pie_chart.file_paths[0]}`
        );
        this.PieChartDataFanout = {
          completeUrl,
          isLoaded: false,
        };

        console.log(this.PieChartDataFanout,"pie chart");
      }

      // Manually trigger change detection if necessary
      // this.cdr.detectChanges();
    } catch (e: any) {
      // Reset isDataLoaded flag on error
      this.isDataLoaded = false;

      // Log the error for debugging
      console.error('Error while fetching project data for Fanout:', e);

      // Show error message to the user
      this.toaster.error('Error while fetching the project data', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }

  removeSpaceInStringsInanArray(arrayOfStrings:any) {
    return arrayOfStrings.map((element:any)=> {
      return element.replace(/\s+/g, '')
    })
  }



  //End Modal Fanout




  getData() {
    this.isLoading = true;
    this.dataPreviewService
      .getData(this.dataset_id, this.currentPage, this.rowCountPerPage)
      .then((response) => {
        this.displayedColumns = this.removeSpaceInStringsInanArray(response.column_names);
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
        this.convertval = '0';
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

  async changeViewer(viewerType: any) {
    this.selectedPreviewType = viewerType;
    if (viewerType === 'Line Charts') {
      this.lineChartData = [];
      // Check if line_plot exists in responseData and has file_paths
      if (this.responseData.model_refresh.line_plot && this.responseData.model_refresh.line_plot.file_paths) {
        this.responseData.model_refresh.line_plot.file_paths.forEach((path: string) => {
          let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
            `${this.configService.getAppAuxApiURL}/eda/file?path=${path}`
          );
          this.lineChartData.push({
            completeUrl,
            isLoaded: false,
          });
        });
      }
    }

    if (viewerType === 'CpK Bar Chart') {
      // Check if bar_plot exists in responseData and has file_paths
      if (this.responseData.model_refresh.bar_plot && this.responseData.model_refresh.bar_plot.file_paths) {
        let path = this.responseData.model_refresh.bar_plot.file_paths[0]; // Assuming you only want the first file path for bar chart
        let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
          `${this.configService.getAppAuxApiURL}/eda/file?path=${path}`
        );
        this.barChartPlotData = {
          completeUrl,
          isLoaded: false,
        };
      }
    }
  }


  async changeViewerFanout(viewerType: any) {
    if (this.isDisabled) {
    this.selectedPreviewTypeFanout = viewerType;
    if (viewerType === 'Line Charts') {
      this.lineChartDataFanout = [];
      this.responseDataFanout.fan_out_line_charts.forEach((path: any) => {
        let completeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
          `${this.configService.getAppAuxApiURL}/eda/file?path=${path}`,
        );
        this.lineChartDataFanout.push({
          completeUrl,
          isLoaded: false,
        });
      });
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
    this.flexValue = this.flexValue === 'calc(100% - 334px)' ? 'calc(100% - 58px)' : 'calc(100% - 334px)';
  }

}
