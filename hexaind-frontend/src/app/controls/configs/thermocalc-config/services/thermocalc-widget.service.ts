import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { LoggerService } from 'src/app/services/logger.service';
import {Observable} from "rxjs"

@Injectable({
  providedIn: 'root'
})
export class ThermoCalcWidgetService {
  constructor(
    private configService: ConfigService, 
    public http: HttpClient, 
    private loggerService:   LoggerService,
  ) { }
  authenticate(siteId: string, projectId: string, authObj: any) {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/thermocalc_authentication/`;
    return this.http.post(url, authObj);
  }
  getInputOutputSchemaByType(
    widget_type: any,
  ): Observable<any> {
    const baseUrl = this.configService.getApiUrl+'/v1';
    const url = `${baseUrl}/widget/${widget_type}/schema`;
    return this.http.get(url, {});
  }
  uploadRescaleFilesToPlatform(data:any): Observable<any> {
    const formData = new FormData();
    data.files.forEach((file:any) => formData.append('files', file, file.name));
    formData.append('folder_name', data.folder_name);
    formData.append('connectorId', data.connectorId);
    formData.append('workflowId', data.workflowId);
    formData.append('post_python', 'thermocalc');
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${data.siteId}/projects/${data.projectId}/assets/multiple_file_uploads`;
    return this.http.post(url, formData);
  }
  getFeatures(siteId:string,projectId:string,moduleId:string): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/thermocalc/getFeatures?module_id=${moduleId}`;
    return this.http.post(url, {});
  }
  readJsonFile(file: File): Promise<any> {
    return new Promise((resolve, reject) => {
      const fileReader = new FileReader();
      fileReader.onload = () => {
        try {
          const result = JSON.parse(fileReader.result as string);
          resolve(result);
        } catch (e) {
          reject(e);
        }
      };

      fileReader.onerror = (error) => {
        reject(error);
      };

      fileReader.readAsText(file);
    });
  }

  getModuleInfo(data: any): Observable<any> {
    const baseUrl = this.configService.getApiUrl+'/v1';
    const url = `${this.configService.getApiUrl}/${data.siteId}/projects/${data.projectId}/assets/modules/${data.moduleId}`;
    return this.http.get(url);
  }

  
}