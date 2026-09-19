import { Component, Output, Input, EventEmitter, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ConfigService } from 'src/app/services/config.service';
import { Project } from 'src/app/models/project-models';
import { ToastrService } from 'ngx-toastr';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { UsersService } from 'src/app/pages/users/users.service';
import { ApiService } from 'src/app/services/api.service';
import { Workflow } from 'src/app/models/workflow-models';

@Component({
  selector: 'app-update-workflow',
  templateUrl: './update-workflow.component.html',
  styleUrls: ['./update-workflow.component.less'],
})
export class UpdateWorkflowComponent {
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
  selectedOwner: any = undefined;
  workflowName: any = this.workflow.name;
  workflowDesription: any = this.workflow.description;
  updateButton: boolean = true;

  constructor(
    private usersService: UsersService,
    private sharedDataService: SharedDataService,
    private configService: ConfigService,
    public apiService: ApiService,
    public dialogRef: MatDialogRef<UpdateWorkflowComponent>,
    public toaster: ToastrService,
    @Inject(MAT_DIALOG_DATA) public workflow: Workflow,
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

  handleChange(){
    this.workflowName = this.workflowName.trim();
    this.workflowDesription = this.workflowDesription.trim();
    if(this.workflowName && this.workflowDesription){
      this.updateButton = false;
    }
  }

  onClosePanel() {
    this.dialogRef.close();
  }

  async onUpdateWorkflow() {
    if (!this.workflow._id) {
      return;
    }

    this.workflowSessionNameError = '';
    this.workflowSessionDescriptionError = '';
    this.workflowSessionOwnerError = '';
    let error: boolean = false;
    this.workflowName = this.workflowName.trim();
    let selectedProjectId = this.configService.SelectedProjectId;

    if (!selectedProjectId) {
      return;
    }

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
      this.workflow.owner_id = this.selectedOwner?.id;
      this.workflow.owner_name = this.selectedOwner?.name;
    }*/
    if (!error) {
      this.onClosePanel();
      this.workflow.name = this.workflowName;
      this.workflow.description = this.workflowDesription;
      let selectedProjectId: string | undefined =
        this.configService.SelectedProjectId;
      if (!selectedProjectId) {
        return;
      }
      try {
        await this.apiService.UpdateWorkflowFields(
          this.configService.SelectedSiteId,
          selectedProjectId,
          this.workflow,
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
