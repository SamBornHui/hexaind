import { Component, Input, SimpleChanges, OnChanges, OnDestroy } from '@angular/core';
import { DataPreviewService } from '../../services/data-preview.service'
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { ConfigService } from '../../../../services/config.service';
import { catchError, interval, of, Subscription, switchMap, takeWhile } from 'rxjs';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-comparison-instance',
  templateUrl: './comparison-instance.component.html',
  styleUrls: ['./comparison-instance.component.less']
})
export class ComparisonInstanceComponent implements OnChanges, OnDestroy {
  @Input() dataset_id!: string;
  //@Input() visualizationType!: string;
  @Input() interactive!: boolean

  private isFirstChange: boolean = true;
  selectedPlotType: string | undefined = "";
  plotTypes: any[] = [{ 'name': 'Scatter Plot', 'type': 'SCATTER_PLOT' }, { 'name': 'Box Plot', 'type': 'BOX_PLOT' }, { 'name': 'Histogram', 'type': 'HISTOGRAM' }, { 'name': 'IQR', 'type': 'IQR_PLOT' }];

  isLoading = false;
  numericalColumns: string[] = [];
  categoricalColumns: string[] = [];
  xAxisColumnNames: string[] = [];
  yAxisColumnNames: string[] = [];
  filteredXAxisColumnNames: string[] = [];
  filteredYAxisColumnNames: string[] = [];
  filteredAvailableColourByOptions: string[] = [];
  _selectedXAxisColumnName: any = null;
  _selectedYAxisColumnName: any = null;
  _selectedColourBy: string = ""
  plotData!: SafeResourceUrl;
  displayMessage = 'Select X-axis and Y-axis and click Generate'
  disableGenerateButton: boolean = true
  searchText: string = "";
  visualizationType: any = "DISTRIBUTION";
  isRadioButonChanged: boolean = false
  excludedColumns: string[] = [
    'Pareto-optimal_num',
    'generation_method',
    'trial_index',
    'visual_dir',
    'arm_name',
    'coords',
    'image_intensity',
    'image',
    'image_convex',
    'image_filled'
  ];
  isLineFitEnabled: boolean = false;
  additional_config: any;
  visualizationSubscription: Subscription | null = null;
  POLLING_INTERVAL = 5000;
  availableColourByOptions: any = [];

  constructor(
    private dataPreviewService: DataPreviewService,
    private sanitizer: DomSanitizer,
    private configService: ConfigService,
    public toaster: ToastrService,
  ) {
    // this.filteredAvailableColourByOptions = this.availableColourByOptions;
  }

  ngOnInit() {
    this.dataPreviewService.getNumericalColumnNamesObservable().subscribe((columnNames: string[]) => {
      this.numericalColumns = columnNames;
      this.initializeColumns();
    });

    this.dataPreviewService.getCategoricalColumnNamesObservable().subscribe((columnNames: string[]) => {
      this.categoricalColumns = columnNames;
      this.initializeColumns();
    });

    // this.setColumns();

  }

  async setColumns() {
    const numerical = await this.dataPreviewService.loadNumericalData(this.dataset_id)
    if (numerical && numerical.statistics) {
      this.numericalColumns = numerical.statistics[0].column_names;
      this.initializeColumns();
    }
    this.dataPreviewService.unsubscribeNumerical();

    const categorical = await this.dataPreviewService.loadCategoricalData(this.dataset_id)
    if (categorical && categorical.statistics) {
      this.categoricalColumns = categorical.statistics[0].column_names;
      this.initializeColumns();
    }
    this.dataPreviewService.unsubscribeCategorical();

    if (this.selectedXAxisColumnName && this.selectedYAxisColumnName) {
      this.generate();
    }
  }

  ngOnDestroy() {
    this.visualizationSubscription?.unsubscribe();
    this.dataPreviewService.unsubscribeNumerical();
    this.dataPreviewService.unsubscribeCategorical();
  }

  initializeColumns() {
    this.xAxisColumnNames = [...this.numericalColumns, ...this.categoricalColumns];
    this.filteredXAxisColumnNames = [...this.xAxisColumnNames];
    this.yAxisColumnNames = [...this.xAxisColumnNames];
    this.filteredYAxisColumnNames = [...this.xAxisColumnNames];
    this.selectedPlotType = 'SCATTER_PLOT'
    this.onPlotTypeChange()
    if (!this.selectedYAxisColumnName && !this.selectedXAxisColumnName && this.numericalColumns.length > 0) {
      this.selectedXAxisColumnName = this.numericalColumns[0];
      this.selectedYAxisColumnName = this.numericalColumns[1];
    }
    this.filteredAvailableColourByOptions = this.availableColourByOptions;
    if (this.selectedXAxisColumnName && this.selectedYAxisColumnName) {
      // this.generate();
    }
  }

