import {
  ChangeDetectorRef,
  Component,
  ElementRef,
  Renderer2,
  ViewChild,
  AfterViewInit,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { Subject, Subscription, debounceTime } from 'rxjs';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { NavService } from 'src/app/controls/left-nav/nav.service';
import { ConnectorsService } from '../connectors/services/connectors.service';
import { CreateJupyterServer } from 'src/app/dialogs/create-jupyter-server/create-jupyter-server.component';
import { MatDialog } from '@angular/material/dialog';
import { NotificationComponent } from 'src/app/controls/notification/notification.component';
import { Utils } from 'src/app/utils';
import { ApiPollingService } from 'src/app/services/api-polling.service';
import { takeWhile } from 'rxjs/operators';
import { ConfigService } from '../workflow-designer/workflow-canvas.service';
import { ApiService } from "src/app/services/api.service";
import { ToastrService } from 'ngx-toastr';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { CreateJupyterNotebookComponent } from 'src/app/dialogs/create-jupyter-notebook/create-jupyter-notebook.component';

@Component({
  selector: 'app-jupyter-notebooks',
  templateUrl: './jupyter-notebooks.component.html',
  styleUrls: ['./jupyter-notebooks.component.less'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({ height: '0px', minHeight: '0', display: 'none' })),
      state('expanded', style({ height: '*' })),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ],
})
export class JupyterNotebooksComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('notification') notificationComponent!: NotificationComponent;
  @ViewChild(MatSort) sort!: MatSort;

  private searchTerms = new Subject<string>();
  searchText: string = '';
  selectedWorkflowRow: any = null;
  showUserContextMenu = false;
  displayedColumns: string[] = ['expand', 'Name', 'Description', 'URL', 'Status', 'Last Modified', 'menu'];
  selectedType: string = '';
  selectedUploader: string = '';
  selectedSort: string = 'Most recent';
  numberOfColumns: number = 1;
  screenWidth: number = 0;
  tileData: any[] = [];
  assets: any = {};
  status: string | undefined;
  isRunning = false;
  projectId: any;
  private projectSubscription: Subscription | undefined = undefined;

  private boundResizeFunction: () => void;
  isExpanded = (index: number, element: any) => this.expandedElement === element;
  isNotExpanded = (index: number, element: any) => this.expandedElement !== element;
  dataSource: MatTableDataSource<any> = new MatTableDataSource<any>();
  showLoader: boolean | undefined;
  expandedElement: any | null;
  user_id: string | undefined;

  constructor(
    private cdRef: ChangeDetectorRef,
    public navService: NavService,
    private renderer: Renderer2,
    private el: ElementRef,
    private connectorsService: ConnectorsService,
    private dialog: MatDialog,
    private apiPollingService: ApiPollingService,
    private configService: ConfigService,
    private apiService: ApiService,
    public toaster: ToastrService
  ) {
    this.renderer.listen('document', 'click', (event) => {
      if (this.el.nativeElement.contains(event.target)) {
        this.showUserContextMenu = false;
      }
    });

    this.searchTerms.pipe(debounceTime(300)).subscribe((term) => {
      this.dataSource.filter = term.trim().toLowerCase();
    });

    this.boundResizeFunction = this.onResize.bind(this);
    window.addEventListener('resize', this.boundResizeFunction);
  }

  ngOnInit() {
    this.projectId = this.configService.SelectedProjectId;
    this.user_id = JSON.parse(localStorage.getItem('currentUser')!)['_id'];
    this.projectSubscription =
      this.configService.selectedProjectIdObservable.subscribe(
        (projectId: any) => {
          if (projectId) {
            this.getJupyterNotebooks(projectId);
          }
        },
      );
    this.numberOfColumns = this.getNumberOfColumns();
  }

  ngAfterViewInit() {
    this.screenWidth = window.innerWidth;
    this.dataSource.sort = this.sort;

    setTimeout(() => {
      this.calculateColumns();
    }, 250);
  }

  ngOnDestroy() {
    window.removeEventListener('resize', this.boundResizeFunction);
    this.projectSubscription?.unsubscribe();
  }


  onResize(event?: Event) {
    this.calculateColumns();
    this.screenWidth = window.innerWidth;
    this.cdRef.detectChanges();
  }

  private calculateColumns() {
    const parentWidth = document.querySelector('[fxLayout]')!.clientWidth;
    this.numberOfColumns = Utils.CalculateColumns(parentWidth);
  }

  async getJupyterNotebooks(project_id: any) {
    let res = await this.apiService.GetAllServers(project_id, this.user_id || '');
    console.log(res, "response get all servers");
    this.dataSource = new MatTableDataSource(res);
  }

  getNumberOfColumns(): number {
    const screenWidth = window.innerWidth;
    const tileCount = Math.floor(screenWidth / 220);
    return tileCount;
  }

  onSearchTextChange(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.searchTerms.next(filterValue);
  }

  isWorkflowRowSelected(row: any): boolean {
    return this.selectedWorkflowRow === row;
  }

  addJupyterServer(): void {
     this.showLoader = true;
    const dialogRef = this.dialog.open(CreateJupyterServer, {
      width: '560px',
    });
    dialogRef.afterClosed().subscribe((result) => { 
      
          this.apiPollingService
      .pollApi(this.projectId) // Pass projectId here
      .pipe(
        takeWhile((response) => response.status !== 'RUNNING', true) // Check for 'RUNNING'
      )
      .subscribe(
        (response) => {
          this.showLoader = false;
          this.status = response.status;
          this.getJupyterNotebooks(this.projectId); // Call function when status is 'RUNNING'
        },
        (error) => {
          if (error.message === 'Polling complete') {
            this.isRunning = true;
          } else {
            console.error('Polling error:', error);
          }
        }
      );

    });
  }

  async startServer(element: any) {
    this.showLoader = true;
    let res = await this.apiService.StartServer(element.project_id);
    if (res.status == 'RUNNING') {
      this.showLoader = false;
      this.toaster.success('Server Started Succesfully', '', {
        positionClass: 'custom-toast-position'
      });
    }
    this.getJupyterNotebooks(element.project_id);
  }

  async stopServer(element: any) {
    this.showLoader = true;
    let res = await this.apiService.StopServer(element.project_id);
    if (res.status == 'STOPPED') {
      this.showLoader = false;
      this.toaster.success('Server Stopped Succesfully', '', {
        positionClass: 'custom-toast-position'
      });
    }
    this.getJupyterNotebooks(element.project_id);

  }

  async deleteServer(element: any) {
    let res = await this.apiService.DeleteServer(element.project_id);
    this.toaster.success('Server Deleted Succesfully', '', {
      positionClass: 'custom-toast-position'
    });
    this.getJupyterNotebooks(element.project_id);
  }

  async createJNB_folders(element: any) {
    let res = await this.apiService.createJNB_folders(this.configService.SelectedProjectId, this.user_id);
    this.toaster.success('User folder space refreshed successfully', '', {
      positionClass: 'custom-toast-position'
    });
  }

  launchServer(element: any, url: string) { 
    this.createJNB_folders(element);
    window.open(url, '_blank'); 
  }

  toggleExpandButtonClicked(event: any, element: any) {
    if (
      this.expandedElement &&
      this.expandedElement !== element &&
      this.expandedElement.expanded
    ) {
      this.expandedElement.expanded = false;
    }
    if (element.expanded === undefined) {
      element.expanded = true;
    } else {
      element.expanded = !element.expanded;
    }

    if (element.expanded) {
      this.expandedElement = element;
    } else {
      this.expandedElement = undefined;
    }
    event.stopPropagation();
  }

  getColumnName(name: string) {
    if (name === 'menu' || name === 'expand') {
      return '';
    }
    return name;
  }

  addJNBMasterClone(type: string, notebook: any): void {
    const dialogRef = this.dialog.open(CreateJupyterNotebookComponent, {
      width: '560px',
      data: { type: type, notebook: notebook },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result === true) {
        this.getJupyterNotebooks(this.projectId);
      }
    });
  }
  createNotebook(type: string, element: any){
    console.log(type);
    
    const dialogRef = this.dialog.open(CreateJupyterNotebookComponent, {
      width: '560px',
      data: { type: type, notebook: element },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result === true) {
        this.getJupyterNotebooks(this.projectId);
      }
    });
    
  }

}
