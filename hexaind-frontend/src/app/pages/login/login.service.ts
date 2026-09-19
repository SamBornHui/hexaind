import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ConfigService } from '../../services/config.service';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable({ providedIn: 'root' })
export class UserLoginService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) {}

  private loginMethodSubject = new BehaviorSubject<any>(null);
  loginMethod$ = this.loginMethodSubject.asObservable();

  setLoginMethod(loginMethod: any) {
    this.loginMethodSubject.next(loginMethod);
  }

  getLoginMethod() {
    return this.loginMethodSubject.getValue();
  }

  userLogin(user: any): Observable<any> {
    let url: string = `${this.configService.getAuthUrl}/login`;
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    return this.http.post(url, user, { headers: headers, observe: 'response' });
  }

  userLogout(user: any): Observable<any> {
    let url: string = `${this.configService.getAuthUrl}/logout?email=${user}`;
    const headers = new HttpHeaders();
    headers.append('Content-Type', 'application/json');
    return this.http.post(url, user);
  }

  resetPasswordByUser(email:string,reason:string): Observable<any> {
    let url: string =`${environment.apiUrl}/v1/authentication/reset_password_by_user?email=${email}&reason=${reason}`;
    return this.http.post(url,{email, reason});
  }

  SSOLogin(JsonData:object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/sso_login`;
    return this.http.post<any>(url,JsonData);
  }

  loginMethod(): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/get_login_methods_of_plotform`;
    return this.http.get<any>(url);
  }

  getUsersList(email:string): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/isUserAlreadyRegistered?email=${email}`;
    return this.http.get<any>(url);
  }
}