  onPlotTypeChange() {
    this._selectedXAxisColumnName = '';
    this._selectedYAxisColumnName = '';
    this.selectedColourBy = '';

    this.updateColumnNamesBasedOnPlotType();
    this.filteredXAxisColumnNames = [...this.xAxisColumnNames];
    this.filteredYAxisColumnNames = [...this.yAxisColumnNames];
    this.availableColourByOptions = this.filteredAvailableColourByOptions;

    this.isLineFitEnabled = false;
  }

  updateColumnNamesBasedOnPlotType() {
    switch (this.selectedPlotType) {
      case 'SCATTER_PLOT':
        this.xAxisColumnNames = this.numericalColumns;
        this.yAxisColumnNames = this.numericalColumns;
        this.filteredAvailableColourByOptions = [...this.numericalColumns, ...this.categoricalColumns];
        break;
      case 'BOX_PLOT':
        this.xAxisColumnNames = this.categoricalColumns;
        this.yAxisColumnNames = this.numericalColumns;
        this.filteredAvailableColourByOptions = [...this.numericalColumns, ...this.categoricalColumns];
        break;
      case 'HISTOGRAM':
        this.xAxisColumnNames = [...this.numericalColumns, ...this.categoricalColumns];
        this.filteredAvailableColourByOptions = [...this.numericalColumns, ...this.categoricalColumns];
        this._selectedYAxisColumnName = null
        break;
      case 'IQR_PLOT':
        this.yAxisColumnNames = this.numericalColumns;
        this.filteredAvailableColourByOptions = this.numericalColumns;
        this._selectedXAxisColumnName = null
        break;
      default:
        this.xAxisColumnNames = [];
        this.yAxisColumnNames = [];
    }
  }


  filterOptions(event: any, type: string) {
    const searchText = (event.target.value || '').trim().toLowerCase();
    switch (type) {
      case 'X':
        this.filteredXAxisColumnNames = searchText ? this.xAxisColumnNames.filter(columnName =>
          columnName.toLowerCase().includes(searchText)
        ) : this.xAxisColumnNames.slice();
        break;
      case 'Y':
        this.filteredYAxisColumnNames = searchText ? this.yAxisColumnNames.filter(columnName =>
          columnName.toLowerCase().includes(searchText)
        ) : this.yAxisColumnNames.slice();
        break;
      case 'Z':
        this.filteredAvailableColourByOptions = searchText ? this.availableColourByOptions.filter((option: any) =>
          option.toLowerCase().includes(searchText)
        ) : this.availableColourByOptions.slice();
        break;
    }
  }


  ngOnChanges(changes: SimpleChanges) {
    if (this.isFirstChange) {
      this.isFirstChange = false;
      return;
    }

    if (changes['interactive'] || changes['visualizationType']) {
      this.plotData = ''
      this.updateButtonState()
    }
  }

  pollForVisualization() {
    this.visualizationSubscription = interval(this.POLLING_INTERVAL)
      .pipe(
        switchMap(() => this.dataPreviewService.getVisualization(
          this.dataset_id,
          this._selectedXAxisColumnName,
          this._selectedYAxisColumnName ?? null,
          this.selectedPlotType ?? "",
          this.interactive,
          this._selectedColourBy,
          this.additional_config
        )),
        takeWhile(response => !response, true),
        catchError(error => {
          this.isLoading = false
          this.displayMessage = error;
          this.plotData = '';
          this.visualizationSubscription?.unsubscribe();
          return of(null);
        })
      )
      .subscribe(response => {
        if (response) {
          this.setPlotData(response);
          this.visualizationSubscription?.unsubscribe();
        }
      });
  }

