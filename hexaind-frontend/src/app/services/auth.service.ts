import { Injectable } from '@angular/core';
import * as Msal from 'msal';
import { BehaviorSubject,from, Observable, throwError } from 'rxjs';
import { catchError, filter, map, switchMap, take, tap } from 'rxjs/operators';
import { environment } from 'src/environments/environment';
@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private _isLoggedIn = new BehaviorSubject<boolean>(false);
  isLoggedIn$ = this._isLoggedIn.asObservable();
  configService: any;
  private accessTokenSource = new BehaviorSubject<string | null>(null);
  accessToken$ = this.accessTokenSource.asObservable();
  private msalClient!: Msal.UserAgentApplication;

  constructor() {
    this.initializeAzure_OAuth();
  }

  setLoggedIn(value: boolean) {
    this._isLoggedIn.next(value);
  }

  initializeAzure_OAuth(){
    this.msalClient = new Msal.UserAgentApplication({
      auth: {
        clientId: environment.clientId,
        authority: `https://login.microsoftonline.com/${environment.authority}`,
        redirectUri: environment.redirectUri
      },
      cache: {
        cacheLocation: 'localStorage',
        storeAuthStateInCookie: true,
      },
    });
  }

  azureAuthentication(): Observable<any> {
    return from(this.msalClient.loginPopup({ scopes: ['openid', 'profile',  `${environment.clientId}/.default`] })).pipe(
      switchMap(loginResponse => {
        return from(this.msalClient.acquireTokenSilent({ scopes: ['openid', 'profile',  `${environment.clientId}/.default`] }));
      }),
      catchError(error => {
        if (error.name === "InteractionRequiredAuthError") {
          return from(this.msalClient.acquireTokenPopup({ scopes: ['openid', 'profile',  `${environment.clientId}/.default`] }));
        } else {
          return throwError(error);
        }
      }),
      map(tokenResponse => {
        return tokenResponse;
      }),
      catchError(error => {
        console.error('Token acquisition error', error);
        return throwError(error);
      })
    );
  }
    
}
