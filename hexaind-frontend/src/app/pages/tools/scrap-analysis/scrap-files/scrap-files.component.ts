import { Component, EventEmitter, Input, OnInit, Output, ViewChild } from '@angular/core';
import { ConfigService } from 'src/app/services/config.service';
import { Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { ImportDatasetDialogComponent } from 'src/app/dialogs/import-dataset-dialog/import-dataset-dialog.component';
import { MatDialog } from '@angular/material/dialog';
import { AccessMode } from 'src/app/models/data-models';
import { ScrapAnalysisService } from '../services/scrap-analysis.service'
import { MatTableDataSource } from '@angular/material/table';
import { ApiService } from 'src/app/services/api.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { Utils } from 'src/app/utils';
import { MatSort } from '@angular/material/sort';


@Component({
  selector: 'app-scrap-files',
  templateUrl: './scrap-files.component.html',
  styleUrls: ['./scrap-files.component.less'],
})
export class ScrapFilesComponent implements OnInit {
  
  showMainHeader: boolean = false;
  // scrapAllFiles = [];
  apiCall: boolean = false;
  isDownloading: boolean = false;
  filter:string = 'admin_upload';
  baselineFilesColumns: string[] = [
    'name',
    'description',
    'add_date',
    'added_by',
    'add_method',
    'actions',
  ];
  // baselineFilesDataSource = BASELINE_FILES_DATA_LIST;
  baselineFilesDataSource:any;
  @Input() scrapAllFiles: any;
  @Output() baselineFileEvent = new EventEmitter();
  @ViewChild(MatSort, { static: true }) sort!: MatSort;
  assets: any = {};
  public deleteConfirmation: boolean = false;
  currentUser:any = {}
  constructor(
    private configService: ConfigService,
    private router: Router,
    public toaster: ToastrService,
    public dialog: MatDialog,
    private scrapAnalysisService: ScrapAnalysisService,
    private apiService:ApiService,
    private errorHandlerService:ErrorHandlerService,

  ) {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);  
  }

  ngOnInit() {
    this.fetchUploadedFiles();
  }

  checkUserCanDelete(file: any) {
    if (file.user_id == this.currentUser._id) {
      return true;
    } else if(this.currentUser.server_role == 'Server Admin' || this.currentUser.server_role == 'Project Admin') {
      return true;     
    }
    
    return false;
  }
  addFilter(type:string){
    this.filter = type;
    this.setDataSource();
  }

  fetchUploadedFiles(){
    this.apiCall = true;
    this.scrapAnalysisService
    .getUploadedFiles()
    .then((response) => {
      this.apiCall = false;
      if (response) {
        if(response.datasets){
          this.scrapAllFiles = response.datasets;
          this.scrapAllFiles.sort((a:any, b:any) => {
            // Assuming `modified_date` is a Date object or a string in ISO format
            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
          });
          this.baselineFileEvent.emit(this.scrapAllFiles);
          this.setDataSource();
        }
      } 
    })
    .catch((error) => {
      this.apiCall = false;
      console.error('Failed to get files:', error);
    });
  }
    lastAccessedDate(date: string) {
      if (!date.endsWith('Z')) {
        date += 'Z';
        return Utils.formatDateTime(date);
      } else {
        return Utils.formatDateTime(date);
      }
    }
  
  applyFilter(event: Event) {
      const filterValue = (event.target as HTMLInputElement).value.trim().toLowerCase();
      this.baselineFilesDataSource.filter = filterValue;
  }
  
  setDataSource(){
    if(this.filter=='all'){
      this.baselineFilesDataSource = new MatTableDataSource(this.scrapAllFiles);
    }else if(this.filter=='upload'){
      let uploadedData = this.scrapAllFiles.filter((element:any)=>(element.tags.includes('upload') && !element.tags.includes('admin_upload')));
      this.baselineFilesDataSource = new MatTableDataSource(uploadedData);
    }else if(this.filter=='admin_upload'){
      let uploadedData = this.scrapAllFiles.filter((element:any)=>element.tags.includes('admin_upload'));
      this.baselineFilesDataSource = new MatTableDataSource(uploadedData);
    }else if(this.filter=='scenario_run'){
      let scrapRunData = this.scrapAllFiles.filter((element:any)=>element.tags.includes('scenario_run'));
      this.baselineFilesDataSource = new MatTableDataSource(scrapRunData);    }
    this.baselineFilesDataSource.sort = this.sort;  
    this.baselineFilesDataSource.sortingDataAccessor = (item: any, header: string) => {
      switch (header) {
        case 'name':
          return item.name.toLowerCase();
        case 'description':
          return item.description.toLowerCase();
        case 'added_by':
          return item.created_by;          
        case 'add_method':
          return this.isUploadedFile(item)          
        case 'add_date':
          return new Date(item.created_at); 
        default:
          new Date(item.created_at);
      }
    };

  }

  isUploadedFile(file:any){
    if(file.tags.includes('upload') && !file.tags.includes('admin_upload')){
      return 'User upload';
    }else if(file.tags.includes('upload') && file.tags.includes('admin_upload')){
      return 'Admin upload'
    }else if(file.tags.includes('scenario_run')){
      return 'Scenario Run'
    }

    return '';
  }

  importDataDialog() {
    const dialogRef = this.dialog.open(ImportDatasetDialogComponent, {
      height: '90%',
      width: '60%',
      data: {
        file_type: 'excel',
        tags : ['sam', 'upload', 'scrap_analysis'],
        accessMode:AccessMode.INTERNAL
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.fetchUploadedFiles();
      }
    });
  }
  
  async onDownload(element:any) {
    this.isDownloading = true;
    let filePath = element.dataset_location[0].path;
    if(filePath){
      let type = 'baseline'
      let fileName = element.name+'.xlsx';
      let data:any = {
        type:type,
        dataset_id:element._id,
      }
      
      this.scrapAnalysisService
      .downloadSamFilesData(data)
      .subscribe({
        next: (blob: Blob) =>
          this.handleBlob(blob,fileName),
        error: (error: any) => {
          this.isDownloading = false;
          console.error('Download failed:', error);
          this.errorHandlerService.handleError(error);
        },
      });
    }
  }
  
  private handleBlob(
    blob: Blob,
    fileName:string
  ) {
    const blobUrl = window.URL.createObjectURL(blob);
    this.triggerDownload(blobUrl, fileName);
  }

  private triggerDownload(blobUrl: string, fileName: string) {
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(blobUrl);
    link.remove();
    this.isDownloading = false;
  }
  onIconClick(event: MouseEvent): void {
    // Stop the event from propagating
    event.stopPropagation();
  }

  deleteBaselineFile(baseline:any){
    this.scrapAnalysisService
    .deleteSamData({
      id:baseline._id,
      type:'baseline',
      document_project:baseline.project_id,
      project_id:this.configService.SelectedProjectId
    })
    .then((response) => {
      this.deleteConfirmation = false
      if (response) {
        this.toaster.success(response['message'], '', {
          positionClass: 'custom-toast-position',
        });
        let filteredData = this.scrapAllFiles.filter((file:any)=>file._id !=baseline._id);
        this.scrapAllFiles = filteredData;
        this.baselineFileEvent.emit(this.scrapAllFiles);
        this.setDataSource();
      }else{
        this.toaster.error(response['message'], '', {
          positionClass: 'custom-toast-position',
        });
      } 
    })
    .catch((error) => {
      this.deleteConfirmation = false
      console.error('Failed to delete file:', error);
    });
  }

}