import {
  Component,
  ChangeDetectorRef,
  HostListener,
  ViewChild,
} from '@angular/core';
import { ApiService } from "src/app/services/api.service";
import { NavService } from 'src/app/controls/left-nav/nav.service';
import { ElementRef, Renderer2 } from '@angular/core';
import { DataService } from './services/data.service';
import { Subject, Subscription } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { MatDialog } from '@angular/material/dialog';
import { ModuleImportDialogComponent } from 'src/app/dialogs/module-import-dialog/module-import-dialog.component';
import { ModuleService } from './services/module.service';
import { DataImportDialogComponent } from 'src/app/dialogs/data-import/data-import-dialog.component';
import { ActivatedRoute, Router } from '@angular/router';
import { ConnectorType } from 'src/app/models/connector-models';
import { ConnectorDialogComponent } from 'src/app/dialogs/connector-dialog/connector-dialog.component';

import { takeUntil } from 'rxjs/operators';
import { Dataset } from '../../models/data-models';
import { Utils } from 'src/app/utils';
import { DataPreviewComponent } from 'src/app/dialogs/data-preview/data-preview.component';
import { MatMenuTrigger } from '@angular/material/menu';
import { UpdateDatasetsComponent } from 'src/app/dialogs/update-datasets/update-datasets.component';
import { NotificationComponent } from 'src/app/controls/notification/notification.component';
import { MountedDriveDataPreviewComponent } from 'src/app/dialogs/mounted-drive-data-preview/mounted-drive-data-preview.component';
import { Sort, MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';



import { ToastrService } from 'ngx-toastr';
import { ConfigService } from '../workflow-designer/workflow-canvas.service';
import { VisualizeTextdataComponent } from 'src/app/dialogs/data-preview/visualize/visualize-textdata/visualize-textdata.component';
@Component({
  selector: 'app-data',
  templateUrl: './data.component.html',
  styleUrls: ['./data.component.less'],
})
export class DataComponent {
  @ViewChild('notification') notificationComponent!: NotificationComponent;
  private searchTerms = new Subject<string>();
  searchText: string = '';
  selectedWorkflowRow: any = null;
  showUserContextMenu = false;
  pageTitle: string = 'Datasets';
  displayedColumns: string[] = [
    'name',
    'type',
    'size',
    'created_by',
    'created_at',
    'last_modified',
    'more_vert',
  ];

  dataSource: any;
  searchResults: any[] = [];
  searchModuleResults: any[] = [];
  moduleSource: any;
  assetType: string = 'dataset';
  selectedOwner: string = '';
  selectedSort: string = 'Most recent';
  numberOfColumns: number = 1;
  screenWidth: number = 0;
  dialogRef: any;
  private boundResizeFunction: () => void;
  private destroy$ = new Subject<void>();
  public deleteConfirmation: boolean = false;
  showDeleteConfirmation: boolean = false;
  descending: boolean = true;
  assets: any = {};
  dataset_owners: any;

  @ViewChild('deleteConfirmation')
  deleteConfirmationMenu!: MatMenuTrigger;
  moreOptions: boolean = false;
  datasetSource!: MatTableDataSource<any>;
  @ViewChild(MatSort, { static: true }) sort!: MatSort;
  // @ViewChild('searchInput') searchInput!: MatInput;
  private projectSubscription: Subscription | undefined = undefined;
  getUrl: any;
  isDataSetLoaded: boolean = false;
  selectedValue: boolean = true;

  // Other component code

  @HostListener('document:click', ['$event'])
  clickOutside(event: Event) {
    if (!this.deleteConfirmationMenu.menuOpen) {
      this.resetDeleteConfirmation();
    }
  }

  resetDeleteConfirmation() {
    this.showDeleteConfirmation = false;
  }

  constructor(
    private cdRef: ChangeDetectorRef,
    public navService: NavService,
    private renderer: Renderer2,
    private el: ElementRef,
    private dataService: DataService,
    private moduleService: ModuleService,
    public dialog: MatDialog,
    private apiService: ApiService,
    public toaster: ToastrService,
    private configService: ConfigService,
    private route: ActivatedRoute
  ) {

    const rolesfeaturesString = localStorage.getItem('rolesfeatures');
    if (rolesfeaturesString !== null) {
      this.assets = JSON.parse(rolesfeaturesString).assets.datasets;
    } else {
      this.assets = "server_admin";
      console.error('No rolesfeatures found in localStorage.');
    }
    this.dataService.currentAssetType
      .pipe(takeUntil(this.destroy$))
      .subscribe((assetType) => {
        if (assetType && assetType === 'dataset' || assetType === 'module') {
          this.assetType = assetType;
          if (this.assetType === 'dataset') {
            this.pageTitle = 'Datasets';
            this.searchText = '';
            this.getData();
          }
          if (this.assetType === 'module') {
            this.pageTitle = 'Python Modules';
            this.searchText = '';
            this.getModules();
          }
        }
      });

    this.renderer.listen('document', 'click', (event) => {
      if (this.el.nativeElement.contains(event.target)) {
        this.showUserContextMenu = false;
      }
    });

    this.searchTerms.pipe(debounceTime(500)).subscribe((term) => {
      this.searchText = term;
      if (this.assetType === 'dataset') {
        this.datasetSource.filter = this.searchText.trim().toLowerCase();
      }
      if (this.assetType === 'module') {
        this.getModules();
      }
    });

    this.boundResizeFunction = this.onResize.bind(this);
    window.addEventListener('resize', this.boundResizeFunction);
  }

  ngOnInit() {
    this.datasetSource = new MatTableDataSource<any>([]);
    this.datasetSource.sort = this.sort;
    this.getData();
    this.sortProjectsByLastModified();
    this.numberOfColumns = this.getNumberOfColumns();

    this.projectSubscription =
      this.configService.selectedProjectIdObservable.subscribe((projectId: any) => {
        if (projectId) {
          this.getData();
        }
      });

      const datasetId = this.route.snapshot.queryParams['dataset_id'];
      var dataset = {_id: datasetId}      
      if (dataset && dataset._id !== undefined) {
        this.openDataPreviewDialog(dataset);
      }
  }

  ngAfterViewInit() {
    this.screenWidth = window.innerWidth;

    setTimeout(() => {
      this.calculateColumns();
    }, 250);
  }

  ngOnDestroy() {
    // Remove the event listener when the component is destroyed
    window.removeEventListener('resize', this.boundResizeFunction);
    this.projectSubscription?.unsubscribe();
    this.destroy$.next();
    this.destroy$.complete();
  }

  onResize(event?: Event) {
    this.calculateColumns();
    this.screenWidth = window.innerWidth;
    this.cdRef.detectChanges();
  }

  private calculateColumns() {
    const parentWidth = document.querySelector('[fxLayout]')!.clientWidth; // Ensure this selects your flex container
    this.numberOfColumns = Utils.CalculateColumns(parentWidth);
  }

  getNumberOfColumns(): number {
    let screenWidth = window.innerWidth;
    let tileCount = Math.floor(screenWidth / 220);
    return tileCount;
  }

  onSearchTextChange(event: Event) {
    let searchTerm = (event.target as HTMLInputElement).value.trim();
    let result= [];
    if(searchTerm){
    result= this.searchResults.filter((session: any) => {
      searchTerm = searchTerm.toLowerCase();
        return (session.name.toLowerCase().includes(searchTerm) ||  
        session.description.toLowerCase().includes(searchTerm));
      
    });
    this.datasetSource.data = result;
    }else{
    this.datasetSource.data = [...this.searchResults];
    }
  }

  isWorkflowRowSelected(row: any): boolean {
    return this.selectedWorkflowRow === row;
  }

  openConnectorPopup(type: string) {
    this.dialogRef = this.dialog.open(ConnectorDialogComponent, {
      width: '560px',
      data: { selectedConnector: type, skipStep: true },
      disableClose: true,
    });
    this.dialogRef.afterClosed().subscribe((result: any) => {
      // Add any logic to handle the dialog closure
    });
  }

  closeRescalePopup(): void {
    this.dialogRef.close();
  }

  async getData() {
    this.isDataSetLoaded = false
    let datasets = await this.dataService.GetDatasets(this.searchText);
    let modules = await this.moduleService.GetModules(this.searchText);
    if (modules && modules.modules.length > 0 || datasets && datasets.datasets.length > 0) {
      this.moduleSource = modules.modules;
      if (this.moduleSource.length > 0) {
        this.moduleSource.forEach((element: any) => {
          const array = [];
          array.push({
            "extension": element.module_location.extension
          })
          element.dataset_location = array;
        });
      }
      this.dataSource = datasets.datasets;
      const dataResult = this.moduleSource.concat(this.dataSource);
      this.searchResults = [...dataResult];
      this.datasetSource.data = this.searchResults;
      this.dataset_owners = this.getUniqueOwners(this.searchResults);
    }
    if (modules && modules.modules.length <= 0 && datasets && datasets.datasets.length <= 0) {
      this.searchResults = [];
      this.datasetSource.data = this.searchResults;
    }
    this.fileSizeConveter();
    this.sortProjectsByLastModified();
    this.isDataSetLoaded = true
  }
  async ConvertToCsv(rowData: any) {
    const data = {
      conversion_type: "TABULAR_PARQUET_TO_CSV",
      from_config: {
        dataset_id: rowData._id
      },
      to_config: {
        name: "CSV"
      },
      retain_older: "True"
    }
    await this.apiService.AssestDataModification(rowData.site_id, rowData.project_id, data);
    this.getData();
  }
  async getModules() {
    let modules = await this.moduleService.GetModules(this.searchText);
    if (modules && modules.modules.length > 0) {
      this.moduleSource = modules.modules;
      this.searchModuleResults = [...this.moduleSource];
    }
    if (modules && modules.modules.length <= 0) {
      this.searchModuleResults = [];
    }
  }

  uploadFile($event: any, file_type: string) {
    const dialogRef = this.dialog.open(DataImportDialogComponent, {
      width: '560px',
      data: {
        file: $event.target.files[0],
        file_type,
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.toaster.success('Created Successfully', '', {
          positionClass: 'custom-toast-position'
        });
      } 
      else {
        this.toaster.error(result.error, '',{
          positionClass: 'custom-toast-position'
        });
      }
      this.getData();
    });
  }

  uploadModule($event: any, file_type: string) {
    const dialogRef = this.dialog.open(ModuleImportDialogComponent, {
      width: '560px',
      data: {
        file: $event.target.files[0],
        file_type,
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.toaster.success('Created Successfully', '',{
          positionClass: 'custom-toast-position'
        });
        this.getData();
      }
    });
  }

  onRefreshView(){
    this.searchText='';
    this.getData();
    this.selectedValue = false;
  }

  onToggleSort() {
    this.descending = !this.descending;
    this.sortProjectsByLastModified();
  }

  datasetOwner(event : any){
    this.datasetSource.data = this.searchResults;
    let filteredResults = this.datasetSource.data.filter((session: any) => {
      if (session.user_id == event.user_id) {
        return session;
      }
    });
    this.datasetSource.data = filteredResults;
    this.selectedValue = true;
  }

  getUniqueOwners(sessions: any[]){
    const uniqueOwnersMap: { [userId: string]: string } = {};
    sessions.forEach((session) => {
      uniqueOwnersMap[session.user_id] = session.created_by;
    });

    return Object.keys(uniqueOwnersMap).map((userId) => ({
      user_id: userId,
      user_name: uniqueOwnersMap[userId],
    }));
  }


  displayPreviewMessage(){
    this.toaster.error('Preview not available', '',{
      positionClass: 'custom-toast-position'
    });
  }

  sortProjectsByLastModified(): void {
    this.searchResults.sort((a, b) => {
      const dateA = new Date(a.dataset_location[0].last_modified_at).getTime();
      const dateB = new Date(b.dataset_location[0].last_modified_at).getTime();
      return this.descending ? dateB - dateA : dateA - dateB;
    });
    this.searchResults = [...this.searchResults]
    this.datasetSource.data = this.searchResults;
  }

  deleteData(rowdata: any) {
    if(rowdata.module_type){
      rowdata.dataset_type = rowdata.module_type;   // If type is Python adding here to dataset_type
    }
    const payload = {
      dataset_ids: [rowdata._id],
      delete_type: 'HARD',
      dataset_type: rowdata.dataset_type,
    };
    this.dataService.DeleteDataset(payload).subscribe((res: any) => {
      if (res.response[0].status == 'SUCCESS') this.getData();
      this.showDeleteConfirmation = false;
    });
  }

  isCsvFile(rowData: Dataset): boolean {
    const extension = rowData.dataset_location[0].extension.toLowerCase();
    return extension === '.csv';
  }

  isJsonFile(rowData: Dataset): boolean {
    const extension = rowData.dataset_location[0].extension.toLowerCase();
    return extension === '.json';
  }

  isTextFile(rowData: Dataset): boolean {
    const extension = rowData.dataset_location[0].extension.toLowerCase();
    return extension === '.txt';
  }

  isParquetFile(rowData: Dataset): boolean {
    const extension = rowData.dataset_location[0].extension.toLowerCase();
    return extension === '.parquet';
  }

  isPythonFile(rowData: any): boolean {
    if (rowData.module_location && rowData.module_location.extension) {
      const extension = rowData.module_location.extension.toLowerCase();
      return extension === 'py';
    }
    return false;
  }

  isImageFile(rowData: Dataset): boolean {
    const extension = rowData.dataset_location[0].extension.toLowerCase();
    return ['.jpg', '.jpeg', '.png', '.gif', '.bmp'].includes(extension);
  }

  isPDFFile(rowData: Dataset): boolean {
    const extension = rowData.dataset_location[0].extension.toLowerCase();
    return extension === '.pdf';
  }

  isZipFile(rowData: any): boolean {
    if (rowData.module_location && rowData.module_location.extension) {
      const extension = rowData.module_location.extension.toLowerCase();
      return extension === 'zip';
    }
    return false;
  }


  fileSizeConveter() {
    this.sortProjectsByLastModified();
    for (let k = 0; this.searchResults.length > k; k++) {
      let bytesDataset = this.searchResults[k].dataset_location[0].size;
      const sizesDataset = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
      const iDataset = Math.floor(Math.log(bytesDataset) / Math.log(1024));
      this.searchResults[k].dataset_location[0].size = `${parseFloat((bytesDataset / Math.pow(1024, iDataset)).toFixed(1))} ${sizesDataset[iDataset]}`;
      this.searchResults[k]['size'] = `${parseFloat((bytesDataset / Math.pow(1024, iDataset)).toFixed(1))} ${sizesDataset[iDataset]}`;
      this.searchResults[k]['last_modified'] = this.searchResults[k]['dataset_location'][0]?.last_modified_at;
      this.searchResults[k]['type'] = this.searchResults[k]['dataset_type'];
      // For module_location.size
      if (this.searchResults[k].module_location && this.searchResults[k].module_location.size) {
        let bytesModule = this.searchResults[k].module_location.size;
        const sizesModule = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const iModule = Math.floor(Math.log(bytesModule) / Math.log(1024));
        this.searchResults[k].module_location.size = `${parseFloat((bytesModule / Math.pow(1024, iModule)).toFixed(1))} ${sizesModule[iModule]}`;
        this.searchResults[k]['size'] = `${parseFloat((bytesModule / Math.pow(1024, iModule)).toFixed(1))} ${sizesModule[iModule]}`;
        this.searchResults[k]['last_modified'] = this.searchResults[k]['module_location']['last_modified_at'];
        this.searchResults[k]['type'] = this.searchResults[k]['module_type'];
      }
    }
  }

  openDataPreviewDialog(dataset: any) {
    let dialogRef;
    console.log(dataset)
    if(dataset.type === "TEXT") {
      dialogRef = this.dialog.open(VisualizeTextdataComponent, {
        width: '75vw',
        maxWidth: '75vw',
        height: '75%',
        data: {
          datasetId: dataset._id,
        },
      })
    }
    else if(dataset.type === "PYTHON" || dataset.type === "JSON"){
      this.toaster.info('Preview not available for this file type', '', {
        positionClass: 'custom-toast-position'
      });
    }
    else {
      dialogRef = this.dialog.open(DataPreviewComponent, {
        width: '95vw',
        maxWidth: '95vw',
        height: '95%',
        data: {
          datasetId: dataset._id,
        },
      });
    }
    if(dialogRef){
      dialogRef.afterClosed().subscribe((result) => { });
    }
  }

  showMountedDriveDialog() {
    const dialogRef = this.dialog.open(MountedDriveDataPreviewComponent, {
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: {
        type: 'csv',
        name: '',
        description: ''
      },
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.toaster.success('Created Successfully', '', {
          positionClass: 'custom-toast-position'
        });
        this.getData();
      }
    });
  }

  openDatasetRenameDialog(dataset: any) {
    const dialogRef = this.dialog.open(UpdateDatasetsComponent, {
      width: '600px',
      maxWidth: '95vw',
      data: {
        name: dataset['name'],
        datasetId: dataset['_id'],
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result['status']) {
        this.toaster.success('Updated Successfully', '', {
          positionClass: 'custom-toast-position'
        });
        //this.notificationComponent.display(result['message'], 'success');
        this.getData();
      }
    });
  }

  async sortData(sort: Sort) {
    this.searchResults.sort((a, b) => {
      const aValue = a[sort['active']];
      const bValue = b[sort['active']];
      // Define a function to handle comparison based on data type
      const compareValues = (valueA: any, valueB: any) => {
        // Handle numbers
        if (!isNaN(valueA) && !isNaN(valueB)) {
          return valueA - valueB;
        }
        // Handle dates
        const dateA = new Date(valueA);
        const dateB = new Date(valueB);
        if (!isNaN(dateA.getTime()) && !isNaN(dateB.getTime())) {
          return dateA.getTime() - dateB.getTime();
        }
        // Handle strings
        return valueA.localeCompare(valueB);
      };

      // Call the compareValues function to compare the values
      const comparisonResult = compareValues(aValue, bValue);

      // Adjust the comparison result based on sort direction
      return sort['direction'] === 'asc' ? comparisonResult : -comparisonResult;
    });
    this.datasetSource.data = this.searchResults;

  }

  async openDatasetDownload(rowdata: any) {
    console.log(rowdata, "get rowdata"); 

    if(rowdata.module_type == 'PYTHON'){
      const downloadUrl = await this.apiService.DownloadDatset(rowdata.site_id, rowdata.project_id, rowdata._id,rowdata.module_type);
      console.log(downloadUrl, "download URL Pythonś");
  
    // If you received the correct URL, initiate the download
    if (downloadUrl) {
      // Create a hidden anchor element
      const link = document.createElement('a');
      link.href = downloadUrl; // Set the href to the download URL
      link.download = ''; // If you want a specific filename, set it here
      link.style.display = 'none'; // Hide the element
  
      document.body.appendChild(link); // Append to the DOM
      link.click(); // Programmatically trigger the click event
      document.body.removeChild(link); // Clean up the DOM by removing the link
    } else {
      console.error("Invalid download URL");
    }
    }else if(rowdata.dataset_type == 'TABULAR' || rowdata.dataset_type == 'TEXT'){
      const downloadUrl = await this.apiService.DownloadDatset(rowdata.site_id, rowdata.project_id, rowdata._id,rowdata.dataset_type);
      console.log(downloadUrl, "download URL tabluar");
  
    // If you received the correct URL, initiate the download
    if (downloadUrl) {
      // Create a hidden anchor element
      const link = document.createElement('a');
      link.href = downloadUrl; // Set the href to the download URL
      link.download = ''; // If you want a specific filename, set it here
      link.style.display = 'none'; // Hide the element
  
      document.body.appendChild(link); // Append to the DOM
      link.click(); // Programmatically trigger the click event
      document.body.removeChild(link); // Clean up the DOM by removing the link
    } else {
      console.error("Invalid download URL");
    }
    }
  
    // Get the download URL from your API service
    
    
    
  }
  
}
