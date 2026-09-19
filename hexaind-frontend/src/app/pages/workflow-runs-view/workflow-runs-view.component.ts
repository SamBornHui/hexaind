import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from 'src/app/services/api.service';
import { Location } from '@angular/common';
import { WorkflowRun } from '../../models/workflow-models';
import { MatDialog } from '@angular/material/dialog';
import { WorkflowRunPreviewComponent } from 'src/app/dialogs/workflow-run-preview/workflow-run-preview.component';
@Component({
  selector: 'app-workflow-runs-view',
  templateUrl: './workflow-runs-view.component.html',
  styleUrls: ['./workflow-runs-view.component.less'],
})
export class WorkflowRunsViewComponent {
  displayedColumns: string[] = [
    'Run ID',
    'status',
    'lastModified',
    'more_vert',
  ];
  descending: boolean = true;
  searchText: string = '';
  workflow_id: any;
  workflow = { site_id: '1', project_id: '1' };
  workflows: WorkflowRun[] = [];
  searchResults: any[] = [];
  public menuItem: any;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private location: Location,
    public dialog: MatDialog,
  ) {}

  ngOnInit() {
    this.route.paramMap.subscribe((params) => {
      this.workflow_id = params.get('id');
    });

    this.getWorkflowRunStatuses();
  }

  async getWorkflowRunStatuses() {
    let response = await this.apiService.GetAllRunsForWorkflowById(
      this.workflow_id,
    );
    if (response) this.workflows = response;
    this.searchResults = [...this.workflows];
  }

  onToggleSort() {
    this.descending = !this.descending;
    this.sortWorkflowsByLastModified();
  }

  sortWorkflowsByLastModified(): void {
    this.workflows.sort((a, b) => {
      const dateA = new Date(a.last_modified_at).getTime();
      const dateB = new Date(b.last_modified_at).getTime();
      return this.descending ? dateB - dateA : dateA - dateB;
    });
  }

  goBackToPrevPage() {
    this.location.back();
  }

  onSearchTextChange() {
    const lowerCaseQuery = this.searchText.toLowerCase();

    if (lowerCaseQuery.trim() === '') {
      this.searchResults = this.workflows;
      return;
    }

    this.searchResults = this.workflows.filter((workflow: any) => {
      const searchableFields = ['Run ID', 'status'];
      return searchableFields.some((field) =>
        workflow[field].toLowerCase().includes(lowerCaseQuery),
      );
    });
  }

  async onWorkflowView(data: any) {
    let response = await this.apiService.GetVersionedWorkflowRunStatus(
      '1',
      data.project_id,
      data.workflow_id,
      data._id,
    );
    this.openResponseModal(response);
  }

  openResponseModal(responseData: any): void {
    const dialogRef = this.dialog.open(WorkflowRunPreviewComponent, {
      width: '600px',
      data: responseData,
    });
  }
}
