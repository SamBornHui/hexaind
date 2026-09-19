import { MatTableDataSource } from '@angular/material/table';
import {
  ElementRef,
  Renderer2,
  Component,
  ChangeDetectorRef,
  EventEmitter,
  Output,
  OnInit,
  OnDestroy,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { ActivatedRoute, Route, Router } from '@angular/router';
import { ConfigService } from '../../services/config.service';
import { ApiService } from '../../services/api.service';
import { Project } from '../../models/project-models';
import { Utils } from '../../utils';
import { CreateNewProjectComponent } from 'src/app/dialogs/create-new-project/create-new-project.component';
import { HttpHeaders, HttpResponse } from '@angular/common/http';
import { Subscription } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { ProjectButtonVisibilityServiceService } from 'src/app/controls/header/project-button-visibility-service.service';
import { Sort } from '@angular/material/sort';

@Component({
  selector: 'app-projects',
  templateUrl: './projects.component.html',
  styleUrls: ['./projects.component.less'],
})
export class ProjectsComponent implements OnInit, OnDestroy {
  queryParamsSubscription: Subscription | undefined;
  legacyMode: boolean = false;
  M2projects: Project[] = [];
  M2projectsList: any;
  showingListView: boolean = true;
  loadAllProjects: any[] = [];
  getFeaturesList: any;
  rolefeatures: any;
  projectid_unique: any;

  onRowDblClick(_t196: any) {
    throw new Error('Method not implemented.');
  }
  @Output() workflowSelectedEvent = new EventEmitter<string>();
  @ViewChild('confirmationDialogTemplate')
  confirmationDialogTemplate!: TemplateRef<any>;
  dialogRef!: MatDialogRef<any>;
  selectedSiteId = 0;
  selectedProjectId = 0;
  selectedSiteRow: any = null;
  selectedProjectRow: any = null;
  showUserContextMenu = false;
  menuPosition = { x: 0, y: 0 };
  screenWidth: number = 0;
  searchText: string = '';
  descending: boolean = true;
  projectsList = new MatTableDataSource<Project>();
  currentUser: any;
  unfavoriteDatsets: any = [];
  favoriteDatasets: any = [];
  selectOwner: any = [];
  filteredResults: any = [];
  private boundResizeFunction: () => void;
  public deleteConfirmation: boolean = false;
  selectedValue: boolean = true;
  role_id: any;
  role_id_sso: any;
  areProjectsLoaded: boolean = false;

  constructor(
    private route: ActivatedRoute,
    private cdRef: ChangeDetectorRef,
    private renderer: Renderer2,
    private el: ElementRef,
    private router: Router,
    private configService: ConfigService,
    private apiService: ApiService,
    private dialog: MatDialog,
    private toaster: ToastrService,
    private projectVisibilityService: ProjectButtonVisibilityServiceService,
  ) {
    this.renderer.listen('document', 'click', (event) => {
      if (this.el.nativeElement.contains(event.target)) {
        this.showUserContextMenu = false;
      }
    });

    this.boundResizeFunction = this.onResize.bind(this);
    window.addEventListener('resize', this.boundResizeFunction);
  }

  onSearchTextChange(event: any) {
    let searchTerm = event.trim();
    let result = [];
    if (this.filteredResults.length === 0) {
      this.filteredResults = this.selectOwner;
    }
    if (searchTerm) {
      result = this.filteredResults.filter((session: any) => {
        const projectName = session.project_name.toLowerCase();
        const projectOwnerName = session.project_owner_name.toLowerCase();
        searchTerm = searchTerm.toLowerCase();
        if (
          projectName.includes(searchTerm) ||
          projectOwnerName.includes(searchTerm)
        ) {
          return (
            projectName.includes(searchTerm) ||
            projectOwnerName.includes(searchTerm)
          );
        } else {
          return false;
        }
      });
      this.projectsList.filteredData = result;
    } else {
      if (this.filteredResults.length > 0) {
        this.projectsList.filteredData = this.filteredResults;
      } else {
        this.projectsList.filteredData = this.selectOwner;
      }
    }
    //this.loadProjects(this.searchText);
  }

  displayedColumns: string[] = [
    'favorite',
    'name',
    'owner',
    'description',
    'created_at',
    'lastModified',
    'more_vert',
  ];
  projects: Project[] = [];
  IsCreatingNewProject: boolean = false;
  numberOfColumns: number = 0;

  ngOnDestroy(): void {
    this.projectVisibilityService.showProjectsButton();
    // Remove the event listener when the component is destroyed
    window.removeEventListener('resize', this.boundResizeFunction);
    if (this.queryParamsSubscription) {
      this.queryParamsSubscription.unsubscribe();
    }
  }

  onResize(event?: Event) {
    this.numberOfColumns = this.getNumberOfColumns();
    this.screenWidth = window.innerWidth;
    this.cdRef.detectChanges();
  }

  ngOnInit() {
    this.projectVisibilityService.hideProjectsButton();
    this.role_id = localStorage.getItem('role_id');
    this.role_id_sso = localStorage.getItem('role_id_sso');
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!) as any;
    this.numberOfColumns = this.getNumberOfColumns();
  }

  ngAfterViewInit() {
    this.loadProjects(undefined);
    this.screenWidth = window.innerWidth;
  }

  getNumberOfColumns(): number {
    let screenWidth = window.innerWidth;
    let tileCount = Math.floor(screenWidth / 220);
    return tileCount;
  }

  onCloseCreateNewProjectPanel() {
    this.IsCreatingNewProject = false;
  }

  OnProjectCreated(project: Project) {
    this.IsCreatingNewProject = false;
    this.projects.push(project);
  }

  createNewProject(): void {
    const dialogRef = this.dialog.open(CreateNewProjectComponent, {
      width: '560px',
      disableClose: true,
      data: { update: false },
    });
    dialogRef.componentInstance.closePanelClicked.subscribe(() => {
      dialogRef.close();
      this.onRefreshView();
    });
    dialogRef.afterClosed().subscribe((result) => {});
  }

  onRefreshView() {
    this.searchText = '';
    this.loadProjects(undefined);
    this.filteredResults.length = 0;
    this.selectedValue = false;
  }

  async loadProjects(searchTerms: string | undefined) {
    this.areProjectsLoaded = false;
    const jsonData = {
      id: this.currentUser._id,
      get_details: true,
    };
    this.projects = [];
    this.loadAllProjects = await this.apiService.GetProjects(
      '1',
      searchTerms,
      jsonData,
    );
    this.projects = this.loadAllProjects;
    this.selectOwner = this.loadAllProjects;
    this.projectid_unique = this.getUniqueOwners();
    localStorage.setItem('projects_values', JSON.stringify(this.projects));
    this.projects.forEach((project) => {
      project.last_modified_at = Utils.formatDateTime(project.last_modified_at);
    });
    this.sortProjectsByLastModified();
    this.areProjectsLoaded = true;
  }

  getUniqueOwners() {
    const uniqueOwners: { [key: string]: string } = {};
    this.projects.forEach((project) => {
      uniqueOwners[project.project_owner_id] = project.project_owner_name;
    });
    return Object.keys(uniqueOwners).map((ownerId) => ({
      project_owner_id: ownerId,
      project_owner_name: uniqueOwners[ownerId],
    }));
  }

  isProjectAdministrator(): boolean {
    if (this.projects && this.projects.length > 0) {
      return this.projects.every(
        (project) =>
          project.role_name === 'PROJECT ADMINISTRATOR' ||
          project.role_name === 'Not Applicable',
      );
    }
    return false;
  }

  onShowTileView() {
    document!.getElementById('tile-button')!.style.backgroundColor = '#F2F5F5';
    document!.getElementById('list-button')!.style.backgroundColor = 'white';
    this.showingListView = false;
  }

  onShowListView() {
    document!.getElementById('tile-button')!.style.backgroundColor = 'white';
    document!.getElementById('list-button')!.style.backgroundColor = '#F2F5F5';
    this.showingListView = true;
  }

  highlightButton(clickedButtonId: any) {
    // Highlight the clicked buttonf
    document!.getElementById(clickedButtonId)!.style.backgroundColor =
      '#F2F5F5';
  }

  viewProject() {}

  updateProject(project: Project): void {
    const dialogRef = this.dialog.open(CreateNewProjectComponent, {
      width: '560px',
      disableClose: true,
      data: { project, update: true }, // Pass the project data to the dialog
    });
    dialogRef.componentInstance.closePanelClicked.subscribe(() => {
      dialogRef.close(); // Close the dialog when closePanelClicked is emitted
      this.onRefreshView();
    });
    dialogRef.afterClosed().subscribe((result) => {
      // Handle the result if needed
    });
  }

  async DeleteProject(project: Project): Promise<void> {
    const jsonData = {
      id: this.currentUser._id,
      get_details: true,
    };
    try {
      const projectId: string = project.project_id;
      await this.apiService.DeleteProject('1', projectId, jsonData);
      this.projects = this.projects.filter((p) => p._id !== projectId);
      this.toaster.success('Project Deleted Successfully', '', {
        positionClass: 'custom-toast-position',
      });
      this.dialogRef.close();
    } catch (error) {
      console.error('Failed to delete project', error);
      this.toaster.error('Error Deleting Project', '', {
        positionClass: 'custom-toast-position',
      });
      throw error;
    }
    this.onRefreshView();
  }

  viewWorkflowsForProject(projectId: string) {
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([`sites/${siteId}/projects/${projectId}`]);
  }

  onToggleSort() {
    this.descending = !this.descending;
    this.sortProjectsByLastModified();
  }

  sortProjectsByLastModified(): void {
    this.projects.sort((a, b) => {
      const dateA = new Date(a.last_accessed_at).getTime();
      const dateB = new Date(b.last_accessed_at).getTime();
      return this.descending ? dateB - dateA : dateA - dateB;
    });
    this.projectsList = new MatTableDataSource<Project>(this.projects);
    this.setDatasetTableData();
  }

  onProjectRowSingleClick(project: Project): void {
    if (project && project.project_id) {
      this.selectedProjectRow = project;
      this.configService.SelectedProjectId = project._id!;
      this.configService.SelectedRoleId = project.role_id;
      if (project.role_id == 'Not Applicable') {
      } else {
        this.apiService
          .getFeaturesMappingProject(project.role_id)
          .then((features) => {
            if (features) {
              this.getFeaturesList = features;
              if (
                this.getFeaturesList !== undefined &&
                this.getFeaturesList.role_info! == undefined
              ) {
                localStorage.setItem(
                  'rolesfeatures',
                  JSON.stringify(this.getFeaturesList.role_info.features),
                );

                localStorage.setItem(
                  'rolesName',
                  this.getFeaturesList.role_info,
                );
              }
            } else {
              // Remove rolesfeatures from localStorage if features are not available
              localStorage.removeItem('rolesfeatures');
            }
          })
          .catch((error) => {
            console.error('Error fetching features:', error);
            // Remove rolesfeatures from localStorage in case of error
            localStorage.removeItem('rolesfeatures');
          });
      }
      this.workflowSelectedEvent.emit(project.project_id);
      this.viewWorkflowsForProject(project.project_id);
      this.apiService.updateProjectAccessedDate('1', project.project_id);
    }
  }

  projectOwner(event: any) {
    this.filteredResults = this.selectOwner.filter((session: any) => {
      if (session.project_owner_id == event.project_owner_id) {
        return session;
      }
    });
    this.projectsList.filteredData = this.filteredResults;
    this.selectedValue = true;
  }

  onViewProject(project: Project): void {
    this.configService.SelectedProjectId = project._id!;
    this.configService.SelectedRoleId = project.role_id;
    this.workflowSelectedEvent.emit(project.project_id);
    if (project.role_id == 'Not Applicable') {
    } else {
      this.apiService
        .getFeaturesMappingProject(project.role_id)
        .then((features) => {
          if (features) {
            this.getFeaturesList = features;
            localStorage.setItem(
              'rolesfeatures',
              JSON.stringify(this.getFeaturesList.role_info.features),
            );
          } else {
            // Remove rolesfeatures from localStorage if features are not available
            localStorage.removeItem('rolesfeatures');
          }
        })
        .catch((error) => {
          console.error('Error fetching features:', error);
          // Remove rolesfeatures from localStorage in case of error
          localStorage.removeItem('rolesfeatures');
        });
    }
    this.viewWorkflowsForProject(project.project_id!);
  }

  getContextMenuWidth(): number {
    const contextMenu = this.el.nativeElement.querySelector('.context-menu');
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

  contextMenuTargetId: string | undefined = undefined;

  toggleUserContextMenu(event: MouseEvent, project: Project) {
    this.contextMenuTargetId = project.project_id;
    this.showUserContextMenu = !this.showUserContextMenu;
    this.selectedProjectRow = project;
    this.menuPosition.x = event.clientX - this.getContextMenuWidth() + 165; // Adjusted the x position
    this.menuPosition.y = event.clientY;
    this.menuPosition.y += 10;
    event.stopPropagation();
  }

  isProjectRowSelected(row: any): boolean {
    return this.selectedProjectRow === row;
  }

  toggleSelection(dataset: any) {
    let favoriteStatus = false;
    if (!dataset.favourited_by.includes(this.currentUser._id)) {
      favoriteStatus = true;
      dataset.favourited_by[0] = this.currentUser._id;
    } else {
      favoriteStatus = false;
      dataset.favourited_by = [];
    }
    let siteId = dataset.site_id;
    let projectId = dataset._id;
    let favorite = favoriteStatus;
    this.apiService.toggleFavourite(siteId, projectId, favorite).subscribe(
      (res: HttpResponse<any>) => {
        if (res && res.status === 200 && res.body && res.body.success) {
          this.setDatasetTableData();
        } else {
          console.error(
            'Failed to update favorite status or unexpected response:',
            res,
          );
        }
      },
      (error) => {
        console.error('HTTP request error:', error);
      },
    );
  }

  checkFavStatus(dataset: any): boolean {
    const currentUserID = this.currentUser._id;
    if (dataset.favourited_by) {
      const favoritedArr = dataset.favourited_by;
      return favoritedArr.includes(currentUserID);
    }
    return false;
  }

  checkFavPresent(dataset: any): boolean {
    return dataset.hasOwnProperty('favourited_by');
  }

  setDatasetTableData() {
    this.unfavoriteDatsets = [];
    this.favoriteDatasets = [];

    // This is not supported in the BE.
    //Allowing favourites for displaying the tabular data
    for (let index = 0; index < this.projects.length; index++) {
      let status = false;
      if (
        this.projects[index].favourited_by &&
        this.projects[index].favourited_by.includes(this.currentUser._id)
      ) {
        status = true;
      }
      if (status == true) {
        this.favoriteDatasets.push(this.projects[index]);
      } else {
        this.unfavoriteDatsets.push(this.projects[index]);
      }
    }
    let tableData = [...this.favoriteDatasets, ...this.unfavoriteDatsets];
    this.projectsList = new MatTableDataSource<Project>([]);
    this.projectsList = new MatTableDataSource<Project>(tableData);
  }

  setM2DatasetTableData() {
    this.unfavoriteDatsets = [];
    this.favoriteDatasets = [];

    // This is not supported in the BE.
    //Allowing favourites for displaying the tabular data
    for (let index = 0; index < this.M2projects.length; index++) {
      let status = false;
      if (this.M2projects[index].favourited_by.includes(this.currentUser._id)) {
        status = true;
      }
      if (status == true) {
        this.favoriteDatasets.push(this.M2projects[index]);
      } else {
        this.unfavoriteDatsets.push(this.M2projects[index]);
      }
    }
    let tableData = [...this.favoriteDatasets, ...this.unfavoriteDatsets];
    this.M2projectsList = new MatTableDataSource<Project>([]);
    this.M2projectsList = new MatTableDataSource<Project>(tableData);
  }

  navigate_url(project: any) {
    const projectId = project.project_id;
    const siteId = this.configService.SelectedSiteId;
    const access_token = localStorage.getItem('access_token');
    const url = 'https://hexaind2manualtest01.corp.databrick.tech/login';

    const headers = new HttpHeaders({
      accessToken: `${access_token}`,
      'Custom-Header': 'value',
      Project_id: projectId.toString(),
      'Site-Id': siteId.toString(),
    });
    this.apiService.redirectToUrlWithHeaders(url, headers);
  }

  lastAccessedDate(date: string) {
    return Utils.formatDateTime(date);
  }

  openConfirmationDialog(): void {
    this.dialogRef = this.dialog.open(this.confirmationDialogTemplate);
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  async sortData(sort: Sort) {
    this.projects.sort((a: any, b: any) => {
      let aValue: any = '';
      let bValue: any = '';
      if (sort.active === 'name') {
        aValue = a.project_name;
        bValue = b.project_name;
      } else if (sort.active === 'owner') {
        aValue = a.project_owner_name;
        bValue = b.project_owner_name;
      } else if (sort.active === 'description') {
        aValue = a.description;
        bValue = b.description;
      } else if (sort.active === 'created_at') {
        aValue = new Date(a.created_at);
        bValue = new Date(b.created_at);
      } else if (sort.active === 'lastModified') {
        aValue = new Date(a.last_accessed_at);
        bValue = new Date(b.last_accessed_at);
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
    this.projectsList = new MatTableDataSource<Project>(this.projects);
    this.setDatasetTableData();
  }
}
