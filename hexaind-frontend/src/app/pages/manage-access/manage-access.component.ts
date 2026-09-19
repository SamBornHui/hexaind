import { Component, OnInit, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatSort, Sort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { grantAccessComponent } from 'src/app/dialogs/grant-access/grant-access.component';
import { grantServerAccessComponent } from 'src/app/dialogs/grant-server-access/grant-server-access.component';
import { ApiService } from 'src/app/services/api.service';
import { UsersService } from '../users/users.service';
import { ToastrService } from 'ngx-toastr';
import { ConfigService } from '../../services/config.service';
import { Subscription } from 'rxjs/internal/Subscription';
import { formatDate } from '@angular/common';
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
  last_login: string;
}

@Component({
  selector: 'app-manage-access',
  templateUrl: './manage-access.component.html',
  styleUrls: ['./manage-access.component.less'],
})
export class ManageAccessComponent implements OnInit {
  dataSource: MatTableDataSource<any> = new MatTableDataSource<any>();
  mappingResponse: any[] = [];
  @ViewChild(MatSort, { static: true }) sort!: MatSort;

  displayedColumns: string[] = [
    'user',
    'created_by',
    'created_at',
    'last_modified_at',
    'server_role',
    'actions',
  ];
  deleteAction: boolean = false;
  serveRoles: Role[] = [];
  userStatus: Status[] = [];
  searchText: string = '';
  selectedElement: any;
  role_id: any;
  defaultOption: string = '';
  selectedOption: string | undefined = '';
  options: { value: string; label: string }[] = [];
  projects: any;
  user: any;
  userInfo: any;
  project_id: any;
  deleteConfirmation: any;
  projectSubscription: Subscription | undefined = undefined;
  role_name: any;
  server_role_value: Number = 1;
  isUsersLoaded = false;

  constructor(
    private dialog: MatDialog,
    private apiService: ApiService,
    public toaster: ToastrService,
    private usersService: UsersService,
    private configService: ConfigService,
  ) {
    this.dataSource = new MatTableDataSource<any>([]);
    this.project_id = this.configService.SelectedProjectId;
  }

  ngOnInit(): void {
    const storedName = localStorage.getItem('rolesName');
    if (storedName !== null) {
      try {
        const parsedName = JSON.parse(storedName);
        this.role_name = parsedName.name;
      } catch (error) {
        console.error('Error parsing storedName JSON', error);
      }
    }
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;

    this.user = localStorage.getItem('currentUser');
    this.userInfo = JSON.parse(this.user);
    this.role_id = localStorage.getItem('role_id');
    this.projectSubscription =
      this.configService.selectedProjectIdObservable.subscribe(
        (projectId: any) => {
          if (projectId) {
            this.fetchData();
          }
        },
      );
    this.fetchOptions();
  }

  fetchData(): void {
    this.isUsersLoaded = false;
    const indexToUpdateBy = this.displayedColumns.indexOf('updated_by');
    if (indexToUpdateBy !== -1) {
      this.displayedColumns.splice(indexToUpdateBy, 1);
    }
    const indexUpdatedAt = this.displayedColumns.indexOf('updated_at');
    if (indexUpdatedAt !== -1) {
      this.displayedColumns.splice(indexUpdatedAt, 1);
    }
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    this.selectedOption = selectedProjectId;
    const jsonData = {
      id: selectedProjectId,
      get_details: true,
    };
    if (!this.selectedOption) {
      return;
    }
    this.usersService.getProjectData(jsonData).subscribe(
      (response: any) => {
        if (response.succeeded && response.mappings) {
          if (this.dataSource) {
            this.dataSource.data = this.processDates(response.mappings);
            this.mappingResponse = response.mappings;
            this.isUsersLoaded = true;
          }
        } else {
          console.error('Invalid response format:', response);
        }
      },
      (error: any) => {
        console.error('Error fetching data:', error);
        this.isUsersLoaded = false;
      },
    );
  }

  convertDateFormat(isoDateString: string): string {
    const date = new Date(isoDateString);
    return formatDate(date, 'd-MMM-yyyy h:mm a', 'en-US');
  }

