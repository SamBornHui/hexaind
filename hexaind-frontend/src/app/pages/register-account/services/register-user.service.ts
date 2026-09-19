import { Injectable } from '@angular/core';
import { HttpClient,HttpHeaders } from '@angular/common/http';
import { ConfigService } from '../../../services/config.service';
import { User } from '../../../models/user-models';
import { Observable, of } from 'rxjs';
import { environment } from 'src/environments/environment';

interface UserGetResponse {
  users: [];
}

@Injectable({
  providedIn: 'root',
})
export class RegisterAccountService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
  ) {}

  async registerAccount( userData: any ) {
    let url: string = `${this.configService.getAuthApiUrl}/registerUser`;
    let response = await this.http.post<any>(url,userData).toPromise();
    return response;
  }
  
  activateSSOUser(jsonData:object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/activate_user`;
    return this.http.post<any>(url,jsonData);
  }

  isUserAlreadyRegistered(email:string): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/isUserAlreadyRegistered?email=${email}`;
    return this.http.get<any>(url);
  }
}
