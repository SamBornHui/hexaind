import { Component, Output, EventEmitter, Input, Inject } from '@angular/core';
import {
  Position,
  WorkflowClientTags,
} from 'src/app/pages/workflow-designer/client-tags';
import { ApiService } from '../../services/api.service';
import { ConfigService } from '../../services/config.service';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import {
  SessionWorkflow,
  WorkflowSession,
} from 'src/app/models/workflow-sessions-api-response.models';
import { ToastrService } from 'ngx-toastr';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { Observable, catchError, of } from 'rxjs';


@Component({
  selector: 'app-create-new-workflow-template',
  templateUrl: './create-new-workflow-template.component.html',
  styleUrls: ['./create-new-workflow-template.component.less'],
})
export class CreateNewWorkflowTemplateComponent {
  @Output() closeDialogClicked = new EventEmitter<any>();
  // @Output() workflowSessionCreatedEvent = new EventEmitter<WorkflowSession>();
  disableSubmit: boolean = true;
  workflowTemplateName: string = '';
  workflowTemplateDescription: string = '';
  selectedOwner: any;
  isCreatingWorkflowSession: boolean = false;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    private sharedDataService: SharedDataService,
    private sessionApi: WorkflowsSessionsApiService,
    private configService: ConfigService,
    public toaster: ToastrService,
    private apiService: ApiService,
    public dialogRef: MatDialogRef<CreateNewWorkflowTemplateComponent>,
    private router: Router,
  ) {}

  onClosePanel() {
    this.dialogRef.close();
  }

  workflowSessionNameError: string = '';
  workflowSessionDescriptionError: string = '';
  workflowSessionOwnerError: string = '';
  workflowSessionNameExistsError: string = '';

  public sessions: WorkflowSession[] = [];

  ngOnInit() {
  }


  creatingWorkflow: boolean = false;

  async onCreateWorkflowTemplate() {
    if (this.creatingWorkflow) {
      return;
    }
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    this.creatingWorkflow = true;

    this.workflowSessionNameError = '';
    this.workflowSessionDescriptionError = '';
    this.workflowSessionOwnerError = '';
    this.workflowSessionNameExistsError = '';
    let error: boolean = false;

    if (!this.workflowTemplateName) {
      this.workflowSessionNameError = 'Name is required.';
      error = true;
    }
    if (!this.workflowTemplateDescription) {
      this.workflowSessionDescriptionError = 'Description is required.';
      error = true;
    }

    let workflowClientTags: WorkflowClientTags = new WorkflowClientTags();
    workflowClientTags.StartWidgetPosition = new Position(150, 150);
    workflowClientTags.EndWidgetPosition = new Position(650, 150);

    let currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    if (!error) {
      this.isCreatingWorkflowSession = true;
      let workflowTemplate: any = {
        name:this.workflowTemplateName,
        description:this.workflowTemplateDescription,
        user_name:currentUser.first_name + ' ' + currentUser.last_name,
        user_id:currentUser._id.toString(),
        workflow_id:this.data.workflow_id,
        version_tag:'0.1'
      };

      let error: boolean = false;
      let createdTemplate: any | undefined = undefined;

      try {
        createdTemplate = await this.sessionApi.CreateWorkflowTemplate(
          this.configService.SelectedSiteId,
          selectedProjectId,
          this.data.sessionId,
          workflowTemplate,
          this.dataURLToBlob(this.data.screenshot)
        );
        if(createdTemplate){
          this.toaster.success('Workflow Template Created Successfully', 'Success', {
            positionClass: 'custom-toast-position',
          });
        }
      } catch {
        this.toaster.error('Failed to create workflow template', 'Success', {
          positionClass: 'custom-toast-position',
        });
      } 

      this.isCreatingWorkflowSession = false;
      this.dialogRef.close(createdTemplate);
    }

    this.creatingWorkflow = false;
  }

  validate() {
    this.workflowTemplateName = this.workflowTemplateName.trim();
    this.workflowTemplateDescription =
      this.workflowTemplateDescription.trim();
    if (
      this.workflowTemplateName.length == 0 ||
      this.workflowTemplateDescription.length == 0
    ) {
      this.disableSubmit = true;
    } else {
      this.disableSubmit = false;
    }
  }

  private dataURLToBlob(dataURL: string): Blob {
    const byteString = atob(dataURL.split(',')[1]);
    const mimeString = dataURL.split(',')[0].split(':')[1].split(';')[0];
    
    const arrayBuffer = new ArrayBuffer(byteString.length);
    const uint8Array = new Uint8Array(arrayBuffer);
    
    for (let i = 0; i < byteString.length; i++) {
      uint8Array[i] = byteString.charCodeAt(i);
    }
    
    return new Blob([arrayBuffer], { type: mimeString });
  }
}
