import { ChangeDetectorRef, Component } from '@angular/core';
import { MatDialogModule,MatDialogRef } from "@angular/material/dialog";
import { Router,RouterModule } from '@angular/router';
import { ApiService } from 'src/app/services/api.service';
import { ConfigService } from 'src/app/services/config.service';
import { TimeAgoPipe } from 'src/app/time-ago.pipe';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { FlexLayoutModule } from '@angular/flex-layout';
import { MatButtonModule } from '@angular/material/button';
import { ToastrService } from 'ngx-toastr';
import { Notification, NotificationType, NotificationResponseMessages } from 'src/app/models/notification-models';

@Component({
  selector: 'app-notification-dailog',
  templateUrl: './notification-dailog.component.html',
  styleUrls: ['./notification-dailog.component.less'],
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    RouterModule,
    MatIconModule,
    FlexLayoutModule,
    MatButtonModule,
    TimeAgoPipe
  ],
})
export class NotificationDailogComponent {
  user: any;
  readNotificationIds: string[] | undefined;
  notifications: any[] = [];
  notificationCount: number = 4;
  project_id: any;
  
  constructor(
    public dialogRef: MatDialogRef<NotificationDailogComponent>,
    private configService: ConfigService, private router: Router,
    private apiService: ApiService,
    private cdr: ChangeDetectorRef,
    private toaster: ToastrService
  ) {
    this.user = localStorage.getItem('currentUser');
    this.user = JSON.parse(this.user);
    this.project_id = this.configService.SelectedProjectId;
  }


  close(): void {
    this.dialogRef.close();
  }

  ngOnInit() {
    this.loadnotifications(undefined);
  }

  async loadnotifications(searchTerms: string | undefined) {
    try {
      this.notifications = await this.apiService.GetNotifications("1", this.project_id, searchTerms);
      if (this.notifications.length > 0) {
        this.readNotificationIds = this.notifications[this.notifications.length - 1].read;
      } else {
        this.readNotificationIds = undefined;
      }
      this.cdr.detectChanges();
    } catch (error) {
      this.showNotificationResponseStatus(NotificationType.ERROR,NotificationResponseMessages.FETCH_FAILURE)
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
      } else {
          this.showNotificationResponseStatus(NotificationType.ERROR,NotificationResponseMessages.UPDATE_ERROR)
      }
    } catch (error) {
      this.showNotificationResponseStatus(NotificationType.ERROR,NotificationResponseMessages.UPDATE_FAILURE)
    }
  }

  navigate(pageName: string, assetType: string | undefined = undefined) {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${selectedProjectId}/${pageName}`,
    ]);
    this.close();
  }

  showNotificationResponseStatus(type: NotificationType, message: string) {
    switch (type) {
        case NotificationType.SUCCESS:
            this.toaster.success(message);
            break;
        case NotificationType.ERROR:
            this.toaster.error(message);
            break;
        case NotificationType.INFO:
            this.toaster.info(message);
            break;
        case NotificationType.WARNING:
            this.toaster.warning(message,);
            break;
        case NotificationType.SYSTEM:
            this.toaster.info(message);
            break;
        default:
            this.toaster.info(message);
    }
  }

}
