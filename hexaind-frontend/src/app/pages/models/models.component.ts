import { Component, ChangeDetectorRef, Input } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { NavService } from 'src/app/controls/left-nav/nav.service';
import { ElementRef, Renderer2, HostListener } from '@angular/core';
import { ModelsService } from './services/models.service';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, map } from 'rxjs/operators';
import { Utils } from 'src/app/utils';
import { ConfigService } from '../workflow-designer/workflow-canvas.service';
import { ToastrService } from 'ngx-toastr';
import { Sort, MatSort } from '@angular/material/sort';
import { BehaviorSubject, combineLatest } from 'rxjs';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { AnyCatcher } from 'rxjs/internal/AnyCatcher';
import { ModelPreviewDialogBoxComponent } from 'src/app/dialogs/model-preview-dialog-box/model-preview-dialog-box.component';
import { MatDialog } from '@angular/material/dialog';
import { EditModelComponent } from 'src/app/dialogs/edit-model/edit-model.component';

interface ModelConfig {
  problem_type: string;
}

interface DeployedStatus {
  status: string;
  port: number;
}

@Component({
  selector: 'app-models',
  templateUrl: './models.component.html',
  styleUrls: ['./models.component.less'],
})
export class ModelsComponent {
  @Input() assetType: any;
  private searchTerms = new Subject<string>();
  public deleteConfirmation: boolean = false;
  public compareModels: boolean = false;
  public previewModel: boolean = false;

  errorMessage: string = 'Please select another model to compare';

  models: [] = [];
  searchText: string = '';
  project_id: string | undefined;
  site_id: string | undefined = '1';
  selectedWorkflowRow: any = null;
  showUserContextMenu = false;
  displayedColumns: string[] = [
    'name',
    'type',
    'problem_type',
    'input',
    'output',
    'created_by',
    'created_at',
    'ml_deployed_status',
    'more_vert',
  ];
  dataSource: any;
  selectedType: string = '';
  selectedUploader: string = '';
  userFilter = new BehaviorSubject<string>('');
  selectedSort: string = 'Most recent';
  numberOfColumns: number = 1;
  screenWidth: number = 0;
  showLoader: boolean = true;
  modelDetails: any = {};
  deleteConfim: boolean = false;
  deletionId: string | null = null;
  selectedModels: any[] = [];
  compareModelsButtons: boolean = false;
  canCompare: boolean = false;
  errorKey: boolean = false;
  type: string = 'comparision';
  spinnerFlag: boolean = false;
  private projectSubscription: Subscription | undefined = undefined;
  loadingStates: { [key: string]: boolean } = {};

