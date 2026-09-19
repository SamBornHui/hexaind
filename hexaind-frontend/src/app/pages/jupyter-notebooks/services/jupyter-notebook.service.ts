import { Injectable } from '@angular/core';
import { ConfigService } from '../../workflow-designer/workflow-canvas.service';
import { HttpErrorResponse } from '@angular/common/http';
import { Utils } from 'src/app/utils';
import { CommonApiService } from 'src/app/services/common-api-service/common-api.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';

@Injectable({
  providedIn: 'root'
})
export class JupyterNotebookService {

  constructor(
    public configService: ConfigService,
    private commonApiService: CommonApiService,
    private sharedDataService: SharedDataService,
  ) { }

 async createJupyterNotebook(source: string, destination: string, project_id: string) {
      try {
        const jsonData = {
          source: source,
          destination: destination,
        };
        let url: string = `${this.configService.getApiUrl}/projects/${project_id}/jupyter/hub/server/jnb_copy_folder`;
        let response = await this.commonApiService
          .post_api<any>(url, jsonData)
          .toPromise();
        return response;
      } catch (error) {
        if (error instanceof HttpErrorResponse) {
          this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        }
      }
      return [];
    }

 async createNewJupyterNotebook(name: string, description: string, project_id: string) {
      try {
        const jsonData = {
          name: name,
          description: description,
        };
        let url: string = `${this.configService.getApiUrl}/projects/${project_id}/jupyter/hub/server/create_notebook`;
        let response = await this.commonApiService
          .post_api<any>(url, jsonData)
          .toPromise();
        return response;
      } catch (error) {
        if (error instanceof HttpErrorResponse) {
          this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        }
      }
      return [];
    }
}
