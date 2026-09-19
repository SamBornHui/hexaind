import { Injectable } from '@angular/core';
import { jwtDecode } from 'jwt-decode';
import { ConfigService } from '../services/config.service';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class TokenService {
  constructor(
    private configService: ConfigService,
    private http: HttpClient,
  ) {}

  decodeToken(token: string): any {
    return jwtDecode(token);
  }

  getTokenExpirationDate(token: string): Date | null {
    const decoded = this.decodeToken(token);

    if (decoded.expires === undefined) return null;

    const date = new Date(0);
    date.setUTCSeconds(decoded.expires);

    return date;
  }

  isTokenExpired(token: string): boolean {
    const expirationDate = this.getTokenExpirationDate(token);

    if (expirationDate === null) return false;

    return expirationDate.valueOf() < new Date().valueOf();
  }

  refreshToken(user: any) {
    let url: string = `${this.configService.getAuthUrl}/getRefreshedTokens`;
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      Authorization: `Bearer ${user.access_token}`,
    });
    let data = {
      email: user.email,
      access_token: user.access_token,
      refresh_token: user.refresh_token,
    };
    return this.http.post(url, data, {
      headers: headers,
      observe: 'response',
    });
  }
}
