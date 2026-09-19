import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { BehaviorSubject, Observable } from 'rxjs';
import { AssetsListResponse } from 'src/app/models/data-models';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { Utils } from 'src/app/utils';

@Injectable({
  providedIn: 'root',
})
export class DataStructureService {
  private assetTypeSource = new BehaviorSubject<string>('');
  currentAssetType = this.assetTypeSource.asObservable();

  changeAssetType(assetType: string) {
    this.assetTypeSource.next(assetType);
  }

  constructor(
    private http: HttpClient,
    private configService: ConfigService,
    private sharedDataService: SharedDataService,
  ) {}

  async GetDatasets(
    searchTerms: string | undefined,
  ): Promise<AssetsListResponse> {
    let url: string = `${this.configService.getAppApiURL}/assets/datasets?page_limit=0&page_number=0`;
    if (searchTerms) {
      if (searchTerms === 'hexaind_csv') {
        url += '&file_ext=csv';
      } else {
        url += '&search_term=' + searchTerms;
      }
    }
    let response = await this.http.get<AssetsListResponse>(url).toPromise();
    if (response) {
      return response;
    }

    return new AssetsListResponse([], 0);
  }

  async createFolder(payload: any) {
    try {
      const url: string = `${this.configService.getAppApiURL}/create_folder`;
      let response = await this.http.post<any>(url, payload).toPromise();

      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }
  async moveDataset(payload: any) {
    try {
      const url: string = `${this.configService.getAppApiURL}/move_assets`;
      let response = await this.http.post<any>(url, payload).toPromise();

      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async renameFolderData(payload: any) {
    try {
      let url: string = `${this.configService.getAppApiURL}/rename_assets`;
      let response = await this.http.post<any>(url, payload).toPromise();

      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }
  async duplicateDataset(payload: any) {
    try {
      let url: string = `${this.configService.getAppApiURL}/create_dataset_duplicate`;
      let response = await this.http.post<any>(url, payload).toPromise();

      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async deleteAsset(payload: any) {
    try {
      let url: string = `${this.configService.getAppApiURL}/delete_asset`;
      let response = await this.http
        .delete<any>(url, { body: payload })
        .toPromise();

      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  downloadDataFile(payload: any): Observable<any> {
    const url: string = `${this.configService.getAppAuxApiURL}/download_asset`;
    return this.http.post(url, payload, {
      responseType: 'blob',
    });
  }

  async getChildrenForImageFolder(payload: any): Promise<any> {
    try {
      const url = `${this.configService.getAppApiURL}/get_childern`;
      const response = await this.http.post<any>(url, payload).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
      return undefined;
    }
  }
}
