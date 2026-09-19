import {
  ChangeDetectorRef,
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
  EventEmitter,
  Output
} from '@angular/core';
import { DataPreviewService } from '../services/data-preview.service'
import { MatDialog } from "@angular/material/dialog";
import { DownloadRescaleVisualizeDataComponent } from 'src/app/dialogs/data-preview/download-rescale-vizualize-data/download-rescale-vizualize-data.component';
import { PageEvent } from '@angular/material/paginator';
import { DataCatalogComponent } from 'src/app/pages/tools/data-catalog/data-catalog.component';
import { DataCatalogService } from 'src/app/pages/tools/data-catalog/data-catalog.service';
import { ToastrService } from 'ngx-toastr';
import { catchError, interval, of, Subscription, switchMap, takeWhile } from 'rxjs';
import { DataService } from 'src/app/pages/data/services/data.service';
DataService

@Component({
  selector: 'app-data-preview-data',
  templateUrl: './data.component.html',
  styleUrls: ['./data.component.less']
})
export class DataPreviewDataComponent implements OnChanges, OnDestroy {
  @Input() dataset_id!: string;
  @Input() uc2SigmaFilePath: string | undefined;
  @Output() downloadTriggered = new EventEmitter<string>();

  isLoading: boolean = false
  isError: boolean = false;
  displayedColumns: string[] = [];
  dataSource: any[] = [];
  filteredData: any[] = [];
  totalRows: number = 0;
  totalColumns: number = 0;
  totalRowsToShow: number = 0;
  totalColumnsToShow: number = 0;
  editableColumnName: string | null = null;
  currentEditValue: string = '';
  roundValue = "0";
  convertval: any;
  enableVisButton: boolean = false;
  vizTrialsData: any[] = []
  sliderValue: any
  currentPage: number = 1
  sliderIncreamentValue: any | undefined;
  rowCountPerPage: any = 50
  isDataBeingFetchedWhenScrolling = false
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
  isDataRequestedBeyondLimit: boolean = false
  isScientificNotationEnabled: boolean = false;

  MAX_ROWS: number = 1000;
  MAX_COLUMNS: number = 500;
  showRowsBeyondLimitAlert: boolean = false;
  showColsBeyondLimitAlert: boolean = false;

  POLLING_INTERVAL = 5000;

  dataSubscription: Subscription | null = null;
  filePath: any;

  @ViewChild('scrollableDiv') scrollableDiv!: ElementRef;

  constructor(
    private dataCatService: DataCatalogService,
    private dataPreviewService: DataPreviewService,
    public dialog: MatDialog,
    private cdr: ChangeDetectorRef,
    public toaster: ToastrService,
    private dataService: DataService
  ) { }

  ngOnInit() {
  }

