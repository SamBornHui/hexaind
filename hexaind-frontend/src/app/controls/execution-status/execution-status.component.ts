import { Component, Input } from '@angular/core';
import {
  ConfigService,
  WorkflowCanvasService,
} from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ApiService } from 'src/app/services/api.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { ActivityLog, ActivityLogResponse } from 'src/app/models/api-models';
import {
  ActionResultType,
  DatasetWidgetResult,
  FailureActionResult,
  JSONActionResult,
  StringActionResult,
  StringListActionResult,
  WidgetRunResult,
} from 'src/app/models/workflow-sessions-api-response.models';
import { MatTableDataSource } from '@angular/material/table';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';


@Component({
  selector: 'app-execution-status',
  templateUrl: './execution-status.component.html',
  styleUrls: ['./execution-status.component.less'],
})
export class ExecutionStatusComponent {
  @Input() widgetUrn: string | undefined = undefined;

  isExpanded: boolean = false;
  dataSource!: MatTableDataSource<ActivityLog>;

  displayedColumns: string[] = ['Time', 'Log Level', 'exc_info', 'Message'];
  widgetRunResults: WidgetRunResult[] = [];
  lastActivityLogResponse: ActivityLogResponse | undefined = undefined;
  moreLogs: boolean = true;
  widgetResultApiCalled: boolean = false;
  isDownloading: boolean = false;

  constructor(
    private apiService: ApiService,
    private configService: ConfigService,
    private workflowsSessionsApiService: WorkflowsSessionsApiService,
    public sharedDataService: SharedDataService,
    public workflowCanvasService: WorkflowCanvasService,
    private errorHandlerService: ErrorHandlerService
  ) { }

  ngOnInit() {
    this.dataSource = new MatTableDataSource<ActivityLog>();
    this.getActivityLog();
    this.getWidgetRunResult();
  }
  fetchWidgetRunResult() {
    return this.widgetRunResults;
  }

  getIndividualWidgetRunResults(): string | undefined {
    if (this.widgetRunResults.length && this.widgetRunResults[0]) {
      switch (this.widgetRunResults[0].result_type) {
        case ActionResultType.DATASET:
          let result: DatasetWidgetResult = this.widgetRunResults[0].result_value as DatasetWidgetResult;
          return result.output_name;
        case ActionResultType.FAILURE:
          return (this.widgetRunResults[0].result_value as FailureActionResult).error_description;
        case ActionResultType.STRING:
          return (this.widgetRunResults[0].result_value as StringActionResult).string_value;
        case ActionResultType.JSON:
          return (this.widgetRunResults[0].result_value as JSONActionResult).json_value;
        case ActionResultType.STRINGS_LIST:
          return (this.widgetRunResults[0].result_value as StringListActionResult).strings_list_value.length > 0
            ? (this.widgetRunResults[0].result_value as StringListActionResult).strings_list_value[
            (this.widgetRunResults[0].result_value as StringListActionResult).strings_list_value.length - 1
            ]
            : '';
      }
    }
    return 'Not available yet';
  }

  isZipPath(content: string | undefined) {
    if (content) {
      return (content.endsWith('.zip')) ? true : false;
    } else {
      return false;
    }
  }

  async onDownloadZip(path: string | undefined) {
    if (path) {
      this.isDownloading = true;
      let fileName = 'vpsc_result.zip'
      this.apiService.downloadZipByPath({ source: path })
        .subscribe({
          next: (blob: Blob) => this.handleBlob(blob, fileName),
          error: (error: any) => {
            this.isDownloading = false;
            this.errorHandlerService.handleError(error);
          },
        });
    }
  }

  private handleBlob(blob: Blob, fileName: string) {
    const blobUrl = window.URL.createObjectURL(blob);
    this.triggerDownload(blobUrl, fileName);
  }

  private triggerDownload(blobUrl: string, fileName: string) {
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(blobUrl);
    link.remove();
    this.isDownloading = false;
  }

  async getWidgetRunResult() {
    this.workflowCanvasService.setWidgetRunResults([])
    if (this.workflowCanvasService.IsVersionedWorkflow) {
      try {
        this.widgetRunResults =
          await this.workflowsSessionsApiService.GetVersionedWorkflowWidgetRunStatus(
            this.configService.SelectedSiteId,
            this.configService.SelectedProjectId!,
            this.workflowCanvasService.SelectedWorkflow?._id!,
            this.workflowCanvasService.ViewingRunId!,
            this.widgetUrn!,
          );
        this.workflowCanvasService.setWidgetRunResults(this.widgetRunResults)

      } catch (error) {
        this.widgetRunResults = [];
        this.workflowCanvasService.setWidgetRunResults(this.widgetRunResults)
      }
    } else {
      try {
        this.widgetRunResults =
          await this.workflowsSessionsApiService.GetWorkflowSessionWidgetRunStatus(
            this.configService.SelectedSiteId,
            this.configService.SelectedProjectId!,
            this.workflowCanvasService.SelectedWorkflowSession?._id!,
            this.widgetUrn!,
          );

        this.workflowCanvasService.setWidgetRunResults(this.widgetRunResults)
      } catch (error) {
        this.widgetRunResults = [];
        this.workflowCanvasService.setWidgetRunResults(this.widgetRunResults)
      }
    }
  }

