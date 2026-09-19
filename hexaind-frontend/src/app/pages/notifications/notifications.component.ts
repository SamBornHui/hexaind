import { Component, ChangeDetectorRef, ViewChild, Output, EventEmitter, OnInit } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { NotificationDetailsComponent } from './notification-details/notification-details.component';
import { ConfigService } from 'src/app/services/config.service';
import { ToastrService } from 'ngx-toastr';
@Component({
  selector: 'app-notifications',
  templateUrl: './notifications.component.html',
  styleUrls: ['./notifications.component.less']
})
export class NotificationsComponent implements OnInit {
  @ViewChild(NotificationDetailsComponent, { static: false }) notificationDetailsComponent: NotificationDetailsComponent | undefined;
  @Output() tabChange = new EventEmitter<string>();
  tabs = [
    { title: 'Tab 1', content: 'Content for Tab 1' },
    { title: 'Tab 2', content: 'Content for Tab 2' },
    { title: 'Tab 3', content: 'Content for Tab 3' }
  ];

  notifications: any[] = [];
  notificationCount: number = 4;
  selectedTab: string = 'Unread'; // Default tab
  notificationstatus: any;
  user: any;
  projectId: any

  constructor(
    private apiService: ApiService,
    private cdr: ChangeDetectorRef,
    private configService: ConfigService,
    private toaster: ToastrService
  ) {
    this.user = localStorage.getItem('currentUser');
    this.user = JSON.parse(this.user);
    this.projectId = this.configService.SelectedProjectId
  }

  ngOnInit() {
    this.loadnotifications(undefined);
  }

  receiveData(data: string) {
    this.loadnotifications(undefined);
  }

  async loadnotifications(searchTerms: string | undefined) {
    try {
      this.notifications = await this.apiService.GetNotifications("1", this.projectId, searchTerms);
      this.getUnreadNotificationCount();
      this.cdr.detectChanges();
    } catch (error) {
      const errorMessage = 'Error while fetching notifications. Please try again later.';
      this.toaster.error(
        errorMessage,
        'ERROR',
        {
          positionClass: 'custom-toast-position',
        }
      );
    }
  }

  selectTab(tab: string) {
    this.selectedTab = tab;
    this.tabChange.emit(tab);
  }

  getUnreadNotificationCount(): number {
    return this.notifications.filter(notification => !notification.read.includes(this.user._id)).length;
  }

}