  ngOnDestroy() {
    this.dataSubscription?.unsubscribe();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['dataset_id']) {
      const previousValue = changes['dataset_id'].previousValue;
      const currentValue = changes['dataset_id'].currentValue;

      if (previousValue!==currentValue) {
        this.getData();
      }
    }
  }

  pollForData() {
    this.dataSubscription = interval(this.POLLING_INTERVAL) 
    .pipe(
      switchMap(() => this.dataPreviewService.getData(this.dataset_id, this.currentPage, this.rowCountPerPage)),
      takeWhile(response => !response.data, true),
      catchError(error => {
        console.error('Error during polling:', error);
        this.dataSubscription?.unsubscribe();
        return of(null);
      })
    )
    .subscribe(response => {
      if (response && response.data) {
        this.processDataResponse(response)
        this.dataSubscription?.unsubscribe();
      } else {
        this.isLoading = false;
      }
    });
  }

  getData() {
    this.isLoading = true;
    this.isError = false;
    this.isDataRequestedBeyondLimit = false
    if(this.uc2SigmaFilePath) {
      this.dataCatService.getUC2SigmaDataPreview(this.uc2SigmaFilePath).then(response=>{
        this.processDataResponse(response)
      }).catch(error => {
        console.error('Error:', error);
      });
      return;
    }

    this.dataPreviewService.getData(this.dataset_id, this.currentPage, this.rowCountPerPage).then(response => {
      if (response.data) {
        this.processDataResponse(response)
      } else {
        this.pollForData();
      }      
    }).catch(error => {
      console.error('Error:', error);
      this.isLoading = false;
      this.isError = true;
    });
  }

  processDataResponse(response: any) {
      this.displayedColumns = response.column_names
      this.dataSource = response.data;
      this.filteredData = this.dataSource;
      this.totalRows = response.total_rows;
      this.totalRowsToShow = this.totalRows;

      this.totalColumns = response.total_columns;
      this.totalColumnsToShow = this.totalColumns;
      
      if (this.totalRowsToShow>this.MAX_ROWS) {
        this.totalRowsToShow = this.MAX_ROWS;
        this.showRowsBeyondLimitAlert = true;
      }

      if (this.totalColumnsToShow>this.MAX_COLUMNS) {
        this.totalColumnsToShow = this.MAX_COLUMNS;
        this.showColsBeyondLimitAlert = true;
      }

      this.isLoading = false
      this.checkVisulazData();
  }

  getDataWhenScrolled() {
    this.isDataBeingFetchedWhenScrolling = true
    this.dataPreviewService.getData(this.dataset_id, this.currentPage, this.rowCountPerPage).then(response => {
      this.dataSource = this.dataSource.concat(response.data);
      this.filteredData = this.dataSource;
      this.isDataBeingFetchedWhenScrolling = false
      this.checkVisulazData();
      this.cdr.detectChanges();
    }).catch(error => {
      console.error('Error:', error);
    });
  }

  isDataFetcedBeyondTheLimit(response: any) {
    if(response?.data?.length == 0) {

      if (response?.total_rows>this.MAX_ROWS) {
        this.toaster.warning('The data requested is beyond the limit (1000 rows)', '', {
          positionClass: 'custom-toast-position',
        });
      }
      
      this.isDataRequestedBeyondLimit = true
      return true
    }
    return false
  }

  checkVisulazData() {
    var vis_dir_index = this.displayedColumns.indexOf('visual_dir');
    if (vis_dir_index != -1) {
      let filteredVizData = this.dataSource.filter(item => {
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
        var trial_index_visual = this.displayedColumns.indexOf('trial_index_visual');
        for (var i = 0; i < filteredVizData.length; i++) {
          let Obj = {
            "visual_dir": filteredVizData[i][vis_dir_index],
            "trial_index": filteredVizData[i][vis_trial_index],
            "job_id": filteredVizData[i][job_id_index],
            "batch": filteredVizData[i][batch_index],
            "trial_status": filteredVizData[i][status_index],
            "trial_index_visual": filteredVizData[i][trial_index_visual],
            "selected": false
          }
          dataToSend.push(Obj);
          if (i == filteredVizData.length - 1) {
            this.vizTrialsData = dataToSend
          }
        }
      }
    }
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value.toLowerCase();
    this.filteredData = this.dataSource.filter(row => {
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
      this.displayedColumns = this.displayedColumns.map(name => name === oldName ? newName : name);
      this.dataPreviewService.renameColumn(this.dataset_id, { oldName: newName }).then(response => {
        this.getData()
      }).catch(error => {
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

  showDowloadDataDialog() {
    const dialogRef = this.dialog.open(DownloadRescaleVisualizeDataComponent, {
      maxWidth: '30vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: {
        trialsData: this.vizTrialsData
      },
    });

    dialogRef.afterClosed().subscribe((result) => {

    });
  }
  onSliderChange(event: any) {
    this.fetchPagedDataUsingSliderPercentage(event.target.value)
  }

  /**
   * This method calculates the required page to be fetched from the backend using the sliderValue which is in percentage.
   * (this.totalRows * sliderPercentage)/100 gives the starting row number at that particular percentage
   * when the starting row number was divided by rowCountPerpage it gives the repective page in which this row is present
   * If scroll bar is at 100 show last page which is at 99th percentage
   */
  fetchPagedDataUsingSliderPercentage(sliderPercentage: number) {
    if (sliderPercentage == 100) sliderPercentage = 99
    let pageNumber: number = Math.floor((this.totalRows * sliderPercentage) / (100 * this.rowCountPerPage)) + 1
    this.currentPage = pageNumber
    if (this.totalRows < this.rowCountPerPage) {
      const scrollableHeight = this.scrollableDiv.nativeElement.scrollHeight - this.scrollableDiv.nativeElement.clientHeight;
      const relativePosition = (sliderPercentage / 100) * scrollableHeight;
      this.scrollableDiv.nativeElement.scrollTop = relativePosition;
    }
    else {
      this.getData()
    }
  }

  onScroll(): void {
    const element = this.scrollableDiv.nativeElement;
    const scrollPosition = element.scrollTop;
    const maxScroll = element.scrollHeight - element.clientHeight;
    const scrollPercentage = (scrollPosition / maxScroll) * 100;

    if (scrollPercentage > 50 && !this.isDataBeingFetchedWhenScrolling) {
      this.currentPage += 1
      this.getDataWhenScrolled();
    }
  }

  onPageChange($event: PageEvent) {
    this.currentPage = $event.pageIndex + 1
    this.getData()
  }

  getDisplayColumns() {
    return this.displayedColumns.filter(col => !this.excludedColumns.includes(col))
  }

  refreshData() {
    this.getData();
  }

  async triggerDownloadDataset(){
    try{
      let datasetDetails : any = await this.dataService.getDataset(this.dataset_id)
      if(datasetDetails?.name){
        this.filePath = datasetDetails?.dataset_location[0]?.path
        if(this.filePath)
          this.downloadTriggered.emit(this.filePath);
        else
          this.toaster.error("File Path not found")
      }
      else
          this.toaster.error("File Path not found")
    }
    catch(error:any){
      this.toaster.error(error)
    }
  }
}

