import { BootstrapOptions, Component, EventEmitter, Input, Output } from '@angular/core';
import { Location } from '@angular/common';
import { Widget, WorkflowRun } from 'src/app/models/workflow-models';
import { ApiService } from 'src/app/services/api.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { Project } from 'src/app/models/project-models';
import { ConfigService } from 'src/app/services/config.service';
import { format, parseISO } from 'date-fns';
import { ActivatedRoute, Router, UrlTree } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { PublishedWorkflowRunsComponent } from 'src/app/dialogs/published-workflow-runs/published-workflow-runs.component';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { WorkflowSession } from 'src/app/models/workflow-sessions-api-response.models';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { CreateNewScheduleComponent } from 'src/app/dialogs/create-schedule/create-schedule.component';
import { BehaviorSubject, Subscription } from 'rxjs';

@Component({
  selector: 'app-workflow-designer-header',
  templateUrl: './workflow-designer-header.component.html',
  styleUrls: ['./workflow-designer-header.component.less'],
})
export class WorkflowDesignerHeaderComponent {
  @Output() onRunChanged: EventEmitter<string> = new EventEmitter<string>();
  @Output() runWorkflowExecution: EventEmitter<string> =
    new EventEmitter<string>();
  @Output() stopWorkflowExecution: EventEmitter<string> =
    new EventEmitter<string>();
  @Output() saveWorkflow: EventEmitter<string> = new EventEmitter<string>();
  @Output() saveAsWorkflow: EventEmitter<string> = new EventEmitter<string>();
  @Output() publishWorkflow: EventEmitter<string> = new EventEmitter<string>();
  @Output() closeViewRunMode: EventEmitter<string> = new EventEmitter<string>();
  @Output() openViewRunMode: EventEmitter<string> = new EventEmitter<string>();
  @Output() openViewRunSummary: EventEmitter<string> = new EventEmitter<string>();
  @Output() createWorkflowTemplate: EventEmitter<string> = new EventEmitter<string>();
  @Output() loadWorkflowTemplate: EventEmitter<string> = new EventEmitter<string>();
  @Output() onHeaderNavigateBack: EventEmitter<any> = new EventEmitter<any>();
  @Input() disableSaveAndRun: boolean = false

  workflowRuns: WorkflowRun[] = [];
  selectedRunId: string | undefined = undefined;
  lastRun: string = 'Last run: Never';
  public WorkflowName: string = '';
  versionedWorkflowId: string | undefined;
  master_workflow_name: string | undefined;
  workflowSessionId: any[] = [];
  publishedWorkflows: any[] = [];
  selectedWorkflow: any;
  templateWorkflowId: string | undefined;

  private _data: BehaviorSubject<string> = new BehaviorSubject<string>('');
  private dataSubscription!: Subscription;
  workflowResults: any;
  getAllworkflowRuns: Array<any> = []
  selectedWorkflowWidgets: any = [];

  @Input()
  set data(value: string) {
    this._data.next(value || ''); // Emit the new value to the observable
  }

