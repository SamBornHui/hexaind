import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { Widget } from 'src/app/models/workflow-models';
import { WorkflowRunStatus } from 'src/app/models/workflow-sessions-api-response.models';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';

@Component({
  selector: 'app-run-summary',
  templateUrl: './run-summary.component.html',
  styleUrls: ['./run-summary.component.less'],
})
export class RunSummaryComponent {
  workflowRunStatus: WorkflowRunStatus | undefined = undefined;
  widgetStatuses: any[] = [];
  displayedColumns: string[] = ['name', 'status'];
  constructor(
    public dialogRef: MatDialogRef<RunSummaryComponent>,
    private workflowCanvasService: WorkflowCanvasService,
  ) {
    this.workflowRunStatus = this.workflowCanvasService.WorkflowRunStatus;
    this.workflowCanvasService.WorkflowRunStatus?.widgets_status.forEach(
      (widgetStatus) => { 
        let results: {
          name: string | undefined;
          status: string | undefined;
        } = {
          name: undefined,
          status: widgetStatus.status,
        };
        let widget: Widget | undefined =
          this.workflowCanvasService.SelectedWorkflow?.widgets.find(
            (t) => t.urn === widgetStatus.urn,
          );  
        if (widget) {
          results.name = widget.name;
          this.widgetStatuses.push(results);
        }
      },
    );
  }

  GetWorkflowStatus() {
    if (this.workflowRunStatus) {
      return this.workflowRunStatus.run_status;
    }
    return 'Run status could not be loaded.';
  }

  onClosePanel() {
    this.dialogRef.close();
  }

  onViewDataset() {
    this.dialogRef.close({
      viewDataset: true,
    });
  }
}
