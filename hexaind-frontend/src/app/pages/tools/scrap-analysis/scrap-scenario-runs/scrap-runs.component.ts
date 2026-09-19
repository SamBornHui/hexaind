import { 
  Component, 
  OnInit, 
  ViewChild, 
  Input, 
  Output, 
  EventEmitter 
} from '@angular/core';

import {
  HttpClient,
  HttpEventType,
} from '@angular/common/http';
import { Subscription } from 'rxjs';
import * as Plotly from 'plotly.js-dist-min';
import { ToastrService } from 'ngx-toastr';
import { MatTableDataSource } from '@angular/material/table';
import { ConfigService } from 'src/app/services/config.service';
import { Router } from '@angular/router';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { MatSort } from '@angular/material/sort';
import { ApiService } from 'src/app/services/api.service';
import { MatMenuTrigger } from '@angular/material/menu';
import { ScrapAnalysisService } from '../services/scrap-analysis.service'
import { formatDate } from '@angular/common';
import { Utils } from 'src/app/utils';

@Component({
  selector: 'app-scrap-runs',
  templateUrl: './scrap-runs.component.html',
  styleUrls: ['./scrap-runs.component.less'],
})
export class ScrapRunsComponent implements OnInit {
  @Input() scrapAllFiles: any;
  @Input() useCasesList: any;
  @Output() editScenarioEvent = new EventEmitter();

  @ViewChild(MatSort, { static: true }) sort!: MatSort;
  sort_by:string = 'usecase_name'
  public deleteConfirmation: boolean = false;
  @ViewChild('rootMenu') rootMenu!: MatMenuTrigger;
  @Output() viewRunEvent = new EventEmitter();
  currentUser:any = {}
  assets: any = {};

  constructor(
    private http: HttpClient,
    public toaster: ToastrService,
    private configService: ConfigService,
    private router: Router,
    private errorHandlerService: ErrorHandlerService,
    private apiService:ApiService,
    private scrapAnalysisService:ScrapAnalysisService
  ) {

  }

  showMainHeader: boolean = false;
  displayedColumns: string[] = [
    'usecase_name',
    'desc',
    'baseline_file_name',
    'no_of_scenarios',
    'created_date',
    'modified_date',
    'actions',
  ];
  dataSource:any;
  apiCall: boolean = false;

  ngOnInit(): void {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    this.fetchUseCases();
  }
  onIconClick(event: MouseEvent): void {
    // Stop the event from propagating
    event.stopPropagation();
  }
  checkUserCanDelete(usecase: any) {
    if (usecase.user_id == this.currentUser._id) {
      return true;
    } else {
      if (this.currentUser.server_role == 'Server Admin' || this.currentUser.server_role == 'Project Admin') {
        return true;
      }
    }
    
    return false;
  }

