import {
  Component,
  Input,
  ChangeDetectorRef,
  SimpleChanges,
  EventEmitter, Output
} from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { TimeAgoPipe } from 'src/app/time-ago.pipe';
import { NgZone } from '@angular/core';
import { ConfigService } from '../../workflow-designer/workflow-canvas.service';
import { Router } from '@angular/router';
import { UsersService } from '../../users/users.service';
import { ToastrService } from 'ngx-toastr';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { FormsModule } from '@angular/forms';
import { FlexLayoutModule } from '@angular/flex-layout';
import { MatButtonModule } from '@angular/material/button';
@Component({
  selector: 'app-notification-details',
  templateUrl: './notification-details.component.html',
  styleUrls: ['./notification-details.component.less'],
  standalone: true,
  imports: [CommonModule, 
    TimeAgoPipe, 
    MatIconModule, 
    MatFormFieldModule, 
    MatSelectModule, 
    MatInputModule,
    MatDatepickerModule,
    MatNativeDateModule,
    FormsModule,
    FlexLayoutModule,
    MatButtonModule
  ],
})
export class NotificationDetailsComponent {
  @Input() selectedTab: string = '';

  @Output() callingEvent = new EventEmitter<string>();
  notifications: any[] = [];
  Readnotifications: any[] = [];
  notificationstatus: any;
  user: any;
  descending = false;
  filteredNotification: any;
  selectedType: string | null = null;
  userIdToNameMap: { [userId: string]: string } = {};
  usersList: any
  filteredUsers: any;
  selectedUserId: any
  projectId: any
  selectedDate = "";
  selectedStartDate: Date | undefined;
  selectedEndDate: Date | undefined;

  constructor(
    private apiService: ApiService,
    private cdr: ChangeDetectorRef,
    private zone: NgZone,
    private configService: ConfigService,
    private router: Router,
    private usersService: UsersService,
    public toaster: ToastrService,
  ) {
    this.user = localStorage.getItem('currentUser');
    this.user = JSON.parse(this.user);
    this.projectId = this.configService.SelectedProjectId;
  }

  ngOnInit() {
    this.loadnotifications(undefined);
    this.getAllTheUsers()
  }

  ngOnChanges(changes: SimpleChanges) {
    if (
      changes['selectedTab'].currentValue === 'Unread' ||
      changes['selectedTab'].currentValue === 'All'
    ) {
      this.loadnotifications(undefined);
    }
  }

  async loadnotifications(searchTerms: string | undefined) {
    try {
      this.notifications = await this.apiService.GetNotifications(
        '1',
        this.projectId,
        searchTerms,
      );
      this.filteredNotification = this.notifications;
      this.zone.run(() => this.cdr.detectChanges());
    } catch (error) {
      const errorMessage = 'Error while fetching notifications. Please try again later';
      this.toaster.error(
        errorMessage,
        'ERROR',
        {
          positionClass: 'custom-toast-position',
        }
      );
    }
  }

  async updateNotificationStatus(notificationId: any, status: any) {
    try {
      let response;
      response = await this.apiService.UpdateNotificationStatus(
        '1',
        notificationId,
        status,
        this.user._id
      );
      if (response) {
        this.callingEvent.emit("Updated");
        this.loadnotifications(undefined);
        this.apiService.updateNotificationStatus();
        setTimeout(() => {
          this.apiService.updateNotificationCount(this.getUnreadNotificationCount())
        }, 2000);
      } else {
        this.toaster.error('Failed to update notification', '', {
          positionClass: 'custom-toast-position'
        });
      }
    } catch (error) {
      const errorMessage = 'Error while updating notification. Please try again later';
      this.toaster.error(
        errorMessage,
        'ERROR',
        {
          positionClass: 'custom-toast-position',
        }
      );
    }
  }

  async UpdateNotificationStatusAsUnread(notificationId: any) {
    try {
      let response;
      response = await this.apiService.UpdateNotificationStatusAsUnread(
        '1',
        notificationId
      );
      if (response) {
        this.loadnotifications(undefined);
        this.apiService.updateNotificationStatus();
      } else {
        this.toaster.error('Failed to update notification', '', {
          positionClass: 'custom-toast-position'
        });
      }
    } catch (error) {
      const errorMessage = 'Error while updating notification. Please try again later';
      this.toaster.error(
        errorMessage,
        'ERROR',
        {
          positionClass: 'custom-toast-position',
        }
      );
    }
  }

  getUnreadNotificationCount(): number {
    return this.notifications.filter((notification) => !notification.read.includes(this.user._id))
      .length;
  }

  async markAllNotifucationAsread() {
    try {
      let response;
      response = await this.apiService.UpdateAllNotificationStatus(
        '1',
        this.user._id
      );
      if (response) {
        this.loadnotifications(undefined);
        this.apiService.updateNotificationStatus();
        setTimeout(() => {
          this.apiService.updateNotificationCount(this.getUnreadNotificationCount())
        }, 2000);
        this.toaster.success('Notifications updated successfully', '', {
          positionClass: 'custom-toast-position'
        });
        this.getUnreadNotificationCount();
        this.callingEvent.emit("Updated");
      } else {
        this.toaster.error('Failed to update notifications', '', {
          positionClass: 'custom-toast-position'
        });
      }
    } catch (error) {
      const errorMessage = 'Error while updating notifications. Please try again later';
      this.toaster.error(
        errorMessage,
        'ERROR',
        {
          positionClass: 'custom-toast-position',
        }
      );
    }
  }

