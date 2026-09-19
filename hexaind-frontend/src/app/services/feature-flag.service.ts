import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, catchError, Observable, of, tap, timeout } from 'rxjs';
import { ConfigService } from './config.service';

@Injectable({
  providedIn: 'root'
})
export class FeatureFlagService {

  public featureFlags: any;
  private flagSubject = new BehaviorSubject<{[key: string]: boolean}>({})


  constructor(private httpClient: HttpClient, private configService: ConfigService) { 
    this.featureFlags = {}
  }
  loadFeatureFlags() {
    return this.httpClient.get<any>(this.configService.getApiUrl + '/1/feature_flags')
    .pipe(
      timeout(4000),
      tap( (flags: any) => {
        this.featureFlags = flags
        this.flagSubject.next(flags)
      }),
      catchError((error:any) => {
        console.log("Error while loading feature flags", error)
        return of({});
      })
    )
  }

}