  get data(): string {
    return this._data.getValue(); // Return the current value
  }

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private location: Location,
    public sharedDataService: SharedDataService,
    public workflowCanvasService: WorkflowCanvasService,
    public dialog: MatDialog,
    public apiService: ApiService,
    public workflowsSessionsApiService: WorkflowsSessionsApiService,
    public configService: ConfigService,
  ) { }

  ngOnInit(): void {
    this.dataSubscription = this._data.subscribe((value) => {
      this.onDataChange(value);
    });
    this.workflowCanvasService.selectedWorkflow$.subscribe((workflow) => {
      this.selectedWorkflowWidgets = workflow?.widgets
    });

    this.workflowCanvasService.widgetExecutionStatus$.subscribe((status) => {
      if (status) {
        this.getWorkflowResults();
      }
    });

    this.getWorkflowResults();
  }

  async getWorkflowResults() {
    const siteId = this.configService.SelectedSiteId;
    const projectId = this.configService.SelectedProjectId;
    const workflowId = this.route.snapshot.queryParamMap.get('versionedWorkflowId');
    const sessionId = this.route.snapshot.queryParamMap.get('workflowSessionId');
    const isVersioned = this.workflowCanvasService.IsVersionedWorkflow;

    if (isVersioned) {
      try {
        this.getAllworkflowRuns = await this.apiService.GetWorkflowRuns(siteId, projectId!, workflowId!);
      } catch (error) {
        console.error('Error fetching all runs for versioned workflow:', error);
      }
    }

    else {
      this.workflowsSessionsApiService.getWorkflowResults(
        siteId!,
        projectId!,
        sessionId!,
      ).subscribe(
        (results) => {
          this.workflowResults = results;
        },
        (error) => {
          console.error('Error fetching workflow results:', error);
        }
      );
    }
  }

  get hasWorkflowRuns(): boolean {
    return this.getAllworkflowRuns && this.getAllworkflowRuns.length > 0;
  }

  get hasWidgets(): boolean {
    return this.selectedWorkflowWidgets && this.selectedWorkflowWidgets.length > 0
  }


  async getSessionById(workflowSessionId: any) {
    if (workflowSessionId) {
      var sessionDetails = await this.workflowsSessionsApiService.GetWorkflowSession(
        this.configService.SelectedSiteId,
        this.configService.SelectedProjectId ?? '',
        workflowSessionId
      )
      this.master_workflow_name = sessionDetails?.name;
      this.templateWorkflowId = sessionDetails!.workflow_id;
      if (sessionDetails && sessionDetails.saved_workflows.length > 0) {
        this.publishedWorkflows = sessionDetails.saved_workflows;
        this.selectedWorkflow = this.publishedWorkflows.find(workflow => workflow.workflow_id === this.versionedWorkflowId) || null;
      } else {
        this.publishedWorkflows = [];
      }
    };
  }

  onDataChange(newValue: string) {
    this.route.queryParams.subscribe((params) => {
      this.versionedWorkflowId = params['versionedWorkflowId'];
      this.workflowSessionId = params['workflowSessionId'];
    });
    this.getSessionById(this.workflowSessionId);
  }

  updateDataFromParent(newData: string) {
    this._data.next(newData);
  }

  onSelectWorkflow(event: any): void {
    let queryParams = {
      siteId: this.configService.SelectedSiteId,
      projectId: this.configService.SelectedProjectId,
      workflowSessionId: this.workflowSessionId,
      versionedWorkflowId: event.workflow_id,
    };
    this.router.navigate(['/workflow-designer'], {
      queryParams,
    });
  }

  navigateToMasterWorkflow() {
    let queryParams = {
      siteId: this.configService.SelectedSiteId,
      projectId: this.configService.SelectedProjectId,
      workflowSessionId: this.workflowSessionId
    };
    this.selectedWorkflow = null;
    this.router.navigate(['/workflow-designer'], {
      queryParams,
    });
  }

  truncateName(name: string): string {
    return name.length > 25 ? name.substring(0, 25) + '...' : name;
  }

  public Initialize(workflowName: string) {
    this.WorkflowName = workflowName;
  }

  getLastRunText() {
    if (this.workflowCanvasService.WorkflowRunStatus) {
      return (
        'Workflow Run Status: ' +
        this.workflowCanvasService.WorkflowRunStatus.run_status
      );
    }
    return 'Workflow Run Status: Loading...';
  }

  findMostRecentWorkflowRun(objects: WorkflowRun[]): WorkflowRun {
    return objects.reduce((a, b) => (a.created_at > b.created_at ? a : b));
  }

  goBack() {
    if (this.workflowCanvasService.IsViewingRunMode) {
      this.onCloseViewRunMode();
      return;
    }

    this.onHeaderNavigateBack.emit();
  }

  workflowRunning() {
    return false; // TBD this.sharedDataService.WorkflowRunning;
  }

  convertToReadableDate(isoDateString: string): string {
    // Parse the ISO string to a Date object
    const date = parseISO(isoDateString);

    // Format the date to a more readable format, e.g., "Friday 9 AM"
    // Adjust the timezone offset as per your requirement. This example uses 'UTC'
    return format(date, 'iiii h a');
  }

  getRunLabel(run: WorkflowRun) {
    return this.convertToReadableDate(run.created_at);
  }

  getSelectedRun() {
    return this.workflowRuns.find((t) => t._id == this.selectedRunId);
  }

  setSelectedRun(runId: string) {
    this.selectedRunId = runId;
    this.onRunChanged.emit(this.selectedRunId);
  }

  onRunWorkflowExecution() {
    this.runWorkflowExecution.emit();
  }

  onStopWorkflowExecution() {
    this.stopWorkflowExecution.emit();
  }

  onSaveWorkflow() {
    this.saveWorkflow.emit();
  }

  onSaveAsWorkflow() {
    this.saveAsWorkflow.emit();
  }

  onPublishWorkflow() {
    this.publishWorkflow.emit();
  }

  disabledSaveAsTemplate() {
    const { originalSavedWorkflowClone } = this.workflowCanvasService;
    return !(
      Object.keys(originalSavedWorkflowClone).length > 0 &&
      originalSavedWorkflowClone.widgets.length > 0 &&
      this.selectedWorkflowWidgets.length > 0 &&
      originalSavedWorkflowClone.widgets.length === this.selectedWorkflowWidgets.length &&
      this.selectedWorkflowWidgets.some((widget: Widget) => widget.type !== 'UX')
    );
  }

  onCreateWorkflowTemplate() {
    let workflow: any = {
      workflow_id: this.templateWorkflowId
    }
    this.createWorkflowTemplate.emit(workflow);
  }
  onLoadWorkflowTemplate() {
    let workflow: any = {
      workflow_id: this.templateWorkflowId
    }
    this.loadWorkflowTemplate.emit(workflow);
  }

  removeQueryParam(paramKey: string) {
    // Get the current URL tree
    const urlTree: UrlTree = this.router.parseUrl(this.router.url);

    // Get the query params object from the URL tree
    const queryParams = { ...urlTree.queryParams };

    // Remove the specified parameter from the query params object
    delete queryParams[paramKey];

    // Create a new URL tree with the updated query params
    const updatedUrlTree = this.router.createUrlTree([], { queryParams });

    // Serialize the updated URL tree to a URL string
    const urlWithoutQueryParam: string =
      this.router.serializeUrl(updatedUrlTree);

    // Replace the current URL without triggering navigation
    history.replaceState({}, '', urlWithoutQueryParam);
  }

  onCloseViewRunMode() {
    this.getWorkflowResults();
    this.workflowCanvasService.IsViewingRunMode = false;
    this.removeQueryParam('viewingRunId');
    this.closeViewRunMode.emit();
  }

  onViewRun() {
    this.openViewRunMode.emit();
  }

  onViewRunSummary() {
    this.openViewRunSummary.emit();
  }

  createNewSchedule(status: any, workflow_id: any) {
    const dialogRef = this.dialog.open(CreateNewScheduleComponent, {
      width: '1200px',
      disableClose: true,
      data: { status, workflow_id },
    });
    dialogRef.componentInstance.addEvent.subscribe((result: any) => {
      //this.onRefreshView();
    });
  }

  ngOnDestroy() {
    if (this.dataSubscription) {
      this.dataSubscription.unsubscribe();
    }
  }
}
