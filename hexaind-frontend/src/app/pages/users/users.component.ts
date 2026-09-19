import { Component, HostListener, OnInit, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatSelectChange } from '@angular/material/select';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { UsersService } from './users.service';
import { EditUserComponent } from 'src/app/dialogs/edit-user/edit-user.component';
import { AddUsersComponent } from 'src/app/dialogs/add-users/add-users.component';
import { ToastrService } from 'ngx-toastr';
import { MatInput } from '@angular/material/input';
import { ProjectButtonVisibilityServiceService } from 'src/app/controls/header/project-button-visibility-service.service';
import { CreateNewPasswordComponent } from 'src/app/dialogs/create-new-password/create-new-password.component';
import { formatDate } from '@angular/common';
import { Router } from '@angular/router';
import { interval, Subject, takeUntil } from 'rxjs';

export interface Role {
  role_id: string;
  role_name: string;
}

export interface Status {
  status_id: string;
  status_name: string;
}

export interface dataTable {
  _id: string;
  name: string;
  email: string;
  server_role: string;
  projects: string;
  status: string;
  invited_by: string;
  created_at: string;
  last_login: string;
}

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.less'],
})
export class UsersComponent implements OnInit {
  dataSource!: MatTableDataSource<dataTable>;
  @ViewChild(MatSort, { static: true }) sort!: MatSort;
  @ViewChild('searchInput') searchInput!: MatInput;
  private destroy$ = new Subject<void>();

  displayedColumns: string[] = [
    'log_status',
    'name',
    'server_role',
    'email',
    'projects',
    'status',
    'invited_by',
    'created_at',
    'last_login',
    'actions',
  ];
  deleteAction: boolean = false;
  serveRoles: Role[] = [];
  userStatus: Status[] = [];
  private _selectedRole: Role | null = null;
  private _selectedStatus: Status | null = null;
  searchText: string = '';
  selectedElement: any;
  originalData: any;
  loader: boolean = false;
  userInfo: any;
  isLoading: boolean = false; // For initial loading status
  isUpdating: boolean = false;
  actionType: 'delete' | 'deactivate' | null = null;

  constructor(
    private dialog: MatDialog,
    private usersService: UsersService,
    public toaster: ToastrService,
    private projectVisibilityService: ProjectButtonVisibilityServiceService,
    private router: Router
  ) {
    let user: any = localStorage.getItem('currentUser');
    this.userInfo = JSON.parse(user);
  }

  @HostListener('document:click', ['$event'])
  onClick(event: MouseEvent) {
    if (this.deleteAction) {
      this.deleteAction = false;
    }
  }

  ngOnInit(): void {
    this.projectVisibilityService.hideProjectsButton();
    this.serveRoles = [
      { role_id: '1', role_name: 'Server Admin' },
      { role_id: '2', role_name: 'Project Admin' },
      { role_id: '3', role_name: 'Default User' },
    ];
    this.userStatus = [
      { status_id: '1', status_name: 'Active' },
      { status_id: '2', status_name: 'Inactive' },
      { status_id: '3', status_name: 'Invited' },
    ];
    this.fetchUsersList(true);
    interval(30000)
    .pipe(takeUntil(this.destroy$))
    .subscribe(() => {
      this.fetchUsersList(false);
    });
  }

  ngOnDestroy(): void {
    this.projectVisibilityService.showProjectsButton();
    this.destroy$.next();
    this.destroy$.complete();
  }

  fetchUsersList(isInitialLoad = false): void {
    if (isInitialLoad) {
    this.loader = true; // Show loader for the first load
  } else {
    this.loader = false; // Show loader for polling updates
  }
    this.usersService.getUsersList().subscribe({
      next: (response) => {
        this.originalData = response;
        this.originalData = this.processDates(this.originalData);
        this.dataSource = new MatTableDataSource(this.originalData);
        this.dataSource.sort = this.sort;
        this.dataSource.sortingDataAccessor = (item: any, header: string) => {
          switch (header) {
            case 'name':
              return item.name.toLowerCase();
            case 'server_role':
              return item.server_role.toLowerCase();
            case 'email':
              return item.email.toLowerCase();
            case 'projects':
              return item.user_projects_count;
            case 'invited_by':
              return item.invited_by.toLowerCase();
            case 'last_login':
              return new Date(item.last_login_date);
            default:
              return item[header];
          }
        };
        this.loader = false;
      },
      error: (error) => {
        this.loader = false;
        console.error('Error', error);
      },
    });
  }

  processDates(data: any[]): any[] {
    return data.map((item) => {
      return {
        ...item,
        created_at: this.convertDateFormat(item.created_at),
        last_login_date: this.convertDateFormat(item.last_login_date),
        role_updated_at: this.convertDateFormat(item.role_updated_at),
        updated_at: this.convertDateFormat(item.updated_at),
      };
    });
  }

  convertDateFormat(isoDateString: string): string {
    if (!isoDateString) return '';
    const date = new Date(isoDateString);
    return formatDate(date, 'd-MMM-yyyy h:mm a', 'en-US');
  }

  get selectedRole(): Role | null {
    return this._selectedRole;
  }

  set selectedRole(role: Role | null) {
    this._selectedRole = role;
  }

  get selectedStatus(): Status | null {
    return this._selectedStatus;
  }

  set selectedStatus(status: Status | null) {
    this._selectedStatus = status;
  }

  onRoleSelectionChange(event: MatSelectChange): void {
    this.selectedRole = event.value;
    this.applyFilter();
  }

