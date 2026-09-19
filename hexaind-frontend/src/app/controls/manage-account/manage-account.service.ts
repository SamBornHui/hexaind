import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ConfigService } from '../../services/config.service';
import { Observable, of } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ManageAccountService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) {}

  private getAccessToken(): string {
    let user: any = localStorage.getItem('currentUser');
    user = JSON.parse(user);
    return user ? user.access_token : '';
  }

  changePassword(data: any): Observable<any> {
    const token = this.getAccessToken();
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    });
    let url: string = `${this.configService.getAuthUrl}/changePassword`;
    return this.http.post(url, data, { headers: headers, observe: 'response' });
  }
  updateUserName(data: any): Observable<any> {
    const token = this.getAccessToken();
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    });
    let url: string = `${this.configService.getAuthUrl}/updateUserNames`;
    return this.http.post(url, data, { headers: headers, observe: 'response' });
  }
}
