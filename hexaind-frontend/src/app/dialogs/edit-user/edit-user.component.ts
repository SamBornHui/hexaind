import {
  Component,
  Output,
  EventEmitter,
  Input,
  Inject,
  ViewChild,
} from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Project } from 'src/app/models/project-models';
import { UsersService } from 'src/app/pages/users/users.service';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { SnackBarNotificationService } from 'src/app/services/snack-bar-notification.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-edit-user',
  templateUrl: './edit-user.component.html',
  styleUrls: ['./edit-user.component.css'],
})
export class EditUserComponent {
  serveRoles!: { role_id: string; role_name: string }[];

  userStatus!: { status_id: string; status_name: string }[];
  private _data: any;
  @Output() editEvent: EventEmitter<any> = new EventEmitter<any>();
  userProjects: Project[] = [];

  constructor(
    public dialogRef: MatDialogRef<EditUserComponent>,
    @Inject(MAT_DIALOG_DATA) public dialogData: any,
    private usersService: UsersService,
    private snackBarNotificationService: SnackBarNotificationService,
    private errorHandlerService: ErrorHandlerService,
    public toaster: ToastrService,
  ) {
    this._data = dialogData;
    dialogRef.disableClose = true;
  }

  close(): void {
    this.dialogRef.close();
  }

  ngOnInit() {
    this.setDefaultRole();
    this.data.server_role_value = this._data.server_role_value?.toString();
    this.initializeRoles();
    // Initialize the selected value to match one of the role_ids
    //this.data.server_role_value = '3';
    this.userStatus = [
      { status_id: '1', status_name: 'Active' },
      { status_id: '2', status_name: 'Invited' },
      { status_id: '2', status_name: 'Inactive' },
    ];
    this.fetchUserProjects();
  }

  setDefaultRole() {
    if (this.data.server_role_value === 4) {
      this.data.server_role_value = 3;
    }
  }

  initializeRoles() {
    this.serveRoles = [
      { role_id: '1', role_name: 'Server Admin' },
      { role_id: '2', role_name: 'Project Admin' },
      { role_id: '3', role_name: 'Default User' },
    ];
  }

  fetchUserProjects() {
    const siteId = '1';
    let object = {
      id: this.data.user_id,
      get_details: true,
    };
    this.usersService.getUserProjects(siteId, object).subscribe({
      next: (response) => {
        if (response.succeeded) {
          this.userProjects = response.mappings;
        }
      },
      error: (error) => {
        console.log(error);
      },
    });
  }

  get data(): any {
    return this._data;
  }

  set data(value: any) {
    this._data = value;
  }

  onRoleChange(newValue: string) {
    this.data.server_role = newValue;
  }

  onStatusChange(newValue: string) {
    this.data.status = newValue;
  }

  isReadOnly(): boolean {
    if (this.data.is_sso_user) {
      return true;
    }
    return false;
  }

  onSave() {
    let object = {
      user_id: this.data.user_id,
      name: this.data.name,
      email: this.data.email,
      status: this.data.status,
      server_role_id: this.data.server_role_value,
    };

    this.usersService.update_user_by_admin(object).subscribe({
      next: (response) => {
        if (response.status) {
          this.editEvent.emit(response);
          this.toaster.success('User updated successfully', '', {
            positionClass: 'custom-toast-position',
          });
          this.dialogRef.close();
        }
      },
      error: (error) => {
        console.log(error);
        this.errorHandlerService.handleError(error);
      },
    });
  }
}
