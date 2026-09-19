import { Component, ChangeDetectorRef } from '@angular/core';
import { Workflow } from '../../models/workflow-models';
import { Router } from '@angular/router';
import { ConfigService } from 'src/app/services/config.service';
import { MatDialog } from '@angular/material/dialog';
import { Utils } from 'src/app/utils';
import { WorkflowSession } from 'src/app/models/workflow-sessions-api-response.models';
import { Project } from 'src/app/models/project-models';
import { CreateSessionComponent } from '../create-session/create-session.component';
import { FeatureFlagService } from 'src/app/services/feature-flag.service';
import { ApiService } from 'src/app/services/api.service';
import { ToastrService } from 'ngx-toastr';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { lastValueFrom } from 'rxjs';
@Component({
  selector: 'app-tools',
  templateUrl: './tools.component.html',
  styleUrls: ['./tools.component.less'],
})
export class ToolsComponent {
  numberOfColumns: number = 1;
  screenWidth: number = 0;
  IsCreatingNewWorkflowSession: boolean = false;
  isDataSheetGenerator: boolean = false;
  searchText: string = '';
  dataSource = [
    {
      name: 'Datasheet Generator',
      image: 'assets/data-sheet-generator.png',
      default_user: false,
    },
    {
      name: 'Scrap Analysis',
      image: 'assets/data-sheet-generator.png',
      default_user: false,
    },
    {
      name: 'UC6',
      image: 'assets/data-sheet-generator.png',
      default_user: false,
    },
    {
      name: 'UC7/Data Catalog',
      image: 'assets/data-sheet-generator.png',
      default_user: false,
    },
    {
      name: 'UC12',
      image: 'assets/data-sheet-generator.png',
      default_user: false,
    },
    {
      name: 'UC1-Configuration',
      image: 'assets/data-sheet-generator.png',
      default_user: false,
    },
    {
      name: 'Data Catalog',
      image: 'assets/data-sheet-generator.png',
      default_user: false,
    },
    {
      name: 'UC2-Visualization-results',
      image: 'assets/data-sheet-generator.png',
      default_user: false,
    },
    {
      name: 'UC3-Dashboard',
      image: 'assets/data-sheet-generator.png',
      default_user: false,
    },
  ];
  searchResults: any
  isEditPermission: boolean = false;
  permissionsList = [];
  isSavingPermission: boolean = true;
  showLoader:boolean = true;
  appHubApplicationsList: any = [];
  private boundResizeFunction: () => void;

  constructor(
    private cdRef: ChangeDetectorRef,
    private router: Router,
    private configService: ConfigService,
    private featureFlagService: FeatureFlagService,
    private apiService: ApiService,
    public toaster: ToastrService,
    private http: HttpClient
  ) {
    this.boundResizeFunction = this.onResize.bind(this);
    window.addEventListener('resize', this.boundResizeFunction);
    this.applyFeatureFlagsForAppList()
    // this.searchResults = [...this.dataSource];
  } 

  ngOnInit(): void {
    
    this.numberOfColumns = this.getNumberOfColumns();
    this.getAppPermissions();
    this.getAppHubApplications()
  }

  async getAppHubApplications() {
    try {
      let response: any = await lastValueFrom(this.http.get(environment.apiUrl + "/v1/apphub/applications"))
      this.appHubApplicationsList = response;
    }
    catch(error) {
      console.error("Unable to fetch the appHub list", error)
    }
  }

  getAppPermissions(): void {
    let site_id = this.configService.SelectedSiteId
    this.apiService.getPermissions(site_id).subscribe((permissions: any) => {
      if(permissions.length > 0) {
        this.permissionsList = permissions
        permissions.forEach((data:any)=>{
        const displayName = this.getAppName(data.app_name);
        const foundApp = this.dataSource.find((app: any) => app.name === displayName);
      if (foundApp) {
        foundApp.default_user = data.default_user;
      }          
      })

      let userState = localStorage.getItem('currentUser');
      if (userState) {
        const parsedUserState = JSON.parse(userState);
        if(parsedUserState?.server_role == 'Server Admin' || parsedUserState?.server_role == 'Project Admin'){
          this.isEditPermission = true
          this.searchResults = [...this.dataSource];
        }
        else
        {
          this.isEditPermission = false
          this.searchResults = this.dataSource.filter((per:any)=> per.default_user)
          let arr = this.dataSource.filter((per:any)=> per.default_user)
        }
        // this.searchResults.push({
        //   name: 'Scrap Analysis',
        //   image: 'assets/data-sheet-generator.png',
        //   default_user: false,
        // })

        this.showLoader = false;
      }
    }
    })
       
  }


  getAppName(appName:any){
    switch (appName) {
      case "ScrapAnalysis":
        return 'Scrap Analysis';
      case "DatasheetGenerator":
        return 'Datasheet Generator';
      case "UC6":
        return 'UC6';
      case "UC7_DataCatalog":
        return 'UC7/Data Catalog';
      case "UC12":
        return 'UC12';
      case "UC1_Configuration":
        return 'UC1-Configuration';
      case "DataCatalog":
        return 'Data Catalog';
      case "UC2_Result_Visualization":
        return 'UC2-Visualization-results';
      default:
      return null;
    }
  }

  applyFeatureFlagsForAppList() {
    this.dataSource =  this.dataSource.filter((app: any) => {
      return !this.featureFlagService.featureFlags?.disabledApps?.includes(app.name)
    })
  }

