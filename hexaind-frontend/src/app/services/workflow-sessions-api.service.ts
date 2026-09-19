import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ConfigService } from './config.service';
import * as SessionApiModels from '../models/workflow-sessions-api-response.models';
import { SharedDataService } from './shared services/shared-data.service';
import { Utils } from '../utils';
import { DatasetModel, Widget, WidgetType, Workflow, WorkflowState } from '../models/workflow-models';
import { ActivityLogResponse, GetWorkflowResponse } from '../models/api-models';
import { from, Observable, of } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';



interface ApiResponse {
  sessions: SessionApiModels.WorkflowSession[];
  invalid_session_ids: string[];
}
@Injectable({
  providedIn: 'root',
})
export class WorkflowsSessionsApiService {
  constructor(
    private http: HttpClient,
    private configService: ConfigService,
    private sharedDataService: SharedDataService,
  ) { }

  async GetWorkflowSessionWidgetActivityLog(
    siteId: string,
    projectId: string,
    sessionId: string,
    widgetUrn: string,
    nextCursorTimeStamp: string | undefined,
    nextCursorRecordId: string | undefined,
  ): Promise<ActivityLogResponse | undefined> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/widget/${widgetUrn}/activity_log?size=50`;
      if (
        nextCursorTimeStamp !== undefined &&
        nextCursorRecordId !== undefined
      ) {
        url += `&next_cursor_timestamp=${nextCursorTimeStamp}&next_cursor_record_id=${nextCursorRecordId}`;
      }
      let log: ActivityLogResponse | undefined = await this.http
        .get<ActivityLogResponse>(url)
        .toPromise();
      return log;
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
      }
    }
    return undefined;
  }

  async GetWorkflowSessions(
    siteId: string,
    projectId: string,
  ): Promise<SessionApiModels.WorkflowSession[]> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/session?page_limit=100&page_number=1&get_updated_details=true`;
      let response = await this.http
        .get<SessionApiModels.WorkflowSessions>(url)
        .toPromise();

