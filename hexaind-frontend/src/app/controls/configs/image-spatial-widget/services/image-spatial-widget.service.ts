import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { CommonApiService } from 'src/app/services/common-api-service/common-api.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { Utils } from 'src/app/utils';

import { Observable, throwError } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ImageSpatialWidgetService {
  constructor(
    private configService: ConfigService, 
    public http: HttpClient, 
    private commonApiService:   CommonApiService,
    private sharedDataService:SharedDataService
  ) { }

  getSegmentedImages(siteId: string, projectId: any, datasetId:string): Observable<any> {
    try {
      let url  = `${this.configService.getImageAnalysisUrl()}/dataset/${datasetId}/retrieve_fe_data`
      return this.commonApiService.get_api(url);
    } catch (error: any) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error('Error fetching tech nodes:', error);
        return throwError(error);
    }    
  }

  getImageSize(siteId: string, projectId: any, path:string): Observable<any> {
    try {
      let url  = `${this.configService.getImageAnalysisUrl()}/get_image_size`
      return this.commonApiService.post_api(url,{path:path});
    } catch (error: any) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error('Error fetching tech nodes:', error);
        return throwError(error);
    }    
  }

  quanticationTechnique(siteId: string, projectId: any, datasetId:string,data:object): Observable<any> {
    try {
      let url  = `${this.configService.getImageAnalysisUrl()}/dataset/${datasetId}/quantification_techniques`
      return this.commonApiService.post_api(url,data);
    } catch (error: any) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error('Error fetching tech nodes:', error);
        return throwError(error);
    }    
  }



}
