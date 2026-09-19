import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { ConfigService } from "src/app/services/config.service";

@Injectable({
  providedIn: "root",
})
export class PostRescaleConfigService {
  constructor(private http: HttpClient, private configService: ConfigService) {}

  getAllPRModules(
    site_id: any,
    project_id: any,
    page_limit: any,
    page_number: any
  ): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${site_id}/projects/${project_id}/assets/modules?page_limit=${page_limit}&page_number=${page_number}`;
    return this.http.get(url, {});
  }

  createFolderPath(
    siteId: any,
    projectId: any,
    workflowId: any,
    folder_path: any
  ): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/workflow/${workflowId}/createfolder?folder_name=${encodeURIComponent(
      folder_path
    )}`;
    return this.http.post(url, {});
  }

  uploadFiles(
    siteId: any,
    projectId: any,
    name: string,
    description: string,
    file: any
  ): Observable<any> {
    const formData = new FormData();
    formData.append("file", file);
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/assets/module/upload?name=${name}&description=${description}`;
    return this.http.post(url, formData);
  }
}
