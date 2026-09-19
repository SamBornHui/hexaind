import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { UpdateWorkflowSessionComponent } from '../../dialogs/update-workflow-session/update-workflow-session.component';
import { Router } from '@angular/router';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { ChangeDetectorRef, Component, TemplateRef, ViewChild } from '@angular/core';
import { ElementRef, Renderer2 } from '@angular/core';
import { ConfigService } from '../../services/config.service';
import { Utils } from '../../utils';
import { Workflow, WorkflowState } from '../../models/workflow-models';
import { NavService } from 'src/app/controls/left-nav/nav.service';
import { catchError, finalize, Subject, Subscription, tap } from 'rxjs';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { WorkflowSession } from 'src/app/models/workflow-sessions-api-response.models';
import { ApiService } from 'src/app/services/api.service';
import {
  animate,
  state,
  style,
  transition,
  trigger,
} from '@angular/animations';
import { UpdateWorkflowComponent } from 'src/app/dialogs/update-workflow/update-workflow.component';
import { PublishedWorkflowRunsComponent } from 'src/app/dialogs/published-workflow-runs/published-workflow-runs.component';
import { WorkflowCanvasService } from '../workflow-designer/workflow-canvas.service';
import { CreateNewWorkflowSessionComponent } from 'src/app/dialogs/create-new-workflow/create-new-workflow-session.component';
import { DataSetResultsComponent } from 'src/app/dialogs/data-set-results/data-set-results/data-set-results.component';
import { Sort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { ToastrService } from 'ngx-toastr';
import { PublishWorkflowComponent } from 'src/app/dialogs/publish-workflow/publish-workflow.component';
import { ShareWorkflowTemplateComponent } from 'src/app/dialogs/share-workflow-template/share-workflow-template.component';
import { HttpResponse } from '@angular/common/http';


@Component({
  selector: 'app-workflow',
  templateUrl: './workflow.component.html',
  styleUrls: ['./workflow.component.less'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({ height: '0px', minHeight: '0' })),
      state('expanded', style({ height: '*' })),
      transition(
        'expanded <=> collapsed',
        animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)'),
      ),
    ]),
  ],
})
export class WorkflowComponent {
  private searchTerms = new Subject<string>();
  isLargeScreen: boolean = true;
  selectedSiteId = 0;
  selectedWorkflowSessionId = 0;
  selectedSiteRow: any = null;
  selectedWorkflowSessionRow: any = null;
  showUserContextMenu = false;
  menuPosition = { x: 0, y: 0 };
  screenWidth: number = 0;
  searchText: string = '';
  descending: boolean = true;
  WorkflowState = WorkflowState;
  displayedColumns: string[] = [
    'expand',
    'Name',
    'Description',
    'Version',
    'Created By',
    'Date Created',
    'Last Modified',
    'menu',
  ];
  sessions: any;
  currentUser: any;
  filteredSessionsData: any[] = [];
  expandedElement: any | null;
  IsCreatingNewWorkflowSession: boolean = false;
  numberOfColumns: number = 0;
  projectName: string = '';
  @ViewChild('confirmationDialogTemplate') confirmationDialogTemplate!: TemplateRef<any>;
  @ViewChild('versionedconfirmationDialogTemplate') versionedconfirmationDialogTemplate!: TemplateRef<any>;
  dialogRef!: MatDialogRef<any>;
  private boundResizeFunction: () => void;
  public trackedPublishedWorkflow: any;
  public trackedWorkflowSession: any;
  public workflowSession: any;
  public deleteConfirmation: boolean = false;
  public actionsItem: boolean = false;
  contextMenuTargetId: string | undefined = undefined;
  private projectSubscription: Subscription | undefined = undefined;
  assets: any = {};
  session_owners: any;
  showLoader: boolean = true;
  isSessionLoaded: boolean = false;
  sessionResult: any;
  selectedValue: boolean = true;
  role_name: any;
  savedWorkflow: any;
  fetchedSessionList: any;

