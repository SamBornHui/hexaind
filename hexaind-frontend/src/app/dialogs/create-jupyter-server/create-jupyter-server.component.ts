import { Component, Output, EventEmitter, Inject, OnInit } from "@angular/core";
import { Project } from "src/app/models/project-models";
import { ApiService } from "src/app/services/api.service";
import { MatDialogRef, MAT_DIALOG_DATA } from "@angular/material/dialog";
import { ToastrService } from "ngx-toastr";
import { SnackBarNotificationService } from "src/app/services/snack-bar-notification.service";
import { UsersService } from "src/app/pages/users/users.service";
import { ConfigService } from "src/app/services/config.service";


@Component({
  selector: 'app-create-jupyter-server',
  templateUrl: './create-jupyter-server.component.html',
  styleUrls: ['./create-jupyter-server.component.less'],
})
export class CreateJupyterServer {
  @Output() closePanelClicked = new EventEmitter<any>();
  @Output() projectCreatedEvent = new EventEmitter<Project>();

  newProjectName: string = '';
  newProjectDescription: string = '';
  newProjectOwnerName: string = 'select';
  updateButton: any;
  getProjectAdmins: any;
  projects: any = [];
  singleProject: any =[];
  projectId: any;

  isCreatingProject: boolean = false;
  user: any;
  userInfo: any;
  constructor(
    private dialogRef: MatDialogRef<CreateJupyterServer>,
    @Inject(MAT_DIALOG_DATA)
    public data: {
      update: any;
      project: Project;
    }, // Inject the project data
    private apiService: ApiService,
    public toaster: ToastrService,
    private snackBarNotification: SnackBarNotificationService,
    private usersService: UsersService,
    private configService: ConfigService
  ) {}

  ngOnInit(): void {
    this.user = localStorage.getItem('currentUser');
    this.projectId = this.configService.SelectedProjectId;
    console.log(this.projectId,"get data list");
    this.userInfo = JSON.parse(this.user);
    if (this.data.project != undefined) {
      this.newProjectName = this.data.project.project_name || "";
      this.newProjectDescription = this.data.project.description || "";
      this.newProjectOwnerName =  this.userInfo._id || "";
      this.updateButton = this.data.update;
    }
    this.getAllProject();
  }

  async getAllProject() {
    const jsonData = {      
      "id": this.userInfo._id,
      "get_details": true
    };
    this.projects = await this.apiService.GetProjects('1', undefined, jsonData);
  }

  onClosePanel() {
    this.closePanelClicked.emit();
    this.dialogRef.close({ success: true });
  }

  projectNameError: string = '';
  projectDescriptionError: string = '';
  projectNameExistsError: string = '';
  modified_count: any;

  async onCreateProject() {
    this.projectNameError = '';
    this.projectDescriptionError = '';
    this.projectNameExistsError = '';
    this.modified_count = '10';
    let error: boolean = false;

    var findObject = this.projects.some(
      (obj: { project_name: any }) =>
        obj.project_name.toLowerCase() === this.newProjectName.toLowerCase(),
    );

    if (findObject) {
      this.projectNameExistsError = 'Server name is already exists.';
      error = true;
    }
    this.newProjectName = this.newProjectName.trim();
    if (!this.newProjectName) {
      this.projectNameError = 'Server name is required.';
      error = true;
    }
    this.newProjectDescription = this.newProjectDescription.trim();
    if (!this.newProjectDescription) {
      this.projectDescriptionError = 'Description is required.';
      error = true;
    }
    
    if (!error) {
    try{
      this.isCreatingProject = true;      
      const jsonData = {      
        "name": this.newProjectName,
        "description": this.newProjectDescription
      };
      let response:any = await this.apiService.CreateJupyterServer("1",  jsonData, this.projectId);
      if(response.status == 'RUNNING'){
        this.onClosePanel();
        this.toaster.success('Server Created Successfully', '',{
          positionClass: 'custom-toast-position'
        });
      }else{
        this.toaster.error('Error Creating Server', '',{
          positionClass: 'custom-toast-position' 
        });
      }
    } catch (error) {
      this.toaster.error('Error Creating Server', '',{
        positionClass: 'custom-toast-position' 
      });
    }
  }
}

async onUpdateProject() {
  this.projectNameError = '';
  this.projectDescriptionError = '';
  let error: boolean = false;
  this.singleProject = await this.apiService.GetProject(this.data.project.site_id, this.data.project.project_id);

  if (this.singleProject.name?.toLowerCase() !== this.newProjectName?.toLowerCase()) {
    var findObject = this.projects.some(
      (obj: {project_name: any }) =>
        obj.project_name.toLowerCase() === this.newProjectName.toLowerCase(),
    );
    if (findObject) {
      this.projectNameExistsError = 'Project name is already exists.';
      error = true;
    }
  }
  this.newProjectName = this.newProjectName.trim();
  if (!this.newProjectName) {
    this.projectNameError = 'Project name is required.';
    error = true;
  }
  this.newProjectDescription = this.newProjectDescription.trim();
  if (!this.newProjectDescription) {
    this.projectDescriptionError = 'Description is required.';
    error = true;
  }
  

  if (!error && this.data.project) {
    try {
      this.isCreatingProject = true;
      this.data.project.name = this.newProjectName;
      this.data.project.description = this.newProjectDescription;
      this.data.project.last_modified_at = this.data.project.created_at; // Set last_modified_at to match created_at
      console.log(this.data.project, "payload for update project");
      await this.apiService.UpdateProject('1', this.data.project);
      this.onClosePanel();
      this.toaster.success('Server Updated Successfully', '', {
        positionClass: 'custom-toast-position'
      });
    } catch (error) {
      // Error handling
      console.error("Error updating server:", error);
      this.toaster.error('Error Updating server', '', {
        positionClass: 'custom-toast-position'
      });
    }
  }
}

}
