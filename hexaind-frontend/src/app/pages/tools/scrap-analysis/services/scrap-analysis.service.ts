import { Injectable } from '@angular/core';
import {
  HttpClient,
  HttpHeaders,
  HttpErrorResponse,
} from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { Utils } from 'src/app/utils';
import { catchError, map, tap } from 'rxjs/operators';
import { BehaviorSubject, forkJoin, Observable, of, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ScrapAnalysisService {
  saveWorkflowBtnChange: Subject<any> = new Subject<any>();
  closeManageWorkflowChange: Subject<any> = new Subject<any>();

  constructor(
    private http: HttpClient,
    private configService: ConfigService,
    private sharedDataService: SharedDataService,
  ) { }
  returnKeysFromObject(inpObj: any) {
    return Object.keys(inpObj);
  }
  readConfig(): Observable<any> {
    return new Observable((observer) => {
      this.http.get('assets/sam-config/config.ini', { responseType: 'text' }).subscribe(
        (data: string) => {
          try {
            // Parse the INI file content
            observer.next(data);
            observer.complete();
          } catch (error) {
            observer.error('Error parsing INI file');
          }
        },
        (error) => {
          observer.error('Error reading INI file');
        }
      );
    });
  }

  async getUploadedFiles() {
    try {
      let url = `${this.configService.getAppApiURL}/sam/get_baselines`;
      let response = await this.http.get<any>(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async removeWorkflowForImage(payload: any) {
    try {
      payload['userId'] = localStorage.getItem('currUserID');
      let url = `${this.configService.getImageAnalysisUrl()}/deassociate_workflow_from_image`;
      let response = await this.http.post<any>(url, payload).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getFormatScrapData(path:string){
     try {
      let url = `${this.configService.getAppApiURL}/sam/format_scrap_data?file_path=${path}`;
      let response = await this.http.get<any>(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getUseCasesData(){
    try {
     let url = `${this.configService.getAppApiURL}/sam/get_scenarios`;
     let response = await this.http.get<any>(url).toPromise();
     return response;
   } catch (error) {
     if (error instanceof HttpErrorResponse) {
       this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
       throw error;
     }
   }
   return undefined;
 }

  async getFormatScrapDetailData(data:any){
    try {
     let url = `${this.configService.getAppApiURL}/sam/extract_alloys_data`;
     let response = await this.http.post<any>(url,data).toPromise();
     return response;
   } catch (error) {
     if (error instanceof HttpErrorResponse) {
       this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
       throw error;
     }
   }
   return undefined;
 }

 async saveUsecaseData(data:any){
    try {
     let url = `${this.configService.getAppApiURL}/sam/save_scenarios`;
     let response = await this.http.post<any>(url,data).toPromise();
     return response;
   } catch (error) {
     if (error instanceof HttpErrorResponse) {
       this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
       throw error;
     }
   }
   return undefined;
 }

  async runUsecasScenarios(usecaseId:string,userId:string){
    try {
    let url = `${this.configService.getAppApiURL}/sam/usecase/${usecaseId}/run_scenarios?user_id=${userId}`;
    let response = await this.http.post<any>(url,{}).toPromise();
    return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }
  async getDefaultConfigFile(){
    try {
    let url = `${this.configService.getAppApiURL}/sam/get_configfile`;
    let response = await this.http.get<any>(url).toPromise();
    return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }
  readConfigFileData(data: any): Observable<any | null> {
    const url = `${this.configService.getApiUrl}/1/projects/${this.configService.SelectedProjectId}/assets/read_file_content`;
    return this.http
      .post(
        url,
        data,
        { observe: 'response', responseType: 'json' },
      )
      .pipe(
        map((response) => {
          return response.body
        }),
        catchError((error) => {
          return of(null);
        }),
      );
  }

  async generatePlot(data:any){
    try {
     let url = `${this.configService.getAppApiURL}/sam/plot_viz`;
     let response = await this.http.post<any>(url,data).toPromise();
     return response;
   } catch (error) {
     if (error instanceof HttpErrorResponse) {
       this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
       throw error;
     }
   }
   return undefined;
 }

  downloadSamFilesData(data: any): Observable<any> {
    let url: string ='';
    if(data.type=='baseline'){
      url = `${this.configService.getAppApiURL}/assets/dataset/tabular/download/${data.dataset_id}`;
      return this.http.get(url, {
        responseType: 'blob',
      });  
    }else{
      url = `${this.configService.getAppApiURL}/assets/download_file?download_json=false`;
      return this.http.post(url, data.files, {
        responseType: 'blob',
      });
  
    }
  }

  getImageContent(file: any): Observable<any | null> {
    const url = `${this.configService.getApiUrl}/1/projects/${this.configService.SelectedProjectId}/assets/read_file_content`;
    if (!file.name || file.name.trim() === '') {
      file.name = file.path.split('/').pop();
    }
    let reqData = { 'file_path': file.path, 'file_name': file.name }
    return this.http
      .post(
        url,
        reqData,
        { observe: 'response', responseType: 'blob' },
      )
      .pipe(
        map((response) => {
          if (response.body) {
            const objectURL = URL.createObjectURL(response.body);
            return objectURL;
          } else {
            return null;
          }
        }),
        catchError((error) => {
          return of(null);
        }),
      );
  }
  
  async deleteSamData(data: any){
    try {
      let path = this.configService.getAppApiURL?.replace(data.project_id,data.document_project);
      let url = `${path}/sam/type/${data.type}/id/${data.id}`;
      let response = await this.http.delete<any>(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }


  getJSONContent(file: any): Observable<any | null> {
    const url = `${this.configService.getApiUrl}/1/projects/${this.configService.SelectedProjectId}/assets/read_file_content`;
    if (!file.name || file.name.trim() === '') {
      file.name = file.path.split('/').pop();
    }
    let reqData = { 'file_path': file.path, 'file_name': file.name }
    return this.http
      .post(
        url,
        reqData,
        { observe: 'response'},
      )
      .pipe(
        map((response) => {
          if (response.body) {
            return response.body;
          } else {
            return null;
          }
        }),
        catchError((error) => {
          return of(null);
        }),
      );
  }

  async getFormatLimitsData(path:string){
    try {
     let url = `${this.configService.getAppApiURL}/sam/get_limits?file_path=${path}`;
     let response = await this.http.get<any>(url).toPromise();
     return response;
   } catch (error) {
     if (error instanceof HttpErrorResponse) {
       this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
       throw error;
     }
   }
   return undefined;
 }
 async baselinePlot(baselineId:string){
  try {
   let url = `${this.configService.getAppApiURL}/sam/plot/baselines/{baselineId}"`;
   let response = await this.http.get<any>(url).toPromise();
   return response;
 } catch (error) {
   if (error instanceof HttpErrorResponse) {
     this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
     throw error;
   }
 }
 return undefined;
}


}
