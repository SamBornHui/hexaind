import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { BehaviorSubject, lastValueFrom, Observable } from 'rxjs';
import { AssetsListResponse } from 'src/app/models/data-models';

interface RenameResponse {
  status: boolean;
  new_name: string;
  message: string;
}
@Injectable({
  providedIn: 'root',
})
export class DataService {
  private assetTypeSource = new BehaviorSubject<string>('');
  currentAssetType = this.assetTypeSource.asObservable();

  changeAssetType(assetType: string) {
    this.assetTypeSource.next(assetType);
  }

  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) {}

  async GetDatasets(
    searchTerms: string | undefined,
  ): Promise<AssetsListResponse> {
    let url: string = `${this.configService.getAppApiURL}/assets/datasets?page_limit=0&page_number=0`;
    if (searchTerms) {
      if (searchTerms === 'hexaind_csv') {
        url += '&file_ext=csv';
      } else if (searchTerms === 'hexaind_parquet') {
        url += '&file_ext=parquet';
      } else if (searchTerms === 'hexaind_excel') {
        url += '&file_ext=xlsx';
      } else if (searchTerms === 'hexaind_text') {
        url += '&file_ext=text';
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

  async GetDatasetsforXls(
    searchTerms: string | undefined,
  ): Promise<AssetsListResponse> {
    let url: string = `${this.configService.getAppApiURL}/assets/datasets?page_limit=0&page_number=0`;
    if (searchTerms) {
      if (searchTerms === 'xls') {
        url += '&file_ext=xls';
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

  async GetDatasetsforTex(
    searchTerms: string | undefined,
  ): Promise<AssetsListResponse> {
    let url: string = `${this.configService.getAppApiURL}/assets/datasets?page_limit=0&page_number=0`;
    if (searchTerms) {
      if (searchTerms === 'tex') {
        url += '&file_ext=tex';
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

  getDataset(datasetId: any) {
    let url: string = `${this.configService.getAppApiURL}/assets/dataset/${datasetId}`;
    return lastValueFrom(this.http.get(url));
  }

  DeleteDataset(payload: any) {
    let url: string = `${this.configService.getAppApiURL}/assets/datasets/delete`;
    return this.http.delete(url, { body: payload });
  }

  renameDataset(payload: any): Observable<RenameResponse> {
    let url: string = `${this.configService.getAppApiURL}/assets/dataset/rename/${payload['dataset_id']}`;
    return this.http.post<RenameResponse>(url, payload);
  }
}
