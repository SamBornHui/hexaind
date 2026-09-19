import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ConfigService } from 'src/app/services/config.service';
import { Observable } from 'rxjs'

@Injectable({
  providedIn: 'root',
})
export class PlatformFilesDialogService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) { }
  getUploadedFiles(
    siteId: string,
    projectId: string,
    connectorId: any
  ): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/assets/rescale_information?connector_id=${connectorId}`;
    return this.http.get(url, {});
  }
  
  uploadtoRescale(siteId: any, projectId: any, connectorId:any, jsonData: any): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/upload_to_rescale?connector_id=${connectorId}`;
    return this.http.post(url, jsonData);
  }


}
