import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CommonApiService {

  constructor(private http: HttpClient) {}

  get_api<T>(url: string): Observable<any> {
    return this.http.get<T>(url);
  }

  post_api<T>(url: string, body: any): Observable<any> {
    return this.http.post<T>(url, body);
  }

  delete_api<T>(url: string): Observable<any> {
    return this.http.delete<T>(url);
  }

  put_api<T>(url: string, body: any): Observable<any> {
    return this.http.put<T>(url, body);
  }

  patch_api<T>(url: string, body: any): Observable<any> {
    return this.http.patch<T>(url, body);
  }
}
