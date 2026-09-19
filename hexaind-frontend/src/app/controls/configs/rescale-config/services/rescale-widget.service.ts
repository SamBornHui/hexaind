import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { LoggerService } from 'src/app/services/logger.service';
import { CommonApiService } from 'src/app/services/common-api-service/common-api.service';
import {Observable} from "rxjs"

@Injectable({
  providedIn: 'root'
})
export class RescaleWidgetService {
  constructor(
    private configService: ConfigService, 
    public http: HttpClient, 
    private commonApiService:   CommonApiService,
  ) { }
  authenticate(siteId: string, projectId: string, token: any) {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/rescale_authentication/`;
    return this.commonApiService.post_api(url, token);
  }
  createFolderPath(siteId: any, projectId: any, workflowId: any, connection: any): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/workflow/${workflowId}/createfolder?folder_name=${connection}`;
    return this.commonApiService.post_api(url, {});
  }

  
  uploadtoRescale(siteId: any, projectId: any, connectorId:any, jsonData: any): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/upload_to_rescale?connector_id=${connectorId}`;
    return this.commonApiService.post_api(url, jsonData);
  }
  getUploadedFiles(
    siteId: string,
    projectId: string,
    connectorId: any
  ): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/assets/rescale_information?connector_id=${connectorId}`;
    return this.http.get(url, {});
  }

  uploadRescaleFilesToPlatform(data:any): Observable<any> {
    const formData = new FormData();
    data.files.forEach((file:any) => formData.append('files', file, file.name));
    formData.append('folder_name', data.folder_name);
    formData.append('connectorId', data.connectorId);
    formData.append('workflowId', data.workflowId);
    formData.append('post_python', data.post_python);
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${data.siteId}/projects/${data.projectId}/assets/multiple_file_uploads`;
    return this.http.post(url, formData);
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
  getFileContent(
    siteId: string,
    projectId: string,
    file: any
  ): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/assets/read_file_content/`;
    return this.commonApiService.post_api(url, {file_path:file.file_path,file_name:file.file_name});
  }


}