  constructor(
    public navService: NavService,
    private cdRef: ChangeDetectorRef,
    private renderer: Renderer2,
    private el: ElementRef,
    private router: Router,
    private configService: ConfigService,
    private breakpointObserver: BreakpointObserver,
    public dialog: MatDialog,
    private sessionApi: WorkflowsSessionsApiService,
    private apiService: ApiService,
    private workflowCanvasService: WorkflowCanvasService,
    private toastr: ToastrService,
    private cdr: ChangeDetectorRef
  ) {
    const rolesfeaturesString = localStorage.getItem('rolesfeatures');
    const storedName = localStorage.getItem('rolesName');
    //this.role_name = this.getFeaturesList.role_info.name;
    if (storedName !== null) {
      try {
        const parsedName = JSON.parse(storedName);
        this.role_name = parsedName.name;
      } catch (error) {
        console.error("Error parsing storedName JSON", error);
      }
    }
    if (rolesfeaturesString !== null) {
      this.assets = JSON.parse(rolesfeaturesString).assets.workflows;
    } else {
      this.assets = 'server_admin';
      console.error('No rolesfeatures found in localStorage.');
    }
    this.renderer.listen('document', 'click', (event) => {
      if (this.el.nativeElement.contains(event.target)) {
        this.showUserContextMenu = false;
      }
    });

    this.breakpointObserver
      .observe([Breakpoints.Handset, Breakpoints.Small, Breakpoints.XSmall])
      .subscribe((result) => {
        this.isLargeScreen = !result.matches;
      });

    this.boundResizeFunction = this.onResize.bind(this);
    window.addEventListener('resize', this.boundResizeFunction);
  }

  ngOnDestroy() {
    // Remove the event listener when the component is destroyed
    window.removeEventListener('resize', this.boundResizeFunction);
    this.projectSubscription?.unsubscribe();
    this.showLoader = false;
  }

  ngOnInit() {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!)
    this.showLoader = true;
    // this.loadData();

