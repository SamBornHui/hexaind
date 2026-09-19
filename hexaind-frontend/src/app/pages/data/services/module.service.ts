import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { AssetsListResponse } from 'src/app/models/data-models';
import { ModulesListResponse } from 'src/app/models/module-models';
import { ConfigService } from 'src/app/services/config.service';

@Injectable({
  providedIn: 'root',
})
export class ModuleService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) {}

  async GetModules(searchTerms: string | undefined): Promise<ModulesListResponse> {
    let url: string = `${this.configService.getAppApiURL}/assets/modules`;
    if (searchTerms) {
      url += '?search_term=' + searchTerms;
    }

    let response = await this.http.get<ModulesListResponse>(url).toPromise();
    if (response) {
      return response;
    }

    return new ModulesListResponse([], 0);
  }
}
