import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse,HttpHeaders } from '@angular/common/http';
import { User } from '../../models/user-models';
import { ConfigService } from '../../services/config.service';
import { Observable } from 'rxjs';


interface UserPostResponse {
  user: any;
}

@Injectable({
  providedIn: 'root',
})
export class NewUserService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) {}
  getAccessToken(){
    var currentUser =  JSON.parse(localStorage.getItem('currentUser')!);
    let access_token = currentUser.access_token;
    return access_token
  }  
  CreateMultipleUsers(data: any): Observable<any> {
    const token = this.getAccessToken();
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    let url: string = `${this.configService.getAuthApiUrl}/createMultipleUsers/`;
    return this.http.post(url, data, { headers: headers, observe: 'response' });
  }
  UpdateUser(siteId: string, user: any) {
    let url: string = `${this.configService.getApiUrl}/${siteId}/users`;
    // return this.http.post<UserPostResponse>(url, user);
  }
}
