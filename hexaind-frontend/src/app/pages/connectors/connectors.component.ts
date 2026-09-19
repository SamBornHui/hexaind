import { Component, ChangeDetectorRef } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { NavService } from 'src/app/controls/left-nav/nav.service';
import { ElementRef, Renderer2, HostListener } from '@angular/core';
import { ConnectorsService } from './services/connectors.service';
import { ApiService } from 'src/app/services/api.service';
import { Subject, Subscription } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { MatDialog } from '@angular/material/dialog';
import { ConnectorDialogComponent } from '../../dialogs/connector-dialog/connector-dialog.component';
import { Utils } from 'src/app/utils';
import { ConnectorsUpdateComponent } from 'src/app/dialogs/connectors-update/connectors-update.component';
import { ToastrService } from 'ngx-toastr';
import { ConfigService } from '../workflow-designer/workflow-canvas.service';
import { Sort } from '@angular/material/sort';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-connectors',
  templateUrl: './connectors.component.html',
  styleUrls: ['./connectors.component.less'],
})
export class ConnectorsComponent {
  private searchTerms = new Subject<string>();
  public deleteConfirmation: boolean = false;

  searchText: string = '';
  selectedWorkflowRow: any = null;
  showUserContextMenu = false;
  displayedColumns: string[] = [
    'name',
    'type',
    'created_by',
    'created_at',
    'last_modified_at',
    'more_vert',
  ];
  dataSource: any;
  selectedType: string = '';
  selectedUploader: string = '';
  selectedSort: string = 'Most recent';
  numberOfColumns: number = 1;
  screenWidth: number = 0;
  tileData: any[] = [];
  searchResults: any[] = [];
  selectOwner: any[] = [];
  filteredResults: any[] = [];
  isConnectorsLoaded = false;
  projectId: string = '';
  fullUrl: string = '';
  isLoading = false;

  private boundResizeFunction: () => void;
  assets: any = {};
  connectors_owners: any;
  private projectSubscription: Subscription | undefined


  constructor(
    private cdRef: ChangeDetectorRef,
    public navService: NavService,
    private renderer: Renderer2,
    private el: ElementRef,
    private connectorsService: ConnectorsService,
    private dialog: MatDialog,
    public toaster: ToastrService,
    private configService: ConfigService,
    private apiService: ApiService,
    private route: ActivatedRoute,
    private router: Router
  ) {

    const rolesfeaturesString = localStorage.getItem('rolesfeatures');
    if (rolesfeaturesString !== null) {
      this.assets = JSON.parse(rolesfeaturesString).assets.connectors;
    } else {
      this.assets = "server_admin";
      console.error('No rolesfeatures found in localStorage.');
    }

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
    this.getConnectors();
    this.numberOfColumns = this.getNumberOfColumns();
    this.projectSubscription = this.configService.selectedProjectIdObservable.subscribe((projectId: any) => {
      if (projectId) {
        this.getConnectors();
      }
    });
  }

  ngAfterViewInit() {
    this.screenWidth = window.innerWidth;

    setTimeout(() => {
      this.calculateColumns();
    }, 250);
  }