  deleteUsecase(usecase:any){
    this.scrapAnalysisService
    .deleteSamData({
      id:usecase.usecase_id,
      type:'usecase',
      document_project:this.configService.SelectedProjectId,
      project_id:this.configService.SelectedProjectId
    })
    .then((response) => {
      this.apiCall = false;
      if (response) {
        this.toaster.success(response['message'], '', {
          positionClass: 'custom-toast-position',
        });
        this.deleteConfirmation = false;
        let filteredData = this.useCasesList.filter((element:any)=>element.usecase_id != usecase.usecase_id);
        this.useCasesList = filteredData;
        this.setDataSource();
      }else{
        this.toaster.error(response['message'], '', {
          positionClass: 'custom-toast-position',
        });
      } 
    })
    .catch((error) => {
      this.apiCall = false;
      console.error('Failed to delete file:', error);
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

  fetchUseCases(){
    this.apiCall = true;
    this.scrapAnalysisService
      .getUseCasesData()
      .then((response) => {
        this.apiCall = false;
        if (response) {
          this.useCasesList = response;
          this.useCasesList.forEach((element:any) => {
            element.baseline_file_name = this.showBaseFileName(element.baseline_file)
          });
          this.useCasesList = this.useCasesList.sort((a:any, b:any) => {
            // Assuming `modified_date` is a Date object or a string in ISO format
            return new Date(b.modified_date).getTime() - new Date(a.modified_date).getTime();
          });
          this.setDataSource()
        }
      })
      .catch((error) => {
        this.apiCall = false;
        console.error('Failed to get usecases:', error);
    });
  }
  
  showBaseFileName(basefile:string){
    let index = this.scrapAllFiles.findIndex((file:any)=>file._id==basefile);
    return (index != -1)?this.scrapAllFiles[index].name:'N/A'
  }

  viewScenarioRun(event:MouseEvent,usecase:any){
    event.stopPropagation(); 
    this.viewRunEvent.emit({view:'vizualization',data:usecase,from_view:'runs'});
  }

  setDataSource(){
    this.makeTableReadable()
  }
  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value.trim().toLowerCase();
    this.dataSource.filter = filterValue;
  }

  makeTableReadable() {
    let sortedData = [...this.useCasesList]; // Make a copy of the array to avoid mutating the original
    this.dataSource = new MatTableDataSource(sortedData);
    this.dataSource.sort = this.sort;
    this.dataSource.sortingDataAccessor = (item: any, header: string) => {
      switch (header) {
        case 'usecase_name':
          return item.usecase_name.toLowerCase();
        case 'baseline_file_name':
          return item.baseline_file_name.toLowerCase();
        case 'no_of_scenarios':
          return item.scenarios.length;          
        case 'created_date':
          return new Date(item.created_date);
        case 'modified_date':
          return new Date(item.modified_date);  
        default:
          new Date(item.modified_date);
      }
    };
  }

  editScenario(event:MouseEvent,usecase:any){
    event.stopPropagation();
    this.editScenarioEvent.emit(usecase);
  }

  disableResultActionButton(usecase:any){
    let pathsList = usecase.scenarios
    .filter((scenario: any) => {
      return scenario.results?.excel_result && scenario.results.excel_result.trim() !== '';
    })
    .map((scenario: any) => {
      return { file_path: scenario.results.excel_result };
    });
    return (pathsList.length>0)?false:true;
  }

  

  async onDownload(event:MouseEvent,usecase:any) {
    event.stopPropagation();
    let pathsList = usecase.scenarios
    .filter((scenario: any) => {
      return scenario.results?.excel_result && scenario.results.excel_result.trim() !== '';
    })
    .map((scenario: any) => {
      return { file_path: scenario.results.excel_result.substring(0, scenario.results.excel_result.lastIndexOf('/')) };
      // return { file_path: scenario.results.excel_result };
    });

    let resultFiles = usecase.scenarios
    .filter((scenario: any) => {
      return scenario.results?.excel_result && scenario.results?.intermediate_processing?.file_path.trim() !== '';
    })
    .map((scenario: any) => {
      return {
        file_path: scenario.results?.excel_result && scenario.results?.intermediate_processing?.file_path?.substring(0, scenario.results?.intermediate_processing?.file_path.lastIndexOf('/'))
      };      
      // return { file_path: scenario.results?.excel_result && scenario.results?.intermediate_processing?.file_path };
    });
    if(resultFiles.length){
      pathsList = pathsList.concat(resultFiles);
      
    }
    if(pathsList.length>0){
      const uniqueFilePaths = Array.from(
        new Set(pathsList.map((file:any) => file.file_path))
      ).map(file_path => ({ file_path }));
      
      this.apiService
      .downloadWorkflowResultData(uniqueFilePaths)
      .subscribe({
        next: (blob: Blob) =>
          this.handleBlob(blob,usecase.usecase_name),
        error: (error: any) => {
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
    
    let nameWithoutExtension: string;
    if (fileName.includes('.')) {
        nameWithoutExtension = fileName.split('.').slice(0, -1).join('.');
    } else {
        nameWithoutExtension = fileName;
    }

    link.setAttribute('download', nameWithoutExtension+'.zip');
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(blobUrl);
    link.remove();
  }

  runScenarios(usecase:any){
    usecase.runScenario = true;
    this.scrapAnalysisService
    .runUsecasScenarios(usecase.usecase_id,this.currentUser._id)
    .then((response) => {      
      if (response) {
        if(response['usecase_id'] && response['usecase_id'] !=''){
          this.toaster.success('Scenario run successfully', '', {
            positionClass: 'custom-toast-position',
          });           
          let useCaseIndex = this.useCasesList.findIndex((item:any)=>item.usecase_id == usecase.usecase_id);
          if(useCaseIndex != -1){
            this.useCasesList[useCaseIndex] = response;
          }     
          setTimeout(() => {
            this.setDataSource();
          }, 20);          
        }else{
          this.toaster.error(response['message'], '', {
            positionClass: 'custom-toast-position',
          });
        }              
      } else{
        this.toaster.error('Failed to run scenarios', '', {
          positionClass: 'custom-toast-position',
        });
      }
      
    })
    .catch((error) => {
      console.error('Failed to run scenarios:', error);
      this.toaster.error('Failed to save scenario', error, {
        positionClass: 'custom-toast-position',
      });
    });  
  }

  
}
