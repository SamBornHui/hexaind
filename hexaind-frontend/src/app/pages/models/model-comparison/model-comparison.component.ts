import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { ModelsService } from '../services/models.service';
import { ToastrService } from 'ngx-toastr';
import {
  ConfigService,
  WorkflowCanvasService,
} from '../../workflow-designer/workflow-canvas.service';
import * as Plotly from 'plotly.js-dist-min';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { ProblemType } from 'src/app/models/workflow-models';

@Component({
  selector: 'app-model-comparison',
  templateUrl: './model-comparison.component.html',
  styleUrls: ['./model-comparison.component.less'],
})
export class ModelComparisonComponent implements OnInit {
  @Input() compareSelectedModel: any;
  @Output() compareModelEvent = new EventEmitter();
  selectedData: string | undefined;
  selectedInputFeature: string | undefined;
  selectedOutputFeature: string | undefined;
  compareVisualizationData: any[] = [];
  columns = ['precision', 'recall', 'f1-score', 'support'];

  constructor(
    private modelsService: ModelsService,
    private toaster: ToastrService,
    private configService: ConfigService,
    public workflowCanvasService: WorkflowCanvasService,
    private errorHandlerService: ErrorHandlerService,
  ) { }

  ngOnInit() {
    if (this.compareSelectedModel) {
      if (
        this.isRegressionModel(
          this.getFirstModel(this.compareSelectedModel).model,
        )
      ) {
        this.defaultGraphPlot(this.compareSelectedModel);
      } else if (
        this.isClassificationModel(
          this.getFirstModel(this.compareSelectedModel).model,
        )
      ) {
        this.fetchConfusionMatrix();
      }
    }
  }

  fetchConfusionMatrix(): void {
    this.compareSelectedModel.forEach((model: any) => {
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
            },
          );
      }
    });
  }

  goToModelPage() {
    this.compareModelEvent.emit(false);
  }

  getMetricsKeys(obj: any): string[] {
    return Object.keys(obj);
  }

  formatKey(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  isObject(value: any): boolean {
    return value && typeof value === 'object' && !Array.isArray(value);
  }

  objectKeys(obj: any): string[] {
    return Object.keys(obj);
  }

  getFilteredConfigKeys(configs: any): string[] {
    return Object.keys(configs).filter(
      (key) => key !== 'input_cols' && key !== 'output_cols',
    );
  }

  isArray(value: any): boolean {
    return Array.isArray(value);
  }

  onSelectionChange() {
    if (
      this.selectedData &&
      this.selectedInputFeature &&
      this.selectedOutputFeature
    ) {
      this.compareModels();
    }
  }

  modelType() {
    if (this.compareSelectedModel.length > 0) {
      var modelType = this.compareSelectedModel[0].model.type;
      return modelType;
    }
    return null;
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
      modelType == 'GPR' || modelType == 'MOGPR' || modelType == 'SVM Regressor' || modelType == 'WeightedEnsemble_L2' ||
      modelType == 'GPC' ||
      modelType == 'MPR' ||
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

  hasOutputColsKey(): boolean {
    return (
      'output_cols' in
      this.getFirstModel(this.compareSelectedModel).model.configs
    );
  }

  isNumber(value: any): boolean {
    return !isNaN(parseFloat(value)) && isFinite(value);
  }

  getFirstModel(models: any[]): any {
    if (models.length > 0) {
      return models[0];
    }
    return null;
  }

  defaultGraphPlot(models: any[]): void {
    const firstModel = this.getFirstModel(models);
    if (this.isIncludedModelType(firstModel.model.type)) {
      this.selectedData = 'all';
      this.selectedInputFeature = firstModel.model.configs.input_cols[0];
      this.selectedOutputFeature = (firstModel.model.configs.output_cols) ? firstModel.model.configs.output_cols[0] : firstModel.model.configs.output_col;
      this.compareModels();
    } else {
    }
  }

  async compareModels() {
    try {
      const siteId = '1';
      const comparisonObjects = [];
      for (const model of this.compareSelectedModel) {
        const comparisonObject = {
          model: model.model.type,
          summary_path: model.ml_model_file_path,
          data_path: model.dataset_path,
          chosen_column: this.selectedInputFeature,
          output_col: this.selectedOutputFeature,
          split_ratio: (model.model.configs.split_ratio) ? model.model.configs.split_ratio : 0,
          data_type: this.selectedData,
        };
        comparisonObjects.push(comparisonObject);
      }
      const obj = {
        models_config: comparisonObjects,
      };
      const result = await this.modelsService.compareModels(
        siteId,
        this.compareSelectedModel[0].project_id,
        obj,
      );
      this.compareVisualizationData = result.comapre_visualization_data;

      if (
        this.compareVisualizationData &&
        this.compareVisualizationData.length > 0
      ) {
        if (document.readyState === 'complete') {
          this.renderAllGraphs();
        } else {
          window.onload = () => this.renderAllGraphs();
        }
      } else {
        console.error('No visualization data available or data is not valid.');
      }
    } catch (error) {
      console.error('Failed to compare models:', error);
      this.errorHandlerService.handleError(error);
    }
  }

  renderAllGraphs() {
    this.compareVisualizationData.forEach(async (model, index) => {
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
    });
  }

  renderPredictionGraph(data: any, elementId: string, graphIndex: number) {
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

    Plotly.newPlot(elementId, [trace, identityLine], layout).then((plot) => {
      plot.on('plotly_click', (data) => {
        const pointIndex = data.points[0].pointNumber;
        this.highlightGraphPair(pointIndex, graphIndex);
      });
    });
  }

  renderResidualGraph(data: any, elementId: string, graphIndex: number) {
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

    Plotly.newPlot(elementId, [trace, zeroLine], layout).then((plot) => {
      plot.on('plotly_click', (data) => {
        const pointIndex = data.points[0].pointNumber;
        this.highlightGraphPair(pointIndex, graphIndex);
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

  truncateModelName(name: string): string {
    return name.length > 5 ? name.substring(0, 10) + '...' : name;
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

  isDecimal(value: any): boolean {
    return !isNaN(value) && value % 1 !== 0;
  }

  keys(obj: any) {
    return Object.keys(obj);
  }

  isObj(value: any): boolean {
    return value && typeof value === 'object' && !Array.isArray(value);
  }

  multipleOutputs(model: any) {
    if ('output_cols' in model.configs) {
      return (model.configs.output_cols.length > 1 && this.isObj(model.metrics['Mean Absolute Error (MAE)'])) ? true : false;
    } else {
      return false;
    }
  }

}
