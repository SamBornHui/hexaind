import {
  Component,
  EventEmitter,
  Inject,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { Router, NavigationEnd, NavigationExtras } from '@angular/router';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Role } from 'src/app/pages/users/users.component';
import { FormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';
import { MatTabChangeEvent } from '@angular/material/tabs';
import { UsersService } from '../../pages/users/users.service';
import { SnackBarNotificationService } from 'src/app/services/snack-bar-notification.service';
import { ToastrService } from 'ngx-toastr';
import { UserForProjects } from 'src/app/models/user-models';

interface RowItem {
  role_id: any;
  added: boolean;
  name: any;
  user: string;
  role: string;
  role_name: any;
  user_id: any;
  user_name: any;
  id: any;
}

@Component({
  selector: 'app-grant-access',
  templateUrl: './grant-access.component.html',
  styleUrls: ['./grant-access.component.css'],
})
export class grantAccessComponent implements OnInit {
  @Output() addEvent: EventEmitter<any> = new EventEmitter<any>();
  private selectedRoleIndex!: string;
  form!: FormGroup;
  inviteType: string = '';
  is_sso_user: boolean = false;

  rows: RowItem[] = [];
  users: any[] = [];
  roles: any[] = [];
  lastAddedUser: string = '';
  lastAddedRole: string = '';

  getUsersRole: any;
  access_view: any;
  editedRow: any = { role_id: '' };
  rowUser: any = {};
  selectedUsers: any[] = [];

  constructor(
    public dialogRef: MatDialogRef<grantAccessComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fb: FormBuilder,
    private usersService: UsersService,
    private snackBarNotification: SnackBarNotificationService,
    public toaster: ToastrService,
  ) {}

  ngOnInit() {
    if (this.data.Access === 'Edit') {
      this.access_view = true;
      this.loadProjectData();
    } else {
      this.access_view = false;
      this.loadInitialData();
    }
  }

  loadProjectData() {
    const jsonData = { id: this.data.projectId.project_id, get_details: true };
    this.usersService.getProjectData(jsonData).subscribe(
      (response: any) => {
        if (response.succeeded && response.mappings) {
          this.getUsersRole = response.mappings;
          this.rowUser =
            this.getUsersRole.find(
              (user: any) =>
                user.user_id === this.data.projectId.user_id &&
                user.role_id === this.data.projectId.role_id,
            ) || {};
        }
      },
      (error: any) => console.error('Error fetching project data:', error),
    );
    this.loadRoles();
  }

  loadInitialData() {
    this.loadRoles();
    const jsonData = {
      id: this.data.projectId,
      project_id: this.data.projectId,
      get_details: true,
      search_term: '',
      page_number: 1,
      page_limit: 100,
    };
    this.loadUserDataForProject(jsonData);
  }

  loadRoles() {
    this.usersService.getRolesList().subscribe({
      next: (roleResponse: { results: any[] }) =>
        (this.roles = roleResponse.results),
      error: (error: any) => console.error('Error fetching roles:', error),
    });
  }

  async loadUserDataForProject(jsonData: any) {
    try {
      const response: UserForProjects[] =
        await this.usersService.getProjectUserData(jsonData);
      this.getUsersRole = response;
      this.pushDataToRows();
    } catch (error) {
      console.error('Error loading user data for project:', error);
    }
  }

  pushDataToRows() {
    this.rows.push({
      user: '',
      id: '',
      user_id: '',
      user_name: '',
      role_name: '',
      added: false,
      name: '',
      role_id: '',
      role: '',
    });
  }

  addRow() {
    this.rows.push({
      user: '',
      role: '',
      added: false,
      name: undefined,
      role_id: undefined,
      role_name: '',
      user_name: '',
      user_id: '',
      id: '',
    });
  }

  removeRow(row: any) {
    if (this.rows.length > 1) {
      const index = this.rows.indexOf(row);
      if (index !== -1) {
        this.rows.splice(index, 1);
      }
    }
  }

  // getFilteredUsers(index: number) {
  //   const selectedUsers = this.rows.map(row => row.user);
  //   return this.getUsersRole.filter((user: { id: string }) => !selectedUsers.includes(user.id) || this.rows[index].user === user.id);
  // }

  getFilteredUsers(index: number) {
    const selectedUsers = this.rows.map((row) => row.user);

    return this.getUsersRole.filter(
      (user: { id: string; server_role_value: number }) => {
        const isSelectedUser = selectedUsers.includes(user.id);
        const isCurrentRowUser = this.rows[index].user === user.id;
        const isProjectAdmin = user.server_role_value === 2;

        return !isSelectedUser || isCurrentRowUser || isProjectAdmin;
      },
    );
  }

  getFilteredRoles(userId: string) {
    const user = this.getUsersRole.find((u: { id: string }) => u.id === userId);
    if (user) {
      if (user.server_role_value === 2) {
        return this.roles; // Display all roles
      } else {
        return this.roles.filter(
          (role) =>
            role.name === 'FULL ACCESS' || role.name === 'LIMITED ACCESS',
        );
      }
    }
    return [];
  }

  getUpdatedFilteredRoles(userId: string) {
    const user = this.getUsersRole.find(
      (u: { _id: string }) => u._id === userId,
    );
    if (user) {
      if (
        user.server_role_value === 2 ||
        user.role_name == 'PROJECT ADMINISTRATOR'
      ) {
        return this.roles;
      } else {
        return this.roles.filter(
          (role) =>
            role.name === 'FULL ACCESS' || role.name === 'LIMITED ACCESS',
        );
      }
    }
    return [];
  }

  trackLastAdded(user: string, role: string, index: number) {
    const selectedUser = this.getUsersRole.find(
      (u: { id: string }) => u.id === user,
    );
    if (selectedUser) {
      this.rows[index].name = selectedUser.name;
    }
    const selectedRole = this.roles.find((r: { id: string }) => r.id === role);
    if (selectedRole) {
      this.rows[index].role_id = selectedRole.id;
    }
    this.rows[index].added = true;
    this.updateSelectedUsers();
  }

  updateSelectedUsers() {
    this.selectedUsers = this.rows
      .map(
        (row) =>
          this.getUsersRole.find((u: { id: string }) => u.id === row.user)
            ?.name,
      )
      .filter((name) => !!name);
  }

  saveData() {
    const jsonData = {
      project_id: this.data.projectId,
      mappings: this.rows.map((row) => ({
        user_id: row.user,
        project_id: this.data.projectId,
        role_id: row.role_id,
      })),
    };
    this.usersService.createProjectAccess(jsonData).subscribe({
      next: (response: { succeeded: any }) => {
        if (response.succeeded) {
          this.toaster.success('Successfully Updated Access!');
          this.dialogRef.close();
        }
      },
      error: (error: any) => console.error('Error saving data:', error),
    });
  }

  close(): void {
    this.dialogRef.close();
  }

  updateData(rowUser: any) {
    const jsonData = {
      user_id: rowUser.user_id,
      project_id: rowUser.project_id,
      role_id: rowUser.role_id,
    };
    this.usersService.updateProjectAccess(jsonData).subscribe({
      next: (response: { succeeded: any }) => {
        if (response.succeeded) {
          this.toaster.success('Successfully Updated Access!');
          this.dialogRef.close();
        }
      },
      error: (error: any) => console.error('Error updating data:', error),
    });
  }
}
