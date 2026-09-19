import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ConfigService } from 'src/app/services/config.service';
import { LoggerService } from 'src/app/services/logger.service';
import {Observable} from "rxjs"

@Injectable({
  providedIn: 'root'
})
export class PredictionWidgetService {
  constructor(
    private configService: ConfigService, 
    public http: HttpClient, 
    private loggerService:   LoggerService,
  ) { }

  getModeleInfo(data: any): Observable<any> {
    let url: string = `${this.configService.getMBAppApiURL}/${data.siteId}/projects/${data.projectId}/model/${data.modelId}`;
    return this.http.get(url);
  }
  
}