  viewCustomBuilder() {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${selectedProjectId}/custom-code-builder`,
    ]);

  }

  ngAfterViewInit() {
    setTimeout(() => {
      this.calculateColumns();
    }, 250);
  }

  ngOnDestroy() {
    window.removeEventListener('resize', this.boundResizeFunction);
  }

  onResize(event?: Event) {
    this.calculateColumns();
    this.screenWidth = window.innerWidth;
    this.cdRef.detectChanges();
  }

  private calculateColumns() {
    const parentWidth = document.querySelector('[fxLayout]')!.clientWidth; // Ensure this selects your flex container
    this.numberOfColumns = Utils.CalculateColumns(parentWidth);
  }

  getNumberOfColumns(): number {
    let screenWidth = window.innerWidth;
    let tileCount = Math.floor(screenWidth / 220);
    return tileCount;
  }

  onCloseCreateNewWorkflowSessionDialog() {
    this.IsCreatingNewWorkflowSession = false;
  }

  OnWorkflowSessionCreated(workflowSession: WorkflowSession) {
    this.IsCreatingNewWorkflowSession = false;
    this.onViewWorkflowSession(workflowSession._id);
  }

  createNewWorkflowSession(event : any) {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    if(event == 'UC1-Configuration') {
      this.viewTrainModelPage()
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    if(event == 'UC6')
    {
      const url = `https://azldspock01:8050`
      window.open(url, '_blank')
    }
    if(event == 'UC7/Data Catalog')
    {
      const url = `http://azldspock02.az.micron.com:8891`
      window.open(url, '_blank')
    }
    if(event == 'UC12')
    {
      const url = `http://azldspock01.az.micron.com:8891/uc12`
      window.open(url, '_blank')
    }
    if (event == 'Data Catalog') {      
      this.viewDataCatalogPage();
    }

    this.IsCreatingNewWorkflowSession = true;
  }

  closeDataSheetGenerator(): void {
    this.isDataSheetGenerator = false;
  }

  onViewWorkflowSession(workflowSessionId: any) {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    this.router.navigate(['/workflow-designer'], {
      queryParams: {
        siteId: this.configService.SelectedSiteId,
        projectId: selectedProjectId,
        workflowSessionId: workflowSessionId,
      },
    });

  }

  onSearchTextChange() {
    const lowerCaseQuery = this.searchText.toLowerCase();

    if (lowerCaseQuery.trim() === '') {
      this.searchResults = this.dataSource;
      return;
    }

    this.searchResults = this.dataSource.filter((workflow: any) => {
      const searchableFields = ['name'];
      return searchableFields.some((field) =>
        workflow[field].toLowerCase().includes(lowerCaseQuery),
      );
    });
  }

  viewDataSheet() {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${selectedProjectId}/data-sheet-generator`,
    ]);
  }

  viewScrapAnalysis() {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${selectedProjectId}/scrap-analysis`,
    ]);
  }



  viewTrainModelPage() {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${selectedProjectId}/train-predictions`,
    ]);
  }
  viewDataCatalogPage() {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${selectedProjectId}/data-catalog`,
    ]);
  }

  uc2Results() {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${selectedProjectId}/uc2-results`,
    ]);
  }

  uc2ResultsNew() {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${selectedProjectId}/uc2-results-new`,
    ]);
  }

  navigateTo(name: string): void {
    if(this.isEditPermissionEnabled) return;
    switch (name) {
      case 'Datasheet Generator':
        this.viewDataSheet();
        break;
      case 'UC2-Visualization-results':
        this.uc2ResultsNew();
        break;
      case 'UC3-Dashboard':
        this.ucThreeDashboard();
        break;
      case 'Custom Code Widget Builder':
        this.viewCustomBuilder();
        break;
      case 'Scrap Analysis':
        this.viewScrapAnalysis();
        break;
      default:
        this.createNewWorkflowSession(name);
    }
  }

  isEditPermissionEnabled = false;
  enableEdit() {
    this.isEditPermissionEnabled = true 
  }

  openUrlInNewTab(url: string) {
    if(url) {
      window.open(url,'_blank')
    }
  }

  ucThreeDashboard() {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${selectedProjectId}/uc3Dashboard`,
    ]);
  }

  updateRbac() {
    this.isSavingPermission = true;
    let site_id = this.configService.SelectedSiteId
    let updatePermission: any = []
    this.permissionsList.forEach((data:any)=>{
      let obj : any = {}
      let app_name = this.getAppName(data.app_name)
      if(app_name){
        let matchedEntry = this.dataSource.find((item: any) => item.name === app_name);
        if(matchedEntry){
          obj['default_user'] = matchedEntry.default_user
          obj['app_name'] = data.app_name
          updatePermission.push(obj)
        }
        else
        {
          obj['default_user'] = false
          obj['app_name'] = data.app_name
          updatePermission.push(obj)
        }
      }
      
    })
    
    this.apiService.updatePermissions(site_id,updatePermission).subscribe(
      (updated: any) => {
      if(updated)
      {
        this.toaster.success("Permissions updated successfully")
        this.getAppPermissions();        
      }
    },
    (error) => {
      this.toaster.error("Failed to update permissions. Please try again.");
      console.error("Error updating permissions:", error);
      this.isSavingPermission = false;
    })

    this.isEditPermissionEnabled = false
    
  }
  isEnableEditPermission():boolean {
      return this.permissionsList.every((data: any) => {
      const app_name = this.getAppName(data.app_name);
      const matchedItem = this.dataSource.find((item: any) => item.name === app_name);
      return matchedItem && data.default_user === matchedItem.default_user;
    });
  }

  updateStatus(){
    this.isSavingPermission = this.isEnableEditPermission()   
  }
}
