import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConnectorListResponse } from 'src/app/models/connector-models';
import { ConfigService } from 'src/app/services/config.service';

@Injectable({
  providedIn: 'root',
})
export class ConnectorsService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) {}

  GetConnectors() {
    let url: string = `${this.configService.getAppApiURL}/connectors`;
    return this.http.get<ConnectorListResponse>(url);
  }

  ConnectorsUpdate(connector: any){
    let url: string = `${this.configService.getApiUrl}/${connector['site_id']}/projects/${connector['project_id']}/connector/${connector['_id']}`;
    return this.http.post(url, connector);
  }

  DeleteDataset(connector: any){
    let url: string = `${this.configService.getApiUrl}/${connector['site_id']}/projects/${connector['project_id']}/connectors/${connector['_id']}`;
    return this.http.delete(url);
  }
}
