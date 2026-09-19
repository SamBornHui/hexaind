import { Injectable } from '@angular/core';
import {
  HttpEvent,
  HttpInterceptor,
  HttpHandler,
  HttpRequest,
  HttpErrorResponse,
} from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, filter, take, switchMap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { TokenService } from './token.service';

@Injectable()
export class TokenInterceptor implements HttpInterceptor {
  private refreshTokenInProgress = false;
  private refreshTokenSubject: BehaviorSubject<any> = new BehaviorSubject<any>(
    null,
  );

  constructor(
    private router: Router,
    private tokenService: TokenService,
  ) {}

  private getAccessToken(): string {
    const currentUser = localStorage.getItem('currentUser');
    return currentUser ? JSON.parse(currentUser).access_token : '';
  }

  intercept(
    request: HttpRequest<any>,
    next: HttpHandler,
  ): Observable<HttpEvent<any>> {
    if (
      request.url.includes('/v1/authentication/login') ||
      request.url.includes('/v1/authentication/azureLogin') ||
      request.url.includes('/v1/authentication/gcpLogin')
    ) {
      return next.handle(request);
    }

    const accessToken = this.getAccessToken();
    if (accessToken && !this.tokenService.isTokenExpired(accessToken)) {
      request = this.addTokenToRequest(request, accessToken);
    }

    return next.handle(request).pipe(
      catchError((error: HttpErrorResponse) => {
        if (
          (error.status === 401 || error.status === 403) &&
          !this.tokenService.isTokenExpired(accessToken)
        ) {
          this.refreshTokenInProgress = false;
          this.router.navigate(['/login']);
          return throwError(error);
        }

        if (error.status === 401 || error.status === 403) {
          if (this.refreshTokenInProgress) {
            return this.refreshTokenSubject.pipe(
              filter((token) => token != null),
              take(1),
              switchMap((token) =>
                next.handle(this.addTokenToRequest(request, token)),
              ),
            );
          } else {
            this.refreshTokenInProgress = true;
            this.router.navigate(['/login']);
            this.refreshTokenSubject.next(null);
            const currentUser = JSON.parse(
              localStorage.getItem('currentUser') || '{}',
            );

            return this.tokenService.refreshToken(currentUser).pipe(
              switchMap((token: any) => {
                this.refreshTokenInProgress = false;
                currentUser['access_token'] = token.access_token;
                currentUser['refresh_token'] = token.refresh_token;
                localStorage.setItem(
                  'currentUser',
                  JSON.stringify(currentUser),
                );
                this.refreshTokenSubject.next(token.access_token);
                return next.handle(
                  this.addTokenToRequest(request, token.access_token),
                );
              }),
              catchError((err) => {
                this.refreshTokenInProgress = false;
                this.router.navigate(['/login']);
                return throwError(err);
              }),
            );
          }
        } else {
          return throwError(error);
        }
      }),
    );
  }

  private addTokenToRequest(
    request: HttpRequest<any>,
    token: string,
  ): HttpRequest<any> {
    return request.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
}
