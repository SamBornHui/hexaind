import { Component, Renderer2, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ElementRef, ViewChild, HostListener } from '@angular/core';
import { Router, NavigationEnd, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { UserLoginService } from '../../pages/login/login.service';
import { ConfigService } from '../../services/config.service';
import { ApiService } from 'src/app/services/api.service';
import { debounceTime, Observable, Subject, Subscription } from 'rxjs';
import { NotificationComponent } from '../notification/notification.component';
import { ManageAccountComponent } from '../../controls/manage-account/manage-account.component';
import { NotificationDailogComponent } from '../../controls/notification-dailog/notification-dailog.component';
import { ShowPagesService } from 'src/app/services/show-pages.service';
import { Project } from 'src/app/models/project-models';
import { Utils } from 'src/app/utils';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { ProjectButtonVisibilityServiceService } from './project-button-visibility-service.service';
import { WebSocketService } from 'src/app/services/web-sockets.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.less'],
})
export class HeaderComponent {
  @ViewChild('notification') notificationComponent!: NotificationComponent;
  notificationCount$!: Observable<number>;
  private routerEventsSubscription: Subscription;
  socketSubscription!: Subscription;
  notificationCountSubscription: Subscription | undefined;
  webSocketSubscription: Subscription | undefined;
  socketData: any;

