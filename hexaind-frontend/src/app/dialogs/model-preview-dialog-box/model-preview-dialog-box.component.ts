import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  Inject,
  Input,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { ToastrService } from 'ngx-toastr';
import {
  ConfigService,
  WorkflowCanvasService,
} from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ApiService } from 'src/app/services/api.service';
import { ModelsService } from 'src/app/pages/models/services/models.service';
import * as Plotly from 'plotly.js-dist-min';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { environment } from 'src/environments/environment';
import { DomSanitizer } from '@angular/platform-browser';
import { catchError, forkJoin, Observable, of } from 'rxjs';
import { ActivatedRoute } from '@angular/router';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatExpansionPanel } from '@angular/material/expansion';
import { ProblemType } from 'src/app/models/workflow-models';




interface ProblemTypeConfig {
  problem_type: string;
}
interface ModelConfigs {
  input_cols: any[];
  output_cols: any[];
}

interface Model {
  configs: ModelConfigs;
  type: string;
  name: string;
}

interface SelectedModel {
  model: Model;
}

@Component({
  selector: 'app-model-preview-dialog-box',
  templateUrl: './model-preview-dialog-box.component.html',
  styleUrls: ['./model-preview-dialog-box.component.less'],
})
export class ModelPreviewDialogBoxComponent implements OnInit {
  selectedTabIndex = 0;
  loading: boolean = false;
  loader!: boolean;
  workflow_name: string | undefined;
  dataSource = new MatTableDataSource([]);
  dataLoaded: boolean = false;

  selectedData: string = '';
  selectedModel: SelectedModel | null = null;
  modelType: string = '';

  highlightedData: any[] = [];
  project_id: string | undefined;
  site_id: string | undefined = '1';
  run_id: any;
  models: any[] = [];
  matches: any[] = [];
  isEditing: boolean = false;
  editedName: string = '';
  originalName: string = '';
  selectedInputColumn: string = '';
  selectedOutputColumn: string = '';
  selectedModelInputs: any[] = [];
  selectedModelOutputs: any[] = [];
  workflowSessionId: string | null | undefined;
  workflowId: string | null | undefined;
  files: any[] = [];
  confusionMetricsGraphs: any[] = [];
  confusionMetricsVizGrouped: { [key: string]: any } = {};

  columns = ['precision', 'recall', 'f1-score', 'support'];

  selectedPreviewIndex: number = 0;
  currentPredictionData: any;
  currentResidualData: any;
  mostRecentModel: any;
  selectedModelObject: any;

