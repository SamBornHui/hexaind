import {
  Component,
  EventEmitter,
  Input,
  Output,
  HostListener,
  ElementRef,
} from '@angular/core';
import { NavService } from './nav.service';
import { Page } from '../../main/main.component';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { ApiService } from 'src/app/services/api.service';
import { Router } from '@angular/router';
import { DataService } from 'src/app/pages/data/services/data.service';
import { ConfigService } from '../../services/config.service';
import { Project } from 'src/app/models/project-models';

@Component({
  selector: 'app-left-nav',
  templateUrl: './left-nav.component.html',
  styleUrls: ['./left-nav.component.less'],
})
export class LeftNavComponent {
  @Output() navigateEvent: EventEmitter<any> = new EventEmitter();
  @Input() message: string = '';
  @Input() type: 'success' | 'error' = 'success'; // default to 'success'
  show: boolean = false;

  isAiExpanded = false;
  isAdminExpanded = false;
  isAssetsExpanded = false;
  isToolsExpanded = false;
  isDashboardsExpanded = false;
  notificationCount: any;
  isSmallScreen: boolean = false;
  notifications: any[] = [];

  Page = Page;
  rolesfeaturesString: any;
  user: any;
  project_id: any;

  activeDataset: string = '';
  http: any;
  rolesfeatures: any;
  assets: any = {};
  tools: any = {};
  getFeaturesList: any = {};
  getFeaturesListLocalstorage: any = {};
  role_name: any;
  user_id: any;

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    let assetsNav = this.eRef.nativeElement.querySelector(
      '.collapsed .assets-nav',
    );

    if (assetsNav) {
      const isClickInsideassetsNav = assetsNav.contains(event.target);
      if (!isClickInsideassetsNav) {
        this.isAssetsExpanded = false;
      }
    }

    let toolsNav = this.eRef.nativeElement.querySelector(
      '.collapsed .tools-nav',
    );

    if (toolsNav) {
      const isClickInsidetoolsNav = toolsNav.contains(event.target);
      if (!isClickInsidetoolsNav) {
        this.isToolsExpanded = false;
      }
    }

    let adminexp = this.eRef.nativeElement.querySelector(
      '.collapsed .admin-exp',
    );

    if (adminexp) {
      const isClickInsideadminexp = adminexp.contains(event.target);
      if (!isClickInsideadminexp) {
        this.isAdminExpanded = false;
      }
    }
  }

  constructor(
    public navService: NavService,
    private breakpointObserver: BreakpointObserver,
    private apiService: ApiService,
    private eRef: ElementRef,
    private router: Router,
    private dataService: DataService,
    private configService: ConfigService,
  ) {
    const storedFeatures = localStorage.getItem('rolesfeatures');
    const storedName = localStorage.getItem('rolesName');
    //this.role_name = this.getFeaturesList.role_info.name;
    if (storedName !== null) {
      try {
        const parsedName = JSON.parse(storedName);
        this.role_name = parsedName.name;
      } catch (error) {
        console.error('Error parsing storedName JSON', error);
      }
    }
    if (storedFeatures !== null) {
      this.getFeaturesListLocalstorage = JSON.parse(storedFeatures);
      if (this.getFeaturesListLocalstorage !== null) {
        this.assets = this.getFeaturesListLocalstorage.assets;
        this.tools = this.getFeaturesListLocalstorage.tools;
      } else {
        this.assets = {};
        this.tools = {};
        console.error('No rolesfeatures found in localStorage.');
      }
    }
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    let SelectedRoleId: string | undefined = this.configService.SelectedRoleId;
    if (selectedProjectId) {
      if (SelectedRoleId == 'Not Applicable') {
      } else {
        this.apiService
          .getFeaturesMappingProject(SelectedRoleId)
          .then((features) => {
            if (features) {
              this.getFeaturesList = features;
              if (this.getFeaturesList.role_info) {
                localStorage.setItem(
                  'rolesfeatures',
                  JSON.stringify(this.getFeaturesList.role_info.features),
                );
                localStorage.setItem(
                  'rolesName',
                  JSON.stringify(this.getFeaturesList.role_info),
                );

                if (this.getFeaturesList.role_info.features !== null) {
                  this.assets = this.getFeaturesList.role_info.features.assets;
                  this.tools = this.getFeaturesList.role_info.features.tools;
                } else {
                  this.assets = {};
                  this.tools = {};
                  console.error('No rolesfeatures found in localStorage.');
                }
              }
            } else {
              localStorage.removeItem('rolesfeatures');
            }
          })
          .catch((error) => {
            console.error('Error fetching features:', error);
            localStorage.removeItem('rolesfeatures');
          });
      }
    }

    this.display();
    this.breakpointObserver
      .observe([Breakpoints.Handset, Breakpoints.Small])
      .subscribe((state) => {
        this.isSmallScreen = state.matches;
        if (!this.isSmallScreen) {
          navService.isNavCollapsed = false;
        } else {
          navService.isNavCollapsed = true;
        }
      });
    this.user = localStorage.getItem('currentUser');
    this.project_id = this.configService.SelectedProjectId;
    this.user = JSON.parse(this.user);
    this.loadNotifications(undefined);
  }

  isEmptyObject(obj: any): boolean {
    // Check if obj is null or undefined
    if (obj === null || obj === undefined) {
      return true; // If obj is null or undefined, consider it empty
    }

    // Check if the object is empty
    return Object.keys(obj).length === 0;
  }

  ngOnInit() {
    this.apiService.updateNotificationStatus$.subscribe(() => {
      this.loadnotifications(undefined);
    });
  }

  // ngAfterViewInit() {
  //   this.loadnotifications(undefined);
  // }

  // onRefreshView() {
  //   this.loadnotifications(undefined);
  // }

  toggleSection(section: string): void {
    if (section === 'ai') {
      this.isAiExpanded = !this.isAiExpanded;
    } else if (section === 'admin') {
      this.isAdminExpanded = !this.isAdminExpanded;
    } else if (section === 'assets') {
      this.isAssetsExpanded = !this.isAssetsExpanded;
    } else if (section === 'tools') {
      this.isToolsExpanded = !this.isToolsExpanded;
    } else if (section === 'dashboards') {
      this.isDashboardsExpanded = !this.isDashboardsExpanded;
    }
  }
  public display(): void {
    this.show = true;
    setTimeout(() => {
      this.show = false;
    }, 4000);
  }
  public dismiss() {
    this.show = false;
  }

  async loadnotifications(searchTerms: string | undefined) {
    this.notifications = [];
    this.notifications = await this.apiService.GetNotifications(
      '1',
      this.project_id,
      searchTerms,
    );
    if (this.notifications) {
      this.notificationCount = this.notifications.length;
    }
  }

  getUnreadNotificationCount(): number {
    return this.notifications.filter((notification) => !notification.read)
      .length;
  }

  navigate(pageName: string, assetType: string | undefined = undefined) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${selectedProjectId}/${pageName}`,
    ]);
    if (assetType) {
      this.dataService.changeAssetType(assetType);
      this.activeDataset = assetType;
    } else {
      this.activeDataset = '';
    }
  }

  async loadNotifications(searchTerms: string | undefined): Promise<void> {
    try {
      this.notifications = await this.apiService.GetNotifications(
        '1',
        this.project_id,
        searchTerms
      );
      this.notificationCount = this.notifications.filter((notification) => !notification.read.includes(this.user._id))
        .length;
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  }
}