  generate() {
    if (this.selectedXAxisColumnName == '' && this.selectedPlotType !== 'IQR_PLOT') {
      this.toaster.error('Please select X-axis feature', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }
    if (this.selectedYAxisColumnName == '' && this.selectedPlotType !== 'HISTOGRAM') {
      this.toaster.error('Please select Y-axis feature', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }
    this.isLoading = true;
    this.plotData = '';
    this.disableGenerateButton = true;

    this.additional_config = this.isLineFitEnabled ? {
      "line_fit": this.isLineFitEnabled
    } : undefined;

    this.dataPreviewService.getVisualization(
      this.dataset_id,
      this._selectedXAxisColumnName,
      this._selectedYAxisColumnName ?? null,
      this.selectedPlotType ?? "",
      this.interactive,
      this._selectedColourBy,
      this.additional_config
    ).then(async response => {
      if (response) {
        this.setPlotData(response);
        this.isLoading = false;
      } else {
        this.pollForVisualization();
      }
    }).catch(error => {
      this.isLoading = false
      this.displayMessage = error;
      this.plotData = '';
    });
  }

  setPlotData(response: any) {
    this.plotData = this.sanitizer.bypassSecurityTrustResourceUrl(`${this.configService.getAppAuxApiURL}/eda/file?path=${response}`);
    this.isLoading = false;
  }

  get selectedXAxisColumnName(): string {
    return this._selectedXAxisColumnName && this._selectedXAxisColumnName.length > 3500
      ? this._selectedXAxisColumnName.substring(0, 35) + '...'
      : this._selectedXAxisColumnName;
  }

  set selectedXAxisColumnName(value: string) {
    this._selectedXAxisColumnName = value;
    // if (this._selectedXAxisColumnName && this._selectedYAxisColumnName) {
    this.disableGenerateButton = false;
    // }
    // if (!this.isRadioButonChanged) {
    //   this.updateButtonState();
    // }

  }

  get selectedYAxisColumnName(): string {
    return this._selectedYAxisColumnName && this._selectedYAxisColumnName.length > 3500
      ? this._selectedYAxisColumnName.substring(0, 35) + '...'
      : this._selectedYAxisColumnName;
  }

  set selectedYAxisColumnName(value: string) {
    this._selectedYAxisColumnName = value;
    // if (this._selectedXAxisColumnName && this._selectedYAxisColumnName) {
    this.disableGenerateButton = false;
    // }
    if (!this.isRadioButonChanged) {
      this.updateButtonState();
    }

  }

  get selectedColourBy(): string {
    return this._selectedColourBy;
  }

  set selectedColourBy(value: string) {
    this._selectedColourBy = value;
    if (!this.isRadioButonChanged) {
      this.updateButtonState();
    }
  }

  public updateButtonState() {
    if (this.isRadioButonChanged) {
      this.selectedXAxisColumnName = '';
      this.selectedYAxisColumnName = '';
      this._selectedColourBy = '';
      this.isRadioButonChanged = false
    }
    const isXAndYAxisSelected = this.selectedXAxisColumnName !== '' && this.selectedYAxisColumnName !== '';

    // if (this.visualizationType == 'CONTOUR') {
    //   this.displayMessage = "Select X-axis, Y-axis and Color by with all numeric";
    //   this.disableGenerateButton = !(isXAndYAxisSelected && this.selectedColourBy !== '');
    //   this.plotData = '';
    //   return
    // }
    // if(this.visualizationType == 'SPLINEFIT' || this.visualizationType == 'LINEARFIT'){
    //   this.displayMessage = "Select X-axis, Y-axis and Color by with all numeric";
    //   this.plotData = '';
    // }
    if (this.interactive || !this.interactive) {
      this.disableGenerateButton = false;
      return;
    }

    // switch (this.visualizationType) {
    //   case 'DISTRIBUTION':
    //     this.displayMessage = "Select X-axis and Y-axis";
    //     this.plotData = '';
    //     this.disableGenerateButton = !isXAndYAxisSelected;
    //     break;
    //   case 'SPLINEFIT':
    //     this.displayMessage = "Select X-axis, Y-axis and Color by with all numeric";
    //     this.plotData = '';
    //     this.disableGenerateButton = !isXAndYAxisSelected;
    //     break;
    //   case 'LINEARFIT':
    //     this.displayMessage = "Select X-axis, Y-axis and Color by with all numeric";
    //     this.plotData = '';
    //     this.disableGenerateButton = !isXAndYAxisSelected;
    //     break;

    //   case 'CONTOUR':
    //     this.displayMessage = "Select X-axis, Y-axis and Color by with all numeric";
    //     this.disableGenerateButton = !(isXAndYAxisSelected && this.selectedColourBy !== '');
    //     this.plotData = '';
    //     break;

    //   default:
    //     this.disableGenerateButton = false
    //     break;
    // }
  }

  filteredXAxis() {
    return this.filteredXAxisColumnNames.filter(option => !this.excludedColumns.includes(option) && option !== this.selectedYAxisColumnName);
  }
  filteredYAxis() {
    return this.filteredYAxisColumnNames.filter(option => !this.excludedColumns.includes(option) && option !== this.selectedXAxisColumnName);
  }
  filteredAvailableColourBy() {
    return this.filteredAvailableColourByOptions.filter((option: any) => !this.excludedColumns.includes(option) && option !== this.selectedYAxisColumnName && option !== this.selectedXAxisColumnName);
  }

  truncate(name: string): string {
    return name.length > 1000 ? name.substring(0, 50) + '...' : name;
  }

  onLineFitChange() {
    this.disableGenerateButton = false;
  }
}
