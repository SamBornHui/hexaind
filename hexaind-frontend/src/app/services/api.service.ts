import { Injectable } from '@angular/core';
import { DirectoryItem, Utils } from './../utils';
import {
  BehaviorSubject,
  lastValueFrom,
  Observable,
  Subject,
  throwError,
} from 'rxjs';
import { ConfigService } from './config.service';
import { WebSocketSubject, webSocket } from 'rxjs/webSocket';
import {
  HttpClient,
  HttpErrorResponse,
  HttpHeaders,
  HttpEventType,
  HttpParams,
} from '@angular/common/http';
import { catchError, map } from 'rxjs/operators';
import {
  InputOutputConfig,
  MOBOWidgetConfig,
  Widget,
  WidgetType,
  Workflow,
  WorkflowRun,
} from '../models/workflow-models';
import { Project } from '../models/project-models';
import { User } from '../models/user-models';
import { Notification } from '../models/notification-models';
import { Connector, ConnectorListResponse } from '../models/connector-models';
import {
  Position,
  WidgetClientType,
} from '../pages/workflow-designer/client-tags';
import { Arrow } from '../controls/widget-control/arrow';

import * as APIModels from '../models/api-models';

import { takeUntil } from 'rxjs/operators';
import { DatasetLocation } from '../models/data-models';
import { SharedDataService } from './shared services/shared-data.service';
import { CommonApiService } from './common-api-service/common-api.service';
import {
  VersionedWorkflowRunStatus,
  WorkflowSession,
} from '../models/workflow-sessions-api-response.models';
import { WorkflowCanvasService } from '../pages/workflow-designer/workflow-canvas.service';
import { WorkflowsSessionsApiService } from '../../app/services/workflow-sessions-api.service';
import * as SessionApiModels from '../models/workflow-sessions-api-response.models';
import { quartersToYears } from 'date-fns';
import { BaseRouteReuseStrategy } from '@angular/router';
interface UpdateWorkflowResponse {
  success: boolean;
}

interface GetFilesPostResponse {
  files: any;
  file_names: [];
  file_path: [];
}

interface GetFilesNames {
  file_names: [];
  file_path: [];
}

interface UserGetResponse {
  users: User[];
}

interface ProjectGetResponse {
  projects: Project[];
  total_count: number;
}

interface GetRecipeResponse {
  succeeded: boolean;
  results: Recipe[];
  count: number;
  message: string;
}

interface Recipe {
  displayName: any;
  iconName: any;
  clientType: any;
  type: any;
  version: string;
  _id: string;
  name: string;
  recipe_name: string;
  description: string;
  reference_links: string[];
  tags: string[] | null;
  input_types: string[];
  output_types: string[];
  module_id: string;
  inputs_map: InputMap[];
  outputs_map: OutputMap[];
  project_id: string;
  site_id: string;
  access_mode: string;
  validation_workflow_id: string | null;
  validation_run_id: string | null;
  created_by: string;
  created_at: Date;
  last_modified_by: string;
  last_modified_at: Date;
}

interface GetCustomCodeResponse {
  succeeded: boolean;
  results: Recipe[];
  message: string;
}

interface CustomCode {
  type: WidgetType;
  clientType: WidgetClientType;
  iconName: string;
  displayName: string;
  id: string | null;
  // Remove the 'name' property if it's not relevant for all widgets
}

interface InputMap {
  arg_name: string;
  type: string;
  default_value: string;
  is_mandatory: boolean;
  is_widget_input: boolean;
  mapped_input: any; // Depending on your data structure, this could be of a specific type
}

interface OutputMap {
  key_name: string;
  reference_name: string;
  type: string;
}

interface ProjectPostResponse {
  project_id: string;
}

interface RunWorkflowPostResponse {
  run_id: string;
}

interface RunWorkflowStatusPostResponse {}

interface UploadStats {
  percentage: string;
}

interface GetWorkflowResponse {
  workflow: Workflow;
}

interface NotificationsGetResponse {
  notifications: Notification[];
}

export interface GetWorkflowsRunsResponse {
  runs: WorkflowRun[];
  total_count: number;
}

interface GetProjectResponse {
  project: Project;
}

export interface PostCSVResponse {
  dataset_id: string;
}

