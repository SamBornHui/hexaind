import { Component, Input, OnChanges, OnDestroy, SimpleChanges } from '@angular/core';
import { DataPreviewService } from '../services/data-preview.service'
import { PageEvent } from '@angular/material/paginator';
import { catchError, interval, of, Subscription, switchMap, takeWhile } from 'rxjs';

interface TableRow {
  first_column: any;
  [key: string]: any;
}

@Component({
  selector: 'app-statistics-schema',
  templateUrl: './statistics-schema.component.html',
  styleUrls: ['./statistics-schema.component.less']
})
export class StatisticsSchemaComponent implements OnChanges, OnDestroy {
  @Input() dataset_id!: string;

  isNumericalLoading: boolean = false;
  isCategoricalLoading: boolean = false;
  isLoading: boolean = false;
  isNumericalError: boolean = false;
  isCategoricalError: boolean = false;
  numericalDisplayedColumns: string[] = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 'missing'];
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
  numericalDataSource: TableRow[] = [];
  isNumericalExpanded = true;

  categoricalDisplayedColumns: string[] = ['unique', 'count', 'top', 'freq', 'missing'];
  categoricalDataSource: TableRow[] = [];
  isCategoricalExpanded = true;
  filteredNumericalDataSource: TableRow[] = [];
  filteredCategoricalDataSource: TableRow[] = [];
  convertval: any;
  roundValue = "0";
  displayedColumns: string[] = [];
  totalColumns: number = 0;
  totalRows: number = 0
  numericalPage: number = 1;
  numericalPageSize: number = 50;
  totalNumericalCols: number = 0;
  categoricalPage: number = 1;
  categoricalPageSize: number = 50;
  totalCategoricalCols: number = 0;
  isScientificNotationEnabled: boolean = false;

  numericalStatisticsSubscription: Subscription | null = null;
  categoricalStatisticsSubscription: Subscription | null = null;

  POLLING_INTERVAL = 5000;

  constructor(private dataPreviewService: DataPreviewService) { }

  ngOnInit() {
  }

  ngOnDestroy() {
    this.numericalStatisticsSubscription?.unsubscribe();
    this.categoricalStatisticsSubscription?.unsubscribe();
  }

  loadNumericalData() {
    this.resetNumericalColumns();
    this.isNumericalLoading = true;
    this.isNumericalError = false;

    this.dataPreviewService.getNumericalStatistics(this.dataset_id,this.numericalPage,this.numericalPageSize).then(async response => {
      if (response) {
        if (response.statistics) {
          this.setNumericalStatistics(response);
        } else if (response.api_job_id) {
          this.pollForNumericalStatistics();
        }
      } else {
        this.isNumericalLoading = false;
      }
    }).catch(error => {
      console.error('Error:', error);
      this.isNumericalLoading = false;
      this.isNumericalError = true;
    });
  }

  async setNumericalStatistics(response: any) {
    const numerical = await response.statistics
    if (numerical.length > 0) {
      this.prepareNumaricalTableData(numerical[0]);
      this.dataPreviewService.updateNumericalColumnNames(numerical[0].column_names);
    } else {
      this.dataPreviewService.updateNumericalColumnNames([]);
    }

    this.filteredNumericalDataSource = this.numericalDataSource;
    this.isNumericalLoading = false;
    this.totalNumericalCols = response.numerical_columns_count; 
    this.totalColumns = response.columns_count;
    this.totalRows = response.rows_count;
  }

  pollForNumericalStatistics() {
    this.numericalStatisticsSubscription = interval(this.POLLING_INTERVAL) 
    .pipe(
      switchMap(() => this.dataPreviewService.getNumericalStatistics(this.dataset_id,this.numericalPage,this.numericalPageSize)),
      takeWhile(response =>  response && !response.statistics, true),
      catchError(error => {
        console.error('Error during polling:', error);
        this.numericalStatisticsSubscription?.unsubscribe();
        return of(null);
      })
    )
    .subscribe(response => {
      if (response && response.statistics) {
        this.setNumericalStatistics(response);
        this.numericalStatisticsSubscription?.unsubscribe();
      } else {
        this.isNumericalLoading = false;
      }
    });
  }

  loadCategoricalData() {
    this.resetCategoricalColumns();
    this.isCategoricalLoading = true;
    this.isCategoricalError = false;

    this.dataPreviewService.getCategoricalStatistics(this.dataset_id,this.categoricalPage,this.categoricalPageSize).then(async response => {
      if (response) {
        if (response.statistics) {
          this.setCategoricalStatistics(response);
        } else if (response.api_job_id) {
          this.pollForCategoricalStatistics();
        }
      } else {
        this.isCategoricalLoading = false;
      }
    }).catch(error => {
      console.error('Error:', error);
      this.isCategoricalLoading = false;
      this.isCategoricalError = true;
    });
  }

  async setCategoricalStatistics(response: any) {
    const categorical = await response.statistics
    if (categorical.length > 0) {
      this.prepareCategoricalTableData(categorical[0]);
      this.dataPreviewService.updateCategoricalColumnNames(categorical[0].column_names);
    } else {
      this.dataPreviewService.updateCategoricalColumnNames([]);
    }

    this.filteredCategoricalDataSource = this.categoricalDataSource;
    this.isCategoricalLoading = false;
    this.totalCategoricalCols = response.categorical_columns_count; 
    this.totalColumns = response.columns_count;
    this.totalRows = response.rows_count;
  }

  pollForCategoricalStatistics() {
    this.categoricalStatisticsSubscription = interval(this.POLLING_INTERVAL) 
    .pipe(
      switchMap(() => this.dataPreviewService.getCategoricalStatistics(this.dataset_id,this.categoricalPage,this.categoricalPageSize)),
      takeWhile(response =>  response && !response.statistics, true),
      catchError(error => {
        console.error('Error during polling:', error);
        this.categoricalStatisticsSubscription?.unsubscribe();
        return of(null);
      })
    )
    .subscribe(response => {
      if (response && response.statistics) {
        this.setCategoricalStatistics(response);
        this.categoricalStatisticsSubscription?.unsubscribe();
      } else {
        this.isCategoricalLoading = false;
      }
    });
  }

  resetNumericalColumns() {
    this.numericalDisplayedColumns = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 'missing'];
    this.excludedColumns = [
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
    ]
    this.isNumericalExpanded = true;
    this.displayedColumns = [];
    this.numericalDataSource = [];
    this.filteredNumericalDataSource = [];
  }

  resetCategoricalColumns() {
    this.excludedColumns = [
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
    ]
    this.categoricalDisplayedColumns = ['unique', 'count', 'top', 'freq', 'missing'];
    this.isCategoricalExpanded = true;
    this.displayedColumns = [];
    this.categoricalDataSource = [];
    this.filteredCategoricalDataSource = [];
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['dataset_id']) {
      const previousValue = changes['dataset_id'].previousValue;
      const currentValue = changes['dataset_id'].currentValue;

      if (previousValue!==currentValue) {
        // this.getData();
        this.dataPreviewService.updateNumericalColumnNames([]);
        this.dataPreviewService.updateCategoricalColumnNames([]);
        this.dataPreviewService.updateNumericalDataSource([]);
        this.loadNumericalData();
        this.loadCategoricalData();
      }
    }
  }

  getData() {
    this.isLoading = true;
    this.isNumericalError = false;
    this.isCategoricalError = false;
    this.dataPreviewService.getData(this.dataset_id, 1, 1000).then(response => {
      this.displayedColumns = response.column_names;
      this.totalColumns = this.displayedColumns.length;
      this.totalRows = response.total_rows;
      this.isLoading = false;
    }).catch(error => {
      console.error('Error:', error);
      this.isLoading = false;
    });
  }

  getTotalColumns() {
    return this.numericalDisplayedColumns.length
  }

  getTotalRows() {
    const sourceArray = [...this.numericalDataSource, ...this.categoricalDataSource]
    return sourceArray.length
  }

  prepareNumaricalTableData(data: any) {
    const columnNames = ['Column Name'].concat(this.numericalDisplayedColumns);
    const rows = data.data;
    const firstColumn = data.column_names;

    this.numericalDataSource = rows.map((row: any[], index: string | number) => {
      const rowData: { [key: string]: any } = { 'Column Name': firstColumn[index] };
      row.forEach((cell: any, idx: number) => {
        rowData[columnNames[idx + 1]] = cell;
      });
      return rowData;
    });

    this.numericalDisplayedColumns = columnNames
    this.dataPreviewService.updateNumericalDataSource(this.numericalDataSource);
  }

  prepareCategoricalTableData(data: any) {
    const columnNames = ['Column Name'].concat(this.categoricalDisplayedColumns);
    const rows = data.data;
    const firstColumn = data.column_names;

    this.categoricalDataSource = rows.map((row: any[], index: string | number) => {
      const rowData: { [key: string]: any } = { 'Column Name': firstColumn[index] };
      row.forEach((cell: any, idx: number) => {
        rowData[columnNames[idx + 1]] = cell;
      });
      return rowData;
    });
    this.categoricalDisplayedColumns = columnNames;
  }

  toggleTable(type: any) {
    if (type === "numerical") {
      this.isNumericalExpanded = !this.isNumericalExpanded;
    }
    if (type === "categorical") {
      this.isCategoricalExpanded = !this.isCategoricalExpanded;
    }
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value.toLowerCase().trim();
    if (filterValue === '') {
      this.filteredNumericalDataSource = this.numericalDataSource;
      this.filteredCategoricalDataSource = this.categoricalDataSource;
    } else {
      this.filteredNumericalDataSource = this.numericalDataSource.filter(row =>
        Object.values(row).some(value =>
          value !== null && value !== undefined && value.toString().toLowerCase().includes(filterValue)));

      this.filteredCategoricalDataSource = this.categoricalDataSource.filter(row =>
        Object.values(row).some(value =>
          value !== null && value !== undefined && value.toString().toLowerCase().includes(filterValue)));
    }
  }

  getDisplayNumColumns() {
    return this.numericalDisplayedColumns.filter(col => !this.excludedColumns.includes(col))
  }

  getDisplayCatColumns() {
    return this.categoricalDisplayedColumns.filter(col => !this.excludedColumns.includes(col))
  }

  onNumericalPageChange($event: PageEvent) {
    this.numericalPage = $event.pageIndex + 1
    this.loadNumericalData();
  }

  onCategoricalPageChange($event: PageEvent) {
    this.categoricalPage = $event.pageIndex + 1
    this.loadCategoricalData();
  }
}