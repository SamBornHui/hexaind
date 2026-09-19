import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { interval, Observable, throwError } from 'rxjs';
import { switchMap, catchError, map, takeWhile } from 'rxjs/operators';
import { ConfigService } from './config.service';

@Injectable({
  providedIn: 'root'
})
export class ApiPollingService {
  //private apiUrl = `${this.configService.getApiUrl}/projects/${project_id}/jupyter/hub/server`;
  private pollingInterval = 5000; // 5 seconds

  constructor(private http: HttpClient,private configService: ConfigService,) {}

  pollApi(project_id: any): Observable<any> { 
    let apiUrl: string = `${this.configService.getApiUrl}/projects/${project_id}/jupyter/hub/server`;
    return interval(this.pollingInterval).pipe(
      switchMap(() => this.http.get<any>(apiUrl)),
      map(response => { 
        if (response.status === 'RUNNING') {
         return response;
        }      
       }),
      catchError(error => {
        if (error.message === 'Polling complete') {
          return throwError(error);
        } else {
          console.error('Polling error:', error);
          return throwError(error);
        }
      }),
      takeWhile(response => response.status !== 'running', true)
    );
  }
}
