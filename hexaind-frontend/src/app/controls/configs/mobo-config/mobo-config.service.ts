import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ConfigService } from 'src/app/services/config.service';
import { environment } from '../../../../environments/environment';
import { CommonApiService } from 'src/app/services/common-api-service/common-api.service';

@Injectable({
  providedIn: 'root',
})
export class MoboConfigService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
    private commonApiService: CommonApiService,
  ) { }

  getAllModules(
    site_id: any,
    project_id: any,
    page_limit: any,
    page_number: any,
  ): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${site_id}/projects/${project_id}/assets/modules?page_limit=${page_limit}&page_number=${page_number}`;
    return this.commonApiService.get_api(url);
  }

  getDataset(
    site_id: string,
    project_id: string,
    dataset_id: string,
  ): Observable<any> {
    const baseUrl = this.configService.getAuxApiUrl;
    const url = `${baseUrl}/${site_id}/projects/${project_id}/eda/statistics?dataset_id=${dataset_id}`;
    return this.commonApiService.get_api(url);
  }

  getInputOutputSchemaByType(
    widget_type: any,
  ): Observable<any> {
    const baseUrl = `${environment.apiUrl}/v1`;
    const url = `${baseUrl}/widget/${widget_type}/schema`;
    return this.commonApiService.get_api(url);
  }

  async getDatasetResults(site_id: string, project_id: string, session_id: string, widgetURN: string): Promise<any[]> {
    try {
      const baseUrl = this.configService.getApiUrl; // Assuming getApiUrl is a method
      const url = `${baseUrl}/${site_id}/projects/${project_id}/sessions/${session_id}/workflow/run/widget/${widgetURN}/results`;
      return await this.http.get<any>(url).toPromise();
    } catch (error) {
      console.log("Error fetching dataset results: ", error);
      throw new Error("Error fetching dataset results: " + error);
    }
  }
}
