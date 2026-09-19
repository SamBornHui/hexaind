import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { BehaviorSubject, Observable } from 'rxjs';
import { AssetsListResponse } from 'src/app/models/data-models';

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

  async GetDatasets(searchTerms: string | undefined): Promise<AssetsListResponse>  {
    let url: string = `${this.configService.getAppApiURL}/assets/datasets`;
    if (searchTerms) {
      url += '?search_term=' + searchTerms;
    }

    let response = await this.http.get<AssetsListResponse>(url).toPromise();
    if (response) {
      return response;
    }

    return new AssetsListResponse([], 0);
  }

  DeleteDataset(payload: any) {
    let url: string = `${this.configService.getAppApiURL}/assets/datasets/delete`;
    return this.http.delete(url, { body: payload });
  }
}