    this.projectSubscription =
      this.configService.selectedProjectIdObservable.subscribe((projectId) => {
        console.log("changed project id", projectId);
        if (projectId) {
          this.loadData();
        }
      });
  }
  onShareWorkflowTemplate(workflow: any) {
    let dialogRef: any;
    dialogRef = this.dialog.open(ShareWorkflowTemplateComponent, {
      width: '600px',
      data: {
        workflowId: workflow.workflow_id, // Use camelCase for JavaScript properties
        sessionId: workflow._id,
      },
    });

    dialogRef.afterClosed().subscribe((result: any) => {
      if (result) { }
    });
  }

  onDuplicateWorkflow(workflow: any, type: string) {
    let data: any = {
      isDuplicate: true,
      workflow_id: workflow.workflow_id,
      type: type,
      sessionId: this.trackedWorkflowSession._id,
      is_template: this.isTemplateWorkflow(workflow)
    }
    if (type == 'master') {
      let dialog: any;
      dialog = this.dialog.open(CreateNewWorkflowSessionComponent, {
        width: '500px',
        data: data
      });
      dialog.afterClosed().subscribe((res: WorkflowSession) => {
        if (res) {
          const currentData = this.sessions;
          this.sessions = [...currentData, res];
          this.loadData()
        }
      });
    } else {
      const dialogRef = this.dialog.open(PublishWorkflowComponent, {
        width: '500px',
        data: data
      });
      dialogRef.afterClosed().subscribe((result: any) => {
        if (result) {
          this.duplicateVersionedWorkflow(workflow, result)
        }
      });
    }
  }
  async duplicateVersionedWorkflow(workflow: any, inputData: any) {
    let workflowRequest: any = {
      name: inputData.name,
      description: inputData.description,
      user_name: inputData.owner,
      user_id: inputData.ownerId,
      version_tag: inputData.version,
      workflow_id: workflow.workflow_id,
      is_template: false
    };
    let type: any = 'version'
    let savedWorkflow: string | undefined = undefined;
    try {
      savedWorkflow = await this.apiService.duplicateWorkflow(
        this.configService.SelectedSiteId,
        this.configService.SelectedProjectId,
        this.trackedWorkflowSession._id,
        type,
        workflowRequest
      );
      this.toastr.success('Workflow Created Successfully', 'Success', {
        positionClass: 'custom-toast-position',
      });
      this.loadData()
    } catch {
      this.toastr.error('Failed to created workflow', 'Error', {
        positionClass: 'custom-toast-position',
      });
    }

  }

  onExportWorkflow(workflow: any, type: string) {
    let data: any = {
      isExport: true,
      workflow_id: workflow.workflow_id,
      type: type,
      sessionId: this.trackedWorkflowSession._id,
      is_template: this.isTemplateWorkflow(workflow)
    }
    if (type == 'master') {
      let dialog: any;
      dialog = this.dialog.open(CreateNewWorkflowSessionComponent, {
        width: '500px',
        data: data
      });
      dialog.afterClosed().subscribe((res: WorkflowSession) => {
        if (res) {
          const currentData = this.sessions;
          this.sessions = [...currentData, res];
          this.loadData()
        }
      });
    } else { // need to make changes for published feature
      const dialogRef = this.dialog.open(PublishWorkflowComponent, {
        width: '500px',
        data: data
      });
      dialogRef.afterClosed().subscribe((result: any) => {
        if (result) {
          this.exportVersionedWorkflow(workflow, result)
        }
      });
    }
  }
  async exportVersionedWorkflow(workflow: any, inputData: any) {
    let workflowRequest: any = {
      name: inputData.name,
      description: inputData.description,
      user_name: inputData.owner,
      user_id: inputData.ownerId,
      version_tag: inputData.version,
      workflow_id: workflow.workflow_id,
      is_template: false
    };
    let type: any = 'version';
    let savedWorkflowUrl: string | undefined = undefined;

    try {
      // Call exportWorkflow and handle the Blob response
      const exportedBlob = await this.apiService.exportWorkflowData(
        this.configService.SelectedSiteId,
        this.configService.SelectedProjectId,
        this.trackedWorkflowSession._id,
        type,
        workflowRequest
      );

      // Convert Blob to a URL for direct download or open in a new tab
      savedWorkflowUrl = URL.createObjectURL(exportedBlob);
      window.open(savedWorkflowUrl, '_blank'); // Opens the file in a new tab

      this.toastr.success('Workflow Created Successfully', 'Success', {
        positionClass: 'custom-toast-position',
      });

      // Call loadData if further data is needed post export
      this.loadData();
    } catch {
      this.toastr.error('Failed to created workflow', 'Error', {
        positionClass: 'custom-toast-position',
      });
    }

  }
  onPreviewDatasetResultsForWorkflowVersion(trackedWorkflow: any, workflowSession: WorkflowSession) {
    let dialogRef: any;

    dialogRef = this.dialog.open(PublishedWorkflowRunsComponent, {
      width: '600px',
      data: {
        workflowId: trackedWorkflow.workflow_id, // Use camelCase for JavaScript properties
        workflowSessionId: workflowSession._id,
      },
    });

    dialogRef.afterClosed().subscribe((queryParams: any) => {
      if (queryParams) {
        dialogRef = this.dialog.open(DataSetResultsComponent, {
          width: '800px',
          height: '90%',
          data: { workflowSessionId: workflowSession._id, workflowId: trackedWorkflow.workflow_id, runId: queryParams.viewingRunId }
        });

        dialogRef.afterClosed().subscribe(() => {

        });
      }
    });
  }

  onPreviewDatasetResultForWorkflowSession(workflowSession: WorkflowSession) {
    let dialogRef: any;
    dialogRef = this.dialog.open(DataSetResultsComponent, {
      width: '800px',
      data: { workflowId: workflowSession.workflow_id, workflowSessionId: workflowSession._id, runId: undefined }
    });

    dialogRef.afterClosed().subscribe(() => {

    });
  }

  getColumnName(name: string) {
    if (name === 'menu' || name === 'expand') {
      return '';
    }
    return name;
  }

  toggleExpandButtonClicked(event: any, element: any) {
    if (
      this.expandedElement &&
      this.expandedElement !== element &&
      this.expandedElement.expanded
    ) {
      this.expandedElement.expanded = false;
    }
    if (element.expanded === undefined) {
      element.expanded = true;
    } else {
      element.expanded = !element.expanded;
    }

    if (element.expanded) {
      this.expandedElement = element;
    } else {
      this.expandedElement = undefined;
    }
    event.stopPropagation();
  }

  hoveredRow: any;

  async onSearchTextChange(event: Event) {
    let searchTerm = (event.target as HTMLInputElement).value.trim();
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    if (this.fetchedSessionList) {
      this.sessions = this.fetchedSessionList
    }
    else {
      this.fetchedSessionList = await this.sessionApi.GetWorkflowSessions(
        this.configService.SelectedSiteId,
        selectedProjectId,
      );
    }

    let result = [];
    result = this.sessions.filter((session: any) => {
      if (searchTerm) {
        const workflowName = session.name.toLowerCase();
        const workflowOwnerName = session.owner_name.toLowerCase();
        searchTerm = searchTerm.toLowerCase();
        if (workflowName.includes(searchTerm) || workflowOwnerName.includes(searchTerm)) {
          return workflowName.includes(searchTerm) || workflowOwnerName.includes(searchTerm);
        } else {
          return false;
        }
      }
    });
    if (!searchTerm) {
      this.loadWorkflowSessions();
    } else {
      this.sessions = result;
    }
  }

  getWorkflowName(workflow: any) {
    return workflow.name;
  }

  onResize(event?: Event) {
    this.calculateColumns();
    this.screenWidth = window.innerWidth;
    this.cdRef.detectChanges();
  }

  private calculateColumns() {
    const parentWidth = document.querySelector('[fxLayout]')!.clientWidth; // Ensure this selects your flex container
    this.numberOfColumns = Utils.CalculateColumns(parentWidth);
  }

  ngAfterViewInit() {
    //this.loadData();
  }

  loadData() {
    this.loadWorkflowSessions();
    this.screenWidth = window.innerWidth;

    setTimeout(() => {
      this.calculateColumns();
    }, 250);
  }

  onToggleSort() {
    this.descending = !this.descending;
    this.sortWorkflowsSessionsByLastModified();
  }

  workflowName(element: any) {
    return element.name;
  }

  workflowDescription(element: any) {
    return element.description;
  }

  sortWorkflowsSessionsByLastModified(): void {
    this.sessions.sort((a: { last_modified_at: string | number | Date; }, b: { last_modified_at: string | number | Date; }) => {
      // Convert dates to timestamps. If the date is undefined, use 0 as a fallback.
      const dateA = a.last_modified_at
        ? new Date(a.last_modified_at).getTime()
        : 0;
      const dateB = b.last_modified_at
        ? new Date(b.last_modified_at).getTime()
        : 0;

      // Now that we have numbers, subtraction is possible.
      return this.descending ? dateB - dateA : dateA - dateB;
    });
  }

  test(element: any) {
    if (element) {
      console.log(element);
    }
    return 'hi';
  }
  getNumberOfColumns(): number {
    let screenWidth = window.innerWidth;
    let tileCount = Math.floor(screenWidth / 220);
    return tileCount;
  }

  onCloseCreateNewWorkflowDialog() {
    this.IsCreatingNewWorkflowSession = false;
  }
  // Converted to matdialog on 23-04-2024
  // OnWorkflowSessionCreated(session: WorkflowSession) {
  //   this.IsCreatingNewWorkflowSession = false;
  //   const currentData = this.sessions;
  //   this.sessions = [...currentData, session];
  //   this.loadWorkflowSessions();
  // }

  onRefreshView() {
    this.loadWorkflowSessions();
    this.selectedValue = false;
  }


  async loadWorkflowSessions() {
    try {
      this.isSessionLoaded = false;
      let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
      if (!selectedProjectId) {
        return;
      }

      this.showLoader = true;
      // Call to API to get workflow sessions and invalid session IDs
      const response = await this.sessionApi.GetInvalidWorkflowSessions(this.configService.SelectedSiteId, selectedProjectId);
      if (response) {
        // Assuming response has sessions and invalid_session_ids properties
        this.sessions = response.sessions.map(session => ({
          ...session,
          isInvalid: response.invalid_session_ids.includes(session._id || '')
        }));

        // Store the original sessions for filtering or further processing
        this.filteredSessionsData = this.sessions.slice();
        this.sessionResult = this.sessions;

        // Other operations on sessions
        this.session_owners = this.getUniqueOwners(this.sessions);
        this.sortWorkflowsSessionsByLastModified();
        this.sortSessions();
      } else {
        console.error('Failed to fetch workflow sessions.');
      }
    } catch (error) {
      console.error('Error loading workflow sessions:', error);
    } finally {
      this.isSessionLoaded = true;
      this.showLoader = false;
    }
  }


  getUniqueOwners(sessions: any[]): { owner_id: string; owner_name: string }[] {
    const uniqueOwnersMap: { [ownerId: string]: string } = {};

    sessions.forEach((session) => {
      uniqueOwnersMap[session.owner_id] = session.owner_name;
    });

    return Object.keys(uniqueOwnersMap).map((ownerId) => ({
      owner_id: ownerId,
      owner_name: uniqueOwnersMap[ownerId],
    }));
  }

  workflowOwner(event: any) {
    this.sessions = this.sessionResult;
    let filteredResults = this.sessions.filter((session: any) => {
      if (session.owner_id == event.owner_id) {
        return session;
      }
    });
    this.sessions = filteredResults;
    this.selectedValue = true;
  }

  getContextMenuWidth(): number {
    const contextMenu = this.el.nativeElement.querySelector('.context-menu');
    if (!contextMenu) return 0;
    // Temporarily show and move the context menu off-screen for measuring
    contextMenu.style.display = 'block';
    contextMenu.style.left = '-9999px';
    const width = contextMenu.offsetWidth;
    // Reset the styles
    contextMenu.style.display = 'none';
    contextMenu.style.left = '0px';

    return width;
  }

  toggleUserContextMenu(event: MouseEvent, workflow: any) {
    this.contextMenuTargetId = workflow._id;
    this.showUserContextMenu = !this.showUserContextMenu;
    this.selectedWorkflowSessionRow = workflow;
    this.menuPosition.x = event.clientX - this.getContextMenuWidth() + 165; // Adjusted the x position
    this.menuPosition.y = event.clientY;
    this.menuPosition.y += 10;

    event.stopPropagation();
  }

  isWorkflowSessionRowSelected(row: any): boolean {
    return this.selectedWorkflowSessionRow === row;
  }

  async onViewWorkflowSessionRun(workflowSession: WorkflowSession) {
    let siteId = this.configService.SelectedSiteId;
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    let queryParams = {
      siteId: siteId,
      projectId: selectedProjectId,
      workflowSessionId: workflowSession._id,
      versionedWorkflowId: undefined,
      viewingRunId: workflowSession.run_id,
    };
    this.router.navigate(['/workflow-designer'], {
      queryParams,
    });
  }

  onViewWorkflowSession(workflowSession: WorkflowSession) {
    this.workflowCanvasService.IsViewingRunMode = false;
    if (!workflowSession._id) {
      return;
    }
    this.configService.workflowName = workflowSession.name ?? 'Unknown';
    let siteId = this.configService.SelectedSiteId;
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    let queryParams = {
      siteId: siteId,
      projectId: selectedProjectId,
      workflowSessionId: workflowSession._id,
      versionedWorkflowId: undefined,
    };
    this.router.navigate(['/workflow-designer'], {
      queryParams,
    });
  }

  onViewPublishedWorkflow(workflowSession: any, workflowDetails: any) {
    let siteId = this.configService.SelectedSiteId;
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    let queryParams = {
      siteId: siteId,
      projectId: selectedProjectId,
      workflowSessionId: workflowSession._id,
      versionedWorkflowId: workflowDetails.workflow_id,
    };
    this.router.navigate(['/workflow-designer'], {
      queryParams,
    });
  }

  async onEditPublishedWorkflow(workflowDetails: any) {
    let dialogRef: any;
    let siteId = this.configService.SelectedSiteId;
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    let workflow: Workflow | undefined = await this.apiService.GetWorkflowById(
      siteId,
      selectedProjectId,
      workflowDetails.workflow_id,
    );
    if (!workflow) {
      return;
    }
    dialogRef = this.dialog.open(UpdateWorkflowComponent, {
      width: '500px',
      data: workflow,
    });

    dialogRef.afterClosed().subscribe(() => {
      setTimeout(() => {
        let selectedProjectId: string | undefined =
          this.configService.SelectedProjectId;
        if (!selectedProjectId) {
          return;
        }
        workflowDetails.name = workflow?.name;
        workflowDetails.description = workflow?.description;
      }, 1000);
    });
  }

  async onEditWorkflowSession(workflowSession: WorkflowSession) {
    let dialogRef: any;

    dialogRef = this.dialog.open(UpdateWorkflowSessionComponent, {
      width: '500px',
      data: workflowSession,
    });

    dialogRef.afterClosed().subscribe(() => {
      setTimeout(() => {
        let selectedProjectId: string | undefined =
          this.configService.SelectedProjectId;
        if (!selectedProjectId) {
          return;
        }
        this.sessionApi.GetWorkflowSessions(
          this.configService.SelectedSiteId,
          selectedProjectId,
        );
        this.onRefreshView();
      }, 1000);
    });
  }

  createNewWorkflowSession() {
    // this.IsCreatingNewWorkflowSession = true;
    let dialog: any;
    dialog = this.dialog.open(CreateNewWorkflowSessionComponent, {
      width: '500px',
      data: { isDuplicate: false }
    });
    dialog.afterClosed().subscribe((res: WorkflowSession) => {
      if (res) {
        const currentData = this.sessions;
        this.sessions = [...currentData, res];
        this.loadWorkflowSessions();
      }
    });
  }

  async onDeletePublishedWorkflow(workfowDetails: any) {
    await this.sessionApi.deleteWorkflow(workfowDetails.workflow_id)
    this.dialogRef.close()
    this.loadData()
  }

  async onDeleteWorkflowSession(session: WorkflowSession) {
    let id = session._id;
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    var result: any = await this.sessionApi.DeleteWorkflowSession(
      this.configService.SelectedSiteId,
      selectedProjectId,
      session._id!,
    );

    if (!result['success']) {
      this.toastr.error('Failed to delete workflow', 'ERROR', {
        positionClass: 'custom-toast-position',
      });
      return;
    } else {
      this.toastr.success('Workflow session deleted successfully', 'SUCCESS', {
        positionClass: 'custom-toast-position',
      });
      this.sessions = this.sessions.filter((session: { _id: string | null; }) => session._id !== id);
      this.dialogRef.close();
    }
  }

  async onViewPublishedWorkflowRuns(
    workflowDetails: any,
    workflowSession: WorkflowSession,
  ) {
    let dialogRef: any;

    dialogRef = this.dialog.open(PublishedWorkflowRunsComponent, {
      width: '600px',
      data: {
        workflowId: workflowDetails.workflow_id, // Use camelCase for JavaScript properties
        workflowSessionId: workflowSession._id,
      },
    });

    dialogRef.afterClosed().subscribe((queryParams: any) => {
      if (queryParams) {
        this.router.navigate(['/workflow-designer'], {
          queryParams,
        });
      }
    });
  }

  openConfirmationDialog(): void {
    this.dialogRef = this.dialog.open(this.confirmationDialogTemplate);
  }

  openVersionedConfirmationDialog(): void {
    this.dialogRef = this.dialog.open(this.versionedconfirmationDialogTemplate);
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  async sortData(sort: Sort) {
    const favoritedSessions = this.filteredSessionsData.filter(session =>
      session.favourited_by.includes(this.currentUser._id)
    );

    const nonFavoritedSessions = this.filteredSessionsData.filter(session =>
      !session.favourited_by.includes(this.currentUser._id)
    );

    nonFavoritedSessions.sort((a: any, b: any) => {
      let aValue: any = '';
      let bValue: any = '';

      if (sort.active === 'Name') {
        aValue = a.name;
        bValue = b.name;
      } else if (sort.active === 'Created By') {
        aValue = a.owner_name;
        bValue = b.owner_name;
      } else if (sort.active === 'Description') {
        aValue = a.description;
        bValue = b.description;
      } else if (sort.active === 'Version') {
        aValue = a.version;
        bValue = b.version;
      } else if (sort.active === 'Date Created') {
        aValue = new Date(a.created_at);
        bValue = new Date(b.created_at);
      } else if (sort.active === 'Last Modified') {
        aValue = new Date(a.last_modified_at);
        bValue = new Date(b.last_modified_at);
      } else {
        aValue = a[sort.active];
        bValue = b[sort.active];
      }

      const compareValues = (valueA: any, valueB: any) => {
        if (valueA == null && valueB == null) {
          return 0;
        }
        if (valueA == null) {
          return -1;
        }
        if (valueB == null) {
          return 1;
        }
        if (!isNaN(valueA) && !isNaN(valueB)) {
          return valueA - valueB;
        }
        const dateA = new Date(valueA);
        const dateB = new Date(valueB);
        if (!isNaN(dateA.getTime()) && !isNaN(dateB.getTime())) {
          return dateA.getTime() - dateB.getTime();
        }
        return String(valueA).localeCompare(String(valueB));
      };

      const comparisonResult = compareValues(aValue, bValue);
      return sort.direction === 'asc' ? comparisonResult : -comparisonResult;
    });
    this.filteredSessionsData = [...favoritedSessions, ...nonFavoritedSessions];
    this.sessions = new MatTableDataSource(this.filteredSessionsData);
  }

  lastAccessedDate(date: string) {
    if (date && date.endsWith && !date.endsWith('Z')) {
      date += 'Z';
      return Utils.formatDateTime(date);
    } else {
      return Utils.formatDateTime(date);
    }
  }

  isTemplateWorkflow(workflow: any) {
    return (workflow && ('is_template' in workflow) && workflow.is_template) ? true : false;
  }

  checkFavStatus(dataset: any): boolean {
    const currentUserID = this.currentUser._id;
    if (dataset.favourited_by) {
      const favoritedArr = dataset.favourited_by;
      return favoritedArr.includes(currentUserID);
    }
    return false;
  }

  async toggleSelection(data: any) {
    let favoriteStatus = false;
    const isUserFavorited = data.favourited_by.includes(this.currentUser._id);
    if (!isUserFavorited) {
      data.favourited_by.push(this.currentUser._id);
      favoriteStatus = true;
    } else {
      data.favourited_by = data.favourited_by.filter((id: any) => id !== this.currentUser._id);
      favoriteStatus = false;
    }
    const siteId = data.site_id;
    const projectId = data._id;

    try {
      await this.apiService.toggleFavoriteForWorkflow(siteId, projectId, this.currentUser._id, favoriteStatus, data._id).toPromise();
      this.sessions = this.sessions.map((session: any) => ({
        ...session
      }));
      this.sortWorkflowsSessionsByLastModified();
      this.sortSessions();
      this.toastr.success('Workflow favorite status updated successfully', 'SUCCESS', {
        positionClass: 'toast-top-right',
      });
    } catch (error) {
      console.error("Error in toggleSelection", error);
    }
  }

  sortSessions() {
    this.sessions.sort((a: { favourited_by: string | any[]; }, b: { favourited_by: string | any[]; }) => {
      const aIsFavorite = a.favourited_by.includes(this.currentUser._id);
      const bIsFavorite = b.favourited_by.includes(this.currentUser._id);
      if (aIsFavorite && !bIsFavorite) {
        return -1;
      } else if (!aIsFavorite && bIsFavorite) {
        return 1;
      } else {
        return 0;
      }
    });
  }
}
