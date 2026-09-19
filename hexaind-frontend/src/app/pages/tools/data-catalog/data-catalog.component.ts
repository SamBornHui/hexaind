import { Component,TemplateRef, ViewChild } from '@angular/core';
import { ConfigService } from 'src/app/services/config.service';
import { Router } from '@angular/router';
import { environment } from 'src/environments/environment';
import { ToastrService } from 'ngx-toastr';
import { CreateSessionComponent } from '../../create-session/create-session.component';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { DataCatalogService } from './data-catalog.service';

@Component({
  selector: 'app-data-catalog',
  templateUrl: './data-catalog.component.html',
  styleUrls: ['./data-catalog.component.less'],
})
export class DataCatalogComponent {
  showMainHeader: boolean = false;
  searchText: string = '';
  role_id: any;
  role_id_sso: any;
  dialogRef!: MatDialogRef<any>;
  sessionsList: any;
  toggleHeaderButton: string = 'expand_more';
  displayedColumns: string[] = [
    'name',
    'description',
    'created_at',
    'owner_name',
    'more_vert'
    // 'size',
    // 'uploader',
    // 'last_modified',
    // 'actions',
  ];
  deleteConfirmation: boolean = false;
  @ViewChild('confirmationDialogTemplate') confirmationDialogTemplate!: TemplateRef<any>;
  sessionName: any = '';
  
  constructor(
    private configService: ConfigService,
    private router: Router,
    public toaster: ToastrService,
    private dialog: MatDialog,
    private dataCatService: DataCatalogService,
  ) {}

  ngOnInit() {
    this.role_id = localStorage.getItem('role_id');
    this.role_id_sso = localStorage.getItem('role_id_sso');
    this.getAllSessions();
  }

  async getAllSessions() {
    let projectId = this.configService.SelectedProjectId;
    let page_number = 1;
    let page_limit = 100;
    try {
      const allSessions = await this.dataCatService.getAllSessions(
        projectId,
        page_limit,
        page_number,
      );
      if (allSessions) {
        console.log(allSessions);
        this.sessionsList = allSessions?.datacatalog_sessions;
      }
    } catch (error) {
      console.log('Error:', error);
    }
  }
  navigate(pageName: string) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const projectId = selectedProjectId;
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([`sites/${siteId}/projects/${projectId}/${pageName}`]);
  }

  createNewSession(): void {
    const dialogRef = this.dialog.open(CreateSessionComponent, {
      width: '560px',
      disableClose: true,
      data: { update: false },
    });
    dialogRef.afterClosed().subscribe((result) => {
      this.getAllSessions();
      this.onRefreshView();
    });
  }

  onRefreshView() {
    this.searchText = '';
    this.showMainHeader = false;
  }

  onCloseCreateNewSession() {}

  onSessionClick(event: any) {
    if (event) {
      let selectedProjectId: string | undefined =
        this.configService.SelectedProjectId;
      if (!selectedProjectId) {
        return;
      }
      const siteId = this.configService.SelectedSiteId;
      let data = {
        name : event.name,
        job_id : event.data_pull_job_id
      }
      if(event.data_pull_job_id) {
        this.dataCatService.setData(data);
        this.router.navigate([
          `sites/${siteId}/projects/${selectedProjectId}/UC7`,
          { queryParams: { data: data } },
        ]);
      }
      else
      {
        this.toaster.error('No Data Pull Job ID Found');
      }
    }
  }

  toggleMainHeader() {
    this.showMainHeader = !this.showMainHeader;
    this.toggleHeaderButton = this.showMainHeader
      ? 'expand_less'
      : 'expand_more';
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  deleteSession(rowData:any){
    try{
      this.dataCatService.deleteSession(rowData._id).subscribe((res)=>{
        if(res.status === 204){
          this.getAllSessions();
          this.onRefreshView();
          this.toaster.success('Session deleted successfully');
          this.dialogRef.close();
        }
        else
        {
          this.toaster.error('Failed to delete session');
        }
      })
    }
    catch(error: any){
      this.toaster.error('Error:', error);
    }
  }

  openConfirmationDialog(): void {
    this.dialogRef = this.dialog.open(this.confirmationDialogTemplate);
  }
}
