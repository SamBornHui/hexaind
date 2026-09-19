import { Component, Output, Input, EventEmitter, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { ConfigService } from 'src/app/services/config.service';
import { WorkflowSession } from 'src/app/models/workflow-sessions-api-response.models';
import { Project } from 'src/app/models/project-models';
import { ToastrService } from 'ngx-toastr';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { UsersService } from 'src/app/pages/users/users.service';
import { lastValueFrom } from 'rxjs';

@Component({
  selector: 'app-update-workflow',
  templateUrl: './update-workflow-session.component.html',
  styleUrls: ['./update-workflow-session.component.less'],
})
export class UpdateWorkflowSessionComponent {
  @Output() closeDialogClicked = new EventEmitter<any>();
  @Output() workflowSessionCreatedEvent = new EventEmitter<any>();

  public newWorkflowSessionName: string = '';
  public ownerName: string = 'select';
  public newWorkflowSessionDescription: string = '';
  public isCreatingWorkflowSession: boolean = false;
  public workflowSessionNameError: string = '';
  public workflowSessionDescriptionError: string = '';
  public workflowSessionOwnerError: string = '';
  ownerNameArray: any = [];
  selectedOwner: any;
  workflowName: any = this.workflowSession.name;
  workflowDesription: any = this.workflowSession.description;
  updateButton: boolean = true;

  constructor(
    private usersService: UsersService,
    private sharedDataService: SharedDataService,
    private configService: ConfigService,
    public sessionApi: WorkflowsSessionsApiService,
    public dialogRef: MatDialogRef<UpdateWorkflowSessionComponent>,
    public toaster: ToastrService,
    @Inject(MAT_DIALOG_DATA) public workflowSession: WorkflowSession,
  ) {}

  ngOnInit() {
    this.loadUsers();
  }

  async loadUsers() {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    const jsonData = {
      id: selectedProjectId,
      get_details: true,
      search_term: '',
      page_number: 1,
      page_limit: 100,
    };

    this.usersService.getProjectData(jsonData).subscribe(userData => {
      userData.mappings.forEach((user : any) => {
        if (user.user_name && user.user_id) {
          this.ownerNameArray.push({ id: user.user_id, name: user.user_name });
        }
      });
    });
    
  }

  onClosePanel() {
    this.dialogRef.close();
    this.loadUsers();
  }

  handleChange(){
    this.workflowName = this.workflowName.trim();
    this.workflowDesription = this.workflowDesription.trim();
    if(this.workflowName && this.workflowDesription){
      this.updateButton = false;
    }
  }

  async onUpdateWorkflowSession() {
    if (!this.workflowSession._id) {
      return;
    }

    this.workflowSessionNameError = '';
    this.workflowSessionDescriptionError = '';
    this.workflowSessionOwnerError = '';
    let error: boolean = false;
    let siteId = this.configService.SelectedSiteId;
    let selectedProjectId = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    let getWorkflowSession = await this.sessionApi.GetWorkflowSession(
      siteId,
      selectedProjectId,
      this.workflowSession._id,
    );
    let originalWorkflowName = getWorkflowSession?.name;
    let getAllWorkflowSessions = await this.sessionApi.GetWorkflowSessions(
      siteId,
      selectedProjectId,
    );

    if (
      this.workflowName?.toLowerCase() !==
      originalWorkflowName?.toLowerCase()
    ) {
      var findObject = getAllWorkflowSessions.some(
        (obj: { name: any }) =>
          obj.name.toLowerCase() === this.workflowName?.toLowerCase(),
      );
      if (findObject) {
        this.workflowSessionNameError =
          'A session with that name already exists.';
        error = true;
      }
    }

    this.workflowName = this.workflowName?.trim();
    if (!this.workflowName) {
      this.workflowSessionNameError = 'Name is required.';
      error = true;
    }
    this.workflowDesription = this.workflowDesription?.trim();
    if (!this.workflowDesription) {
      this.workflowSessionDescriptionError = 'Description is required.';
      error = true;
    }
    /*if (!this.selectedOwner || this.selectedOwner?.name == '') {
      this.workflowSessionOwnerError = 'Owner name is required.';
      error = true;
    } else {
      this.workflowSession.owner_id = this.selectedOwner?.id;
      this.workflowSession.owner_name = this.selectedOwner?.name;
    }*/
    if (!error) {
      this.onClosePanel();
      this.workflowSession.name = this.workflowName;
      this.workflowSession.description = this.workflowDesription;
      let selectedProjectId: string | undefined =
        this.configService.SelectedProjectId;
      if (!selectedProjectId) {
        return;
      }
      try {
        await this.sessionApi.UpdateWorkflowSession(
          this.configService.SelectedSiteId,
          selectedProjectId,
          this.workflowSession._id,
          this.workflowSession.version ?? '1',
          this.workflowSession.name!,
          this.workflowSession.description!,
          this.workflowSession.owner_id!,
          this.workflowSession.owner_name!,
        );
      } catch {
        if (this.sharedDataService.LastError) {
          this.toaster.error(
            'An error occurred: ' + this.sharedDataService.LastError,
            '',
            {
              positionClass: 'custom-toast-position',
            },
          );
          return;
        }
      }
      this.toaster.success('Workflow Updated Successfully', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }
}
