import {
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { DateAdapter, MAT_DATE_LOCALE } from '@angular/material/core';
import * as Plotly from 'plotly.js-dist-min';
import { DataSheetGenerateService } from './data-sheet-generate.service';
import { MatTabChangeEvent } from '@angular/material/tabs';
import { ConfigService } from 'src/app/services/config.service';
import { Router } from '@angular/router';
import { environment } from 'src/environments/environment';
import { ToastrService } from 'ngx-toastr';
import { PromptSaveComponent } from 'src/app/dialogs/prompt-save/prompt-save.component';
import { MatDialog } from '@angular/material/dialog';
import { ConfirmationDialogComponent } from './dsg-files/confirmation-dialog/confirmation-dialog.component';
import { CustomDateAdapter } from './custom-date-adapter/custom-date-adapter';
import { DSGHandler } from './datasheet-handler';
import { NotificationService } from './notification.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { SnackBarNotificationService } from 'src/app/services/snack-bar-notification.service';


interface CSVResponse {
  csv_data: DataItem[];
}
interface DataItem {
  file_name: string;
  xdata: string;
  ydata: string;
}

interface DataPoint {
  Rm: number;
  Ag: number;
  E: number;
}
@Component({
  selector: 'app-data-sheet-generator',
  templateUrl: './data-sheet-generator.component.html',
  styleUrls: ['./data-sheet-generator.component.less'],
  providers: [
    { provide: DateAdapter, useClass: CustomDateAdapter },
    { provide: MAT_DATE_LOCALE, useValue: 'en-GB' },
  ],
})
export class DataSheetGeneratorComponent implements OnInit, OnDestroy {
  objectKeys = Object.keys;
  loader: boolean = false;
  editState: { [key: string]: boolean } = {};
  isEditingCR: { [key: string]: boolean } = {};
  productName: string = 'Default commercial name';
  gauge: number = 1;
  m_source: string = 'Europe';
  branchName: string = 'production';
  specName: string = 'specA';
  latestRevalidationDate: Date = new Date('2024-01-01');
  validUntilDate: Date = new Date('2024-01-01');
  selectedTensileSample: string = '';
  editMode: { [key: string]: boolean } = {};
  datasheetId!: number;
  nominalAge!: number;
  dataSheetResults: any;
  bulgeFiles: string[] = [];
  bulgePlotDataPath: string = '';
  tensileSelectedOptions: string[] = [];
  tensileFilteredOptions: string[] = [];
  tensileReasons: string[] = new Array(this.tensileFilteredOptions.length);
  bulgeSelectedOptions: string[] = [];
  bulgeFilteredOptions: string[] = [];
  bulgeReasons: string[] = new Array(this.bulgeFilteredOptions.length);
  showMainHeader: boolean = false;
  toggleHeaderButton: string = 'expand_more';
  showDropdown: boolean = true;
  uniqueParameters: string[] = [];
  tensilePanel: boolean = false;
  bulgePanel: boolean = false;
  correctedTensileGraph: boolean = false;
  dataSheetGenerated: boolean = false;
  dataSheetFilePath: string = '';
  recomputeRp02: boolean = true;
  streamLiteLoadData: boolean = false;
  modelAdjust: string = 'Hocket Sherby Swift';
  scale_TensileBulge: boolean = false;
  modelComparisonData: any = '';
  traces: any = [];
  tabIndex: number = 0;
  modelResults: any = '';
  showTabs: boolean = false;
  activeTabIndexStressStrain: number = 0;
  activeTabIndexNValues: number = 0;
  resultLoader: boolean = false;
  tensile_grad: number = 15;
  bulge_grad: number = 10;
  tensile_n_grad: number = 15;
  bulge_n_grad: number = 10;
  tensile_plot_data: DataItem[] = [];
  bulge_plot_data: DataItem[] = [];
  tensile_0_data: DataItem[] = [];
  tensile_x_data: number[] = [];
  tensile_y_data: number[] = [];
  correctedTensileParams: any;
  selectedDirectory: any;
  formData: FormData = new FormData();
  selectedFiles: any;
  filesFromFolder: any;
  foldersDetailList: any;
  parentFolderName: any;
  filesPaths: any;
  selectedFolder: String = '';
  dataSheetsArray: any = [];
  nominalAgeArray: any = [];
  uploadLoader: boolean = false;
  tensileExcludedData: { file_name: string; reason: string }[] = [];
  bulgeExcludedData: { file_name: string; reason: string }[] = [];
  tensileInputChanged: any[];
  bulgeInputChanged: any[];
  editingCell: { rowKey: string; colKey: string } | null = null;
  roundingRules: any = {
    Rp02: 2,
    Rm: 2,
    Ag: 4,
    Agt: 4,
    A80: 4,
    E: 1,
    E_c: 2,
    nu: 3,
    nu_c: 5,
    r4_6: 4,
    r8_12: 4,
    r2_20: 4,
    r10_15: 4,
    n4_6: 4,
    n10_15: 4,
    n10_20: 4,
    n2_20: 4,
  };
  dataSheetSpinner: boolean = false;
  tensileRecentlyChangedFiles = new Set<string>();
  bulgeRecentlyChangedFiles = new Set<string>();
  showButtons: boolean = false;
  projectId: string = '';
  private hasChanged: boolean = false;
  basePath: string = 'base';
  originalDataSheetResults: any = {};
  modifiedDataSheetResults: any = {};
  allDataSheets: any;
  selectedDataSheet: any;
  loggedInUser: any;
  animatedDots = '';
  private dotsInterval: any;
  private isAnimating = false;
  dynamicMessage: string = 'Processing';
  tensileDirections: any[] = [];
  selectedDirections: any;
  isHardeningFit: boolean = true;
  isComputingElastic: boolean = false;
  tensileSampleData: any;
  tensileStatsAndResults: any;
  tensileCSVData: any;
  private originalTensileCSVData: any[] = [];


  constructor(
    private dsgHandler: DSGHandler,
    private datasheetService: DataSheetGenerateService,
    private configService: ConfigService,
    private router: Router,
    public toaster: ToastrService,
    public dialog: MatDialog,
    private notificationService: NotificationService,
    private snackBarNotificationService: SnackBarNotificationService,
    private errorHandlerService: ErrorHandlerService,
  ) {
    this.tensileInputChanged = new Array(
      this.tensileFilteredOptions.length,
    ).fill(false);
    this.bulgeInputChanged = new Array(this.bulgeFilteredOptions.length).fill(
      false,
    );

    const selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    selectedProjectId ? (this.projectId = selectedProjectId) : null;
  }

  getAges(tensileStats: any): string[] {
    return Object.keys(tensileStats);
  }

  getProperties(tensileStats: any): string[] {
    const firstAge = Object.keys(tensileStats)[0];
    const properties = Object.keys(tensileStats[firstAge]);
    return properties.filter(prop => prop !== 'datasheet' && prop !== 'nominal_age');
  }

  ngOnInit() {
    this.loggedInUser = JSON.parse(localStorage.getItem('currentUser')!);
    this.getDataSheetSource();
    this.startAnimatingDots();

    if (this.datasheetService.getActivityLogData()) {
      this.dynamicMessage = "Loading"
      this.datasheetId = this.datasheetService.getActivityLogData().datasheetId;
      this.nominalAge = this.datasheetService.getActivityLogData().nominalAge;
      this.nominalAgeArray = this.datasheetService.getActivityLogData().nominalAgeArray;
      this.selectedDataSheet = this.datasheetService.getActivityLogData().selectedDataSheet;
      this.onDataChange(false);
    }
  }

  private startAnimatingDots(): void {
    if (this.isAnimating) return;
    const dotStates = ['', '.', '..', '...'];
    let index = 0;
    this.isAnimating = true;
    this.dotsInterval = setInterval(() => {
      this.animatedDots = dotStates[index];
      index = (index + 1) % dotStates.length;
    }, 500);
  }

  private stopAnimatingDots(): void {
    if (this.dotsInterval) {
      clearInterval(this.dotsInterval);
      this.dotsInterval = null;
      this.isAnimating = false;
      this.animatedDots = '';
    }
  }

  getDataSheetSource() {
    const obj = { base_path: 'base' };
    this.loader = true;

    this.datasheetService.getDataSheetNumber(obj, this.projectId).subscribe({
      next: (data: any) => {
        this.allDataSheets = data.datasheets
        this.dataSheetsArray = data.datasheets
          .sort((a: any, b: any) => parseInt(a.datasheet) - parseInt(b.datasheet))
          .map((datasheet: any) => ({
            ...datasheet,
            tensile_ages: datasheet.tensile_ages
              .map((age: number) => age.toString())
              .sort((a: string, b: string) => parseInt(a) - parseInt(b)),
          }));
        this.loader = false;
      },
      error: (error) => {
        this.notificationService.showError(error);
        this.loader = false;
      },
    });
  }


  onDataSheetChange(datasheetId: string) {
    this.showButtons = false;
    this.nominalAge = -1;
    this.streamLiteLoadData = false;
    this.selectedDataSheet = this.dataSheetsArray.find((sheet: any) => sheet.datasheet === datasheetId);
    this.nominalAgeArray = this.selectedDataSheet ? this.selectedDataSheet.tensile_ages : [];
  }

  async toggleLock(sheet: any, isLocked: boolean): Promise<void> {
    const updatedDatasheet = {
      datasheet: sheet.datasheet,
      tensile_ages: sheet.tensile_ages,
      bulge_ages: sheet.bulge_ages,
      datasheet_path: sheet.datasheet_path,
      tensile_files: sheet.tensile_files,
      bulge_files: sheet.bulge_files,
      flc_files: sheet.flc_files,
      locked: isLocked,
    };

    try {
      const response = await this.datasheetService.updateDatasheet(sheet.id, updatedDatasheet);
      if (!!response) {
        sheet.locked = isLocked;
        const message = isLocked
          ? 'Read only mode activated successfully'
          : 'Editable mode activated successfully';
        this.toaster.success(message, '', {
          positionClass: 'custom-toast-position',
        });
      }
      else {
        this.notificationService.showError('Failed to update datasheet. Please try again.');
      }
    } catch (error) {
      this.notificationService.showError('Failed to update datasheet. Please try again.');
      console.error('Error toggling lock:', error);
    }
  }


  canModify(datasheet: any): boolean {
    if (!datasheet) {
      return false;
    }

    const isServerAdmin = this.loggedInUser.server_role === 'Server Admin';
    const isProjectAdmin = this.loggedInUser.server_role === 'Project Admin';
    const isCreator = datasheet.user_id === this.loggedInUser._id;

    if (isServerAdmin || isProjectAdmin) {
      return true;
    } else if (this.loggedInUser.server_role === 'Default User' && isCreator) {
      return true;
    }

    return false;
  }


  get tensileWeight(): number {
    return this.dataSheetResults.hss_weights_object.tensile_weight;
  }

  set tensileWeight(value: number) {
    this.dataSheetResults.hss_weights_object.tensile_weight = value;
    this.modifiedDataSheetResults.hss_weights_object.tensile_weight = value;

    if (this.dataSheetResults.new_fit_params && Object.keys(this.dataSheetResults.new_fit_params).length > 0) {
      if (!this.dataSheetResults.new_fit_params.hss_weights_object) {
        this.dataSheetResults.new_fit_params.hss_weights_object = {};
      }
      this.dataSheetResults.new_fit_params.hss_weights_object.tensile_weight = value;
    }
  }

  get bulgeWeight(): number {
    return this.dataSheetResults.hss_weights_object.bulge_weight;
  }

  set bulgeWeight(value: number) {
    this.dataSheetResults.hss_weights_object.bulge_weight = value;
    this.modifiedDataSheetResults.hss_weights_object.bulge_weight = value;

    if (this.dataSheetResults.new_fit_params && Object.keys(this.dataSheetResults.new_fit_params).length > 0) {
      if (!this.dataSheetResults.new_fit_params.hss_weights_object) {
        this.dataSheetResults.new_fit_params.hss_weights_object = {};
      }
      this.dataSheetResults.new_fit_params.hss_weights_object.bulge_weight = value;
    }
  }

  get considereWeight(): number {
    return this.dataSheetResults.hss_weights_object.considere_weight;
  }

  set considereWeight(value: number) {
    this.dataSheetResults.hss_weights_object.considere_weight = value;
    this.modifiedDataSheetResults.hss_weights_object.considere_weight = value;

    if (this.dataSheetResults.new_fit_params && Object.keys(this.dataSheetResults.new_fit_params).length > 0) {
      if (!this.dataSheetResults.new_fit_params.hss_weights_object) {
        this.dataSheetResults.new_fit_params.hss_weights_object = {};
      }
      this.dataSheetResults.new_fit_params.hss_weights_object.considere_weight = value;
    }
  }

  get scaleTensileBulge(): boolean {
    return this.scale_TensileBulge;
  }
  set scaleTensileBulge(value: boolean) {
    this.scale_TensileBulge = value;
  }

  getStressFitLowerBound(): number {
    return this.dataSheetResults.corrected_tensile_results.s_min;
  }

  getStressFitUpperBound(): number {
    return this.dataSheetResults.corrected_tensile_results.s_max;
  }

  setStressFitLowerBound(value: number): void {
    // Update original results
    this.dataSheetResults.corrected_tensile_results.s_min = value;
    // Ensure modifiedDataSheetResults is initialized
    if (!this.modifiedDataSheetResults.corrected_tensile_results) {
      this.modifiedDataSheetResults.corrected_tensile_results = JSON.parse(
        JSON.stringify(this.dataSheetResults.corrected_tensile_results)
      );
    }
    // Update modified results
    this.modifiedDataSheetResults.corrected_tensile_results.s_min = value;
  }

  setStressFitUpperBound(value: number): void {
    // Update original results
    this.dataSheetResults.corrected_tensile_results.s_max = value;
    // Ensure modifiedDataSheetResults is initialized
    if (!this.modifiedDataSheetResults.corrected_tensile_results) {
      this.modifiedDataSheetResults.corrected_tensile_results = JSON.parse(
        JSON.stringify(this.dataSheetResults.corrected_tensile_results)
      );
    }
    // Update modified results
    this.modifiedDataSheetResults.corrected_tensile_results.s_max = value;
  }


  resetConfig() {
    this.onDataChange(true);
  }

  onDataChange(reset: boolean) {
    if (this.datasheetId && this.nominalAge !== -1) {
      this.loader = true;
      this.resultLoader = true;
      const siteId = 1;
      this.dataSheetResults = null;
      this.tensileExcludedData = [];
      this.bulgeExcludedData = [];
      this.originalDataSheetResults = {};
      this.modifiedDataSheetResults = {};
      const datasheetId = Number(this.datasheetId);
      const nominalAge = Number(this.nominalAge);
      this.datasheetService.getDatasheet(siteId, this.projectId, datasheetId, nominalAge, reset).subscribe({
        next: (response) => {
          try {
            this.dataSheetResults = response.datasheet[0];

            if (typeof this.dataSheetResults.corrected_tensile_results === 'string') {
              this.dataSheetResults.corrected_tensile_results = JSON.parse(this.dataSheetResults.corrected_tensile_results);
            }

            this.originalDataSheetResults = JSON.parse(JSON.stringify(this.dataSheetResults));
            this.modifiedDataSheetResults = JSON.parse(JSON.stringify(this.dataSheetResults));

            this.showButtons = true;

            if (this.dataSheetResults) {
              this.tensilePropertyTable();
              this.tensileStats();
              this.process_TensileData(
                this.dataSheetResults.tensile_files,
                this.dataSheetResults.tensile_plot_data_path,
              );
              this.process_BulgeData(
                this.dataSheetResults.bulge_files,
                this.dataSheetResults.bulge_plot_data_path,
              );
              this.process_correctedTensileResults(
                this.dataSheetResults.tensile_files,
                this.dataSheetResults.corrected_tensile_results,
              );

              this.updateMetadata();

              setTimeout(() => {
                this.computeAndSaveChanges(false);
              }, 2000);


              this.updateFitParameters();
            }

            if (this.dataSheetResults.preview) {
              this.dataSheetGenerated = true;
            } else {
              this.dataSheetGenerated = false;
            }
            this.streamLiteLoadData = true;
          } catch (error) {
            console.error('Error processing the datasheet:', error);
            this.showButtons = false;
            this.notificationService.showError(error);
            this.dataSheetResults = null;
            this.streamLiteLoadData = false;
            this.resultLoader = false;
          } finally {
            this.loader = false;
          }
        },
        error: (error) => {
          console.error(error);
          this.notificationService.showError(error);
          this.dataSheetResults = null;
          this.loader = false;
          this.streamLiteLoadData = false;
          this.showButtons = false;
          this.resultLoader = false;
        },
      });
    }
  }

  async tensileStats(): Promise<any> {
    try {
      const csvData = await this.dsgHandler.readTensileCSV(
        this.configService.SelectedSiteId || '',
        this.configService.SelectedProjectId || '',
        this.datasheetId,
        this.nominalAge,
        this.dataSheetResults
      );

      this.tensileCSVData = csvData;
      this.originalTensileCSVData = [...csvData];

      const statsData = await this.dsgHandler.fetchTensileSampleData(
        this.tensileCSVData,
        this.configService.SelectedSiteId || '',
        this.configService.SelectedProjectId || '',
        this.datasheetId,
        this.nominalAge
      );

      if (statsData.csv_data) {
        this.tensileStatsAndResults = statsData.csv_data
        this.tensileStatsAndResults.tensile_stats = Object.fromEntries(
          Object.entries(this.tensileStatsAndResults.tensile_stats)
            .filter(([key]) => !['datasheet', 'nominal_age', 'load_direction'].includes(key))
        );
      }
    } catch (error) {
      this.notificationService.showError(error);
    }
  }

  getStatProperties(direction: string): string[] {
    const normalizedDirection = parseFloat(direction).toString();
    if (this.tensileStatsAndResults?.tensile_stats?.[normalizedDirection]) {
      return Object.keys(this.tensileStatsAndResults.tensile_stats[normalizedDirection]);
    }
    return [];
  }

  getNormalizedDirection(direction: string): string {
    return parseFloat(direction).toString();
  }

  getTensileRoundedValue(value: number, column: string): string {
    return value.toFixed(2);
  }

  async refreshTensileStats(): Promise<void> {
    try {
      const statsData = await this.dsgHandler.fetchTensileSampleData(
        this.tensileCSVData,
        this.configService.SelectedSiteId || '',
        this.configService.SelectedProjectId || '',
        this.datasheetId,
        this.nominalAge
      );

      if (statsData.csv_data) {
        this.tensileStatsAndResults = statsData.csv_data;
        this.tensileStatsAndResults.tensile_stats = Object.fromEntries(
          Object.entries(this.tensileStatsAndResults.tensile_stats).filter(
            ([key]) => !['datasheet', 'nominal_age', 'load_direction'].includes(key)
          )
        );
      }
    } catch (error) {
      this.notificationService.showError(error);
    }
  }
  async tensilePropertyTable(): Promise<void> {
    const siteID = this.configService.SelectedSiteId || '';
    const projectId = this.configService.SelectedProjectId || '';
    const datasheetId = this.datasheetId;
    const nominalAge = this.nominalAge;

    if (!siteID || !projectId || !datasheetId || !nominalAge) {
      this.notificationService.showError('Missing required parameters for fetching tensile data');
      return;
    }

    if (!this.dataSheetResults || !this.dataSheetResults.tensile_sample_data) {
      this.notificationService.showError('Incomplete tensile properties results');
      return;
    }

    try {
      const csvData = await this.dsgHandler.readTensileCSV(siteID, projectId, datasheetId, nominalAge, this.dataSheetResults);
      const excludedFiles = this.dataSheetResults.new_fit_params?.excluded_tensile || [];
      this.tensileSampleData = csvData.map((item: any) => {
        const filteredItem = Object.fromEntries(
          Object.entries(item).filter(
            ([key]) => !['datasheet', 'nominal_age', 'load_direction'].includes(key)
          )
        );
        const fileName = item.file_name.split('/').pop();
        const isExcluded = excludedFiles.includes(fileName);
        return {
          ...filteredItem,
          sampleId: this.dsgHandler.extractFileName(item.file_name),
          included: isExcluded ? 'no' : 'yes'
        };
      });
    } catch (error) {
      this.notificationService.showError(error);
    }
  }

  getTensilePropertyColumnNames(jsonData: any): string[] {
    return this.dsgHandler.getTensilePropertyColumnNames(jsonData);
  }

  updateTensileSampleInclusion(fileName: string): void {
    this.dsgHandler.updateTensileSampleInclusion(fileName, this.tensileSampleData, this.tensileExcludedData);
  }

  sortTensileSampleData(data: any[] = this.tensileSampleData): any[] {
    return this.dsgHandler.sortTensileSampleData(data);
  }

  getFilteredAndSortedTensileData(direction: string): any[] {
    return this.dsgHandler.getFilteredAndSortedTensileData(direction, this.tensileSampleData);
  }

  getDirectionFromSampleId(sampleId: string): string {
    return this.dsgHandler.getDirectionFromSampleId(sampleId);
  }

  updateMetadata() {
    if (
      this.dataSheetResults.metadata &&
      Object.keys(this.dataSheetResults.metadata).length > 0
    ) {
      let metadata = this.dataSheetResults.metadata;
      this.productName = metadata.commercial_name;
      this.gauge = metadata.gauge;
      this.m_source = metadata.m_source;
      this.branchName = metadata.branch_name;
      this.specName = metadata.spec_name;

      this.latestRevalidationDate = new Date(metadata.latest_revalidation);
      this.validUntilDate = new Date(metadata.valid_until);
    } else {
      this.resetMetaDataChanges();
    }
  }

  resetMetaDataChanges(): void {
    const defaultValues = {
      productName: 'Default commercial name',
      gauge: 1,
      m_source: 'Europe',
      branchName: 'production',
      specName: 'specA',
      latestRevalidationDate: new Date('2024-01-01'),
      validUntilDate: new Date('2024-01-01'),
    };

    Object.assign(this, defaultValues);

    this.modifiedDataSheetResults.metadata = {
      commercial_name: this.productName,
      gauge: this.gauge,
      m_source: this.m_source,
      latest_revalidation: this.formatDate(this.latestRevalidationDate),
      valid_until: this.formatDate(this.validUntilDate),
      spec_name: this.specName,
      branch_name: this.branchName,
    };
  }


  updateFitParameters() {
    if (
      this.dataSheetResults.new_fit_params &&
      Object.keys(this.dataSheetResults.new_fit_params).length > 0
    ) {
      let gradients = this.dataSheetResults.new_fit_params.gradients;
      this.tensile_grad = gradients.tensile_grad;
      this.bulge_grad = gradients.bulge_grad;
      this.tensile_n_grad = gradients.tensile_n_grad;
      this.bulge_n_grad = gradients.bulge_n_grad;
      this.recomputeRp02 = this.dataSheetResults.new_fit_params.recompute;
      this.getTensileExcludedData(
        this.dataSheetResults.tensile_files,
        this.dataSheetResults.new_fit_params.tensileExcludedData,
      );
      this.getBulgeExcludedData(
        this.dataSheetResults.bulge_files,
        this.dataSheetResults.new_fit_params.bulgeExcludedData,
      );
    }
  }

  getTensileExcludedData(allFiles: string[], excludedData: any[]) {
    this.tensileSelectedOptions = [];
    this.tensileExcludedData = excludedData;
    const excludedFileNames = new Set(
      excludedData.map((item) => item.file_name),
    );
    allFiles.forEach((file) => {
      if (!excludedFileNames.has(file)) {
        this.tensileSelectedOptions.push(file);
      }
    });
    this.tensilePanel = true;
    this.tensile_GraphPlot(
      this.tensileSelectedOptions,
      this.dataSheetResults.tensile_plot_data_path,
    );
  }

  getBulgeExcludedData(allFiles: string[], excludedData: any[]) {
    this.bulgeSelectedOptions = [];
    this.bulgeExcludedData = excludedData;
    const excludedFileNames = new Set(
      excludedData.map((item) => item.file_name),
    );
    allFiles.forEach((file) => {
      if (!excludedFileNames.has(file)) {
        this.bulgeSelectedOptions.push(file);
      }
    });
    this.bulgePanel = true;
    this.bulge_GraphPlot(
      this.bulgeSelectedOptions,
      this.dataSheetResults.bulge_plot_data_path,
    );
    this.updateAvgBulgeScaleFactor();
  }

  process_TensileData(
    tensileFiles: string[],
    tensilePlotDataPath: string,
  ): void {
    this.tensileSelectedOptions = [...tensileFiles];
    this.tensileFilteredOptions = tensileFiles.filter(
      (option) => !this.tensileSelectedOptions.includes(option),
    );
    this.getDirections(this.modifiedDataSheetResults);
    this.tensile_GraphPlot(this.tensileSelectedOptions, tensilePlotDataPath);
  }

  onDirectionToggle(direction: string, isChecked: boolean): void {
    this.selectedDirections[direction] = isChecked;
    this.tensile_GraphPlot(this.tensileSelectedOptions, this.dataSheetResults.tensile_plot_data_path);
  }

  isDirectionDisabled(direction: string): boolean {
    if (!this.dataSheetResults?.tensile_files) return false;
    const directionFiles = this.dataSheetResults.tensile_files.filter(
      (file: string) => file.split('_')[3] === direction
    );
    if (directionFiles.length === 0) return false;
    const excludedFiles = this.tensileExcludedData.map(item => item.file_name);
    return directionFiles.every((file: string) => excludedFiles.includes(file));
  }


  getDirections(dataSheetResults: any): void {
    const tensileFiles = dataSheetResults.tensile_files || [];
    const excludedTensileFiles = dataSheetResults.new_fit_params?.excluded_tensile || [];
    const directions = tensileFiles.map((file: any) => {
      const parts = file.split('_');
      return parts[3];
    });
    const uniqueDirections = Array.from(new Set(directions));
    this.tensileDirections = uniqueDirections;
    this.selectedDirections = {};
    uniqueDirections.forEach((direction: any) => {
      const directionFiles = tensileFiles.filter(
        (file: any) => file.split('_')[3] === direction
      );
      const allExcluded = directionFiles.every((file: any) =>
        excludedTensileFiles.includes(file)
      );
      this.selectedDirections[direction] = !allExcluded;
    });
  }


  tensile_GraphPlot(tensileSelectedOptions: string[], tensilePlotDataPath: string): void {
    let obj = {
      project_id: this.projectId,
      datasheet: this.datasheetId,
      nominal_age: this.nominalAge,
      file_path: tensilePlotDataPath,
    };

    this.datasheetService.readCSV(obj).subscribe({
      next: (response: CSVResponse) => {
        const data = response.csv_data;
        this.tensile_plot_data = data;

        const figData: {
          x: number[];
          y: number[];
          mode: string;
          name: string;
          visible?: 'true' | 'legendonly';
        }[] = [];

        for (const includedSample of tensileSelectedOptions) {
          const fileLines = data.filter(
            (item) => item.file_name === includedSample
          );

          if (fileLines.length > 0) {
            const xdata = fileLines.map((item) => parseFloat(item.xdata));
            const ydata = fileLines.map((item) => parseFloat(item.ydata));
            const fileDirection = includedSample.split('_')[3];

            figData.push({
              x: xdata,
              y: ydata,
              mode: 'lines',
              name: includedSample,
              visible: this.selectedDirections[fileDirection] ? 'true' : 'legendonly',
            });
          }
        }

        const layout = {
          title: 'Stress vs. strain plot of include tensile tests',
          xaxis: {
            title: 'eng.strain [-]',
          },
          yaxis: {
            title: 'eng.stress [MPa]',
          },
          legend: { x: 1.1, y: 1.0 },
          showlegend: true,
        };

        Plotly.newPlot('plotly-div-1', figData, layout);
      },
      error: (error) => {
        console.error('Error loading CSV data:', error);
        this.notificationService.showError(error);
      },
    });
  }


  process_BulgeData(bulgeFiles: string[], bulgePlotDataPath: string): void {
    this.bulgeSelectedOptions = [...bulgeFiles];
    this.bulgeFilteredOptions = bulgeFiles.filter(
      (option) => !this.bulgeSelectedOptions.includes(option),
    );
    this.bulge_GraphPlot(this.bulgeSelectedOptions, bulgePlotDataPath);
  }

  bulge_GraphPlot(
    bulgeSelectedOptions: string[],
    bulgePlotDataPath: string,
  ): void {
    let obj = {
      project_id: this.projectId,
      datasheet: this.datasheetId,
      nominal_age: this.nominalAge,
      file_path: bulgePlotDataPath,
    };
    this.datasheetService.readCSV(obj).subscribe({
      next: (response: CSVResponse) => {
        const data = response.csv_data;
        this.bulge_plot_data = data;
        const included_samples = this.sortOptions(bulgeSelectedOptions);
        const figData: {
          x: number[];
          y: number[];
          mode: string;
          name: string;
        }[] = [];
        for (const includedSample of included_samples) {
          const fileLines = data.filter(
            (item) => item.file_name === includedSample,
          );
          if (fileLines.length > 0) {
            const xdata = fileLines.map((item) => parseFloat(item.xdata));
            const ydata = fileLines.map((item) => parseFloat(item.ydata));
            figData.push({
              x: xdata,
              y: ydata,
              mode: 'lines',
              name: includedSample,
            });
          }
        }
        const layout = {
          title: 'Stress vs. strain plot of include bulge tests', // Updated title
          xaxis: {
            title: 'absolute value of log. plastic thickness strain [-]', // X-axis label
          },
          yaxis: {
            title: 'biaxial true stress [MPa]', // Y-axis label
          },
          legend: { x: 1.1, y: 1.0 }, // Legend position
          showlegend: true,
        };
        Plotly.newPlot('plotly-div-2', figData, layout);
      },
      error: (error) => {
        console.error('Error loading CSV data:', error);
        this.notificationService.showError(error);
      },
    });
  }

  add(event: any, type: string): void {
    if (type == 'tensile') {
      const value = event.value.trim();
      if (value && !this.tensileSelectedOptions.includes(value)) {
        this.tensileSelectedOptions.push(value);
        this.tensileFilteredOptions = this.tensileFilteredOptions.filter(
          (option) => option !== value,
        );
        this.tensile_GraphPlot(
          this.tensileSelectedOptions,
          this.dataSheetResults.tensile_plot_data_path,
        );
      }
      event.input.value = '';
    }
    if (type == 'bulge') {
      const value = event.value.trim();
      if (value && !this.bulgeSelectedOptions.includes(value)) {
        this.bulgeSelectedOptions.push(value);
        this.bulgeFilteredOptions = this.bulgeFilteredOptions.filter(
          (option) => option !== value,
        );
        this.bulge_GraphPlot(
          this.bulgeSelectedOptions,
          this.dataSheetResults.bulge_plot_data_path,
        );
      }
      event.input.value = '';
    }
  }

  removeAll(type: string): void {
    if (type === 'tensile') {
      // Get unique directions dynamically
      this.getDirections(this.modifiedDataSheetResults); // Ensure directions are up-to-date
      const numDirections = this.tensileDirections.length;

      if (this.tensileSelectedOptions.length > numDirections) { // Ensure enough files to leave one per direction
        // Map one file per direction from tensileCSVData
        const directionsMap = new Map<string, string>(); // Map direction (as string) to a file name
        this.tensileCSVData.forEach((item: any) => {
          const fileName = this.dsgHandler.extractFileName(item.file_name);
          if (this.tensileSelectedOptions.includes(fileName)) {
            const direction = fileName.split('_')[3]; // Extract direction from file name
            if (!directionsMap.has(direction)) {
              directionsMap.set(direction, fileName); // Keep first file for each direction
            }
          }
        });

        // Get files to keep (one per direction)
        const filesToKeep = Array.from(directionsMap.values());

        // Exclude all files except those in filesToKeep
        this.tensileSelectedOptions.forEach((option) => {
          if (!filesToKeep.includes(option)) {
            const existingIndex = this.tensileExcludedData.findIndex(
              (item) => item.file_name === option
            );
            if (existingIndex === -1) {
              this.tensileExcludedData.push({ file_name: option, reason: '' });
            }
            this.updateTensileSampleInclusion(option);
          }
        });

        // Update tensileSelectedOptions to keep only the selected files
        this.tensileSelectedOptions = filesToKeep;

        // Filter tensileCSVData to keep only the selected files
        this.tensileCSVData = this.tensileCSVData.filter(
          (item: any) => filesToKeep.includes(this.dsgHandler.extractFileName(item.file_name))
        );

        this.tensilePanel = true;
        this.getDirections(this.modifiedDataSheetResults); // Refresh directions after update
        this.tensile_GraphPlot(
          this.tensileSelectedOptions,
          this.dataSheetResults.tensile_plot_data_path
        );
        this.updateModifiedDataSheetResults('tensile');
        this.refreshTensileStats();
      }
    } else if (type === 'bulge') {
      if (this.bulgeSelectedOptions.length > 1) {
        this.bulgeSelectedOptions.slice(1).forEach((option) => {
          const existingIndex = this.bulgeExcludedData.findIndex(
            (item) => item.file_name === option
          );
          if (existingIndex === -1) {
            this.bulgeExcludedData.push({ file_name: option, reason: '' });
          }
        });
        this.bulgeSelectedOptions = this.bulgeSelectedOptions.slice(0, 1);
        this.bulgePanel = true;
        this.bulge_GraphPlot(
          this.bulgeSelectedOptions,
          this.dataSheetResults.bulge_plot_data_path
        );
        this.updateModifiedDataSheetResults('bulge');
        this.updateAvgBulgeScaleFactor();
      }
    }
  }


  remove(option: string, type: string): void {
    if (type === 'tensile') {
      if (this.tensileSelectedOptions.length > 1) {
        const index = this.tensileSelectedOptions.indexOf(option);
        if (index >= 0) {
          this.tensileSelectedOptions.splice(index, 1);
          this.tensileFilteredOptions.push(option);
          this.tensileExcludedData.push({ file_name: option, reason: '' });
          this.tensilePanel = true;

          this.tensileCSVData = this.tensileCSVData.filter(
            (item: any) => this.dsgHandler.extractFileName(item.file_name) !== option
          );

          this.updateModifiedDataSheetResults('tensile');
          this.getDirections(this.modifiedDataSheetResults);
          this.updateTensileSampleInclusion(option);
          this.tensile_GraphPlot(this.tensileSelectedOptions, this.dataSheetResults.tensile_plot_data_path);
          this.refreshTensileStats();
        }
      } else {
        this.notificationService.showError('At least one file should remain in the tensile list');
      }
    } else if (type === 'bulge') {
      if (this.bulgeSelectedOptions.length > 1) {
        const index = this.bulgeSelectedOptions.indexOf(option);
        if (index >= 0) {
          this.bulgeSelectedOptions.splice(index, 1);
          this.bulgeFilteredOptions.push(option);
          this.bulgeExcludedData.push({ file_name: option, reason: '' });
          this.bulgePanel = true;
          this.bulge_GraphPlot(
            this.bulgeSelectedOptions,
            this.dataSheetResults.bulge_plot_data_path,
          );
          this.updateModifiedDataSheetResults('bulge');
          this.updateAvgBulgeScaleFactor();
        }
      } else {
        this.notificationService.showError('At least one file should remain in the bulge list.');
      }
    }
  }

  sortOptions(optionArray: string[]) {
    return optionArray.sort((a, b) => {
      const regex = /(\d+|[a-zA-Z]+)/g;
      const segmentsA = a.match(regex) || [];
      const segmentsB = b.match(regex) || [];

      for (let i = 0; i < Math.min(segmentsA.length, segmentsB.length); i++) {
        const segA = segmentsA[i];
        const segB = segmentsB[i];

        if (!isNaN(Number(segA)) && !isNaN(Number(segB))) {
          const numA = Number(segA);
          const numB = Number(segB);
          if (numA !== numB) {
            return numA - numB;
          }
        } else {
          const comp = segA.localeCompare(segB);
          if (comp !== 0) {
            return comp;
          }
        }
      }
      return a.localeCompare(b);
    });
  }

  updateModifiedDataSheetResults(type: string): void {
    if (type === 'tensile') {
      this.modifiedDataSheetResults.new_fit_params = {
        excluded_tensile: this.tensileExcludedData.map((file) => file.file_name),
      };
    } else if (type === 'bulge') {
      this.modifiedDataSheetResults.new_fit_params = {
        excluded_bulge: this.bulgeExcludedData.map((file) => file.file_name),
      };
    }
  }


  selected(key: any, type: string): void {
    if (type == 'tensile') {
      const value = key;
      if (!this.tensileSelectedOptions.includes(value)) {
        this.tensileSelectedOptions.push(value);
        this.tensileFilteredOptions = this.tensileFilteredOptions.filter(
          (option) => option !== value,
        );
      }
    }
    if (type == 'bulge') {
      const value = key;
      if (!this.bulgeSelectedOptions.includes(value)) {
        this.bulgeSelectedOptions.push(value);
        this.bulgeFilteredOptions = this.bulgeFilteredOptions.filter(
          (option) => option !== value,
        );
        this.bulge_GraphPlot(
          this.bulgeSelectedOptions,
          this.dataSheetResults.bulge_plot_data_path,
        );
        this.updateAvgBulgeScaleFactor();
      }
    }
  }

  focusOptions(key: string) {
    if (key === 'tensile') {
      this.tensilePanel = !this.tensilePanel;
    } else {
      this.bulgePanel = !this.bulgePanel;
    }
  }

  toggleMainHeader() {
    this.showMainHeader = !this.showMainHeader;
    this.toggleHeaderButton = this.showMainHeader
      ? 'expand_less'
      : 'expand_more';
  }

  getSignatures(): string[] {
    return this.dataSheetResults
      ? Object.keys(this.dataSheetResults.hss_complete_params)
      : [];
  }

  parametersWithOutParam_value(): string[] {
    const allParams = new Set<string>();
    const signatures = this.getSignatures();
    for (const signature of signatures) {
      const params = Object.keys(
        this.dataSheetResults.hss_complete_params[signature],
      );
      params.forEach((param) => {
        if (param !== 'param_value') {
          allParams.add(param);
        }
      });
    }
    return Array.from(allParams);
  }

  parametersOnlyParam_value(): string[] {
    const allParams = new Set<string>();
    const signatures = this.getSignatures();
    for (const signature of signatures) {
      const params = Object.keys(
        this.dataSheetResults.hss_complete_params[signature],
      );
      params.forEach((param) => {
        if (param == 'param_value') {
          allParams.add(param);
        }
      });
    }
    return Array.from(allParams);
  }

  enableEdit(param: string, signature: string): void {
    this.editState[`${param}-${signature}`] = true;
    setTimeout(() => {
      const inputElement = document.querySelector(
        `input[data-param="${param}"][data-signature="${signature}"]`,
      );
      if (inputElement instanceof HTMLElement) {
        inputElement.focus();
      }
    }, 0);
  }

  disableEdit(param: string, signature: string): void {
    this.editState[`${param}-${signature}`] = false;
  }

  isEditing(param: string, signature: string): boolean {
    return !!this.editState[`${param}-${signature}`];
  }

  formatDate(date: Date): string {
    if (!date) return '';
    const year = date.getFullYear();
    const month = ('0' + (date.getMonth() + 1)).slice(-2);
    const day = ('0' + date.getDate()).slice(-2);
    return `${year}-${month}-${day}`;
  }

  generateDataSheet(fit_type: string) {
    this.dataSheetSpinner = true;
    if (!this.isMetadataComplete()) {
      this.dataSheetSpinner = false;
      this.notificationService.showError('Metadata is incomplete. Please complete all required fields.');
      return;
    }

    this.dataSheetGenerated = false;
    let obj = {
      datasheet: Number(this.datasheetId),
      commercial_name: this.productName,
      gauge: this.gauge,
      m_source: this.m_source,
      latest_revalidation: this.formatDate(this.latestRevalidationDate),
      valid_until: this.formatDate(this.validUntilDate),
      spec_name: this.specName,
      branch_name: this.branchName,
    };
    let siteId = 1;

    // Proceed with API call
    this.datasheetService
      .generateDataSheet(
        siteId,
        this.projectId,
        this.datasheetId,
        this.nominalAge,
        obj,
        fit_type,
      )
      .subscribe({
        next: (results) => {
          this.dataSheetGenerated = true;
          this.dataSheetSpinner = false;
          this.dataSheetResults.pdf_path = results.datasheet_path.datasheet;
        },
        error: (error) => {
          console.error(error);
          this.dataSheetSpinner = false;
          this.dataSheetGenerated = false;
          this.notificationService.showError('Unable to generate datasheet, please try again.');
        },
      });
  }

  private isMetadataComplete(): boolean {
    if (
      !this.datasheetId ||
      !this.productName ||
      !this.gauge ||
      !this.m_source ||
      !this.latestRevalidationDate ||
      !this.validUntilDate ||
      !this.specName ||
      !this.branchName
    ) {
      return false;
    }
    return true;
  }

  onFocus() {
    this.hasChanged = false;
  }
  onBlur() {
    if (this.hasChanged) {
      this.saveMetadata();
    }
  }
  onChange() {
    this.hasChanged = true;
    this.dataSheetGenerated = false;
  }

  saveMetadata() {
    if (!this.isMetadataChanged()) {
      return;
    }
    let obj = {
      commercial_name: this.productName,
      gauge: this.gauge,
      m_source: this.m_source,
      latest_revalidation: this.formatDate(this.latestRevalidationDate),
      valid_until: this.formatDate(this.validUntilDate),
      spec_name: this.specName,
      branch_name: this.branchName,
    };

    this.dataSheetGenerated = false;
    this.modifiedDataSheetResults.metadata = JSON.parse(JSON.stringify(obj));
  }

  private isMetadataChanged(): boolean {
    const newMetadata: any = {
      commercial_name: this.productName,
      gauge: this.gauge,
      m_source: this.m_source,
      latest_revalidation: this.formatDate(this.latestRevalidationDate),
      valid_until: this.formatDate(this.validUntilDate),
      spec_name: this.specName,
      branch_name: this.branchName,
    };

    for (let key in newMetadata) {
      if (
        newMetadata[key] === '' ||
        newMetadata[key] === null ||
        newMetadata[key] === undefined
      ) {
        const message = `${key.replace('_', ' ')} should not be empty`;
        this.notificationService.showError(message);

        return false;
      }
    }

    for (let key in newMetadata) {
      if (newMetadata[key] !== this.dataSheetResults.metadata[key]) {
        return true;
      }
    }
    return false;
  }

  previewDataSheet() {
    const object = {
      project_id: this.projectId,
      datasheet: this.datasheetId,
      nominal_age: this.nominalAge,
      file_path: this.dataSheetResults.pdf_path,
    };

    this.datasheetService.previewDatasheet(object).subscribe({
      next: (response: any) => {
        if (response.file_name && response.file_url) {
          const pdfUrl = `${environment.apiUrl}/${response.file_url}`;
          window.open(pdfUrl, '_blank');
        } else {
          console.error(
            'Invalid response format. Missing file_name or file_url.',
          );
        }
      },
      error: (error) => {
        console.error('Error previewing datasheet:', error);
        this.notificationService.showError(error);
      },
    });
  }

  downloadDataSheetResults() {
    let datasheet = this.datasheetId.toString();

    this.datasheetService
      .downloadDatasheet(this.projectId, datasheet)
      .subscribe({
        next: (response: Blob) => {
          const blobUrl = window.URL.createObjectURL(response);
          const link = document.createElement('a');
          link.href = blobUrl;
          link.setAttribute('download', datasheet + '_results.zip');
          document.body.appendChild(link);
          link.click();
          window.URL.revokeObjectURL(blobUrl);
          link.remove();
        },
        error: (error) => {
          console.error('Error downloading datasheet results:', error);
          this.notificationService.showError(error);
        },
      });
  }

  process_correctedTensileResults(tensile_files: string[], results: any) {
    if (tensile_files && tensile_files.length > 0) {
      const defaultFile = tensile_files.find(
        (file) => file === results.sample_name,
      );
      this.selectedTensileSample = defaultFile ? defaultFile : tensile_files[0];
      setTimeout(() => {
        this.generateCorrectedTensileGraph(results);
      }, 2000);
    }
  }

  generateCorrectedTensileGraph(result: any) {
    const data = {
      xdata: result.xdata,
      ydata: result.ydata,
      x_E: result.x_E,
      y_E: result.y_E,
      x_E_Rp02: result.x_E_Rp02.map((x: any) => x + 0.002),
      sig_Rp02: result.sig_Rp02,
      Agt: result.Agt,
      Rm: result.Rm,
      sample_name: result.sample_name,
      s_min: result.s_min,
      s_max: result.s_max,
      E: result.df_results[0].E,
      eps_Rp02: 0,
    };
    data['eps_Rp02'] = 0.2 / 100 + data.sig_Rp02 / data.E;

    const trace1 = {
      x: data.xdata,
      y: data.ydata,
      mode: 'lines',
      name: data.sample_name,
      line: { color: 'blue' },
    };

    const trace2 = {
      x: data.x_E,
      y: data.y_E,
      mode: 'lines',
      name: 'Elastic Modulus',
      line: { color: 'red' },
    };

    const traceElasticModulusFitBoundary = {
      x: [data.s_min / data.E, data.s_max / data.E],
      y: [data.s_min, data.s_max],
      mode: 'markers',
      name: 'Elastic Modulus fit boundary',
      marker: { color: 'red' },
    };

    const slope = (data.y_E[1] - data.y_E[0]) / (data.x_E[1] - data.x_E[0]);
    const x_Rp02_start = data.eps_Rp02 - data.sig_Rp02 / data.E;
    const x_Rp02_end = data.eps_Rp02 + data.sig_Rp02 / data.E;

    const traceRp02TangentModulus = {
      x: [x_Rp02_start, x_Rp02_end],
      y: [
        data.sig_Rp02 - slope * (data.eps_Rp02 - x_Rp02_start),
        data.sig_Rp02 + slope * (x_Rp02_end - data.eps_Rp02),
      ],
      mode: 'lines',
      name: 'Rp02 tangent modulus',
      line: { color: 'green' },
    };

    const traceRp02Point = {
      x: [data.x_E_Rp02[0]],
      y: [data.sig_Rp02[0]],
      mode: 'markers',
      name: 'Rp02',
      marker: { color: 'purple', size: 8 },
    };

    const traceAgtRm = {
      x: [data.Agt],
      y: [data.Rm],
      mode: 'markers',
      name: 'Agt/Rm',
      marker: { color: 'orange', size: 8 },
    };

    const figData = [
      trace1,
      trace2,
      traceElasticModulusFitBoundary,
      traceRp02TangentModulus,
      traceRp02Point,
      traceAgtRm,
    ];
    const layout = {
      title: 'Stress/strain plot of ' + data.sample_name,
      xaxis: {
        title: 'eng. strain [-]',
      },
      yaxis: {
        title: 'eng. stress [MPa]',
      },
      legend: {
        x: 1.1,
        y: 1.0,
      },
    };

    Plotly.newPlot('plotly-div-3', figData, layout);
  }

  // Corrected Tensile Results
  get autoFitResult(): any {
    return this.dataSheetResults?.corrected_tensile_results?.df_initial_results?.[0] || {};
  }

  get adjustedResult(): any {
    return this.dataSheetResults?.corrected_tensile_results?.df_results?.[0] || {};
  }


  getCorrectedSignatures(): string[] {
    const autoFit = this.autoFitResult;
    if (autoFit && Object.keys(autoFit).length) {
      return Object.keys(autoFit).filter(
        key => !["file_name", "datasheet", "nominal_age", "load_direction"].includes(key)
      );
    }
    return [];
  }

  getRoundedValue(value: any, signature: string): any {
    if (value === null || value === undefined) {
      return value;
    }
    const digits = this.roundingRules[signature];
    return digits !== undefined ? parseFloat(value.toFixed(digits)) : value;
  }
  getValueAdjusted(signature: string): any {
    const result = this.adjustedResult;
    if (result == null || result[signature] === null || result[signature] === undefined) {
      return null;
    }
    const value = result[signature];
    const digits = this.roundingRules[signature];
    return digits !== undefined ? parseFloat(value.toFixed(digits)) : value;
  }

  setValueAdjusted(signature: string, value: any): void {
    if (value == null) {
      this.snackBarNotificationService.openSnackBar(
        "Input cannot be empty, preserving previous value.",
        "error"
      );
      return;
    }
    if (!this.isNumeric(value)) {
      this.snackBarNotificationService.openSnackBar(
        "Input must be numeric.",
        "error"
      );
      return;
    }
    const numericValue = Number(value);
    const digits = this.roundingRules[signature];
    const roundedValue =
      digits !== undefined
        ? parseFloat(numericValue.toFixed(digits))
        : numericValue;
    let result = this.adjustedResult;
    if (result) {
      result[signature] = roundedValue;
    }
  }

  fileChangeOnCorrectedResults(): void {
    let obj = {
      project_id: this.projectId,
      datasheet: Number(this.datasheetId),
      nominal_age: Number(this.nominalAge),
      selected_sample: this.selectedTensileSample,
      corrected_tensile_results: {},
      s_min: 20,
      s_max: 60,
      recompute_Rp02: false,
    };

    this.datasheetService.computeElasticModule(obj).subscribe({
      next: (results) => {
        if (results.correct_data) {
          this.dataSheetResults.corrected_tensile_results = results.correct_data;
          this.modifiedDataSheetResults.corrected_tensile_results = JSON.parse(JSON.stringify(results.correct_data));
          if (!this.modifiedDataSheetResults.corrected_tensile_results) {
            this.modifiedDataSheetResults.corrected_tensile_results = JSON.parse(
              JSON.stringify(this.dataSheetResults.corrected_tensile_results)
            );
          }
          this.modifiedDataSheetResults.corrected_tensile_results.sample_name = this.selectedTensileSample;

          this.process_correctedTensileResults(
            this.dataSheetResults.tensile_files,
            results.correct_data,
          );
        }
      },
      error: (error) => {
        console.error('Error computing elastic module:', error);
        this.notificationService.showError(error);
      },
    });
  }

  computeElasticModule() {
    this.isComputingElastic = true;
    if (!this.correctedTensileParams) {
      this.correctedTensileParams = {};
    }
    this.correctedTensileParams = { ...this.adjustedResult };
    let obj = {
      project_id: this.projectId,
      datasheet: Number(this.datasheetId),
      nominal_age: Number(this.nominalAge),
      selected_sample: this.selectedTensileSample,
      corrected_tensile_results: this.correctedTensileParams,
      s_min: this.dataSheetResults.corrected_tensile_results.s_min,
      s_max: this.dataSheetResults.corrected_tensile_results.s_max,
      recompute_Rp02: this.recomputeRp02,
    };

    this.datasheetService.computeElasticModule(obj).subscribe({
      next: (results) => {
        if (results.correct_data) {
          this.dataSheetResults.corrected_tensile_results =
            results.correct_data;
          this.process_correctedTensileResults(
            this.dataSheetResults.tensile_files,
            results.correct_data,
          );
          this.isComputingElastic = false;
        }
      },
      error: (error) => {
        console.error('Error computing elastic module:', error);
        this.errorHandlerService.handleError(error);
        this.isComputingElastic = false;
      },
    });
  }

  switchEditMode(colIndex: number, signature: string, mode: boolean) {
    const cellKey = `${colIndex}-${signature}`;
    this.isEditingCR[cellKey] = mode;
    if (mode) {
      setTimeout(() => {
        const inputElement = document.querySelector(
          `input.editable-input[data-param="${cellKey}"][data-signature="${signature}"]`
        );
        if (inputElement instanceof HTMLElement) {
          inputElement.focus();
        }
      }, 0);
    } else {
      this.generateCorrectedTensileGraph(this.dataSheetResults.corrected_tensile_results);
    }
  }

  trackBySignature(index: number, item: any): any {
    return item;
  }

  async computeAndSaveChanges(recompute: boolean): Promise<boolean> {
    this.resultLoader = true;
    this.dynamicMessage = 'Processing';
    try {

      // Step 1: Call computeLocalFit
      const fitSuccess = await this.computeLocalFit(recompute);
      if (!fitSuccess) {
        this.resultLoader = false;
        return false;
      }
      // Step 2: Call saveMetadataChanges
      const saveMetadataSuccess = await this.saveMetadataChanges();
      if (!saveMetadataSuccess) {
        this.resultLoader = false;
        return false;
      }

      // Step 3: Call saveChangesToDB if computeLocalFit succeeds
      const saveSuccess = await this.saveChangesToDB();
      if (saveSuccess) {
        this.updateOriginalData();
        this.resultLoader = false;
        return true;
      } else {
        this.resultLoader = false;
        return false;
      }
    } catch (error) {
      this.resultLoader = false;
      console.error('Error in computeAndSaveChanges:', error);
      this.notificationService.showError('An error occurred during the compute and save process.');
      return false;
    }
  }

  async saveMetadataChanges(): Promise<boolean> {
    try {
      const siteId = '1';
      const projectId = this.configService.SelectedProjectId ?? '';
      const dataSheetId = this.datasheetId?.toString() ?? '';
      const jsonData = this.modifiedDataSheetResults.metadata;
      await this.datasheetService.saveMetadata(siteId, projectId, dataSheetId, jsonData);
      return true;
    } catch (error) {
      console.error('Error saving metadata changes:', error);
      return false;
    }
  }


  async computeLocalFit(recompute: boolean): Promise<boolean> {
    this.showTabs = false;
    let scaled_residue = 0;

    if (this.modelComparisonData && this.modelResults) {
      delete this.modelComparisonData['new local fit'];
      delete this.modelResults['m_err_new'];
    }

    if (this.scaleTensileBulge) {
      scaled_residue = 1;
    }

    const obj = {
      project_id: this.projectId,
      datasheet: Number(this.datasheetId),
      nominal_age: Number(this.nominalAge),
      params: {
        excluded_tensile: this.tensileExcludedData.map((file) => file.file_name),
        excluded_bulge: this.bulgeExcludedData.map((file) => file.file_name),
        model_params: this.dataSheetResults.hss_complete_params,
        gradients: {
          tensile_grad: this.tensile_grad,
          bulge_grad: this.bulge_grad,
          tensile_n_grad: this.tensile_n_grad,
          bulge_n_grad: this.bulge_n_grad,
        },
        model_weights: {
          tensile_weight: this.tensileWeight,
          bulge_weight: this.bulgeWeight,
          considere_weight: this.considereWeight,
          scaled_residue: scaled_residue,
        },
        recompute: recompute,
        tensileExcludedData: this.tensileExcludedData,
        bulgeExcludedData: this.bulgeExcludedData,
      },
    };

    return new Promise((resolve, reject) => {
      this.datasheetService.computeLocalFit(obj).subscribe({
        next: (results) => {
          if (results.local_fit) {
            this.modelResults = results.local_fit;
            this.modelComparisonData = results.local_fit.df_model_params;
            this.fetchDataAndRenderPlot();
            resolve(true);
          } else {
            resolve(false);
          }
        },
        error: (error) => {
          console.error('Error computing local fit:', error);
          this.resultLoader = false;
          this.notificationService.showError(error);
          reject(false);
        },
      });
    });
  }

  async fetchDataAndRenderPlot() {
    try {
      let tensfileobj = {
        project_id: this.projectId,
        datasheet: this.datasheetId,
        nominal_age: this.nominalAge,
        file_path: this.modelResults.df_tensile_plot_path,
      };
      let bulgefileobj = {
        project_id: this.projectId,
        datasheet: this.datasheetId,
        nominal_age: this.nominalAge,
        file_path: this.modelResults.df_bulge_plot_path,
      };

      const tensfileobjResponse = await this.datasheetService
        .readCSV(tensfileobj)
        .toPromise();
      const tensileData = tensfileobjResponse.csv_data;
      this.modelResults['df_tensile_plot'] = tensileData;

      const bulgefileobjResponse = await this.datasheetService
        .readCSV(bulgefileobj)
        .toPromise();
      const bulgeData = bulgefileobjResponse.csv_data;
      this.modelResults['df_bulge_plot'] = bulgeData;
      this.showTabs = true;
      this.renderInitialGraphs();
    } catch (error) {
      console.error('Error fetching data:', error);
      this.resultLoader = false;
      this.notificationService.showError(error);
    }
  }

  reset_weights() {
    this.tensileWeight = 5.0;
    this.bulgeWeight = 1.0;
    this.considereWeight = 0.005;
    this.scaleTensileBulge = true;
  }

  renderInitialGraphs() {
    setTimeout(() => {
      this.onTabChangeStressStrain(0);
      this.onTabChangeNValues(0);
      this.resultLoader = false;
    });
  }

  getTensileAndNValueTraces(df_tensile_plot: any[]): {
    traces: Partial<Plotly.Data>[];
  } {
    let tensileTraces: Partial<Plotly.Data>[] = [];
    let xdata: any = [];
    let ndata: any = [];
    let ndataSmooth: any = [];
    const uniqueFileNames = Array.from(
      new Set(df_tensile_plot.map((item) => item.file_name)),
    );

    uniqueFileNames.forEach((fileName) => {
      const samples = df_tensile_plot.filter(
        (item) => item.file_name === fileName,
      );

      xdata.push(...samples.map((item) => item.eps_pl));
      ndata.push(...samples.map((item) => item.n_value));
      ndataSmooth.push(...samples.map((item) => item.n_value_smoothed));
    });
    tensileTraces = [
      {
        x: xdata,
        y: ndata,
        type: 'scatter',
        mode: 'lines',
        name: 'Tensile n-values raw',
        line: { color: 'rgba(173,216,230,0.6)', dash: 'dot' },
        visible: 'legendonly',
      },
      {
        x: xdata,
        y: ndataSmooth,
        type: 'scatter',
        mode: 'lines',
        name: 'Tensile n-values smoothed',
        line: { color: 'rgba(222, 195, 150, 0.56)' },
        visible: 'legendonly',
      },
    ];
    return {
      traces: tensileTraces,
    };
  }

  getBulgeNValueTraces(df_bulge_plot: any[]): {
    traces: Partial<Plotly.Data>[];
  } {
    let bulgeTraces: Partial<Plotly.Data>[] = [];
    const uniqueFileNames = Array.from(
      new Set(df_bulge_plot.map((item) => item.file_name)),
    );
    const xdata: any[] = [];
    const ndata: any[] = [];
    const ndataSmooth: any[] = [];
    uniqueFileNames.forEach((fileName) => {
      const samples = df_bulge_plot.filter(
        (item) => item.file_name === fileName,
      );
      xdata.push(...samples.map((item) => item.eps_sc));
      ndata.push(...samples.map((item) => item.n_value));
      ndataSmooth.push(...samples.map((item) => item.n_value_smoothed));
    });
    bulgeTraces = [
      {
        x: xdata,
        y: ndata,
        type: 'scatter',
        mode: 'lines',
        name: 'Bulge n-values raw',
        line: { color: 'rgba(128,128,128,0.8)', width: 2, dash: 'dot' },
        visible: 'legendonly',
      },
      {
        x: xdata,
        y: ndataSmooth,
        type: 'scatter',
        mode: 'lines',
        name: 'Bulge n-values smoothed',
        line: { color: '#fcbf49' },
        visible: 'legendonly',
      },
    ];
    return {
      traces: bulgeTraces,
    };
  }

  getModelNValueTraceCurrent(df_models: any): Partial<Plotly.Data>[] {
    const nValueCurrent = df_models.map((item: any) => item.n_value_current);
    const xModel = df_models.map((item: any) => item.x_model);
    const modelTrace: Partial<Plotly.Data> = {
      x: xModel,
      y: nValueCurrent,
      type: 'scatter',
      mode: 'lines',
      name: 'Curve fit - Initial',
      line: { color: '#cca3ff', width: 1.5 },
    };

    return [modelTrace];
  }

  getModelNValueTraceNew(df_models: any): Partial<Plotly.Data>[] {
    const nValueNew = df_models.map((item: any) => item.n_value_new);
    const xModel = df_models.map((item: any) => item.x_model);
    const modelTrace: Partial<Plotly.Data> = {
      x: xModel,
      y: nValueNew,
      type: 'scatter',
      mode: 'lines',
      name: 'Curve fit - New',
      line: { color: '#34a434', width: 1.5 },
    };

    return [modelTrace];
  }

  getNValueMeasurementsTrace(jsonData: any): Partial<Plotly.Data>[] {
    const dfNvalues = jsonData['df_nvalues'];
    const keys = Object.keys(dfNvalues.value);
    const nvalMeasX = keys.map((key) => dfNvalues.log_strain_avg[key]);
    const nvalMeasY = keys.map((key) => dfNvalues.value[key]);
    let color = '#ff7f0e';

    const nValueMeasurementsTrace: Partial<Plotly.Data> = {
      x: nvalMeasX,
      y: nvalMeasY,
      type: 'scatter',
      mode: 'markers',
      name: 'n-value Measurements',
      marker: {
        color: color,
        size: 20,
        symbol: 'star',
      },
    };

    return [nValueMeasurementsTrace];
  }

  getAgRmPointTrace(
    df_results: DataPoint[],
    color: string = 'maroon',
  ): Partial<Plotly.Data> {
    const meanRm =
      df_results.reduce((sum, curr) => sum + curr.Rm, 0) / df_results.length;
    const meanAg =
      df_results.reduce((sum, curr) => sum + curr.Ag, 0) / df_results.length;
    const meanE =
      df_results.reduce((sum, curr) => sum + curr.E, 0) / df_results.length;

    const s_Ag = meanRm * (1 + meanAg + meanRm / meanE);
    const e_Ag = Math.log(1 + meanAg + meanRm / meanE) - s_Ag / meanE;

    const agRmPointTrace: Partial<Plotly.Data> = {
      x: [e_Ag],
      y: [e_Ag],
      type: 'scatter',
      mode: 'markers',
      name: 'Ag/Rm Point',
      marker: {
        color: color,
        size: 20,
        symbol: 'star',
      },
    };
    return agRmPointTrace;
  }

  calculateXRange(df_models: any[]): [number, number] {
    const xModelValues = df_models.map((item) => item.x_model);
    const xMin = Math.min(...xModelValues);
    const xMax = Math.max(...xModelValues);
    return [xMin, xMax];
  }

  calculateYRange(df_models: any[], df_results: any[]): [number, number] {
    const nValueCurrent = df_models.map((item) => item.n_value_current);
    const nValueNew = df_models.map((item) => item.n_value_new);
    const RmMean =
      df_results.reduce((acc, cur) => acc + cur.Rm, 0) / df_results.length;
    const AgMean =
      df_results.reduce((acc, cur) => acc + cur.Ag, 0) / df_results.length;
    const EMean =
      df_results.reduce((acc, cur) => acc + cur.E, 0) / df_results.length;
    const yMinCalculation =
      Math.log(1 + AgMean + RmMean / EMean) -
      (RmMean * (1 + AgMean + RmMean / EMean)) / EMean;
    const yMin = 0.85 * Math.min(...nValueCurrent, yMinCalculation);
    const yMax = 1.15 * Math.max(...nValueCurrent, yMinCalculation);
    return [yMin, yMax];
  }

  getOneToOneLineTrace(
    df_models: any[],
    df_results: any[],
  ): Partial<Plotly.Data> {
    const [xMin, xMax] = this.calculateXRange(df_models);
    const [yMin, yMax] = this.calculateYRange(df_models, df_results);
    const rangeMin = Math.min(xMin, yMin);
    const rangeMax = Math.max(xMax, yMax);

    const x = Array.from(
      { length: 100 },
      (_, idx) => rangeMin + ((rangeMax - rangeMin) * idx) / 99,
    );
    return {
      x: x,
      y: x,
      type: 'scatter',
      mode: 'lines',
      line: {
        dash: 'dash',
        color: 'slategray',
      },
      name: '1:1 Line',
    };
  }

  calculateDifferences(ydata: any, xdata: any): (number | null)[] {
    if (!Array.isArray(ydata) || !Array.isArray(xdata)) {
      console.error('calculateDifferences was called with non-array arguments');
      return [];
    }
    const ydiff = ydata
      .slice(1)
      .map((current: number, i: number) => current - ydata[i]);
    const xdiff = xdata
      .slice(1)
      .map((current: number, i: number) => current - xdata[i]);
    const diffs = ydiff.map((current: number, i: number) =>
      xdiff[i] !== 0 ? current / xdiff[i] : null,
    );
    return [null, ...diffs];
  }

  getBulgeTraces(df_bulge_plot: any[]): {
    traces: Partial<Plotly.Data>[];
    xMin: number;
    xMax: number;
    yMin: number;
    yMax: number;
  } {
    let bulgeTraces: Partial<Plotly.Data>[] = [];
    const uniqueFileNames = Array.from(
      new Set(df_bulge_plot.map((item) => item.file_name)),
    );
    let xdata: any[] = [];
    let ydata: any[] = [];
    let xMin = Infinity;
    let xMax = -Infinity;
    let yMin = Infinity;
    let yMax = -Infinity;
    const dsig_deps_raw: any = [];
    const dsig_deps_smoothed: any = [];

    uniqueFileNames.forEach((fileName) => {
      const samples = df_bulge_plot.filter(
        (item) => item.file_name === fileName,
      );
      let xdata1 = [];
      let ydata1 = [];
      if (df_bulge_plot[0].eps_sc) {
        xdata1 = samples.map((item) => item.eps_sc);
        ydata1 = samples.map((item) => item.sig_sc);
      }
      if (df_bulge_plot[0].xdata) {
        xdata1 = samples.map((item) => item.xdata);
        ydata1 = samples.map((item) => item.ydata);
      }

      xdata.push(...xdata1);
      xdata.push(null);
      ydata.push(...ydata1);
      ydata.push(null);
      dsig_deps_raw.push(...this.calculateDifferences(ydata1, xdata1));
      dsig_deps_smoothed.push(...samples.map((item) => item.grad_smoothed));
    });

    bulgeTraces = [
      {
        x: xdata,
        y: ydata,
        type: 'scatter',
        mode: 'lines',
        name: 'Bulge Samples',
        visible: 'legendonly',
        line: { color: '#cca3ff', width: 2 },
      },
      {
        x: xdata,
        y: dsig_deps_raw,
        type: 'scatter',
        mode: 'lines',
        name: 'Bulge Gradient (Raw)',
        visible: 'legendonly',
        line: { color: 'rgba(128,128,128,0.8)', width: 2, dash: 'dot' },
      },
      {
        x: xdata,
        y: dsig_deps_smoothed,
        type: 'scatter',
        mode: 'lines',
        name: 'Bulge Gradient (Smoothed)',
        visible: 'legendonly',
        line: { color: 'rgba(70,130,180,0.7)', width: 2 },
      },
    ];

    xMin = Math.min(xMin, Math.min(...xdata));
    xMax = Math.max(xMax, Math.max(...xdata));
    yMin = Math.min(yMin, Math.min(...ydata));
    yMax = Math.max(yMax, Math.max(...ydata));

    return {
      traces: bulgeTraces,
      xMin: xMin === Infinity ? 0 : xMin,
      xMax: xMax === -Infinity ? 1 : xMax,
      yMin: yMin === Infinity ? 0 : yMin,
      yMax: yMax === -Infinity ? 1 : yMax,
    };
  }

  getTensileTraces(df_tensile_plot: any[]): {
    traces: Partial<Plotly.Data>[];
    xMin: number;
    xMax: number;
    yMin: number;
    yMax: number;
  } {
    let tensileTraces: Partial<Plotly.Data>[] = [];
    let xMin = Infinity;
    let xMax = -Infinity;
    let yMin = Infinity;
    let yMax = -Infinity;
    let xdata: any = [];
    let ydata: any = [];
    const dsig_deps_raw: any = [];
    const dsig_deps_smoothed: any = [];

    const uniqueFileNames = Array.from(
      new Set(df_tensile_plot.map((item) => item.file_name)),
    );

    uniqueFileNames.forEach((fileName) => {
      const samples = df_tensile_plot.filter(
        (item) => item.file_name === fileName,
      );
      let xdata1 = [];
      let ydata1 = [];
      if (df_tensile_plot[0].eps_pl) {
        xdata1 = samples.map((item) => item.eps_pl);
        ydata1 = samples.map((item) => item.sig);
      }
      if (df_tensile_plot[0].xdata) {
        xdata1 = samples.map((item) => item.xdata);
        ydata1 = samples.map((item) => item.ydata);
      }

      xdata.push(...xdata1);
      xdata.push(null);
      ydata.push(...ydata1);
      ydata.push(null);

      const currentXMin = Math.min(...xdata);
      const currentXMax = Math.max(...xdata);
      const currentYMin = Math.min(...ydata);
      const currentYMax = Math.max(...ydata);

      xMin = Math.min(xMin, currentXMin);
      xMax = Math.max(xMax, currentXMax);
      yMin = Math.min(yMin, currentYMin);
      yMax = Math.max(yMax, currentYMax);

      dsig_deps_raw.push(...this.calculateDifferences(ydata1, xdata1));
      dsig_deps_smoothed.push(...samples.map((item) => item.grad_smoothed));
    });

    tensileTraces = [
      {
        x: xdata,
        y: ydata,
        type: 'scatter',
        mode: 'lines',
        name: 'Tensile Samples',
        visible: 'legendonly',
        line: { color: 'rgba(30,144,255,0.8)', width: 2 },
      },
      {
        x: xdata,
        y: dsig_deps_raw,
        type: 'scatter',
        mode: 'lines',
        name: 'Tensile Gradient (Raw)',
        visible: 'legendonly',
        line: { color: 'rgba(173,216,230,0.6)', width: 2 },
      },
      {
        x: xdata,
        y: dsig_deps_smoothed,
        type: 'scatter',
        mode: 'lines',
        name: 'Tensile Gradient (Smoothed)',
        visible: 'legendonly',
        line: { color: 'rgba(222, 195, 150, 0.56)', width: 2 },
      },
    ];
    return {
      traces: tensileTraces,
      xMin: xMin === Infinity ? 0 : xMin,
      xMax: xMax === -Infinity ? 1 : xMax,
      yMin: yMin === Infinity ? 0 : yMin,
      yMax: yMax === -Infinity ? 1 : yMax,
    };
  }

  getModelDataTracesCurrent(
    df_models: any,
    model_name: string,
  ): Partial<Plotly.Data>[] {
    const xModel = df_models.map((m: any) => m.x_model);
    const mCurrent = df_models.map((m: any) => m.m_current);
    const mGradCurrent = df_models.map((m: any) => m.m_grad_current);
    const modelTraces: Partial<Plotly.Data>[] = [
      {
        x: xModel,
        y: mCurrent,
        type: 'scatter',
        mode: 'lines',
        name: `${model_name} - Initial`,
        line: { color: 'rgba(255,127,80,0.9)', width: 2 },
      },
      {
        x: xModel,
        y: mGradCurrent,
        type: 'scatter',
        mode: 'lines',
        name: `${model_name} gradient - Initial`,
        line: { color: 'rgba(255,127,80,0.9)', width: 1.5, dash: 'dot' },
      },
    ];
    return modelTraces;
  }

  getModelDataTracesNew(
    df_models: any,
    model_name: string,
  ): Partial<Plotly.Data>[] {
    const xModel = df_models.map((m: any) => m.x_model);
    const mNew = df_models.map((m: any) => m.m_new);
    const mGradNew = df_models.map((m: any) => m.m_grad_new);
    const newModelTraces: Partial<Plotly.Data>[] = [
      {
        x: xModel,
        y: mNew,
        type: 'scatter',
        mode: 'lines',
        name: `${model_name} - New`,
        line: { color: '#34a434', width: 2 },
      },
      {
        x: xModel,
        y: mGradNew,
        type: 'scatter',
        mode: 'lines',
        name: `${model_name} gradient - New`,
        line: { color: '#34a434', width: 1.5, dash: 'dot' },
      },
    ];

    return newModelTraces;
  }

  getSpecialPointsTraces(
    eps_sig_pl_02: any,
    eps_sig_pl_ag: any,
    fit: string,
  ): Partial<Plotly.Data>[] {
    let color = '#ff4500';

    let specialPointsTraces: Partial<Plotly.Data>[] = [];
    specialPointsTraces.push({
      x: [eps_sig_pl_02[0]],
      y: [eps_sig_pl_02[1]],
      type: 'scatter',
      mode: 'markers',
      name: 'YS/Rp0.2',
      marker: { color: color, size: 20, symbol: 'star' },
    });

    // Rm point trace
    specialPointsTraces.push({
      x: [eps_sig_pl_ag[0]],
      y: [eps_sig_pl_ag[1]],
      type: 'scatter',
      mode: 'markers',
      name: 'UTS/Rm',
      marker: { color: color, size: 20, symbol: 'diamond' },
    });

    return specialPointsTraces;
  }

  getCurrentVSNewGraphConfigStressStrain(jsonData: any): { traces: Partial<Plotly.Data>[]; layout: Partial<Plotly.Layout> } {
    const bulgeData = this.getBulgeTraces(jsonData.df_bulge_plot);
    const tensileData = this.getTensileTraces(jsonData.df_tensile_plot);
    const modelTracesCurrent = this.getModelDataTracesCurrent(
      jsonData.df_models,
      'Curve fit',
    );
    const currspecialPointsTraces = this.getSpecialPointsTraces(
      jsonData.eps_sig_pl_02,
      jsonData.eps_sig_pl_ag,
      '',
    );
    const modelTracesNew = this.getModelDataTracesNew(
      jsonData.df_models,
      'Curve fit',
    );

    let allTracesCurrent = [
      ...modelTracesCurrent,
      ...modelTracesNew,
      ...currspecialPointsTraces,
      ...tensileData.traces,
      ...bulgeData.traces,
    ];

    allTracesCurrent = allTracesCurrent.filter(trace => trace.name !== 'Tensile Gradient (Raw)' && trace.name !== 'Bulge Gradient (Raw)');

    allTracesCurrent = allTracesCurrent.map(trace => ({
      ...trace,
      visible: true,
    }));

    const legenddesiredOrder = [
      'Curve fit - Initial',
      'Curve fit gradient - Initial',
      'Curve fit - New',
      'Curve fit gradient - New',
      'YS/Rp0.2',
      'UTS/Rm',
      'Tensile Samples',
      'Bulge Samples',
      'Tensile Gradient (Smoothed)',
      'Bulge Gradient (Smoothed)',
    ];

    const tracesdesiredOrder = [
      'YS/Rp0.2',
      'UTS/Rm',
      'Curve fit - Initial',
      'Curve fit gradient - Initial',
      'Curve fit - New',
      'Curve fit gradient - New',
      'Tensile Samples',
      'Bulge Samples',
      'Tensile Gradient (Smoothed)',
      'Bulge Gradient (Smoothed)',
    ];
    const sortedTraces = this.sortTraces(allTracesCurrent, legenddesiredOrder, tracesdesiredOrder);
    const layoutCurrent = this.getLayout(
      bulgeData,
      tensileData,
      'True stress vs. strain plot of test data and hardening fits',
    );
    return { traces: sortedTraces, layout: layoutCurrent };
  }

  sortTraces(traces: any[], legenddesiredOrder: string[], tracesdesiredOrder: string[]): any[] {
    const orderMap = new Map(tracesdesiredOrder.map((name, index) => [name, index]));
    const legendOrderMap = new Map(legenddesiredOrder.map((name, index) => [name, index]));

    // Sort traces by desired order
    const sortedTraces = traces.sort((a, b) => {
      const indexA = orderMap.get(a.name) ?? tracesdesiredOrder.length;
      const indexB = orderMap.get(b.name) ?? tracesdesiredOrder.length;
      return indexA - indexB;
    });

    // Update the legend order by assigning 'legendrank'
    sortedTraces.forEach(trace => {
      trace.legendrank = legendOrderMap.get(trace.name) ?? legenddesiredOrder.length;
    });

    // Reverse the array to fix layering issue (top traces are drawn last)
    return sortedTraces.reverse();
  }

  getCurrentGraphConfigStressStrain(jsonData: any): {
    traces: Partial<Plotly.Data>[];
    layout: Partial<Plotly.Layout>;
  } {
    this.bulge_plot_data;
    const bulgeData = this.getBulgeTraces(this.bulge_plot_data);
    const tensileData = this.getTensileTraces(this.tensile_plot_data);
    const modelTracesCurrent = this.getModelDataTracesCurrent(
      jsonData.df_models,
      'Curve fit',
    );
    const currspecialPointsTraces = this.getSpecialPointsTraces(
      jsonData.eps_sig_pl_02,
      jsonData.eps_sig_pl_ag,
      'Initial fit',
    );

    const allTracesCurrent = [
      ...modelTracesCurrent,
      ...currspecialPointsTraces,
      ...bulgeData.traces,
      ...tensileData.traces,
    ];

    const layoutCurrent = this.getLayout(
      bulgeData,
      tensileData,
      'Stress/strain plot of current hardening parameters for Hocket Sherby Swift',
    );

    return { traces: allTracesCurrent, layout: layoutCurrent };
  }

  getLayout(
    bulgeData: any,
    tensileData: any,
    title: string,
  ): Partial<Plotly.Layout> {
    const combinedXMin = Math.min(bulgeData.xMin, tensileData.xMin);
    const combinedXMax = Math.max(bulgeData.xMax, tensileData.xMax);
    const combinedYMin = Math.min(bulgeData.yMin, tensileData.yMin);
    const combinedYMax = Math.max(bulgeData.yMax, tensileData.yMax);

    return {
      xaxis: { title: 'log. plastic strain [-]', range: [combinedXMin, combinedXMax] },
      yaxis: { title: 'true stress [MPa]', range: [combinedYMin, combinedYMax] },
      legend: { x: 1, y: 1 },
      title: title,
    };
  }

  onTabChangeStressStrain(input: number | MatTabChangeEvent) {
    let tabIndex: number;
    if (typeof input === 'number') {
      tabIndex = input;
    } else {
      tabIndex = input.index;
    }

    if (tabIndex === 0) {
      const { traces, layout } = this.getCurrentVSNewGraphConfigStressStrain(
        this.modelResults,
      );
      this.renderPlot('plotDiv1', traces, layout);
    }
  }

  onTabChangeNValues(input: number | MatTabChangeEvent) {
    let tabIndex: number;
    if (typeof input === 'number') {
      tabIndex = input;
    } else {
      tabIndex = input.index;
    }

    if (tabIndex === 0) {
      const { traces, layout } = this.getCurrentVSNewNValuePlotConfig(
        this.modelResults,
      );
      this.renderPlot('plotDiv3', traces, layout);
    }
  }

  renderPlot(divId: string, data: any[], layout: any) {
    const element = document.getElementById(divId);
    if (element) {
      Plotly.newPlot(divId, data, layout);
    }
  }

  getCurrentVSNewNValuePlotConfig(jsonData: any): {
    traces: Partial<Plotly.Data>[];
    layout: Partial<Plotly.Layout>;
  } {
    const tensileData = this.getTensileAndNValueTraces(
      jsonData.df_tensile_plot,
    );
    const bulgeData = this.getBulgeNValueTraces(jsonData.df_bulge_plot);
    const modelDataTraceCurrent = this.getModelNValueTraceCurrent(
      jsonData.df_models,
    );
    const nValueMeasurementsTrace = this.getNValueMeasurementsTrace(jsonData);
    const agRmPointTrace = this.getAgRmPointTrace(jsonData.df_results);
    const modelDataTraceNew = this.getModelNValueTraceNew(jsonData.df_models);
    const oneToOneLineTrace = this.getOneToOneLineTrace(
      jsonData.df_models,
      jsonData.df_results,
    );

    let combinedTracesCurrent = [
      ...modelDataTraceCurrent,
      ...modelDataTraceNew,
      ...nValueMeasurementsTrace,
      agRmPointTrace,
      oneToOneLineTrace,
      ...tensileData.traces,
      ...bulgeData.traces,
    ];

    combinedTracesCurrent = combinedTracesCurrent.filter(trace =>
      trace.name !== 'Tensile n-values raw' && trace.name !== 'Bulge n-values raw'
    );
    combinedTracesCurrent = combinedTracesCurrent.map(trace => ({
      ...trace,
      visible: true
    }));

    const layoutCurrent: Partial<Plotly.Layout> = {
      title:
        'n-value vs. strain plot of test data and hardening fits',
      xaxis: {
        title: 'log. plastic strain [-]',
        range: this.calculateXRange(jsonData.df_models),
      },
      yaxis: {
        title: 'instantaneous n-values [-]',
        range: this.calculateYRange(jsonData.df_models, jsonData.df_results),
      },
      legend: { orientation: 'v' },
    };

    const tracesdesiredOrder = [
      'n-value Measurements',
      'Ag/Rm Point',
      'Curve fit - Initial',
      'Curve fit - New',
      'Tensile n-values smoothed',
      'Bulge n-values smoothed',
      '1:1 Line',
    ];

    const legenddesiredOrder = [
      'Curve fit - Initial',
      'Curve fit - New',
      'n-value Measurements',
      'Ag/Rm Point',
      'Tensile n-values smoothed',
      'Bulge n-values smoothed',
      '1:1 Line',
    ];
    const sortedTraces = this.sortTraces(combinedTracesCurrent, legenddesiredOrder, tracesdesiredOrder);
    return { traces: sortedTraces, layout: layoutCurrent };
  }

  getCurrentNValuePlotConfig(jsonData: any): {
    traces3: Partial<Plotly.Data>[];
    layout3: Partial<Plotly.Layout>;
  } {
    const modelDataTraceCurrent = this.getModelNValueTraceCurrent(
      jsonData.df_models,
    );
    const nValueMeasurementsTrace = this.getNValueMeasurementsTrace(jsonData);
    const modelDataTraceNew = this.getModelNValueTraceNew(jsonData.df_models);

    const combinedTracesCurrent = [
      ...modelDataTraceCurrent,
      ...nValueMeasurementsTrace,
      // agRmPointTrace,
      // ...tensileData.traces,
      // ...bulgeData.traces,
    ];

    const layoutCurrent: Partial<Plotly.Layout> = {
      title:
        'N-value plot of current hardening parameters for Hocket Sherby Swift',
      xaxis: {
        title: 'X Model',
        range: this.calculateXRange(jsonData.df_models),
      },
      yaxis: {
        title: 'Y Model',
        range: this.calculateYRange(jsonData.df_models, jsonData.df_results),
      },
      legend: { orientation: 'v' },
    };

    return { traces3: combinedTracesCurrent, layout3: layoutCurrent };
  }

  getCellValue(signature: string, param: string): any {
    const value = this.dataSheetResults.hss_complete_params?.[signature]?.[param] ?? '';

    if (typeof value === 'number') {
      const valueStr = value.toString();
      const decimalIndex = valueStr.indexOf('.');
      if (decimalIndex !== -1) {
        const decimalPlaces = valueStr.length - decimalIndex - 1;
        if (decimalPlaces > 9) {
          return parseFloat(value.toFixed(9));
        }
      }
      return value;
    }
    return value;
  }

  getModelCellValue(signature: string, param: string): any {
    let value;
    // Check if new_fit_params exists and is not empty
    const newFitParams = this.dataSheetResults.new_fit_params?.hss_complete_params;
    if (newFitParams && Object.keys(newFitParams).length > 0) {
      value = newFitParams?.[signature]?.[param] ?? '';
    } else {
      value = this.dataSheetResults.hss_complete_params?.[signature]?.[param] ?? '';
    }

    if (typeof value === 'number') {
      const valueStr = value.toString();
      const decimalIndex = valueStr.indexOf('.');
      if (decimalIndex !== -1) {
        const decimalPlaces = valueStr.length - decimalIndex - 1;
        if (decimalPlaces > 9) {
          return parseFloat(value.toFixed(9));
        }
      }
      return value;
    }

    return value;
  }

  setCellValue(signature: string, param: string, value: any): void {
    const newFitParams = this.dataSheetResults.new_fit_params;
    const newFitParamsCompleteParams = newFitParams?.hss_complete_params;

    // Ensure top-level `hss_complete_params` is initialized
    if (!this.dataSheetResults.hss_complete_params[signature]) {
      this.dataSheetResults.hss_complete_params[signature] = {};
    }

    // Ensure nested `new_fit_params.hss_complete_params` is initialized if it exists
    if (newFitParamsCompleteParams && !newFitParamsCompleteParams[signature]) {
      newFitParamsCompleteParams[signature] = {};
    }

    if (param === 'param_variable') {
      const boolValue = value === 'true' ? true : false;

      // Always update the top-level
      this.dataSheetResults.hss_complete_params[signature][param] = boolValue;
      this.modifiedDataSheetResults.hss_complete_params[signature][param] = boolValue;

      // Update `new_fit_params.hss_complete_params` if it exists
      if (newFitParamsCompleteParams) {
        newFitParamsCompleteParams[signature][param] = boolValue;
      }
      return;
    }

    if (value === '') {
      this.notificationService.showError('Input cannot be empty, preserving previous value.');
      return;
    }

    if (!this.isNumeric(value)) {
      this.notificationService.showError('Input must be numeric.');
      return;
    }

    const numericValue = parseFloat(value);

    // Always update the top-level
    this.dataSheetResults.hss_complete_params[signature][param] = numericValue;
    this.modifiedDataSheetResults.hss_complete_params[signature][param] = numericValue;

    // Update `new_fit_params.hss_complete_params` if it exists
    if (newFitParamsCompleteParams) {
      newFitParamsCompleteParams[signature][param] = numericValue;
    }
  }

  isNumeric(value: any): boolean {
    return /^-?\d+\.?\d*$/.test(value);
  }

  getKeys(obj: any): string[] {
    return Object.keys(obj);
  }

  getFitValue(item: string, key: string): any {
    return this.modelComparisonData[item][key];
  }

  getErrorValue(key: string): any {
    return this.modelResults[key];
  }

  onDirectorySelected(event: any) {
    const directory = event.target.files;
    const folderName = directory[0].webkitRelativePath.split('/')[0];

    // Check if folder name is integer only
    if (!this.isFolderNameInteger(folderName)) {
      this.notificationService.showError('Invalid folder name.');
      this.resetSelection(event);
      return;
    }

    // Validate subfolders
    if (!this.validateSubfolders(directory)) {
      this.notificationService.showError(
        'Folder must contain exactly the subfolders: FLC, Tensile, and Bulge (no other subfolders allowed)'
      );
      this.resetSelection(event);
      return;
    }

    // If all validations pass, proceed with selection
    this.selectedFolder = folderName;
    this.formData = new FormData();
    for (let i = 0; i < directory.length; i++) {
      this.formData.append('files', directory[i], directory[i].name);
      this.formData.append('filePaths', directory[i].webkitRelativePath);
    }
  }

  private isFolderNameInteger(folderName: string): boolean {
    const integerOnlyRegex = /^[0-9]+$/;
    return integerOnlyRegex.test(folderName);
  }

  private validateSubfolders(directory: FileList): boolean {
    const subfolders = new Set<string>();
    for (let i = 0; i < directory.length; i++) {
      const pathParts = directory[i].webkitRelativePath.split('/');
      if (pathParts.length > 2 && pathParts[1]) {
        const subfolderName = pathParts[1];
        subfolders.add(subfolderName);
      }
    }

    const requiredFolders = ['FLC', 'Tensile', 'Bulge'];
    const hasRequiredFolders = requiredFolders.every(folder => subfolders.has(folder));
    const hasOnlyRequiredFolders = subfolders.size === 3 && hasRequiredFolders;

    return hasOnlyRequiredFolders;
  }

  private resetSelection(event: any): void {
    this.selectedFolder = '';
    this.formData = new FormData();
    event.target.value = '';
  }

  uploadDirectory() {
    if (!this.selectedFolder) {
      this.notificationService.showError('Please select a valid folder first');
      return;
    }

    this.uploadLoader = true;
    const siteId = '1';
    this.datasheetService.ingestData(this.formData, siteId, this.projectId).subscribe({
      next: (result) => { },
      error: (error) => {
        this.notificationService.showError(error);
        this.uploadLoader = false;
      },
      complete: () => {
        this.getDataSheetSource();
        this.uploadLoader = false;
        this.formData = new FormData();
        this.selectedFolder = '';
        this.toaster.success('Folder Uploaded Successfully', '', {
          positionClass: 'custom-toast-position',
        });
      },
    });
  }

  saveExcludedFile(
    option: string,
    reason: string,
    index: number,
    type: string,
  ) {
    if (type === 'tensile') {
      const existingFileIndex = this.tensileExcludedData.findIndex(
        (item) => item.file_name === option,
      );
      if (existingFileIndex !== -1) {
        this.tensileExcludedData[existingFileIndex].reason = reason;
      } else {
        this.tensileExcludedData.push({ file_name: option, reason: reason });
      }
      this.tensileRecentlyChangedFiles.delete(option);
    } else if (type === 'bulge') {
      const existingFileIndex = this.bulgeExcludedData.findIndex(
        (item) => item.file_name === option,
      );
      if (existingFileIndex !== -1) {
        this.bulgeExcludedData[existingFileIndex].reason = reason;
      } else {
        this.bulgeExcludedData.push({ file_name: option, reason: reason });
      }
      this.bulgeRecentlyChangedFiles.delete(option);
    }
  }

  removeExcludedFile(option: string, type: string): void {
    if (type === 'tensile') {
      const index = this.tensileExcludedData.findIndex(
        (data) => data.file_name === option,
      );
      if (index !== -1) {
        this.tensileExcludedData.splice(index, 1);

        const originalItem = this.originalTensileCSVData.find(
          (item) => this.dsgHandler.extractFileName(item.file_name) === option
        );
        if (originalItem && !this.tensileCSVData.some(
          (item: any) => this.dsgHandler.extractFileName(item.file_name) === option
        )) {
          this.tensileCSVData.push(originalItem);
        }

        this.updateModifiedDataSheetResults('tensile');
        this.getDirections(this.modifiedDataSheetResults);
        this.updateTensileSampleInclusion(option);
        this.tensile_GraphPlot(
          this.tensileSelectedOptions,
          this.dataSheetResults.tensile_plot_data_path,
        );
        this.refreshTensileStats();
      }
    } else if (type === 'bulge') {
      const index = this.bulgeExcludedData.findIndex(
        (data) => data.file_name === option,
      );
      if (index !== -1) {
        this.bulgeExcludedData.splice(index, 1);
        this.updateModifiedDataSheetResults('bulge');
        this.updateAvgBulgeScaleFactor()
      }
    }
  }

  onInputChange(fileName: string, type: string): void {
    if (type == 'tensile') {
      this.tensileRecentlyChangedFiles.add(fileName);
    } else {
      this.bulgeRecentlyChangedFiles.add(fileName);
    }
  }

  updateTensileGradient(value: number): void {
    // Ensure new_fit_params and gradients exist
    if (!this.modifiedDataSheetResults.new_fit_params) {
      this.modifiedDataSheetResults.new_fit_params = {};
    }
    if (!this.modifiedDataSheetResults.new_fit_params.gradients) {
      this.modifiedDataSheetResults.new_fit_params.gradients = {};
    }

    // Initialize tensile_grad if undefined
    if (this.modifiedDataSheetResults.new_fit_params.gradients.tensile_grad === undefined) {
      this.modifiedDataSheetResults.new_fit_params.gradients.tensile_grad = 15;
    }

    // Update tensile_grad
    this.tensile_grad = value;
    this.modifiedDataSheetResults.new_fit_params.gradients.tensile_grad = value;
  }

  updateBulgeGradient(value: number): void {
    // Ensure new_fit_params and gradients exist
    if (!this.modifiedDataSheetResults.new_fit_params) {
      this.modifiedDataSheetResults.new_fit_params = {};
    }
    if (!this.modifiedDataSheetResults.new_fit_params.gradients) {
      this.modifiedDataSheetResults.new_fit_params.gradients = {};
    }

    // Initialize bulge_grad if undefined
    if (this.modifiedDataSheetResults.new_fit_params.gradients.bulge_grad === undefined) {
      this.modifiedDataSheetResults.new_fit_params.gradients.bulge_grad = 10;
    }

    // Update bulge_grad
    this.bulge_grad = value;
    this.modifiedDataSheetResults.new_fit_params.gradients.bulge_grad = value;
  }

  updateTensileNGradient(value: number): void {
    // Ensure new_fit_params and gradients exist
    if (!this.modifiedDataSheetResults.new_fit_params) {
      this.modifiedDataSheetResults.new_fit_params = {};
    }
    if (!this.modifiedDataSheetResults.new_fit_params.gradients) {
      this.modifiedDataSheetResults.new_fit_params.gradients = {};
    }

    // Initialize tensile_n_grad if undefined
    if (this.modifiedDataSheetResults.new_fit_params.gradients.tensile_n_grad === undefined) {
      this.modifiedDataSheetResults.new_fit_params.gradients.tensile_n_grad = 15;
    }

    // Update tensile_n_grad
    this.tensile_n_grad = value;
    this.modifiedDataSheetResults.new_fit_params.gradients.tensile_n_grad = value;
  }

  updateBulgeNGradient(value: number): void {
    // Ensure new_fit_params and gradients exist
    if (!this.modifiedDataSheetResults.new_fit_params) {
      this.modifiedDataSheetResults.new_fit_params = {};
    }
    if (!this.modifiedDataSheetResults.new_fit_params.gradients) {
      this.modifiedDataSheetResults.new_fit_params.gradients = {};
    }

    // Initialize bulge_n_grad if undefined
    if (this.modifiedDataSheetResults.new_fit_params.gradients.bulge_n_grad === undefined) {
      this.modifiedDataSheetResults.new_fit_params.gradients.bulge_n_grad = 10;
    }

    // Update bulge_n_grad
    this.bulge_n_grad = value;
    this.modifiedDataSheetResults.new_fit_params.gradients.bulge_n_grad = value;
  }




  async navigate(pageName: string) {
    if (!this.hasUnsavedChanges()) {
      this.performNavigation(pageName);
      return;
    }

    const dialogRef = this.dialog.open(PromptSaveComponent, { width: '300px' });

    dialogRef.afterClosed().subscribe(async (result) => {
      if (!result) {
        this.performNavigation(pageName); // Proceed without saving
        return;
      }

      this.loader = true;
      this.showButtons = false;

      try {
        // Step 1: Compute local fit
        const fitSuccess = await this.computeLocalFit(true);
        if (!fitSuccess) {
          this.notificationService.showError('Computation failed. Changes cannot be saved.');
          return;
        }

        // Step 2: Save changes
        const saveSuccess = await this.saveChangesToDB();
        if (saveSuccess) {
          this.performNavigation(pageName);
        }

      } finally {
        this.loader = false;
      }
    });
  }

  async saveChangesToDB(): Promise<boolean> {
    try {
      this.modifiedDataSheetResults.tensile_files = this.originalDataSheetResults.tensile_files;
      this.modifiedDataSheetResults.bulge_files = this.originalDataSheetResults.bulge_files;

      const newFitParams = this.dataSheetResults.new_fit_params;
      const isNewFitParamsEmpty = !newFitParams || Object.keys(newFitParams).length === 0;

      this.modifiedDataSheetResults.new_fit_params = {
        excluded_tensile: this.tensileExcludedData.map((file) => file.file_name),
        excluded_bulge: this.bulgeExcludedData.map((file) => file.file_name),
        gradients: {
          tensile_grad: this.tensile_grad,
          bulge_grad: this.bulge_grad,
          tensile_n_grad: this.tensile_n_grad,
          bulge_n_grad: this.bulge_n_grad,
        },
        hss_weights_object: isNewFitParamsEmpty
          ? { ...this.dataSheetResults.hss_weights_object }
          : { ...newFitParams.hss_weights_object },
        hss_complete_params: isNewFitParamsEmpty
          ? JSON.parse(JSON.stringify(this.dataSheetResults.hss_complete_params))
          : JSON.parse(JSON.stringify(newFitParams.hss_complete_params)),
        recompute: true,
        bulgeExcludedData: this.bulgeExcludedData,
        tensileExcludedData: this.tensileExcludedData,
      };


      const initialFitParams = this.originalDataSheetResults?.initial_fit_params;
      if (!initialFitParams || Object.keys(initialFitParams).length === 0) {
        const clonedNewFitParams = JSON.parse(
          JSON.stringify(this.modifiedDataSheetResults.new_fit_params)
        );
        this.modifiedDataSheetResults.initial_fit_params = clonedNewFitParams;
      }

      const siteID = '1';
      const response = await this.datasheetService.saveChanges(
        siteID,
        this.projectId,
        this.datasheetId,
        this.nominalAge,
        this.selectedDataSheet.id,
        this.modifiedDataSheetResults
      );

      if (response.status_code === 200) {
        return true;
      } else {
        console.error('Unexpected API response:', response);
        this.notificationService.showError('Failed to save changes due to unexpected response.');
        return false;
      }
    } catch (error) {
      console.error('Error during saveChangesToDB:', error);
      this.notificationService.showError('Failed to save changes. Please try again.');
      return false;
    }
  }


  hasUnsavedChanges(): boolean {
    if (!this.originalDataSheetResults || !this.modifiedDataSheetResults) {
      return false;
    }

    // Create deep copies of the objects to avoid modifying the originals
    const originalCopy = JSON.parse(JSON.stringify(this.originalDataSheetResults));
    const modifiedCopy = JSON.parse(JSON.stringify(this.modifiedDataSheetResults));

    // Remove fields that are not relevant for comparison
    const cleanUnnecessaryFields = (obj: any) => {
      if (obj.corrected_tensile_results) {
        delete obj.corrected_tensile_results.xdata;
        delete obj.corrected_tensile_results.ydata;
      }
    };
    cleanUnnecessaryFields(originalCopy);
    cleanUnnecessaryFields(modifiedCopy);

    // Normalize array fields for order-independent comparison
    const normalizeArrays = (obj: any) => {
      if (obj.tensile_files) {
        obj.tensile_files.sort();
      }
      if (obj.bulge_files) {
        obj.bulge_files.sort();
      }
      if (obj.new_fit_params?.tensileExcludedData) {
        obj.new_fit_params.tensileExcludedData.sort((a: any, b: any) =>
          a.file_name.localeCompare(b.file_name)
        );
      }
      if (obj.new_fit_params?.bulgeExcludedData) {
        obj.new_fit_params.bulgeExcludedData.sort((a: any, b: any) =>
          a.file_name.localeCompare(b.file_name)
        );
      }
    };
    normalizeArrays(originalCopy);
    normalizeArrays(modifiedCopy);

    // Stringify the normalized objects for comparison
    const originalStr = JSON.stringify(originalCopy);
    const modifiedStr = JSON.stringify(modifiedCopy);

    // Return true if there's a difference
    return originalStr !== modifiedStr;
  }


  performNavigation(pageName: string): void {
    const selectedProjectId = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const projectId = selectedProjectId;
    const siteId = this.configService.SelectedSiteId;

    if (pageName === 'activity-logs') {
      const activityLogData = {
        ...this.originalDataSheetResults,
        datasheetId: this.datasheetId,
        nominalAge: this.nominalAge,
        nominalAgeArray: this.nominalAgeArray,
        selectedDataSheet: this.selectedDataSheet,
      };

      this.datasheetService.setActivityLogData(activityLogData);
      this.router.navigate([`sites/${siteId}/projects/${projectId}/${pageName}`]);
    } else {
      this.router.navigate([`sites/${siteId}/projects/${projectId}/${pageName}`]);
    }
  }



  updateOriginalData(): void {
    this.originalDataSheetResults = JSON.parse(JSON.stringify(this.modifiedDataSheetResults));
  }

  areDataSheetsEqual(): boolean {
    if (!this.originalDataSheetResults || !this.modifiedDataSheetResults) {
      return true;
    }
    const original = this.originalDataSheetResults;
    const modified = this.modifiedDataSheetResults;

    const areArraysEqualUnordered = (arr1: any[], arr2: any[]): boolean => {
      if (arr1.length !== arr2.length) return false;
      const sorted1 = [...arr1].sort();
      const sorted2 = [...arr2].sort();
      return sorted1.every((val, index) => val === sorted2[index]);
    };

    return (
      areArraysEqualUnordered(original.tensile_files, modified.tensile_files) &&
      areArraysEqualUnordered(original.bulge_files, modified.bulge_files) &&
      JSON.stringify(original.hss_complete_params) === JSON.stringify(modified.hss_complete_params) &&
      JSON.stringify(original.corrected_tensile_results) === JSON.stringify(modified.corrected_tensile_results) &&
      JSON.stringify(original.bulge_scale_factor) === JSON.stringify(modified.bulge_scale_factor) &&
      JSON.stringify(original.hss_weights_object) === JSON.stringify(modified.hss_weights_object) &&
      JSON.stringify(original.new_fit_params) === JSON.stringify(modified.new_fit_params) &&
      JSON.stringify(original.initial_fit_params) === JSON.stringify(modified.initial_fit_params) &&
      JSON.stringify(original.metadata) === JSON.stringify(modified.metadata)
    );
  }

  reset(section: string) {
    if (section === 'meta-data') {
      this.resetMetaData();
    } else if (section === 'tensile') {
      this.resetTensile();
      this.refreshTensileStats();
    } else if (section === 'bulge') {
      this.resetBulge();
    } else if (section === 'corrected-tensile') {
      this.resetCorrectedTensile();
    }
    else if (section === 'model-parameters') {
      this.resetModelParameters();
    }
  }

  private resetMetaData() {
    const metadata = this.originalDataSheetResults.metadata;

    // Update UI state
    this.productName = metadata.commercial_name;
    this.gauge = metadata.gauge;
    this.m_source = metadata.m_source;
    this.branchName = metadata.branch_name;
    this.specName = metadata.spec_name;
    this.latestRevalidationDate = new Date(metadata.latest_revalidation);
    this.validUntilDate = new Date(metadata.valid_until);

    // Update modified object
    this.modifiedDataSheetResults.metadata = { ...metadata };
  }

  private resetTensile() {
    const tensileExcludedData = this.originalDataSheetResults.initial_fit_params.tensileExcludedData.map(
      (excluded: any) => excluded.file_name
    );
    const allTensileFiles = this.originalDataSheetResults.tensile_files;

    // Update UI state
    this.tensileSelectedOptions = allTensileFiles.filter(
      (file: string) => !tensileExcludedData.includes(file)
    );
    this.tensileExcludedData = [...this.originalDataSheetResults.initial_fit_params.tensileExcludedData];

    this.tensileCSVData = this.originalTensileCSVData.filter(
      (item: any) => this.tensileSelectedOptions.includes(this.dsgHandler.extractFileName(item.file_name))
    );

    if (this.tensileSampleData) {
      this.tensileSampleData.forEach((sample: any) => {
        const fileName = sample.sampleId || sample.file_name;
        this.updateTensileSampleInclusion(fileName);
      });
    }

    this.getDirections(this.modifiedDataSheetResults);

    this.tensile_GraphPlot(
      this.tensileSelectedOptions,
      this.originalDataSheetResults.tensile_plot_data_path
    );

    // No need to update modifiedDataSheetResults here
  }

  private resetBulge() {
    const bulgeExcludedData = this.originalDataSheetResults.initial_fit_params.bulgeExcludedData.map(
      (excluded: any) => excluded.file_name
    );
    const allBulgeFiles = this.originalDataSheetResults.bulge_files;

    // Update UI state
    this.bulgeSelectedOptions = allBulgeFiles.filter(
      (file: string) => !bulgeExcludedData.includes(file)
    );
    this.bulgeExcludedData = [...this.originalDataSheetResults.initial_fit_params.bulgeExcludedData];

    // Re-generate the bulge graph plot
    this.bulge_GraphPlot(
      this.bulgeSelectedOptions,
      this.originalDataSheetResults.bulge_plot_data_path
    );
    this.updateAvgBulgeScaleFactor();
  }

  private resetCorrectedTensile() {
    const correctedTensileResults = this.originalDataSheetResults.corrected_tensile_results;
    this.selectedTensileSample = correctedTensileResults.sample_name;
    this.recomputeRp02 = this.originalDataSheetResults.initial_fit_params.recompute;
  }

  private resetModelParameters(): void {

    const weightsObject = this.originalDataSheetResults.initial_fit_params.hss_weights_object;
    if (weightsObject) {
      this.tensileWeight = weightsObject.tensile_weight;
      this.bulgeWeight = weightsObject.bulge_weight;
      this.considereWeight = weightsObject.considere_weight;
      this.dataSheetResults.hss_weights_object = { ...weightsObject };
    }

    const gradients = this.originalDataSheetResults.initial_fit_params.gradients;
    if (gradients) {
      this.tensile_grad = gradients.tensile_grad;
      this.bulge_grad = gradients.bulge_grad;
      this.tensile_n_grad = gradients.tensile_n_grad;
      this.bulge_n_grad = gradients.bulge_n_grad;
      this.dataSheetResults.new_fit_params.gradients = { ...gradients };
    }

    // Reset complete parameters table from originalDataSheetResults
    if (
      this.originalDataSheetResults.initial_fit_params &&
      this.originalDataSheetResults.initial_fit_params.hss_complete_params
    ) {
      this.dataSheetResults.new_fit_params.hss_complete_params = JSON.parse(
        JSON.stringify(this.originalDataSheetResults.initial_fit_params.hss_complete_params)
      );
      this.modifiedDataSheetResults.new_fit_params.hss_complete_params = JSON.parse(
        JSON.stringify(this.originalDataSheetResults.initial_fit_params.hss_complete_params)
      );
    }
  }

  async onResetCorrectedTensile(): Promise<void> {
    try {

      // Call the API to reset the tensile sample
      const projectId = this.configService.SelectedProjectId ?? '';
      const datasheetId = this.datasheetId ?? '';
      const nominalAge = this.nominalAge ?? '';
      const selectedSample = this.selectedTensileSample;

      const jsonData = {
        project_id: projectId,
        datasheet: datasheetId,
        nominal_age: nominalAge,
        selected_sample: selectedSample,
        corrected_tensile_results: {},
        s_min: 20,
        s_max: 60,
        recompute_Rp02: this.recomputeRp02,
      };

      const response = await this.datasheetService.resetCorrectedTensileSample(jsonData);

      if (response) {
        this.dataSheetResults.corrected_tensile_results = { ...response.correct_data };
        this.modifiedDataSheetResults.corrected_tensile_results = { ...response.correct_data };
        this.process_correctedTensileResults(
          this.dataSheetResults.tensile_files,
          this.dataSheetResults.corrected_tensile_results
        );
        this.reset('corrected-tensile');
      } else {
        this.notificationService.showError('Failed to reset tensile sample. Please try again.');
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to reset tensile sample. Please try again.';
      this.notificationService.showError(errorMessage);
    }
  }


  hasSectionChanged(section: string): boolean {
    const arraysAreEqual = (arr1: string[], arr2: string[]): boolean => {
      if (!arr1 || !arr2) return false;
      if (arr1.length !== arr2.length) return false;
      const sortedArr1 = [...arr1].sort();
      const sortedArr2 = [...arr2].sort();
      return sortedArr1.every((value, index) => value === sortedArr2[index]);
    };

    // Use spread operator to create shallow copies
    const initialFitParams = { ...this.originalDataSheetResults?.initial_fit_params };
    const newFitParams = { ...this.originalDataSheetResults?.new_fit_params };

    const isInitialFitEmpty = (): boolean => {
      return Object.keys(initialFitParams).length === 0;
    };

    if (isInitialFitEmpty()) {
      return false; // No changes if initial_fit_params is empty.
    }

    if (section === 'meta-data') {
      return JSON.stringify(this.originalDataSheetResults?.metadata || {}) !==
        JSON.stringify(this.modifiedDataSheetResults?.metadata || {});
    } else if (section === 'tensile') {
      // Compare excluded data in initial_fit_params and modifiedDataSheetResults
      const originalTensile = this.originalDataSheetResults?.initial_fit_params?.tensileExcludedData?.map(
        (excluded: any) => excluded.file_name
      ) || [];
      const modifiedTensile = this.tensileExcludedData?.map((excluded: any) => excluded.file_name) || [];
      const tensileParamsChanged = !arraysAreEqual(originalTensile, modifiedTensile);

      // Compare excluded_tensile in initial_fit_params and new_fit_params
      const initialExcludedTensile = [...(initialFitParams.excluded_tensile || [])];
      const newExcludedTensile = [...(newFitParams.excluded_tensile || [])];
      const tensileFitParamsChanged = !arraysAreEqual(initialExcludedTensile, newExcludedTensile);

      return tensileParamsChanged || tensileFitParamsChanged;
    } else if (section === 'bulge') {
      // Compare excluded data in initial_fit_params and modifiedDataSheetResults
      const originalBulge = this.originalDataSheetResults?.initial_fit_params?.bulgeExcludedData?.map(
        (excluded: any) => excluded.file_name
      ) || [];
      const modifiedBulge = this.bulgeExcludedData?.map((excluded: any) => excluded.file_name) || [];
      const bulgeParamsChanged = !arraysAreEqual(originalBulge, modifiedBulge);

      // Compare excluded_bulge in initial_fit_params and new_fit_params
      const initialExcludedBulge = [...(initialFitParams.excluded_bulge || [])];
      const newExcludedBulge = [...(newFitParams.excluded_bulge || [])];
      const bulgeFitParamsChanged = !arraysAreEqual(initialExcludedBulge, newExcludedBulge);

      return bulgeParamsChanged || bulgeFitParamsChanged;
    } else if (section === 'corrected-tensile') {
      const originalSample = this.originalDataSheetResults?.corrected_tensile_results?.sample_name || null;
      const modifiedSample = this.modifiedDataSheetResults?.corrected_tensile_results?.sample_name || null;
      const sampleChanged = originalSample !== modifiedSample;

      const originalBounds = {
        s_min: this.originalDataSheetResults?.corrected_tensile_results?.s_min || 0,
        s_max: this.originalDataSheetResults?.corrected_tensile_results?.s_max || 0,
      };
      const modifiedBounds = {
        s_min: this.modifiedDataSheetResults?.corrected_tensile_results?.s_min || 0,
        s_max: this.modifiedDataSheetResults?.corrected_tensile_results?.s_max || 0,
      };
      const boundsChanged = JSON.stringify(originalBounds) !== JSON.stringify(modifiedBounds);

      const originalDfResults = this.originalDataSheetResults?.corrected_tensile_results?.df_results || [];
      const modifiedDfResults = this.modifiedDataSheetResults?.corrected_tensile_results?.df_results || [];

      const resultsAreEqual = originalDfResults.length === modifiedDfResults.length &&
        originalDfResults.every((originalRow: any, index: number) => {
          const modifiedRow = modifiedDfResults[index];
          return JSON.stringify(originalRow) === JSON.stringify(modifiedRow);
        });

      return sampleChanged || boundsChanged || !resultsAreEqual;
    } else if (section === 'model-parameters') {
      // Check if weights have changed
      const weightsChanged = JSON.stringify(this.originalDataSheetResults?.hss_weights_object || {}) !==
        JSON.stringify(this.modifiedDataSheetResults?.hss_weights_object || {});

      // Check if gradients have changed
      const gradientsChanged = JSON.stringify(this.originalDataSheetResults?.initial_fit_params?.gradients || {}) !==
        JSON.stringify(this.modifiedDataSheetResults?.new_fit_params?.gradients || {});

      // Check if table parameters have changed
      const tableParamsChanged = JSON.stringify(this.originalDataSheetResults?.hss_complete_params || {}) !==
        JSON.stringify(this.modifiedDataSheetResults?.hss_complete_params || {});

      return weightsChanged || gradientsChanged || tableParamsChanged;
    }

    return false;
  }



  setInitialFit(): void {
    if (!this.originalDataSheetResults.initial_fit_params ||
      Object.keys(this.originalDataSheetResults.initial_fit_params).length === 0) {
      this.submitInitialFit();
      return;
    }

    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      width: '450px',
      data: {
        heading: 'Reassign Initial Fit',
        message: 'An initial fit has already been set. Would you like to set the newly calculated fit as the initial fit?',
        confirmButton: 'Reassign',
        cancelButton: 'Cancel',
      }
    });

    dialogRef.afterClosed().subscribe(async (result) => {
      if (result) {
        await this.submitInitialFit();
      }
    });
  }


  async submitInitialFit(): Promise<void> {
    this.dynamicMessage = 'Processing';
    const siteId = '1';
    const projectId = this.configService.SelectedProjectId ?? '';
    const dataSheetId = this.datasheetId?.toString() ?? '';
    const nominalAge = this.nominalAge?.toString() ?? '';
    const jsonData = this.modelResults.df_model_params["new local fit"];

    try {
      const response = await this.datasheetService.setInitialFit(siteId, projectId, dataSheetId, nominalAge, jsonData);
      if (response && response.datasheet) {
        this.modifiedDataSheetResults.initial_fit_params = this.constructInitialFitParams();
        const computeSaveSuccess = await this.computeAndSaveChanges(true);
        if (computeSaveSuccess) {
          this.toaster.success('Initial fit set successfully', '', {
            positionClass: 'custom-toast-position',
          });
        }
      }
    } catch (error: any) {
      this.notificationService.showError(error.message || 'Failed to set initial fit. Please try again.');
    }
  }

  private constructInitialFitParams(): any {
    const newFitParams = this.dataSheetResults.new_fit_params;

    // Check if `new_fit_params` is empty
    const isNewFitParamsEmpty = !newFitParams || Object.keys(newFitParams).length === 0;

    return {
      excluded_tensile: this.tensileExcludedData.map((file) => file.file_name),
      excluded_bulge: this.bulgeExcludedData.map((file) => file.file_name),
      gradients: {
        tensile_grad: this.tensile_grad,
        bulge_grad: this.bulge_grad,
        tensile_n_grad: this.tensile_n_grad,
        bulge_n_grad: this.bulge_n_grad,
      },
      hss_weights_object: isNewFitParamsEmpty
        ? { ...this.dataSheetResults.hss_weights_object }
        : { ...newFitParams.hss_weights_object },
      hss_complete_params: isNewFitParamsEmpty
        ? JSON.parse(JSON.stringify(this.dataSheetResults.hss_complete_params))
        : JSON.parse(JSON.stringify(newFitParams.hss_complete_params)),
      recompute: true,
      bulgeExcludedData: this.bulgeExcludedData,
      tensileExcludedData: this.tensileExcludedData,
    };
  }

  isInitialFitParamsEmpty(): boolean {
    const initialFitParams = { ...this.originalDataSheetResults?.initial_fit_params };
    return Object.keys(initialFitParams).length === 0;
  }

  updateAvgBulgeScaleFactor(): void {
    const averageScaleFactor = this.dsgHandler.calculateAvgBulgeScaleFactor(this.dataSheetResults, this.bulgeSelectedOptions);
    this.dataSheetResults.bulge_scale_factor.k_mean = averageScaleFactor;
  }

  get dfYieldKeys(): string[] {
    return this.dsgHandler.getDfYieldKeys(this.modelResults.df_yield);
  }

  get dfYieldValues(): { key: string; value: string }[] {
    return this.dsgHandler.getDfYieldValues(this.modelResults.df_yield);
  }

  get hasDfYieldData(): boolean {
    return this.dsgHandler.hasDfYieldData(this.modelResults.df_yield);
  }

  ngOnDestroy(): void {
    this.stopAnimatingDots();
  }

}
