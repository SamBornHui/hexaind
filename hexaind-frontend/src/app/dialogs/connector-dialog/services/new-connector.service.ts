import { query } from '@angular/animations';
import { HttpClient,HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Connector, CreateConnectorResponse } from 'src/app/models/connector-models';
import { ConfigService } from 'src/app/services/config.service';
import { environment } from 'src/environments/environment';
@Injectable({
  providedIn: 'root',
})
export class NewConnectorService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService
  ) { }

  async CreateConnector(siteId: string, projectId: string, connector: Connector): Promise<string | null> {
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/projects/${projectId}/connector/`;
    return new Promise((resolve, reject) => {
      this.http.post<CreateConnectorResponse>(url, connector).subscribe(
        createConnectorResponse => {
          let connectorId = createConnectorResponse.connector_id;
          if (connectorId !== undefined) {
            resolve(connectorId);
          } else {
            resolve(null);
          }
        },
        error => {
          console.error('Error:', error);
          reject(null);
        }
      );
    });
  }
  
  authenticateConnector(siteId: string, projectId: string, data: any) {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/bigquery/authenticate`;
    return this.http.post(url, data);
  }

  SnowflakeauthenticateConnector(siteId: string, projectId: string, data: any) {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/data/snowflake/authenticate`;
    return this.http.post(url, data);
  }

  async getTableData(parentName: string, childName:string,siteId: string, projectId: string, connectorId: any) {
    let data = {
      "dataset_name": parentName,
      "table_name": childName
    }
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/bigquery/preview?connector_id=${connectorId}`;
    let result = await this.http.post(url, data).toPromise();
    return result;
  }

  async getQueryPreviewData(textBoxQuery: string,siteId: string, projectId: string, connectorId: any, query_params: any) {
    let data = {
      "query_config":{
        "query": textBoxQuery,
        "query_params": query_params
      }
    }
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/bigquery/preview?connector_id=${connectorId}`;
    let result = await this.http.post(url, data).toPromise();
    return result;
  }

  async createQuery(query_params : any, textBoxQuery: string,queryName:string,siteId: string, projectId: string, connectorId: any){
    let data: any = {
      "query": textBoxQuery,
      "name": queryName,
      "connector_id": connectorId,
      "query_params" : query_params
    }
    // if (query_params !== '') {
    //   data["query_params"] = query_params;
    // }
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/bigquery/query`;
    let result = await this.http.post(url, data).toPromise();
    return result;
  }

  async deleteQuery(querId: any,siteId: string, projectId: string){
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/bigquery/query/${querId}`;
    let result = await this.http.delete(url).toPromise();
    return result;
  }

  async createTableQuery(childName: string,parentName: string, queryName:string,siteId: string, projectId: string, connectorId: any){
    let data = {
      "dataset_name": parentName,
      "table_name": childName,
      "name": queryName,
      "connector_id": connectorId
    }

    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/bigquery/query`;
    let result = await this.http.post(url, data).toPromise();
    return result;
  }

  ///1/projects/663e46bcd6a0bf997355f943/query/?search_term=test&page_number=1&page_limit=10

  async getallqueries(siteId: string, projectId: string, connectorId: any) {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/bigquery/query?page_limit=100`;
    console.log("Url is : ", url)
    let result = await this.http.get(url).toPromise();
    return result;
  }

  rescaleAuthenticate(siteId: string, projectId: string, token: any) {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/rescale_authentication/`;
    return this.http.post(url, token);
  }

  thermoCalcAuthenticate(siteId: string, projectId: string, token: any) {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/thermocalc_authentication/`;
    return this.http.post(url, token);
  }
}
