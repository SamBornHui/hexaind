import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  CreateNewPassword,
  UserForProjects,
  UserForProjectsResponse,
} from 'src/app/models/user-models';
import { Utils } from 'src/app/utils';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { CreateNewPasswordComponent, CreateNewPasswordResponse } from 'src/app/dialogs/create-new-password/create-new-password.component';
@Injectable({
  providedIn: 'root',
})
export class UsersService {
  constructor(
    private http: HttpClient,
    private sharedDataService: SharedDataService,
  ) {}

  getUsersList(): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/get_users_list`;
    return this.http.get<any>(url);
  }

  getRolesList(): Observable<any> {
    let siteId = 1;
    let data: any[] = [];
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/roles_features_maps/get_all_roles`;
    return this.http.post<any>(url, data);
  }

  getUserListProject(JsonData: object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/get_user_details_based_on_filter`;
    return this.http.post<any>(url, JsonData);
  }

  getUserListByServer(JsonData: object): Observable<any> {
    console.log(JsonData, 'jsonData');
    let url: string = `${environment.apiUrl}/v1/authentication/get_user_details_based_on_filter`;
    return this.http.post<any>(url, JsonData);
  }

  bulkInvite(JsonData: object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/invite_bulk_users`;
    return this.http.post<any>(url, JsonData);
  }

  customInvite(JsonData: object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/invite_users`;
    return this.http.post<any>(url, JsonData);
  }

  createProjectAccess(JsonData: object): Observable<any> {
    let siteId = 1;
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/users_projects_mappings/create_user_project_mappings`;
    return this.http.post<any>(url, JsonData);
  }

  updateProjectAccess(JsonData: object): Observable<any> {
    let siteId = 1;
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/users_projects_mappings/update_user_project_mapping`;
    return this.http.post<any>(url, JsonData);
  }

  createUserAccess(JsonData: object): Observable<any> {
    let siteId = 1;
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/update_server_based_roles_with_mappings`;
    return this.http.post<any>(url, JsonData);
  }

  getProjectData(JsonData: object): Observable<any> {
    let siteId = 1;
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/users_projects_mappings/get_mappings_based_on_project_id`;
    return this.http.post<any>(url, JsonData);
  }

  async getProjectUserData(JsonData: object): Promise<UserForProjects[]> {
    let siteId = 1;
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/get_unmapped_users_for_project`;
    try {
      let response: UserForProjectsResponse | undefined = await this.http
        .post<UserForProjectsResponse>(url, JsonData)
        .toPromise();
      if (response) {
        return response.results;
      }
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetgetProjectUserDataWorGetUserskflows() failed' +
            this.sharedDataService.LastError,
        );
      }
    }
    return [];
  }

  getUserData(jsonData: object): Observable<any> {
    let siteId = 1;
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/users_projects_mappings/get_mappings_based_on_user_id`;
    return this.http.post<any>(url, jsonData);
  }

  inactivateUser(email: string): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/deleteUser?email=${email}`;
    return this.http.delete<any>(url);
  }

  deleteProjectAccess(data: object): Observable<any> {
    let siteId = 1;
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/roles_features_maps/delete_user_project_mapping`;
    return this.http.delete(url, { body: data });
  }

  removeServerAccess(data: object): Observable<any> {
    console.log(data, 'data');
    let siteId = 1;
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/update_server_based_roles_with_mappings`;
    return this.http.post(url, data);
  }

  resendInvitation(email: string): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/resend_invitation_mail?email=${email}`;
    return this.http.post<any>(url, {});
  }

  async createNewPassword(email: string, reason: string): Promise<CreateNewPasswordResponse> {
    const url = `${environment.apiUrl}/v1/authentication/reset_password_by_server_admin?email=${encodeURIComponent(email)}&reason=${encodeURIComponent(reason)}`;
    const jsonData = { email, reason };

    try {
      const response = await this.http.post<CreateNewPasswordResponse>(url, jsonData).toPromise();
      if (response !== undefined) {
        console.log(response, "response rers");
        return response;
      } else {
        throw new Error('Undefined response from server');
      }
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error('Call to API resetPasswordByOrgAdmin() failed: ' + this.sharedDataService.LastError);
      } else {
        console.error('Unexpected error:', error);
      }
      throw error;
    }
  }

  update_user_by_admin(JsonData: object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/update_user_by_admin`;
    return this.http.post<any>(url, JsonData);
  }

  updatePasswordByEmailToken(JsonData: object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/updatePasswordByEmailToken`;
    return this.http.post<any>(url, JsonData);
  }

  getUserProjects(siteId: string, JsonData: object): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/sites/${siteId}/users_projects_mappings/get_mappings_based_on_user_id`;
    return this.http.post<any>(url, JsonData);
  }

  deleteUser(user_id: string): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/delete_user/${user_id}`;
    return this.http.delete<any>(url);
  }

  activateUser(payload: { email: string }): Observable<any> {
    let url: string = `${environment.apiUrl}/v1/authentication/activate_user_by_admin?email=${payload.email}`;
    return this.http.patch<any>(url, null);
  }
}