export interface InputCount {
  count: number | undefined;
}
interface SchemaGetResponse {
  inputs: InputCount;
}
export interface FileNode {
  name: string;
  full_path: string;
  type: string;
  children?: FileNode[];
}

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private socket$!: WebSocketSubject<any>;
  secondApiResponse: Object | undefined;
  thirdApiResponse: Object | undefined;
  private notificationCountSubject: BehaviorSubject<number> =
    new BehaviorSubject<number>(0);
  public notificationCount$: Observable<number> =
    this.notificationCountSubject.asObservable();
  apiService: any;

  constructor(
    private http: HttpClient,
    private configService: ConfigService,
    private sharedDataService: SharedDataService,
    private commonApiService: CommonApiService,
    public workflowCanvasService: WorkflowCanvasService,
    public WorkflowsSessionsApiService: WorkflowsSessionsApiService,
  ) {}
  private readonly CHUNK_SIZE = 1024 * 1024; // 1 MB per chunk
  private updateNotificationStatusSource = new Subject<void>();
  updateNotificationStatus$ =
    this.updateNotificationStatusSource.asObservable();
  tokenHeaders = this.getAuthHeaders();

  public getAccessToken(): string {
    let user: any = localStorage.getItem('currentUser');
    user = JSON.parse(user);
    return user ? user.access_token : '';
  }

  private getAuthHeaders(): HttpHeaders {
    const token = this.getAccessToken();
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    });
    return headers;
  }

  connect(executionId: string, siteId: string, projectId: string): void {
    const config = {
      url: `${this.configService.getSocketBaseUrl}/custom_python/validation_logs/${executionId}`, // Replace with your WebSocket server URL
      deserializer: (msg: any) => JSON.stringify(msg.data),
      serializer: (msg: any) => JSON.stringify(msg),
    };
    // WebSocket URL with execution ID parameter
    this.socket$ = webSocket(config);
  }

  onMessage() {
    return this.socket$.asObservable();
  }

  async GetMountedDrive(): Promise<any> {
    let result = await this.commonApiService
      .get_api(`${this.configService.getDataApiUrl}/mounted-drive`)
      .toPromise();
    return result;
  }

  async GetProject(
    siteId: string,
    projectId: string,
  ): Promise<Project | undefined> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}`;
    try {
      let response = await this.commonApiService
        .get_api<APIModels.GetProjectResponse>(url)
        .toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async RunVersionedWorkflow(
    siteId: string,
    projectId: string,
    workflowId: string,
  ): Promise<string | undefined> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/${workflowId}/run`;
    try {
      let response = await this.commonApiService
        .post_api<APIModels.RunWorkflowPostResponse>(url, {})
        .toPromise();
      return response.run_id;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async GetVersionedWorkflowRunStatus(
    siteId: string,
    projectId: string,
    workflowId: string,
    runId: string,
  ): Promise<VersionedWorkflowRunStatus | undefined> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/${workflowId}/run/${runId}/status`;
    try {
      let response = await this.http
        .get<VersionedWorkflowRunStatus>(url, {})
        .toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async GetWorkflowRuns(
    siteId: string,
    projectId: string,
    workflowId: string,
  ): Promise<WorkflowRun[]> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflows/${workflowId}/run?page_limit=100&page_number=1`;
    try {
      let response = await this.http
        .get<APIModels.GetWorkflowsRunsResponse>(url)
        .toPromise();
      return response!.runs;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return [];
  }

  async ListDirectoryOnServer(
    path: string,
  ): Promise<DirectoryItem[] | undefined> {
    try {
      const formData: FormData = new FormData();
      formData.append('path', path);
      let result = await this.http
        .post<DirectoryItem[]>(
          `${this.configService.getDataApiUrl}/list-directory`,
          formData,
        )
        .toPromise();
      return result;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async UploadFileChunk(
    chunk: Blob,
    chunkIndex: number,
  ): Promise<Object | undefined> {
    try {
      let formData = new FormData();
      formData.append('file', chunk);
      formData.append('chunk_number', chunkIndex.toString());
      let result = await this.http
        .post(`${this.configService.getDataApiUrl}/upload-chunk`, formData)
        .toPromise();
      return result;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async CompleteFileChunkUpload(
    totalChunks: number,
    fileName: string,
  ): Promise<Object | undefined> {
    try {
      let formData = new FormData();
      formData.append('file_name', fileName);
      formData.append('total_chunks', totalChunks.toString());
      let result = await this.http
        .post(`${this.configService.getDataApiUrl}/complete-upload`, formData)
        .toPromise();
      return result;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async UploadFile(file: File, fileName: string): Promise<void> {
    const totalChunks = Math.ceil(file.size / this.CHUNK_SIZE);
    try {
      for (let i = 0; i < totalChunks; i++) {
        const chunk: Blob = file.slice(
          i * this.CHUNK_SIZE,
          (i + 1) * this.CHUNK_SIZE,
        );
        await this.UploadFileChunk(chunk, i);
      }
      await this.CompleteFileChunkUpload(totalChunks, fileName);
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async GetCsvColumns(filePath: string): Promise<any> {
    try {
      const response = await this.http
        .get<{ columns: string[] }>(
          `${this.configService.getDataApiUrl}/columns/${filePath}`,
        )
        .toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async RunWidget(
    siteId: string,
    projectId: string,
    workflowId: string,
    widgetUrn: string,
  ): Promise<boolean> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/${workflowId}/widget/${widgetUrn}/run`;
    try {
      await this.http.post<string>(url, {}).toPromise();
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API RunWidget() failed: ' + this.sharedDataService.LastError,
        );
        throw error;
      }
    }

    return true;
  }

  async CreateProject(
    siteId: string,
    project: Project,
  ): Promise<string | undefined> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/create_new_project_with_user_mappings`;
      let response = await this.commonApiService
        .post_api<APIModels.ProjectPostResponse>(url, project)
        .toPromise();
      return response!.project_id;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async CreateJupyterServer(
    siteId: string,
    jsonData: any,
    project_id: string,
  ): Promise<string | undefined> {
    console.log(project_id, 'project display', jsonData);
    try {
      let url: string = `${this.configService.getApiUrl}/projects/${project_id}/jupyter/hub/server`;
      let response = await this.commonApiService
        .post_api<APIModels.ProjectPostResponse>(url, jsonData)
        .toPromise();
      console.log(response, 'response back');
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async AssestDataModification(
    siteId: string,
    projectId: string,
    data: any,
  ): Promise<string | undefined> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets_modification/datasets_conversion`;
      let response = await this.commonApiService
        .post_api(url, data)
        .toPromise();
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        //this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
      throw error;
    }
    return undefined;
  }
  async UpdateProject(siteId: string, project: Project): Promise<void> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project._id}`;

      // Assuming you have a proper API endpoint for updating projects, adjust this accordingly
      await this.http.patch(url, project).toPromise();
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
      throw error;
    }
  }

  async DeleteProject(
    siteId: string,
    project: any,
    jsonData: any,
  ): Promise<void> {
    try {
      // Assuming 'project' has an '_id' property representing the project ID
      const projectId: string = project;

      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}`;

      // Assuming you have a proper API endpoint for deleting projects, adjust this accordingly
      await this.commonApiService.delete_api(url).toPromise();

      // Assuming you want to reload the projects list after deletion
      await this.GetProjects('1', '', jsonData);
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async DeleteScheduleId(
    siteId: string,
    project: any,
    schedule_id: any,
  ): Promise<void> {
    try {
      const projectId: string = project;
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/scheduling/delete_schedule/${schedule_id}`;
      const response = await this.http.delete(url).toPromise();
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async CancelScheduleId(
    siteId: string,
    project: any,
    jsonData: any,
  ): Promise<void> {
    try {
      const projectId: string = project;
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/scheduling/pause_schedule`;
      const response = await this.commonApiService
        .post_api(url, jsonData)
        .toPromise();
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async UploadCsv(
    siteId: string,
    projectId: string,
    file: any,
    name: string,
    description: any,
    fileType: any,
  ): Promise<string | undefined> {
    try {
      const formData: any = new FormData();
      formData.append('file', file);
      let url: string = `${this.configService.getAuxApiUrl}/${siteId}/projects/${projectId}/assets/dataset/tabular/upload?name=${name}&description=${description}&file_type=${fileType}`;
      let response: any = await this.commonApiService
        .post_api(url, formData)
        .toPromise();
      return response!.dataset_id;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API UploadCsv() failed: ' + this.sharedDataService.LastError,
        );
      }
    }
    return undefined;
  }

  async GetProjects(
    siteId: string,
    searchTerms: string | undefined,
    jsonData: any,
  ): Promise<Project[]> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/users_projects_mappings/get_mappings_based_on_user_id`;
      if (searchTerms) {
        url += '?search_term=' + searchTerms;
      }
      let response = await this.commonApiService
        .post_api<APIModels.ProjectGetResponse>(url, jsonData)
        .toPromise();
      return response!.mappings;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetProjects() failed or User records are removed, The removed users ids exist in projects records owner_id and last_modified_by_id ' +
            this.sharedDataService.LastError,
        );
      }
    }
    return [];
  }

  async getAllAdmins(siteId: string, jsonData: any): Promise<User[]> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/users/`;

      let response = await this.http
        .get<APIModels.UserGetResponse>(url)
        .toPromise();
      return response!.users.sort((a, b) => {
        let dateA = new Date(a.created_at);
        let dateB = new Date(b.created_at);
        return dateB.getTime() - dateA.getTime(); // Ascending order
      });
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
    }
    return [];
  }

  async GetAllServers(
    project_id: any,
    user_id: any,
  ): Promise<APIModels.TransformedServerResponse[]> {
    try {
      const url: string = `${this.configService.getApiUrl}/projects/${project_id}/jupyter/hub/server/all`;
      const response = await this.http
        .get<APIModels.ServerResponse[]>(url)
        .toPromise();

      if (response) {
        console.log(response, 'respnse of all servers');
        // Transform the response data to match TransformedServerResponse
        return (
          response.map((server) => ({
            server_id: server.project_id, // Assuming `project_id` as `server_id`
            server_name: server.name,
            server_description: server.description,
            project_id: server.project_id,
            project_name: 'Unknown Project Name', // Placeholder, adjust based on your data
            server_status: server.status,
            launch_url: server.launch_url,
            last_activity: server.last_activity,
            notebooks: server.notebooks,
            actions: {
              can_delete: true, // Default or computed value
              can_start: server.status === 'STOPPED', // Example logic
              can_stop: server.status === 'RUNNING', // Example logic
            },
          })) || []
        );
      }
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
      console.error('Error fetching servers:', error);
    }
    return [];
  }

  async getFeaturesMappingProject(role_id: any): Promise<Project[]> {
    try {
      const jsonData = {
        roles_id: role_id,
      };
      let siteId = '1';
      let url: string = `${this.configService.getApiUrl}/${siteId}/roles_features_maps/get_role_feature_map_id`;

      let response = await this.commonApiService
        .post_api<APIModels.ProjectGetResponse>(url, jsonData)
        .toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        // console.error(
        //   'Call to API GetProjects() failed: ' +
        //     this.sharedDataService.LastError,
        // );
      }
    }
    return [];
  }

  async GetM2Projects(data: any): Promise<any> {
    try {
      //const baseUrl = this.configService.getApiUrl();
      const url: string = `https://hexaind2manualtest01api.corp.databrick.tech/project/getAllProjectsWithPagination`;
      let response: any = await this.commonApiService
        .post_api(url, data)
        .toPromise();
      return response.data; // Return the array of projects
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
      throw error;
    }
  }

  async GetCustomPythonWidgetRecipes(
    projectId: string,
    siteId: string,
  ): Promise<APIModels.CustomPythonWidgetRecipe[]> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/custom_python/custom_python_widget_recipes`;

    try {
      const response = await this.http
        .get<APIModels.GetCustomPythonWidgetRecipeResponse>(url)
        .toPromise();
      if (response === undefined) {
        throw new Error('Response is undefined');
      }
      return response.results; // Assuming `results` contain an array of Recipe objects
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
      throw error;
    }
  }

  async GetVersionedWorkflowWidgetActivityLog(
    siteId: string,
    projectId: string,
    runId: string,
    widgetUrn: string,
    nextCursorTimeStamp: string | undefined,
    nextCursorRecordId: string | undefined,
  ): Promise<APIModels.ActivityLogResponse | undefined> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/runs/${runId}/widget/${widgetUrn}/activity_log?size=50`;
      if (
        nextCursorTimeStamp !== undefined &&
        nextCursorRecordId !== undefined
      ) {
        url += `&next_cursor_timestamp=${nextCursorTimeStamp}&next_cursor_record_id=${nextCursorRecordId}`;
      }
      let log: APIModels.ActivityLogResponse | undefined = await this.http
        .get<APIModels.ActivityLogResponse>(url)
        .toPromise();
      return log;
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
    }
    return undefined;
  }

  async getCustomCodePythonWidgets(
    siteId: string,
    projectId: string,
  ): Promise<APIModels.CustomCode[]> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/custom_python/custom_code_widget/fetch_all`;

    try {
      const response = await this.commonApiService
        .get_api<APIModels.GetCustomCodeResponse>(url)
        .toPromise();
      if (!response || !response.results) {
        throw new Error('Response is undefined or does not contain results');
      }
      const customWidgets: APIModels.CustomCode[] = response.results.map(
        (customCode: { name: any; _id: any; description: string }) => ({
          type: WidgetType.CUSTOM_CODE,
          clientType: WidgetClientType.CustomCode, // Adjust as needed
          iconName: customCode.name, // Assuming `name` is the property for the icon name
          displayName: customCode.name, // Assuming `name` is the property for the display name
          id: customCode._id,
          description: customCode.description,
        }),
      );

      return customWidgets;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return [];
  }

  filterOnValidWidgets(widgets: Widget[]): Widget[] {
    return widgets.filter((widget) => widget.urn !== '0');
  }

  getStartNodeWidget(widgets: Widget[]): Widget | undefined {
    return widgets.find(
      (widget) => widget.client_tags.ClientType === WidgetClientType.Start,
    );
  }

  getEndNodeWidget(widgets: Widget[]): Widget | undefined {
    return widgets.find(
      (widget) => widget.client_tags.ClientType === WidgetClientType.End,
    );
  }

  getMOBOWidget(widgets: Widget[]): Widget | undefined {
    return widgets.find((widget) => widget.type === WidgetType.MOBO);
  }

  async UpdateWorkflowFields(
    siteId: string,
    projectId: string,
    workflow: Workflow,
  ) {
    let response: APIModels.UpdateWorkflowResponse | undefined = undefined;
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/${workflow._id}`;
    workflow.last_modified_at = new Date();
    try {
      response = await this.http
        .put<APIModels.UpdateWorkflowResponse>(url, workflow)
        .toPromise();
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async UpdateWorkflow(
    siteId: string,
    projectId: string,
    workflow: Workflow,
    arrows: Arrow[] | undefined,
  ): Promise<boolean> {
    let response: APIModels.UpdateWorkflowResponse | undefined = undefined;
    let startWidget: Widget | undefined = undefined;
    let endWidget: Widget | undefined = undefined;
    let moboWidget: Widget | undefined = undefined;
    let success: boolean = true;

    try {
      if (arrows) {
        let arrow_cache: any[] = [];

        arrows.forEach((arrow) => {
          arrow_cache.push({
            start_urn: arrow.startPoint.widgetControl.Widget.urn,
            start_connector_point_type: arrow.startPoint.connectorPointType,
            end_urn: arrow.endPoint.widgetControl.Widget.urn,
            end_connector_point_type: arrow.endPoint.connectorPointType,
            arrow_type: arrow.arrowType,
          });
        });
        workflow.client_tags.Arrows = arrow_cache;
      }

      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/${workflow._id}`;
      workflow.last_modified_at = new Date();

      startWidget = this.getStartNodeWidget(workflow.widgets);
      if (startWidget) {
        workflow.widgets = workflow.widgets.filter(
          (widget) => widget.urn !== startWidget!.urn,
        );
      }

      endWidget = this.getEndNodeWidget(workflow.widgets);
      if (endWidget) {
        workflow.widgets = workflow.widgets.filter(
          (widget) => widget.urn !== endWidget!.urn,
        );
      }

      moboWidget = this.getMOBOWidget(workflow.widgets);
      if (moboWidget) {
        const response = await this.GetWorkflowRuns(
          '1',
          projectId,
          workflow._id ?? '',
        );
        const latestRun = response.sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        )[0];

        if (latestRun) {
          const run_id = latestRun._id ?? '';
          const runStatus =
            await this.WorkflowsSessionsApiService.GetVersionedWorkflowWidgetRunStatus(
              siteId,
              projectId,
              workflow._id ?? '',
              run_id,
              moboWidget?.urn ?? '',
            );

          if (runStatus?.[0]?.result_value) {
            const result_value = runStatus[0]
              .result_value as SessionApiModels.DatasetWidgetResult;
            const dataset_path = result_value.dataset_location?.[0]?.path ?? '';
            if (moboWidget.config && typeof moboWidget.config === 'object') {
              (moboWidget.config as MOBOWidgetConfig).dataset = dataset_path;
            }
          } else {
            if (moboWidget.config && typeof moboWidget.config === 'object') {
              (moboWidget.config as MOBOWidgetConfig).dataset = '';
            }
          }
        } else if (moboWidget.config && typeof moboWidget.config === 'object') {
          (moboWidget.config as MOBOWidgetConfig).dataset = '';
        }
      }

      if (startWidget) {
        workflow.client_tags.StartWidgetPosition = new Position(
          Widget.GetPositionX(startWidget),
          Widget.GetPositionY(startWidget),
        );
      }

      if (endWidget) {
        workflow.client_tags.EndWidgetPosition = new Position(
          Widget.GetPositionX(endWidget),
          Widget.GetPositionY(endWidget),
        );
      }

      try {
        response = await this.http
          .put<APIModels.UpdateWorkflowResponse>(url, workflow)
          .toPromise();
      } catch (error: any) {
        success = false;
        if (error instanceof HttpErrorResponse) {
          this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
          throw error;
        }
      }
      if (response) {
        success = response.success;
      }
    } catch (error) {}

    if (startWidget) {
      workflow.widgets.push(startWidget);
    }
    if (endWidget) {
      workflow.widgets.push(endWidget);
    }

    return success;
  }

  async GetWorkflowById(
    siteId: string,
    projectId: string,
    workflowId: string,
  ): Promise<Workflow | undefined> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/${workflowId}`;
      let workflow: any = await this.http
        .get<APIModels.GetWorkflowResponse>(url)
        .toPromise();
      return workflow;
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
    }
    return undefined;
  }

  async GetSessionByWorkflowId(
    siteId: string,
    projectId: string,
    workflowId: string,
  ): Promise<any> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/workflow/${workflowId}/get_session`;
      let session: any = await this.http.get(url).toPromise();
      return session;
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
    }
    return undefined;
  }

  async DeleteWorkflowById(
    siteId: string,
    projectId: string,
    workflowId: string,
  ): Promise<Workflow | undefined> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/${workflowId}`;
      let workflow: any = await this.http
        .delete<APIModels.GetWorkflowResponse>(url)
        .toPromise();
      return workflow;
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async GetWorkflows(searchTerms: string | undefined): Promise<Workflow[]> {
    try {
      let url: string = `${this.configService.getAppApiURL}/workflow?page_limit=100&page_number=1`;
      if (searchTerms) {
        url += '&search_term=' + searchTerms;
      }
      let response = await this.http
        .get<APIModels.GetWorkflowsResponse>(url)
        .toPromise();
      return response!.workflows.sort((a, b) => {
        let dateA = new Date(a.created_at);
        let dateB = new Date(b.created_at);
        return dateB.getTime() - dateA.getTime(); // Ascending order
      });
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return [];
  }

  async GetUsers(
    siteId: string,
    searchTerms: string | undefined,
  ): Promise<User[]> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/users/`;
      if (searchTerms) {
        url += '?search_term=' + searchTerms;
      }
      let response = await this.http
        .get<APIModels.UserGetResponse>(url)
        .toPromise();
      return response!.users.sort((a, b) => {
        let dateA = new Date(a.created_at);
        let dateB = new Date(b.created_at);
        return dateB.getTime() - dateA.getTime(); // Ascending order
      });
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return [];
  }

  async GetNotifications(
    siteId: string,
    project_id: string,
    searchTerms: string | undefined,
  ): Promise<Notification[]> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project_id}/notification?page_limit=100&page_number=1`;

      if (searchTerms) {
        url += '?search_term=' + searchTerms;
      }
      let response = await this.http
        .get<APIModels.NotificationsGetResponse>(url)
        .toPromise();

      return response!.notification;
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return [];
  }

  async GetConnectors(
    siteId: string,
    projectId: string,
  ): Promise<Connector[] | undefined> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/connectors`;
    try {
      let response = await this.commonApiService
        .get_api<ConnectorListResponse>(url)
        .toPromise();
      return response!.connectors;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);

        if (error.status === 400) {
          console.error('Bad request:', error.error.detail);
          throw new Error(error.error.detail || 'Error creating user');
        } else if (error.status === 500) {
          console.error('Server error:', error.error.detail);
          throw new Error('Internal server error');
        }
      } else {
        console.error('Non-HTTP error:', error);
        throw new Error('Error creating user');
      }
    }
    return undefined;
  }

  RescaleAuthenticate(siteId: string, projectId: string, token: any) {
    const baseUrl = this.configService.getApiUrl;
    const url = `${baseUrl}/${siteId}/projects/${projectId}/rescale_authentication/`;
    return this.http.post(url, token);
  }

  async UpdateNotificationStatus(
    site_id: string,
    notificationId: string,
    status: boolean,
    user_id: string,
  ): Promise<string> {
    let notificationStatusId: string = '';
    let response: string | undefined = undefined;
    try {
      let url: string = `${this.configService.getApiUrl}/${site_id}/notification/${notificationId}/updateNotification`;
      response = await this.commonApiService
        .put_api<string>(url, { status: status, user_id: user_id })
        .toPromise();
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
      throw error;
    }
    if (response) {
      const responseObject = JSON.parse(response);
      notificationStatusId = responseObject.notification._id;
    }

    return notificationStatusId;
  }

  async UpdateNotificationStatusAsUnread(
    site_id: string,
    notificationId: string,
  ): Promise<string> {
    let notificationStatusId: string = '';
    let response: string | undefined = undefined;
    try {
      let url: string = `${this.configService.getApiUrl}/${site_id}/notification_unread/${notificationId}`;
      response = await this.commonApiService
        .put_api<string>(url, {})
        .toPromise();
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
      throw error;
    }
    if (response) {
      const responseObject = JSON.parse(response);
      notificationStatusId = responseObject.notification._id;
    }

    return notificationStatusId;
  }

  async UpdateAllNotificationStatus(
    siteId: string,
    userId: string,
  ): Promise<string> {
    let notificationResponse: string = '';
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/userid/${userId}`;
      const response: string = await this.commonApiService
        .put_api<string>(url, {})
        .toPromise();

      // Assign the response directly to notificationStatusId
      notificationResponse = response;
    } catch (error) {
      // Handle HTTP errors
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
      // Throw the error for further handling if needed
      throw error;
    }

    return notificationResponse;
  }

  updateNotificationStatus() {
    this.updateNotificationStatusSource.next();
  }

  UploadCsvFile(
    file: File,
    name: string,
    description: string,
    access_mode: string,
    onProgress: (progress: number) => void,
  ): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    let query = `name=${encodeURIComponent(
      name,
    )}&description=${encodeURIComponent(
      description,
    )}&file_type=CSV&access_mode=${encodeURIComponent(access_mode)}`;
    const url: string = `${this.configService.getAppAuxApiURL}/assets/dataset/tabular/upload?${query}`;

    return this.http
      .post(url, formData, {
        reportProgress: true,
        observe: 'events',
      })
      .pipe(
        map((event: any) => {
          switch (event.type) {
            case HttpEventType.UploadProgress:
              if (event.total) {
                const percentDone = Math.round(
                  (99 * event.loaded) / event.total,
                );
                onProgress(percentDone);
              }
              break;
            case HttpEventType.Response:
              onProgress(100);
              return event.body;
          }
        }),
        catchError((error: HttpErrorResponse) => {
          console.error('Upload failed:', error.message);
          throw error;
        }),
      );
  }

  UploadCsvFileDestinationFolder(
    file: File,
    name: string,
    description: string,
    access_mode: string,
    destination_folder: string,
    workflow_id: any,
    onProgress: (progress: number) => void,
  ): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    let query = `name=${encodeURIComponent(
      name,
    )}&description=${encodeURIComponent(
      description,
    )}&upload_type=${encodeURIComponent(
      'WORKFLOWS',
    )}&workflow_id=${encodeURIComponent(
      workflow_id,
    )}&file_type=CSV&access_mode=${encodeURIComponent(
      access_mode,
    )}&destination_folder=${encodeURIComponent(destination_folder)}`;
    const url: string = `${this.configService.getAppAuxApiURL}/assets/dataset/tabular/upload?${query}`;

    return this.http
      .post(url, formData, {
        reportProgress: true,
        observe: 'events',
      })
      .pipe(
        map((event: any) => {
          switch (event.type) {
            case HttpEventType.UploadProgress:
              if (event.total) {
                const percentDone = Math.round(
                  (99 * event.loaded) / event.total,
                );
                onProgress(percentDone);
              }
              break;
            case HttpEventType.Response:
              onProgress(100);
              return event.body;
          }
        }),
        catchError((error: HttpErrorResponse) => {
          console.error('Upload failed:', error.message);
          throw error;
        }),
      );
  }
  async GetUploadFiles(
    file: File,
    projectId: any,
    siteId: any,
    isPythonFileUpload: any,
    fileName?: any,
  ): Promise<any> {
    const url = `${this.configService.getAppApiURL}/assets/custom_python_code_builder/multiple_file_uploads`;
    const formData = new FormData();
    formData.append('files', file, file.name || fileName);
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });
    try {
      const response = await this.http
        .post<APIModels.GetFilesPostResponse>(url, formData, { headers })
        .toPromise();
      if (response) {
        let secondApiResponse: any = [];
        if (isPythonFileUpload) {
          secondApiResponse = [file.name];
        } else {
          secondApiResponse = await this.CallSecondApi(
            response,
            projectId,
            siteId,
          );
        }

        const filePath = response.files[0].file_path;
        const thirdApiResponse = await this.callThirdApi(
          filePath,
          siteId,
          projectId,
        );
        return {
          firstApiResponse: response,
          secondApiResponse: secondApiResponse,
          finalresponse: thirdApiResponse,
        };
      } else {
        console.error('First API Response is undefined.');
        return null;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetUploadFiles() failed' +
            this.sharedDataService.LastError,
        );
      }
    }
  }

  async uploadFileWithFixedPath(file: File, path: string = 'defaultPath') {
    const url = `${this.configService.getAppApiURL}/assets/custom_python_code_builder/multiple_file_uploads`;
    const formData = new FormData();
    formData.append('files', file, file.name);
    formData.append('prefered_path', path);
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });

    return await lastValueFrom(this.http.post(url, formData, { headers }));
  }

  async mountedUploadFiles(file: any, projectId: any, siteId: any) {
    if (file) {
      const secondApiResponse = await this.CallSecondApi(
        file,
        projectId,
        siteId,
      );
      const filePath = file.files[0].file_path;
      const thirdApiResponse = await this.callThirdApi(
        filePath,
        siteId,
        projectId,
      );
      return {
        secondApiResponse: secondApiResponse,
        finalresponse: thirdApiResponse,
      };
    } else {
      console.error('First API Response is undefined.');
      return null;
    }
  }

  async CallSecondApi(
    data: APIModels.GetFilesPostResponse,
    projectId: any,
    siteId: any,
  ): Promise<any> {
    const filePath = data.files[0].file_path;
    const url = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/custom_python_code_builder/get_file_names`;
    const queryParams = { file_path: filePath }; // Changed to JSON object
    const headers = new HttpHeaders().set('Accept', 'application/json');
    try {
      // Make the second API call
      const response = await this.http
        .post(url, queryParams, { headers })
        .toPromise();
      // Call the third API with the file path and first API response
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async callThirdApi(
    filePath: string,
    siteId: any,
    projectId: any,
  ): Promise<any> {
    const url = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/custom_python_code_builder/get_metadata`;
    const headers = new HttpHeaders().set('Accept', 'application/json');
    const queryParams = { file_path: filePath };
    try {
      const response = await this.http
        .post(url, queryParams, { headers })
        .toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async getFileNames(file: File, projectId: any, siteId: any): Promise<any> {
    const url = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/multiple_file_uploads`;
    const formData = new FormData();
    formData.append('files', file, file.name);
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });
    try {
      const response = await this.http
        .post<APIModels.GetFilesPostResponse>(url, formData, { headers })
        .toPromise();
      if (response) {
        return { firstApiResponse: response };
      } else {
        console.error('First API Response is undefined.');
        return null;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async executeValidation(
    siteId: any,
    projectId: any,
    formData: any,
    correlationId: any,
  ): Promise<any> {
    const url = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/custom_python_code_builder/validate_custom_code`;
    const headers = new HttpHeaders({
      Accept: 'application/json',
      'x-correlation-ID': correlationId,
    });

    try {
      const execute_response = await this.http
        .post<APIModels.GetFilesPostResponse>(url, formData, { headers })
        .toPromise();
      if (execute_response) {
        return execute_response;
      } else {
        console.error('First API Response is undefined.');
        return null;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async createModuleId(
    siteId: any,
    projectId: any,
    formData: any,
  ): Promise<any> {
    const url = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/assets/custom_python_code_builder/create_module`;
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });
    try {
      const module_response = await this.http
        .post<APIModels.GetFilesPostResponse>(url, formData, {
          headers: this.tokenHeaders,
        })
        .toPromise();
      if (module_response) {
        return module_response;
      } else {
        console.error('First API Response is undefined.');
        return null;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async saveRecipe(siteId: any, projectId: any, formData: any): Promise<any> {
    const url = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/custom_python/custom_python_widget_recipe/update_or_insert`;
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });
    try {
      const save_response = await this.http
        .post<APIModels.GetFilesPostResponse>(url, formData, { headers })
        .toPromise();
      if (save_response) {
        return save_response;
      } else {
        console.error('First API Response is undefined.');
        return null;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async publishRecipe(siteId: any, projectId: any, data: any): Promise<any> {
    const url = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/custom_python/custom_code_widget/publish`;
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });
    try {
      const publish_response = await this.http
        .post<APIModels.GetFilesPostResponse>(url, data, { headers })
        .toPromise();
      if (publish_response) {
        return publish_response;
      } else {
        console.error('First API Response is undefined.');
        return null;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async saveCustomData(
    projectId: string,
    siteId: string,
    formData: any,
  ): Promise<any> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/custom_python/custom_python_widget_recipe/update_or_insert`; // Adjust the URL according to your API endpoint
      let response = await this.http.post(url, formData).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async getMountedDriveDirectoryList(
    folderPath?: string,
    type?: string,
  ): Promise<APIModels.FileNodeResponse | undefined> {
    try {
      let url: string = `${this.configService.getAppApiURL}/assets/datasets/mounted_files_list`;
      let payload: any = {};

      if (type) {
        url += `?file_ext=${encodeURIComponent(type)}`;
      }
      if (folderPath !== undefined) {
        payload.folder_path = folderPath;
      }

      const response = await this.http
        .post<APIModels.FileNodeResponse>(url, payload)
        .toPromise();

      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async importMountedDriveFile(
    file: string,
    name: string,
    description: string,
    access_mode: string,
    destination_folder: string,
  ): Promise<APIModels.PostCSVResponse | undefined> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      let query = `name=${encodeURIComponent(
        name,
      )}&description=${encodeURIComponent(
        description,
      )}&file_type=CSV&access_mode=${encodeURIComponent(access_mode)}`;
      if (destination_folder != '') {
        query = query + '&destination_folder=' + destination_folder;
      }
      const url: string = `${this.configService.getAppApiURL}/assets/dataset/tabular/mounted_upload?${query}`;
      const response = await this.http
        .post<APIModels.PostCSVResponse>(url, formData)
        .toPromise();

      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async importDatasetMountedDriveFile(
    file: string,
    name: string,
    description: string,
    destination_folder: string,
    dataset_type: string,
  ): Promise<APIModels.PostCSVResponse | undefined> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      let query = `name=${encodeURIComponent(
        name,
      )}&description=${encodeURIComponent(
        description,
      )}&dataset_type=${dataset_type}`;
      if (destination_folder != '') {
        query =
          query +
          '&destination_folder=' +
          destination_folder +
          '&upload_type=DATASETS';
      }
      const url: string = `${this.configService.getAppApiURL}/assets/dataset/tabular/mounted_upload?${query}`;
      const response = await this.http
        .post<APIModels.PostCSVResponse>(url, formData)
        .toPromise();

      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getFilterWidgetFields(
    site_id: string,
    project_id: string,
    datasetId: any,
  ): Promise<any | undefined> {
    let response: string | undefined = undefined;
    try {
      let url: string = `${this.configService.getAppAuxApiURL}/eda/metadata?dataset_id=${datasetId}`;
      // let url: string = `${this.configService.getAppAuxApiURL}/eda/statistics?dataset_id=${datasetId}`;
      const response = await this.http.get(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getMetadataOfDataset(datasetId: any): Promise<any | undefined> {
    let response: string | undefined = undefined;
    try {
      let url: string = `${this.configService.getAppAuxApiURL}/eda/metadata?dataset_id=${datasetId}`;
      const response = await this.http.get(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  /**
   * Currently every widget is using eda/statictics api for getting the columns list which causes latency and other issues when dataset is not yet
   * processed . Since in every widget code, statistics api is implemented and instead of formatting the code in every widget
   * call this function which gives only column names in statistics api response format, to avoid refactoring the code in every widget
   * @param datasetId
   */

  async getColumnsViaMetadataApi(datasetId: any) {
    try {
      let response = await this.getMetadataOfDataset(datasetId);
      let extractedColumnNames = Object.keys(response.data_column_types);
      return {
        statistics: [{ column_names: [...extractedColumnNames] }],
      };
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return {};
  }

  async getUniqueValuesOfColumn(
    datasetId: any,
    columnName: string,
  ): Promise<any | undefined> {
    let response: string | undefined = undefined;
    try {
      let url: string = `${this.configService.getAppAuxApiURL}/eda/get_unique_values?dataset_id=${datasetId}&column_name=${columnName}`;
      const response = await this.http.get(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getDatasetList(
    site_id: string,
    project_id: string,
    connector_id: any,
  ): Promise<any | undefined> {
    let response: string | undefined = undefined;
    try {
      let url: string = `${this.configService.getApiUrl}/${site_id}/projects/${project_id}/assets/bigquery/datasets_list?connector_id=${connector_id}`;
      response = await this.http.post<string>(url, {}).toPromise();
      if (response !== undefined) {
        return response;
      } else {
        return undefined;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getTableList(
    site_id: string,
    project_id: string,
    dataset_name: string,
    connector_id: any,
  ): Promise<any | undefined> {
    let response: string | undefined = undefined;
    try {
      let url: string = `${this.configService.getApiUrl}/${site_id}/projects/${project_id}/assets/bigquery/tables_list?connector_id=${connector_id}`;
      const requestBody = {
        dataset_name: dataset_name,
      };
      response = await this.http.post<string>(url, requestBody).toPromise();
      if (response !== undefined) {
        return response;
      } else {
        return undefined;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getSchemaInputsCount(): Promise<number | undefined> {
    try {
      const url: string = `${this.configService.getSchemaUrl}/APPEND/schema`;
      const response = await this.http
        .get<APIModels.SchemaGetResponse>(url)
        .toPromise();
      return response!.inputs.count; // Return only the count
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async cancelApiRequest(name: string, description: string): Promise<any> {
    try {
      let query = `name=${encodeURIComponent(
        name,
      )}&description=${encodeURIComponent(description)}&file_type=CSV`;
      const url: string = `${this.configService.getAppAuxApiURL}/assets/dataset/tabular/upload?${query}`;

      const response = await this.http.get(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async GetCustomCodeWidget(widgetId: string): Promise<any> {
    let url: string = `${this.configService.getAppApiURL}/custom_python/custom_code_widget/get?widget_id=${widgetId}`;
    let widget: any = await this.http.get(url).toPromise();
    return widget;
  }

  async GetCustomPythonWidgetReceipe(widgetId: string): Promise<any> {
    let url: string = `${this.configService.getAppApiURL}/custom_python/custom_python_widget_recipe/get?custom_python_widget_recipe_id=${widgetId}`;
    let widget: any = await this.http.get(url).toPromise();
    return widget;
  }

  toggleFavourite(
    siteId: string,
    projectId: string,
    favorite: boolean,
  ): Observable<any> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/updateFavoriteProject/${projectId}?is_favorite=${favorite}`;
    let data = { siteId: siteId, projectId: projectId, is_favorite: favorite };
    return this.http.post(url, data, {
      headers: this.tokenHeaders,
      observe: 'response',
    });
  }

  redirectToUrlWithHeaders(url: string, headers: HttpHeaders): void {
    const headersObject: { [key: string]: string } = {};
    headers.keys().forEach((key) => {
      headersObject[key] = headers.get(key) ?? '';
    });
    const queryParams = Object.keys(headersObject)
      .map(
        (key) =>
          encodeURIComponent(key) +
          '=' +
          encodeURIComponent(headersObject[key]),
      )
      .join('&');
    const redirectUrl = url + '?' + queryParams;
    window.location.href = redirectUrl;
  }

  async GetAllRunsForWorkflowById(workflowId: string): Promise<WorkflowRun[]> {
    try {
      let url: string = `${this.configService.getAppApiURL}/workflows/${workflowId}/run`;
      let workflow: any = await this.http
        .get<APIModels.GetWorkflowsRunsResponse>(url)
        .toPromise();
      return workflow!.runs;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return [];
  }

  ImportFile(
    file: File,
    name: string,
    description: string,
    access_mode: string,
    file_type: string,
    onProgress: (progress: number) => void,
    dataset_type: string,
    destination_folder: string,
  ): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (file_type === 'PARQUET') {
      file_type = 'CSV';
    }
    let query = `name=${encodeURIComponent(
      name,
    )}&description=${encodeURIComponent(
      description,
    )}&upload_type=${encodeURIComponent(
      'DATASETS',
    )}&file_type=${encodeURIComponent(
      file_type,
    )}&access_mode=${encodeURIComponent(
      access_mode,
    )}&dataset_type=${encodeURIComponent(
      dataset_type,
    )}&destination_folder=${encodeURIComponent(destination_folder)}
    `;
    const url: string = `${this.configService.getAppAuxApiURL}/assets/dataset/tabular/upload?${query}`;
    return this.http
      .post(url, formData, {
        reportProgress: true,
        observe: 'events',
      })
      .pipe(
        map((event: any) => {
          switch (event.type) {
            case HttpEventType.UploadProgress:
              if (event.total) {
                const percentDone = Math.round(
                  (99 * event.loaded) / event.total,
                );
                onProgress(percentDone);
              }
              break;
            case HttpEventType.Response:
              onProgress(100);
              return event.body;
          }
        }),
        catchError((error: HttpErrorResponse) => {
          this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
          throw this.sharedDataService.LastError;
        }),
      );
  }

  ImportFileWithTags(
    file: File,
    name: string,
    description: string,
    access_mode: string,
    file_type: string,
    onProgress: (progress: number) => void,
    dataset_type: string,
    destination_folder: string,
    tags: string[],
  ): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    if (file_type === 'PARQUET') {
      file_type = 'CSV';
    }
    let query = `name=${encodeURIComponent(
      name,
    )}&description=${encodeURIComponent(
      description,
    )}&upload_type=${encodeURIComponent(
      'DATASETS',
    )}&file_type=${encodeURIComponent(
      file_type,
    )}&access_mode=${encodeURIComponent(
      access_mode,
    )}&dataset_type=${encodeURIComponent(dataset_type)}`;
    // Conditionally append destination_folder if it's not undefined or null
    if (destination_folder != null) {
      query += `&destination_folder=${encodeURIComponent(destination_folder)}`;
    }
    if (tags.length > 0) {
      query += `&tags=${tags.join(',')}`;
    }

    // Loop through the array and append each element individually

    const url: string = `${this.configService.getAppAuxApiURL}/assets/dataset/tabular/upload?${query}`;
    return this.http
      .post(url, formData, {
        reportProgress: true,
        observe: 'events',
      })
      .pipe(
        map((event: any) => {
          switch (event.type) {
            case HttpEventType.UploadProgress:
              if (event.total) {
                const percentDone = Math.round(
                  (99 * event.loaded) / event.total,
                );
                onProgress(percentDone);
              }
              break;
            case HttpEventType.Response:
              onProgress(100);
              return event.body;
          }
        }),
        catchError((error: HttpErrorResponse) => {
          this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
          throw this.sharedDataService.LastError;
        }),
      );
  }

  async createScheduleWorkflow(
    siteId: string,
    project: any,
    jsonData: any,
  ): Promise<string | undefined> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project}/scheduling/create_schedule`;
      let response = await this.commonApiService
        .post_api<APIModels.ProjectPostResponse>(url, jsonData)
        .toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error('Error creating schedule workflow:', error);
        if (error.status === 400) {
          return 'Schedule for this workflow already exists';
        } else if (error.status === 500) {
          return this.sharedDataService.LastError;
        }
      }
    }
    return undefined;
  }

  async getScheduledJobs(
    siteId: any,
    project: any,
    jsonData: any,
  ): Promise<any> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project}/scheduling/get_all_schedules`;
    let schedules: any = await this.http.post(url, jsonData).toPromise();
    return schedules.schedules;
  }

  async getScheduleById(siteId: any, project: any, data: any): Promise<any> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project}/scheduling/get_schedule_by_id/${data._id}`;
    let schedules: any = await this.http.get(url).toPromise();
    return schedules;
  }

  async getScheduleByIdFilterByRunId(
    siteId: any,
    project: any,
    data: any,
  ): Promise<any> {
    if (data.run_id == 'Unknown') {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project}/scheduling/get_schedule_by_id/${data._id}`;
      let schedules: any = await this.http.get(url).toPromise();
      return schedules;
    } else {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project}/workflows/${data.workflow_id}/run_summary/${data.run_id}`;
      let schedules: any = await this.http.get(url).toPromise();
      return schedules;
    }
  }

  async updateScheduleWorkflow(
    siteId: string,
    project: any,
    jsonData: any,
  ): Promise<string | undefined> {
    try {
      const url = `${this.configService.getApiUrl}/${siteId}/projects/${project}/scheduling/update_schedule`;
      const response = await this.http.post<string>(url, jsonData).toPromise();
      return response;
    } catch (error) {
      console.error('Error updating schedule workflow:', error);
      return undefined;
    }
  }

  updateNotificationCount(count: number): void {
    this.notificationCountSubject.next(count);
  }
  /**
   * This is simply an api call to log the lastAccessed date for the project in the database so ignoring the result
   */
  updateProjectAccessedDate(siteId: string, projectId: any): any {
    try {
      const url = `${this.configService.getApiUrl}/${siteId}/update_last_update_at/${projectId}`;
      this.http.patch<any>(url, null).subscribe();
    } catch (error) {
      console.log(
        `Error occurred while updating the last accessed date for project with id:${projectId}`,
      );
    }
  }

  downloadWorkflowResultData(data: any): Observable<any> {
    const url: string = `${this.configService.getAppApiURL}/assets/download_file?download_json=false`;
    return this.http.post(url, data, {
      responseType: 'blob',
    });
  }

  fetchTextDataset(
    datasetId: string,
    page_number: number,
    charLength: number,
  ): Observable<any> {
    const url = `${this.configService.getAppApiURL}/assets/dataset/file_preview/${datasetId}`;

    let params = new HttpParams()
      .set('page_number', page_number)
      .set('length', charLength);
    return this.http.get(url, { params });
  }

  async DownloadDatset(
    siteId: string,
    projectId: string,
    dataset_id: string,
    type: string,
  ): Promise<any> {
    // Construct the base URL
    let url = `${this.configService.getAppApiURL}/assets/dataset/tabular/download/${dataset_id}`;
    // Add the query parameter for dataset type
    url += `?dataset_type=${encodeURIComponent(type)}`; // Ensure encoding for special character
    // Return the constructed URL
    return url;
  }

  async getFolderStructureList(
    folder: any,
  ): Promise<APIModels.FileStructureNodeResponse | undefined> {
    try {
      const url: string = `${this.configService.getAppApiURL}/folder_structure`;
      const response = await this.http
        .get<APIModels.FileStructureNodeResponse>(url)
        .toPromise();

      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  async getJupyterUrl(user_id: string): Promise<any> {
    const url = 'https://hexaind3titans02jn.corp.databrick.tech/launch_server';
    const payload = { username: user_id };
    const headers = new HttpHeaders({
      Accept: 'application/json',
      'Content-Type': 'application/json',
    });

    try {
      // Sending a POST request to launch the Jupyter notebook server
      const response = await this.http
        .post(url, payload, { headers })
        .toPromise();
      return response;
    } catch (error) {
      console.error('Error launching Jupyter notebook:', error);
      throw error;
    }
  }

  async getCustomWidgetModuleMetaData(
    siteId: any,
    project_id: any,
    module_id: any,
  ): Promise<any> {
    let url: string = `${this.configService.getAppApiURL}/assets/modules/${module_id}`;
    let metadata: any = await this.http.get(url).toPromise();
    return metadata;
  }

  async getworkflowsInWhichWidgetIsUsed(
    siteId: any,
    project_id: any,
    recipe_id: any,
  ): Promise<any> {
    let payload = { recipe_id };
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project_id}/custom_python/custom_python_widget_recipe/get_widget_details`;
    let workflowsInWhichWidgetIsUsed: any = await this.http
      .post(url, payload)
      .toPromise();
    return workflowsInWhichWidgetIsUsed;
  }

  async validateCustomWidget(
    siteId: any,
    project_id: any,
    customPythonWidgetRecipeId: any,
  ): Promise<any> {
    let params = new HttpParams().set(
      'custom_python_widget_recipe_id',
      customPythonWidgetRecipeId,
    );
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project_id}/custom_python/custom_python_widget_recipe/validate`;
    let validationResponse: any = await this.http
      .get(url, { params })
      .toPromise();
    return validationResponse;
  }

  async deleteCustomWidgetRecipe(
    siteId: any,
    project_id: any,
    customPythonWidgetRecipeId: any,
  ): Promise<any> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project_id}/custom_python/custom_code_widget/delete/${customPythonWidgetRecipeId}`;
    let validationResponse: any = await this.http.delete(url).toPromise();
  }

  async cloneCustomWidgetRecipe(
    siteId: any,
    project_id: any,
    recipe_id: any,
    recipe_name: any,
  ): Promise<any> {
    let payload = { recipe_id, recipe_name };
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project_id}/custom_python/custom_python_widget_recipe/clone`;
    await this.http.post(url, payload).toPromise();
  }

  async viewRecipeAsCustomWidget(
    siteId: any,
    project_id: any,
    customWidgetRecipe: any,
  ): Promise<any> {
    let payload = { ...customWidgetRecipe };
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${project_id}/custom_python/custom_python_widget_recipe/preview`;
    return await this.http.post(url, customWidgetRecipe).toPromise();
  }

  async uploadImages(
    files: any,
    uploadType: any,
    folderPath: any,
  ): Promise<any> {
    const url = `${this.configService.getImageDatasetUrl()}/projects/${this.configService.getProjectId()}/images/upload_images_data`;
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });

    let params: any = {};
    if (folderPath != '') {
      this.setFolderPathForAddingNewFiles(folderPath, params);
      params.upload_type = uploadType;
    }

    try {
      const response = await this.http
        .post<any>(url, files, { params })
        .toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  /**
   * this is a simple function to divide the imageFolder full path into two parts by first part being the left side of \uploaded\
   * to extract the base_folder and sub_folder parts which can used to upload different kinds of fields like metdata or adding new images
   * to existing folders.
   * @param filePath
   * @param params
   * @returns
   */
  setFolderPathForAddingNewFiles(filePath: string, params: any) {
    const index = filePath.indexOf('/uploaded/');
    if (index === -1) {
      params.sub_folder = '';
      params.base_folder = filePath;
    } else {
      params.sub_folder = filePath.slice(index + '/uploaded/'.length);
      params.base_folder = filePath.slice(0, index);
    }
  }

  async saveImageDataset(params: HttpParams): Promise<any> {
    const url = `${this.configService.getImageDatasetUrl()}/sites/1/projects/${this.configService.getProjectId()}/assets/create_dataset`;
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });
    try {
      const response = await this.http
        .post<any>(url, null, { params })
        .toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async getFolderJsonStructure(dataset_id: any) {
    const url = `${this.configService.getImageDatasetUrl()}/get_folder_struct_json`;
    const params = { dataset_id };
    const response = await lastValueFrom(this.http.get(url, { params }));
    return response;
  }

  getImageDatasetThumbnail(
    base_path: any,
    folder: any,
    image_file_name: any,
  ): Observable<any> {
    let params = { base_path, folder, image_file_name };
    const url = `${this.configService.getImageDatasetUrl()}/get_file`;
    return this.http.get(url, { responseType: 'blob', params });
  }

  async uploadImageDataToMountedDrive(
    upload_type: string,
    mountedDriveFilePaths: any,
    destinationFolder: any,
  ) {
    const url = `${this.configService.getImageDatasetUrl()}/projects/${this.configService.getProjectId()}/images/upload_images_data_from_mounted_drive`;
    let params = { upload_type };
    if (destinationFolder != '') {
      this.setFolderPathForAddingNewFiles(destinationFolder, params);
    }
    return await lastValueFrom(
      this.http.post(url, mountedDriveFilePaths, { params }),
    );
  }

  async renameImageFolder(new_name: string, base_folder: any, path: any) {
    const url = `${this.configService.getImageDatasetUrl()}/projects/${this.configService.getProjectId()}/images/rename`;
    let params = { new_name, base_folder, path };
    return await lastValueFrom(this.http.post(url, null, { params }));
  }

  async deleteImageDatasetEntity(base_folder: string, filePath: string) {
    const url = `${this.configService.getImageDatasetUrl()}/projects/${this.configService.getProjectId()}/images/delete`;
    let params = { base_folder, path: filePath };
    return await lastValueFrom(this.http.post(url, null, { params }));
  }

  async getUC2ProjectNames() {
    const url = `${this.configService.getConfigureApiUrl}/v1/uc2/get_project_names`;
    return await lastValueFrom(this.http.get(url));
  }

  async getUC2ProjectMetaData(project_name: string) {
    const url = `${this.configService.getConfigureApiUrl}/v1/uc2/get_project_metadata`;
    const params = { project_name };
    return await lastValueFrom(this.http.get(url, { params }));
  }

  async getUC2ProjectData(
    project_name: string,
    work_week_folder_name: string,
    output_column_name: string,
  ) {
    const url = `${this.configService.getConfigureApiUrl}/v1/uc2/get_project_data_with_chamber_count`;
    const params = { project_name, work_week_folder_name, output_column_name };
    return await lastValueFrom(this.http.get(url, { params }));
  }

  async getUC2ProjectResultData(
    project_name: string,
    work_week_folder_name: string,
    output_column_name: string,
    optimization_folder: string,
  ) {
    const url = `${this.configService.getConfigureApiUrl}/v1/uc2/get_project_data_with_chamber_count`;
    const params = {
      project_name,
      work_week_folder_name,
      output_column_name,
      optimization_folder,
    };
    return await lastValueFrom(this.http.get(url, { params }));
  }

  async getUC2SpcDataPoints(
    project_name: string,
    work_week_folder_name: string,
    output_column_name: string,
    chamber_ids: any,
    filter_by_feedforward: boolean,
  ) {
    const url = `${this.configService.getConfigureApiUrl}/v1/uc2/get_spc_charts_data`;
    // ?project_name=${project_name}
    // &work_week_folder_name=${work_week_folder_name}&output_column_name=${output_column_name}&
    // chamber_ids=${chamber_ids}&filter_by_feedforward=${filter_by_feedforward}`;
    const params = {
      project_name,
      work_week_folder_name,
      output_column_name,
      chamber_ids,
      filter_by_feedforward,
    };
    return await lastValueFrom(this.http.get(url, { params }));
  }

  async fetchUC2ResultsUsingFilteredData(selectedProjectData: any) {
    const url = `${this.configService.getAppApiURL}/uc2_results_aggregator/filter`;
    return await lastValueFrom(this.http.post(url, selectedProjectData));
  }

  async getUC2DataAggregationPaginatedData(file_path: string, page: any) {
    const url = `${this.configService.getAppApiURL}/uc2_results_aggregator/preview`;
    let params = { file_path, page, page_size: 50 };
    return await lastValueFrom(this.http.get(url, { params }));
  }

  async getUC2PlotsData(
    project_name: string,
    work_week_folder_name: string,
    output_column_name: string,
    optimization_folder: string,
    subfolder: any,
  ) {
    const url = `${this.configService.getConfigureApiUrl}/v1/uc2/get_siso_plots`;
    const params = {
      project_name,
      work_week_folder_name,
      output_column_name,
      optimization_folder,
      subfolder,
    };
    return await lastValueFrom(this.http.get(url, { params }));
  }

  async StopServer(project_id: any): Promise<any> {
    let url: string = `${this.configService.getApiUrl}/projects/${project_id}/jupyter/hub/server/run`;
    let validationResponse: any = await this.http.delete(url).toPromise();
    return validationResponse;
  }

  async StartServer(project_id: any): Promise<any> {
    let url: string = `${this.configService.getApiUrl}/projects/${project_id}/jupyter/hub/server/run`;
    let validationResponse: any = await this.http.post(url, {}).toPromise();
    return validationResponse;
  }

  async DeleteServer(project_id: any): Promise<any> {
    let url: string = `${this.configService.getApiUrl}/projects/${project_id}/jupyter/hub/server`;
    let validationResponse: any = await this.http.delete(url).toPromise();
    return validationResponse;
  }

  async createJNB_folders(project_id: any, user_id: any): Promise<any> {
    let url: string = `${this.configService.getApiUrl}/projects/${project_id}/jupyter/hub/server/create_folders`;
    let validationResponse: any = await this.http.post(url, {}).toPromise();
    return validationResponse;
  }

  getAggregatedConfig(projectId: any): Observable<any> {
    const url: string = `${this.configService.getConfigureApiUrl}/v1/uc1/projects/${projectId}/get_aggregated_config`;
    return this.http.get<any>(url).pipe(
      map((response) => {
        return {
          allTrainedDids: response.all_trained_dids,
          uniqueIds: response.unique_ids,
          modelsMap: response.models_map,
        };
      }),
      catchError((error: HttpErrorResponse) => {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error('Error fetching aggregated config:', error);
        return throwError(error);
      }),
    );
  }

  getPredictionData(projectId: string): Observable<any> {
    const url: string = `${this.configService.getConfigureApiUrl}/v1/uc1/projects/${projectId}/get_prediction_config`;
    return this.http.get<any>(url).pipe(
      map((response) => {
        return {
          // Transform the response as needed
          ...response,
        };
      }),
      catchError((error: HttpErrorResponse) => {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error('Error fetching prediction data:', error);
        return throwError(error);
      }),
    );
  }

  getTrainData(projectId: string): Observable<any> {
    const url: string = `${this.configService.getConfigureApiUrl}/v1/uc1/projects/${projectId}/get_train_config`;
    return this.http.get<any>(url).pipe(
      map((response) => {
        console.log(response, 'get rersponse train data');
        return {
          // Transform the response as needed
          ...response,
        };
      }),
      catchError((error: HttpErrorResponse) => {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error('Error fetching train data:', error);
        return throwError(error);
      }),
    );
  }

  uploadFile(formData: FormData, tab: string): Observable<any> {
    const url: string = `${this.configService.getConfigureApiUrl}/v1/uc1/projects/upload_files?folder_path_suffix=saa`;
    return this.http.post<any>(url, formData).pipe(
      catchError((error: HttpErrorResponse) => {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error('Error uploading file:', error);
        return throwError(error);
      }),
    );
  }

  saveDidConfig(configData: any, projectId: any): Observable<any> {
    const url = `${this.configService.getConfigureApiUrl}/v1/uc1/projects/${projectId}/set_train_config`;
    return this.http.post(url, configData);
  }

  savePredictionConfig(configData: any, projectId: any): Observable<any> {
    const url = `${this.configService.getConfigureApiUrl}/v1/uc1/projects/${projectId}/set_prediction_config`;
    return this.http.post(url, configData);
  }

  generateRandomId(length: number): string {
    const characters =
      'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      const randomIndex = Math.floor(Math.random() * characters.length);
      result += characters[randomIndex];
    }
    return result;
  }

  async GetUploadConfigFiles(
    file: File,
    projectId: any,
    siteId: any,
  ): Promise<any> {
    const randomId = this.generateRandomId(8); // Generate a random ID of length 8
    const url = `${this.configService.getConfigureApiUrl}/v1/uc1/projects/${projectId}/upload_files?folder_path_suffix=${randomId}`;
    const formData = new FormData();
    formData.append('files', file, file.name);
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });
    try {
      const response = await this.http
        .post<APIModels.GetFilesPostResponse>(url, formData, { headers })
        .toPromise();
      if (response) {
        console.log(response, 'response get input');
        return response;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetUploadFiles() failed' +
            this.sharedDataService.LastError,
        );
      }
    }
  }

  async GetUploadPredictionConfigFiles(
    file: File,
    projectId: any,
    siteId: any,
  ): Promise<any> {
    const randomId = this.generateRandomId(8); // Generate a random ID of length 8
    const url = `${this.configService.getConfigureApiUrl}/v1/uc1/projects/${projectId}/upload_files/predictions?folder_path_suffix=${randomId}`;
    const formData = new FormData();
    formData.append('files', file, file.name);
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });
    try {
      const response = await this.http
        .post<APIModels.GetFilesPostResponse>(url, formData, { headers })
        .toPromise();
      if (response) {
        console.log(response, 'response get input');
        return response;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetUploadFiles() failed' +
            this.sharedDataService.LastError,
        );
      }
    }
  }

  async getAppendMismatches(datasetId: any) {
    const url = `${this.configService.getConfigureApiUrl}/v1/workflows/widgets/append/get_append_mismatches`;
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });
    try {
      const response = await this.http
        .post<APIModels.GetFilesPostResponse>(url, datasetId, { headers })
        .toPromise();
      if (response) {
        console.log(response, 'response get input');
        return response;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'API getAppendMismatches() failed' + this.sharedDataService.LastError,
        );
      }
    }
    return;
  }

  async getTechnodeId(inputs: any) {
    const url = `${this.configService.getConfigureApiUrl}/micron/data_catalog/fd/tech_nodes`;
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });
    try {
      const response = await this.http
        .post<string>(url, inputs, { headers })
        .toPromise();
      if (response) {
        console.log(response, 'response get input');
        return response;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'API getAppendMismatches() failed' + this.sharedDataService.LastError,
        );
      }
    }
    return;
  }

  getTechNodes(projectId: string): Observable<any> {
    const url: string = `${this.configService.getConfigureApiUrl}/micron/data_catalog/${projectId}`;
    return this.http.get<any>(url).pipe(
      map((response) => {
        console.log(response, 'get rersponse train data');
        return {
          // Transform the response as needed
          ...response,
        };
      }),
      catchError((error: HttpErrorResponse) => {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error('Error fetching tech nodes:', error);
        return throwError(error);
      }),
    );
  }

  async duplicateWorkflow(
    siteId: any,
    projectId: any,
    sessionId: any,
    type: any,
    data: any,
  ): Promise<any> {
    const url = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/duplication/${type}`;
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });
    try {
      const response = await this.http
        .post<any>(url, data, { headers })
        .toPromise();
      if (response) {
        return response;
      } else {
        console.error('No response');
        return null;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  async exportWorkflowData(
    siteId: any,
    projectId: any,
    sessionId: any,
    type: any,
    exportData: any,
  ): Promise<Blob> {
    const url = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/export/${type}`;
    const headers = new HttpHeaders({
      Accept: 'application/zip',
    });
    try {
      const response = await this.http
        .post<Blob>(url, exportData, {
          headers,
          responseType: 'blob' as 'json',
        })
        .toPromise();
      if (response) {
        console.log('Workflow exported successfully.');
        return response; // Return Blob to handle the ZIP download
      } else {
        console.error('No response received from export API');
        throw new Error('Export failed.');
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
      throw error || new Error('Unknown error during export.');
    }
  }

  async importWorkflowData(
    siteId: string,
    projectId: string,
    zipFile: File,
    importData: any,
  ): Promise<void> {
    const url = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/import/workflow`;
    const formData = new FormData();
    formData.append('zip_file', zipFile);
    // Append additional form data required by the backend
    formData.append('user_id', importData.user_id);
    formData.append('user_name', importData.user_name);
    formData.append('workflow_name', importData.workflow_name);
    formData.append('workflow_description', importData.workflow_description);
    formData.append('token', importData.token);
    console.log(importData);
    try {
      await this.http.post(url, formData).toPromise();
      console.log('Workflow imported successfully to target project.');
    } catch (error) {
      console.error('Error importing workflow data:', error);
      throw error;
    }
  }

  async GetWorkflowTemplates(siteId: string, projectId: string): Promise<any> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/templates`;
      let templates: any = await this.http.get(url).toPromise();
      return templates;
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
    }
    return undefined;
  }

  async GetPreviousTabularWidgetResults(
    siteId: any,
    projectId: any,
    sessionId: any,
    widgetURN: any,
  ): Promise<any> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/run/widget/${widgetURN}/results`;
      let widgetResults: any = await this.http.get(url).toPromise();
      return widgetResults;
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw new Error('Failed to get previous widget results');
      }
    }
    return undefined;
  }

  async getTabularInputFields(
    site_id: string,
    project_id: string,
    datasetId: any,
  ): Promise<any | undefined> {
    let response: string | undefined = undefined;
    try {
      let url: string = `${this.configService.getAuxApiUrl}/${site_id}/projects/${project_id}/eda/statistics?dataset_id=${datasetId}`;
      const response = await this.http.get(url).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
    return undefined;
  }

  getPermissions(site_id: string): Observable<any> {
    try {
      let url: string = `${this.configService.getApiUrl}/${site_id}/get_all_apps_permissions`;
      let response = this.http.get(url);
      return response;
    } catch (error: any) {
      this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      console.error('Error fetching tech nodes:', error);
      return throwError(error);
    }
  }

  updatePermissions(site_id: string, payload: any): Observable<any> {
    try {
      let url: string = `${this.configService.getApiUrl}/${site_id}/update_app_permissions`;
      let response = this.http.post(url, payload);
      return response;
    } catch (error: any) {
      this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      console.error('Error fetching tech nodes:', error);
      return throwError(error);
    }
  }

  getImageDatasets(siteId: string, projectId: any): Observable<any> {
    try {
      let url = `${this.configService.getImageDatasetUrl()}/sites/${siteId}/projects/${projectId}/image_datasets`;
      return this.commonApiService.get_api(url);
    } catch (error: any) {
      this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      console.error('Error fetching tech nodes:', error);
      return throwError(error);
    }
  }

  async updateStatusModal(
    site_id: string,
    selectStatus: any,
    project_name: string,
    work_week_folder_name: string,
    output_column_name: string,
    start_date: string,
    end_date: string,
    interval: number | null,
    chamber_id: string,
    optimization_folder: string,
  ) {
    const statusValue = selectStatus ? 'Active' : 'InActive'; // Determine the status value

    // Payload with status
    const payload = {
      status: statusValue, // Status is already included in the payload
    };

    // Include all parameters, including interval and chamber_id, in HttpParams
    const params = new HttpParams()
      .set('project_name', project_name)
      .set('work_week_folder_name', work_week_folder_name)
      .set('output_column_name', output_column_name)
      .set('start_date', start_date) // Add start_date
      .set('end_date', end_date) // Add end_date
      .set('status', statusValue) // Add status (Active or InActive)
      .set('interval', interval?.toString() || '') // Add interval (convert to string)
      .set('chamber_id', chamber_id)
      .set('Optimization_folder', optimization_folder); // Add chamber ID

    const url = `${this.configService.getConfigureApiUrl}/v1/uc2/update_chamber_status`;
    const headers = new HttpHeaders({
      Accept: 'application/json',
    });

    try {
      const response = await this.http
        .post<any>(url, payload, { headers, params }) // Pass both payload and params
        .toPromise();

      if (response) {
        return response;
      } else {
        console.error('No response');
        return null;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        throw error;
      }
    }
  }

  toggleFavoriteForWorkflow(
    siteId: string,
    projectId: string,
    user_id: string,
    is_favourite: boolean,
    workflow_id: string,
  ): Observable<any> {
    // {  "workflow_id": "string",  "user_id": "string",  "is_favourite": true }
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/update_favourite`;
    let data = {
      user_id: user_id,
      workflow_id: workflow_id,
      is_favourite: is_favourite,
    };
    return this.http.post(url, data, {
      headers: this.tokenHeaders,
      observe: 'response',
    });
  }

  async getUC3DashboardWorkflows() {
    const url = `${this.configService.getAppAuxApiURL}/uc3/get_workflow_names`;
    return await lastValueFrom(this.http.get(url));
  }

  async getUC3DashboardRuns(workflow_id: any) {
    const url = `${this.configService.getAppAuxApiURL}/uc3/get_runs_for_workflow`;
    let params = { workflow_id };
    return await lastValueFrom(this.http.get(url, { params }));
  }

  async getUC3DashboardMetadata(run_id: any) {
    const url = `${this.configService.getAppAuxApiURL}/uc3/get_dashboard_metadata`;
    let params = { run_id };
    return await lastValueFrom(this.http.get(url, { params }));
  }

  async getUC3DashboardStepPlotPaths(
    step_name: any,
    feature_name: any,
    run_id: any,
  ) {
    const url = `${this.configService.getAppAuxApiURL}/uc3/get_tool_recipe_plots`;
    let params = { step_name, feature_name, run_id };
    return await lastValueFrom(this.http.get(url, { params }));
  }

  downloadZipByPath(payload: any): Observable<any> {
    const url: string = `${this.configService.getAppAuxApiURL}/download_asset`;
    return this.http.post(url, payload, {
      responseType: 'blob',
    });
  }

  UploadMultipleFiles(
    files: any,
    siteId: string,
    projectId: string,
    workflowId: string,
    name: string,
    description: string,
    access_mode: string,
    file_type: string,
    onProgress: (progress: number) => void,
  ): Observable<any> {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      const extension = file.name.split('.').pop()?.toLowerCase();
      formData.append('file', file);
    }
    var user: any = JSON.parse(localStorage.getItem('currentUser')!);
    console.log(user['access_token']);

    let query = `name=${encodeURIComponent(
      name,
    )}&description=${encodeURIComponent(
      description,
    )}&file_type=${file_type}&access_mode=${encodeURIComponent(
      access_mode,
    )}&workflow_id=${encodeURIComponent(
      workflowId,
    )}&dataset_type=${encodeURIComponent(
      file_type,
    )}&upload_type=${encodeURIComponent('WORKFLOWS')}`;
    const url: string = `${this.configService.getAppAuxApiURL}/assets/dataset/upload/multiple_text_file?${query}`;
    return this.http
      .post(url, formData, {
        reportProgress: true,
        observe: 'events',
      })
      .pipe(
        map((event: any) => {
          switch (event.type) {
            case HttpEventType.UploadProgress:
              if (event.total) {
                const percentDone = Math.round(
                  (99 * event.loaded) / event.total,
                );
                onProgress(percentDone);
              }
              break;
            case HttpEventType.Response:
              onProgress(100);
              return event.body;
          }
        }),
        catchError((error: HttpErrorResponse) => {
          console.error('Upload failed:', error.message);
          throw error;
        }),
      );
  }

  async getCPWPythonFileContent(widget_id: any) {
    const url = `${this.configService.getAppApiURL}/custom_python/file/${widget_id}`;
    return await lastValueFrom(this.http.get(url));
  }

  async updateCPWPythonFileContent(widget_id: any, body: any) {
    const url = `${this.configService.getAppApiURL}/custom_python/file/${widget_id}`;
    return await lastValueFrom(this.http.put(url, body));
  }

  async replaceTheModuleFilePath(widget_id: any, filepath: any) {
    const url = `${this.configService.getAppApiURL}/custom_python/file/update/${widget_id}`;
    return await lastValueFrom(this.http.post(url, { filepath }));
  }

  SupersetConnection(): string {
    const apiUrl = `${this.configService.getBasicDataApiUrl}/explore_data`;
    return apiUrl;
  }

  fetchDataWithToken() {
    const apiUrl = this.SupersetConnection(); // Get the URL
    const token = this.getAccessToken(); // Get the access token

    // Add token as query parameter
    //return `${apiUrl}?token=${token}`;
    // Append the token to the URL as a query parameter
    const tokenWithUrl = `${apiUrl}?token=${token}`; // Add token to the URL

    // Make the HTTP GET request with the token in the URL
    return this.http.get(tokenWithUrl); // No need for headers, as token is part of the URL
  }

  launchServer(
    payload: any,
    project_id: any,
    workflow_id: any,
    run_id: any,
  ): Observable<any> {
    try {
      // Construct base URL
      let url: string = `${this.configService.getBasicDataApiUrl}/widget/servers/${project_id}/${workflow_id}`;

      // Append run_id if it exists
      if (run_id) {
        url += `?run_id=${run_id}`;
      }

      console.log('API URL:', url);
      console.log('Payload:', payload);

      let response = this.http.post(url, payload);
      return response;
    } catch (error: any) {
      this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      console.error('Error launching server:', error);
      return throwError(error);
    }
  }

  GetServerfiles(project_id: any, workflow_id: any): Observable<any> {
    try {
      let url: string = `${this.configService.getBasicDataApiUrl}/widget/notebooks/${project_id}/${workflow_id}`;
      let response = this.http.get(url);
      console.log(response, "response get api's");
      return response;
    } catch (error: any) {
      this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      console.error('Error fetching tech nodes:', error);
      return throwError(error);
    }
  }
}
