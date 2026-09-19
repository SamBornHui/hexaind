import { Component, AfterViewInit, ViewChild } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { ConfigService } from 'src/app/services/config.service';
import { ActivatedRoute, Router } from '@angular/router';
import { MatMenuTrigger } from '@angular/material/menu';
import { ToastrService } from 'ngx-toastr';
import { Project } from 'src/app/models/project-models';
import { MatDialog } from '@angular/material/dialog';
import { CreateNewScheduleComponent } from 'src/app/dialogs/create-schedule/create-schedule.component';
import { ViewScheduleComponent } from 'src/app/dialogs/view-schedule/view-schedule.component';
import { Subscription } from 'rxjs';
import { Utils } from 'src/app/utils';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { RunSummaryComponent } from 'src/app/dialogs/run-summary/run-summary.component';
import { WorkflowCanvasService } from '../workflow-designer/workflow-canvas.service';
import { DataSetResultsComponent } from 'src/app/dialogs/data-set-results/data-set-results/data-set-results.component';
import { VersionedWorkflowRunStatus, WorkflowRunStatus } from 'src/app/models/workflow-sessions-api-response.models';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';


@Component({
  selector: 'app-jobs',
  templateUrl: './jobs.component.html',
  styleUrls: ['./jobs.component.less'],
})
export class JobsComponent {
  sortDirection: 'asc' | 'desc' = 'asc';
  searchTerms: any;
  descending: boolean | undefined;
  public deleteConfirmation: boolean = false;
  public cancelConfirmation: boolean = false;
  getShceduledJobs: any;
  currentProject: any;
  statusFilter: string | null = null;
  frequencyFilter: string | null = null;
  uniqueCreatedBy: string[] = [];
  isJobsLoaded: boolean = false;
  jobsLength: any;

  private projectSubscription: Subscription | undefined = undefined;
  displayedColumns: string[] = [
    'job',
    'run_id',
    'version',
    'workflow',
    'scheduled_by',
    'status',
    'frequency',
    'last_run',
    'scheduled_time',
    'results',
    'actions',
  ];
  isNewSchedule: boolean = false;
  workflows: any = [];
  isWorkflowApi: boolean = false;
  dataSource: MatTableDataSource<any> = new MatTableDataSource<any>();
  @ViewChild(MatSort, { static: true })
  sort!: MatSort;
  SelectedWorkflow: any;
  constructor(private sessionApiService: WorkflowsSessionsApiService,public workflowCanvasService: WorkflowCanvasService,private router: Router,private apiService: ApiService, private dialog: MatDialog, private configService: ConfigService, private route: ActivatedRoute, public toaster: ToastrService,) {
  
  }

  async ngOnInit() {
    this.dataSource.sort = this.sort
    await this.loadschedules(undefined);
    this.projectSubscription =
      this.configService.selectedProjectIdObservable.subscribe((projectId) => {
        if (projectId) {
          this.loadschedules(undefined);
        }
      });

    const job_id = this.route.snapshot.queryParams['job_id'];    
    if (job_id) {
      let selectedJob = this.getShceduledJobs.find((selected_id: any) => selected_id._id === job_id)
      this.viewSchedule(selectedJob);
    }
    this.allowSchedule();
  }

  async allowSchedule(){
    this.isWorkflowApi = false;
    try {
      let selectedProject = this.configService.SelectedProjectId;
      if (selectedProject) {
        this.workflows = await this.apiService.GetWorkflows(undefined);
        this.isNewSchedule = !!(this.workflows && this.workflows.length);
      }
    } catch (error) {
      console.error("Error loading workflow sessions:", error);
    }
    finally{
      this.isWorkflowApi = true;
    }
  }

  ngAfterViewInit() {
  }

  async redirectToPage(data:any) {
    this.loadVersionedWorkflowRunStatus(data);
    this.SelectedWorkflow = await this.sessionApiService.GetWorkflowById(
      data.site_id,
      data.project_id,
      data.workflow_id!,
    );
    this.workflowCanvasService.SelectedWorkflow = this.SelectedWorkflow;
    this.workflowCanvasService.ViewingRunId = data.run_id;
  }

  
  async loadVersionedWorkflowRunStatus(data: any) { 
    let workflowSessionRunStatus: VersionedWorkflowRunStatus | undefined =
      await this.apiService.GetVersionedWorkflowRunStatus(
        this.configService.SelectedSiteId,
        this.configService.SelectedProjectId!,
        this.workflowCanvasService.SelectedWorkflow?._id!,
        data.run_id,
      );

    if (workflowSessionRunStatus) {
      let workflowRunStatus: WorkflowRunStatus = new WorkflowRunStatus();
      workflowRunStatus.widgets_status =
        workflowSessionRunStatus.widgets_status;
      workflowRunStatus.workflow = workflowSessionRunStatus.workflow;
      workflowRunStatus.run_status = 'RUNNING';

      if (
        workflowRunStatus.widgets_status.some(
          (widgetStatus) => widgetStatus.status === 'RUNNING',
        )
      ) {
        workflowRunStatus.run_status = 'RUNNING';
      } else if (
        workflowRunStatus.widgets_status.some(
          (widgetStatus) => widgetStatus.status === 'FAILED',
        )
      ) {
        workflowRunStatus.run_status = 'FAILED';
      } else if (
        workflowRunStatus.widgets_status.some(
          (widgetStatus) => widgetStatus.status === 'PAUSED',
        )
      ) {
        workflowRunStatus.run_status = 'PAUSED';
      } else if (
        workflowRunStatus.widgets_status.some(
          (widgetStatus) => widgetStatus.status === 'IDLE',
        )
      ) {
        workflowRunStatus.run_status = 'NOT RUN';
      } else {
        workflowRunStatus.run_status = 'SUCCEEDED';
      }
      this.workflowCanvasService.WorkflowRunStatus = workflowRunStatus;
      this.onViewRunSummary();
    }
  }

