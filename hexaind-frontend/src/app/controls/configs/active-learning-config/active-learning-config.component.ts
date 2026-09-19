import { Component, OnInit, ViewChild, ElementRef, Input } from '@angular/core';
import {
  ConfigService,
  WorkflowCanvasService,
} from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { ActivatedRoute } from '@angular/router';
import {
  DataCopyWidgetConfig,
  InputOutputConfig,
  LocalFileConfiguration,
  ActiveLearningWidgetConfig,
  Widget,
  WidgetType,
  LoopEndWidgetConfig,
  OnLoopTerminationCriteriaConfig,
} from 'src/app/models/workflow-models';
import { ActiveLearningConfigService } from './active-learning-config.service';
import { MatDialog } from '@angular/material/dialog';
import { MatTableDataSource } from '@angular/material/table';
import { DataPreviewComponent } from 'src/app/dialogs/data-preview/data-preview.component';
import { SettingsComponent } from '../settings/settings.component';
import { ToastrService } from 'ngx-toastr';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { ApiService } from 'src/app/services/api.service';

@Component({
  selector: 'app-active-learning-config',
  templateUrl: './active-learning-config.component.html',
  styleUrls: ['./active-learning-config.component.less'],
})
export class ActiveLearningConfigComponent {
  @Input() widgetName: string = '';
  @Input() widgetUrn: string = '';
  @Input() siteId: string = '';
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  @ViewChild('optscatterplot')
  public optscatterplot!: ElementRef;
  featureColumns: string[] = ['select', 'name', 'input', 'output'];
  inputColumns: string[] = ['inputName', 'min', 'max'];
  outputColumns: string[] = ['outputName', 'min', 'max', 'threshold'];
  initiateSpinner = false;
  datasetFeatures = [
    // 'dcpSpacerThickness',
    // 'ppSpacerThickness',
    // 'ipsPressure',
    // 'upPressure',
    // 'frictionCf',
    // 'bucklingPressure',
    // 'maxThinning',
  ];
  inputFeatures = [
    'dcpSpacerThickness',
    'ppSpacerThickness',
    'ipsPressure',
    'upPressure',
    'frictionCf',
    'bucklingPressure',
    'maxThinning',
  ];
  outcomeConstraints: boolean = true;
  inputValue: any;
  assignOperators: any = ['>=', '<='];
  operator: any = '';
  executionProgress: boolean = true;
  selectedDataset: any = {
    features: [],
    features_io_info: [],
    features_meta_data: {},
  };

  workflowDetail: any = {
    _id: '1231',
    batch_size_input: '1',
    num_iterations: '1',
    config: {
      inputFeatures: [],
      outputFeatures: [],
      unselectedFeatures: [],
    },
    selectedColorByOpt: 'trial_index_visual',
  };
  selectAll: boolean = true;
  findObject: any;
  plotlyPlot: any;
  validationCheck: boolean = true;
  updateFlag: boolean = true;
  percentageArray = [
    0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90,
    95, 100,
  ];
  filteredModelList: any = [];
  selected_connection = '';
  selectedOption = '';
  prefix: any;
  lsDynaprefix: any;
  connectionDetails: any;
  connectionseData = [{ _id: '1', connectionName: 'rescale' }];
  unselectedFeature: string | undefined;

