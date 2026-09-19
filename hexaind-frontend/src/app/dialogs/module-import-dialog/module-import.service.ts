import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ConfigService } from 'src/app/services/config.service';

@Injectable({
  providedIn: 'root',
})
export class ModuleImportService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) {}

  importModule(queryParams: any, file: any) {
    let query = `name=${queryParams.name}&description=${queryParams.description}&file_type=${queryParams.file_type}`;
    
    if (queryParams.destination_folder && queryParams.destination_folder !== undefined && queryParams.destination_folder != '') {
      query += `&destination_folder=${queryParams.destination_folder}&`;
    }
    let url: string = `${this.configService.getAppApiURL}/assets/module/upload?${query}`;
    return this.http.post(url, file);
  }
}
