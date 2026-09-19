import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { ModelsService } from 'src/app/pages/models/services/models.service';
import * as Plotly from 'plotly.js-dist-min';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ProblemType } from 'src/app/models/workflow-models';
import { ChangeDetectorRef } from '@angular/core';
@Component({
  selector: 'app-preview-model-comparision',
  templateUrl: './preview-model-comparision.component.html',
  styleUrls: ['./preview-model-comparision.component.less'],
})
export class PreviewModelComparisionComponent implements OnInit {
  firstModel: any;
  @Input() run_id: any;
  @Input() site_id: any;
  @Input() project_id: any;
  @Input() models: any;
  @Input() isScientificNotationEnabled: any;
  @Output() loaded = new EventEmitter<void>();
  errorLoadingGraphs = false;
  loader: boolean = true;

  selectedInputFeature: string = '';
  selectedOutputFeature: string = '';
  compareModel1: any;
  compareModel2: any;
  selectedModelForCompare: any[] = [];
  selectedData: string = '';
  compareVisualizationData: any[] = [];
  showDiv: boolean = true;
  columns = ['precision', 'recall', 'f1-score', 'support'];
  allModels: any[] = [];
  selectedmetrics: string = 'test';
  // isScientificNotationEnabled = false;
  constructor(
    private modelsService: ModelsService,
    private errorHandlerService: ErrorHandlerService,
    public workflowCanvasService: WorkflowCanvasService,
  ) { }

  onSelectionChangeForCompare() {
    if (
      this.selectedData &&
      this.selectedInputFeature &&
      this.selectedOutputFeature
    ) {
      this.compareModels();
    }
  }

  ngOnInit(): void {
    this.initializeModels();
  }

  async initializeModels(): Promise<void> {
    this.allModels = [];
    try {
      // For testing pupose don't remove commented lines - Taimoor
      // this.allModels = await this.getAllModelsByRunID();
      this.allModels = this.models;
      if (this.allModels.length > 0) {
        // if (!this.workflowCanvasService.IsVersionedWorkflow) {
        //   this.allModels = this.getMostRecentModels(this.allModels);
        // }        
        this.firstModel = this.allModels[0];
        this.selectedModelForCompare[0] = this.firstModel;
        this.compareModel1 = this.firstModel;

        const widgetType = this.firstModel.model.configs.widget_type;
        if (
          this.firstModel.model.configs.problem_type ===
          ProblemType.Regression ||
          [
            'RF',
            'LINEAR_REGRESSION',
            'LGBM',
            'NNFASTAI',
            'NN_TORCH',
            'XGBOOST',
            'CATBOOST',
            'KNEIGHBORS',
            'EXTRA_TREES',
          ].includes(widgetType)
        ) {
          this.defaultGraphPlot();
        } else {
          this.fetchConfusionMatrix();
        }
      }
    } catch (error) {
      this.loaded.emit();
      this.loader = false;
      console.error('Error fetching or initializing models:', error);
      this.errorHandlerService.handleError(error);
    }
  }

