import {
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
  SimpleChanges,
  OnChanges,
} from '@angular/core';
import { ModelsService } from 'src/app/pages/models/services/models.service';
import { ToastrService } from 'ngx-toastr';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { ConfigService } from 'src/app/services/config.service';
import { ProblemType } from 'src/app/models/workflow-models';
import { Subscription } from 'rxjs';
@Component({
  selector: 'app-models-summary',
  templateUrl: './models-summary.component.html',
  styleUrls: ['./models-summary.component.less'],
})
export class ModelsSummaryComponent implements OnInit, OnChanges {
  private subscription!: Subscription;
  @Input() models: any;
  @Input() modelDetails: any;
  @Input() type: any;
  @Input() data: any;
  @Input() spinnerFlag: any;
  @Input() isScientificNotationEnabled: any;
  loader: boolean = true;
  @Output() previewModel = new EventEmitter();
  @Output() loaded = new EventEmitter<void>();

  @Input() items: any[] = [];
  matches: any[] = [];
  modelsList: any[] = [];

  isEditing: boolean = false;
  editedName: string = '';
  originalName: string = '';
  project_id: string | undefined;
  site_id: string | undefined = '1';
  columns = ['precision', 'recall', 'f1-score', 'support'];
  selectedSortOption: string = 'Mean Absolute Error (MAE)';
  selectedmetrics: string = 'test';
  // isScientificNotationEnabled = false;
  constructor(
    private modelsService: ModelsService,
    public errorHandlerService: ErrorHandlerService,
    public toaster: ToastrService,
    private configService: ConfigService,
  ) { }
  ngOnInit(): void {
    this.project_id = this.configService.SelectedProjectId;
    this.loadContent();
    this.subscription = this.modelsService.updatedRows$.subscribe({
      next: (data) => {
        try {
          if (data?.saveAllFlag) {
            this.matches = data.matchedData;
            for (let index = 0; index < this.models.length; index++) {
              if (this.matches && this.matches.length > 0) {
                if (this.matches[index]?.IsActive) {
                  this.models[index].isActive = true;
                }
              }
              setTimeout(() => {
                this.models[index].isActive = false;
              }, 5000);
            }
          } else {
            for (let index = 0; index < this.models.length; index++) {
              this.models[index].isActive = false;
            }
          }
        } catch (error) {
          console.error('Error processing updateRows data:', error);
        }
      },
      error: (error) => {
        console.error('Error in subscription:', error);
      }
    });

    this.modelsService.updateRows(null);
  }

  isActiveModel(model: any) {
    if (model.isActive) {
      return true
    } else return false
  }

  ngOnChanges(changes: SimpleChanges) {
    this.checktheView();
    if (changes['models'] && !changes['models'].firstChange) {
      this.loadContent();
    }
  }

  checktheView() {
    if (this.spinnerFlag !== undefined && this.spinnerFlag !== null && !this.spinnerFlag) {
      this.loader = false;
    }
  }

  loadContent() {
    this.checktheView();
    if (this.models && this.models.length > 0) {
      setTimeout(() => {
        this.loaded.emit();
        this.loader = false;
      }, 1000);
    }
  }

  toggleEdit(modelDetails: any) {
    this.isEditing = !this.isEditing;
    if (this.isEditing) {
      this.originalName = modelDetails.model.name;
      this.editedName = this.originalName;
    }
  }
  cancelEdit() {
    this.isEditing = false;
    this.editedName = this.originalName;
  }
  isClassificationModel(model: any) {
    if (!model.configs) {
      return false;
    }

    if ('problem_type' in model.configs) {
      return model.configs.problem_type === ProblemType.Classification
        ? true
        : false;
    } else {
      return false;
    }
  }
  isRegressionModel(model: any) {
    if (!model.configs) {
      return true;
    }

    if ('problem_type' in model.configs) {
      return model.configs.problem_type === ProblemType.Regression
        ? true
        : false;
    } else {
      return true;
    }
  }

  multipleOutputs(model: any) {
    if ('output_cols' in model.configs) {
      return (model.configs.output_cols.length > 1 && this.isObj(model.metrics['Mean Absolute Error (MAE)'])) ? true : false;
    } else {
      return false;
    }
  }

  saveEdit(modelDetails: any) {
    modelDetails.model.name = this.editedName;
    this.isEditing = false;
    this.updateTheModelObject(modelDetails);
  }

  async updateTheModelObject(modelDetails: any) {
    try {
      const saveResult = await this.modelsService.updateModel(
        this.site_id ?? '',
        this.project_id,
        [modelDetails],
      );
      modelDetails.access_mode = 'EXTERNAL'
      if (saveResult?.length === 0) {
        this.toaster.success('Model saved successfully');
      } else {
        this.toaster.error('Model with this name already exists');
      }

    } catch (error) {
      console.error('Error while saving the model:', error);
      this.errorHandlerService.handleError(error);
    }
  }

  isNotExcludedModelType(modelType: string): boolean {
    return (
      modelType !== 'GPR' &&
      modelType !== 'MOGPR' &&
      modelType !== 'SVM Regressor'
    );
  }

  isIncludedModelType(modelType: string): boolean {
    return (
      modelType == 'GPR' || modelType == 'MOGPR' || modelType == 'SVM Regressor'
    );
  }

  getMetricsKeys(obj: any): string[] {
    return Object.keys(obj);
  }

  formatKey(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  isNumeric(value: any): boolean {
    return !isNaN(parseFloat(value)) && isFinite(value);
  }

  isDecimal(value: any): boolean {
    return !isNaN(value) && value % 1 !== 0;
  }

  keys(obj: any) {
    return Object.keys(obj);
  }

  isObj(value: any): boolean {
    return value && typeof value === 'object' && !Array.isArray(value);
  }

  goToBuildModePage() {
    this.previewModel.emit({ previewModel: false });
  }

  isArray(value: any): boolean {
    return Array.isArray(value);
  }
  checkTheProblemType() {
    if (this.models) {
      for (let model of this.models) {
        if (model.model.configs && 'problem_type' in model.model.configs) {
          return model.model.configs.problem_type === 'regression';
        }
      }
    }
    return false;
  }

  onSortChange(event: any) {
    const key = event;
    this.models.sort((a: any, b: any) => {
      return a.model.metrics[key] - b.model.metrics[key];
    });
  }

  metricsOnChange(event: any) {
    this.selectedmetrics = event;
  }
}