  loadMoreLogs() {
    this.getActivityLog();
  }

  toFriendlyTime(isoDateString: string): string {
    const date = new Date(isoDateString);
    const now = new Date();
    const seconds = Math.round((now.getTime() - date.getTime()) / 1000);
    const minutes = Math.round(seconds / 60);
    const hours = Math.round(minutes / 60);
    const days = Math.round(hours / 24);

    // Formatting the date in a readable format
    const friendlyDate = date.toLocaleDateString('en-US', {
      weekday: 'long', // "Monday"
      year: 'numeric', // "2024"
      month: 'long', // "April"
      day: 'numeric' // "25"
    });

    const friendlyTime = date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });

    return `${friendlyDate} at ${friendlyTime}`;
  }

  async getActivityLog() {
    if (this.workflowCanvasService.IsVersionedWorkflow) {
      this.lastActivityLogResponse =
        await this.apiService.GetVersionedWorkflowWidgetActivityLog(
          this.configService.SelectedSiteId,
          this.configService.SelectedProjectId!,
          this.workflowCanvasService.ViewingRunId!,
          this.widgetUrn!,
          this.lastActivityLogResponse && this.lastActivityLogResponse.new_cursor_timestamp ? this.lastActivityLogResponse.new_cursor_timestamp : undefined,
          this.lastActivityLogResponse && this.lastActivityLogResponse.new_cursor_id ? this.lastActivityLogResponse.new_cursor_id : undefined,
        );
      if (this.lastActivityLogResponse) {
        this.dataSource.data = [
          ...this.dataSource.data,
          ...this.lastActivityLogResponse.logs
        ];
        if (this.lastActivityLogResponse.new_cursor_timestamp === undefined) {
          this.moreLogs = false;
        }
      } else {
        this.moreLogs = false;
      }
    } else {
      this.lastActivityLogResponse =
        await this.workflowsSessionsApiService.GetWorkflowSessionWidgetActivityLog(
          this.configService.SelectedSiteId,
          this.configService.SelectedProjectId!,
          this.workflowCanvasService.SelectedWorkflowSession?._id!,
          this.widgetUrn!,
          this.lastActivityLogResponse && this.lastActivityLogResponse.new_cursor_timestamp ? this.lastActivityLogResponse.new_cursor_timestamp : undefined,
          this.lastActivityLogResponse && this.lastActivityLogResponse.new_cursor_id ? this.lastActivityLogResponse.new_cursor_id : undefined,
        );
      if (this.lastActivityLogResponse) {
        this.dataSource.data = [
          ...this.dataSource.data,
          ...this.lastActivityLogResponse.logs
        ];
        if (this.lastActivityLogResponse.new_cursor_timestamp === undefined) {
          this.moreLogs = false;
        }
      } else {
        this.moreLogs = false;
      }
    }
  }

  getWidgetName() {
    return this.workflowCanvasService.selectedWidgetControl?.Widget.name;
  }

  getWidgetStatus() {
    // return this.widgetRunResult..
    if (this.workflowCanvasService.WorkflowRunStatus) {
      let results =
        this.workflowCanvasService.WorkflowRunStatus?.widgets_status.find(
          (t) => t.urn === this.widgetUrn,
        );
      if (results && results.status) {
        if (results.status === 'SCHEDULED' || results.status === 'IDLE') {
          return 'PENDING';
        }
        if (results.status === 'SUCCEEDED' && !this.widgetResultApiCalled) {
          this.getWidgetRunResult();
          this.widgetResultApiCalled = true;
        }
        return results.status;
      }
    }

    return 'No status';
  }

  getWorkflowRunStatus() {
    if (this.workflowCanvasService.WorkflowRunStatus) {
      return this.workflowCanvasService.WorkflowRunStatus.run_status;
    }
    return 'No results';
  }

  toggleDisplay(): void {
    this.isExpanded = !this.isExpanded;
  }

  getWidgetProgressStatus() {
    if (this.workflowCanvasService.WorkflowRunStatus) {
      let results = this.workflowCanvasService.WorkflowRunStatus.widgets_status.find(
        (t) => t.urn === this.widgetUrn
      );
  
      if (results) {
        let status = results.status;
        let data = (results as any).data || {}; // Ensure data exists
  
        return {
          status: status,
          current_cell: data.current_cell ?? 0,
          total_cells: data.total_cells ?? 1 // Avoid division by zero
        };
      }
    }
  
    return { status: 'No status', current_cell: 0, total_cells: 1 };
  }

}