  userInfo: any;
  fullName: string = '';
  initials: string = '';
  page_name: string = '';
  enable_legacy: boolean = false;
  enable_hexaind3: boolean = true;
  role_id: any;
  showUserContextMenu = false;
  showUserProfilePanel = false;
  showNotificationsContextMenu = false;
  showSettingsContextMenu = false;
  menuPosition = { x: 0, y: 0 };
  userProfilePanelPosition = { x: 0, y: 0 };
  user_id: any;
  project_values: any;
  projects: Project[] = [];
  filteredProjects: Project[] = [];
  private projectSubscription: Subscription = new Subscription();
  subscription: Subscription = new Subscription();
  selectedProject: Project | undefined = undefined;
  project_id: any;
  notifications: any[] = []; // Array to store notifications
  notificationCount: number = 0;
  searchTerm: string = '';
  searchSubject: Subject<string> = new Subject<string>();
  @ViewChild('searchInput') searchInput!: ElementRef;
  constructor(
    private authService: AuthService,
    private loginService: UserLoginService,
    private router: Router,
    private eRef: ElementRef,
    private renderer: Renderer2,
    private configService: ConfigService,
    private apiService: ApiService,
    private dialog: MatDialog,
    private showPagesService: ShowPagesService,
    private sharedDataService: SharedDataService,
    public projectButtonVisibilityService: ProjectButtonVisibilityServiceService,
    private route: ActivatedRoute,
    public webSocketService: WebSocketService,
    public toaster: ToastrService,
    private http: HttpClient,
  ) {
    this.route.params.subscribe((params) => {
      this.project_id = params['projectId'];
    });
    if (this.project_id === undefined) {
      this.project_id = this.configService.SelectedProjectId;
    }

    this.project_values = localStorage.getItem('projects_values');
    this.role_id = localStorage.getItem('role_id');
    this.routerEventsSubscription = this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        this.handleNavigationEnd(event);
      }
    });
    this.renderer.listen('document', 'click', (event) => {
      if (!(event.target instanceof HTMLSelectElement)) {
        if (this.eRef.nativeElement.contains(event.target)) {
          this.hideContextMenus();
        }
      }
    });

    let user: any = localStorage.getItem('currentUser');
    this.userInfo = JSON.parse(user);
    this.user_id = this.userInfo._id;
    this.fullName = Utils.getUserFullName(this.userInfo);
    this.initials = Utils.getUserInitials(this.userInfo);
    // if (this.configService.SelectedProjectId) {
    //   this.loadProjects(this.configService.SelectedProjectId);
    // }
    this.projectSubscription.add(
      this.configService.selectedProjectIdObservable.subscribe((projectId) => {
        if (projectId) {
          this.loadProjects(projectId);
        }
      }),
    );
    this.loadNotifications(undefined);
    const apiURL = `${environment.apiUrl}/ws`;
    const socketURL = apiURL.replace(/^http/, 'ws');
    this.webSocketService.connect(socketURL);
    this.searchSubject.pipe(debounceTime(300)).subscribe((term) => {
      this.filterProjects(term);
    });
  }

  ngOnInit(): void {
    this.notificationCountSubscription =
      this.apiService.notificationCount$.subscribe((count) => {
        this.notificationCount = count;
      });

    this.webSocketSubscription = this.webSocketService.messages.subscribe(
      (notification) => {
        const existingNotificationIndex = this.notifications.findIndex(
          (n) => n.created_at === notification.created_at,
        );
        if (existingNotificationIndex === -1) {
          if (notification.project_id) {
            let isValidProject = false;

            for (let project of JSON.parse(this.project_values)) {
              if (project._id === notification.project_id) {
                isValidProject = true;
                break;
              }
            }

            if (isValidProject) {
              this.notifications.push(notification);
              this.notificationCount = this.notifications.filter(
                (n) => !n.read.includes(this.user_id),
              ).length;
              if (
                notification.notification_category === 'MODEL' ||
                (notification.notification_category === 'WORKFLOWS' &&
                  notification.notification_type === 'SUCCESS')
              ) {
                this.toaster.info(notification.message, '', {
                  positionClass: 'custom-toast-position',
                });
              }
            }
          }
        }
      },
      (error) => {
        console.error('WebSocket error:', error);
      },
    );
  }

  async loadNotifications(searchTerms: string | undefined): Promise<void> {
    try {
      this.notifications = await this.apiService.GetNotifications(
        '1',
        this.project_id,
        searchTerms,
      );
      this.notificationCount = this.notifications.filter(
        (notification) => !notification.read.includes(this.user_id),
      ).length;
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  }

  isProjectAdministrator(): boolean {
    for (let project of this.projects) {
      if (project.role_name === 'PROJECT ADMINISTRATOR') {
        return true;
      }
    }

    return false;
  }

  onShowUserProfilePanelClicked(event: MouseEvent) {
    this.showUserProfilePanel = !this.showUserProfilePanel;
    var rightSideX = window.innerWidth;
    if (this.showUserProfilePanel) {
      this.userProfilePanelPosition.x = rightSideX - 270; // Adjusted the x position
      this.userProfilePanelPosition.y = 60;
    }
    event.stopPropagation();
  }

  async loadProjects(currentProjectId: string) {
    const jsonData = {
      id: this.user_id,
      get_details: true,
    };

    this.projects = await this.apiService.GetProjects(
      this.configService.SelectedSiteId,
      '',
      jsonData,
    );
    this.filteredProjects = [...this.projects];

    this.selectedProject = this.projects.find(
      (t) => t._id === currentProjectId,
    );
    if (this.selectedProject) {
      this.configService.SelectedProjectName =
        this.selectedProject?.project_name;
    }
  }

  onSearchChange(): void {
    this.searchSubject.next(this.searchTerm);
  }

  filterProjects(searchTerm: string): void {
    if (!searchTerm.trim()) {
      this.filteredProjects = this.projects;
    } else {
      this.filteredProjects = this.projects.filter((project) =>
        project.project_name.toLowerCase().includes(searchTerm.toLowerCase()),
      );
    }

    setTimeout(() => {
      if (this.searchInput && this.searchInput.nativeElement) {
        this.searchInput.nativeElement.focus();
      }
    }, 0);
  }

  getProjectName(project: Project) {
    return project.project_name;
  }

  onProjectSelected(project: Project): void {
    this.configService.SelectedProjectId = project._id!;
    this.project_id = project._id!;

    const urlTree = this.router.parseUrl(this.router.url);
    const segments = urlTree.root.children['primary'].segments;
    if (segments.length > 0) {
      this.page_name = segments[segments.length - 1].path;
    }

    // Check if the URL contains "image-analysis"
    const hasImageAnalysis = segments.some(
      (segment) => segment.path === 'image-analysis',
    );
    if (hasImageAnalysis) {
      // Redirect to the structure page if "image-analysis" is present in the URL
      this.router.navigate([
        `sites/${this.configService.SelectedSiteId}/projects/${project._id}/data-structure`,
      ]);
    } else {
      // Default navigation behavior
      this.router.navigate([
        `sites/${this.configService.SelectedSiteId}/projects/${project._id}/${this.page_name}`,
      ]);
    }

    this.loadNotifications(undefined);
  }

  onCloseUserProfilePanel() {
    this.showUserProfilePanel = false;
  }

  GetProjects() {
    this.router.navigate(['/']);
  }

  getSelectedProjectName() {
    if (this.selectedProject) {
      return this.selectedProject.project_name;
    }

    return 'Select a project...';
  }

  OnManageProjectsClicked() {
    this.router.navigate(['/']);
  }

  manageUsers() {
    this.router.navigate(['/manage-users']);
  }

  manageRoles() {
    this.router.navigate(['/roles']);
  }

  get showingPages() {
    return this.showPagesService.showingPages;
  }

  hideContextMenus() {
    this.showUserContextMenu = false;
    this.showNotificationsContextMenu = false;
    this.showSettingsContextMenu = false;
    this.showUserProfilePanel = false;
  }

  getContextMenuWidth(): number {
    const contextMenu = this.eRef.nativeElement.querySelector('.context-menu');
    if (!contextMenu) return 0;
    // Temporarily show and move the context menu off-screen for measuring
    contextMenu.style.display = 'block';
    contextMenu.style.left = '-9999px';
    const width = contextMenu.offsetWidth;
    // Reset the styles
    contextMenu.style.display = 'none';
    contextMenu.style.left = '0px';

    return width;
  }

  showAdminPanel() {
    this.router.navigate(['/admin-panel']);
  }

  showSitesPanel() {
    this.router.navigate(['/sites']);
  }

  changePassword() {
    this.router.navigate(['/change-password']);
  }

  logOut() {
    this.loginService.userLogout(this.userInfo.email).subscribe((response) => {
      this.authService.setLoggedIn(false);
      localStorage.removeItem('currentUser');
      localStorage.removeItem('currUserID');
      localStorage.removeItem('rolesfeatures');
      localStorage.removeItem('role_id');
      localStorage.removeItem('role_id_sso');
      localStorage.removeItem('rolesName');
      this.router.navigate(['/login']);
    });

    // this.hideContextMenus();
  }

  onSitesButtonClicked() {
    this.configService.SelectedProjectId = undefined;
    this.router.navigate(['/']);
  }

  onProjectsButtonClicked() {
    this.configService.workflowName = '';
    this.router.navigate(['/sites']);
  }

  onWorkflowButtonClicked() {}

  toggleNotificationsContextMenu(event: MouseEvent) {
    this.notificationComponent.display('You have no notifications.', 'success');
  }

  toggleSettingsContextMenu(event: MouseEvent) {
    this.showSettingsContextMenu = !this.showSettingsContextMenu;
    this.menuPosition.x = event.clientX - this.getContextMenuWidth(); // Adjusted the x position
    this.menuPosition.y = event.clientY;
    event.stopPropagation();
  }

  toggleUserContextMenu(event: MouseEvent) {
    this.showUserContextMenu = !this.showUserContextMenu;
    this.menuPosition.x = event.clientX - this.getContextMenuWidth(); // Adjusted the x position
    this.menuPosition.y = event.clientY;
    event.stopPropagation();
  }

  openManageAccountDialog(): void {
    const dialogRef = this.dialog.open(ManageAccountComponent, {
      width: '600px',
    });
    dialogRef.afterClosed().subscribe((result) => {
      let user: any = localStorage.getItem('currentUser');
      this.userInfo = JSON.parse(user);
      this.user_id = this.userInfo._id;
      this.fullName = Utils.getUserFullName(this.userInfo);
      this.initials = Utils.getUserInitials(this.userInfo);
    });
  }

  openNotificationDialog(): void {
    const dialogRef = this.dialog.open(NotificationDailogComponent, {
      width: '500px',
      height: '500px',
      // display: 'block',
      position: { right: '10px', top: '72px' },
    });
    dialogRef.afterClosed().subscribe((result) => {});
  }

  openJobsDialog(project_id: any): void {
    this.router.navigate([
      `sites/${this.configService.SelectedSiteId}/projects/${project_id}/jobs`,
    ]);
  }

  showUserPanel: boolean = false;

  toggleUserPanel() {
    this.showUserPanel = !this.showUserPanel;
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.showUserPanel = false;
    }
  }
  onUserPanelClick(event: MouseEvent) {
    event.stopPropagation();
  }

  private handleNavigationEnd(event: NavigationEnd): void {
    // Check if the current route is the home page
    const isHomePage = event.url === '/';

    // Update the showingPages property based on the current route
    this.showPagesService.showingPages['Projects'] = !isHomePage;
  }

  // ... Existing code

  ngOnDestroy(): void {
    // Unsubscribe from router events when the component is destroyed
    this.routerEventsSubscription.unsubscribe();
    this.projectSubscription.unsubscribe();
    this.subscription.unsubscribe();
    if (this.notificationCountSubscription) {
      this.notificationCountSubscription.unsubscribe();
    }
    if (this.webSocketSubscription) {
      this.webSocketSubscription.unsubscribe();
    }
  }

  navigate_url() {
    const siteId = this.configService.SelectedSiteId;
    const access_token = localStorage.getItem('access_token');
    const url = `${environment.hexaind2Urlext}/login`;
    const hexaind_url = `${environment.hexaind3Urlext}`;

    if (url == null) {
      this.toaster.warning(
        'HEXAIND Legacy is currently unavailable. Please contact the administrator.',
      );
    }

    //const url = `${hexaind2UrlExt}/login`;

    this.http.get(url, { responseType: 'text' }).subscribe({
      next: () => {
        const headers = new HttpHeaders({
          accessToken: `${access_token}`,
          'Custom-Header': 'value',
          Project_id: '',
          'Site-Id': siteId.toString(),
          hexaind_url: hexaind_url,
        });
        this.apiService.redirectToUrlWithHeaders(url, headers);
      },
      error: () => {
        this.toaster.warning(
          'HEXAIND Legacy is currently unavailable. Please contact the administrator.',
        );
      },
    });
  }

  // ManageAccess() {
  //   this.router.navigate(['/manage-access']);
  // }

  ManageAccess(role_id: any) {
    this.sharedDataService.RoleId = role_id;
    this.router.navigate(['/manage-access']);
  }

  // hexaind_legacy() {
  //   this.router.navigate([], {
  //     queryParams: { legacy: true },
  //     replaceUrl: true  // Replace current URL with new URL
  //   });
  // }

  // hexaind_3() {
  //   this.router.navigate([], {
  //     queryParams: { legacy: false },
  //     replaceUrl: true  // Replace current URL with new URL
  //   });
  // }
}
