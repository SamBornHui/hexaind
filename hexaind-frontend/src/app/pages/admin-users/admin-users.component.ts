import { Component, ViewChild } from '@angular/core';
import { Utils } from '../../utils';
import { AdminUsersService } from './services/admin-users.service';
import { AddUserComponent } from '../../dialogs/add-user/add-user.component';
import { MatDialog } from '@angular/material/dialog';
import { MatTableDataSource } from '@angular/material/table';
import { NotificationComponent } from '../../controls/notification/notification.component';

@Component({
  selector: 'app-admin-users',
  templateUrl: './admin-users.component.html',
  styleUrls: ['./admin-users.component.less'],
})
export class AdminUsersComponent {
  @ViewChild('notification') notificationComponent!: NotificationComponent;
  isAddingUser: boolean = false;
  searchText: string = '';
  selectedRole: string = '';
  displayedColumns: string[] = [
    'name',
    'email',
    'role',
    'user_type',
    'dateAdded',
    'actions',
  ];
  selectedUserRow: any = null;
  descending: boolean = true;
  actionMenu: boolean = false;
  deleteAction: boolean = false;
  // users: User[] = [];
  users: any = [];
  userRoles: any = [];
  userSites: any = [];
  dataSource = new MatTableDataSource(this.users);
  userType: boolean = false;

  constructor(
    private apiService: AdminUsersService,
    private dialog: MatDialog,
  ) {}

  ngOnInit() {
    this.loadUserRolesAndSites();
  }
  async loadUsers(searchTerms: string | undefined) {
    this.users = await this.apiService.GetUsers('1', searchTerms);
    this.sortUsersByLastCreated();
  }
  async loadUserRolesAndSites() {
    this.userRoles = await this.apiService.GetUserRoles();
    this.userSites = [];
    this.loadUsers(undefined);
  }
  async updateUserRole(user: any, role: any) {
    if (role != user.role) {
      this.apiService
        .UpdateUserRole('1', user._id, role)
        .subscribe((response) => {
          if (response.user_id !== undefined) {
            this.loadUsers(undefined);
          }
        });
    }
  }
  onSearchTextChange() {
    this.dataSource.filter = this.searchText.trim().toLowerCase();
    // this.loadUsers(this.searchText);
  }

  onCloseAddUserDialog() {
    this.isAddingUser = false;
  }

  onUserAdded(user: any) {
    this.isAddingUser = false;
    // this.users.push(user);
  }

  onToggleSort() {
    this.descending = !this.descending;
    this.sortUsersByLastCreated();
  }

  sortUsersByLastCreated(): void {
    this.users = this.users.sort((a: any, b: any) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return this.descending ? dateB - dateA : dateA - dateB;
    });
    this.dataSource = new MatTableDataSource(this.users);
  }
  filterByRole(role: any) {
    var userFilteredData: any[] = this.users.filter((user: any) =>
      user.sites_and_roles[0].role_id
        .toLowerCase()
        .includes(role.toLowerCase()),
    );
    this.dataSource = new MatTableDataSource(userFilteredData);
  }
  filterByUserType(type: any) {
    this.userType = type == 'SSO' ? true : false;
    this.userType = true;
    var userFilteredData: any[] = this.users.filter(
      (user: any) => user.is_sso_user === this.userType,
    );
    this.dataSource = new MatTableDataSource(userFilteredData);
  }

  onRefreshView() {
    this.selectedRole = '';
    this.loadUsers(undefined);
  }

  addUser() {
    const dialogRef = this.dialog.open(AddUserComponent, {
      width: '560px',
      data: {
        edit: false,
        userRoles: this.userRoles,
        userSites: this.userSites,
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.notificationComponent.display(result.message, 'success');
        this.loadUsers(undefined);
      } else {
        this.notificationComponent.display(result.message, 'error');
      }
    });
  }
  editUser(user: any) {
    const dialogRef = this.dialog.open(AddUserComponent, {
      width: '560px',
      data: {
        user: user,
        edit: true,
        userRoles: this.userRoles,
        userSites: this.userSites,
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) this.loadUsers(undefined);
    });
  }

  isSsoUser(user: any) {
    return 'Databrick';
  }
  onRowDblClick(row: any) {}

  onRowSingleClick(row: any) {}

  isRowSelected(row: any): boolean {
    return this.selectedUserRow === row;
  }
  async deleteUser(rowData: any) {
    try {
      const response = await this.apiService.DeleteUser(rowData.email);
      console.log(response);
      this.loadUsers(undefined);
    } catch (error) {
      console.error('API Error:', error);
    }
  }
}
