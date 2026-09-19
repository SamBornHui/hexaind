import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { AssetsListResponse } from 'src/app/models/data-models';
import { CommonApiService } from 'src/app/services/common-api-service/common-api.service';

@Injectable({
  providedIn: 'root',
})
export class SaveConfigService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
    private commonApiService: CommonApiService,
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
    let response = await this.commonApiService
      .get_api<AssetsListResponse>(url)
      .toPromise();
    if (response) {
      return response;
    }

    return new AssetsListResponse([], 0);
  }
}
