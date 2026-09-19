import { Injectable } from '@angular/core';
import { HttpClient,HttpHeaders } from '@angular/common/http';
import { ConfigService } from '../../../services/config.service';
import { User } from '../../../models/user-models';
import { Observable, of } from 'rxjs';

interface UserGetResponse {
  users: [];
}

interface UserDeletePostResponse {
  message: any ;
}
interface UserUpdatePostResponse {
  user_id: string | undefined;
}


@Injectable({
  providedIn: 'root',
})
export class AdminUsersService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) {}
  getAccessToken(){
    var currentUser =  JSON.parse(localStorage.getItem('currentUser')!);
    let access_token = currentUser.access_token;
    return access_token
  }  

  async GetUsers( siteId: string, searchTerms: string | undefined ) {
    let url: string = `${this.configService.getAuthApiUrl}/getUsersWithRoles/`;
    const headers = new HttpHeaders()
    headers.set('Content-Type', 'application/json');
    if (searchTerms) {
      url += '?search_term=' + searchTerms;
    }
    let response = await this.http.get<UserGetResponse>(url).toPromise();
    return response;
  }
  async GetUserRoles() {
    let url: string = `${this.configService.getSiteManagementApiUrl}/getRolesList/`;
    const headers = new HttpHeaders()
    headers.set('Content-Type', 'application/json');
    let response = await this.http.get<any>(url,{ headers }).toPromise();
    return response;
  }
  async GetUserSites() {
    let url: string = `${this.configService.getSiteManagementApiUrl}/getSitesList/`;
    const headers = new HttpHeaders()
    headers.set('Content-Type', 'application/json');
    let response = await this.http.get<any>(url,{ headers }).toPromise();
    return response;
  }
  async DeleteUser(userEmail:string) {
    let url: string = `${this.configService.getAuthApiUrl}/deleteUser?email=`+userEmail;
    const headers = new HttpHeaders();
    headers.set('Content-Type', 'application/json');
    let response = await this.http.delete<any>(url,{headers}).toPromise();
    return response;
  }
  UpdateUserRole(siteId: string, userId: string,userRole: string) {
    let url: string = `${this.configService.getApiUrl}/${siteId}/users/${userId}`;
    return this.http.get<any>(url);

  }
}
