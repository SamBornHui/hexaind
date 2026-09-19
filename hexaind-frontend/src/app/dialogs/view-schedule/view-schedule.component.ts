import { Component, Output, EventEmitter, Inject, OnInit } from "@angular/core";
import { ApiService } from "src/app/services/api.service";
import { MatDialogRef, MAT_DIALOG_DATA } from "@angular/material/dialog";
import { ToastrService } from "ngx-toastr";
import { ConfigService } from 'src/app/services/config.service';
import { WorkflowsSessionsApiService } from "src/app/services/workflow-sessions-api.service";

@Component({
  selector: 'app-view-schedule',
  templateUrl: './view-schedule.component.html',
  styleUrls: ['./view-schedule.component.less'],
})
export class ViewScheduleComponent implements OnInit {
  @Output() closePanelClicked = new EventEmitter<any>();
  addEvent: any;
  runStatus: any;
  schedule_data: any;
  workflow_data: any;
  error_des: any;
  constructor(
    private dialogRef: MatDialogRef<ViewScheduleComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,  // Inject the project data
    private apiService: ApiService,
    public toaster: ToastrService,
    private configService: ConfigService,
    private workflowssessionsspiservice : WorkflowsSessionsApiService
  ) {
    this.workflow_data = data;
   }

  ngOnInit(): void {
    this.loadRunStatus(this.data);
  }

  async loadRunStatus(data: any) {
    //TODO(Radha) 
    // this.runStatus = await this.apiService.GetVersionedWorkflowRunStatus('1',selectedProjectId,this.data.workflow_id, this.data.run_id);
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    this.schedule_data = await this.apiService.getScheduleByIdFilterByRunId('1', selectedProjectId, data);
    
    if(this.schedule_data.failed_widget_urn != null){
      this.runStatus = await this.workflowssessionsspiservice.GetVersionedWorkflowWidgetRunStatus('1',selectedProjectId,this.data.workflow_id, this.data.run_id,this.schedule_data.failed_widget_urn );
      this.error_des = this.runStatus[0].result_value.error_description;
    }
  }

  convertFromUTC = (utcDateTime: string) => {
    if (utcDateTime) {
      const [datePart, timePart] = utcDateTime.split('T');
      const [year, month, day] = datePart.split('-').map(Number);
      const [hours, minutes, secondsWithMilliseconds] = timePart.split(':');
      const [seconds, milliseconds] = secondsWithMilliseconds.split('.').map(Number);
  
      const localDate = new Date(Date.UTC(year, month - 1, day, Number(hours), Number(minutes), seconds));
      return localDate.toLocaleString();
    }

    return "";
  };
}
