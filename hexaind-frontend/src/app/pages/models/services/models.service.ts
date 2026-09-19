import { Injectable } from '@angular/core';
import { ConfigService } from '../../workflow-designer/workflow-canvas.service';
import { CommonApiService } from 'src/app/services/common-api-service/common-api.service';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { DirectoryItem, Utils } from '../../../utils';
import { BehaviorSubject, forkJoin, Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';


@Injectable({
  providedIn: 'root',
})
export class ModelsService {
  private imageCache: { [key: string]: string } = {};

  constructor(
    private configService: ConfigService,
    private commonApiService: CommonApiService,
    private sharedDataService: SharedDataService,
    private http: HttpClient,
    private sanitizer: DomSanitizer,
  ) { }

  private updatedRowsSubject = new BehaviorSubject<any>(null);
  updatedRows$ = this.updatedRowsSubject.asObservable();

  updateRows(data: any) {
    this.updatedRowsSubject.next(data);
  }

  getJsonData() {
    return [
      {
        file: 'assets/model_blue.png',
        name: 'Model GPR',
        type: 'GPR',
        size: '22 KB',
        uploader: 'Arvind',
        last_modified: '12/12/24 02:00 PM',
      },
      {
        file: 'assets/model_blue.png',
        name: 'Model RF',
        type: 'RF',
        size: '22 KB',
        uploader: 'Arvind',
        last_modified: '12/12/24 02:00 PM',
      },
    ];
  }

  async getModelResults(siteId: any, projectId: any, runId: any): Promise<any> {
    let url: string = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/run/${runId}/models/preview_models`;
    let models: any = await this.commonApiService.get_api(url).toPromise();
    return models;
  }

  async getAllModels(siteId: any, projectId: any): Promise<any> {
    let url: string = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/models?siteId=1&page_limit=10000&page_number=1`;
    let models: any = await this.commonApiService.get_api(url).toPromise();
    return models;
  }

  async saveModel(
    siteId: string,
    projectId: any,
    jsonData: any,
  ): Promise<string | undefined> {
    try {
      const url = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/models/save_models`;
      const response = await this.commonApiService
        .post_api<string>(url, jsonData)
        .toPromise();
      return response;
    } catch (error) {
      console.error('Error while saving the models:', error);
      return undefined;
    }
  }
  
  async deleteModel(
    siteId: string,
    projectId: any,
    modelId: any,
  ): Promise<void> {
    try {
      let url: string = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/model/${modelId}`;
      const response = await this.commonApiService.delete_api(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async createVisualizations(
    siteId: string,
    projectId: string,
    visualizationData: object,
  ): Promise<any> {
    const url = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/models/create_visualizations`;
    try {
      const visualizations = await this.commonApiService
        .post_api<any>(url, visualizationData)
        .toPromise();
      return visualizations;
    } catch (error) {
      console.error('Error creating visualizations:', error);
      throw error;
    }
  }

  async compareModels(
    siteId: string,
    projectId: string,
    modelsConfig: object,
  ): Promise<any> {
    const url = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/models/compare_models`;
    try {
      const comparisonResult = await this.commonApiService
        .post_api<any>(url, modelsConfig)
        .toPromise();
      return comparisonResult;
    } catch (error) {
      console.error('Error comparing models:', error);
      throw error;
    }
  }

  getFileContent(model: any): Observable<any> {
    const url = `${this.configService.getApiUrl}/1/projects/${this.configService.SelectedProjectId}/assets/read_file_content`;
    const featureImpPlot = model.model.feature_imp_plot;
    const featureImpPlotArray = Array.isArray(featureImpPlot) ? featureImpPlot : [featureImpPlot];

    const requests = featureImpPlotArray.map(element => {
      return this.http
        .post(
          url,
          { file_path: element, file_name: model.model.name },
          { observe: 'response', responseType: 'blob' },
        )
        .pipe(
          map((response) => {
            const contentType = response.headers.get('Content-Type');
            if(response.body){
              //if (contentType &&contentType.includes('text/html')) {
              const objectURL = URL.createObjectURL(response.body);
              const sanitizedUrl: SafeResourceUrl = this.sanitizer.bypassSecurityTrustResourceUrl(objectURL);
              return {type: 'html',url:sanitizedUrl};
            } else {
              console.error('Response body is null.');
              return null;
            }
          }),
          catchError((error) => {
            console.error('Error fetching file content:', error);
            return of(null);
          })
        );
    });  
    return forkJoin(requests);
  }

  async interactiveGraphHover(
    siteId: string,
    projectId: string,
    jsonData: object,
  ): Promise<any> {
    const url = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/models/interactiveGraphHover`;
    try {
      const graphData = await this.commonApiService
      .post_api<any>(url, jsonData)
        .toPromise();
      return graphData;
    } catch (error) {
      console.error('Error getting table data:', error);
      throw error;
    }
  }

  getConfusionMetricsFileContent(file: any): Observable<any | null> {
    const url = `${this.configService.getApiUrl}/1/projects/${this.configService.SelectedProjectId}/assets/read_file_content`;
    return this.http
      .post(
        url,
        { file_path: file.path, file_name: file.name },
        { observe: 'response', responseType: 'blob' },
      )
      .pipe(
        map((response) => {
          if (response.body) {
            const objectURL = URL.createObjectURL(response.body);
            return objectURL;
          } else {
            console.error('Response body is null.');
            return null;
          }
        }),
        catchError((error) => {
          console.error('Error fetching file content:', error);
          return of(null);
        }),
      );
  }

  async deployModel(
    siteId: string,
    projectId: string,
    modelId: string,
  ): Promise<any> {
    let url: string = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/models/deployModel`;
    try {
      const models: any = await this.commonApiService
        .post_api<any>(url, { ml_id: modelId })
        .toPromise();
      return models;

    } catch (error) {
      console.error('Error getting table data:', error);
      throw error;
    }
  }
  async offlineModel(
    siteId: string,
    projectId: string,
    modelId: string,
  ): Promise<any> {
    let url: string = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/models/undeployModel`;
    try {
      const models: any = await this.commonApiService
        .post_api<any>(url, { ml_id: modelId })
        .toPromise();
      return models;

    } catch (error) {
      console.error('Error getting table data:', error);
      throw error;
    }
  }

  async getMatchingModels(
    siteId: string,
    projectId: string,
    query: object,
  ): Promise<any> {
    let url: string = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/models/compatibleModel`;

    try {
      const response = await this.commonApiService
        .post_api<string>(url, query)
        .toPromise();
      return response;
      // let models: any = await this.commonApiService.get_api(url).toPromise();
      // return models;
    } catch (error) {
      console.error('Error while saving the models:', error);
      return undefined;
    }
  }

  async deleteAllModels(siteId: any, projectId: any): Promise<any> {
    let url: string = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/delete_models`;
    let models: any = await this.http.delete(url).toPromise();
    return models;
  }

  async updateModel(
    siteId: string,
    projectId: any,
    jsonData: any,
  ): Promise<string | undefined> {
    try {
      const url = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/models/save_and_update_models`;
      const response = await this.commonApiService
        .post_api<string>(url, jsonData)
        .toPromise();
      return response;
    } catch (error) {
      console.error('Error while saving the models:', error);
      return undefined;
    }
  }

  downloadModels(
    siteId:string,
    projectId:any,
    runId: string
  ): Observable<any> {
    const url: string = `${this.configService.getMBAppApiURL}/${siteId}/projects/${projectId}/models/download_models?run_id=${runId}`;
    return this.http.get(url,{responseType: 'blob'});
  }

  CPWFileContent(file: any): Observable<any | null> {
    const url = `${this.configService.getApiUrl}/1/projects/${this.configService.SelectedProjectId}/assets/read_file_content`;
    return this.http
      .post(
        url,
        { file_path: file, file_name: file },
        { observe: 'response', responseType: 'blob' },
      )
      .pipe(
        map((response) => {
          if (response.body) {
            const objectURL = URL.createObjectURL(response.body);
            return objectURL;
          } else {
            console.error('Response body is null.');
            return null;
          }
        }),
        catchError((error) => {
          console.error('Error fetching file content:', error);
          return of(null);
        }),
      );
  }
}