  onToggleSort() {
    this.notifications = this.filteredNotification
    this.descending = !this.descending;
    this.sortNotificationsByImportance();
    this.selectedDate = "";
  }

  sortNotificationsByImportance(): void {
    const importanceOrder: any = { 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };

    this.notifications.sort((a, b) => {
      const importanceA = importanceOrder[a.importance];
      const importanceB = importanceOrder[b.importance];

      if (importanceA === importanceB) {
        return 0;
      }

      if (this.descending) {
        return importanceB - importanceA;
      } else {
        return importanceA - importanceB;
      }
    });
  }

  async onViewWorkflowSession(notification: any) {
    let siteId = this.configService.SelectedSiteId;
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    let session = await this.apiService.GetSessionByWorkflowId(
      siteId,
      selectedProjectId,
      notification.category_id,
    );

    if (!session || session === "no session found") {
      this.toaster.error('Workflow not found', '', {
        positionClass: 'custom-toast-position'
      });
      return;
    }
    session = (JSON.parse(session));
    const versionedWorkflow = session.saved_workflows.find((saved: { workflow_id: any; }) => saved.workflow_id === notification.category_id);

    let queryParams = {
      siteId: siteId,
      projectId: selectedProjectId,
      workflowSessionId: session._id,
      versionedWorkflowId: versionedWorkflow?.workflow_id,
    };
    this.router.navigate(['/workflow-designer'], {
      queryParams,
    });
    if (!notification.read.includes(this.user._id)) {
      this.updateNotificationStatus(notification._id, true);
    }
  }

  onViewDataset(notification: any): void {
    const siteId = this.configService.SelectedSiteId;
    let queryParams: any = {};
    queryParams.dataset_id = notification.category_id;

    this.router.navigate([`sites/${siteId}/projects/${notification.project_id}/data`], { queryParams: queryParams });
    if (!notification.read.includes(this.user._id)) {
      this.updateNotificationStatus(notification._id, true);
    }
  }

  onViewJob(notification: any): void {
    const siteId = this.configService.SelectedSiteId;
    let queryParams: any = {};
    queryParams.job_id = notification.category_id;

    this.router.navigate([`sites/${siteId}/projects/${notification.project_id}/jobs`], { queryParams: queryParams });
    if (!notification.read.includes(this.user._id)) {
      this.updateNotificationStatus(notification._id, true);
    }
  }

  applyFilter() {
    if (!this.selectedType || this.selectedType == "") {
      this.notifications = this.filteredNotification;
      return this.notifications;
    }
    this.notifications = this.filteredNotification
    this.notifications = this.notifications.filter(notification => notification.notification_category === this.selectedType);
    return this.notifications;
  }

  onSelectionChange(event: any): void {
    this.selectedType = event.value;
    this.applyFilter();
  }

  getAllTheUsers() {
    this.usersService.getUsersList().subscribe({
      next: (response) => {
        this.usersList = response;
        this.usersList.forEach((user: { _id: string | number; name: string; }) => {
          this.userIdToNameMap[user._id] = user.name;
        });

        const uniqueUserIds: string[] = Array.from(new Set(this.notifications.map(notification => notification.user_id)));
        this.filteredUsers = this.usersList.filter((user: { _id: string; }) => uniqueUserIds.includes(user._id));
      },
      error: (error) => {
        const errorMessage = error?.error?.message || error?.message || 'An unexpected error occurred';
        this.toaster.error(
          errorMessage,
          'ERROR',
          {
            positionClass: 'custom-toast-position',
          }
        );
      },
    });
  }

  applyUserNotification() {
    if (!this.selectedUserId || this.selectedUserId == "") {
      this.notifications = this.filteredNotification;
      return this.notifications;
    }
    this.notifications = this.filteredNotification
    this.notifications = this.notifications.filter(notification => notification.user_id === this.selectedUserId);
    return this.notifications;
  }

  onUserSelectionChange(event: any): void {
    this.selectedUserId = event.value;
    this.applyUserNotification();
  }

  onTimeSelectionOption() {
    this.selectedDate = 'time';
  }

  onStartDateChange(event: any): void {
    this.selectedStartDate = event.value;
    if (this.selectedStartDate && this.selectedEndDate) {
      this.notifications = this.filteredNotification;
      this.onDateChange();
    }
  }

  onEndDateChange(event: any): void {
    this.selectedEndDate = event.value;
    if (this.selectedStartDate && this.selectedEndDate) {
      this.notifications = this.filteredNotification;
      this.onDateChange();
    }
  }

  onDateChange() {
    if (this.selectedStartDate && this.selectedEndDate) {
      this.notifications = this.notifications.filter(notify => {
        const recordDate = new Date(notify.created_at);
        return (this.selectedStartDate?.valueOf() ?? Infinity) <= recordDate.valueOf() &&
          (this.selectedEndDate?.valueOf() ?? -Infinity) >= recordDate.valueOf();
      });
    }
  }
}