  ngOnDestroy() {
    // Remove the event listener when the component is destroyed
    window.removeEventListener('resize', this.boundResizeFunction);
    this.projectSubscription?.unsubscribe
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

  getConnectors() {
    this.isConnectorsLoaded = false;
    this.connectorsService.GetConnectors().subscribe(
      (res) => {
        var connectors: any[] = res.connectors;
        this.connectors_owners = this.getConnectorsOwners(connectors);
        connectors.sort((a: { last_modified_at: number; }, b: { last_modified_at: number; }) => new Date(b.last_modified_at).getTime() - new Date(a.last_modified_at).getTime());
        this.dataSource = new MatTableDataSource(connectors);
        this.tileData = this.dataSource.filteredData;
        this.selectOwner = [...this.tileData];
        this.searchResults = [...this.tileData];
        this.isConnectorsLoaded = true;
      },
      (error) => {
        console.error('Error fetching connectors', error);
        this.isConnectorsLoaded = true; // Set to true even if there is an error
      }
    );
  }


  updateConnectors(connectors: any) {
    const dialogRef = this.dialog.open(ConnectorsUpdateComponent, {
      width: '560px',
      disableClose: true,
      data: {
        connectors: connectors,
      },
    });
    dialogRef.afterClosed().subscribe(() => {
      this.getConnectors();
      this.numberOfColumns = this.getNumberOfColumns();
      this.projectSubscription = this.configService.selectedProjectIdObservable.subscribe((projectId: any) => {
        if (projectId) {
          this.getConnectors();
        }
      });
      dialogRef.close();
    });
  }

  deleteConnectors(connectors: any) {
    this.connectorsService.DeleteDataset(connectors).subscribe((res: any) => {
      if (res.success) {
        this.toaster.success('Deleted successfully', '', {
          positionClass: 'custom-toast-position'
        });
      } else {
        this.toaster.error(res.message, '', {
          positionClass: 'custom-toast-position'
        });
      }
      this.onRefreshView();
    });
  }

  onRefreshView() {
    this.getConnectors();
    this.filteredResults.length = 0;
  }

  onToggleSort() {
  }

  getConnectorsOwners(sessions: any[]): { owner_id: string; owner_name: string }[] {
    const uniqueOwnersMap: { [ownerId: string]: string } = {};

    sessions.forEach(session => {
      uniqueOwnersMap[session.owner_id] = session.owner_name;
    });

    return Object.keys(uniqueOwnersMap).map(ownerId => ({
      owner_id: ownerId,
      owner_name: uniqueOwnersMap[ownerId]
    }));
  }

  getNumberOfColumns(): number {
    let screenWidth = window.innerWidth;
    let tileCount = Math.floor(screenWidth / 220);
    return tileCount;
  }

  /*TextChange() {
    const lowerCaseQuery = this.searchText.toLowerCase();

    if (lowerCaseQuery.trim() === '') {
      this.searchResults = this.tileData;
      return;
    }

    this.searchResults = this.tileData.filter((connector: any) => {
      const searchableFields = ['name', 'type', 'uploader'];

      return searchableFields.some((field) => {
        return (
          connector &&
          connector[field] &&
          connector[field].toLowerCase().includes(lowerCaseQuery)
        );
      });
    });
  }
  */
  onSearchTextChange(event: any) {
    let searchTerm = event.trim();
    let result = [];
    if (this.filteredResults.length === 0) {
      this.filteredResults = this.selectOwner;
    }
    if (searchTerm) {
      result = this.filteredResults.filter((session: any) => {

        const projectName = session.name.toLowerCase();
        const connectorCreatedName = session.owner_name.toLowerCase();
        searchTerm = searchTerm.toLowerCase();
        if (projectName.includes(searchTerm) || connectorCreatedName.includes(searchTerm)) {
          return (projectName.includes(searchTerm) || connectorCreatedName.includes(searchTerm));
        } else {
          return false;
        }
      });
      this.searchResults = result;
    }
    else {
      if (this.filteredResults.length > 0) {
        this.searchResults = this.filteredResults;
      } else {
        this.searchResults = this.selectOwner; 
      }
    }
  }

  projectOwner(event: any) {
    this.filteredResults = this.selectOwner.filter((session: any) => {
      return session.owner_name === event.owner_name;
    });

    this.searchResults = this.filteredResults;
  }

  isWorkflowRowSelected(row: any): boolean {
    return this.selectedWorkflowRow === row;
  }

  openConnectorsDialog(): void {
    const dialogRef = this.dialog.open(ConnectorDialogComponent, {
      width: '560px',
      height: '96%',
    });
  
    dialogRef.afterClosed().subscribe((result) => {
      if (result?.success) {
        this.isLoading = true; // Show spinner
        Promise.resolve(this.getConnectors()).then(() => {
          this.isLoading = false; // Hide spinner after completion
        }).catch(() => {
          this.isLoading = false; // Ensure spinner hides even on error
        });
      }
    });
  }
  

  async sortData(sort: Sort) {
    const data = this.searchResults.slice();
    data.sort((a: any, b: any) => {
      let aValue: any = '';
      let bValue: any = '';
      if (sort.active === 'name') {
        aValue = a.name;
        bValue = b.name;
      } else if (sort.active === 'created_by') {
        aValue = a.owner_name;
        bValue = b.owner_name;
      } else if (sort.active === 'type') {
        aValue = a.type;
        bValue = b.type;
      } else if (sort.active === 'created_at') {
        aValue = new Date(a.created_at);
        bValue = new Date(b.created_at);
      } else if (sort.active === 'last_modified_at') {
        aValue = new Date(a.last_modified_at);
        bValue = new Date(b.last_modified_at);
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
    this.searchResults = data;
  }


  supersetConnect() {
    console.log("Testing connections!");
    this.fullUrl = this.router.url;
    console.log("Full URL:", this.fullUrl);

    // Extract the Project ID from the URL
    const urlSegments = this.fullUrl.split('/');
    const projectIndex = urlSegments.indexOf('projects');
    
    if (projectIndex !== -1 && projectIndex + 1 < urlSegments.length) {
      this.projectId = urlSegments[projectIndex + 1];
    }

    console.log("Extracted Project ID:", this.projectId);
    try {
      // Make the API call to fetch data with token in headers
      this.apiService.fetchDataWithToken().subscribe(
        (response: any) => {
          // Assuming the response contains a URL to open in a new tab
          const url = response?.url;
          console.log(url,);
          if (url) {
            const token = this.apiService.getAccessToken();  // You can get the token like this if you have the getAccessToken method

            // Append the token to the URL as a query parameter
            const urlWithToken = `${url}?token=${token}&projectId=${this.projectId}`;
      
            // Open the URL with the token in a new tab
            window.open(urlWithToken, '_blank');
          } else {
            const errorMessage = 'No URL returned from the server.';
            this.toaster.error(
              errorMessage,
              'ERROR',
              {
                positionClass: 'custom-toast-position',
              }
            );
          }
        },
        (error: any) => {
          const errorMessage = 'Error while connecting to Superset. Please try again later';
          this.toaster.error(
            errorMessage,
            'ERROR',
            {
              positionClass: 'custom-toast-position',
            }
          );
        }
      );
    } catch (error: any) {
      const errorMessage = 'Error while connecting to Superset. Please try again later';
      this.toaster.error(
        errorMessage,
        'ERROR',
        {
          positionClass: 'custom-toast-position',
        }
      );
    }
  }
  
}