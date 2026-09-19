import { Component, Output, EventEmitter, Inject, OnInit } from "@angular/core";
import { Project } from "src/app/models/project-models";
import { ApiService } from "src/app/services/api.service";
import { MatDialogRef, MAT_DIALOG_DATA } from "@angular/material/dialog";
import { ToastrService } from "ngx-toastr";
import { SnackBarNotificationService } from "src/app/services/snack-bar-notification.service";
import { UsersService } from "src/app/pages/users/users.service";


@Component({
  selector: 'app-create-new-project',
  templateUrl: './create-new-project.component.html',
  styleUrls: ['./create-new-project.component.less'],
})
export class CreateNewProjectComponent {
  @Output() closePanelClicked = new EventEmitter<any>();
  @Output() projectCreatedEvent = new EventEmitter<Project>();

  newProjectName: string = '';
  newProjectDescription: string = '';
  newProjectOwnerName: string = 'select';
  updateButton: any;
  getProjectAdmins: any;
  projects: any = [];
  singleProject: any =[];

  isCreatingProject: boolean = false;
  user: any;
  userInfo: any;
  constructor(
    private dialogRef: MatDialogRef<CreateNewProjectComponent>,
    @Inject(MAT_DIALOG_DATA)
    public data: {
      update: any;
      project: Project;
    }, // Inject the project data
    private apiService: ApiService,
    public toaster: ToastrService,
    private snackBarNotification: SnackBarNotificationService,
    private usersService: UsersService
  ) {}

  ngOnInit(): void {
    console.log(this.data,"get data list");
    this.user = localStorage.getItem('currentUser');
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
  }

  projectNameError: string = '';
  projectDescriptionError: string = '';
  projectOwnerError: string = '';
  projectNameExistsError: string = '';
  modified_count: any;

  async onCreateProject() {
    this.projectNameError = '';
    this.projectDescriptionError = '';
    this.projectOwnerError = '';
    this.projectNameExistsError = '';
    this.modified_count = '10';
    let error: boolean = false;

    var findObject = this.projects.some(
      (obj: { project_name: any }) =>
        obj.project_name.toLowerCase() === this.newProjectName.toLowerCase(),
    );

    if (findObject) {
      this.projectNameExistsError = 'Project name is already exists.';
      error = true;
    }
    this.newProjectName = this.newProjectName.trim();
    if (!this.newProjectName) {
      this.projectNameError = 'Project name is required.';
      error = true;
    }
    this.newProjectOwnerName = this.userInfo._id;
    this.newProjectDescription = this.newProjectDescription.trim();
    if (!this.newProjectDescription) {
      this.projectDescriptionError = 'Description is required.';
      error = true;
    }
    if (this.newProjectOwnerName === 'select') {
      this.projectOwnerError = 'Owner name is required.';
      error = true;
    }

    if (!error) {
    try{
      this.isCreatingProject = true;
      let userId: string = "1";

      let project: Project = new Project(
        this.newProjectName,
        this.newProjectDescription,
        '', 
        '', 
        ''  
      );
      
      project.project_administrator_id = this.newProjectOwnerName; 
      project.project_administrator_name = this.userInfo.name; 
      const adminUserRoleMapping = {
      };
      if (!Array.isArray(project.users_roles_mappings)) {
        project.users_roles_mappings = []; 
      }
      
      project.users_roles_mappings;
      project._id = await this.apiService.CreateProject("1", project);
      console.log(project._id,"project id het");
      this.onClosePanel();
      this.toaster.success('Project Created Successfully', '',{
        positionClass: 'custom-toast-position'
      });
    } catch (error) {
      this.toaster.error('Error Creating Project', '',{
        positionClass: 'custom-toast-position' 
      });
    }
  }
}

async onUpdateProject() {
  this.projectNameError = '';
  this.projectDescriptionError = '';
  this.projectOwnerError = '';
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
  if (this.newProjectOwnerName === 'select') {
    this.projectOwnerError = 'Owner name is required.';
    error = true;
  }

  if (!error && this.data.project) {
    try {
      this.isCreatingProject = true;
      this.data.project.name = this.newProjectName;
      this.data.project.description = this.newProjectDescription;
      this.data.project.owner_name = this.newProjectOwnerName;
      this.data.project.last_modified_at = this.data.project.created_at; // Set last_modified_at to match created_at
      console.log(this.data.project, "payload for update project");
      await this.apiService.UpdateProject('1', this.data.project);
      this.onClosePanel();
      this.toaster.success('Project Updated Successfully', '', {
        positionClass: 'custom-toast-position'
      });
    } catch (error) {
      // Error handling
      console.error("Error updating project:", error);
      this.toaster.error('Error Updating Project', '', {
        positionClass: 'custom-toast-position'
      });
    }
  }
}

}
