import { Injectable, OnInit } from '@angular/core';
import { BehaviorSubject, filter } from 'rxjs';
import { Project } from '../models/project-models';
import { environment } from '../../environments/environment';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { ApiService } from './api.service';
import { Utils } from '../utils';

@Injectable({
  providedIn: 'root',
})
export class ConfigService {
  public SelectedSiteId: string = '1';
  private appApiURL: string | undefined = undefined;
  private appAuxApiURL: string | undefined = undefined;
  private appMBApiURL: string | undefined = undefined;
  SelectedRoleId: string | undefined = undefined;

  private _selectedProjectIdSubject = new BehaviorSubject<string | undefined>(
    undefined,
  );
  selectedProjectIdObservable = this._selectedProjectIdSubject.asObservable();

  set SelectedProjectId(value: string | undefined) {
    this._selectedProjectIdSubject.next(value);
    this.updateApiUrl();
    this.updateAuxApiUrl();
  }

  get SelectedProjectId(): string | undefined {
    return this._selectedProjectIdSubject.getValue();
  }

  private _selectedProjectNameSubject = new BehaviorSubject<string | undefined>(
    undefined,
  );
  selectedProjectNameObservable =
    this._selectedProjectNameSubject.asObservable();

  set SelectedProjectName(value: string) {
    this._selectedProjectNameSubject.next(value);
    this.updateApiUrl();
    this.updateAuxApiUrl();
  }

  get SelectedProjectName(): string | undefined {
    return this._selectedProjectNameSubject.getValue();
  }

  constructor(
    private route: ActivatedRoute,
    private router: Router,
  ) {
    this.router.events
      .pipe(filter((event) => event instanceof NavigationEnd))
      .subscribe(() => {
        this.handleRouteParams();
      });

    this.route.queryParams.subscribe((params) => {
      if (params['projectId']) {
        this.SelectedProjectId = params['projectId'];
      }
      if (params['sites']) {
        this.SelectedSiteId = params['sites'];
      }
      if (!this.SelectedProjectId) {
        // Get the current router state
        const routerState = this.router.routerState;
        // Get the current activated route
        const activatedRoute = routerState.snapshot.root;
        // Get the URL segments from the activated route
        const urlSegments = activatedRoute.children[0]?.url;
        // Find the index of '/projects/' in the URL segments
        if (urlSegments) {
          const projectsIndex = urlSegments.findIndex(
            (segment) => segment.path === 'projects',
          );
          if (projectsIndex !== -1 && projectsIndex + 1 < urlSegments.length) {
            // Get the project ID segment
            const projectIdSegment = urlSegments[projectsIndex + 1];
            // Extract the project ID
            if (projectIdSegment.path) {
              this.SelectedProjectId = projectIdSegment.path;
            }
          }
        }
      }
    });
  }

  private handleRouteParams(): void {
    this.route.queryParams.subscribe((params) => {
      if (params['projectId']) {
        if (this.SelectedProjectId != params['projectId']) {
          this.SelectedProjectId = params['projectId'];
        }
      }
      if (params['sites']) {
        this.SelectedSiteId = params['sites'];
      }
      if (!this.SelectedProjectId) {
        const urlSegments = this.router.url.split('/');
        const projectsIndex = urlSegments.indexOf('projects');
        if (projectsIndex !== -1 && projectsIndex + 1 < urlSegments.length) {
          this.SelectedProjectId = urlSegments[projectsIndex + 1];
        }
      }
    });
  }

  private updateApiUrl() {
    if (this.SelectedProjectId) {
      const url = `${environment.apiUrl}/v1/sites/${this.SelectedSiteId}/projects/${this.SelectedProjectId}`;
      this.appApiURL = url;
    }
  }

  get getAppApiURL(): string | undefined {
    this.updateApiUrl();
    return this.appApiURL;
  }

  // ---- AUX

  private updateAuxApiUrl() {
    if (this.SelectedProjectId) {
      const url = `${environment.auxApiUrl}/v1/sites/${this.SelectedSiteId}/projects/${this.SelectedProjectId}`;
      this.appAuxApiURL = url;
    }
  }

  get getAppAuxApiURL(): string | undefined {
    this.updateAuxApiUrl();
    return this.appAuxApiURL;
  }

  // ----

  // Model Builder URL
  private updateMBApiUrl() {
    if (this.SelectedProjectId) {
      const url = `${environment.mbapiUrl}/v1/sites`;
      this.appMBApiURL = url;
    }
  }

  get getMBAppApiURL(): string | undefined {
    this.updateMBApiUrl();
    return this.appMBApiURL;
  }

  // Data API URL
  private _dataApiUrl = new BehaviorSubject<string>(
    `${environment.apiUrl}/data`,
  );

  get getDataApiUrl(): string {
    return this._dataApiUrl.getValue();
  }

  // Data API URL
  private _BasicdataApiUrl = new BehaviorSubject<string>(
    `${environment.apiUrl}`,
  );

  get getBasicDataApiUrl(): string {
    return this._BasicdataApiUrl.getValue();
  }

  private _configureApiUrl = new BehaviorSubject<string>(
    `${environment.apiUrl}`,
  );

  get getConfigureApiUrl(): string {
    return this._configureApiUrl.getValue();
  }

