import { Injectable } from '@angular/core';
import { ConfigService } from '../services/config.service';
import { Observable } from 'rxjs';
import { CommonApiService } from '../services/common-api-service/common-api.service';

@Injectable({
  providedIn: 'root'
})
export class CodeMirrorEditorService {

  constructor(private configService: ConfigService, private commonApiService: CommonApiService) { }

  getFileContent(siteId: string, projectId: string, file: any): Observable<any> {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/assets/read_file_content/`;
    return this.commonApiService.post_api(url, file);
  }
}