  async getAllModelsByRunID(): Promise<any[]> {
    try {
      return await this.modelsService.getModelResults(
        this.site_id,
        this.project_id,
        this.run_id,
      );
    } catch (error) {
      console.error('Error fetching model results:', error);
      this.loaded.emit();
      this.errorHandlerService.handleError(error);
      return [];
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

  fetchConfusionMatrix(): void {
    this.selectedModelForCompare.forEach((model) => {
      if (this.isClassificationModel(model.model)) {
        this.modelsService
          .getConfusionMetricsFileContent({
            path: model.model.visualizations[0],
            name: model.model.name,
          })
          .subscribe(
            (result) => {
              model.model.visualizations.imageUrl = result;
            },
            (error) => {
              console.error('Error fetching confusion metrics:', error);
              this.errorHandlerService.handleError(error);
            },
          );
      }
    });
    this.loaded.emit();
    this.loader = false;
  }

  defaultGraphPlot(): void {
    this.selectedData = 'all';
    this.selectedInputFeature = this.firstModel.model.configs.input_cols[0];
    this.selectedOutputFeature = this.firstModel.model.configs.output_cols
      ? this.firstModel.model.configs.output_cols[0]
      : this.firstModel.model.configs.output_col;
    this.compareModels();
  }

  isIncludedModelTypeWithZeroSplit(modelType: string): boolean {
    return (
      modelType == 'MPR' ||
      modelType == 'GPR' ||
      modelType == 'MOGPR' ||
      modelType == 'SVM Regressor' ||
      modelType == 'SVM Classifier' ||
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

  isArray(value: any): boolean {
    return Array.isArray(value);
  }

  hasOutputColsKey(): boolean {
    return 'output_cols' in this.selectedModelForCompare[0].model.configs;
  }

  getMetricsKeys(obj: any): string[] {
    return Object.keys(obj);
  }

  formatKey(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  isNumber(value: any): boolean {
    return !isNaN(parseFloat(value)) && isFinite(value);
  }

  getFilteredConfigKeys(configs: any): string[] {
    return Object.keys(configs).filter(
      (key) => key !== 'input_cols' && key !== 'output_cols',
    );
  }

  isObject(value: any): boolean {
    return value && typeof value === 'object' && !Array.isArray(value);
  }

  isDecimal(value: any): boolean {
    return !isNaN(value) && value % 1 !== 0;
  }

  isNotExcludedModelTypeWithZeroSplit(modelType: string): boolean {
    return (
      modelType !== 'SVM Regressor' &&
      modelType !== 'SVM Classifier'
    );
  }

  objectKeys(obj: any): string[] {
    return Object.keys(obj);
  }

  onModelChange(model: any, index: number) {
    this.selectedModelForCompare[index] = model;
    if (index === 0) {
      const currentModel = this.selectedModelForCompare[index];
      this.selectedOutputFeature = (this.selectedModelForCompare[index].model.configs.output_col) ? this.selectedModelForCompare[index].model.configs.output_col : this.selectedModelForCompare[index].model.configs.output_cols[0]
      this.selectedInputFeature = this.selectedModelForCompare[index].model.configs.input_cols[0];
      const filteredModels = this.selectedModelForCompare.filter(model =>
        model.model.configs.output_col === currentModel.model.configs.output_col ||
        this.areArraysEqual(model.model.configs.output_cols, currentModel.model.configs.output_cols)
      );

      if (filteredModels.length === 0) {
        this.selectedModelForCompare.splice(1, 1);
      } else {
        this.selectedModelForCompare = filteredModels;
      }
    }
    if (this.isRegressionModel(this.selectedModelForCompare[0].model)) {
      this.compareModels();
    } else if (
      this.isClassificationModel(this.selectedModelForCompare[0].model)
    ) {
      this.fetchConfusionMatrix();
    }
  }

  getFilteredModels(): any[] {
    return this.allModels.filter(
      (model) => !this.selectedModelForCompare.includes(model),
    );
  }

  async compareModels() {
    try {
      const siteId = '1';
      const comparisonObjects = [];
      for (const model of this.selectedModelForCompare) {
        var splitRatio;
        if (model.model.configs.split_ratio) {
          splitRatio = model.model.configs.split_ratio
        } else if (model.model.configs.hyper_params?.split_ratio) {
          splitRatio = model.model.configs.hyper_params.split_ratio
        } else {
          splitRatio = 0;
        }
        const comparisonObject = {
          model: model.model.type,
          summary_path: model.ml_model_file_path,
          data_path: model.dataset_path,
          chosen_column: this.selectedInputFeature,
          output_col: this.selectedOutputFeature,
          split_ratio: splitRatio,
          data_type: this.selectedData,
        };
        comparisonObjects.push(comparisonObject);
      }
      const obj = {
        models_config: comparisonObjects,
      };
      const result = await this.modelsService.compareModels(
        siteId,
        this.selectedModelForCompare[0].project_id,
        obj,
      );
      this.compareVisualizationData = result.comapre_visualization_data;

      if (
        this.compareVisualizationData &&
        this.compareVisualizationData.length > 0
      ) {
        if (document.readyState === 'complete') {
          await this.renderAllGraphs();
        } else {
          window.onload = async () => await this.renderAllGraphs();
        }
      } else {
        console.error('No visualization data available or data is not valid.');
        this.errorLoadingGraphs = true;
      }
    } catch (error) {
      console.error('Failed to compare models:', error);
      this.loaded.emit();
      this.loader = false;
      this.errorLoadingGraphs = true;
      this.errorHandlerService.handleError(error);
    }
  }

  async renderAllGraphs() {
    try {
      const promises = this.compareVisualizationData.map(
        async (model, index) => {
          if (this.selectedData == 'test' || this.selectedData == 'train') {
            await this.renderPredictionGraph(
              model.graph_data.prediction_parity,
              `prediction-parity-${index}`,
              index,
            );
            await this.renderResidualGraph(
              model.graph_data.chosen_residual,
              `chosen-residual-${index}`,
              index,
            );
          } else {
            await this.renderPredictionGraph(
              {
                target_value: model.graph_data.test_data.prediction_parity.target_value.concat(
                  model.graph_data.train_data.prediction_parity.target_value
                ),
                prediction_value: model.graph_data.test_data.prediction_parity.prediction_value.concat(
                  model.graph_data.train_data.prediction_parity.prediction_value
                ),
              },
              `prediction-parity-${index}`,
              index,
            );
            await this.renderResidualGraph(
              {
                chosen_feature_values: model.graph_data.test_data.chosen_residual.chosen_feature_values.concat(
                  model.graph_data.train_data.chosen_residual.chosen_feature_values
                ),
                residual_values: model.graph_data.test_data.chosen_residual.residual_values.concat(
                  model.graph_data.train_data.chosen_residual.residual_values
                ),
              },
              `chosen-residual-${index}`,
              index,
            );
          }
        },
      );

      await Promise.all(promises);
      this.loaded.emit();
      this.loader = false;
    } catch (error) {
      console.error('Error rendering graphs:', error);
      this.errorHandlerService.handleError(error);
      this.errorLoadingGraphs = true;
      this.loader = false;
      this.loaded.emit();
    }
  }

  renderPredictionGraph(
    data: any,
    elementId: string,
    graphIndex: number,
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const xValues = data.target_value;
      const yValues = data.prediction_value;
      const combinedValues = xValues.concat(yValues);
      const minValue = Math.min(...combinedValues);
      const maxValue = Math.max(...combinedValues);
      const buffer = (maxValue - minValue) * 0.05;

      const trace: Partial<Plotly.Data> = {
        x: xValues,
        y: yValues,
        mode: 'markers',
        type: 'scatter',
        marker: { color: 'teal' },
        hovertemplate: 'Actual: %{x}<br>Prediction: %{y}<extra></extra>',
      };

      const identityLine: Partial<Plotly.Data> = {
        x: [minValue, maxValue],
        y: [minValue, maxValue],
        mode: 'lines',
        type: 'scatter',
        line: { color: 'black', dash: 'dot' },
      };

      const layout: Partial<Plotly.Layout> = {
        xaxis: {
          title: 'Actual',
          range: [minValue - buffer, maxValue + buffer],
          zeroline: true,
          showgrid: true,
          showline: true,
          linewidth: 1,
          linecolor: 'black',
        },
        yaxis: {
          title: 'Prediction',
          range: [minValue - buffer, maxValue + buffer],
          zeroline: true,
          showgrid: true,
          showline: true,
          linewidth: 1,
          linecolor: 'black',
        },
        showlegend: false,
        margin: { l: 40, r: 40, t: 40, b: 40 },
        hovermode: 'closest',
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
      };

      Plotly.newPlot(elementId, [trace, identityLine], layout)
        .then((plot) => {
          plot.on('plotly_click', (data) => {
            const pointIndex = data.points[0].pointNumber;
            this.highlightGraphPair(pointIndex, graphIndex);
          });
          resolve();
        })
        .catch((error) => {
          reject(error);
        });
    });
  }

  renderResidualGraph(
    data: any,
    elementId: string,
    graphIndex: number,
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const featureValues = data.chosen_feature_values;
      const residuals = data.residual_values;
      const minX = Math.min(...featureValues);
      const maxX = Math.max(...featureValues);
      const minY = Math.min(...residuals);
      const maxY = Math.max(...residuals);
      const bufferX = (maxX - minX) * 0.05;
      const bufferY = (maxY - minY) * 0.05;

      const trace: Partial<Plotly.Data> = {
        x: featureValues,
        y: residuals,
        mode: 'markers',
        type: 'scatter',
        marker: { color: 'teal' },
        hovertemplate: 'Feature: %{x}<br>Residual: %{y}<extra></extra>',
      };

      const zeroLine: Partial<Plotly.Data> = {
        x: [minX, maxX],
        y: [0, 0],
        mode: 'lines',
        type: 'scatter',
        line: { color: 'black', dash: 'dot' },
      };

      const layout: Partial<Plotly.Layout> = {
        xaxis: {
          title: 'Feature Value',
          range: [minX - bufferX, maxX + bufferX],
          zeroline: true,
          showgrid: true,
          showline: true,
          linewidth: 1,
          linecolor: 'black',
        },
        yaxis: {
          title: 'Residual',
          range: [minY - bufferY, maxY + bufferY],
          zeroline: true,
          showgrid: true,
          showline: true,
          linewidth: 1,
          linecolor: 'black',
        },
        showlegend: false,
        margin: { l: 40, r: 40, t: 40, b: 40 },
        hovermode: 'closest',
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
      };

      Plotly.newPlot(elementId, [trace, zeroLine], layout)
        .then((plot) => {
          plot.on('plotly_click', (data) => {
            const pointIndex = data.points[0].pointNumber;
            this.highlightGraphPair(pointIndex, graphIndex);
          });
          resolve();
        })
        .catch((error) => {
          reject(error);
        });
    });
  }

  highlightGraphPair(selectedIndex: number, selectedGraphIndex: number) {
    const predictionId = `prediction-parity-${selectedGraphIndex}`;
    const residualId = `chosen-residual-${selectedGraphIndex}`;

    this.updateGraphHighlight(
      predictionId,
      this.compareVisualizationData[selectedGraphIndex].graph_data
        .prediction_parity.target_value,
      selectedIndex,
    );
    this.updateGraphHighlight(
      residualId,
      this.compareVisualizationData[selectedGraphIndex].graph_data
        .chosen_residual.chosen_feature_values,
      selectedIndex,
    );
  }

  updateGraphHighlight(elementId: string, values: any[], index: number) {
    const colors = new Array(values.length).fill('teal');
    colors[index] = 'red';
    const update = { marker: { color: colors } };
    Plotly.restyle(elementId, update).catch((err) => {
      console.error('Plotly restyle failed:', err),
        this.errorHandlerService.handleError(err);
    });
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
  isObj(value: any): boolean {
    return value && typeof value === 'object' && !Array.isArray(value);
  }
  keys(obj: any) {
    return Object.keys(obj);
  }

  multipleOutputs(model: any) {
    if ('output_cols' in model.configs) {
      return (model.configs.output_cols.length > 1 && this.isObj(model.metrics['Mean Absolute Error (MAE)'])) ? true : false;
    } else {
      return false;
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

  availableModels(index: number): any[] {
    if (index === 0) {
      return this.allModels.filter(
        (model) => model !== this.selectedModelForCompare[1],
      );
    } else if (index === 1) {
      if (this.selectedModelForCompare[0].model.configs.output_cols) {
        if (this.selectedModelForCompare[0].model.configs.output_cols.length > 1) {
          return this.allModels.filter((model) => {
            return (model !== this.selectedModelForCompare[0] && this.areArraysEqual(this.selectedModelForCompare[0].model.configs.output_cols, model.model.configs.output_cols))
          })
        } else if (this.selectedModelForCompare[0].model.configs.output_cols.length < 2) {
          return this.allModels.filter((model) => {
            return (model !== this.selectedModelForCompare[0] && this.selectedModelForCompare[0].model.configs.output_cols[0] == model.model.configs.output_col)
          })
        }
      } else {
        return this.allModels.filter((model) => {
          return (model !== this.selectedModelForCompare[0] && this.selectedModelForCompare[0].model.configs.output_col == model.model.configs.output_col) ||
            (this.selectedModelForCompare.length > 0 &&
              model.model.configs?.output_cols?.length > 0 &&
              this.selectedModelForCompare[0].model.configs.output_col === model.model.configs.output_cols[0])
        })
      }
    }
    return [];
  }

  areArraysEqual(arr1: any[], arr2: any[]): boolean {
    if (!Array.isArray(arr1) || !Array.isArray(arr2)) {
      return false;
    }
    arr1 = arr1.slice().sort();
    arr2 = arr2.slice().sort();

    for (let i = 0; i < arr1.length; i++) {
      if (arr1[i] !== arr2[i]) {
        return false;
      }
    }
    return true;
  }

  metricsOnChange(event: any) {
    this.selectedmetrics = event;
  }
}
