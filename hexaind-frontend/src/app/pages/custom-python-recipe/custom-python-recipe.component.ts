import { Component, ViewChild, TemplateRef } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import { ConfigService } from 'src/app/services/config.service';
import { Router } from '@angular/router';
import { MatMenuTrigger } from '@angular/material/menu';
import { ToastrService } from 'ngx-toastr';
import { Subject, Subscription } from 'rxjs';
import { CustomPythonWidgetRecipe } from 'src/app/models/api-models';
import { MatDialog, MatDialogConfig, MatDialogRef } from '@angular/material/dialog';
import { FormBuilder, FormGroup } from '@angular/forms';
import { Sort } from '@angular/material/sort';

@Component({
  selector: 'app-custom-python-recipe',
  templateUrl: './custom-python-recipe.component.html',
  styleUrls: ['./custom-python-recipe.component.less'],
})
export class CustomPythonRecipeComponent {
  @ViewChild(MatMenuTrigger)
  public menuItem: any;
  public deleteConfirmation: boolean = false;

  menuTrigger!: MatMenuTrigger;
  showMainHeader: any;
  customWidgets: CustomPythonWidgetRecipe[] = [];
  numberOfColumns: number = 0;
  searchText: string = '';
  descending: boolean = true;
  selectedCustomWidgetRow: any = null;
  filteredResults: any[] = [];
  selectOwner: any[] = [];
  displayedColumns: string[] = [
    'name',
    'owner',
    'description',
    'created_at',
    'lastModified',
    'status',
    'more_vert',
  ];
  allOwners: any = "All Owners";
  custom_owners: any;

  private searchTerms = new Subject<string>();
  private projectSubscription: Subscription | undefined = undefined
  isCustomPythonRecipeLoaded = false;
  @ViewChild('popupTemplate') popupTemplate: TemplateRef<any> | undefined
  dialogRef : MatDialogRef<any> | undefined; 
  isDeleteEnabled: boolean = false
  workFlowsInWhichWidgetIsUsed: Set<any> = new Set();
  currentWidgetRecipeId: any;
  currentWidgetRecipeName: string = '';
  singleInputForm!: FormGroup;
  @ViewChild('cloneForm') cloneForm: TemplateRef<any> | undefined
  customWidgetNamesList: any;
  customWidgetClonedName: any;


  constructor(
    private apiService: ApiService,
    private configService: ConfigService,
    private router: Router,
    public toaster: ToastrService,
    public dialog: MatDialog,
    private fb: FormBuilder
  ) {
    this.singleInputForm = this.fb.group({
      inputField: ['']
    });
  }

  ngAfterViewInit() {
    this.loadCustomWidgets();
  }

  ngOnInit() {
    this.numberOfColumns = this.getNumberOfColumns();
    this.projectSubscription =
      this.configService.selectedProjectIdObservable.subscribe((projectId: any) => {
        if (projectId) {
          this.loadCustomWidgets();
        }
      });
  }

  ngOnDestroy() {
    this.projectSubscription?.unsubscribe()
  }



  onSearchTextChange(event: Event) {
    let searchTerm = (event.target as HTMLInputElement).value.trim();
    let result = [];
    if (this.filteredResults.length === 0) {
      this.filteredResults = this.selectOwner;
    }
    if (searchTerm) {
      result = this.filteredResults.filter((session: any) => {
        searchTerm = searchTerm.toLowerCase();
          return (session.name.toLowerCase().includes(searchTerm) ||  
          session.description.toLowerCase().includes(searchTerm) || 
          session.created_by_name.toLowerCase().includes(searchTerm));
        
      });
      this.customWidgets = result;
    } else {
      if (this.filteredResults.length > 0) {
        this.customWidgets = this.filteredResults;
      } else {
        this.customWidgets = this.selectOwner;
      }
    }
    this.searchTerms.next(searchTerm);
  }

  async projectOwner(event: any) {
    this.filteredResults = this.selectOwner.filter((session: any) => {
      return session.created_by_name === event.owner_name;
    });

    this.customWidgets = this.filteredResults;
  }

