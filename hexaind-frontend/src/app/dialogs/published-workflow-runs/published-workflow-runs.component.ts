import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { WorkflowRun } from 'src/app/models/workflow-models';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ApiService } from 'src/app/services/api.service';
import { ConfigService } from 'src/app/services/config.service';

@Component({
  selector: 'app-published-workflow-runs',
  templateUrl: './published-workflow-runs.component.html',
  styleUrls: ['./published-workflow-runs.component.less'],
})
export class PublishedWorkflowRunsComponent {
  workflowRuns: WorkflowRun[] = [];
  selectedRun: WorkflowRun | undefined = undefined;

  constructor(
    public dialogRef: MatDialogRef<PublishedWorkflowRunsComponent>,
    private apiService: ApiService,
    private configService: ConfigService,
    private workflowCanvasService: WorkflowCanvasService,
    @Inject(MAT_DIALOG_DATA) public data: any,
  ) {}

  ngOnInit() {
    this.loadWorkflowRuns();
  }


  // Convert from UTC -> to users local time stamp.
  
  toFriendlyDate(isoDateString: string): string {
    // Parse the ISO date string to a Date object
    const date = new Date(isoDateString);

    // Define options for displaying the date part
    const dateOptions: Intl.DateTimeFormatOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        timeZone: 'UTC' // Adjust if you want to show in local time instead
    };

    // Define options for displaying the time part
    const timeOptions: Intl.DateTimeFormatOptions = {
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'UTC' // Adjust if you want to show in local time instead
    };

    // Format the date and time parts
    const formattedDate = date.toLocaleDateString('en-US', dateOptions);
    const formattedTime = date.toLocaleTimeString('en-US', timeOptions);

    // Combine the formatted date and time with some custom text
    return `${formattedDate}, at ${formattedTime}`;
}

  async loadWorkflowRuns() {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    this.workflowRuns = await this.apiService.GetWorkflowRuns(
      this.configService.SelectedSiteId,
      selectedProjectId,
      this.data.workflowId,
    );
  }

  onViewSelectedRun() {
    if (!this.selectedRun) {
      // TODO (Mike) notify user to select a run and do not close.
      this.dialogRef.close(undefined);
      return;
    }
    let queryParams: {
      refresh: string;
      siteId: string;
      projectId: string;
      workflowSessionId: string | null | undefined;
      viewingRunId: string | null;
      versionedWorkflowId: string | undefined;
      runworkflow: string;
    } = {
      refresh: Math.random().toString(),
      siteId: this.configService.SelectedSiteId,
      projectId: this.configService.SelectedProjectId!,
      workflowSessionId: this.data.workflowSessionId,
      viewingRunId: this.selectedRun._id,
      versionedWorkflowId: this.data.workflowId,
      runworkflow: "true"
    };

    this.dialogRef.close(queryParams);
  }

  onClosePanel() {
    this.dialogRef.close(undefined);
  }
}
