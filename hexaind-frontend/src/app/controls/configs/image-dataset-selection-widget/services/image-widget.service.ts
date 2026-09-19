import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { LoggerService } from 'src/app/services/logger.service';
import { CommonApiService } from 'src/app/services/common-api-service/common-api.service';
import {Observable} from "rxjs"

@Injectable({
  providedIn: 'root'
})
export class ImageWidgetService {
  constructor(
    private configService: ConfigService, 
    public http: HttpClient, 
    private commonApiService:   CommonApiService,
  ) { }
  
  uploadtoRescale(siteId: any, projectId: any, connectorId:any, jsonData: any): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/upload_to_rescale?connector_id=${connectorId}`;
    return this.commonApiService.post_api(url, jsonData);
  }

  uploadMetaDataFiles(data:any): Observable<any> {
    const formData = new FormData();
    // data.files.forEach((file:any) => formData.append('files', file, file.name));

    data.files.forEach((file:any, index:number) => {
      formData.append('files', file, file.name); // Append file
      // formData.append(`files[${index}][dataset_id]`, file.dataset_id);
      // formData.append(`files[${index}][dataset_location]`, file.dataset_location);

      // formData.append(`metadata[${index}][dataset_id]`, file.dataset_id);
      // formData.append(`metadata[${index}][dataset_location]`, file.dataset_location);
    });
    const metadata = data.files.map((file: any) => ({
      dataset_id: file.dataset_id,
      dataset_location: file.dataset_location,
    }));
    formData.append('metadata', JSON.stringify(metadata));
  
    const baseUrl = this.configService.getApiUrl;
    let url = `${this.configService.getImageDatasetUrl()}/sites/${data.siteId}/projects/${data.projectId}/datasets/upload_defect_images_metadata`;
    // "/sites/{siteId}/projects/{projectId}/datasets/{dataset_id}/upload_defect_images_metadata
    // const url = `${baseUrl}/${data.siteId}/projects/${data.projectId}/upload_defect_images_metadata`;
    return this.http.post(url, formData);
  }

}