  filteredModelsData: any[] = [];
  private boundResizeFunction: () => void;
  assets: any = {};
  actionModel: any = {};
  constructor(
    private cdRef: ChangeDetectorRef,
    public navService: NavService,
    private renderer: Renderer2,
    private el: ElementRef,
    private modelsService: ModelsService,
    private configService: ConfigService,
    public toaster: ToastrService,
    private errorHandlerService: ErrorHandlerService,
    private dialog: MatDialog,
  ) {
    const rolesfeaturesString = localStorage.getItem('rolesfeatures');
    if (rolesfeaturesString !== null) {
      this.assets = JSON.parse(rolesfeaturesString).assets.datasets;
    } else {
      this.assets = 'server_admin';
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
    this.showLoader = true;
    this.project_id = this.configService.SelectedProjectId;
    this.getAllModelsList();
    this.numberOfColumns = this.getNumberOfColumns();
    this.projectSubscription =
      this.configService.selectedProjectIdObservable.subscribe(
        (projectId: any) => {
          if (projectId) {
            this.project_id = projectId;
            this.getAllModelsList();
          }
        },
      );
  }
  isTrainedModel() {
    if (this.actionModel) {
      return this.actionModel.ml_deployed_status.status == 'trained'
        ? true
        : false;
    } else {
      return false;
    }
  }
  isDeployedModel() {
    if (this.actionModel) {
      return this.actionModel.ml_deployed_status.status == 'deployed'
        ? true
        : false;
    } else {
      return false;
    }
  }
  async deployModel(model: any) {
    try {
      this.loadingStates[model._id] = true;
      const deployResponse = await this.modelsService.deployModel(
        this.site_id ?? '',
        this.project_id as string,
        model._id,
      );
      if (deployResponse.ml_deployed_status.status.toLowerCase() == 'trained') {
        this.toaster.error('Failed to deploy model', '', {
          positionClass: 'custom-toast-position',
        });
      } else {
        this.toaster.success('Model Deployed successfully', '', {
          positionClass: 'custom-toast-position',
        });
        let modelIndex = this.filteredModelsData.findIndex(
          (item: any) => item._id == model._id,
        );
        (this.filteredModelsData[modelIndex] as any).ml_deployed_status = (
          deployResponse as any
        ).ml_deployed_status;

        this.dataSource = new MatTableDataSource(this.filteredModelsData);
      }
    } catch (error) {
      this.loadingStates[model._id] = false;
      this.errorHandlerService.handleError(error);
    } finally {
      this.loadingStates[model._id] = false;
    }
  }

  async offlineModel(model: any) {
    try {
      this.loadingStates[model._id] = true;
      const deployResponse = await this.modelsService.offlineModel(
        this.site_id ?? '',
        this.project_id as string,
        model._id,
      );
      if (
        deployResponse.ml_deployed_status.status.toLowerCase() == 'deployed'
      ) {
        this.toaster.error('Failed to undeploy model', '', {
          positionClass: 'custom-toast-position',
        });
      } else {
        this.toaster.success('Model Undeployed successfully', '', {
          positionClass: 'custom-toast-position',
        });
        let modelIndex = this.filteredModelsData.findIndex(
          (item: any) => item._id == model._id,
        );
        (this.filteredModelsData[modelIndex] as any).ml_deployed_status = (
          deployResponse as any
        ).ml_deployed_status;

        this.dataSource = new MatTableDataSource(this.filteredModelsData);
      }
    } catch (error) {
      this.loadingStates[model._id] = false;
      this.errorHandlerService.handleError(error);
    } finally {
      this.loadingStates[model._id] = false;
    }
  }

  async getAllModelsList(): Promise<void> {
    try {
      this.showLoader = true;
      this.models = await this.modelsService.getAllModels(
        this.site_id,
        this.project_id,
      );
      this.models.forEach((item: any, index) => {
        if (!('problem_type' in item.model.configs)) {
          (this.models[index]['model']['configs'] as ModelConfig)[
            'problem_type'
          ] = 'regression';
        }

        if (!('ml_deployed_status' in item)) {
          (
            this.models[index] as { ml_deployed_status: DeployedStatus }
          ).ml_deployed_status = { status: 'trained', port: 0 };
        }
      });

      this.dataSource = new MatTableDataSource(this.models);

      if (this.selectedModels.length > 0) {
        // Re-select models based on persisted selection
        this.selectedModels = this.selectedModels
          .map((selectedModel) =>
            this.models.find((model: any) => model._id === selectedModel._id),
          )
          .filter((model) => model !== undefined);
      }

      this.sortLastModified();
      this.showLoader = false;
    } catch (error) {
      this.showLoader = false;
      this.errorHandlerService.handleError(error);
    }
  }
  sortLastModified(): void {
    this.filteredModelsData = this.models;
    this.filteredModelsData.sort((a, b) => {
      const dateA = new Date(a['created_at']).getTime();
      const dateB = new Date(b['created_at']).getTime();
      return dateB - dateA;
    });
    this.dataSource = new MatTableDataSource(this.filteredModelsData);
  }

  uniqueCreatedBy() {
    let uniqueNames: any = [];
    if (this.models && this.models.length > 0) {
      return [...new Set(this.models.map((model: any) => model.user_name))];
    }
    return uniqueNames;
  }
  async sortData(sort: Sort) {
    this.filteredModelsData.sort((a: any, b: any) => {
      let aValue: any = '';
      let bValue: any = '';

      if (sort['active'] == 'name') {
        aValue = a.model.name;
        bValue = b.model.name;
      } else if (sort['active'] == 'created_by') {
        aValue = a.model.user_name;
        bValue = b.model.user_name;
      } else if (sort['active'] == 'type') {
        aValue = a.model.type;
        bValue = b.model.type;
      } else if (sort['active'] == 'input') {
        aValue = a.model.configs.input_cols.toString();
        bValue = b.model.configs.input_cols.toString();
      } else if (sort['active'] == 'output') {
        aValue = a.model.configs.output_col
          ? a.model.configs.output_col
          : a.model.configs.output_cols.toString();
        bValue = b.model.configs.output_col
          ? b.model.configs.output_col
          : b.model.configs.output_cols.toString();
      } else if (sort['active'] == 'problem_type') {
        aValue = a.model.configs.problem_type.toString();
        bValue = b.model.configs.problem_type.toString();
      } else if (sort['active'] == 'ml_deployed_status') {
        aValue = a.ml_deployed_status.status.toString();
        bValue = b.ml_deployed_status.status.toString();
      } else {
        aValue = a[sort['active']];
        bValue = b[sort['active']];
      }

      const compareValues = (valueA: any, valueB: any) => {
        if (!isNaN(valueA) && !isNaN(valueB)) {
          return valueA - valueB;
        }
        const dateA = new Date(valueA);
        const dateB = new Date(valueB);
        if (!isNaN(dateA.getTime()) && !isNaN(dateB.getTime())) {
          return dateA.getTime() - dateB.getTime();
        }
        return valueA.localeCompare(valueB);
      };

      const comparisonResult = compareValues(aValue, bValue);
      return sort['direction'] === 'asc' ? comparisonResult : -comparisonResult;
    });
    this.dataSource = new MatTableDataSource(this.filteredModelsData);
  }

  ngAfterViewInit() {
    this.screenWidth = window.innerWidth;
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
    const parentWidth = document.querySelector('[fxLayout]')!.clientWidth; // Ensure this selects your flex container
    this.numberOfColumns = Utils.CalculateColumns(parentWidth);
  }

  getNumberOfColumns(): number {
    let screenWidth = window.innerWidth;
    let tileCount = Math.floor(screenWidth / 220);
    return tileCount;
  }

  onSearchTextChange(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.searchText = filterValue;
    this.applyFilters();
  }
  applyFilters() {
    let filteredData: any[] | [] = this.models;

    // Filter based on search text if present
    if (this.searchText.trim() !== '') {
      filteredData = filteredData.filter(
        (item: any) =>
          item.model.name
            .toLowerCase()
            .includes(this.searchText.trim().toLowerCase()) ||
          item.user_name
            .toLowerCase()
            .includes(this.searchText.trim().toLowerCase()),
      );
    }
    this.filteredModelsData = filteredData;
    this.dataSource = new MatTableDataSource(this.filteredModelsData);
  }
  isWorkflowRowSelected(row: any): boolean {
    return this.selectedWorkflowRow === row;
  }

  changeToModelPreview(element: any) {
    if (!this.compareModelsButtons) {
      this.previewModel = true;
      this.compareModels = false;
      this.modelDetails = element;
    }
  }

  previewModelHandler(event: any) {
    this.previewModel = event.previewModel;
    this.showLoader = true;
    this.getAllModelsList();
  }

  compareModelHandler(value: any) {
    this.compareModels = value;
    this.showLoader = true;
    this.compareModelsButtons = true;
    this.getAllModelsList();
  }

  async deleteModelFunc() {
    if (this.deletionId) {
      const deleteResponse = await this.modelsService.deleteModel(
        this.site_id ?? '',
        this.project_id,
        this.deletionId,
      );
      if ((deleteResponse as any).status === 'success') {
        this.toaster.success('Model deleted successfully', '', {
          positionClass: 'custom-toast-position',
        });
        this.getAllModelsList();
      }
    }
    this.deleteConfirmation = false;
  }

  toggleFavorite(element: any): void {
    element.isFavorite = !element.isFavorite;
  }

  toggleCompare(selectedModel: any): void {
    const index = this.selectedModels.indexOf(selectedModel);
    if (index > -1) {
      this.selectedModels.splice(index, 1);
    } else {
      if (this.selectedModels.length < 2) {
        this.selectedModels.push(selectedModel);
      }
    }
    if (this.selectedModels.length === 2) {
      const model1 = this.selectedModels[0];
      const model2 = this.selectedModels[1];

      const isInputColsMatch =
        JSON.stringify(model1.model.configs.input_cols) ===
        JSON.stringify(model2.model.configs.input_cols);
      const isOutputColsMatch =
        JSON.stringify(model1.model.configs.output_cols) ===
        JSON.stringify(model2.model.configs.output_cols);

      if (!isInputColsMatch || !isOutputColsMatch) {
        this.errorMessage =
          'Input or output features are not same, so cannot be compared';
        this.errorKey = true;
      } else {
        this.errorMessage = '';
        this.canCompare = true;
        this.compareModelsButtons = true;
      }
    } else {
      this.errorMessage = 'Please select another model to compare';
      this.errorKey = false;
      this.canCompare = false;
      this.compareModelsButtons = this.selectedModels.length > 0;
    }
  }

  cancelCompareModel(): void {
    this.selectedModels = [];
    this.compareModelsButtons = false;
  }

  confirmCompareModel() {
    this.compareModelsButtons = false;
    this.compareModels = true;
    this.previewModel = false;
  }

  lastAccessedDate(date: string) {
    return Utils.formatDateTime(date);
  }

  async deleteAllModels() {
    var modelsResult = await this.modelsService.deleteAllModels(
      this.site_id,
      this.project_id,
    );
    if (modelsResult.status === 'success') {
      this.getAllModelsList();
    }
  }

  openModelPreveiwDialog(data: any) {
    const dialogRef = this.dialog.open(ModelPreviewDialogBoxComponent, {
      width: '95vw',
      maxWidth: '95vw',
      height: '95%',
      data: {
        data: data,
        type: 'SingleModelPreview',
      },
    });
    dialogRef.afterClosed().subscribe((result: any) => { });
  }

  openEditModelDialog(model: any) {
    const dialogRef = this.dialog.open(EditModelComponent, {
      width: '660px',
      data: {
        model_object: model,
      },
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.getAllModelsList();
      }
    });
  }

  isArray(value: any): boolean {
    return Array.isArray(value);
  }
}