  // Auth URL
  private _authUrl = new BehaviorSubject<string>(
    `${environment.apiUrl}/v1/authentication`,
  );

  get getAuthUrl(): string {
    return this._authUrl.getValue();
  }

  // API URL
  private _apiUrl = new BehaviorSubject<string>(
    `${environment.apiUrl}/v1/sites`,
  );

  get getSocketBaseUrl(): string {
    return `wss:${Utils.removeHttpsFromUrl(environment.apiUrl)}`;
  }

  get getApiUrl(): string {
    return this._apiUrl.getValue();
  }

  // ---

  // EDA URL
  private _auxApiUrl = new BehaviorSubject<string>(
    `${environment.auxApiUrl}/v1/sites`,
  );

  get getAuxApiUrl(): string {
    return this._auxApiUrl.getValue();
  }

  // ----

  private _apiAuthUrl = new BehaviorSubject<string>(
    `${environment.apiUrl}/v1/authentication`,
  );

  get getAuthApiUrl(): string {
    return this._apiAuthUrl.getValue();
  }

  private _apiSiteManagementUrl = new BehaviorSubject<string>(
    `${environment.apiUrl}/v1/site-management`,
  );

  get getSiteManagementApiUrl(): string {
    return this._apiSiteManagementUrl.getValue();
  }

  // Site Name
  private _siteName = new BehaviorSubject<string>('');
  siteName$ = this._siteName.asObservable();

  set siteName(value: string) {
    this._siteName.next(value);
  }

  get siteName(): string {
    return this._siteName.getValue();
  }

  // Workflow Name
  private _workflowName = new BehaviorSubject<string>('');
  private _workflowSessionName = new BehaviorSubject<string>('');

  workflowName$ = this._workflowName.asObservable();

  set workflowName(value: string) {
    this._workflowName.next(value);
  }

  get workflowName(): string {
    return this._workflowName.getValue();
  }

  set workflowSessionName(value: string) {
    this._workflowSessionName.next(value);
  }

  get workflowSessionName(): string {
    return this._workflowSessionName.getValue();
  }

  // Source remote drive
  private _sourceRemoteDrive = new BehaviorSubject<string>('\\azure-mount\\');
  sourceRemoteDrive$ = this._sourceRemoteDrive.asObservable();
  set sourceRemoteDrive(value: string) {
    this._sourceRemoteDrive.next(value);
  }

  get sourceRemoteDrive(): string {
    return this._sourceRemoteDrive.getValue();
  }

  // Data folder
  private _dataFolder = new BehaviorSubject<string>('\\hexaind-data\\');
  dataFolder$ = this._dataFolder.asObservable();

  set dataFolder(value: string) {
    this._dataFolder.next(value);
  }

  get dataFolder(): string {
    return this._dataFolder.getValue();
  }

  // Home folder
  private _homeFolder = new BehaviorSubject<string>('\\hexaind-home\\');
  homeFolder$ = this._homeFolder.asObservable();

  set homeFolder(value: string) {
    this._homeFolder.next(value);
  }

  get homeFolder(): string {
    return this._homeFolder.getValue();
  }

  // Mongo DB URL
  private _mongoDbUrl = new BehaviorSubject<string>(
    `mongodb://${environment.dbUrl}`,
  );
  mongoDbUrl$ = this._mongoDbUrl.asObservable();

  set mongoDbUrl(value: string) {
    this._mongoDbUrl.next(value);
  }

  get mongoDbUrl(): string {
    return this._mongoDbUrl.getValue();
  }

  // Mongo DB Name
  private _mongoDbName = new BehaviorSubject<string>('hexaind_mongo_db');
  mongoDbName$ = this._mongoDbName.asObservable();

  set mongoDbName(value: string) {
    this._mongoDbName.next(value);
  }

  get mongoDbName(): string {
    return this._mongoDbName.getValue();
  }

  // Azure App Insigts Connection String
  private _azureAppInsightsConnectionString = new BehaviorSubject<string>(
    'InstrumentationKey=f77e17bb-6f67-464f-a85f-dfa63e253d18;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/',
  );
  azureAppInsightsConnectionString$ = this._mongoDbUrl.asObservable();

  set azureAppInsightsConnectionString(value: string) {
    this._azureAppInsightsConnectionString.next(value);
  }

  get azureAppInsightsConnectionString(): string {
    return this._azureAppInsightsConnectionString.getValue();
  }

  // SCHEMA URL
  private _schemaUrl = new BehaviorSubject<string>(
    `${environment.apiUrl}/v1/widget`,
  );

  get getSchemaUrl(): string {
    return this._schemaUrl.getValue();
  }

  getImageDatasetUrl() {
    return `${environment.apiUrl}/v1/image_datasets`;
    // private updateApiUrl() {
    //   if (this.SelectedProjectId) {
    //     const url = `${environment.apiUrl}/v1/image_datasets/sites/${this.SelectedSiteId}/projects/${this.SelectedProjectId}`;
    //     this.appApiURL = url;
    //   }
  }
  getImageAnalysisUrl() {
    return `${environment.apiUrl}/v1/image_analysis/sites/${this.SelectedSiteId}/projects/${this.SelectedProjectId}`;
  }

  getProjectId() {
    return this.SelectedProjectId;
  }
}
