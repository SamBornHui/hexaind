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
import { HttpErrorResponse } from '@angular/common/http';
import { User } from 'src/app/models/user-models';

@Component({
  selector: 'app-create-new-workflow-session',
  templateUrl: './create-new-workflow-session.component.html',
  styleUrls: ['./create-new-workflow-session.component.less'],
})
export class CreateNewWorkflowSessionComponent {
  @Output() closeDialogClicked = new EventEmitter<any>();
  @Output() workflowSessionCreatedEvent = new EventEmitter<WorkflowSession>();
  disableSubmit: boolean = true;
  newWorkflowSessionName: string = '';
  newWorkflowSessionOwnerName: string = 'select';
  newWorkflowSessionDescription: string = '';
  selectedOwner: any;
  isCreatingWorkflowSession: boolean = false;
  isDuplicate: boolean = false;
  isExport: boolean = false;
  selectedProject: Project | undefined = undefined;
  projects: Project[] = [];
  user_id: any;
  isCpwOldWidget: boolean = false;
  isCpwCheck: boolean = false;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    private sharedDataService: SharedDataService,
    private sessionApi: WorkflowsSessionsApiService,
    private configService: ConfigService,
    public toaster: ToastrService,
    private apiService: ApiService,
    public dialogRef: MatDialogRef<CreateNewWorkflowSessionComponent>,
    private router: Router,
  ) {}

  onClosePanel() {
    this.dialogRef.close();
  }

  workflowSessionNameError: string = '';
  workflowSessionDescriptionError: string = '';
  workflowSessionOwnerError: string = '';
  workflowSessionNameExistsError: string = '';

  ownerNameArray = [
    { id: '1', name: 'Mike Snow' },
    { id: '1', name: 'Rohan Lam' },
    { id: '2', name: 'Kireeti Kunam' },
    { id: '3', name: 'Rahul Bachina' },
  ];

  public sessions: WorkflowSession[] = [];

  ngOnInit() {
    console.log(this.data)
    if(this.data && ('isDuplicate' in this.data)){
      this.isDuplicate = this.data.isDuplicate;}
    else if(this.data && ('isExport' in this.data)){
      this.isExport = this.data.isExport;
      this.checkWorkflowOldCpw();
    }
    const user = localStorage.getItem('currentUser');
    if (user) {
        const parsedUser = JSON.parse(user);
        this.user_id = parsedUser._id;
    } else {
        console.error('User information is not available in localStorage.');
    }
    this.getAllWorkflowSessions();
    this.loadProjects();
  }

  async checkWorkflowOldCpw (){
    let SelectedWorkflow = await this.sessionApi.GetWorkflowById(
      this.data.sessionId,
      this.data.project_id,
      this.data.workflow_id
    );
    this.isCpwOldWidget = SelectedWorkflow?.older_version_cpw_urns.length > 0
  }

  cpwCheckUpdate(checked: boolean){
    this.isCpwCheck = checked;
  }

  async loadProjects() {
    if (!this.user_id) {
      console.error('User ID is not defined. Cannot load projects.');
      return;}
    try {
      this.projects = await this.apiService.GetProjects(
        this.configService.SelectedSiteId,
        '',
        { id: this.user_id, get_details: true }
      );
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  }
  async getAllWorkflowSessions() {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (selectedProjectId) {
      this.sessions = await this.sessionApi.GetWorkflowSessions(
        this.configService.SelectedSiteId,
        selectedProjectId,
      );
    }
  }

  creatingWorkflow: boolean = false;

  async onCreateWorkflowSession() {
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

    var findObject = this.sessions.some(
      (obj: { name: any }) =>
        obj.name.toLowerCase() === this.newWorkflowSessionName.toLowerCase(),
    );

    if (findObject) {
      this.workflowSessionNameExistsError =
        'A session with that name already exists.';
      error = true;
    }

    if (!this.newWorkflowSessionName) {
      this.workflowSessionNameError = 'Name is required.';
      error = true;
    }
    if (!this.newWorkflowSessionDescription) {
      this.workflowSessionDescriptionError = 'Description is required.';
      error = true;
    }

    let workflowClientTags: WorkflowClientTags = new WorkflowClientTags();
    workflowClientTags.StartWidgetPosition = new Position(150, 150);
    workflowClientTags.EndWidgetPosition = new Position(650, 150);

    let currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    if (!error) {
      this.isCreatingWorkflowSession = true;
      let workflowSession: WorkflowSession = new WorkflowSession();
      workflowSession.name = this.newWorkflowSessionName;
      workflowSession.description = this.newWorkflowSessionDescription;
      workflowSession.owner_name =
        currentUser.first_name + ' ' + currentUser.last_name;
      workflowSession.owner_id = currentUser._id.toString();
      workflowSession.project_id = selectedProjectId;
      workflowSession.site_id = this.configService.SelectedSiteId;

      let error: boolean = false;
      let sessionId: string | undefined = undefined;
      try {
        sessionId = await this.sessionApi.CreateWorkflowSession(
          this.configService.SelectedSiteId,
          selectedProjectId,
          '1.0',
          this.newWorkflowSessionName,
          this.newWorkflowSessionDescription,
          workflowSession.owner_id!,
          workflowSession.owner_name!,
        );
      } catch {
        error = true;
      }      

      if (sessionId) {
        try {
          let workflowSession: WorkflowSession | undefined =
            await this.sessionApi.GetWorkflowSession(
              this.configService.SelectedSiteId,
              selectedProjectId,
              sessionId,
            );
          if (workflowSession) {
            let workflow: Workflow | undefined =
              await this.sessionApi.GetWorkflowById(
                this.configService.SelectedSiteId,
                selectedProjectId,
                workflowSession.workflow_id!,
              );
            if (workflow) {
              workflow.client_tags = workflowClientTags;
              workflow.owner_id = workflowSession.owner_id!;
              workflow.owner_name = workflowSession.owner_name!;

              await this.apiService.UpdateWorkflow(
                this.configService.SelectedSiteId,
                selectedProjectId,
                workflow,
                undefined,
              );
            }

            let queryParams = {
              siteId: 1,
              projectId: selectedProjectId,
              workflowSessionId: sessionId,
            };
            this.router.navigate(['/workflow-designer'], {
              queryParams,
            });
          }
        } catch {
          error = true;
        }
      }

      if (error) {
        this.toaster.error(
          this.sharedDataService.LastError ?? 'Unknown error',
          'Workflow Created Failed',
          {
            positionClass: 'custom-toast-position',
          },
        );
      } else {
        this.toaster.success('Workflow Created Successfully', 'Success', {
          positionClass: 'custom-toast-position',
        });
      }

      this.isCreatingWorkflowSession = false;
      this.dialogRef.close(workflowSession);
    }

    this.creatingWorkflow = false;
  }

  async onDuplicateWorkflow() {
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

    var findObject = this.sessions.some(
      (obj: { name: any }) =>
        obj.name.toLowerCase() === this.newWorkflowSessionName.toLowerCase(),
    );

    if (findObject) {
      this.workflowSessionNameExistsError =
        'A session with that name already exists.';
      error = true;
    }

    if (!this.newWorkflowSessionName) {
      this.workflowSessionNameError = 'Name is required.';
      error = true;
    }
    if (!this.newWorkflowSessionDescription) {
      this.workflowSessionDescriptionError = 'Description is required.';
      error = true;
    }
    let currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    if (!error) {
      this.isCreatingWorkflowSession = true;
      let workflowSession:any = {
        name:this.newWorkflowSessionName,
        description:this.newWorkflowSessionDescription,
        user_name:currentUser.first_name + ' ' + currentUser.last_name,
        user_id:currentUser._id.toString(),
        workflow_id:this.data.workflow_id,
        version_tag:'',
        is_template:this.data.is_template
      };

      let error: boolean = false;
      let savedWorkflow: string | undefined = undefined;
      try {
        savedWorkflow = await this.apiService.duplicateWorkflow(
          this.configService.SelectedSiteId,
          this.configService.SelectedProjectId,
          this.data.sessionId,
          this.data.type,
          workflowSession,
        );
      } catch {
        error = true;
      }      

      

      if (error) {
        this.toaster.error(
          this.sharedDataService.LastError ?? 'Unknown error',
          'Workflow Created Failed',
          {
            positionClass: 'custom-toast-position',
          },
        );
      } else {
        this.toaster.success('Workflow Created Successfully', 'Success', {
          positionClass: 'custom-toast-position',
        });
      }

      this.isCreatingWorkflowSession = false;
      this.dialogRef.close(savedWorkflow);
    }

    this.creatingWorkflow = false;
  }

  async onDownloadWorkflow() {
    if (this.creatingWorkflow) {
      return;
    }
  
    this.creatingWorkflow = true;
  
    const currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    const exportData = {
      user_name: `${currentUser.first_name} ${currentUser.last_name}`,
      user_id: currentUser._id.toString(),
      workflow_id: this.data.workflow_id,
      token: currentUser.access_token
    };
    
    try {
      const exportedBlob = await this.apiService.exportWorkflowData(
        this.configService.SelectedSiteId,
        this.data.project_id, 
        this.data.sessionId,
        this.data.type,
        exportData
      );
  
      if (exportedBlob) {
        const exportedFileUrl = URL.createObjectURL(exportedBlob);
        const a = document.createElement('a');
        a.href = exportedFileUrl;
        a.download = `workflow_download.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        this.toaster.success('Workflow downloaded successfully', 'Success', {
          positionClass: 'custom-toast-position'
        });
      }
    } catch (error) {
      console.error('Failed to download the workflow:', error);
      this.toaster.error('Failed to download the workflow', 'Download Failed', {
        positionClass: 'custom-toast-position'
      });
    }
  
    this.creatingWorkflow = false;
  }
  async onExportWorkflow() {
    if (this.creatingWorkflow) {
      return;
    }
    if (!this.selectedProject) {
      this.toaster.error('Please select a project for export.', 'Error');
      return;
    } 
    this.creatingWorkflow = true;
    this.workflowSessionNameError = '';
    this.workflowSessionDescriptionError = '';
    this.workflowSessionOwnerError = '';
    this.workflowSessionNameExistsError = '';
    let error: boolean = false;
    // Check if a workflow with the same name already exists
    const findObject = this.sessions.some(
      (obj: { name?: string }) => (obj.name ?? '').toLowerCase() === this.newWorkflowSessionName.toLowerCase()
    );
    if (findObject) {
      this.workflowSessionNameExistsError = 'A session with that name already exists.';
      error = true;
    }
    // Validate required fields: Name and Description
    if (!this.newWorkflowSessionName) {
      this.workflowSessionNameError = 'Name is required.';
      error = true;
    }
    if (!this.newWorkflowSessionDescription) {
      this.workflowSessionDescriptionError = 'Description is required.';
      error = true;
    }
    const currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    if (!error) {
      this.isCreatingWorkflowSession = true;
  
      const exportData = {
        name: this.newWorkflowSessionName,
        description: this.newWorkflowSessionDescription,
        user_name: `${currentUser.first_name} ${currentUser.last_name}`,
        user_id: currentUser._id.toString(),
        workflow_id: this.data.workflow_id,
        version_tag: '',
        is_template: this.data.is_template,
        token: currentUser.access_token,
        project_id: this.selectedProject.project_id
      };
      console.log("*****************")
      console.log(exportData)
      try {
        const exportedBlob = await this.apiService.exportWorkflowData(
          this.configService.SelectedSiteId,
          this.selectedProject.project_id,
          this.data.sessionId,
          this.data.type,
          exportData
        );
  
        if (exportedBlob) {
          const importData = {
            user_id: currentUser._id.toString(),
            user_name: `${currentUser.first_name} ${currentUser.last_name}`,
            workflow_name: this.newWorkflowSessionName,
            workflow_description: this.newWorkflowSessionDescription,
            token: currentUser.access_token
          };
  
          const zipFile = new File([exportedBlob], `${this.newWorkflowSessionName}.zip`, { type: 'application/zip' });
          await this.apiService.importWorkflowData(
            this.configService.SelectedSiteId,
            this.selectedProject.project_id,
            zipFile,
            importData
          );
  
          this.toaster.success('Workflow exported and imported successfully', 'Success', {
            positionClass: 'custom-toast-position'
          });
        }
      } catch (error) {
        console.error("Error during export/import:", error);
        this.toaster.error(
          this.sharedDataService.LastError ?? 'Unknown error occurred during export or import.',
          'Export/Import Failed',
          { positionClass: 'custom-toast-position' }
        );
      }
  
      this.isCreatingWorkflowSession = false;
      this.dialogRef.close();
    }
  
    this.creatingWorkflow = false;
  
  }
  validate() {
    this.newWorkflowSessionName = this.newWorkflowSessionName.trim();
    this.newWorkflowSessionDescription =
      this.newWorkflowSessionDescription.trim();
    if (
      this.newWorkflowSessionName.length == 0 ||
      this.newWorkflowSessionDescription.length == 0
    ) {
      this.disableSubmit = true;
    } else {
      this.disableSubmit = false;
    }
  }
}