  onViewRunSummary() {
    const dialogRef = this.dialog.open(RunSummaryComponent, {
      width: '500px',
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result && result.viewDataset) { 
          this.onPreviewDatasetResultsForWorkflowVersion();        
      }
    });
  }

  onPreviewDatasetResultsForWorkflowVersion() { 
    let dialogRef: any;
    dialogRef = this.dialog.open(DataSetResultsComponent, {
      width: '800px',
      data: {
        workflowSessionid:
          'this.workflowCanvasService.SelectedWorkflowSession?._id',
          workflowId: this.workflowCanvasService.SelectedWorkflow?._id,
          runId: this.workflowCanvasService.ViewingRunId,
      },
    });

    dialogRef.afterClosed().subscribe(() => {});
  }


  applyFilter(event: Event) {
    if (event.target instanceof HTMLInputElement) {
      const filterValue = event.target.value.trim().toLowerCase();

      // If the dataSource has a paginator, reset it back to the first page
      if (this.dataSource.paginator) {
        this.dataSource.paginator.firstPage();
      }

      // Or, if you have specific fields to filter on, you can do something like this:
      this.dataSource.filter = filterValue;
      this.dataSource.filterPredicate = (data: any, filter: string) => {
        const searchString = filter.toLowerCase();
        return (
          (data.name && data.name.toLowerCase().includes(searchString)) ||
          (data.run_id && data.run_id.toLowerCase().includes(searchString)) ||
          (data.version && data.version.toLowerCase().includes(searchString)) ||
          (data.workflow_name && data.workflow_name.toLowerCase().includes(searchString)) ||
          (data.created_by_name && data.created_by_name.toLowerCase().includes(searchString)) ||
          (data.schedule_status && data.schedule_status.toLowerCase().includes(searchString)) ||
          (data.schedule_type && data.schedule_type.toLowerCase().includes(searchString)) ||
          (data.run_created_at && data.run_created_at.toLowerCase().includes(searchString)) ||
          (data.next_run && data.next_run.toLowerCase().includes(searchString))
        );
      };
    }
  }

  applyStatusFilter() {
    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
    this.dataSource.filterPredicate = (data: any) => {
      if (this.statusFilter) {
        return data.schedule_status === this.statusFilter;
      } else {
        return true;
      }
    };
    if (this.statusFilter !== null) {
      this.dataSource.filter = this.statusFilter;
    }
  }

  applyFrequencyFilter() {
    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
    this.dataSource.filterPredicate = (data: any) => {
      if (this.frequencyFilter) {
        return data.schedule_type === this.frequencyFilter;
      } else {
        return true;
      }
    };
    this.dataSource.filter = this.frequencyFilter || '';
  }

  toggleSortOrder() {
    this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    this.dataSource.sort = this.sort;
    this.dataSource.sort.active = 'run_created_at';
    this.dataSource.sort.direction = this.sortDirection;
  }

  applyCreatedByFilter(createdBy: string): void {
    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }

    // Apply filter to the data source
    this.dataSource.filter = createdBy.trim().toLowerCase();
  }

  convertFromUTC = (utcDateTime: string) => {
    const [datePart, timePart] = utcDateTime.split(' ');
    const [year, month, day] = datePart.split('-').map(Number);
    const [hours, minutes, seconds] = timePart.split(':').map(Number);

    const utcDate = new Date(Date.UTC(year, month - 1, day, hours, minutes, seconds));  
    return utcDate.toISOString();
  };

  async loadschedules(searchTerms: string | undefined) {
    this.isJobsLoaded = false;
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const jsonData = {
      "get_details": true
    }
    this.getShceduledJobs = await this.apiService.getScheduledJobs('1', selectedProjectId, jsonData);
    // TODO(Radha)
    // this.getShceduledJobs.forEach((schedule: { next_run: any; run_created_at: any }) => {
    //   schedule.next_run = Utils.formatDateTime(schedule.next_run);
    //   schedule.run_created_at = Utils.formatDateTime(schedule.run_created_at);
    // });
    this.jobsLength = this.getShceduledJobs.length;
    this.isJobsLoaded = true;
    this.dataSource = new MatTableDataSource(this.getShceduledJobs);
    this.uniqueCreatedBy = Array.from(new Set(this.dataSource.data.map(item => item.created_by_name)));
  }

  async onSearchTextChange(event: Event) {

  }

  getNumberOfColumns(): number {
    let screenWidth = window.innerWidth;
    let tileCount = Math.floor(screenWidth / 220);
    return tileCount;
  }

  onToggleSort() {
    this.descending = !this.descending;
    this.sortCustomWidgetsByLastModified();
  }
  sortCustomWidgetsByLastModified() {
    throw new Error('Method not implemented.');
  }

  onRefreshView() {
    console.log("refresh view");
    this.loadschedules(undefined);
  }

  createNewSchedule(rowdata: any, isEdit: boolean) {
    const dialogRef = this.dialog.open(CreateNewScheduleComponent, {
      width: '1370px',
      maxWidth: '1370px', // Ensures the dialog is responsive on smaller screens
      disableClose: true,
      data: { isEdit, rowData: isEdit ? rowdata : null }
    });
  
    dialogRef.componentInstance.addEvent.subscribe((result: any) => {
      this.onRefreshView();
    });
  }
  

  viewSchedule(data: any) { console.log(data,"get data");
    const dialogRef = this.dialog.open(ViewScheduleComponent, {
      width: '1200px',
      disableClose: true,
      data: { workflow_id: data.workflow_id, run_id: data.run_id, workflow_name: data.workflow_name }
    });
    // Todo: Radha will double check if this is needed
    // dialogRef.componentInstance.addEvent.subscribe((result: any) => {
    // });
  }

  lastLoginDate(last_login_date: string) {
    if (!last_login_date) return null;
    const date = Utils.formatDateTime(last_login_date);
    return date;
  }

  editSchedule(rowdata: any, isEdit: boolean) {
    const dialogRef = this.dialog.open(CreateNewScheduleComponent, {
      width: '1200px',
      disableClose: true,
      data: { isEdit, rowData: isEdit ? rowdata : null }
    });
    dialogRef.componentInstance.addEvent.subscribe((result: any) => {
      this.onRefreshView();
    });
  }

  async deleteScheduler(schedule: any): Promise<void> {
    try {
      let selectedProjectId: string | undefined =
        this.configService.SelectedProjectId;
      if (!selectedProjectId) {
        return;
      }
      const schedule_id: string = schedule._id;
      await this.apiService.DeleteScheduleId('1', selectedProjectId, schedule_id);
      this.toaster.success('Schedule Deleted Successfully', '', {
        positionClass: 'custom-toast-position',
      });
    } catch (error) {
      console.error('Failed to delete project', error);
      this.toaster.error('Error Deleting Schedule', '', {
        positionClass: 'custom-toast-position',
      });
      throw error;
    }
    this.onRefreshView();
  }

  async cancelScheduler(schedule: any): Promise<void> {
    try {
      let selectedProjectId: string | undefined =
        this.configService.SelectedProjectId;
      if (!selectedProjectId) {
        return;
      }
      const jsonData = {
        schedule_id: schedule._id,
        is_paused: true
      }
      await this.apiService.CancelScheduleId('1', selectedProjectId, jsonData);
      this.toaster.success('Schedule Deleted Successfully', '', {
        positionClass: 'custom-toast-position',
      });
    } catch (error) {
      console.error('Failed to delete project', error);
      this.toaster.error('Error Deleting Schedule', '', {
        positionClass: 'custom-toast-position',
      });
      throw error;
    }
    this.closeCancelConfirmation();
    this.onRefreshView();
  }

  closeCancelConfirmation() {
    this.cancelConfirmation = false;
  }

  formatDateTime(dateTimeString: string): string {
    const date = new Date(dateTimeString);

    // Get day, month, and year
    const day = date.getDate();
    const month = date.getMonth() + 1; // Months are zero-based
    const year = date.getFullYear();

    // Get hours and minutes
    let hours = date.getHours();
    const minutes = date.getMinutes();

    // Convert hours to 12-hour format and determine A.M. or P.M.
    const amOrPm = hours >= 12 ? 'P.M' : 'A.M';
    hours = hours % 12 || 12; // Convert 0 to 12 for 12-hour clock

    // Format the date and time string
    return `${day < 10 ? '0' + day : day}/${month < 10 ? '0' + month : month}/${year} ${hours}:${minutes < 10 ? '0' + minutes : minutes}${amOrPm}`;
  }

resetConfirmations() {
  this.deleteConfirmation = false;
  this.cancelConfirmation = false;
}


}