  changeMade: boolean = false;
  inputChangeMade: boolean = false;
  outputChangeMade: boolean = false;
  changeSetting: boolean = false;
  config: ActiveLearningWidgetConfig | undefined;
  configCache: ActiveLearningWidgetConfig | undefined;
  outputName: string | undefined = undefined;
  inputName: string | undefined = undefined;
  plotConfig: any;
  output_features: any;
  selectedFeatures: any;
  outcome_constraints_variables_list: any;
  widgetControl: WidgetControl | undefined;
  outcome_constraints_variable: any;
  layout: any = {};
  data: any = {
    x: '',
    y: '',
    text: '',
    customdata: '',
    mode: '',
    type: '',
    marker: {
      color: '',
      size: '',
      colorscale: '',
      colorbar: '',
      opacity: '',
      line: { color: '', width: '' },
    },
    showlegend: false,
    hovertemplate: '',
  };
  widgetdataInformation = {};
  site_id: string = '1';
  project_id: any;
  module_list: any;
  inputWidgets: Widget[] = [];
  inputURN: Widget[] = [];
  widget: any;
  dataset_id: string | undefined;
  selectedInputWidget: Widget | undefined = undefined;
  selectedInputWidgetIndex: number = -1;
  prevWidgetURN: any;
  datasetIDFetched = false;
  constructor(
    private editWorkflowService: WorkflowCanvasService,
    private activeLearningConfigService: ActiveLearningConfigService,
    private route: ActivatedRoute,
    private dialog: MatDialog,
    public sharedDataService: SharedDataService,
    public workflowCanvasService: WorkflowCanvasService,
    public toaster: ToastrService,
    private configService: ConfigService,
    private apiService: ApiService,
  ) {
    if (!this.editWorkflowService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.editWorkflowService.selectedWidgetControl;
    this.widget = this.widgetControl.Widget as Widget;

    if (this.widgetControl && this.widgetControl.Widget.config) {
      this.config = this.widgetControl.Widget
        .config as ActiveLearningWidgetConfig;
      this.config.widget_type = WidgetType.ACTIVE_LEARNING;
      this.configCache = JSON.parse(JSON.stringify(this.config));
    }

    if (this.widgetControl.Widget.outputs.length) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
      // var urn = this.widgetControl.Widget.inputs[0].urn;
    }
    if (this.widgetControl.Widget.inputs.length) {
      this.inputName = this.widgetControl.Widget.inputs[0].name;
    }
  }

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      this.project_id = params['projectId'];
    });

    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.editWorkflowService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );
      const urnsInWidgets =
        this.workflowCanvasService.SelectedWorkflow?.widgets.map(
          (widget) => widget.urn,
        ) || [];
      this.inputWidgets = this.inputWidgets.filter((widget) =>
        urnsInWidgets.includes(widget.outputs[0]['urn']),
      );

      if (this.inputWidgets.length > 0) {
        this.inputURN = this.editWorkflowService.findConnectedWidgets(
          this.widgetControl?.Widget.inputs[0]?.urn ?? '',
        );
        if (this.inputURN.length > 0) {
          this.datasetIDFetched = true;
          var configuration = this.inputURN[0].config as DataCopyWidgetConfig;
          var source = configuration?.source
            .configuration as LocalFileConfiguration;
          var dataset_id = source?.dataset_id;
          this.dataset_id = source?.dataset_id;

          if (
            this.configCache &&
            this.configCache['features_detail'] &&
            this.configCache['features_detail'].length !== 0
          ) {
            this.getTheFeaturesMetaData(dataset_id);
          } else {
            this.getDatasetStats(dataset_id);
          }
        }
      } else {
        this.datasetIDFetched = false;
      }

      // Remove any widgets that dont have outputs.
      if (this.inputWidgets && this.inputWidgets.length > 0) {
        this.inputWidgets = this.inputWidgets.filter(
          (widget) => widget.outputs.length > 0,
        );
        this.getAllModules();
        this.loadSelectedInputWidget();
      }
    }
    this.loadFeatures();
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  loadFeatures() {
    this.widgetdataInformation = {
      type: this.widgetControl?.Widget.type + ' widget',
      description:
        'Active Learning widget allows supported HEXAIND 3.0 users to perform active learning on tabular datasets',
      version: this.configCache?.version,
    };
  }

  loadSelectedInputWidget() {
    this.selectedInputWidget = undefined;
    if (!this.widgetControl) {
      return;
    }
    if (this.widgetControl.Widget.inputs.length > 0) {
      this.selectedInputWidget = this.inputWidgets.find(
        (t) => t.urn === this.widgetControl?.Widget.inputs[0].urn,
      );
    } else {
      if (this.inputWidgets.length === 1) {
        this.selectedInputWidget = this.inputWidgets[0];
        this.onInputSave();
      }
    }
    if (this.selectedInputWidget && this.datasetIDFetched == false) {
      let selectedWidgetUrn = this.selectedInputWidget.urn;
      this.selectedInputWidgetIndex = this.inputWidgets.findIndex(
        (widget) => widget.urn === selectedWidgetUrn,
      );
      this.prevWidgetURN = this.inputWidgets[this.selectedInputWidgetIndex].urn;
      this.getDataSetId();
    }
  }

  async getDataSetId() {
    if (
      this.configService.SelectedSiteId &&
      this.configService.SelectedProjectId &&
      this.workflowCanvasService.SelectedWorkflowSession?._id &&
      this.prevWidgetURN
    ) {
      this.apiService
        .GetPreviousTabularWidgetResults(
          this.configService.SelectedSiteId,
          this.configService.SelectedProjectId,
          this.workflowCanvasService.SelectedWorkflowSession?._id,
          this.prevWidgetURN,
        )
        .then((prevWidgetResults: any) => {
          if (this.selectedInputWidget) {
            this.dataset_id =
              this.workflowCanvasService.getDataSetIdFromResults(
                prevWidgetResults,
                this.selectedInputWidget,
              );
            if (this.dataset_id) {
              this.getTheFeaturesMetaData(this.dataset_id);
              return true;
            }
          }
          return false;
        })
        .catch((error) => {
          this.toaster.info(
            'Please execute the previous widget to see the parameters',
          );
        });
    }
  }

  getDatasetStats(dataset_id: string | undefined) {
    this.selectedDataset.features_io_info = [];
    if (dataset_id !== undefined) {
      this.activeLearningConfigService
        .getDataset(this.site_id, this.project_id, dataset_id)
        .subscribe({
          next: (response) => {
            if (response) {
              var data = response.statistics;
              const columnNames = data[0].column_names;
              this.datasetFeatures = columnNames;
              this.selectedDataset.features = columnNames;
              this.datasetFeatures.forEach((element: string) => {
                let feature = {
                  name: element,
                  dataType: 'Numerical',
                  selected: true,
                  input: true,
                  output: false,
                };
                if (!Array.isArray(this.selectedDataset.features_io_info)) {
                  this.selectedDataset.features_io_info = [];
                }
                this.selectedDataset.features_io_info.push(feature);
              });
              this.selectedDataset.features_io_info = new MatTableDataSource(
                this.selectedDataset.features_io_info,
              );

              const rowNames = data[0].row_names;
              const columns_data = data[0].data;
              columnNames.forEach(
                (columnName: string | number, columnIndex: string | number) => {
                  const columnStats: any = {};
                  rowNames.forEach(
                    (rowName: string | number, rowIndex: string | number) => {
                      columnStats[rowName] =
                        columns_data[columnIndex][rowNames.indexOf(rowName)];
                    },
                  );
                  columnStats.name = columnName;
                  columnStats.type = 'Numerical';
                  this.selectedDataset.features_meta_data[columnName] =
                    columnStats;
                },
              );
            }
          },
          error: (error) => {
            const errorMessage =
              error?.error?.message ||
              error?.message ||
              'An unexpected error occurred';
            this.toaster.error(errorMessage, 'ERROR', {
              positionClass: 'custom-toast-position',
            });
          },
        });
    }
  }

  getTheFeaturesMetaData(dataset_id: string | undefined) {
    if (dataset_id !== undefined) {
      this.activeLearningConfigService
        .getDataset(this.site_id, this.project_id, dataset_id)
        .subscribe({
          next: (response) => {
            if (response) {
              var data = response.statistics;
              const columnNames = data[0].column_names;
              const rowNames = data[0].row_names;
              const columns_data = data[0].data;
              columnNames.forEach(
                (columnName: string | number, columnIndex: string | number) => {
                  const columnStats: any = {};
                  rowNames.forEach(
                    (rowName: string | number, rowIndex: string | number) => {
                      columnStats[rowName] =
                        columns_data[columnIndex][rowNames.indexOf(rowName)];
                    },
                  );
                  columnStats.name = columnName;
                  columnStats.type = 'Numerical';
                  this.selectedDataset.features_meta_data[columnName] =
                    columnStats;
                },
              );
              const outputNames = this.configCache?.features_detail.map(
                (item: any) => item.name,
              );
              const matchingKeys = Object.keys(
                this.selectedDataset.features_meta_data,
              ).filter((key) => outputNames?.includes(key));
              if (matchingKeys.length > 0) {
                this.selectedDataset['features_io_info'] =
                  new MatTableDataSource(this.configCache?.['features_detail']);
                this.setWorkflowDetail();
              } else {
                this.getDatasetStats(this.dataset_id);
              }
            }
          },
          error: (error) => {
            const errorMessage =
              error?.error?.message ||
              error?.message ||
              'An unexpected error occurred';
            this.toaster.error(errorMessage, 'ERROR', {
              positionClass: 'custom-toast-position',
            });
          },
        });
    }
  }

  changedInputOutput(feature: any, type: String, event: any) {
    if (type == 'input') {
      if (feature.input) {
        feature.input = true;
        feature.output = false;
      } else {
        var outputs = this.selectedDataset.features_io_info.data.filter(
          (val: any) => val['output'] === true,
        );
        if (outputs.length > 1) {
          feature.input = true;
          feature.output = false;
          event.source.checked = false;
        } else {
          feature.input = false;
          feature.output = true;
        }
      }
    } else if (type == 'output') {
      var outputs = this.selectedDataset.features_io_info.data.filter(
        (val: any) => val['output'] === true,
      );
      if (feature.output) {
        if (outputs.length > 2) {
          feature.input = true;
          feature.output = false;
          event.source.checked = false;
        } else {
          feature.input = false;
          feature.output = true;
        }
      } else {
        feature.input = true;
        feature.output = false;
      }
    }
    this.changeFeaturesConfig();
  }

  changeFeaturesConfig() {
    for (
      let index = 0;
      index < this.selectedDataset.features_io_info.data.length;
      index++
    ) {
      if (this.selectedDataset.features_io_info.data[index].selected == false) {
        this.selectedDataset.features_io_info.data[index].input = false;
        this.selectedDataset.features_io_info.data[index].output = false;
      } else if (
        this.selectedDataset.features_io_info.data[index].selected == true &&
        this.selectedDataset.features_io_info.data[index].output == false
      ) {
        this.selectedDataset.features_io_info.data[index].input = true;
      }
    }

    var inputs = this.selectedDataset.features_io_info.data.filter(
      (val: any) =>
        val['selected'] === true &&
        val['input'] === true &&
        val['dataType'] == 'Numerical',
    );

    var outputs = this.selectedDataset.features_io_info.data.filter(
      (val: any) =>
        val['selected'] === true &&
        val['output'] === true &&
        val['dataType'] == 'Numerical',
    );

    var remainingFeatures = this.selectedDataset.features_io_info.data.filter(
      (val: any) =>
        val['selected'] == false ||
        (val['selected'] === true &&
          val['input'] === false &&
          val['output'] === false &&
          val['dataType'] == 'Numerical'),
    );
    var inconsistantFeature = inputs.filter(
      (val: any) => val['name'] === this.outcome_constraints_variable,
    );
    if (inconsistantFeature.length > 0) {
      this.outcome_constraints_variable = '';
      this.operator = '';
      this.inputValue = '';
    }
    this.outcome_constraints_variables_list =
      this.selectedDataset.features_io_info.data
        .filter(
          (val: any) =>
            val['selected'] === false && val['dataType'] == 'Numerical',
        )
        .map((val: any) => val['name']);
    var unselectedFeatures: any = [];
    if (remainingFeatures.length > 0) {
      for (var i = 0; i < remainingFeatures.length; i++) {
        var index = this.workflowDetail.config.unselectedFeatures.findIndex(
          (val: any) => val['name'] == remainingFeatures[i].name,
        );
        if (index == -1) {
          unselectedFeatures.push({
            name: remainingFeatures[i].name,
          });
        } else {
          unselectedFeatures.push(
            this.workflowDetail.config.unselectedFeatures[index],
          );
        }
        if (i == remainingFeatures.length - 1) {
          this.workflowDetail.config.unselectedFeatures = unselectedFeatures;
        }
      }
    } else {
      this.workflowDetail.config.unselectedFeatures = unselectedFeatures;
    }

    var inputFeatures: any = [];
    if (inputs.length > 0) {
      for (var i = 0; i < inputs.length; i++) {
        var index = this.workflowDetail.config.inputFeatures.findIndex(
          (val: any) => val['name'] == inputs[i].name,
        );
        if (index == -1) {
          inputFeatures.push({
            name: inputs[i].name,
            min: '',
            max: '',
          });
        } else {
          inputFeatures.push(this.workflowDetail.config.inputFeatures[index]);
        }
        if (i == inputs.length - 1) {
          this.workflowDetail.config.inputFeatures = inputFeatures;
        }
      }
    } else {
      this.workflowDetail.config.inputFeatures = inputFeatures;
    }
    var outputFeatures: any = [];
    if (outputs.length > 0) {
      for (var i = 0; i < outputs.length; i++) {
        var index = this.workflowDetail.config.outputFeatures.findIndex(
          (val: any) => val['name'] == outputs[i].name,
        );
        if (index == -1) {
          outputFeatures.push({
            name: outputs[i].name,
            min_max_value: '',
            threshold: '',
            connector: 'api',
            objective_url: '',
            model: '',
          });
        } else {
          outputFeatures.push(this.workflowDetail.config.outputFeatures[index]);
        }
        if (i == outputs.length - 1) {
          this.workflowDetail.config.outputFeatures = outputFeatures;
        }
      }
    } else {
      this.workflowDetail.config.outputFeatures = outputFeatures;
    }
    this.changeMade = true;
    this.saveWorkflow();
  }

  onInputChange(event: any) {
    this.saveWorkflow();
  }

  getInputMax(input: any) {
    return input.max;
  }

  setInputMax(input: any, value: any) {
    input.max = value;
    this.changeMade = true;
    this.saveWorkflow();
  }
  getInputMin(input: any) {
    return input.min;
  }

  setInputMin(input: any, value: any) {
    input.min = value;
    this.changeMade = true;
    this.saveWorkflow();
  }

  getOutputThreshold(output: any) {
    return output.threshold;
  }

  setOutputThreshold(output: any, value: any) {
    output.threshold = value;
    this.saveWorkflow();
  }

  getIterations(): number {
    const endLoopConfig =
      this.workflowCanvasService.findConnectedByWidgetType('LOOP_END');
    if (endLoopConfig.length > 0) {
      const loopEndConfig = endLoopConfig[0].config as LoopEndWidgetConfig;
      const terminationConfig =
        loopEndConfig.loop_end_config as OnLoopTerminationCriteriaConfig;
      terminationConfig.loop_count =
        Number(this.configCache!.num_iterations) + 1;
    }
    return this.configCache!.num_iterations;
  }

  setIterations(value: number) {
    this.configCache!.num_iterations = value;
    const endLoopConfig =
      this.workflowCanvasService.findConnectedByWidgetType('LOOP_END');

    if (endLoopConfig.length > 0) {
      const loopEndConfig = endLoopConfig[0].config as LoopEndWidgetConfig;
      const terminationConfig =
        loopEndConfig.loop_end_config as OnLoopTerminationCriteriaConfig;
      terminationConfig.loop_count = Number(value) + 1;
    }
    this.changeMade = true;
  }

  getBatchSize() {
    return this.configCache!.batch_size;
  }

  setBatchSize(value: any) {
    this.configCache!.batch_size = value;
    this.changeMade = true;
  }

  updateMinMax(val: any, index: any) {
    this.workflowDetail.config.outputFeatures[index].min_max_value = val;
    this.changeMade = true;
  }

  selectUnselectFeatures() {
    this.changeMade = true;
    for (
      var i = 0;
      i < this.selectedDataset.features_io_info.data.length;
      i++
    ) {
      this.selectedDataset.features_io_info.data[i].selected = this.selectAll
        ? true
        : false;
      if (i == this.selectedDataset.features_io_info.data.length - 1) {
        this.changeFeaturesConfig();
      }
    }

    this.selectedFeatures = this.selectedDataset.features_io_info.data.filter(
      (val: any) => val['selected'] === true,
    );
    this.changeMade = true;
  }

  makeApiSelectedOutput(event: any, connection: any) {
    for (var i = 0; i < this.workflowDetail.config.outputFeatures.length; i++) {
      this.workflowDetail.config.outputFeatures[i].objective_url =
        connection.value;
    }
  }

  getAutoFilledValues(percentage: number) {
    this.workflowDetail.config.inputFeatures =
      this.selectedDataset.features_io_info.data.filter(
        (val: any) =>
          val['selected'] === true &&
          val['input'] === true &&
          val['dataType'] == 'Numerical',
      );

    for (var i = 0; i < this.workflowDetail.config.inputFeatures.length; i++) {
      const featureName =
        this.workflowDetail['config']['inputFeatures'][i]['name'];
      const metaData = this.selectedDataset['features_meta_data'][featureName];

      this.workflowDetail.config.inputFeatures[i].min = metaData['min'];

      if (metaData['min'] === metaData['max']) {
        if (metaData['min'] === 0) {
          this.workflowDetail.config.inputFeatures[i].max =
            0.0001 * (1 + percentage / 100);
          this.workflowDetail.config.inputFeatures[i].min = 0;
        } else {
          const adjustedValue = metaData['min'] * (1 + percentage / 100);
          this.workflowDetail.config.inputFeatures[i].max =
            adjustedValue + adjustedValue * 0.0001;
          this.workflowDetail.config.inputFeatures[i].min = adjustedValue;
        }
      } else {
        this.workflowDetail.config.inputFeatures[i].min =
          metaData['min'] * (1 + percentage / 100);
        this.workflowDetail.config.inputFeatures[i].max =
          metaData['max'] * (1 + percentage / 100);
      }

      this.workflowDetail.config.inputFeatures[i].min = parseFloat(
        this.workflowDetail.config.inputFeatures[i].min.toString(),
      );
      this.workflowDetail.config.inputFeatures[i].max = parseFloat(
        this.workflowDetail.config.inputFeatures[i].max.toString(),
      );
    }

    this.changeMade = true;
  }

  drawOptimizationScatterPlot() {
    this.findObject = [
      {
        dcpSpacerThickness: '0.177586611',
        ppSpacerThickness: '0.164183707',
        ipsPressure: '193.3498952',
        upPressure: '86.3233632',
        frictionCf: '0.056472611',
        bucklingPressure: '103.6842149',
        maxThinning: '12.75395926',
        'Pareto-optimal_num': '0.0',
        'Pareto-optimal': 'False',
        trial_index_visual: '1.0',
      },
      {
        dcpSpacerThickness: '0.191568904',
        ppSpacerThickness: '0.154802862',
        ipsPressure: '108.5796799',
        upPressure: '121.1084129',
        frictionCf: '0.083372115',
        bucklingPressure: '116.1550504',
        maxThinning: '11.31078209',
        'Pareto-optimal_num': '0.0',
        'Pareto-optimal': 'False',
        trial_index_visual: '2.0',
      },
      {
        dcpSpacerThickness: '0.181921353',
        ppSpacerThickness: '0.148786221',
        ipsPressure: '180.6815391',
        upPressure: '128.6842001',
        frictionCf: '0.097818147',
        bucklingPressure: '107.552194',
        maxThinning: '13.81042524',
        'Pareto-optimal_num': '0.0',
        'Pareto-optimal': 'False',
        trial_index_visual: '3.0',
      },
      {
        dcpSpacerThickness: '0.18475312',
        ppSpacerThickness: '0.15588516',
        ipsPressure: '121.4134899',
        upPressure: '96.68034591',
        frictionCf: '0.038094117',
        bucklingPressure: '112.6485747',
        maxThinning: '9.511406483',
        'Pareto-optimal_num': '0.0',
        'Pareto-optimal': 'False',
        trial_index_visual: '4.0',
      },
      {
        dcpSpacerThickness: '0.174693048',
        ppSpacerThickness: '0.162807693',
        ipsPressure: '160.3373854',
        upPressure: '68.76961362',
        frictionCf: '0.023746368',
        bucklingPressure: '106.2568831',
        maxThinning: '11.19054575',
        'Pareto-optimal_num': '0.0',
        'Pareto-optimal': 'False',
        trial_index_visual: '5.0',
      },
      {
        dcpSpacerThickness: '0.180962997',
        ppSpacerThickness: '0.164242946',
        ipsPressure: '119.1378274',
        upPressure: '78.2290753',
        frictionCf: '0.091521471',
        bucklingPressure: '109.2514938',
        maxThinning: '12.38082634',
        'Pareto-optimal_num': '0.0',
        'Pareto-optimal': 'False',
        trial_index_visual: '6.0',
      },
      {
        dcpSpacerThickness: '0.191218513',
        ppSpacerThickness: '0.159630591',
        ipsPressure: '115.9705921',
        upPressure: '114.2096984',
        frictionCf: '0.07654827',
        bucklingPressure: '114.4359374',
        maxThinning: '11.18121744',
        'Pareto-optimal_num': '0.0',
        'Pareto-optimal': 'False',
        trial_index_visual: '7.0',
      },
      {
        dcpSpacerThickness: '0.181359186',
        ppSpacerThickness: '0.155306702',
        ipsPressure: '141.5679914',
        upPressure: '95.71150572',
        frictionCf: '0.029055712',
        bucklingPressure: '111.0704553',
        maxThinning: '10.44669986',
        'Pareto-optimal_num': '0.0',
        'Pareto-optimal': 'False',
        trial_index_visual: '8.0',
      },
      {
        dcpSpacerThickness: '0.189235493',
        ppSpacerThickness: '0.154858152',
        ipsPressure: '112.804518',
        upPressure: '112.8826827',
        frictionCf: '0.064341464',
        bucklingPressure: '114.9122441',
        maxThinning: '10.78615525',
        'Pareto-optimal_num': '0.0',
        'Pareto-optimal': 'False',
        trial_index_visual: '9.0',
      },
      {
        dcpSpacerThickness: '0.192',
        ppSpacerThickness: '0.154680416',
        ipsPressure: '104.329415',
        upPressure: '129.409584',
        frictionCf: '0.1',
        bucklingPressure: '117.4828124',
        maxThinning: '11.98608187',
        'Pareto-optimal_num': '0.0',
        'Pareto-optimal': 'False',
        trial_index_visual: '10.0',
      },
      {
        dcpSpacerThickness: '0.18703340886539468',
        ppSpacerThickness: '0.15585914707066248',
        ipsPressure: '116.54374252443277',
        upPressure: '104.5357588079927',
        frictionCf: '0.04482280803176221',
        bucklingPressure: '115.3431036192',
        maxThinning: '9.803259357',
        'Pareto-optimal_num': '0.0',
        'Pareto-optimal': 'False',
        trial_index_visual: '11.0',
      },
    ];

    var completedData = this.findObject;

    let x = completedData.map(
      (val: { [x: string]: any }) => val[this.workflowDetail.selectedOUT_X],
    );
    let y = completedData.map(
      (val: { [x: string]: any }) => val[this.workflowDetail.selectedOUT_Y],
    );

    let feature: any = [];
    let feature2: any = [];
    if (
      this.workflowDetail.selectedColorByOpt != '' &&
      this.findObject.length > 0
    ) {
      if (this.workflowDetail.selectedColorByOpt == 'Pareto-optimal') {
        feature = completedData.map(
          (val: { [x: string]: any }) => val['Pareto-optimal_num'],
        );
        feature2 = completedData.map(
          (val: { [x: string]: any }) => val['trial_index_visual'],
        );
        for (let h = 0; h < feature.length; h++) {
          feature[h] = Math.round(feature[h]);
          if (feature[h] === 1) {
            feature[h] = 'True';
          } else if (feature[h] === 0) {
            feature[h] = 'False';
          } else {
            feature[h] = 'Outside constraints';
          }
        }
        for (let i = 0; i < feature2.length; i++) {
          feature2[i] = Math.round(feature2[i]);
        }
      } else {
        feature = completedData.map(
          (val: { [x: string]: any }) => val['Pareto-optimal'],
        );
        feature2 = completedData.map(
          (val: { [x: string]: any }) => val['trial_index_visual'],
        );
        for (let i = 0; i < feature2.length; i++) {
          feature2[i] = Math.round(feature2[i]);
        }
      }
    }
    var xLabelText = this.workflowDetail.selectedOUT_X;
    var yLabelText = this.workflowDetail.selectedOUT_Y;
    //  axisTicks
    const axmin_x = Math.min.apply(Math, x);
    const axmax_x = Math.max.apply(Math, x);
    const axmin_y = Math.min.apply(Math, y);
    const axmax_y = Math.max.apply(Math, y);

    // Calculation of limits
    let axlims_x = [
      axmin_x - (axmax_x - axmin_x) * 0.05,
      axmax_x + (axmax_x - axmin_x) * 0.05,
    ];
    let axlims_y = [
      axmin_y - (axmax_y - axmin_y) * 0.05,
      axmax_y + (axmax_y - axmin_y) * 0.05,
    ];
    // Generating axes tick values
    let axticks_x = this.linspace(axlims_x[0], axlims_x[1], 5); // X axis ticks
    let axticks_y = this.linspace(axlims_y[0], axlims_y[1], 5); // X axis ticks
    // Calling axis_labels function to generate axis labels
    var axtick_x_labels = this.axis_labels(axlims_x, axticks_x);
    var axtick_y_labels = this.axis_labels(axlims_y, axticks_y);
    var sizes = [];
    var colors: any = [];
    var hoverTemperate =
      xLabelText + ': %{x:.3f}' + '<br>' + yLabelText + ': %{y:.3f}';
    if (
      this.workflowDetail.selectedColorByOpt != '' &&
      this.findObject.length > 0
    ) {
      var colorAttribute;
      var colorAttribute2;
      if (this.workflowDetail.selectedColorByOpt == 'trial_index_visual') {
        colorAttribute = 'Trial';
        colorAttribute2 = 'Pareto-optimal';
      } else {
        colorAttribute = 'Trial';
        colorAttribute2 = 'Pareto-optimal';
      }
      var text = '<br>' + colorAttribute + ': %{text}';
      var customdata =
        '<br>' + colorAttribute2 + ': %{customdata}<extra></extra>';
      hoverTemperate = hoverTemperate + text + customdata;

      for (var j = 0; j < feature.length; j++) {
        if (this.workflowDetail.selectedColorByOpt == 'Pareto-optimal') {
          if (feature[j] === 'True') {
            colors.push('#FF5F1F');
          } else if (feature[j] === 'False') {
            colors.push('blue');
          } else {
            colors.push('#808080');
          }
        } else {
          colors.push(feature2[j]);
        }
      }
    } else {
      for (var j = 0; j < x.length; j++) {
        colors.push(x[j]);
      }
    }

    var scatter = {
      x: x,
      y: y,
      text: feature2,
      customdata: feature,
      mode: 'markers',
      type: 'scatter',
      marker: {
        color: colors,
        size: 10,
        colorscale: 'Viridis',
        colorbar: {},
        opacity: 1,
        line: {
          color: '#C9D0D0',
          width: 1,
        },
      },
      showlegend: false,
      hovertemplate: hoverTemperate + '<extra></extra>',
    };
    if (
      this.workflowDetail.selectedColorByOpt != '' &&
      this.workflowDetail.selectedColorByOpt == 'trial_index_visual'
    ) {
      scatter['marker']['colorscale'] = 'Viridis';
    }
    scatter['marker']['colorscale'] = 'Viridis';
    if (this.workflowDetail.selectedColorByOpt == 'trial_index_visual') {
      scatter['marker']['colorbar'] = {
        len: 1,
        thickness: 20,
        title: 'Color By<br>' + "'" + 'Trial' + "'" + '<br>',
        titleside: 'top',
        tickmode: 'array',
        ticklen: 3,
        tickfont: {
          size: 10,
          color: '#21969D',
        },
      };
    }
    // Setting the layout
    this.layout = {
      // X axis parameters
      xaxis: {
        showline: true,
        mirror: true,
        range: axlims_x,
        // range:[Math.min.apply(Math, axlims_x),Math.max.apply(Math, axlims_x)],
        zeroline: false,
        showgrid: false,
        gridcolor: 'white',
        tickvals: axticks_x,
        ticktext: axtick_x_labels,
        tickfont: {
          size: 12,
        },
        automargin: true,
        title: {
          text: xLabelText,
          standoff: 5,
        },
        linecolor: '#979797',
        linewidth: 1,
        titlefont: {
          size: 14,
        },
      },
      // Y axis parameters
      yaxis: {
        showline: true,
        mirror: true,
        range: axlims_y,
        // range:[Math.min.apply(Math, axlims_y),Math.max.apply(Math, axlims_y)],
        zeroline: false,
        showgrid: false,
        tickvals: axticks_y,
        ticktext: axtick_y_labels,
        tickfont: {
          size: 12,
        },
        gridcolor: 'white',
        automargin: true,
        title: {
          text: yLabelText,
          standoff: 5,
        },
        linecolor: '#979797',
        linewidth: 1,
        titlefont: {
          size: 14,
        },
      },
      showlegend: false,
      margin: {
        t: 25,
        b: 30,
        // r: 15
      },
      // plot_bgcolor: "rgba(229,236,246,255)",
      plot_bgcolor: 'white',
      autosize: true,
      hovermode: 'closest',
    };
    this.data = [scatter];

    this.plotConfig = {
      responsive: true,
      scrollZoom: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'autoScale2d', 'toggleSpikelines'],
    };
  }

  linspace(start: number, stop: number, num: number, endpoint = true) {
    const div = endpoint ? num - 1 : num;
    const step = (stop - start) / div;
    return Array.from({ length: num }, (_, i) => start + step * i);
  }

  axis_labels(axlims: number[], axticks: string | any[]) {
    // Specifying the number of decimals to keep
    var axrange = axlims[1] - axlims[0];
    var rd;
    if (axrange > 100) {
      rd = 0;
    } else if (axrange >= 10 && axrange < 100) {
      rd = 1;
    } else if (axrange >= 0.1 && axrange < 10) {
      rd = 2;
    } else if (axrange >= 0.001 && axrange < 0.1) {
      rd = 3;
    } else if (axrange < 0.001) {
      rd = 4;
    }
    // Specifying the strings for axes ticks (used for not showing excess decimals)
    var axtick_labels: any = [, , , , ,];
    var i;
    for (i = 0; i < axticks.length; i++) {
      var axtick_rounded = parseFloat(axticks[i].toFixed(rd));
      axtick_labels[i] = axtick_rounded.toString();
    }
    return axtick_labels;
  }

  colorByOptPlot() {}

  operatorSelection(e: any) {}

  getSelectedInputWidget(): Widget | undefined {
    return this.selectedInputWidget;
  }

  setSelectedInputWidget(widget: Widget) {
    this.inputChangeMade = true;
    this.selectedInputWidget = widget;
  }

  getWidgetOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let outputConfig: InputOutputConfig = widget.outputs[0];
      return outputConfig.name!;
    }

    return '';
  }

  get widgetOutput(): string | undefined {
    return this.outputName;
  }

  set widgetOutput(value: string | undefined) {
    this.outputName = value;
    this.outputChangeMade = true;
  }

  unselectedFeatureSelection(value: any) {
    if (value == 'None' || this.unselectedFeature == 'None') {
      this.outcome_constraints_variable = '';
      this.operator = '';
      this.inputValue = '';
    } else {
      this.outcome_constraints_variable = value;
      this.saveWorkflow();
    }
  }

  selectModule(value: any) {
    this.configCache!.constraints_module_id = value;
    this.saveWorkflow();
  }

  getConstraintsModuleId() {
    return this.configCache!.constraints_module_id;
  }

  saveWorkflow() {
    if (!this.configCache) {
      return;
    }
    this.changeMade = true;
    var variables: any = [];
    this.configCache.input_variables = [];
    this.configCache.output_variables = [];
    this.configCache.input_variables_constraints = [];
    var output_variables_models = [];
    var connectors: any = [];
    var objectives_api_url: any = [];
    var selectedInputs = this.workflowDetail.config.inputFeatures;
    for (var i = 0; i < selectedInputs.length; i++) {
      variables.push(selectedInputs[i].name);
      this.configCache.input_variables.push(selectedInputs[i].name);
      this.configCache.input_variables_constraints.push([
        selectedInputs[i].min,
        selectedInputs[i].max,
      ]);
    }

    var selectedOutputs = this.workflowDetail.config.outputFeatures;
    for (var i = 0; i < selectedOutputs.length; i++) {
      variables.push(selectedOutputs[i].name);
      this.configCache.output_variables.push(selectedOutputs[i].name);
      connectors.push(selectedOutputs[i].connector);
      objectives_api_url.push(selectedOutputs[i].objective_url);
      output_variables_models.push(selectedOutputs[i].model);
    }
    if (this.selectedDataset['features_io_info'].data) {
      this.configCache.features_detail = this.selectedDataset[
        'features_io_info'
      ].data.filter((val: any) => val.dataType === 'Numerical');
    }
  }

  cancel() {}

  setWorkflowDetail() {
    if (!this.configCache) {
      return;
    }

    this.workflowDetail.batch_size = this.configCache.batch_size
      ? this.configCache.batch_size
      : 1;
    var input_variables = this.configCache.input_variables;
    var output_variables = this.configCache.output_variables;

    this.output_features = output_variables;
    var inputs = [];
    var input_variables_constraints =
      this.configCache.input_variables_constraints;

    if (
      input_variables &&
      input_variables.length > 0 &&
      this.selectedDataset.features_io_info.data.length > 0
    ) {
      for (var m = 0; m < input_variables.length; m++) {
        var input = this.selectedDataset.features_io_info.data.filter(
          (val: any) => val['name'] == input_variables[m],
        );
        inputs.push(input[0]);
        if (m == input_variables.length - 1) {
          this.workflowDetail.config.inputFeatures = [...inputs];
          for (
            var j = 0;
            j < this.workflowDetail.config.inputFeatures.length;
            j++
          ) {
            var index = input_variables.findIndex(
              (val: any) =>
                val == this.workflowDetail.config.inputFeatures[j].name,
            );
            if (index != -1) {
              this.workflowDetail.config.inputFeatures[j].min =
                input_variables_constraints[index][0];
              this.workflowDetail.config.inputFeatures[j].max =
                input_variables_constraints[index][1];
            }
          }
        }
      }
    } else {
      const errorMessage = 'Input variables are undefined or empty';
      this.toaster.error(errorMessage, 'ERROR', {
        positionClass: 'custom-toast-position',
      });
    }
    var outputs = [];
    var outputFeatures: any = [];

    if (
      output_variables.length > 0 &&
      this.selectedDataset.features_io_info.data.length > 0
    ) {
      for (var n = 0; n < output_variables.length; n++) {
        var outputIndex = this.selectedDataset[
          'features_io_info'
        ].data.findIndex((val: any) => val['name'] == output_variables[n]);
        this.selectedDataset.features_io_info.data[outputIndex].select = true;
        this.selectedDataset.features_io_info.data[outputIndex].output = true;
        this.selectedDataset.features_io_info.data[outputIndex].input = false;
        outputs.push(this.selectedDataset.features_io_info.data[outputIndex]);
        outputFeatures.push({
          name: output_variables[n],
          min_max_value:
            this.configCache.output_variables_objectives[n] == 'MINIMUM'
              ? 1
              : 2,
          threshold: this.configCache.output_variables_thresholds[n],

          objective_url: '',
          model: '',
        });
        if (n == output_variables.length - 1) {
          this.workflowDetail.config.outputFeatures = outputFeatures;
          this.workflowDetail.selectedOUT_X =
            this.workflowDetail.config.outputFeatures[0].name;
          this.workflowDetail.selectedOUT_Y =
            this.workflowDetail.config.outputFeatures[1].name;

          var combineFeatures = this.workflowDetail.config.inputFeatures.concat(
            this.workflowDetail.config.outputFeatures,
          );
          var remainingFeatures = [];
          for (
            var c = 0;
            c < this.selectedDataset.features_io_info.data.length;
            c++
          ) {
            if (
              this.selectedDataset.features_io_info.data[c].dataType ==
              'Numerical'
            ) {
              var index: number = combineFeatures.findIndex(
                (val: any) =>
                  val['name'] ==
                  this.selectedDataset.features_io_info.data[c].name,
              );
              if (index == -1) {
                remainingFeatures.push(
                  this.selectedDataset.features_io_info.data[c],
                );
              }
            }
            if (c == this.selectedDataset.features_io_info.data.length - 1) {
              this.workflowDetail.config.unselectedFeatures = [
                ...remainingFeatures,
              ];
            }
          }
        }
      }
    }
  }
  getAllModules() {
    this.activeLearningConfigService
      .getAllModules(this.site_id, this.project_id, 10, 1)
      .subscribe({
        next: (response) => {
          this.module_list = response['modules'];
        },
        error: (error) => {
          const errorMessage =
            error?.error?.message ||
            error?.message ||
            'An unexpected error occurred';
          this.toaster.error(errorMessage, 'ERROR', {
            positionClass: 'custom-toast-position',
          });
        },
      });
  }

  getDataCsvWidgetConfig(): Widget | null {
    let dataCsvActivityConfig: Widget = this.widgetControl?.Widget as Widget;

    return dataCsvActivityConfig;
  }

  openPreveiwDialog() {
    if (this.dataset_id) {
      const dialogRef = this.dialog.open(DataPreviewComponent, {
        width: '95vw',
        maxWidth: '95vw',
        height: '95%',
        data: {
          datasetId: this.dataset_id,
        },
      });
      dialogRef.afterClosed().subscribe((result) => {});
    }
  }

  get dataSource() {
    return this.workflowDetail.config.inputFeatures;
  }

  get outputDataSource() {
    return this.workflowDetail.config.outputFeatures;
  }

  getConfigOutputFeatures() {
    return this.workflowDetail.config.inputFeatures.concat(
      this.workflowDetail.config.outputFeatures,
    );
  }

  setTheOutcomeConstraints(value: boolean) {
    if (this.configCache) {
      // this.configCache.outcome_constraints_active = value;
      this.saveWorkflow();
    }
  }

  onAppSettingsUpdated() {
    this.changeSetting = true;
  }

  onInputSave() {
    if (this.selectedInputWidget) {
      let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
      inputOutputConfig.name = this.selectedInputWidget.outputs[0].name;
      inputOutputConfig.urn = this.selectedInputWidget.urn;
      if (this.widgetControl) {
        this.widgetControl.Widget.inputs.length = 0;
        this.widgetControl.Widget.inputs.push(inputOutputConfig);
        this.getAttachedWidgetData();
      }

      this.inputChangeMade = false;
    }
  }

  onInputCancel() {
    this.loadSelectedInputWidget();
    this.inputChangeMade = false;
  }

  onOutputSave() {
    if (this.outputName) {
      this.outputName = this.outputName.trim();
      if (
        this.widgetControl &&
        this.widgetControl.Widget.outputs &&
        this.widgetControl.Widget.outputs.length > 0
      ) {
        this.widgetControl.Widget.outputs[0].name = this.outputName;
      }
    }
    this.outputChangeMade = false;
  }

  onOutputCancel() {
    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
    }
    this.outputChangeMade = false;
  }

  onSaveSetting() {
    this.settingsComponent.SaveAppSettings();
    this.changeSetting = false;
  }

  onCancelSetting() {
    this.settingsComponent.RevertAppSetting();
    this.changeSetting = false;
  }

  onSave() {
    this.workflowCanvasService.changeMadeToWorkflow = true;
    if (this.ValidateConfiguration()) {
      this.saveWorkflow();
      if (this.widgetControl && this.configCache) {
        this.widgetControl.Widget.config = this.configCache;
        this.config = this.widgetControl?.Widget
          .config as ActiveLearningWidgetConfig;
        this.configCache = JSON.parse(JSON.stringify(this.config));
      }
      if (!this.widgetControl) {
        return;
      }
      this.changeMade = false;
    }
  }

  onCancel() {
    // Deep clone to prevent updates from modifying original
    this.configCache = JSON.parse(JSON.stringify(this.config));
    this.changeMade = false;
    this.loadFeatures();
  }

  ValidateConfiguration() {
    this.validationCheck = true;
    if (
      this.workflowDetail['config']['inputFeatures'].length == 0 ||
      this.workflowDetail['config']['outputFeatures'].length == 0
    ) {
      return false;
    } else {
      var selectedInputs = this.workflowDetail['config']['inputFeatures'];
      var selectedOutputs = this.workflowDetail['config']['outputFeatures'];

      var inputFlag = false;
      var outputFlag = false;
      for (var i = 0; i < selectedInputs.length; i++) {
        if (
          parseFloat(selectedInputs[i].min) >
            parseFloat(selectedInputs[i].max) ||
          parseFloat(selectedInputs[i].min) ===
            parseFloat(selectedInputs[i].max)
        ) {
          inputFlag = true;
          this.validationCheck = false;
          this.toaster.error(
            'Min value should be less than Max value for each input',
            '',
            {
              positionClass: 'custom-toast-position',
            },
          );
          return false;
        }

        if (
          selectedInputs[i].min === null ||
          selectedInputs[i].max === null ||
          selectedInputs[i].min === '' ||
          selectedInputs[i].max === ''
        ) {
          this.validationCheck = false;
          inputFlag = true;
          this.toaster.error('Please fill all required fields', '', {
            positionClass: 'custom-toast-position',
          });
          return false;
        }
      }

      if (!this.getBatchSize() || !this.getIterations()) {
        outputFlag = true;
        this.validationCheck = false;
        this.toaster.error('Please fill all required fields', '', {
          positionClass: 'custom-toast-position',
        });
        return false;
      }

      if (inputFlag || outputFlag) {
        this.validationCheck = false;
        return false;
      } else {
        this.validationCheck = true;
        return true;
      }
    }
  }

  getAttachedWidgetData() {
    this.inputURN = this.editWorkflowService.findConnectedWidgets(
      this.widgetControl?.Widget.inputs[0]?.urn ?? '',
    );
    if (this.inputURN.length > 0) {
      var configuration = this.inputURN[0].config as DataCopyWidgetConfig;
      var source = configuration?.source
        .configuration as LocalFileConfiguration;
      var dataset_id = source?.dataset_id;
      this.dataset_id = source?.dataset_id;

      if (
        this.configCache &&
        this.configCache['features_detail'] &&
        this.configCache['features_detail'].length !== 0
      ) {
        this.selectedDataset['features_io_info'] = new MatTableDataSource(
          this.configCache['features_detail'],
        );
        this.getTheFeaturesMetaData(dataset_id);
      } else {
        this.getDatasetStats(dataset_id);
      }
      this.datasetIDFetched = true;
    } else {
      this.datasetIDFetched = false;
    }
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }

  validateInput(event: KeyboardEvent): boolean {
    const charCode = event.charCode;
    const inputValue = (event.target as HTMLInputElement).value;
    if (charCode >= 49 && charCode <= 57) {
      return true;
    }
    if (charCode === 48 && inputValue.length > 0) {
      return true;
    }
    return false;
  }

  checkInputEquality(input: { min: any; max: any }) {
    const min_input = parseFloat(input.min);
    const max_input = parseFloat(input.max);
    if (
      min_input === max_input ||
      min_input > max_input ||
      min_input === null ||
      max_input === null
    ) {
      return true;
    }
    return false;
  }

  hasValidInputWidgets(): boolean {
    return (
      this.inputWidgets.length > 0 &&
      this.inputWidgets.some(
        (widget) => this.getWidgetOutputName(widget) !== '',
      )
    );
  }
}
