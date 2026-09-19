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
import { Project } from 'src/app/models/project-models';
import { ToastrService } from 'ngx-toastr';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { Workflow } from 'src/app/models/workflow-models';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { Router } from '@angular/router';

@Component({
  selector: 'app-share-workflow-template',
  templateUrl: './share-workflow-template.component.html',
  styleUrls: ['./share-workflow-template.component.less'],
})
export class ShareWorkflowTemplateComponent {
  disableSubmit: boolean = true;
  isSharingWorkflowTemplate: boolean = false;
  selectedProject: string = '';
  projects: Project[] = [];
  user_id: any;
  userInfo: any;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    private sharedDataService: SharedDataService,
    private sessionApi: WorkflowsSessionsApiService,
    private configService: ConfigService,
    public toaster: ToastrService,
    private apiService: ApiService,
    public dialogRef: MatDialogRef<ShareWorkflowTemplateComponent>,
    private router: Router,
  ) {}

  onClosePanel() {
    this.dialogRef.close();
  }

  ngOnInit() {
    let user: any = localStorage.getItem('currentUser');
    this.userInfo = JSON.parse(user);
    this.user_id = this.userInfo._id;
    this.loadProjects();
  }


  async loadProjects() {
    const jsonData = {
      id: this.user_id,
      get_details: true,
    };

    this.projects = await this.apiService.GetProjects(
      this.configService.SelectedSiteId,
      '',
      jsonData,
    );

  }

  async onShareWorkflowTemplate() {

    if(this.selectedProject ==''){
      this.toaster.error('Please select project', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }

    this.isSharingWorkflowTemplate = true;

    try {
      // let createdTemplate = await this.sessionApi.CreateWorkflowTemplate(
      //   this.configService.SelectedSiteId,
      //   selectedProjectId,
      //   this.data.sessionId,
      //   workflowTemplate
      // );
      // if(createdTemplate){
      //   this.toaster.success('Workflow Template Created Successfully', 'Success', {
      //     positionClass: 'custom-toast-position',
      //   });
      // }
      this.isSharingWorkflowTemplate = false;
    } catch {
      this.toaster.error('Failed to share workflow template', '', {
        positionClass: 'custom-toast-position',
      });
      this.isSharingWorkflowTemplate = false;
    } 
  }
}