  allModels: any[] = [];
  type: string = 'summary';
  downloadLoder: boolean = false;
  isScientificNotationEnabled: boolean = false;
  disabledTabIndex: number = 0;
  violenPlots: any = [];
  isTrainErrorVisible: boolean = true;  // By default, error bars for the train set are visible
  isTestErrorVisible: boolean = true;
  selectedTrace = 'Test set'
  loadingContent = false;
  selectedmetrics: string = 'test';

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public workflowCanvasService: WorkflowCanvasService,
    public toaster: ToastrService,
    private configService: ConfigService,
    private apiService: ApiService,
    private modelsService: ModelsService,
    private errorHandlerService: ErrorHandlerService,
    private sanitizer: DomSanitizer,
    private route: ActivatedRoute,
    private cdRef: ChangeDetectorRef,
  ) {
    this.models = [];
  }

  ngOnInit() {
    this.project_id = this.configService.SelectedProjectId;
    if (this.data.type == 'SingleModelPreview') {
      this.models = [];
      this.models.push(this.data.data);
      this.run_id = this.models[0].wf_run_id
    } else {
      this.workflowSessionId =
        this.workflowCanvasService.SelectedWorkflowSession?._id;
      if (this.workflowCanvasService.IsVersionedWorkflow) {
        const viewingRunId = this.route.snapshot.queryParams['viewingRunId'];
        this.workflowId = this.workflowCanvasService.SelectedWorkflow!._id;
        if (viewingRunId !== undefined) {
          this.run_id = viewingRunId;
          this.getResultsOfModels();
        } else {
          this.getVersionedWorkflowRuns();
        }
      } else {
        this.run_id =
          this.workflowCanvasService.SelectedWorkflowSession?.run_id;
        this.workflowId = this.workflowCanvasService.SelectedWorkflow!._id;
        this.getResultsOfModels();
      }
      if (this.workflowCanvasService.SelectedWorkflow) {
        this.workflow_name = this.workflowCanvasService.SelectedWorkflow.name;
      }
    }
  }
  downloadModels() {
    let fileName = '';
    if (this.data.type == 'SingleModelPreview') {
      fileName = this.models[0].model.name + '-' + this.run_id + '.zip';
    } else {
      fileName = this.workflow_name + '-' + this.run_id + '.zip';
    }

    this.downloadLoder = true;

    this.modelsService.downloadModels(this.configService.SelectedSiteId, this.project_id, this.run_id)
      .subscribe({
        next: (blob: Blob) => this.handleBlob(blob, fileName),
        error: (error: any) => {
          this.downloadLoder = false;
          this.errorHandlerService.handleError(error);
        },
      });
  }
  private handleBlob(blob: Blob, fileName: string) {
    const blobUrl = window.URL.createObjectURL(blob);
    this.triggerDownload(blobUrl, fileName);
  }

  private triggerDownload(blobUrl: string, fileName: string) {
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(blobUrl);
    link.remove();
    this.downloadLoder = false;
  }
  onTabClick(index: number) {
    if (!this.loading) {
      this.selectedTabIndex = index;
      this.loading = true;
      // this.disabledTabIndex = index;
      this.selectedModelObject = this.models[0];
    }
  }

  onTabLoaded() {
    this.loading = false;
  }

  existsVisualization() {
    if (this.models.length > 0) {
      const hasVisualizations = this.models.some((model: any) => {
        return 'visualizations' in model.model && model.model.visualizations;
      });
      return hasVisualizations;
    } else {
      return false;
    }
    return false;
  }
  preloadConfusionGraps() {
    let visualizationList: any[] = [];
    this.models.forEach((model: any, index: number) => {
      if ('visualizations' in model.model && model.model.visualizations) {
        for (var i = 0; i < model.model.visualizations.length; i++) {
          visualizationList.push({
            path: model.model.visualizations[i],
            name: model.model.name,
          });
          if (
            i == model.model.visualizations.length - 1 &&
            index == this.models.length - 1
          ) {
            for (var i = 0; i < visualizationList.length; i++) {
              if (!this.confusionMetricsVizGrouped[visualizationList[i].name]) {
                this.confusionMetricsVizGrouped[visualizationList[i].name] = {
                  loader: false,
                  data: [],
                };
              }
              this.confusionMetricsVizGrouped[
                visualizationList[i].name
              ].data.push({
                name: visualizationList[i].name,
                path: visualizationList[i].path,
                imageUrl: '',
              });
            }
          }
        }
      }
    });
  }

  onAccordionExpanded(event: any, key: any) {
    this.loading = true;
    const data = this.confusionMetricsVizGrouped[key].data.filter(
      (item: any) => item.imageUrl === '',
    );

    if (data.length > 0) {
      const promises: Promise<any>[] = [];
      this.confusionMetricsVizGrouped[key].loader = true;

      data.forEach((item: any) => {
        if (item.imageUrl === '') {
          const promise = this.modelsService
            .getConfusionMetricsFileContent({
              path: item.path,
              name: item.name,
            })
            .toPromise();

          promises.push(
            promise.then((result) => {
              const index = this.confusionMetricsVizGrouped[key].data.findIndex(
                (metric: any) => metric.path === item.path,
              );
              if (index !== -1) {
                this.confusionMetricsVizGrouped[key].data[index].imageUrl =
                  result;
              }
            }),
          );
        }
      });

      Promise.all(promises)
        .then(() => {
          this.confusionMetricsVizGrouped[key].loader = false;
          this.loading = false;
        })
        .catch((error) => {
          console.error('Error loading confusion metrics:', error);
          this.confusionMetricsVizGrouped[key].loader = false;
          this.loading = false;
        });
    } else {
      this.loading = false;
    }
  }

  async getVersionedWorkflowRuns() {
    let response = await this.apiService.GetWorkflowRuns(
      this.site_id ?? '',
      this.project_id ?? '',
      this.workflowId ?? '',
    );
    if (response) {
      var run_obj = response.sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )[0];
      this.run_id = run_obj._id || '';
      this.getResultsOfModels();
    }
  }

  onModelSelection() {
    this.selectedModelObject = this.models.find(
      (model) => model.model.name === this.selectedModel,
    );
    this.modelType = this.selectedModelObject.model.type
    this.selectedModelInputs = this.selectedModelObject.model.configs.input_cols;
    this.selectedInputColumn = this.selectedModelObject.model.configs.input_cols[0];
    if (this.modelType === 'GPR' || this.modelType === 'MOGPR' || this.modelType === 'SVM Regressor') {
      this.selectedModelOutputs =
        this.selectedModelObject.model.configs.output_cols;
      this.selectedOutputColumn = this.selectedModelObject.model.configs.output_cols[0];
    } else {
      this.selectedOutputColumn = this.selectedModelObject.model.configs.output_col;
      this.selectedModelOutputs = [this.selectedModelObject.model.configs.output_col]
    }
    this.modelVisualization();
  }

  onSelectionChange() {
    if (
      this.selectedData &&
      this.selectedInputColumn &&
      this.selectedOutputColumn
    ) {
      this.modelVisualization();
    }
  }

  async showVisualization(): Promise<void> {
    this.loading = true;
    this.loader = true;
    this.modelType = this.selectedModelObject.model.type;

    try {
      if (
        this.isRegressionModel(this.selectedModelObject.model)
      ) {
        const modelConfig = this.selectedModelObject.model.configs;

        this.selectedModel = this.selectedModelObject.model.name;
        this.selectedInputColumn = modelConfig.input_cols[0];
        this.selectedModelInputs = modelConfig.input_cols;
        this.selectedOutputColumn = modelConfig.output_cols
          ? modelConfig.output_cols[0]
          : modelConfig.output_col;
        this.selectedModelOutputs = modelConfig.output_cols
          ? modelConfig.output_cols
          : [modelConfig.output_col];
        this.selectedData = 'all';
        await this.modelVisualization();
        this.onTabLoaded();
        this.loader = false;
      } else {
        this.onTabLoaded();
        this.loader = false;
      }
    } catch (error) {
      console.error('Error creating visualizations:', error);
      this.errorHandlerService.handleError(error);
      this.onTabLoaded();
      this.loader = false;
    }
  }

  async modelVisualization() {
    try {
      const siteId = '1';
      const projectId = this.project_id || '';
      const summary_path = this.selectedModelObject.ml_model_file_path;
      const dataPath = this.selectedModelObject.dataset_path;
      const type = this.selectedModelObject.model.type;
      const chosenColumn = this.selectedInputColumn;
      const outputCol = this.selectedOutputColumn;
      var splitRatio;
      if (this.selectedModelObject.model.configs.split_ratio) {
        splitRatio = this.selectedModelObject.model.configs.split_ratio
      } else if (this.selectedModelObject.model.configs.hyper_params?.split_ratio) {
        splitRatio = this.selectedModelObject.model.configs.hyper_params.split_ratio
      } else {
        splitRatio = 0;
      }
      const dataType = this.selectedData;

      const visualizations = await this.modelsService.createVisualizations(
        siteId,
        projectId,
        {
          model: type,
          summary_path: summary_path,
          data_path: dataPath,
          chosen_column: chosenColumn,
          output_col: outputCol,
          split_ratio: splitRatio,
          data_type: dataType,
        },
      );
      if (visualizations.visualization_data) {
        this.cdRef.detectChanges();
        this.renderPredictionGraph(
          visualizations.visualization_data,
          'graph1',
          dataType
        );
        this.renderResidualGraph(
          visualizations.visualization_data,
          'graph2',
          dataType
        );
      }
    } catch (error) {
      console.error('Error creating visualizations:', error);
      this.onTabLoaded();
      this.errorHandlerService.handleError(error);
    } finally {
      this.onTabLoaded();
    }
  }

  onTabChange(event: any) {
    this.selectedTabIndex = event.index;
  }

  async getResultsOfModels(): Promise<void> {
    try {
      const models = await this.modelsService.getModelResults(
        this.site_id,
        this.project_id,
        this.run_id,
      );
      if (this.data.selectedPreview === 'single') {
        this.models = models.filter((model: { widget_urn: any; }) => model.widget_urn === this.data.urn);
      } else {
        this.models = models
      }
      // this.models = this.getMostRecentModels(models);
      this.models.forEach((item: any, index) => {
        if (this.models[index]['access_mode'] == 'EXTERNAL') {
          this.models[index]['isActive'] = true;
        } else {
          this.models[index]['isActive'] = false;
        }
        if (
          !('problem_type' in item.model.configs) &&
          item.model.type !== 'GPC'
        ) {
          (this.models[index]['model']['configs'] as ProblemTypeConfig)[
            'problem_type'
          ] = 'regression';
        }
      });
      if (this.models.length > 0) {
        this.preloadConfusionGraps();
      }
    } catch (error) {
      console.error('Error fetching model results:', error);
      this.errorHandlerService.handleError(error);
    }
  }

  getMostRecentModels(models: any[]): any[] {
    if (models.length === 0) return [];
    let latestDate = new Date(models[0].created_at);
    models.forEach((model) => {
      const modelDate = new Date(model.created_at);
      if (modelDate > latestDate) {
        latestDate = modelDate;
      }
    });
    return models.filter(
      (model) => new Date(model.created_at).getTime() === latestDate.getTime(),
    );
  }

  featureImpotance() {
    this.loader = true;
    this.preloadImages(this.models);
  }

  truncateModelName(name: string): string {
    return name.length > 35 ? name.substring(0, 50) + '...' : name;
  }

  isNotExcludedModelType(modelType: string): boolean {
    return (
      modelType !== 'SVM Regressor'
    );
  }

  isIncludedModelType(modelType: string): boolean {
    return (
      modelType == 'MPR' ||
      modelType == 'GPR' ||
      modelType == 'MOGPR' ||
      modelType == 'SVM Regressor' ||
      modelType == 'WeightedEnsemble_L2' ||
      modelType == 'GPC' ||
      modelType == 'RandomForest' ||
      modelType == 'KNN' ||
      modelType == 'CatBoost/T1' ||
      modelType == 'ExtraTrees' ||
      modelType == 'KNeighbors' ||
      modelType == 'XGBoost/T1' ||
      modelType == 'NNFASTAI' ||
      modelType == 'LinearModel/T1' ||
      modelType == 'LightGBM/T1' ||
      modelType == 'NeuralNetTorch/T1'
    );
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

  saveEdit(modelDetails: any) {
    modelDetails.model.name = this.editedName;
    this.isEditing = false;
    this.updateTheModelObject(modelDetails);
  }

  async updateTheModelObject(modelDetails: any) {
    try {
      const saveResult = await this.modelsService.saveModel(
        this.site_id ?? '',
        this.project_id,
        [modelDetails],
      );

      if (saveResult?.length === 0) {
        this.toaster.success('Model saved successfully');
      } else {
        this.toaster.info('Model already saved');
      }
    } catch (error) {
      this.onTabLoaded();
      console.error('Error while saving the model:', error);
      this.errorHandlerService.handleError(error);
    }
  }

  async saveAllModels() {
    try {
      this.getResultsOfModels();
      const saveResult: any = await this.modelsService.saveModel(
        this.site_id ?? '',
        this.project_id,
        this.models
      );

      const filteredModels = this.models.filter(model => model.access_mode === 'EXTERNAL');
      if (filteredModels.length > 0) {
        this.toaster.info('Models already saved');
      } else {
        this.toaster.success('Models saved successfully')
      }
      this.models.forEach(model => {
        if (model.access_mode !== 'EXTERNAL') {
          model.access_mode = 'EXTERNAL';
        }
      });
      var data = {
        matchedData: this.models,
        saveAllFlag: true
      }
      this.modelsService.updateRows(data);

    } catch (error) {
      this.onTabLoaded();
      console.error('Error while saving the models:', error);
      this.errorHandlerService.handleError(error);
    }
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

  preloadImages(files: any[]): void {
    this.loading = true;
    this.files = [];
    this.violenPlots = [];
    forkJoin(
      files.map((file) => {
        // Might be useful in future - Written by Taimoor:
        // If the file has an 'html' extension, return the file directly
        // if (typeof file.model.feature_imp_plot === 'string' && file.model.feature_imp_plot.endsWith('.html')) {
        //   const unsafeUrl = file.model.feature_imp_plot; // The raw URL
        //   return [[{url: this.sanitizer.bypassSecurityTrustResourceUrl(`${this.configService.getAppAuxApiURL}/eda/file?path=${unsafeUrl}`)}]];
        // } else {
        return this.modelsService.getFileContent(file).pipe(
          catchError((error) => {
            console.error(`Error loading file: ${file.name}`, error);
            return of(null);
          }),
        );
        // }
      }),
    ).subscribe({
      next: (results) => {
        const combinedFiles: any = [];
        results.forEach((result, index) => {
          if (result) {
            const model = files[index].model;
            const fileData = {
              name: model.name,
              imageUrl: result,
            };
            const violenData = this.getViolenPlots(model);
            combinedFiles.push({
              ...fileData,
              voilenUrlData: violenData || [],
            });
          } else {
            console.error('Result is null ${index}');
          }
        });
        this.loadingContent = true;
        this.files = combinedFiles;
        setTimeout(() => {
          this.loadingContent = false;
        }, 10000);
      },
      error: (error) => {
        console.error('Error loading images:', error);
        this.errorHandlerService.handleError(error);
        this.loading = false;
        this.loadingContent = false;
      },
      complete: () => {
        this.onTabLoaded();
        this.loader = false;
      },
    });
  }

  private getViolenPlots(model: any): any {
    if ('feature_imp_plot_violen' in model) {
      if (model.feature_imp_plot_violen) {
        const featureImpPlot = model.feature_imp_plot_violen;
        const featureImpPlotArray = Array.isArray(featureImpPlot) ? featureImpPlot : [featureImpPlot];
        const urls = featureImpPlotArray.map((plot) =>
          this.sanitizer.bypassSecurityTrustResourceUrl(
            `${this.configService.getAppAuxApiURL}/eda/file?path=${plot}`
          )
        );
        return { name: model.name, voilenUrl: urls.map((url) => ({ interactivePlot: url })) };
      }
    }
    return { voilenUrl: [] };
  }

  hasVoilenPlot(model: any) {
    let plots = this.violenPlots.filter((plot: any) => plot.name == model.name);
    return (plots.length > 0) ? true : false;
  }

  onTrainErrorToggleChange(): void {
    this.renderPredictionGraph(this.currentPredictionData, 'graph1', this.selectedData);
  }

  onTestErrorToggleChange(): void {
    this.renderPredictionGraph(this.currentPredictionData, 'graph1', this.selectedData);
  }

  renderPredictionGraph(data: any, elementId: string, dataType: string): void {
    this.currentPredictionData = data;
    let testXValues: number[] = [];
    let testYValues: number[] = [];
    let trainXValues: number[] = [];
    let trainYValues: number[] = [];
    let combinedValues: number[] = [];
    let y_error_test: number[] = [];
    let y_error_train: number[] = [];

    if (dataType === 'test') {
      testXValues = data.prediction_parity.target_value;
      testYValues = data.prediction_parity.prediction_value;
      y_error_test = data.prediction_std;
      combinedValues = testXValues.concat(testYValues);
    } else if (dataType === 'train') {
      trainXValues = data.prediction_parity.target_value;
      trainYValues = data.prediction_parity.prediction_value;
      combinedValues = trainXValues.concat(trainYValues);
      y_error_train = data.prediction_std;
    } else if (dataType === 'all') {
      testXValues = data.test_data.prediction_parity.target_value;
      testYValues = data.test_data.prediction_parity.prediction_value;
      trainXValues = data.train_data.prediction_parity.target_value;
      trainYValues = data.train_data.prediction_parity.prediction_value;
      combinedValues = testXValues.concat(testYValues, trainXValues, trainYValues);
      y_error_test = data.test_data.prediction_std;
      y_error_train = data.train_data.prediction_std;
    }

    const minValue = Math.min(...combinedValues);
    const maxValue = Math.max(...combinedValues);
    const buffer = (maxValue - minValue) * 0.05;

    const minY = Math.min(...testYValues, ...trainYValues);
    const maxY = Math.max(...testYValues, ...trainYValues);
    const bufferY = (maxY - minY) * 0.05;

    const testTrace: Partial<Plotly.Data> = {
      x: testXValues,
      y: testYValues,
      mode: 'markers',
      type: 'scatter',
      marker: { color: '#E05900', size: 8 },
      name: 'Test set',
      hovertemplate: 'Actual: %{x}<br>Prediction: %{y}<extra></extra>',
      visible: this.isTestErrorVisible,
      showlegend: false,
      legendgroup: 'test',
    };

    const staticLegendTestTrace: Partial<Plotly.Data> = {
      x: [null],
      y: [null],
      mode: 'markers',
      type: 'scatter',
      marker: { color: '#E05900', size: 8 },
      name: 'Test set',
      showlegend: true,
      hoverinfo: 'none',
      visible: this.isTestErrorVisible,
      legendrank: 1,
      legendgroup: 'test'
    };

    const staticLegendTrainTrace: Partial<Plotly.Data> = {
      x: [null],
      y: [null],
      mode: 'markers',
      type: 'scatter',
      marker: { color: 'teal', size: 8 },
      name: 'Train set',
      showlegend: true,
      hoverinfo: 'none',
      visible: this.isTrainErrorVisible,
      legendrank: 2,
      legendgroup: 'train'
    };

    const trainTrace: Partial<Plotly.Data> = {
      x: trainXValues,
      y: trainYValues,
      mode: 'markers',
      type: 'scatter',
      marker: { color: 'teal', size: 8 },
      name: 'Train set',
      hovertemplate: 'Actual: %{x}<br>Prediction: %{y}<extra></extra>',
      // legendrank: 2,
      visible: this.isTrainErrorVisible,
      showlegend: false,
      legendgroup: 'train'
    };

    const testErrorTrace: Partial<Plotly.Data> = {
      x: testXValues,
      y: testYValues,
      mode: 'markers',
      type: 'scatter',
      name: 'Test set ± Std Dev',
      error_y: {
        type: 'data',
        array: y_error_test,
        visible: this.isTestErrorVisible,
        color: 'darkgray',
        thickness: 1,
        width: 2,
      },
      showlegend: true,
      marker: {
        // size: 15,
        symbol: 'line-ns',
        color: 'darkgray',
        opacity: 0.5,
        line: { width: 2 },
      },
      legendrank: 3,
    };

    const trainErrorTrace: Partial<Plotly.Data> = {
      x: trainXValues,
      y: trainYValues,
      mode: 'markers',
      type: 'scatter',
      name: 'Train set ± Std Dev',
      error_y: {
        type: 'data',
        array: y_error_train,
        visible: this.isTrainErrorVisible,
        color: 'darkgray',
        thickness: 1,
        width: 2,
      },
      showlegend: true,
      marker: {
        // size: 15,
        symbol: 'line-ns',
        color: 'darkgray',
        opacity: 0.5,
        line: { width: 2 },
      },
      legendrank: 4,
    };

    const identityLine: Partial<Plotly.Data> = {
      x: [minValue, maxValue],
      y: [minValue, maxValue],
      mode: 'lines',
      type: 'scatter',
      line: { color: 'black', dash: 'dot' },
      showlegend: false,
    };

    // Determine final error traces - empty if not visible or not GPR/MOGPR
    const testErrorTraceFinal: Partial<Plotly.Data> =
      (this.modelType === 'GPR' || this.modelType === 'MOGPR')
        ? (this.isTestErrorVisible ? testErrorTrace : {})
        : {};

    const trainErrorTraceFinal: Partial<Plotly.Data> =
      (this.modelType === 'GPR' || this.modelType === 'MOGPR')
        ? (this.isTrainErrorVisible ? trainErrorTrace : {})
        : {};

    const tracesToRender: Partial<Plotly.Data>[] =
      dataType === 'all'
        ? [
          staticLegendTestTrace,
          staticLegendTrainTrace,
          testErrorTraceFinal,
          trainErrorTraceFinal,
          trainTrace,
          testTrace,
          identityLine,
        ]
        : dataType === 'test'
          ? [
            staticLegendTestTrace,
            testErrorTraceFinal,
            testTrace,
            identityLine,
          ]
          : [
            staticLegendTrainTrace,
            trainErrorTraceFinal,
            trainTrace,
            identityLine,
          ];

    const layout = {
      xaxis: {
        title: { text: 'Actual', standoff: 20 },
        range: [minValue - buffer, maxValue + buffer],
        zeroline: true,
        showgrid: true,
        showline: true,
        linewidth: 1,
        linecolor: 'black',
      },
      yaxis: {
        title: { text: 'Prediction', standoff: 10 },
        range: [minValue - buffer, maxValue + buffer],
        zeroline: true,
        showgrid: true,
        showline: true,
        linewidth: 1,
        linecolor: 'black',
      },
      shapes: [
        {
          type: 'line',
          x0: minValue - buffer,
          x1: maxValue + buffer,
          y0: 0,
          y1: 0,
          line: {
            color: 'black',
            width: 1,
          },
        },
        {
          type: 'line',
          x0: 0,
          x1: 0,
          y0: minY - bufferY,
          y1: maxY + bufferY,
          line: {
            color: 'black',
            width: 1,
          },
        },
      ],
      showlegend: true,
      legend: {
        x: 0,
        y: 1,
        xanchor: 'left',
        yanchor: 'top',
        orientation: 'v',
        font: {
          size: 12, // Reduce font size for compactness
        },
        itemwidth: 20, // Adjust item width if necessary
        itemspacing: 5, // Reduce spacing between items
        traceorder: 'normal', // Keep legend order consistent
      },
      margin: { l: 50, r: 40, t: 40, b: 40 },
      hovermode: 'closest',
      plot_bgcolor: 'white',
      paper_bgcolor: 'white',
    } as Partial<Plotly.Layout>;



    Plotly.newPlot(elementId, tracesToRender, layout).then((plot) => {
      this.updateGraphHighlight(elementId, testXValues, trainXValues, 0, 'parity_plot', dataType, 5);
      const coordinates = {
        target_x: [...testXValues, ...trainXValues][0],
        prediction_y: [...testYValues, ...trainYValues][0],
      };
      this.getGraphdetailsOnClick(coordinates, 'parity');
      plot.on('plotly_click', (data) => {
        const pointIndex = data.points[0].pointIndex;
        const traceIndex = data.points[0].curveNumber;
        const coordinates = {
          target_x: data.points[0].x,
          prediction_y: data.points[0].y,
        };

        if (dataType === 'all') {
          if (traceIndex === 5) {
            this.selectedTrace = 'Test set'
            this.updateGraphHighlight(elementId, testXValues, trainXValues, pointIndex, 'parity_plot', 'all', traceIndex);
            this.updateGraphHighlight('graph2', this.currentResidualData.test_data.chosen_residual.chosen_feature_values,
              this.currentResidualData.train_data.chosen_residual.chosen_feature_values, pointIndex, 'parity_plot', 'all', traceIndex);
          } else if (traceIndex === 4) {
            this.selectedTrace = 'Train set'
            this.updateGraphHighlight(elementId, testXValues, trainXValues, pointIndex, 'parity_plot', 'all', traceIndex);
            this.updateGraphHighlight('graph2', this.currentResidualData.test_data.chosen_residual.chosen_feature_values,
              this.currentResidualData.train_data.chosen_residual.chosen_feature_values, pointIndex, 'parity_plot', 'all', traceIndex);
          }
        } else if (dataType === 'test') {
          this.updateGraphHighlight(elementId, testXValues, [], pointIndex, 'parity_plot', 'test', traceIndex);
          this.updateGraphHighlight('graph2', this.currentResidualData.chosen_residual.chosen_feature_values, [], pointIndex, 'parity_plot', 'test', traceIndex);
        } else if (dataType === 'train') {
          this.updateGraphHighlight(elementId, [], trainXValues, pointIndex, 'parity_plot', 'train', traceIndex);
          this.updateGraphHighlight('graph2', [], this.currentResidualData.chosen_residual.chosen_feature_values, pointIndex, 'parity_plot', 'train', traceIndex);
        }
        this.getGraphdetailsOnClick(coordinates, 'parity');
      });
    });
  }

  renderResidualGraph(data: any, elementId: string, dataType: string): void {
    this.currentResidualData = data;

    let testFeatureValues: number[] = [];
    let testResiduals: number[] = [];
    let trainFeatureValues: number[] = [];
    let trainResiduals: number[] = [];
    let combinedValues: number[] = [];
    let minValue: number, maxValue: number, buffer: number, minY: number, maxY: number, bufferY: number;

    if (dataType === 'test') {
      testFeatureValues = data.chosen_residual.chosen_feature_values;
      testResiduals = data.chosen_residual.residual_values;
      combinedValues = testFeatureValues.concat(testResiduals);
    } else if (dataType === 'train') {
      trainFeatureValues = data.chosen_residual.chosen_feature_values;
      trainResiduals = data.chosen_residual.residual_values;
      combinedValues = trainFeatureValues.concat(trainResiduals);
    } else if (dataType === 'all') {
      testFeatureValues = data.test_data.chosen_residual.chosen_feature_values;
      testResiduals = data.test_data.chosen_residual.residual_values;
      trainFeatureValues = data.train_data.chosen_residual.chosen_feature_values;
      trainResiduals = data.train_data.chosen_residual.residual_values;
      combinedValues = testFeatureValues.concat(testResiduals, trainFeatureValues, trainResiduals);
    }

    minValue = Math.min(...testFeatureValues, ...trainFeatureValues);
    maxValue = Math.max(...testFeatureValues, ...trainFeatureValues);
    buffer = (maxValue - minValue) * 0.05;
    minY = Math.min(...testResiduals, ...trainResiduals);
    maxY = Math.max(...testResiduals, ...trainResiduals);
    bufferY = (maxY - minY) * 0.05;

    const zeroLine: Partial<Plotly.Data> = {
      x: [Math.min(...[...testFeatureValues, ...trainFeatureValues]), Math.max(...[...testFeatureValues, ...trainFeatureValues])],
      y: [0, 0],
      mode: 'lines',
      type: 'scatter',
      line: { color: 'black' },
      showlegend: false,
      name: 'Zero Line',
    };

    const testResidualTrace: Partial<Plotly.Data> = {
      x: testFeatureValues,
      y: testResiduals,
      mode: 'markers',
      type: 'scatter',
      name: 'Test set',
      marker: { color: '#E05900', size: 8 },
      hovertemplate: 'Feature: %{x}<br>Residual: %{y}<extra></extra>',
      showlegend: false,
      // legendrank: 1
      legendgroup: 'test'
    };

    const trainResidualTrace: Partial<Plotly.Data> = {
      x: trainFeatureValues,
      y: trainResiduals,
      mode: 'markers',
      type: 'scatter',
      name: 'Train set',
      marker: { color: 'teal', size: 8 },
      hovertemplate: 'Feature: %{x}<br>Residual: %{y}<extra></extra>',
      showlegend: false,
      // legendrank: 2
      legendgroup: 'train'
    };

    const staticLegendTestTrace: Partial<Plotly.Data> = {
      x: [null],
      y: [null],
      mode: 'markers',
      type: 'scatter',
      marker: { color: '#E05900', size: 8 },
      name: 'Test set',
      showlegend: true,
      hoverinfo: 'none',
      visible: true,
      legendrank: 1,
      legendgroup: 'test'
    };

    const staticLegendTrainTrace: Partial<Plotly.Data> = {
      x: [null],
      y: [null],
      mode: 'markers',
      type: 'scatter',
      marker: { color: 'teal', size: 8 },
      name: 'Train set',
      showlegend: true,
      hoverinfo: 'none',
      visible: true,
      legendrank: 2,
      legendgroup: 'train'
    };

    // Layout configuration
    const layout = {
      xaxis: {
        title: 'Feature Value',
        range: [minValue - buffer, maxValue + buffer],
        zeroline: false,
        showgrid: true,
        showline: true,
        linewidth: 1,
        linecolor: 'black',
      },
      yaxis: {
        title: 'Residual',
        range: [minY - bufferY, maxY + bufferY],
        zeroline: false,
        showgrid: true,
        showline: true,
        linewidth: 1,
        linecolor: 'black',
      },
      shapes: [
        {
          type: 'line',
          x0: minValue - buffer,
          x1: maxValue + buffer,
          y0: 0,
          y1: 0,
          line: {
            color: 'black',
            width: 1,
          },
        },
      ],
      showlegend: true,
      legend: {
        x: 0,
        y: 1,
        xanchor: 'left',
        yanchor: 'top',
        orientation: 'v',
        font: {
          size: 12,
        },
        itemwidth: 20,
        itemspacing: 5,
        traceorder: 'normal',
      },
      margin: { l: 50, r: 40, t: 40, b: 40 },
      hovermode: 'closest',
      plot_bgcolor: 'white',
      paper_bgcolor: 'white',
    } as Partial<Plotly.Layout>;

    // Add traces based on the dataType
    let tracesToRender = [];
    if (dataType === 'all') {
      tracesToRender.push(staticLegendTestTrace, staticLegendTrainTrace, {}, {}, trainResidualTrace, testResidualTrace, {});
    } else if (dataType === 'test') {
      tracesToRender.push(staticLegendTestTrace, {}, testResidualTrace, {});
    } else if (dataType === 'train') {
      tracesToRender.push(staticLegendTrainTrace, {}, trainResidualTrace, {});
    }

    // Render the plot
    Plotly.newPlot(elementId, tracesToRender, layout).then((plot) => {
      const coordinates = {
        target_x: [...trainFeatureValues, ...testFeatureValues][0],
        prediction_y: [...trainResiduals, ...testResiduals][0],
      };

      // Highlight the first point
      if (dataType === 'all') {
        this.updateGraphHighlight('graph2', testFeatureValues, trainFeatureValues, 0, 'residual_plot', dataType, 5);
      } else if (dataType === 'test') {
        this.updateGraphHighlight('graph2', testFeatureValues, [], 0, 'residual_plot', dataType, 5);
      } else if (dataType === 'train') {
        this.updateGraphHighlight('graph2', [], this.currentPredictionData.prediction_parity.target_value, 0, 'residual_plot', dataType, 5);
      }

      // this.getGraphdetailsOnClick(coordinates, 'residual');

      // Add click functionality
      plot.on('plotly_click', (data) => {
        const { pointNumber, x, y, curveNumber } = data.points[0];
        this.selectedPreviewIndex = pointNumber;
        const clickedCoordinates = { target_x: x, prediction_y: y };
        if (dataType === 'all') {
          if (curveNumber === 5) {
            this.selectedTrace = 'Test set'
            this.updateGraphHighlight('graph2', testFeatureValues, trainFeatureValues, pointNumber, 'residual_plot', 'all', curveNumber);
            this.updateGraphHighlight('graph1', this.currentPredictionData.test_data.prediction_parity.target_value, this.currentPredictionData.train_data.prediction_parity.target_value, pointNumber, 'parity_plot', 'all', curveNumber);
          } else if (curveNumber === 4) {
            this.selectedTrace = 'Train set'
            this.updateGraphHighlight('graph2', testFeatureValues, trainFeatureValues, pointNumber, 'residual_plot', 'all', curveNumber);
            this.updateGraphHighlight('graph1', this.currentPredictionData.test_data.prediction_parity.target_value, this.currentPredictionData.train_data.prediction_parity.target_value, pointNumber, 'parity_plot', 'all', curveNumber);
          }
        } else if (dataType === 'test') {
          this.updateGraphHighlight('graph2', testFeatureValues, [], pointNumber, 'residual_plot', dataType, curveNumber);
          this.updateGraphHighlight('graph1', this.currentPredictionData.prediction_parity.target_value, [], pointNumber, 'parity_plot', dataType, curveNumber);
        } else if (dataType === 'train') {
          this.updateGraphHighlight('graph2', [], trainFeatureValues, pointNumber, 'residual_plot', dataType, curveNumber);
          this.updateGraphHighlight('graph1', [], this.currentPredictionData.prediction_parity.target_value, pointNumber, 'parity_plot', dataType, curveNumber);
        }

        this.getGraphdetailsOnClick(clickedCoordinates, 'residual');
      });
    });
  }

  updateGraphHighlight(
    elementId: string,
    testValues: number[],
    trainValues: number[],
    index: number,
    type: string,
    dataType: string,
    traceIndex: number
  ): void {
    const testColor = '#E05900';
    const trainColor = 'teal';
    const highlightColor = 'red';

    let testColors = new Array(testValues.length).fill(testColor);
    let trainColors = new Array(trainValues.length).fill(trainColor);

    if (type === 'parity_plot' || type === 'residual_plot') {
      if (dataType === 'all') {
        testColors = new Array(testValues.length).fill(testColor);
        trainColors = new Array(trainValues.length).fill(trainColor);

        if (index < testValues.length && traceIndex == 5) {
          testColors[index] = highlightColor;

          Plotly.restyle(
            elementId,
            { 'marker.color': [testColors] },
            [5]
          ).catch((err) => console.error('Plotly restyle failed for test trace in all mode:', err));

          Plotly.restyle(
            elementId,
            { 'marker.color': [trainColors] },
            [4]
          ).catch((err) => console.error('Plotly restyle failed for train reset in all mode:', err));
        } else {
          trainColors[index] = highlightColor;
          Plotly.restyle(
            elementId,
            { 'marker.color': [trainColors] },
            [4]
          ).catch((err) => console.error('Plotly restyle failed for train trace in all mode:', err));

          Plotly.restyle(
            elementId,
            { 'marker.color': [testColors] },
            [5]
          ).catch((err) => console.error('Plotly restyle failed for test reset in all mode:', err));
        }
      }
      else if (dataType === 'test') {
        testColors = new Array(testValues.length).fill(testColor);
        testColors[index] = highlightColor;
        Plotly.restyle(
          elementId,
          { 'marker.color': [testColors] },
          [2]
        ).catch((err) => console.error('Plotly restyle failed for test trace:', err));
      } else if (dataType === 'train') {
        trainColors = new Array(trainValues.length).fill(trainColor);
        trainColors[index] = highlightColor;
        Plotly.restyle(
          elementId,
          { 'marker.color': [trainColors] },
          [2]
        ).catch((err) => console.error('Plotly restyle failed for train trace:', err));
      } else {
        console.warn(`WARN: Unsupported dataType = '${dataType}' in updateGraphHighlight.`);
      }
    } else {
      console.warn(`WARN: Unsupported type = '${type}' in updateGraphHighlight.`);
    }
  }

  getTheDataTypeForClickedPoints() {
    if (this.selectedData === 'all') {
      return this.selectedTrace;
    } else if (this.selectedData === 'test') {
      return 'Test set'
    } else if (this.selectedData === 'train') {
      return 'Train set'
    } else return '';
  }

  async getGraphdetailsOnClick(coordinates: any, type: string) {
    const siteId = '1';
    const projectId = this.project_id || '';
    var splitRatio;
    if (this.selectedModelObject.model.configs.split_ratio) {
      splitRatio = this.selectedModelObject.model.configs.split_ratio
    } else if (this.selectedModelObject.model.configs.hyper_params?.split_ratio) {
      splitRatio = this.selectedModelObject.model.configs.hyper_params.split_ratio
    } else {
      splitRatio = 0;
    }
    let obj = {
      model: this.selectedModelObject.model.type,
      summary_path: this.selectedModelObject.ml_model_file_path,
      data_path: this.selectedModelObject.dataset_path,
      chosen_column: this.selectedInputColumn,
      output_col: this.selectedOutputColumn,
      split_ratio: splitRatio,
      data_type: this.selectedData,
      graph_name: type,
      coordinates: coordinates,
    };

    let results = await this.modelsService.interactiveGraphHover(
      siteId,
      projectId,
      obj,
    );

    const prioritizedKeys = [
      "Output (Target)",
      "Output (Prediction Mean)",
      "Output (Prediction)",
      "Output (Prediction Std Dev)",
      "Residual",
      "Absolute Error (%)"
    ];

    const renamedResults = Object.entries(results.point_summary).map(([key, value]) => {
      if (this.selectedModelObject.model.type === 'GPR' || this.selectedModelObject.model.type === 'MOGPR') {
        let newKey = key;
        if (key === "Output (Prediction)") {
          newKey = "Output (Prediction Mean)";
        } else if (key === "Output (Prediction) std") {
          newKey = "Output (Prediction Std Dev)";
        } else if (key === "Error Percentage") {
          newKey = "Absolute Error (%)";
        }
        return { key: newKey, value };
      } else {
        let newKey = key;
        if (key === "Error Percentage") {
          newKey = "Absolute Error (%)";
        }
        return { key: newKey, value };
      }
    });
    const allData = renamedResults;
    const prioritizedData = allData
      .filter(item => prioritizedKeys.includes(item.key))
      .sort((a, b) => prioritizedKeys.indexOf(a.key) - prioritizedKeys.indexOf(b.key));

    const otherData = allData.filter(item => !prioritizedKeys.includes(item.key));

    this.highlightedData = [...prioritizedData, ...otherData];

  }

  isObject(value: any): boolean {
    return typeof value === 'object' && value !== null;
  }

  objectKeys(obj: any): string[] {
    return Object.keys(obj);
  }

  isArray(value: any): boolean {
    return Array.isArray(value);
  }

  async getAllModelsOfRun() {
    try {
      let models = await this.modelsService.getAllModels(
        this.site_id,
        this.project_id,
      );

      const { input_cols, output_cols, output_col } =
        this.mostRecentModel.model.configs;
      const filteredModels = models.filter(
        (model: any) =>
          (this.arraysMatch(model.model.configs.input_cols, input_cols) &&
            this.arraysMatch(model.model.configs.output_cols, output_cols)) ||
          (this.arraysMatch(model.model.configs.input_cols, input_cols) &&
            this.arraysMatch(model.model.configs.output_col, output_col)),
      );
      this.allModels = filteredModels;
      return this.allModels;
    } catch (error) {
      this.onTabLoaded();
      console.error('Error fetching Models:', error);
      this.errorHandlerService.handleError(error);
      return null;
    }
  }

  arraysMatch(arr1: string[] | string, arr2: string[] | string): boolean {
    if (!Array.isArray(arr1)) arr1 = [arr1];
    if (!Array.isArray(arr2)) arr2 = [arr2];

    if (arr1.length !== arr2.length) return false;

    const sortedArr1 = [...arr1].sort();
    const sortedArr2 = [...arr2].sort();
    return sortedArr1.every((value, index) => value === sortedArr2[index]);
  }

  keys(obj: any) {
    return Object.keys(obj);
  }

  isObj(value: any): boolean {
    return value && typeof value === 'object' && !Array.isArray(value);
  }

  getValue(data: any, key: string, subKey: string): any {
    return this.isObj(data[key])
      ? data[key][subKey]
      : subKey === 'accuracy'
        ? data[key]
        : '-';
  }

  isDecimal(value: any): boolean {
    return !isNaN(value) && value % 1 !== 0;
  }

  isRegressionModel(model: any) {
    if (!model.configs) {
      return true;
    }

    if ('problem_type' in model.configs) {
      return model.configs.problem_type === 'regression' ? true : false;
    } else {
      return true;
    }
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

  metricsOnChange(event: any) {
    this.selectedmetrics = event;
  }

  multipleOutputs(model: any) {
    if ('output_cols' in model.configs) {
      return (model.configs.output_cols.length > 1 && this.isObj(model.metrics['Mean Absolute Error (MAE)'])) ? true : false;
    } else {
      return false;
    }
  }
}