  async allOwner() {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    this.customWidgets = await this.apiService.GetCustomPythonWidgetRecipes(
      selectedProjectId,
      this.configService.SelectedSiteId,
    );
    this.selectOwner = this.customWidgets;
  }

  getNumberOfColumns(): number {
    let screenWidth = window.innerWidth;
    let tileCount = Math.floor(screenWidth / 220);
    return tileCount;
  }

  onToggleSort() {
    this.descending = !this.descending;
    this.sortCustomWidgetsByLastModified();
  }

  onCustomWidgetRowSingleClick(row: any): void {
    this.selectedCustomWidgetRow = row;
  }

  onRowClicked(customWidget: CustomPythonWidgetRecipe) {
    this.openCustomWidget(customWidget, 'VIEW')
  }

  isCustomWidgetRowSelected(row: CustomPythonWidgetRecipe): boolean {
    return this.selectedCustomWidgetRow === row;
  }

  sortCustomWidgetsByLastModified(): void {
    this.customWidgets.sort((a, b) => {
      // Convert dates to timestamps. If the date is undefined, use 0 as a fallback.
      const dateA = new Date(a.last_modified_at).getTime();
      const dateB = new Date(b.last_modified_at).getTime();
      // Now that we have numbers, subtraction is possible.
      return this.descending ? dateB - dateA : dateA - dateB;
    });
    this.customWidgets = [...this.customWidgets];
  }

  createNewCustomWidget() {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate([
      `sites/${siteId}/projects/${selectedProjectId}/custom-code-builder/0/CREATE`,
    ]);
  }

  onDeleteCustomWidget(customWidget: CustomPythonWidgetRecipe) { }

  openCustomWidget(customWidget: CustomPythonWidgetRecipe, viewMode: any) {
			let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
			if (!selectedProjectId) {
					return;
			}
			const siteId = this.configService.SelectedSiteId;
			console.log(this.menuItem);
			
			this.router.navigate([
					`sites/${siteId}/projects/${selectedProjectId}/custom-code-builder/${this.menuItem._id}/${viewMode}`, {
						state: {customWidgetData: this.menuItem}
					}
			]);
  }

  onEditCustomWidget(customWidget: CustomPythonWidgetRecipe) { }

  onRefreshView() {
    this.loadCustomWidgets();
    this.filteredResults.length = 0;
    this.searchText = '';
  }

  async loadCustomWidgets() {
    this.isCustomPythonRecipeLoaded = false;
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    this.customWidgets = await this.apiService.GetCustomPythonWidgetRecipes(
      selectedProjectId,
      this.configService.SelectedSiteId,
    );
    this.selectOwner = this.customWidgets;
    this.custom_owners = this.getUniqueCustomOwners(this.customWidgets);
    this.sortCustomWidgetsByLastModified();
    this.isCustomPythonRecipeLoaded = true;
    this.customWidgetNamesList = []
    this.customWidgets.forEach((customWidget)=>{
      this.customWidgetNamesList.push(customWidget.name)
    })
  }

  getUniqueCustomOwners(customWidgets: any[]): { owner_id: string; owner_name: string }[] {
    const uniqueOwnersMap: { [ownerId: string]: string } = {};

    customWidgets.forEach(widget => {
      uniqueOwnersMap[widget.created_by] = widget.created_by_name;
    });

    return Object.keys(uniqueOwnersMap).map(ownerId => ({
      owner_id: ownerId,
      owner_name: uniqueOwnersMap[ownerId]
    }));
  }




  viewCustomWidget(row: any) {
    let selectedProjectId: string | undefined = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const siteId = this.configService.SelectedSiteId;
    this.router.navigate(
      [`sites/${siteId}/projects/${selectedProjectId}/custom-code-builder`],
      { state: { data: row } },
    );
  }