      return response!.sessions.sort((a, b) => {
        let dateA = new Date(a.created_at!);
        let dateB = new Date(b.created_at!);
        return dateB.getTime() - dateA.getTime(); // Ascending order
      });
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetSessions() failed: ' +
          this.sharedDataService.LastError,
        );
      }
    }
    return [];
  }

  async GetInvalidWorkflowSessions(
    siteId: string,
    projectId: string,
  ): Promise<ApiResponse> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/session?page_limit=100&page_number=1&get_updated_details=true`;
      let response = await this.http
        .get<ApiResponse>(url)
        .toPromise();

      // Ensure response is not undefined
      if (response) {
        return response;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetWorkflowSessions() failed: ' +
          this.sharedDataService.LastError,
        );
      }
    }

    // Default response in case of error or undefined response
    return { sessions: [], invalid_session_ids: [] };
  }

  async GetWorkflowById(
    siteId: string,
    projectId: string,
    workflowId: string,
  ): Promise<Workflow | undefined> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/${workflowId}`;
      let workflow: Workflow | undefined = await this.http
        .get<Workflow>(url)
        .toPromise();
      return workflow;
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetWorkflowById() failed: ' +
          this.sharedDataService.LastError,
        );
      }
    }
    return undefined;
  }

  async GetWorkflowByRunId(
    siteId: string,
    projectId: string,
    workflowId: string,
    run_id: string | undefined
  ): Promise<Workflow | undefined> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/${workflowId}/run/${run_id}/status`;
      let response = await this.http.get<any>(url).toPromise();
      if (response && response.workflow) {
        return response.workflow;
      }
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetWorkflowById() failed: ' +
          this.sharedDataService.LastError,
        );
      }
    }
    return undefined;
  }

  async GetWorkflowSession(
    siteId: string,
    projectId: string,
    sessionId: string,
  ): Promise<SessionApiModels.WorkflowSession | undefined> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/session/${sessionId}`;
      let session = await this.http
        .get<SessionApiModels.WorkflowSession>(url)
        .toPromise();

      return session;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetSession() failed: ' +
          this.sharedDataService.LastError,
        );
      }
      throw error;
    }
  }

  async GetVersionedWorkflowStatus(
    siteId: string,
    projectId: string,
    workflowId: string,
    run_id: string | undefined
  ): Promise<any> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/${workflowId}/run/${run_id}/status`;
      let response = await this.http.get<any>(url).toPromise();
      if (response) {
        return response;
      }
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetWorkflowById() failed: ' +
          this.sharedDataService.LastError,
        );
      }
    }
    return undefined;
  }

  async DeleteWorkflowSession(
    siteId: string,
    projectId: string,
    sessionId: string,
  ): Promise<string | undefined> {
    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/session/${sessionId}`;
      let session = await this.http.delete<string>(url).toPromise();
      return session!;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API DeleteSession() failed: ' +
          this.sharedDataService.LastError,
        );
      }
    }
    return undefined;
  }

  deleteWorkflow(workflowId: string): any {
    let url = `${this.configService.getAppApiURL}/workflow/${workflowId}`;
    return this.http.delete<string>(url).toPromise();
  }

  async CreateWorkflowSession(
    siteId: string,
    projectId: string,
    version: string,
    name: string,
    description: string,
    ownerId: string,
    ownerName: string,
  ): Promise<string | undefined> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/session`;
    try {
      let sessionCreateBody: SessionApiModels.WorkflowSessionCreateUpdateBody =
        new SessionApiModels.WorkflowSessionCreateUpdateBody(
          version,
          name,
          description,
          ownerId,
          ownerName,
        );
      let response = await this.http
        .post<SessionApiModels.SessionCreateResponse>(url, sessionCreateBody)
        .toPromise();
      return response!.session_id;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API CreateSession() failed: ' +
          this.sharedDataService.LastError,
        );
      }
      throw error;
    }
    return undefined;
  }

  async UpdateWorkflowSession(
    siteId: string,
    projectId: string,
    sessionId: string,
    version: string,
    name: string,
    description: string,
    ownerId: string,
    ownerName: string,
  ): Promise<boolean> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/session/${sessionId}`;
    try {
      let sessionCreateBody: SessionApiModels.WorkflowSessionCreateUpdateBody =
        new SessionApiModels.WorkflowSessionCreateUpdateBody(
          version,
          name,
          description,
          ownerId,
          ownerName,
        );
      await this.http
        .put<SessionApiModels.SessionCreateResponse>(url, sessionCreateBody)
        .toPromise();
      return true;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API UpdateSession() failed: ' +
          this.sharedDataService.LastError,
        );
        throw error;
      }
    }
    return false;
  }

  async SaveSessionWorkflow(
    siteId: string,
    projectId: string,
    sessionId: string,
    sessionWorkflow: SessionApiModels.SessionWorkflow,
  ): Promise<any> {

    try {
      let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/save`;
      let response = await this.http
        .post<string>(url, sessionWorkflow)
        .toPromise();
      return response;
    } catch (error: any) {
      if (error.error.missing_fields?.length != 0) {
        let messageString = ""
        let isWidgetMissingFieldsError = true
        error.error.missing_fields.forEach((missingField: any) => {
          messageString += missingField + " "
        })
        this.sharedDataService.LastError = messageString
        throw { messageString, isWidgetMissingFieldsError };
      }
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API SaveSessionWorkflow() failed: ' +
          this.sharedDataService.LastError,
        );
        throw error;
      }
    }
    return undefined;
  }

  async PublishSessionWorkflow(
    siteId: string,
    projectId: string,
    sessionId: string,
    sessionSaveAsWorkflow: SessionApiModels.SessionSaveAsWorkflow,
  ): Promise<string | undefined> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/saveas`;
    try {
      let response = await this.http
        .post<SessionApiModels.SaveAsSessionWorkflowPostResponseClass>(
          url,
          sessionSaveAsWorkflow,
        )
        .toPromise();
      return response?.workflow_id;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API SaveAsSessionWorkflow() failed: ' +
          this.sharedDataService.LastError,
        );
        throw error;
      }
    }
    return undefined;
  }

  async RunSessionWorkflow(
    siteId: string,
    projectId: string,
    sessionId: string,
    rerunCompletedWidgets: boolean,
  ): Promise<string | undefined> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/run`;
    try {
      let body = { rerun_completed_widgets: rerunCompletedWidgets };
      let response = await this.http.post<string>(url, body).toPromise();
      console.log(response);
      return response;
    } catch (error: any) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API RunSession() failed: ' +
          this.sharedDataService.LastError,
        );
      }
      throw error;
    }
    return undefined;
  }

  async StopSessionRun(
    siteId: string,
    projectId: string,
    sessionId: string,
    stopParams: { run_id?: string; stop_all?: boolean; stop_pending?: boolean; user_id?: string } = {}
  ): Promise<boolean> {
    this.sharedDataService.LastError = null;
    // let status: SessionApiModels.WorkflowRunStatus | undefined = await this.GetWorkflowSessionRunStatus(siteId, projectId, sessionId);
    // if (status) {
    //   if (
    //     status.run_status !== WorkflowState.RUNNING &&
    //     status.run_status !== WorkflowState.PAUSED
    //   ) {
    //     return false;
    //   }
    // }

    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/stop`;
    try {
      await this.http.post<string>(url, stopParams).toPromise();
      return true;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API StopSessionRun() failed: ' +
          this.sharedDataService.LastError,
        );
        return false;
      }
    }
    return true;
  }

  async RunWidget(
    siteId: string,
    projectId: string,
    sessionId: string,
    widgetUrn: string,
  ): Promise<boolean> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/widget/${widgetUrn}/run`;
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

  async StopWidgetRun(
    siteId: string,
    projectId: string,
    sessionId: string,
    widgetUrn: string,
  ): Promise<string | undefined> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/widget/${widgetUrn}/stop`;
    try {
      let response = await this.http.post<string>(url, {}).toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API StopWidgetRun() failed: ' +
          this.sharedDataService.LastError,
        );
      }
    }
    return undefined;
  }

  async GetWorkflowSessionRunStatus(
    siteId: string,
    projectId: string,
    sessionId: string,
  ): Promise<SessionApiModels.WorkflowRunStatus | undefined> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/run/status`;
    try {
      let response = await this.http
        .get<SessionApiModels.WorkflowRunStatus>(url, {})
        .toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetSessionRunStatus() failed: ' +
          this.sharedDataService.LastError,
        );
      }
    }
    return undefined;
  }

  async GetDatasetIdFromWidgetRunResult(
    isVersioned: boolean,
    siteId: string,
    projectId: string,
    workflowId: string,
    runId: string,
    sessionId: string,
    widgetUrn: string,
  ): Promise<string | undefined> {
    let runResult: SessionApiModels.WidgetRunResult[] = [];
    if (isVersioned) {
      runResult = await this.GetVersionedWorkflowWidgetRunStatus(
        siteId,
        projectId,
        workflowId,
        runId,
        widgetUrn,
      );
    } else {
      runResult = await this.GetWorkflowSessionWidgetRunStatus(
        siteId,
        projectId,
        sessionId,
        widgetUrn,
      );
    }

    switch (runResult[0].result_type) {
      case SessionApiModels.ActionResultType.DATASET:
        let result: SessionApiModels.DatasetWidgetResult = runResult[0]
          .result_value as SessionApiModels.DatasetWidgetResult;
        return result._id;
      default:
        return undefined;
    }
  }

  async GetDatasetIdsFromWidgetRunResult(
    isVersioned: boolean,
    siteId: string,
    projectId: string,
    workflowId: string,
    runId: string,
    sessionId: string,
    widgetUrn: string,
  ): Promise<DatasetModel[] | undefined> {
    let runResults: SessionApiModels.WidgetRunResult[] = [];
    if (isVersioned) {
      runResults = await this.GetVersionedWorkflowWidgetRunStatus(
        siteId,
        projectId,
        workflowId,
        runId,
        widgetUrn,
      );
    } else {
      runResults = await this.GetWorkflowSessionWidgetRunStatus(
        siteId,
        projectId,
        sessionId,
        widgetUrn,
      );
    }

    let datasetIds: DatasetModel[] = [];

    for (let runResult of runResults) {
      if (runResult.result_type === SessionApiModels.ActionResultType.DATASET) {
        let result: any = runResult
          .result_value;
        if (result._id && result.name) {
          datasetIds.push(new DatasetModel(result.name, result._id))
        }
      }
    }

    return datasetIds;
  }

  async GetResultCPWFromWidgetRunResult(
    isVersioned: boolean,
    siteId: string,
    projectId: string,
    workflowId: string,
    runId: string,
    sessionId: string,
    widgetUrn: string,
  ): Promise<any | undefined> {
    let runResult: SessionApiModels.WidgetRunResult[] = [];
    if (isVersioned) {
      runResult = await this.GetVersionedWorkflowWidgetRunStatus(
        siteId,
        projectId,
        workflowId,
        runId,
        widgetUrn,
      );
    } else {
      runResult = await this.GetWorkflowSessionWidgetRunStatus(
        siteId,
        projectId,
        sessionId,
        widgetUrn,
      );
    }

    switch (runResult[0].result_type) {
      case SessionApiModels.ActionResultType.VISUALIZATION:
        return runResult;
      default:
        return undefined;
    }
  }


  async GetVersionedWorkflowWidgetRunStatus(
    siteId: string,
    projectId: string,
    workflowId: string,
    runId: string,
    widgetUrn: string,
  ): Promise<SessionApiModels.WidgetRunResult[]> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/workflow/${workflowId}/run/${runId}/widget/${widgetUrn}/result`;
    try {
      let response = await this.http
        .get<SessionApiModels.WidgetRunResult[]>(url, {})
        .toPromise();
      if (!response) {
        return [];
      }
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetWidgetRunStatus() failed: ' +
          this.sharedDataService.LastError,
        );
      }
    }
    return [];
  }

  async GetWorkflowSessionWidgetRunStatus(
    siteId: string,
    projectId: string,
    sessionId: string,
    widgetUrn: string,
  ): Promise<SessionApiModels.WidgetRunResult[]> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/run/widget/${widgetUrn}/results`;
    try {
      let response = await this.http
        .get<SessionApiModels.WidgetRunResult[]>(url, {})
        .toPromise();
      if (!response) {
        return [];
      }
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetWidgetRunStatus() failed: ' +
          this.sharedDataService.LastError,
        );
      }
    }
    return [];
  }

  async CreateWorkflowTemplate(
    siteId: string,
    projectId: string,
    sessionId: string,
    payload: any,
    screenshot: Blob
  ): Promise<string | undefined> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/sessions/${sessionId}/workflow/template`;
    try {
      const formData = new FormData();
      formData.append('file', screenshot, 'screenshot.png');
      for (const key in payload) {
        if (payload.hasOwnProperty(key)) {
          formData.append(key, payload[key]);
        }
      }
      // Define the headers
      const headers = new HttpHeaders({
        // 'Content-Type': 'multipart/form-data' // This is usually not necessary
      });
      let response = await this.http
        .post<any>(url, formData)
        .toPromise();
      return response!.workflow_id;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Save workflow as template failed: ' +
          this.sharedDataService.LastError,
        );
      }
      throw error;
    }
    return undefined;
  }

  async GetWorkflowTemplates(
    siteId: string,
    projectId: any,
  ): Promise<any> {
    let url: string = `${this.configService.getApiUrl}/${siteId}/projects/${projectId}/templates?page_limit=100&page_number=1&get_updated_details=false`;
    try {
      let response = await this.http
        .get<any>(url, {})
        .toPromise();
      return response;
    } catch (error) {
      if (error instanceof HttpErrorResponse) {
        this.sharedDataService.LastError = Utils.GetHttpResponseError(error);
        console.error(
          'Call to API GetWorkflowTemplates() failed: ' +
          this.sharedDataService.LastError,
        );
      }
    }
    return undefined;
  }
  getTemplateImageContent(file: any): Observable<any | null> {
    const url = `${this.configService.getApiUrl}/1/projects/${this.configService.SelectedProjectId}/assets/read_file_content`;
    return this.http
      .post(
        url,
        { file_path: file.path, file_name: file.name },
        { observe: 'response', responseType: 'blob' },
      )
      .pipe(
        map((response) => {
          if (response.body) {
            const objectURL = URL.createObjectURL(response.body);
            return objectURL;
          } else {
            return null;
          }
        }),
        catchError((error) => {
          return of(null);
        }),
      );
  }

  getWorkflowResults(
    siteId: string,
    projectId: string,
    sessionId: string,
  ): Observable<any> {

    return from(this.GetWorkflowSessionRunStatus(siteId, projectId, sessionId));
  }


}