  processDates(data: any[]): any[] {
    return data.map((item) => {
      return {
        ...item,
        created_at: this.convertDateFormat(item.created_at),
        last_modified_at: this.convertDateFormat(item.last_modified_at),
      };
    });
  }

  fetchOptions(): void {
    const jsonData = {
      id: this.userInfo._id,
      get_details: true,
    };
    this.apiService
      .GetProjects('1', '', jsonData)
      .then((projects: any[]) => {
        const projectOptions = projects.map((project: any) => ({
          value: project._id,
          label: project.project_name,
        }));
        if (this.role_id === '1') {
          this.options = [
            { value: 'server', label: 'Administrator' },
            ...projectOptions,
          ];
        } else {
          this.user = localStorage.getItem('currentUser');
          this.userInfo = JSON.parse(this.user);
          this.usersService.getUserData(jsonData).subscribe((response: any) => {
            const projectGetOptions = response.mappings.map((project: any) => ({
              value: project.project_id,
              label: project.project_name,
            }));
            this.options = projectGetOptions;
            this.server_role_value = response.mappings[0].server_role_value;
            this.project_id = this.options[0].value;
            this.fetchData();
          });
        }
      })
      .catch((error) => {
        console.error('Error fetching projects:', error);
      });
  }

  grantAccess(data: any, access: any): void {
    const dialogRef = this.dialog.open(grantAccessComponent, {
      width: '750px',
      height: '90%',
      data: { projectId: data, Access: access },
    });
    dialogRef.afterClosed().subscribe(() => {
      this.fetchData();
    });
  }

  grantServerAccess(role_id: any) {
    const dialogRef = this.dialog.open(grantServerAccessComponent, {
      width: '750px',
      height: '90%',
    });
    dialogRef.componentInstance.addEvent.subscribe((result: any) => {});
  }

  deleteProjectAccess(data: any) {
    const jsonData = {
      user_id: data.user_id,
      project_id: data.project_id,
    };
    this.usersService
      .deleteProjectAccess(jsonData)
      .subscribe((response: any) => {
        if (response.succeeded) {
          this.toaster.success('successfully Deleted!');
          this.fetchData();
        }
      });
  }

  removeServerAccess(data: any) {
    const jsonData = {
      changes: [
        {
          user_id: data.user_id,
          server_role_value: '4',
          server_role: '',
        },
      ],
    };
    this.usersService
      .removeServerAccess(jsonData)
      .subscribe((response: any) => {
        if (response.succeeded) {
          this.toaster.success('successfully Deleted!');
          this.fetchData();
        }
      });
  }

  async sortData(sort: Sort) {
    this.mappingResponse.sort((a: any, b: any) => {
      let aValue: any = '';
      let bValue: any = '';
      if (sort.active === 'user') {
        aValue = a.user_name;
        bValue = b.user_name;
      } else if (sort.active === 'created_by') {
        aValue = a.created_by_name;
        bValue = b.created_by_name;
      } else if (sort.active === 'server_role') {
        aValue = a.role_name;
        bValue = b.role_name;
      } else if (sort.active === 'created_at') {
        aValue = new Date(a.created_at);
        bValue = new Date(b.created_at);
      } else if (sort.active === 'last_modified_at') {
        aValue = new Date(a.last_modified_at);
        bValue = new Date(b.last_modified_at);
      } else {
        aValue = a[sort.active];
        bValue = b[sort.active];
      }

      const compareValues = (valueA: any, valueB: any) => {
        if (valueA == null && valueB == null) {
          return 0;
        }
        if (valueA == null) {
          return -1;
        }
        if (valueB == null) {
          return 1;
        }
        if (!isNaN(valueA) && !isNaN(valueB)) {
          return valueA - valueB;
        }
        const dateA = new Date(valueA);
        const dateB = new Date(valueB);
        if (!isNaN(dateA.getTime()) && !isNaN(dateB.getTime())) {
          return dateA.getTime() - dateB.getTime();
        }
        return String(valueA).localeCompare(String(valueB));
      };

      const comparisonResult = compareValues(aValue, bValue);
      return sort.direction === 'asc' ? comparisonResult : -comparisonResult;
    });
    this.dataSource = new MatTableDataSource(this.mappingResponse);
  }

  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value
      .trim()
      .toLowerCase();
    this.dataSource.filter = filterValue;
  }
}