  async sortData(sort: Sort) {
    const data = this.customWidgets.slice();
    data.sort((a: any, b: any) => {
      let aValue: any = '';
      let bValue: any = '';
      if (sort.active === 'name') {
        aValue = a.name;
        bValue = b.name;
      } else if (sort.active === 'owner') {
        aValue = a.created_by_name;
        bValue = b.created_by_name;
      } else if (sort.active === 'description') {
        aValue = a.description;
        bValue = b.description;
      } else if (sort.active === 'created_at') {
        aValue = new Date(a.created_at);
        bValue = new Date(b.created_at);
      } else if (sort.active === 'lastModified') {
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
    this.customWidgets = data;
  }

  async openValidationDialog(customPythonWidgetRecipeId:any, recipeName:string): Promise<any> {
    if(!this.popupTemplate) return
    await this.fetchAndSetWidgetUsagesInWorkflow(customPythonWidgetRecipeId)
    this.currentWidgetRecipeId = customPythonWidgetRecipeId
    this.currentWidgetRecipeName = recipeName
    if(this.workFlowsInWhichWidgetIsUsed.size == 0) {
      this.proceedToDelete(true)
      return
    }
    const dialogConfig = new MatDialogConfig()
    dialogConfig.panelClass = 'custom-dialog-container';
    dialogConfig.backdropClass = 'custom-dialog-backdrop';
    dialogConfig.autoFocus = true;
    this.dialogRef = this.dialog.open(this.popupTemplate, dialogConfig)
  }

  
  async fetchAndSetWidgetUsagesInWorkflow(customPythonWidgetRecipeId : any) {
    let apiResponse = await this.apiService.getworkflowsInWhichWidgetIsUsed('1', this.configService.SelectedProjectId , customPythonWidgetRecipeId)
    this.workFlowsInWhichWidgetIsUsed = new Set()
    apiResponse.forEach((widget:any) => {
      widget.widget_usage_response.forEach((workflow:any) => {
        this.workFlowsInWhichWidgetIsUsed?.add(workflow.name)
      })
    })
  }


  async proceedToDelete(isDelete:boolean) {
    if(!isDelete) {
      this.dialogRef?.close()
      return
    }
    try {
      await this.apiService.deleteCustomWidgetRecipe('1', this.configService.SelectedProjectId , this.currentWidgetRecipeId)
      this.toaster.success('Custom widget deleted successfully', '', {
        positionClass: 'custom-toast-position'
      });
      this.currentWidgetRecipeName = '';
    }
    catch(error: any) {
      this.toaster.error("Error" + error.error?.detail, '',{
        positionClass: 'custom-toast-position' 
      });
    }
    this.dialogRef?.close()
    this.loadCustomWidgets();
  }

  async openCloneWidgetForm(customPythonWidgetRecipe:any): Promise<any> {
    if(!this.cloneForm) return
    this.customWidgetClonedName = customPythonWidgetRecipe.name + "_clone"
    this.currentWidgetRecipeId = customPythonWidgetRecipe._id
    const dialogConfig = new MatDialogConfig()
    dialogConfig.panelClass = 'custom-dialog-container';
    dialogConfig.backdropClass = 'custom-dialog-backdrop';
    dialogConfig.autoFocus = true;
    this.dialogRef = this.dialog.open(this.cloneForm, dialogConfig)
  }
    
  async procedToCloneWidget() {
    try {
      await this.apiService.cloneCustomWidgetRecipe('1', this.configService.SelectedProjectId , this.currentWidgetRecipeId, this.customWidgetClonedName )
      this.toaster.success('Custom widget ' + this.customWidgetClonedName + ' is cloned successfully', '', {
        positionClass: 'custom-toast-position'
      });
      this.dialogRef?.close()
      this.loadCustomWidgets();
    }
    catch(error: any) {
        this.toaster.error("Error" + error.error?.detail, '',{
          positionClass: 'custom-toast-position' 
        });
    }
  }

  getCssClassForWidgetStatus(element: any) {
    return element.recipe_status === 'PUBLISHED' ? 'published' : 'draft'
  }
 
}