  onStatusSelectionChange(event: MatSelectChange): void {
    this.selectedStatus = event.value;
    this.applyFilter();
  }

  applyFilter() {
    const filteredData = this.originalData.filter((item: any) => {
      let roleMatch = true;
      let statusMatch = true;

      if (this.selectedRole) {
        roleMatch = item.server_role === this.selectedRole;
      }

      if (this.selectedStatus) {
        statusMatch = item.status === this.selectedStatus;
      }

      return roleMatch && statusMatch;
    });
    this.dataSource.data = filteredData;

    if (this.sort) {
      this.dataSource.sort = this.sort;
    }
  }

  addUsers() {
    const dialogRef = this.dialog.open(AddUsersComponent, {
      width: '850px',
      height: '90%',
    });
    dialogRef.componentInstance.addEvent.subscribe((result: any) => {
      this.fetchUsersList();
    });
  }

  editUser() {
    let obj = {
      user_id: this.selectedElement._id,
      name: this.selectedElement.name,
      email: this.selectedElement.email,
      status: this.selectedElement.status,
      is_sso_user: this.selectedElement.is_sso_user,
      server_role_value: this.selectedElement.server_role_value,
      server_role: this.selectedElement.server_role,
    };
    const dialogRef = this.dialog.open(EditUserComponent, {
      width: '850px',
      data: obj,
    });
    dialogRef.componentInstance.editEvent.subscribe((result: any) => {
      if (result.status) {
        this.fetchUsersList();
      } else {
      }
    });
  }

  setCurrentElement(element: any) {
    this.selectedElement = element;
  }

  deactivateUser() {
    this.usersService.inactivateUser(this.selectedElement.email).subscribe({
      next: (response) => {
        const deletedIndex = this.dataSource.data.findIndex(
          (user) => user.email === this.selectedElement.email,
        );
        if (deletedIndex !== -1) {
          this.dataSource.data[deletedIndex].status = 'Inactive';
        }

        this.toaster.success('User deactivated successfully', '', {
          positionClass: 'custom-toast-position',
        });
      },
      error: (error) => {
        console.error('Error', error);
        this.toaster.error(error.error.reason, '', {
          positionClass: 'custom-toast-position',
        });
      },
    });
  }

  applySearch(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();
  }

  getStatusClasses(status: string): any {
    let classes = {};

    switch (status) {
      case 'Active':
        classes = { 'text-green': true };
        break;
      case 'Inactive':
        classes = { 'text-red': true };
        break;
      case 'Invited':
        classes = { 'text-orange': true };
        break;
      default:
        break;
    }

    return classes;
  }

  resendInvitation(): void {
    this.usersService.resendInvitation(this.selectedElement.email).subscribe({
      next: (response) => {
        if (response.status) {
          this.toaster.success('Invitation resent successfully', '', {
            positionClass: 'custom-toast-position',
          });
        }
      },
      error: (error) => {
        console.error('Error', error);
        this.toaster.error(error.error.reason, '', {
          positionClass: 'custom-toast-position',
        });
      },
    });
  }

  onReset() {
    this.selectedRole = null;
    this.selectedStatus = null;
    this.searchInput.value = '';
    this.fetchUsersList();
  }

  createPassword() {
    let obj = {
      email: this.selectedElement.email,
    };
    const dialogRef = this.dialog.open(CreateNewPasswordComponent, {
      width: '850px',
      data: obj,
    });
    dialogRef.componentInstance.passwordEvent.subscribe((result: any) => {
      if (result.status) {
        this.fetchUsersList();
      } else {
      }
    });
  }

  getStatusColor(status: string): string {
  switch (status) {
    case 'ACTIVE':
      return 'text-green';
    case 'INACTIVE':
      return 'text-orange';
    case 'LOGOUT':
      return 'text-grey';
    default:
      return 'text-grey material-symbols-outlined';
  }
}

getTooltipText(status: string): string {
  switch (status) {
    case 'ACTIVE':
      return 'Online';
    case 'INACTIVE':
      return 'Away';
    case 'LOGOUT':
      return 'Logged Out';
    default:
      return 'Unknown Status';
  }
}

startAction(type: 'delete' | 'deactivate', event: Event): void {
  this.actionType = type;
  this.deleteAction = true;
  event.stopPropagation();
}

confirmAction(): void {
  if (this.actionType === 'delete') {
    this.deleteUser(); 
  } else if (this.actionType === 'deactivate') {
    this.deactivateUser(); 
  }
  this.actionType = null; 
}

deleteUser(){
  this.usersService.deleteUser(this.selectedElement._id).subscribe({
      next: (response) => {        
        this.fetchUsersList(false)
        this.toaster.success('User deleted successfully', '', {
          positionClass: 'custom-toast-position',
        });
      },
      error: (error) => {
        console.error('Error', error);
        this.toaster.error(error.error.reason, '', {
          positionClass: 'custom-toast-position',
        });
      },
    });
  }

  activateUser(){
    const payload = {
      email: this.selectedElement.email
    }
    this.usersService.activateUser(payload).subscribe({
      next: (response) => {        
        this.fetchUsersList(false)
        this.toaster.success('User Activated successfully', '', {
          positionClass: 'custom-toast-position',
        });
      },
      error: (error) => {
        console.error('Error', error);
        this.toaster.error(error.error.reason, '', {
          positionClass: 'custom-toast-position',
        });
      },
    });
  }
}
