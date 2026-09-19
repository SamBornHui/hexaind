import {
  Component,
  Input,
  ElementRef,
  ViewChild,
  AfterViewInit,
  HostListener,
  Renderer2,
  ViewContainerRef,
  ComponentRef,
  Type,
  ComponentFactoryResolver,
  ChangeDetectorRef,
} from '@angular/core';
import { Utils } from '../../utils';
import { ActivatedRoute, Router } from '@angular/router';
import { NotificationComponent } from '../../controls/notification/notification.component';
import { WidgetControl } from '../../controls/widget-control/widget-control';
import { Arrow, ArrowType } from '../../controls/widget-control/arrow';
import { ConnectorPoint } from '../../controls/widget-control/connector-point';
import {
  WorkflowCanvasService,
  CanvasButton,
  ConfigService,
} from './workflow-canvas.service';
import * as d3 from 'd3';
import * as dagreD3 from 'dagre-d3';
import { Position, WidgetClientType } from './client-tags';
import { MountedDriveFileSelectorComponent } from '../../dialogs/mounted-drive-file-selector/mounted-drive-file-selector.component';
import {
  Widget,
  WidgetType,
  LoopEndWidgetConfig,
  DataCopyWidgetConfig,
  SourceType,
  LocalFileConfiguration,
  MountedDriveConfiguration,
  Workflow,
  DatasetModel,
  CustomCodeWidgetConfig,
} from '../../models/workflow-models';
import { ApiService } from '../../services/api.service';
import { NavService } from 'src/app/controls/left-nav/nav.service';
import { MatDialog } from '@angular/material/dialog';
import { InjestionDialogComponent } from '../../dialogs/injestion-dialog/injestion-dialog.component';
import { JoinComponent } from 'src/app/controls/configs/join-config/join.component';
import { BigQueryConfigComponent } from 'src/app/controls/configs/big-query-config/big-query-config.component';
import { AppendComponent } from 'src/app/controls/configs/append-config/append-config.component';
import { FilterConfigComponent } from 'src/app/controls/configs/filter-config/filter-config.component';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { MoboConfigComponent } from 'src/app/controls/configs/mobo-config/mobo-config.component';
import { CsvDataConfigComponent } from 'src/app/controls/configs/csv-data-config/csv-data-config.component';
import { JupyterConfigComponent } from 'src/app/controls/configs/jupyter-data-config/jupyter-data-config.component';
import { SaveConfigComponent } from 'src/app/controls/configs/save-config/save-config.component';
import { PythonConfigComponent } from 'src/app/controls/configs/python-config/python-config.component';
import { CustomCodeConfigComponent } from 'src/app/controls/configs/custom-code-config/custom-code-config.component';
import { PostRescaleConfigComponent } from 'src/app/controls/configs/post-rescale-config/post-rescale-config.component';
import { RescaleConfigComponent } from 'src/app/controls/configs/rescale-config/rescale-config.component';
import { DecisionConfigComponent } from 'src/app/controls/configs/decision-config/decision-config.component';
import { FeatureEngineeringConfigComponent } from 'src/app/controls/configs/feature-engineering-config/feature-engineering-config.component';
import { LoopStartConfigComponent } from 'src/app/controls/configs/loop-start-config/loop-start-config.component';
import { LoopEndConfigComponent } from 'src/app/controls/configs/loop-end-config/loop-end-config.component';
import { DataPreviewComponent } from 'src/app/dialogs/data-preview/data-preview.component';
import { ThermoCalcConfigComponent } from 'src/app/controls/configs/thermocalc-config/thermocalc-config.component';
import { PromptSaveComponent } from 'src/app/dialogs/prompt-save/prompt-save.component';
import { ActiveLearningConfigComponent } from 'src/app/controls/configs/active-learning-config/active-learning-config.component';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import {
  VersionedWorkflowRunStatus,
  SessionSaveAsWorkflow,
  SessionWorkflow,
  WorkflowSession,
  WorkflowRunStatus,
} from 'src/app/models/workflow-sessions-api-response.models';
import { Subscription, interval, takeWhile } from 'rxjs';
import { WorkflowDesignerHeaderComponent } from 'src/app/controls/workflow-designer-header/workflow-designer-header.component';
import { PublishWorkflowComponent } from 'src/app/dialogs/publish-workflow/publish-workflow.component';
import { ProjectButtonVisibilityServiceService } from 'src/app/controls/header/project-button-visibility-service.service';
import { PublishedWorkflowRunsComponent } from 'src/app/dialogs/published-workflow-runs/published-workflow-runs.component';
import { RunSummaryComponent } from 'src/app/dialogs/run-summary/run-summary.component';
import { GprConfigComponent } from 'src/app/controls/configs/gpr-config/gpr-config.component';
import { MprConfigComponent } from 'src/app/controls/configs/mpr-config/mpr-config.component';
import { DataSetResultsComponent } from 'src/app/dialogs/data-set-results/data-set-results/data-set-results.component';
import { AutoMlConfigComponent } from 'src/app/controls/configs/auto-ml-config/auto-ml-config.component';
import { RfMlConfigComponent } from 'src/app/controls/configs/rf-ml-config/rf-ml-config.component';
import { NnrMlConfigComponent } from 'src/app/controls/configs/nnr-ml-config/nnr-ml-config.component';
import { CatBoostMlConfigComponent } from 'src/app/controls/configs/cat-boost-ml-config/cat-boost-ml-config.component';
import { XgboostMlConfigComponent } from 'src/app/controls/configs/xgboost-ml-config/xgboost-ml-config.component';
import { KnNeighborsMlConfigComponent } from 'src/app/controls/configs/kn-neighbors-ml-config/kn-neighbors-ml-config.component';
import { ExtraTreesMlConfigComponent } from 'src/app/controls/configs/extra-trees-ml-config/extra-trees-ml-config.component';

import { LGBMMlConfigComponent } from 'src/app/controls/configs/lgbm-ml-config/lgbm-ml-config.component';
import { LRMlConfigComponent } from 'src/app/controls/configs/lr-ml-config/lr-ml-config.component';
import { NnTorchMlConfigComponent } from 'src/app/controls/configs/nntorch-ml-config/nntorch-ml-config.component';
import { ArimaMlConfigComponent } from 'src/app/controls/configs/arima-ml-config/arima-ml-config.component';
import { PredictionConfigComponent } from 'src/app/controls/configs/prediction-config/prediction-config.component';
import { SvmConfigComponent } from 'src/app/controls/configs/svm-config/svm-config.component';
import { GaussianProcessClassificationConfigComponent } from 'src/app/controls/configs/gaussian-process-classification-config/gaussian-process-classification-config.component';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { CustomTooltipComponent } from '../custom-tooltip/custom-tooltip.component';
import { ConfirmationPrompComponent } from 'src/app/dialogs/confirmation-promp/confirmation-promp.component';
import { DropMissingConfigComponent } from 'src/app/controls/configs/drop-missing-config/drop-missing-config.component';

import { CreateNewWorkflowTemplateComponent } from 'src/app/dialogs/create-new-workflow-template/create-new-workflow-template.component';
import { LoadWorkflowTemplatesDialogComponent } from 'src/app/dialogs/load-saved-templates/load-saved-templates-dialog.component';
import { FeatureFlagService } from 'src/app/services/feature-flag.service';
import { DropColumnsConfigComponent } from 'src/app/controls/configs/drop-columns-config/drop-columns-config.component';
import { ParquetWidgetConfigComponent } from 'src/app/controls/configs/parquet-widget-config/parquet-widget-config.component';
import { RenameColumnsConfigComponent } from 'src/app/controls/configs/rename-columns-config/rename-columns-config.component';
import { DatatypeConversionConfigComponent } from 'src/app/controls/configs/datatype-conversion-config/datatype-conversion-config.component';
import { WorkflowDesignerServiceService } from './workflow-designer-service.service';

import { DataVisualizationComponent } from 'src/app/dialogs/data-visualization/data-visualization.component';
import { WidgetRunResult } from 'src/app/models/workflow-sessions-api-response.models';
import { ToastrService } from 'ngx-toastr';
import { ExcelWidgetConfigComponent } from 'src/app/controls/configs/excel-widget-config/excel-widget-config.component';
import { ImageDatasetSelectionWidgetComponent } from 'src/app/controls/configs/image-dataset-selection-widget/image-dataset-selection-widget.component';
import { ImageRegionPropertiesWidgetComponent } from 'src/app/controls/configs/image-region-properties-widget/image-region-properties-widget.component';
import { ImageSpatialWidgetComponent } from 'src/app/controls/configs/image-spatial-widget/image-spatial-widget.component';
import { TextWidgetConfigComponent } from 'src/app/controls/configs/text-widget-config/text-widget-config.component';
interface CustomWidget {
  type: WidgetType;
  clientType: WidgetClientType;
  iconName: string;
  displayName: string;
  id: string | null;
  urn?: string;
  widgetPurpose?: string | null;
  expectedInput?: string | null;
  expectedOutput?: string | null;
  description?: string | null;
}
@Component({
  selector: 'app-workflow-designer',
  templateUrl: './workflow-designer.component.html',
  styleUrls: ['./workflow-designer.component.less'],
})
export class WorkflowDesignerComponent implements AfterViewInit {
  @ViewChild('myCanvas', { static: true })
  canvas: ElementRef<HTMLCanvasElement> | null = null;
  @ViewChild('TopBarDiv', { static: false }) myTopBarDivRef: ElementRef | null =
    null;
  @ViewChild('LeftPanelDiv', { static: false })
  myLeftPanelDivRef: ElementRef | null = null;
  @ViewChild('MiddlePanelDiv', { static: false })
  myMiddlePanelDivRef: ElementRef | null = null;
  @ViewChild('notification') notificationComponent!: NotificationComponent;
  @ViewChild('workflowDesignerHeader')
  workflowDesignerHeader!: WorkflowDesignerHeaderComponent;

  @ViewChild('mountedDriveFileSelector')
  mountedDriveFileSelector!: MountedDriveFileSelectorComponent;

  @ViewChild('widgetConfigContainer', { read: ViewContainerRef })
  widgetConfigContainer!: ViewContainerRef;
  componentRef: ComponentRef<any> | null = null;

  @ViewChild('tooltipContainer', { read: ViewContainerRef })
  tooltipContainer!: ViewContainerRef;

  @Input() snapToGrid: boolean = true;

  private tooltipTimeout: any;
  dragOffsetX = 0;
  dragOffsetY = 0;
  mouseClickPositionX: number = 0;
  mouseClickPositionY: number = 0;
  WidgetType = WidgetType;
  WidgetClientType = WidgetClientType;
  workflowExecutionSubscription: Subscription | null = null;
  runSessionId: string | undefined = undefined;
  pollForExecutionStatus: boolean = false;
  customWidgets: CustomWidget[] = [
    {
      type: WidgetType.SAVE,
      clientType: WidgetClientType.Save,
      iconName: 'save',
      displayName: 'Save',
      id: null,
    },
    {
      type: WidgetType.UX,
      clientType: WidgetClientType.Start,
      iconName: 'line_start_circle',
      displayName: 'Start Widget',
      id: null,
    },
    {
      type: WidgetType.UX,
      clientType: WidgetClientType.End,
      iconName: 'line_end_circle',
      displayName: 'End Widget',
      id: null,
    },
    // {
    //   type: WidgetType.DECISION,
    //   clientType: WidgetClientType.Decision,
    //   iconName: 'thermostat_carbon',
    //   displayName: 'Decision',
    // },
    // Add other widgets similarly
  ];
  filteredCustomWidgets: CustomWidget[] = [];

  loopWidgets: CustomWidget[] = [];
  customPythonWidgets: CustomWidget[] = [];
  thirdPartyAPIWidgets: CustomWidget[] = [];
  filteredThirdPartyAPIWidgets: CustomWidget[] = [];
  dataWidgets: CustomWidget[] = [];
  filteredDataWidgets: CustomWidget[] = [];
  curationWidgets: CustomWidget[] = [];
  AIMLWidgets: CustomWidget[] = [];
  filteredAIMLWidgets: CustomWidget[] = [];
  customCodePythonWidgets: CustomWidget[] = [];
  filteredCustomCodePythonWidgets: CustomWidget[] = [];
  activeWidget: string | null = null;
  searchTerm: string = '';
  filteredIngestionWidgets: CustomWidget[] = [];
  selectedWidgetsToCopy: WidgetControl[] = [];

  private boundOnCanvasMouseMove: EventListener = this.onCanvasMouseMove.bind(
    this,
  ) as EventListener;

  private boundOnResize: EventListener = this.onCanvasResize.bind(
    this,
  ) as EventListener;
  private resizeListener!: () => void;
  private mouseupListener!: () => void;

  private promptingToSave: boolean = false;
  private animationFrameId: number | null = null;

  private panStartX: number = 0;
  private panStartY: number = 0;
  private ctx: CanvasRenderingContext2D | null = null;
  private editImage = new Image();
  private copyDataImage = new Image();
  private optimizeImage = new Image();
  private filterImage = new Image();
  private dataFlowImage = new Image();
  private greenCheckImage = new Image();
  private failedImage = new Image();
  private warningImage = new Image();
  private startFlag = new Image();
  private startFlagCircular = new Image();
  private isPanning = false;
  private mouseX: number = 0;
  private mouseY: number = 0;
  private showConnectingPoints = false;
  private hoveringArrow: Arrow | undefined = undefined;
  // private selectedArrows: Arrow | undefined = undefined;
  private selectedArrows: Arrow[] = [];
  private startY: number = 0;
  private startHeightTop: number = 0;
  private startHeightBottom: number = 0;
  private startX: number = 0;

  private startWidthLeft: number = 0;
  private startWidthRight: number = 0;
  private minZoom: number = 0;
  private maxZoom: number = 100;
  private zoomScale: number = 1;
  private scaleChange: number = 1;
  private widgetSize = this.workflowCanvasService.getWidgetStartRadius();
  private connectingPointsType: ArrowType = ArrowType.OnCompleted;
  public selectedColor: string = '#356DD3'; // Initial color value
  public IsShowingMountedDriveFileSelector: boolean = false;
  public IsShowingMOBOConfig = false;
  public IsDesignerSettingsPanelVisible = false;
  public Scale = 1; // Initial scale factor
  public selectedSource: string = ''; // Default value for 'local'
  public zoomLevel: number = 40;
  public defaultZoomLevel: number = 40;
  /**
   * Default zoom level is 40 but during the first load of the workflow the initial zoom turns out to be around 34 not 40.
   */
  public initialZoomLevelOnScreenLoad: number = 34;
  public previousZoomLevel: number = 34;
  public isWorkflowSaveApiInprogress = false;
  public showCurationWidgets: boolean = false;
  public showDataWidgets: boolean = false;
  public showGeneralWidgets: boolean = false;
  public showLoopWidgets: boolean = false;
  public showThirdPartyAPIWidgets: boolean = false;
  public showCustomPythonWidgets: boolean = false;
  public showMachineLearningWidgets: boolean = false;
  public showCustomCodeWidgets: boolean = false;
  public showDataActivities: boolean = true;
  public showMLActivities: boolean = true;
  public showOptimizationActivities: boolean = true;
  public isExpanded: boolean = true;
  public showCanvasContextMenu = false;
  public showArrowContextMenu = false;
  public showLoopArrowContextMenu = false;
  public contextMenuPosition = { x: 0, y: 0 };
  disableSaveAndRun = true;

  options: any[] = [
    { value: 'option1', viewValue: 'Connector' },
    { value: 'option2', viewValue: 'Local Drive' },
    { value: 'option3', viewValue: 'Mounted Drive' },
  ];

  draggedWidgetType: WidgetType | undefined = undefined;
  draggedWidgetClientType: WidgetClientType = WidgetClientType.None;
  canvasButtons: CanvasButton[] = [];
  hoverStates = new Map<string, boolean>();
  parentData: string = 'Hello from parent';
  private widgetComponentMap: any = {
    [WidgetClientType.BigQuery]: BigQueryConfigComponent,
    [WidgetType.JOIN]: JoinComponent,
    [WidgetType.APPEND]: AppendComponent,
    [WidgetType.FILTER]: FilterConfigComponent,
    [WidgetType.DROP_MISSING]: DropMissingConfigComponent,
    [WidgetType.DROP_COLUMNS]: DropColumnsConfigComponent,
    [WidgetType.RENAME_COLUMNS]: RenameColumnsConfigComponent,
    [WidgetType.DATATYPE_CONVERSION]: DatatypeConversionConfigComponent,
    [WidgetType.LOOP_START]: LoopStartConfigComponent,
    [WidgetType.LOOP_END]: LoopEndConfigComponent,
    [WidgetClientType.MOBO]: MoboConfigComponent,
    [WidgetClientType.CSVFile]: CsvDataConfigComponent,
    [WidgetClientType.Jupyter]: JupyterConfigComponent,
    [WidgetType.SAVE]: SaveConfigComponent,
    [WidgetType.PYTHON]: PythonConfigComponent,
    [WidgetType.CUSTOM_CODE]: CustomCodeConfigComponent,
    [WidgetType.POST_RESCALE]: PostRescaleConfigComponent,
    [WidgetClientType.Rescale]: RescaleConfigComponent,
    [WidgetClientType.Decision]: DecisionConfigComponent,
    [WidgetClientType.Feature_Engineering]: FeatureEngineeringConfigComponent,
    [WidgetClientType.ThermoCalc]: ThermoCalcConfigComponent,
    [WidgetClientType.ACTIVE_LEARNING]: ActiveLearningConfigComponent,
    [WidgetClientType.GPR]: GprConfigComponent,
    [WidgetClientType.MPR]: MprConfigComponent,
    [WidgetClientType.AutoML]: AutoMlConfigComponent,
    [WidgetClientType.LGBM]: LGBMMlConfigComponent,
    [WidgetClientType.LINEAR_REGRESSION]: LRMlConfigComponent,
    [WidgetClientType.RF]: RfMlConfigComponent,
    [WidgetClientType.NNFASTAI]: NnrMlConfigComponent,
    [WidgetClientType.ARIMA]: ArimaMlConfigComponent,
    [WidgetClientType.NN_TORCH]: NnTorchMlConfigComponent,
    [WidgetClientType.CATBOOST]: CatBoostMlConfigComponent,
    [WidgetClientType.XGBOOST]: XgboostMlConfigComponent,
    [WidgetClientType.KNEIGHBORS]: KnNeighborsMlConfigComponent,
    [WidgetClientType.EXTRA_TREES]: ExtraTreesMlConfigComponent,
    [WidgetClientType.PREDICTION]: PredictionConfigComponent,
    [WidgetClientType.SVM]: SvmConfigComponent,
    [WidgetClientType.GPC]: GaussianProcessClassificationConfigComponent,
    [WidgetClientType.ParquetFile]: ParquetWidgetConfigComponent,
    [WidgetClientType.ExcelFile]: ExcelWidgetConfigComponent,
    [WidgetClientType.IMAGE_DATASET]: ImageDatasetSelectionWidgetComponent,
    [WidgetClientType.REGION_PROPERTY]: ImageRegionPropertiesWidgetComponent,
    [WidgetClientType.IMAGE_SPATIAL_STATISTICS]: ImageSpatialWidgetComponent,
    [WidgetClientType.TEXT_FILE]: TextWidgetConfigComponent,
  };

  widget_id: string | null = null;
  dataPreviewWidget: Widget | undefined = undefined;
  private triggerSaveSubscription: Subscription | undefined;
  private triggerMonitorRunSubscription: Subscription | undefined;

  currentUser: any;
  widget_name: string | null | undefined;
  showArrowColorSlider: boolean = false;
  arrowColor = '#2066D3';

  constructor(
    private sessionApi: WorkflowsSessionsApiService,
    private route: ActivatedRoute,
    private router: Router,
    private eRef: ElementRef,
    private renderer: Renderer2,
    public workflowCanvasService: WorkflowCanvasService,
    public sharedDataService: SharedDataService,
    private apiService: ApiService,
    public navService: NavService,
    private dialog: MatDialog,
    private configService: ConfigService,
    private projectVisibilityService: ProjectButtonVisibilityServiceService,
    private sanitizer: DomSanitizer,
    private resolver: ComponentFactoryResolver,
    private changeDetectorRef: ChangeDetectorRef,
    private featureFlagService: FeatureFlagService,
    public toaster: ToastrService,
    private workflowDesignerService: WorkflowDesignerServiceService,
  ) {
    this.resetWidgets();

    this.workflowCanvasService.changeMadeToWorkflow = false;
  }

  ngOnDestroy() {
    this.projectVisibilityService.showProjectsButton();
    window.removeEventListener('mousemove', this.boundOnCanvasMouseMove);
    window.removeEventListener('resize', this.boundOnResize);
    this.stopCanvasDrawing();
    this.pollForExecutionStatus = false;
    this.triggerSaveSubscription?.unsubscribe();
    this.triggerMonitorRunSubscription?.unsubscribe();
    this.workflowExecutionSubscription?.unsubscribe();
  }

  ngOnInit(): void {
    this.currentUser = localStorage.getItem('currentUser')
      ? JSON.parse(localStorage.getItem('currentUser')!)
      : null;
    this.projectVisibilityService.hideProjectsButton();
    this.loadCustomCodePythonWidgets();

    if (this.route) {
      this.route.queryParams.subscribe((params) => {
        this.updateRouteParameters(params);
      });
    }
    window.addEventListener('mouseup', this.onCanvasMouseUp.bind(this));

    this.triggerSaveSubscription =
      this.workflowDesignerService.triggerSave$.subscribe((value) => {
        if (value === true) {
          this.saveWorkflow(true);
          this.workflowDesignerService.setTriggerSave(false);
        }
      });

    this.triggerMonitorRunSubscription =
      this.workflowDesignerService.triggerMonitorRun$.subscribe((value) => {
        if (value === true) {
          this.pollForExecutionStatus = false;
          this.startMonitorRunExecutionLoop();
          this.workflowDesignerService.setTriggerMonitorRun(false);
        }
      });
  }

  ngAfterViewInit() {
    if (!this.canvas) {
      return;
    }

    // this.ctx = this.canvas.nativeElement.getContext('2d');
    this.ctx = this.canvas.nativeElement.getContext('2d')!;

    window.addEventListener('mousemove', this.boundOnCanvasMouseMove);
    window.addEventListener('resize', this.onCanvasResize.bind(this));

    // Set the size of the canvas according to the device pixel ratio
    this.canvas.nativeElement.width =
      this.canvas.nativeElement.offsetWidth * window.devicePixelRatio;
    this.canvas.nativeElement.height =
      this.canvas.nativeElement.offsetHeight * window.devicePixelRatio;
    this.ctx!.scale(window.devicePixelRatio, window.devicePixelRatio);

    this.editImage.src = 'assets/edit.png'; // Change this to the path of your PNG image
    this.copyDataImage.src = 'assets/copy_data.png';
    this.optimizeImage.src = 'assets/optimize.png';
    this.filterImage.src = 'assets/filter.png';
    this.dataFlowImage.src = 'assets/data_flow.png';
    this.failedImage.src = 'assets/failure.png';
    this.warningImage.src = 'assets/warning.png';
    this.greenCheckImage.src = 'assets/greenCheck.png'; // Change this to the path of your PNG image
    this.startFlag.src = 'assets/flag.png';
    this.startFlagCircular.src = 'assets/Transition.png';

    this.startCanvasDrawing();
    this.resizeCanvas();

    setTimeout(() => {
      this.resizeCanvas();
    }, 150); // 2000 milliseconds = 2 seconds

    // const leftPanelElement = document.getElementById('left-panel');
    // if (leftPanelElement) {
    //   // Initialize the custom scrollbar library
    //   new SimpleBar(leftPanelElement);
    // }
  }

  toggleSlider(): void {
    this.showArrowColorSlider = !this.showArrowColorSlider;
  }

  previousCoOrdinatesBeforeAlignment: any = [];
  isWidgetsAligned = false;
  alignWidgets() {
    if (this.doesUserUsedTheZoomFunctionality()) {
      this.isWorkflowSaveApiInprogress = true;
      this.previousZoomLevel = this.zoomLevel;
      this.zoomLevel = this.initialZoomLevelOnScreenLoad;
      this.applyZoom();
    }

    let graph: any = new dagreD3.graphlib.Graph()
      .setGraph({
        rankdir: 'LR',
        edgesep: 0,
        nodesep: 180, // This defines the space between the horizontal layers of
        ranksep: 180,
      })
      .setDefaultEdgeLabel(() => ({}));

    if (this.workflowCanvasService.arrows) {
      this.workflowCanvasService.arrows.forEach((item) => {
        const startNode = item.startPoint.widgetControl.Widget.urn;
        const endNode = item.endPoint.widgetControl.Widget.urn;

        if (!graph.hasNode(startNode)) {
          graph.setNode(startNode, {
            label: startNode,
            width: 110,
            height: 110,
          });
        }
        if (!graph.hasNode(endNode)) {
          graph.setNode(endNode, { label: endNode, width: 110, height: 110 });
        }

        graph.setEdge(startNode, endNode);
      });
    }

    const svg = d3.create('svg');
    const inner: any = svg.append('g');

    svg
      .append('defs')
      .append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 0 10 10')
      .attr('refX', 8)
      .attr('refY', 5)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M 0 0 L 10 5 L 0 10 Z')
      .style('fill', '#888');

    const render = new dagreD3.render();
    render(inner, graph);

    const nodeCoordinates = graph.nodes().map((node: any) => {
      const data = graph.node(node);
      return { id: node, x: data.x, y: data.y };
    });
    this.isWidgetsAligned = true;
    this.workflowCanvasService.widgetControls.forEach(
      (widgetControl: WidgetControl) => {
        let widget = widgetControl.Widget;
        try {
          let newCordinates = nodeCoordinates.find((element: any) => {
            return element.id == widget.urn;
          });
          this.previousCoOrdinatesBeforeAlignment.push({
            previousX: widget.client_tags.PositionX,
            previousY: widget.client_tags.PositionY,
            urn: widget.urn,
          });
          widget.client_tags.PositionX = newCordinates.x;
          widget.client_tags.PositionY = newCordinates.y;
        } catch (error) {
          console.log(widget);
        }
        this.snapToGrid = false;
      },
    );

    if (this.doesUserUsedTheZoomFunctionality()) {
      this.revertBackToSelectedZoomLevelAfterSaving();
    }
  }

  undoAlignmentChanges() {
    if (this.doesUserUsedTheZoomFunctionality()) {
      this.isWorkflowSaveApiInprogress = true;
      this.previousZoomLevel = this.zoomLevel;
      this.zoomLevel = this.initialZoomLevelOnScreenLoad;
      this.applyZoom();
    }

    this.workflowCanvasService.widgetControls.forEach(
      (widgetControl: WidgetControl) => {
        let widget = widgetControl.Widget;
        let prevCoOrdinates = this.previousCoOrdinatesBeforeAlignment.find(
          (element: any) => element.urn == widget.urn,
        );
        if (prevCoOrdinates) {
          widget.client_tags.PositionX = prevCoOrdinates.previousX;
          widget.client_tags.PositionY = prevCoOrdinates.previousY;
        }
      },
    );
    this.isWidgetsAligned = false;
    this.previousCoOrdinatesBeforeAlignment = [];

    if (this.doesUserUsedTheZoomFunctionality()) {
      this.revertBackToSelectedZoomLevelAfterSaving();
    }
  }

  onColorChange(event: any): void {
    this.arrowColor = event.color.hex;
    if (this.workflowCanvasService.SelectedWorkflow) {
      this.workflowCanvasService.SelectedWorkflow.client_tags.arrowColor =
        this.arrowColor;
    }
  }

  onOpenViewRunMode() {
    this.isExpanded = false;
    this.expandToFullPage();
    if (this.workflowCanvasService.IsVersionedWorkflow) {
      let dialogRef: any;
      dialogRef = this.dialog.open(PublishedWorkflowRunsComponent, {
        width: '600px',
        data: {
          workflowId: this.workflowCanvasService.SelectedWorkflow!._id!,
          workflowSessionId:
            this.workflowCanvasService.SelectedWorkflowSession?._id,
        },
      });

      dialogRef.afterClosed().subscribe((queryParams: any) => {
        if (queryParams) {
          this.router.navigate(['/workflow-designer'], {
            queryParams,
          });
        }
      });
    } else {
      let queryParams: {
        refresh: string;
        siteId: string;
        projectId: string;
        workflowSessionId: string | null | undefined;
        viewingRunId: string | null;
        userZoomLevel: any | null;
      } = {
        refresh: Math.random().toString(),
        siteId: this.configService.SelectedSiteId,
        projectId: this.configService.SelectedProjectId!,
        workflowSessionId:
          this.workflowCanvasService.SelectedWorkflowSession?._id,
        viewingRunId:
          this.workflowCanvasService.SelectedWorkflowSession?.run_id!,
        userZoomLevel: undefined,
      };

      if (this.doesUserUsedTheZoomFunctionality()) {
        queryParams.userZoomLevel = this.zoomLevel;
      }

      this.router.navigate(['/workflow-designer'], {
        queryParams,
      });
    }
  }

  onCloseViewRunMode() {
    this.isExpanded = false;
    this.collapseToFullPage();
    this.resizeCanvas();

    setTimeout(() => {
      this.resizeCanvas();
    }, 150); // 2000 milliseconds = 2 seconds
  }

  async updateRouteParameters(params: any) {
    let workflowSessionId: string | undefined = params['workflowSessionId'];
    let versionedWorkflowId: string | undefined = params['versionedWorkflowId'];
    let workflowId: string | undefined = undefined;
    this.workflowCanvasService.IsVersionedWorkflow = versionedWorkflowId
      ? true
      : false;
    if (versionedWorkflowId) {
      workflowId = versionedWorkflowId;
    } else {
      workflowId = params['workflowId'];
    }

    if (params['viewingRunId']) {
      this.workflowCanvasService.ViewingRunId = params['viewingRunId'];
      this.workflowCanvasService.IsViewingRunMode = true;
      this.startMonitorRunExecutionLoop();
    } else {
      this.workflowCanvasService.ViewingRunId = undefined;
      this.workflowCanvasService.IsViewingRunMode = false;
    }

    /**
     * This will normalize the zoom level to initial level
     */

    if (params.userZoomLevel) {
      this.applyZoomLevelOfWorkflowScreenLoad();
    }

    if (workflowSessionId) {
      await this.loadSessionAndWorkflow(
        workflowSessionId,
        workflowId,
        params['runworkflow'],
        params['viewingRunId'],
      );
      this.showConfigByWidgetType();
    } else {
      this.notificationComponent.display(
        'Workflow Session ID is required.',
        'error',
      );
    }

    /**
     * After normalization and get workflow api response we apply the user defined zoom for view run screen
     */

    if (params.userZoomLevel) {
      this.zoomLevel = params.userZoomLevel;
      this.applyZoom();
    }

    this.resizeCanvas();

    if (this.workflowCanvasService?.SelectedWorkflow?.client_tags?.arrowColor) {
      this.arrowColor =
        this.workflowCanvasService.SelectedWorkflow.client_tags.arrowColor;
    } else {
      this.arrowColor = 'gray';
    }

    setTimeout(() => {
      this.resizeCanvas();
    }, 150); // 2000 milliseconds = 2 seconds
  }

  applyZoomLevelOfWorkflowScreenLoad() {
    this.zoomLevel = this.initialZoomLevelOnScreenLoad;
    this.applyZoom();
  }

  async loadSessionAndWorkflow(
    workflowSessionId: string,
    workflowId: string | undefined,
    runworkflow: string | undefined,
    run_id: string | undefined,
  ) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    try {
      workflowId = await this.workflowCanvasService.LoadSessionAndWorkflow(
        this.configService.SelectedSiteId,
        selectedProjectId,
        workflowSessionId,
        workflowId,
        this.widgetSize,
        runworkflow,
        run_id,
      );
    } catch (error) {
      console.error(error);
    }

    this.disableSaveAndRun = false;

    if (!workflowId) {
      this.notificationComponent.display(
        'Workflow could not be found.',
        'error',
      );
      return;
    }

    if (
      this.workflowCanvasService.SelectedWorkflowSession &&
      this.workflowCanvasService.SelectedWorkflow
    ) {
      this.workflowDesignerHeader.Initialize(
        this.workflowCanvasService.SelectedWorkflow.name!,
      );
    }
    // if(workflowId){
    //   this.saveWorkflow();
    // }
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    let generalActivities = this.eRef.nativeElement.querySelector(
      '.collapsed .general-activities',
    );

    if (generalActivities) {
      const isClickInsideGeneralActivities = generalActivities.contains(
        event.target,
      );
      if (!isClickInsideGeneralActivities) {
        this.showGeneralWidgets = false;
      }
    }
    let ingestionActivitites = this.eRef.nativeElement.querySelector(
      '.collapsed .ingestion-activities',
    );

    if (ingestionActivitites) {
      const isClickInsideDataActivities = ingestionActivitites.contains(
        event.target,
      );
      if (!isClickInsideDataActivities) {
        this.showDataWidgets = false;
      }
    }
    let analyticActivities = this.eRef.nativeElement.querySelector(
      '.collapsed .analytics-activities',
    );

    if (analyticActivities) {
      const isClickInsideAnalyticsActivities = analyticActivities.contains(
        event.target,
      );
      if (!isClickInsideAnalyticsActivities) {
        this.showCurationWidgets = false;
      }
    }
    let machineActivities = this.eRef.nativeElement.querySelector(
      '.collapsed .machine-activities',
    );

    if (machineActivities) {
      const isClickInsideAnalyticsActivities = machineActivities.contains(
        event.target,
      );
      if (!isClickInsideAnalyticsActivities) {
        this.showMachineLearningWidgets = false;
      }
    }
  }

  shouldMonitor(): boolean {
    // Could still be loading run status.
    if (!this.workflowCanvasService.WorkflowRunStatus) {
      return true;
    }

    if (
      this.workflowCanvasService.WorkflowRunStatus.run_status &&
      this.workflowCanvasService.WorkflowRunStatus.run_status === 'SUCCEEDED'
    ) {
      return false;
    }

    // Stop polling if single widget run has succeeded
    if (
      this.workflowCanvasService.WorkflowRunStatus.is_single_widget_run &&
      this.workflowCanvasService.WorkflowRunStatus.run_status === 'SUCCEEDED'
    ) {
      this.pollForExecutionStatus = false; // Ensure polling stops for single widget success
      return false;
    }
    // let continueMonitoring: boolean =
    //   this.workflowCanvasService.WorkflowRunStatus.run_status !== undefined &&
    //   (this.workflowCanvasService.WorkflowRunStatus.run_status === 'RUNNING' ||
    //     this.workflowCanvasService.WorkflowRunStatus.run_status ===
    //     'NOT RUN' || this.workflowCanvasService.WorkflowRunStatus.run_status === 'IDLE') &&
    //   this.workflowCanvasService.IsViewingRunMode &&
    //   this.pollForExecutionStatus;

    // return continueMonitoring;
    return this.workflowCanvasService.IsViewingRunMode;
  }

  async startMonitorRunExecutionLoop() {
    if (this.pollForExecutionStatus) {
      return;
    }

    if (this.workflowExecutionSubscription) {
      this.workflowExecutionSubscription.unsubscribe();
    }

    await this.updateRunStatus();
    setTimeout(() => {
      this.updateRunStatus(); // wait for 3 seconds to check if the run_status changed to RUNNING, then poll every 10 seconds
      this.pollForExecutionStatus = true;
      this.workflowExecutionSubscription = interval(10000)
        .pipe(
          takeWhile(() => this.shouldMonitor()), // Continue until shouldMonitor() returns false
        )
        .subscribe(
          () => {
            this.updateRunStatus(); // Called every 10 seconds while shouldMonitor() returns true
          },
          (error) => {
            this.pollForExecutionStatus = false;
            console.error('Error occurred:', error); // Handle any errors
          },
          () => {
            this.pollForExecutionStatus = false;
          },
        );
    }, 3000);
  }

  onHeaderNavigateBack() {
    if (this.workflowCanvasService.changeMadeToWorkflow === true) {
      this.promptToSaveWorkflow();
    } else {
      this.navigateBack(false);
    }
  }

  async navigateBack(saveChanges: boolean) {
    if (saveChanges) {
      let success = await this.saveWorkflow();
      if (!success) {
        return;
      }
    }
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    let url = `/sites/${this.configService.SelectedSiteId}/projects/${selectedProjectId}/workflows`;
    this.router.navigate([url]);
  }

  async updateRunStatus() {
    if (!this.workflowCanvasService.IsVersionedWorkflow) {
      await this.loadWorkflowSessionRunStatus();
    } else {
      if (this.workflowCanvasService.ViewingRunId) {
        await this.loadVersionedWorkflowRunStatus(
          this.workflowCanvasService.ViewingRunId,
        );
      }
    }
  }

  async onStopWorkflowRun() {
    const selectedProjectId = this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    const selectedSessionId =
      this.workflowCanvasService.SelectedWorkflowSession?._id;
    if (!selectedSessionId) {
      return;
    }

    // this.pollForExecutionStatus = false;

    const isVersionedWorkflow = this.workflowCanvasService.IsVersionedWorkflow;
    const runId = this.workflowCanvasService.ViewingRunId;

    // Decide whether to show confirmation dialog
    if (
      this.workflowCanvasService.WorkflowRunStatus?.run_status === 'RUNNING' &&
      this.workflowCanvasService.containsRescaleWidget()
    ) {
      await this.handleRescaleWorkflow(
        selectedProjectId,
        selectedSessionId,
        isVersionedWorkflow!,
        runId,
      );
    } else {
      await this.otherWorkflowsProcess(
        selectedProjectId,
        selectedSessionId,
        isVersionedWorkflow!,
        runId!,
      );
    }
  }

  private async handleRescaleWorkflow(
    selectedProjectId: string,
    selectedSessionId: string,
    isVersionedWorkflow: boolean,
    runId: string | undefined,
  ) {
    const dialogRef = this.dialog.open(ConfirmationPrompComponent, {
      width: '400px',
      data: {
        action: 'stop',
        workflowName: this.workflowCanvasService.selectedWorkflow$,
      },
    });

    dialogRef.afterClosed().subscribe(async (action) => {
      let stopParams: any;

      if (action === 'stopAll') {
        stopParams = {
          run_id: isVersionedWorkflow ? runId : '',
          stop_all: true,
          stop_pending: true,
          user_id: this.currentUser?._id,
        };
      } else if (action === 'stopPending') {
        stopParams = {
          run_id: isVersionedWorkflow ? runId : '',
          stop_all: false,
          stop_pending: true,
          user_id: this.currentUser?._id,
        };
      }

      if (stopParams) {
        await this.processStopAction(
          stopParams,
          action,
          selectedProjectId,
          selectedSessionId,
          isVersionedWorkflow,
          runId,
        );
      }
    });
  }

  private async otherWorkflowsProcess(
    selectedProjectId: string,
    selectedSessionId: string,
    isVersionedWorkflow: boolean,
    runId: string,
  ) {
    let stopParams = {
      run_id: isVersionedWorkflow ? runId : '',
      stop_all: false,
      stop_pending: false,
      user_id: this.currentUser?._id,
    };
    const result: boolean = await this.sessionApi.StopSessionRun(
      this.configService.SelectedSiteId!,
      selectedProjectId!,
      selectedSessionId!,
      stopParams,
    );

    if (!result) {
      const errorMessage =
        this.sharedDataService.LastError || 'Workflow is currently not running';
      this.notificationComponent.display(errorMessage, 'error');
    } else {
      if (!isVersionedWorkflow) {
        await this.updateMasterWorkflowStatus(
          selectedProjectId,
          selectedSessionId,
        );
      } else {
        await this.updateVersionedWorkflowStatus(
          this.configService.SelectedSiteId!,
          selectedProjectId,
          this.workflowCanvasService.SelectedWorkflow!._id!,
          runId,
        );
      }
    }
  }

  private async processStopAction(
    stopParams: any,
    action: string,
    selectedProjectId: string,
    selectedSessionId: string,
    isVersionedWorkflow: boolean,
    runId: string | undefined,
  ) {
    const result: boolean = await this.sessionApi.StopSessionRun(
      this.configService.SelectedSiteId!,
      selectedProjectId!,
      selectedSessionId!,
      stopParams,
    );

    if (!result) {
      const errorMessage =
        this.sharedDataService.LastError || 'Workflow is currently not running';
      this.notificationComponent.display(errorMessage, 'error');
    } else {
      if (action === 'stopAll' && result) {
        if (!isVersionedWorkflow) {
          await this.updateMasterWorkflowStatus(
            selectedProjectId,
            selectedSessionId,
          );
        } else {
          await this.updateVersionedWorkflowStatus(
            this.configService.SelectedSiteId!,
            selectedProjectId,
            this.workflowCanvasService.SelectedWorkflow!._id!,
            runId!,
          );
        }
        this.notificationComponent.display(
          'Workflow execution stopped.',
          'success',
        );
      } else if (action === 'stopPending' && result) {
        // Continue polling even after stopping pending jobs
        this.pollForExecutionStatus = false;
        this.startMonitorRunExecutionLoop();
        this.notificationComponent.display(
          'Rescale pending jobs successfully stopped.',
          'success',
        );
      }
    }
  }

  private async updateMasterWorkflowStatus(
    selectedProjectId: string,
    selectedSessionId: string,
  ) {
    try {
      // Fetch the updated status from the API
      const updatedStatus = await this.sessionApi.GetWorkflowSessionRunStatus(
        this.configService.SelectedSiteId!,
        selectedProjectId!,
        selectedSessionId!,
      );

      if (updatedStatus && Array.isArray(updatedStatus.widgets_status)) {
        // Process identical widgets to update their statuses
        updatedStatus.widgets_status.forEach(
          (widget, index, widgetsStatusArray) => {
            const identicalWidgets = widgetsStatusArray.filter(
              (otherWidget) =>
                otherWidget.urn === widget.urn && otherWidget !== widget,
            );
            identicalWidgets.forEach((identicalWidget) => {
              if (
                widget.status === 'RUNNING' &&
                identicalWidget.status === 'IDLE'
              ) {
                widget.status = 'STOPPED';
              }
            });
          },
        );

        // Update the workflow run status in the canvas service
        this.workflowCanvasService.WorkflowRunStatus = updatedStatus;
        this.notificationComponent.display(
          'Workflow execution stopped.',
          'success',
        );
      } else {
        throw new Error('No valid status received from session API');
      }
    } catch (error) {
      console.error('Error updating workflow session status:', error);
      this.notificationComponent.display(
        'Failed to update workflow status.',
        'error',
      );
    }
  }

  private async updateVersionedWorkflowStatus(
    siteId: string,
    projectId: string,
    workflowId: string,
    runId: string,
  ) {
    try {
      const workflowResults = await this.sessionApi.GetVersionedWorkflowStatus(
        siteId,
        projectId,
        workflowId,
        runId,
      );

      if (
        workflowResults &&
        workflowResults.widgets_status &&
        Array.isArray(workflowResults.widgets_status)
      ) {
        workflowResults.widgets_status.forEach(
          (widget: any, index: any, widgetsStatusArray: any) => {
            const identicalWidgets = widgetsStatusArray.filter(
              (otherWidget: any) =>
                otherWidget.urn === widget.urn && otherWidget !== widget,
            );

            // Update widget status to stop if one is RUNNING and the other is IDLE
            identicalWidgets.forEach((identicalWidget: any) => {
              if (
                widget.status === 'RUNNING' &&
                identicalWidget.status === 'IDLE'
              ) {
                widget.status = 'STOPPED';
              }
            });
          },
        );
      }
      this.workflowCanvasService.WorkflowRunStatus = workflowResults;
      this.notificationComponent.display(
        'Workflow execution stopped.',
        'success',
      );
    } catch (error) {
      // Handle errors during the API call or processing
      console.error('Error fetching versioned workflow status:', error);
      this.notificationComponent.display(
        'Failed to update versioned workflow status.',
        'error',
      );
    }
  }

  onExternalElementDragStart(
    event: DragEvent,
    widgetType: WidgetType,
    widgetClientType: WidgetClientType,
    widget_id: string | null = null,
    widget_name: string | null = null,
  ): void {
    this.hideTooltipData();
    this.draggedWidgetType = widgetType;
    this.draggedWidgetClientType = widgetClientType;
    this.widget_id = widget_id;
    this.widget_name = widget_name;
  }

  onCanvasDragOver(event: DragEvent): void {
    // Allow the drop event
    event.preventDefault();
  }

  onCanvasDrop(event: DragEvent): void {
    event.preventDefault();
    if (this.canvas && this.canvas.nativeElement) {
      const canvasEl: HTMLCanvasElement = this.canvas.nativeElement;
      var posX = event.clientX;
      var posY = event.clientY;
      const canvasRect = canvasEl.getBoundingClientRect();
      this.mouseX = posX - canvasRect.left;
      this.mouseY = posY - canvasRect.top;
    }
    if (this.draggedWidgetType) {
      if (this.draggedWidgetClientType === WidgetClientType.Start) {
        let startWidgetControl: WidgetControl | undefined =
          this.workflowCanvasService.widgetControls.find(
            (widgetControl) =>
              widgetControl.Widget.client_tags.ClientType ===
              WidgetClientType.Start,
          );
        if (startWidgetControl) {
          this.notificationComponent.display(
            'A start node already exists on the canvas.',
            'success',
          );
          return;
        }
      } else if (this.draggedWidgetClientType === WidgetClientType.End) {
        let endWidgetControl: WidgetControl | undefined =
          this.workflowCanvasService.widgetControls.find(
            (widgetControl) =>
              widgetControl.Widget.client_tags.ClientType ===
              WidgetClientType.End,
          );
        if (endWidgetControl) {
          this.notificationComponent.display(
            'An end node already exists on the canvas.',
            'success',
          );
          return;
        }
      }

      let positionX = this.mouseX;
      let positionY = this.mouseY;
      if (positionX <= 0 && positionY <= 0) {
        positionX = Math.floor(Math.random() * (200 - 50 + 1)) + 50;
        positionY = Math.floor(Math.random() * (200 - 50 + 1)) + 50;
      }

      this.workflowCanvasService.changeMadeToWorkflow = true;

      let widgetControl: WidgetControl | undefined =
        this.workflowCanvasService.CreateNewWidgetControl(
          this.draggedWidgetType,
          this.draggedWidgetClientType,
          positionX,
          positionY,
          this.widgetSize,
          this.widget_id,
          this.widget_name,
        );

      if (widgetControl) {
        this.workflowCanvasService.selectedWidgetControl = widgetControl;
        this.showConfigByWidgetType();
        let newWidgetUrn = widgetControl.Widget.urn;
        this.workflowCanvasService.newDraggedWidgetsList = newWidgetUrn;
      }
    }
  }

  async loadCustomCodePythonWidgets() {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    const response = await this.apiService.getCustomCodePythonWidgets(
      this.configService.SelectedSiteId,
      selectedProjectId,
    );
    response.forEach((item: any) => {
      item.widgetPurpose =
        'Custom python widget executes user-defined python scripts. This widget is defined in Custom Widgets section on the Project landing page.';
      item.expectedInput =
        'A range of various input data types expected by the user-defined python script.';
      item.expectedOutput =
        'A range of various output data types from the user-defined python script.';
    });
    this.customCodePythonWidgets = response;
    this.filteredCustomCodePythonWidgets = response;
  }

  async loadVersionedWorkflowRunStatus(runId: string) {
    let workflowSessionRunStatus: VersionedWorkflowRunStatus | undefined =
      await this.apiService.GetVersionedWorkflowRunStatus(
        this.configService.SelectedSiteId,
        this.configService.SelectedProjectId!,
        this.workflowCanvasService.SelectedWorkflow?._id!,
        runId,
      );

    if (workflowSessionRunStatus) {
      let workflowRunStatus: WorkflowRunStatus = new WorkflowRunStatus();
      workflowRunStatus.widgets_status =
        workflowSessionRunStatus.widgets_status;
      workflowRunStatus.workflow = workflowSessionRunStatus.workflow;
      workflowRunStatus.run_status = 'RUNNING';

      if (
        workflowRunStatus.widgets_status.some(
          (widgetStatus) => widgetStatus.status === 'RUNNING',
        )
      ) {
        workflowRunStatus.run_status = 'RUNNING';
      } else if (
        workflowRunStatus.widgets_status.some(
          (widgetStatus) => widgetStatus.status === 'FAILED',
        )
      ) {
        workflowRunStatus.run_status = 'FAILED';
      } else if (
        workflowRunStatus.widgets_status.some(
          (widgetStatus) => widgetStatus.status === 'PAUSED',
        )
      ) {
        workflowRunStatus.run_status = 'PAUSED';
      } else if (
        workflowRunStatus.widgets_status.some(
          (widgetStatus) => widgetStatus.status === 'IDLE',
        )
      ) {
        workflowRunStatus.run_status = 'NOT RUN';
      } else {
        if (
          workflowRunStatus.widgets_status.every(
            (widgetStatus) => widgetStatus.status === 'SUCCEEDED',
          )
        ) {
          workflowRunStatus.run_status = 'SUCCEEDED';
        }
      }
      this.workflowCanvasService.WorkflowRunStatus = workflowRunStatus;
    }
  }

  /**
   * If any few widget are in succeeded and remaining are in idle state we are still considering it as run state.
   * @param widgetStatuses
   * @returns
   */

  doesWidgetsInIdleStateWithFewSucceded(widgetStatuses: any) {
    let isAnyWIdgetInIdleState = false;
    let isAnyWidgetSucceeded = false;
    widgetStatuses.forEach((widgetStatus: any) => {
      if (widgetStatus.status == 'SUCCEEDED') isAnyWidgetSucceeded = true;
      if (widgetStatus.status == 'IDLE') isAnyWIdgetInIdleState = true;
    });
    return isAnyWIdgetInIdleState && isAnyWidgetSucceeded;
  }

  async loadWorkflowSessionRunStatus() {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    if (
      !this.workflowCanvasService.SelectedWorkflowSession ||
      !this.workflowCanvasService.SelectedWorkflowSession._id
    ) {
      return;
    }
    let workflowSessionRunStatus: WorkflowRunStatus | undefined =
      await this.sessionApi.GetWorkflowSessionRunStatus(
        this.configService.SelectedSiteId,
        selectedProjectId,
        this.workflowCanvasService.SelectedWorkflowSession._id,
      );
    if (workflowSessionRunStatus) {
      let allSucceed = workflowSessionRunStatus.widgets_status.every(
        (widgetStatus) => widgetStatus.status === 'SUCCEEDED',
      );
      /**
       * Currently there is an issue in the socket notification if status api is called only once , so manaullay displaying toaster
       */

      if (workflowSessionRunStatus.is_single_widget_run) {
        this.workflowCanvasService.WorkflowRunStatus = workflowSessionRunStatus;
        if (workflowSessionRunStatus.run_status == 'SUCCEEDED') {
          if (this.pollForExecutionStatus) {
            this.toaster.info('Current widget execution is successful', '', {
              positionClass: 'custom-toast-position',
            });
            this.workflowCanvasService.notifyWidgetExecutionStatus(true);
            this.pollForExecutionStatus = false;
          }
        } else {
          workflowSessionRunStatus.run_status = 'RUNNING';
          this.pollForExecutionStatus = true;
        }
      } else if (
        allSucceed ||
        workflowSessionRunStatus.run_status == 'FAILED'
      ) {
        this.workflowCanvasService.WorkflowRunStatus = workflowSessionRunStatus;
      } else {
        workflowSessionRunStatus.run_status = 'RUNNING';
        this.workflowCanvasService.WorkflowRunStatus = workflowSessionRunStatus;
      }
    }
  }

  startCanvasDrawing() {
    this.animationFrameId = window.requestAnimationFrame(() => this.draw());
  }

  stopCanvasDrawing() {
    if (this.animationFrameId !== null) {
      window.cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  onCanvasResize() {
    this.resizeCanvas();
  }

  private resetWidgets() {
    this.showDataWidgets = false;
    this.showGeneralWidgets = false;
    this.showLoopWidgets = false;
    this.showThirdPartyAPIWidgets = false;
    this.showCustomPythonWidgets = false;
    this.showMachineLearningWidgets = false;
    this.showCurationWidgets = false;

    this.dataWidgets = [
      {
        type: WidgetType.DATA_COPY,
        clientType: WidgetClientType.CSVFile,
        iconName: 'csv',
        displayName: 'CSV File',
        id: null,
        widgetPurpose:
          'To load and preprocess CSV data into the HEXAIND 3.0 platform for advanced data analysis',
        expectedInput:
          'One CSV file with tabular data, specifying data types, delimiters, encodings, and column properties',
        expectedOutput: 'One processed tabular data output',
      },
      {
        type: WidgetType.JUPYTER,
        clientType: WidgetClientType.Jupyter,
        iconName: 'jupyter',
        displayName: 'JUPYTER',
        id: null,
        widgetPurpose:
          'To load and preprocess CSV data into the HEXAIND 3.0 platform for advanced data analysis',
        expectedInput:
          'One CSV file with tabular data, specifying data types, delimiters, encodings, and column properties',
        expectedOutput: 'One processed tabular data output',
      },
      {
        type: WidgetType.DATA_COPY,
        clientType: WidgetClientType.ParquetFile,
        iconName: 'data_table',
        displayName: 'Parquet File',
        id: null,
        widgetPurpose:
          'To load and preprocess PARQUET data into the HEXAIND 3.0 platform for advanced data analysis',
        expectedInput:
          'One PARQUET file with tabular data, specifying data types, delimiters, encodings, and column properties',
        expectedOutput: 'One processed tabular data output',
      },
      {
        type: WidgetType.SAVE,
        clientType: WidgetClientType.Save,
        iconName: 'save',
        displayName: 'Save',
        id: null,
        widgetPurpose:
          'To convert and save HEXAIND 3.0 datasets as standard file formats like CSV',
        expectedInput: 'Any number of datasets of various types',
        expectedOutput: 'No output datasets as it is a terminal widget',
      },
      {
        type: WidgetType.APPEND,
        clientType: WidgetClientType.Append,
        iconName: 'add',
        displayName: 'Append',
        id: null,
        widgetPurpose:
          'To combine two tabular datasets with identical columns in a workflow',
        expectedInput: 'Two tabular datasets with identical or similar columns',
        expectedOutput: 'One combined tabular dataset',
      },
      {
        type: WidgetType.JOIN,
        clientType: WidgetClientType.Join,
        iconName: 'join',
        displayName: 'Join',
        id: null,
        widgetPurpose:
          'To join two tabular datasets into a single tabular dataset',
        expectedInput: 'Two tabular datasets',
        expectedOutput: 'One combined tabular dataset',
      },
      {
        type: WidgetType.DATA_COPY,
        clientType: WidgetClientType.BigQuery,
        iconName: 'search_insights',
        displayName: 'Big Query',
        id: null,
        widgetPurpose:
          'The BigQuery widget enables users to interact seamlessly with Google BigQuery within the HEXAIND 3.0 Platform',
        expectedInput:
          'Users input a BigQuery connection, query string or browse catalog to select tables and parameters',
        expectedOutput:
          'The widget outputs tabular data from executed queries, which can be exported or integrated into dashboards',
      },
      {
        type: WidgetType.FILTER,
        clientType: WidgetClientType.Filter,
        iconName: 'filter_alt',
        displayName: 'Filter',
        id: null,
        widgetPurpose:
          'Enable efficient data filtering and subsetting to enhance analysis and exploration workflows',
        expectedInput: 'Accepts tabular data for filtering operations',
        expectedOutput:
          'Generates filtered tabular data based on user-defined criteria',
      },
      {
        type: WidgetType.DROP_COLUMNS,
        clientType: WidgetClientType.DropColumns,
        iconName: 'view_column',
        displayName: 'Drop Columns',
        id: null,
        widgetPurpose:
          'Enable user to drop columns that are not needed for further processing',
        expectedInput: 'Accepts tabular data to drop columns',
        expectedOutput:
          'Generates tabular data after dropping necessary columns',
      },
      {
        type: WidgetType.DROP_MISSING,
        clientType: WidgetClientType.DropMissing,
        iconName: 'delete_sweep',
        displayName: 'Drop Missing',
        id: null,
        widgetPurpose:
          'Enable dropping rows with missing values corresponding to selected column to enhance analysis',
        expectedInput:
          'Accepts tabular data and column names as parameter for dropping rows',
        expectedOutput:
          'Generates tabular data after dropping rows with missing data',
      },
      {
        type: WidgetType.DATATYPE_CONVERSION,
        clientType: WidgetClientType.DatatypeConversion,
        iconName: 'convert_to_text',
        displayName: 'Datatype Conversion',
        id: null,
        widgetPurpose: 'Enable changing the datatype of a column',
        expectedInput:
          'Accepts tabular data and column names and new type as parameter for changing the data type',
        expectedOutput: 'Generates tabular data after changing the data type',
      },
      {
        type: WidgetType.RENAME_COLUMNS,
        clientType: WidgetClientType.RenameColumns,
        iconName: 'edit_note',
        displayName: 'Rename Columns',
        id: null,
        widgetPurpose: 'Enable renaming columns to enhance user understanding',
        expectedInput:
          'Accepts tabular data and column names as parameter for renaming',
        expectedOutput: 'Generates tabular data after renaming columns',
      },
      {
        type: WidgetType.DATA_COPY,
        clientType: WidgetClientType.ExcelFile,
        iconName: 'table_view',
        displayName: 'Excel File',
        id: null,
        widgetPurpose:
          'To load and preprocess Excel data into the HEXAIND 3.0 platform for advanced data analysis',
        expectedInput:
          'One Excel file with tabular data, with support for multiple sheets',
        expectedOutput:
          'One processed tabular data output, with support for multiple sheets if provided in input',
      },
      {
        type: WidgetType.IMAGE_DATASET,
        clientType: WidgetClientType.IMAGE_DATASET,
        iconName: 'photo',
        displayName: 'Image Dataset Selection',
        id: null,
        widgetPurpose:
          'The Image Dataset Widget provides functionalities for ingesting, filtering, and managing image datasets. It supports metadata-driven filtering and tagging for efficient dataset curation and preparation for image analytics workflows.',
        expectedInput:
          'Image datasets with associated metadata, including defect types, annotations, and user-defined tags',
        expectedOutput:
          'Filtered image datasets for downstream processing in workflows',
      },
      {
        type: WidgetType.REGION_PROPERTY,
        clientType: WidgetClientType.REGION_PROPERTY,
        iconName: 'grid_on',
        displayName: 'Image Region Properties',
        id: null,
        widgetPurpose:
          'The Region Props Widget computes region-based geometric and intensity properties from segmented images. The extracted properties are stored in tabular format for use in feature extraction, training, or evaluation workflows',
        expectedInput:
          'Binary segmentation masks from preprocessing workflows.',
        expectedOutput:
          'Tabular datasets in CSV, Parquet, or JSON formats containing region properties such as Geometric: Area, perimeter, centroid, bounding box, etc.. and o	Intensity: Mean, maximum, minimum, and standard deviation',
      },
      {
        type: WidgetType.IMAGE_SPATIAL_STATISTICS,
        clientType: WidgetClientType.IMAGE_SPATIAL_STATISTICS,
        iconName: 'stacks',
        displayName: 'Image Spatial Statistics',
        id: null,
        widgetPurpose:
          'The Spatial Statistics Widget computes spatial metrics to quantify the distribution, clustering, and relationships between defects in segmented images. It provides both numerical results and visualizations for statistical analysis.',
        expectedInput:
          'Defect centroid coordinates and metadata from Region Props or segmentation outputs',
        expectedOutput:
          'Nearest neighbor distances, clustering indices, pair correlation functions',
      },
      {
        type: WidgetType.TEXT_DATA,
        clientType: WidgetClientType.TEXT_FILE,
        iconName: 'text_fields',
        displayName: 'Text File',
        id: null,
        widgetPurpose: '',
        expectedInput: '',
        expectedOutput: '',
      },
      // {
      //   type: WidgetType.CONFIG_FILE,
      //   clientType: WidgetClientType.ConfigFile,
      //   iconName: 'tv_options_input_settings',
      //   displayName: 'Config File',
      //   id: null,
      // },
      // {
      //   type: WidgetType.CUSTOM_CODE,
      //   clientType: WidgetClientType.CustomCode,
      //   iconName: 'code',
      //   displayName: 'Custom Code',
      //   id: null,
      // },
      // {
      //   type: WidgetType.DATA_COPY,
      //   clientType: WidgetClientType.BigQuery,
      //   iconName: 'article_shortcut',
      //   displayName: 'Big Query',
      //   id: null,
      // },
    ];
    this.dataWidgets.sort((a, b) => a.displayName.localeCompare(b.displayName));

    this.filteredDataWidgets = [...this.dataWidgets];

    // this.curationWidgets = [
    //   {
    //     type: WidgetType.APPEND,
    //     clientType: WidgetClientType.Append,
    //     iconName: 'add',
    //     displayName: 'Append',
    //     id: null,
    //   },
    //   {
    //     type: WidgetType.FILTER,
    //     clientType: WidgetClientType.Filter,
    //     iconName: 'filter_alt',
    //     displayName: 'Filter',
    //     id: null,
    //   },

    //   {
    //     type: WidgetType.Feature_Engineering,
    //     clientType: WidgetClientType.Feature_Engineering,
    //     iconName: 'manufacturing',
    //     displayName: 'Feature Engineering',
    //   },
    //];

    this.AIMLWidgets = [
      {
        type: WidgetType.MOBO,
        clientType: WidgetClientType.MOBO,
        iconName: 'stacked_line_chart',
        displayName: 'MOBO',
        id: null,
        widgetPurpose:
          'MOBO widget allows supported HEXAIND 3.0 users to perform multi-objective Bayesian optimization on tabular datasets and connect to external software for feature generation or property prediction',
        expectedInput:
          'Accepts one tabular dataset to configure input and output features',
        expectedOutput:
          'Produces original input data, MOBO-generated input recommendations, and acquisition function values for the recommendations',
      },
      {
        type: WidgetType.ACTIVE_LEARNING,
        clientType: WidgetClientType.ACTIVE_LEARNING,
        iconName: 'repeat',
        displayName: 'Active Learning',
        id: null,
        widgetPurpose:
          'Active Learning widget allows supported HEXAIND 3.0 users to perform active learning on tabular datasets',
        expectedInput:
          'Single tabular dataframe for active learning operations',
        expectedOutput:
          'Generates recommendations and predictions in a tabular format from active learning',
      },
      {
        type: WidgetType.GPC,
        clientType: WidgetClientType.GPC,
        iconName: 'bubble_chart',
        displayName: 'Gaussian Process Classification',
        id: null,
        widgetPurpose:
          'GPC widget allows supported HEXAIND 3.0 users to train GPC models based on a GPyTorch implementation',
        expectedInput: 'Requires one tabular dataset for training GPC models',
        expectedOutput:
          'Produces a trained GPC model saved as a .pkl file, along with optional outputs such as a confusion matrix and accuracy report.',
      },
      {
        type: WidgetType.GPR,
        clientType: WidgetClientType.GPR,
        iconName: 'ssid_chart',
        displayName: 'Gaussian Process Regression',
        id: null,
        widgetPurpose:
          'GPR widget allows supported HEXAIND 3.0 users to train GPR models based on a GPyTorch implementation for regression tasks',
        expectedInput:
          'Requires one tabular dataframe for training GPR models, where features and targets are specified',
        expectedOutput:
          'Produces a trained GPR model saved as an .onnx/.pkl file, along with error performance metrics in a tabular dataset format',
      },
      {
        type: WidgetType.MPR,
        clientType: WidgetClientType.MPR,
        iconName: 'ssid_chart',
        displayName: 'Multi Polynominal Regression',
        id: null,
        widgetPurpose:
          'MPR Widget allows supported HEXAIND 3.0 users to train MPR models based on scikit learn LinearRegression module',
        expectedInput:
          'Requires one tabular dataframe for training MPR models, where features and targets are specified',
        expectedOutput:
          'Produces a trained MPR model saved as an .onnx/.pkl file, along with error performance metrics in a tabular dataset format',
      },
      {
        type: WidgetType.PREDICTION,
        clientType: WidgetClientType.PREDICTION,
        iconName: 'query_stats',
        displayName: 'Prediction',
        id: null,
        widgetPurpose:
          'The Prediction widget allows supported HEXAIND 3.0 users to perform predictions using a deployed ML model',
        expectedInput:
          'Accepts one tabular dataframe containing input features for making predictions',
        expectedOutput:
          'Produces a tabular dataset with prediction results and associated metrics',
      },
      {
        type: WidgetType.SVM,
        clientType: WidgetClientType.SVM,
        iconName: 'scatter_plot',
        displayName: 'SVM',
        id: null,
        widgetPurpose:
          'The purpose of the SVM widget is to allow users to build a support vector machine (SVM) for regression tasks',
        expectedInput:
          'Accepts one tabular dataframe for training SVM models with specified input and output features',
        expectedOutput:
          'Generates a trained SVM classification or regression model file and a tabular dataset containing the confusion matrix and accuracy metric',
      },
      {
        type: WidgetType.AUTOML,
        clientType: WidgetClientType.AutoML,
        iconName: 'settings_motion_mode',
        displayName: 'AutoML',
        id: null,
        widgetPurpose:
          'AutoML widget allows supported HEXAIND 3.0 users to train multiple ML models in one go and rank them in the order of performance',
        expectedInput:
          'Tabular dataset with features and target variable for tasks',
        expectedOutput:
          'Produces a trained AutoML classification or regression model with optimized hyperparameters and performance metrics, including accuracy, F1-score, or RMSE.',
      },
      {
        type: WidgetType.LINEAR_REGRESSION,
        clientType: WidgetClientType.LINEAR_REGRESSION,
        iconName: 'analytics',
        displayName: 'Linear Regression',
        id: null,
        widgetPurpose:
          'Linear Regression widget allows supported HEXAIND 3.0 users to train Linear Regression models based on AutoGluon implementation',
        expectedInput:
          'Tabular dataset with features and target variable for tasks',
        expectedOutput:
          'Produces a trained model with error performance metrics in a tabular dataset format',
      },
      {
        type: WidgetType.LGBM,
        clientType: WidgetClientType.LGBM,
        iconName: 'share',
        displayName: 'LGBM ',
        id: null,
        widgetPurpose:
          'Light GBM widget allows supported HEXAIND 3.0 users to train Light Gradient Boosting Machine (LGBM) Regression models, based on AutoGluon implementation',
        expectedInput:
          'Tabular dataset containing input features and output variable for model training .',
        expectedOutput:
          'Provides model preview with metrics, plots, feature importance, and parameters. For prediction: Outputs tabular prediction results.',
      },
      {
        type: WidgetType.RF,
        clientType: WidgetClientType.RF,
        iconName: 'network_node',
        displayName: 'Random Forest',
        id: null,
        widgetPurpose:
          'Random Forest widget allows supported HEXAIND 3.0 users to train Random Forest Regression models based on AutoGluon implementation',
        expectedInput:
          'Tabular dataset containing input features and output variable for model training',
        expectedOutput:
          'Provides model preview with metrics, plots, feature importance, and parameters.',
      },
      {
        type: WidgetType.NNFASTAI,
        clientType: WidgetClientType.NNFASTAI,
        iconName: 'hub',
        displayName: 'Neural Network(FASTAI)',
        id: null,
        widgetPurpose:
          'Neural Network (FastAI) widget allows supported HEXAIND 3.0 users to train Neural Network Regression models with FastAI backend, based on AutoGluon implementation',
        expectedInput:
          'Tabular dataset containing input features and output variable for model training',
        expectedOutput:
          'Provides model preview with metrics, plots, feature importance, and parameters.',
      },
      {
        type: WidgetType.NN_TORCH,
        clientType: WidgetClientType.NN_TORCH,
        iconName: 'grain',
        displayName: 'Neural Network(TORCH)',
        id: null,
        widgetPurpose:
          'Neural Network (Torch) widget allows supported HEXAIND 3.0 users to train Neural Network Regression models with Pytorch backend, based on AutoGluon implementation',
        expectedInput:
          'Tabular dataset containing input features and output variable for model training',
        expectedOutput:
          'Provides model preview with metrics, plots, feature importance, and parameters.',
      },
      {
        type: WidgetType.CATBOOST,
        clientType: WidgetClientType.CATBOOST,
        iconName: 'tenancy',
        displayName: 'CAT BOOST',
        id: null,
        widgetPurpose:
          'CatBoost widget allows supported HEXAIND 3.0 users to train CatBoost Regression models, based on AutoGluon implementation',
        expectedInput:
          'Tabular dataset containing input features and output variable for model training',
        expectedOutput:
          'Provides model preview with metrics, plots, feature importance, and parameters.',
      },
      {
        type: WidgetType.XGBOOST,
        clientType: WidgetClientType.XGBOOST,
        iconName: 'linked_services',
        displayName: 'XG BOOST',
        id: null,
        widgetPurpose:
          'XGBoost widget allows supported HEXAIND 3.0 users to train XGBoost Regression models, based on AutoGluon implementation',
        expectedInput:
          'Tabular dataset containing input features and output variable for model training',
        expectedOutput:
          'Provides model preview with metrics, plots, feature importance, and parameters.',
      },
      {
        type: WidgetType.KNEIGHBORS,
        clientType: WidgetClientType.KNEIGHBORS,
        iconName: 'blur_circular',
        displayName: 'K Nearest Neighbor',
        id: null,
        widgetPurpose:
          'K-Nearest neighbors (KNN) widget allows supported HEXAIND 3.0 users to train K-Nearest neighbors (KNN) Regression models, based on AutoGluon implementation',
        expectedInput:
          'Tabular dataset containing input features and output variable for model training',
        expectedOutput:
          'Provides model preview with metrics, plots, feature importance, and parameters.',
      },
      {
        type: WidgetType.EXTRA_TREES,
        clientType: WidgetClientType.EXTRA_TREES,
        iconName: 'spoke',
        displayName: 'Extra Trees',
        id: null,
        widgetPurpose:
          'Extra Trees widget allows supported HEXAIND 3.0 users to train Extra Trees Regression models, based on AutoGluon implementation',
        expectedInput:
          'Tabular dataset containing input features and output variable for model training',
        expectedOutput:
          'Provides model preview with metrics, plots, feature importance, and parameters.',
      },
      // {
      //   type: WidgetType.ARIMA,
      //   clientType: WidgetClientType.ARIMA,
      //   iconName: 'hub',
      //   displayName: 'ARIMA ',
      //   id: null,
      // },

      // {
      //   type: WidgetType.MODEL_BUILDER,
      //   clientType: WidgetClientType.LGBM,
      //   iconName: 'gradient',
      //   displayName: 'LGBM',
      //   id: null,
      // },

      // {
      //   type: WidgetType.PYTHON,
      //   clientType: WidgetClientType.Python,
      //   iconName: 'code_blocks',
      //   displayName: 'Python',
      //   id: null,
      // },
      // {
      //   type: WidgetType.POST_RESCALE,
      //   clientType: WidgetClientType.POST_RESCALE,
      //   iconName: 'post_add',
      //   displayName: 'Post Rescale',
      //   id: null,
      // },
      // Add other machine learning widgets similarly
    ].sort((a, b) => {
      if (a.displayName < b.displayName) {
        return -1;
      }
      if (a.displayName > b.displayName) {
        return 1;
      }
      return 0;
    });
    this.applyFeatureFlagsToAIMLWidgets();
    this.filteredAIMLWidgets = [...this.AIMLWidgets];

    this.customWidgets = [
      {
        type: WidgetType.UX,
        clientType: WidgetClientType.Start,
        iconName: 'line_start_diamond',
        displayName: 'Start Widget',
        id: null,
        widgetPurpose: 'Initiates the execution of a workflow in HEXAIND.',
        expectedInput:
          'No specific inputs required as it marks the beginning of the workflow.',
        expectedOutput:
          'No outputs generated as it solely starts the workflow execution.',
      },
      {
        type: WidgetType.UX,
        clientType: WidgetClientType.End,
        iconName: 'line_end_diamond',
        displayName: 'End Widget',
        id: null,
        widgetPurpose: 'Terminates the execution of a workflow in HEXAIND.',
        expectedInput:
          'Accepts any number of inputs from preceding widgets in the workflow.',
        expectedOutput:
          'No outputs generated as it marks the end of the workflow execution.',
      },

      {
        type: WidgetType.LOOP_START,
        clientType: WidgetClientType.LoopStart,
        iconName: 'line_start_circle',
        displayName: 'Loop Start',
        id: null,
        widgetPurpose:
          'Defines the start of a loop within the Workflow Builder.',
        expectedInput:
          'Accepts any number of inputs and data types dynamically mapped to match subsequent Widget inputs.',
        expectedOutput:
          'Generates outputs for initializing the loop and subsequent iterations, matching the number and named fields of subsequent Widget inputs.',
      },
      {
        type: WidgetType.LOOP_END,
        clientType: WidgetClientType.LoopEnd,
        iconName: 'line_end_circle',
        displayName: 'Loop End',
        id: null,
        widgetPurpose:
          'Ends a loop based on provided termination criteria (optional) or mandatory MAX LOOP COUNT.',
        expectedInput: 'Accepts any number of inputs from preceding Widgets.',
        expectedOutput: 'Outputs any number of inputs to subsequent Widgets.',
      },
      // {
      //   type: WidgetType.DECISION,
      //   clientType: WidgetClientType.Decision,
      //   iconName: 'thermostat_carbon',
      //   displayName: 'Decision',
      // },
      // Add other widgets similarly
    ];
    this.filteredCustomWidgets = [...this.customWidgets];
    this.filteredCustomCodePythonWidgets = [...this.customCodePythonWidgets];

    this.thirdPartyAPIWidgets = [
      {
        type: WidgetType.RESCALE,
        clientType: WidgetClientType.Rescale,
        iconName: 'filter_drama',
        displayName: 'Rescale',
        id: null,
        widgetPurpose:
          'Enable HEXAIND 3.0 users to perform cloud-based HPC simulations using Rescale accounts. Version 1.0 supports Abaqus and LS-Dyna software.',
        expectedInput:
          'Python scripts and input files for Abaqus or LS-Dyna simulation.',
        expectedOutput:
          'Tabular data extracted from Abaqus or LS-Dyna simulation results.',
      },
      {
        type: WidgetType.THERMOCALC,
        clientType: WidgetClientType.ThermoCalc,
        iconName: 'change_history',
        displayName: 'Thermocalc',
        id: null,
        widgetPurpose:
          'Enable HEXAIND 3.0 users to perform thermodynamic calculations using ThermoCalc API.',
        expectedInput:
          'Python scripts and input files for thermodynamic calculations.',
        expectedOutput:
          'Tabular data extracted from thermodynamic simulation results.',
      },
    ];
    this.applyFeatureFlagsToThirdPartyAPIWidgets();
    this.filteredThirdPartyAPIWidgets = [...this.thirdPartyAPIWidgets];
  }

  applyFeatureFlagsToAIMLWidgets() {
    this.AIMLWidgets = this.AIMLWidgets.filter((widget: any) => {
      return !this.featureFlagService.featureFlags?.disabledAIMLWidgets?.includes(
        widget.displayName,
      );
    });
  }

  applyFeatureFlagsToThirdPartyAPIWidgets() {
    this.thirdPartyAPIWidgets = this.thirdPartyAPIWidgets.filter(
      (widget: any) => {
        return !this.featureFlagService.featureFlags?.disabledThirdPartyWidgets?.includes(
          widget.displayName,
        );
      },
    );
  }

  searchWidgets() {
    if (this.searchTerm != '') {
      const term = this.searchTerm.toLowerCase();
      this.filteredDataWidgets = this.dataWidgets.filter((widget) =>
        widget.displayName.toLowerCase().includes(term),
      );
      this.showDataWidgets = this.filteredDataWidgets.length > 0 ? true : false;

      this.filteredAIMLWidgets = this.AIMLWidgets.filter((widget) =>
        widget.displayName.toLowerCase().includes(term),
      );
      this.showMachineLearningWidgets =
        this.filteredAIMLWidgets.length > 0 ? true : false;

      this.filteredCustomWidgets = this.customWidgets.filter((widget) =>
        widget.displayName.toLowerCase().includes(term),
      );
      this.showGeneralWidgets =
        this.filteredCustomWidgets.length > 0 ? true : false;

      this.filteredThirdPartyAPIWidgets = this.thirdPartyAPIWidgets.filter(
        (widget) => widget.displayName.toLowerCase().includes(term),
      );
      this.showThirdPartyAPIWidgets =
        this.filteredThirdPartyAPIWidgets.length > 0 ? true : false;

      this.filteredCustomCodePythonWidgets =
        this.customCodePythonWidgets.filter((widget) =>
          widget.displayName.toLowerCase().includes(term),
        );
      this.showCustomCodeWidgets =
        this.filteredCustomCodePythonWidgets.length > 0 ? true : false;
    } else {
      this.resetWidgets();
    }
  }

  getStartNodeWidget(widgets: Widget[]): Widget | undefined {
    return widgets.find(
      (widget) => widget.client_tags.ClientType === WidgetClientType.Start,
    );
  }

  getEndNodeWidget(widgets: Widget[]): Widget | undefined {
    return widgets.find(
      (widget) => widget.client_tags.ClientType === WidgetClientType.End,
    );
  }

  async publishWorkflow(result: any) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }

    let selectedWorkflowSession: WorkflowSession | undefined =
      this.workflowCanvasService.SelectedWorkflowSession;
    if (!selectedWorkflowSession || !selectedWorkflowSession._id) {
      return;
    }
    let saveAsWorkflow: SessionSaveAsWorkflow = new SessionSaveAsWorkflow();
    saveAsWorkflow.name = result.name;
    saveAsWorkflow.description = result.description;
    saveAsWorkflow.version_tag = result.version;
    saveAsWorkflow.user_name = result.owner;
    saveAsWorkflow.user_id = result.ownerId;

    try {
      var publishedWorkflowId = await this.sessionApi.PublishSessionWorkflow(
        this.configService.SelectedSiteId,
        selectedProjectId,
        selectedWorkflowSession._id,
        saveAsWorkflow,
      );
      if (publishedWorkflowId && selectedWorkflowSession._id) {
        const dialogRef = this.dialog.open(ConfirmationPrompComponent, {
          width: '300px',
          data: {
            action: 'publish',
          },
        });

        dialogRef.afterClosed().subscribe((result: any) => {
          if (result && result === true) {
            let queryParams = {
              siteId: this.configService.SelectedSiteId,
              projectId: selectedProjectId,
              workflowSessionId: selectedWorkflowSession?._id,
              versionedWorkflowId: publishedWorkflowId,
            };
            this.router.navigate(['/workflow-designer'], {
              queryParams,
            });
            this.workflowDesignerHeader.updateDataFromParent(
              'Refresh the published workflow list',
            );
          } else {
            this.workflowDesignerHeader.updateDataFromParent(
              'Refresh the published workflow list',
            );
          }
        });
      }
    } catch {
      this.notificationComponent.display(
        'An error has occurred publishing the workflow: ' +
          (this.sharedDataService.LastError ??
            'An unknown error has occurred.'),
        'error',
      );
      return;
    }

    this.notificationComponent.display(
      'The workflow was published successfully.',
      'success',
    );
  }

  onPublishWorkflow() {
    const dialogRef = this.dialog.open(PublishWorkflowComponent, {
      width: '500px',
      data: { isDuplicate: false },
    });

    dialogRef.afterClosed().subscribe((result: any) => {
      if (result) {
        this.publishWorkflow(result);
      }
    });
  }
  captureScreenshot() {
    const canvasElement = document.getElementById(
      'myCanvas',
    ) as HTMLCanvasElement;
    if (canvasElement) {
      return canvasElement.toDataURL('image/png');
    } else {
      return null;
    }
  }

  onCreateWorkflowTemplate(event: any) {
    let data: any = {
      workflow_id: event.workflow_id,
      sessionId: this.workflowCanvasService.SelectedWorkflowSession?._id,
      screenshot: this.captureScreenshot(),
    };
    const dialogRef = this.dialog.open(CreateNewWorkflowTemplateComponent, {
      width: '500px',
      data: data,
    });

    dialogRef.afterClosed().subscribe((result: any) => {});
  }

  onLoadWorkflowTemplate(event: any) {
    const dialogRef = this.dialog.open(LoadWorkflowTemplatesDialogComponent, {
      width: '80%',
      height: '80%',
      data: {},
    });
    dialogRef.afterClosed().subscribe((result: any) => {
      if (result) {
        let workflow: any = this.workflowCanvasService.SelectedWorkflow;
        workflow.widgets = result.workflow.widgets;
        for (let i = 0; i < workflow.widgets.length; i++) {
          workflow.widgets[i].state = 'IDLE';
        }
        workflow.start = result.workflow.start;
        workflow.end = result.workflow.end;
        workflow.client_tags = result.workflow.client_tags;
        workflow.partial_widgets = result.workflow.partial_widgets;
        this.workflowCanvasService.SelectedWorkflow = workflow;
        this.workflowCanvasService.applyTemplateWidgets(this.widgetSize);

        setTimeout(() => {
          this.startCanvasDrawing();
        }, 150);
      }
    });
  }

  async saveWorkflow(runFlag: boolean = false): Promise<boolean> {
    this.workflowCanvasService.saveWorkflowResponse = false;
    this.workflowCanvasService.clearNewDraggedWidgetsList();
    // if (!this.validateWorkflowToSave()) {
    //   return false;
    // }

    if (this.doesUserUsedTheZoomFunctionality()) {
      this.isWorkflowSaveApiInprogress = true;
      this.previousZoomLevel = this.zoomLevel;
      this.zoomLevel = this.initialZoomLevelOnScreenLoad;
      this.applyZoom();
    }
    this.workflowCanvasService.changeMadeToWorkflow = false;

    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return false;
    }

    let selectedWorkflowSession: WorkflowSession | undefined =
      this.workflowCanvasService.SelectedWorkflowSession;
    if (
      !selectedWorkflowSession ||
      !selectedWorkflowSession._id ||
      !this.workflowCanvasService.SelectedWorkflow
    ) {
      this.notificationComponent.display(
        'Workflow could not be found.',
        'error',
      );
      return false;
    }

    let sessionWorkflow: SessionWorkflow = new SessionWorkflow();
    sessionWorkflow.widgets =
      this.workflowCanvasService.SelectedWorkflow.widgets.filter(
        (t) => t.type !== WidgetType.UX,
      );
    sessionWorkflow.client_tags =
      this.workflowCanvasService.SelectedWorkflow.client_tags;
    sessionWorkflow.user_id =
      this.workflowCanvasService.SelectedWorkflow.owner_id;
    sessionWorkflow.user_name =
      this.workflowCanvasService.SelectedWorkflow.owner_name;
    sessionWorkflow.start = this.workflowCanvasService.SelectedWorkflow.start;
    sessionWorkflow.end = this.workflowCanvasService.SelectedWorkflow.end;

    let startWidget = this.getStartNodeWidget(
      this.workflowCanvasService.SelectedWorkflow.widgets,
    );

    let endWidget = this.getEndNodeWidget(
      this.workflowCanvasService.SelectedWorkflow.widgets,
    );

    if (startWidget) {
      sessionWorkflow.client_tags.StartWidgetPosition = new Position(
        Widget.GetPositionX(startWidget),
        Widget.GetPositionY(startWidget),
      );
    }

    if (endWidget) {
      sessionWorkflow.client_tags.EndWidgetPosition = new Position(
        Widget.GetPositionX(endWidget),
        Widget.GetPositionY(endWidget),
      );
    }

    if (this.workflowCanvasService.arrows) {
      let uniqueArrows = new Set();
      let arrow_cache: any[] = [];
      this.workflowCanvasService.arrows.forEach((arrow) => {
        if (
          arrow.startPoint.widgetControl.Widget.urn &&
          arrow.endPoint.widgetControl.Widget.urn
        ) {
          let key =
            arrow.startPoint.widgetControl.Widget.urn +
            arrow.endPoint.widgetControl.Widget.urn;
          if (uniqueArrows.has(key)) return;
          uniqueArrows.add(key);
        }
        arrow_cache.push({
          start_urn: arrow.startPoint.widgetControl.Widget.urn,
          start_connector_point_type: arrow.startPoint.connectorPointType,
          end_urn: arrow.endPoint.widgetControl.Widget.urn,
          end_connector_point_type: arrow.endPoint.connectorPointType,
          arrow_type: arrow.arrowType,
        });
      });
      sessionWorkflow.client_tags!.Arrows = arrow_cache;
    }
    try {
      let saveResponse: any = {};
      let removeDefaults: SessionWorkflow = new SessionWorkflow();
      removeDefaults = JSON.parse(JSON.stringify(sessionWorkflow));
      removeDefaults?.widgets.forEach((widget: any) => {
        if (widget?.config?.widget_type === 'FILTER') {
          if (
            widget?.config?.config?.filter_operands.length == 0 &&
            widget?.config?.config?.filter_values.length == 0
          ) {
            delete widget?.config?.config?.filter_operands;
            delete widget?.config?.config?.filter_values;
          }
        }
        if (widget?.config?.widget_type === 'RENAME_COLUMNS') {
          const columnsToRename = widget?.config?.config?.columns_to_rename;
          if (columnsToRename && Object.keys(columnsToRename).length == 0) {
            delete widget.config.config.columns_to_rename;
          }
        }
        if (widget?.config?.widget_type === 'DATATYPE_CONVERSION') {
          const dataTypeConversion =
            widget?.config?.config?.column_type_mapping;
          if (
            dataTypeConversion &&
            Object.keys(dataTypeConversion).length == 0
          ) {
            delete widget.config.config.column_type_mapping;
          }
        }
        if (widget?.config?.widget_type === 'DROP_COLUMNS') {
          const dropColumns = widget?.config?.config?.selected_columns;
          if (Array.isArray(dropColumns) && dropColumns.length == 0) {
            delete widget.config.config.selected_columns;
          }
        }
        if (widget?.config?.widget_type === 'DROP_MISSING') {
          const dropMissing = widget?.config?.config?.selected_columns;
          if (Array.isArray(dropMissing) && dropMissing.length == 0) {
            delete widget.config.config.selected_columns;
          }
        }
        if (widget?.config?.widget_type === 'DATA_COPY') {
          const dataConfiguration = widget?.config?.source?.configuration;
          if (dataConfiguration && dataConfiguration?.dataset_id === '') {
            delete widget?.config?.source?.configuration.dataset_id;
          }
        }
        if (widget?.config?.widget_type === 'SAVE') {
          const saveConfig = widget?.config?.datasetConfig;
          if (Array.isArray(saveConfig) && saveConfig.length == 0) {
            delete widget?.config?.datasetConfig;
          }
        }
        if (
          widget?.config?.widget_type === 'ACTIVE_LEARNING' ||
          widget?.config?.widget_type === 'MOBO'
        ) {
          const AIMLConfig = widget?.config?.features_detail;
          if (Array.isArray(AIMLConfig) && AIMLConfig.length == 0) {
            delete widget?.config?.input_variables;
          }
        }
        if (
          widget?.config?.widget_type === 'SVM' ||
          widget?.config?.widget_type === 'GPR'
        ) {
          const svmGprConfigInput = widget?.config?.input_cols;
          const svmGprConfigOutput = widget?.config?.output_cols;
          if (
            (Array.isArray(svmGprConfigInput) &&
              svmGprConfigInput.length == 0) ||
            (Array.isArray(svmGprConfigOutput) &&
              svmGprConfigOutput.length == 0)
          ) {
            delete widget?.config?.input_cols;
            delete widget?.config?.output_cols;
          }
        }
        if (widget?.config?.widget_type === 'LOOP_END') {
          const loopTermination = widget?.config?.on_termination;
          const onLoop = widget?.config?.on_loop;
          if (
            (Array.isArray(loopTermination) && loopTermination.length == 0) ||
            (Array.isArray(onLoop) && onLoop.length == 0)
          ) {
            delete widget?.config?.on_termination;
            delete widget?.config?.on_loop;
          }
        }
        if (widget?.config?.widget_type === 'LOOP_START') {
          const loopStartInputs = widget?.inputs;
          if (Array.isArray(loopStartInputs) && loopStartInputs.length == 0) {
            delete widget?.config?.loop_start_config;
          }
        }
        // if(widget?.config?.widget_type === "CUSTOM_CODE"){
        //   if(widget?.inputs.length>0){
        //     widget?.inputs.forEach((element:any) => {
        //       if(element.name === '<ToBeModifiedDuringWidgetRunTimeByUI>' || element.urn === '<ToBeModifiedDuringWidgetRunTimeByUI>'){
        //         element.name = null;
        //         element.urn = null;
        //       }
        //     });
        //   }
        // }
      });
      if (this.workflowCanvasService.IsVersionedWorkflow) {
        saveResponse = await this.apiService.UpdateWorkflow(
          this.configService.SelectedSiteId,
          selectedProjectId,
          this.workflowCanvasService.SelectedWorkflow,
          this.workflowCanvasService.arrows,
        );
      } else {
        saveResponse = await this.sessionApi.SaveSessionWorkflow(
          this.configService.SelectedSiteId,
          selectedProjectId,
          selectedWorkflowSession._id,
          removeDefaults,
        );
      }
      // this if will run only in onRunWorkflow case
      if (
        saveResponse &&
        Array.isArray(saveResponse.invalid_widgets) &&
        saveResponse.invalid_widgets.length > 0 &&
        runFlag
      ) {
        this.workflowCanvasService.saveWorkflowResponse = true;
        this.workflowCanvasService.invalid_widgets =
          saveResponse.invalid_widgets;
        this.toaster.warning(
          'Cannot run. There are invalid widgets in the workflow!',
          'WARNING',
          {
            positionClass: 'custom-toast-position',
          },
        );
        return false;
      } else {
        // this  will run only in onSaveWorkflow case
        if (!runFlag) {
          this.workflowCanvasService.updateWorkflowToBeSaved();
          this.notificationComponent.display(
            'The workflow was saved successfully.',
            'success',
          );
        }
      }
      if (saveResponse) {
        this.workflowCanvasService.saveWorkflowResponse = true;
        this.workflowCanvasService.invalid_widgets =
          saveResponse.invalid_widgets;
      }

      if (
        this.workflowDesignerService.getSaveTriggeredFrom() == 'INTERACTIVE'
      ) {
        this.workflowDesignerService.setSaveTriggeredFrom('');
        this.workflowDesignerService.setTriggerExecuteWidget(true);
      }
    } catch (error: any) {
      console.error(error);
      if (this.doesUserUsedTheZoomFunctionality()) {
        this.revertBackToSelectedZoomLevelAfterSaving();
      }

      if (error.isWidgetMissingFieldsError) {
        this.notificationComponent.display(
          'Following fields are not configured properly in the widgets:' +
            error.messageString,
          'error',
        );
        return false;
      }

      // General error handling for unknown errors
      this.notificationComponent.display(
        'An error has occurred saving the workflow: ' +
          (this.sharedDataService.LastError ??
            'An unknown error has occurred.'),
        'error',
      );

      return false;
    }

    if (this.doesUserUsedTheZoomFunctionality())
      this.revertBackToSelectedZoomLevelAfterSaving();
    return true;
  }

  /**
   * If the user used the zoom functionality then zoomLevel will change. we will be using only one value of zoom which is {@link this.initialZoomLevelOnScreenLoad}
   * to save the coordinates in the database, so whenever the zoom value changes we zoom the canvas but
   *  we will only save the coordinates of the widget at zoom value of {@link this.initialZoomLevelOnScreenLoad}.
   */
  doesUserUsedTheZoomFunctionality() {
    return this.zoomLevel != this.defaultZoomLevel;
  }

  /**
   * We saved the workflow using this zoom level {@link this.initialZoomLevelOnScreenLoad} in the save api, and now after saving we revert back to the
   * current zoom which is set by user which is stored in {@link previousZoomLevel}.
   */

  revertBackToSelectedZoomLevelAfterSaving() {
    this.zoomLevel = this.previousZoomLevel;
    this.applyZoom();
    this.isWorkflowSaveApiInprogress = false;
    this.startCanvasDrawing();
  }

  toggleNav() {
    this.navService.toggleNav();
    if (this.navService.isNavCollapsed) {
      const leftDiv = document.getElementById('left');
      const rightDiv = document.getElementById('designer');

      if (leftDiv) leftDiv.style.width = `50px`;
      if (rightDiv) rightDiv.style.width = `100%`;
    }

    // this.resizeCanvas();
    setTimeout(() => {
      this.resizeCanvas();
    }, 300); // 2000 milliseconds = 2 seconds
  }

  getContextMenuWidth(): number {
    const contextMenu = this.eRef.nativeElement.querySelector('.context-menu');
    if (!contextMenu) return 0;
    // Temporarily show and move the context menu off-screen for measuring
    contextMenu.style.display = 'block';
    contextMenu.style.left = '-9999px';
    const width = contextMenu.offsetWidth;
    // Reset the styles
    contextMenu.style.display = 'none';
    contextMenu.style.left = '0px';

    return width;
  }

  sortWidgetControlsByZIndexDesc(): WidgetControl[] {
    // Create a copy of the activities array to avoid mutating the original array
    return [...this.workflowCanvasService.widgetControls].sort(
      (a, b) => a.ZIndex - b.ZIndex,
    );
  }

  getWidgetControlWithHighestZIndex(): WidgetControl | undefined {
    return this.workflowCanvasService.widgetControls.reduce((prev, current) => {
      return prev.ZIndex > current.ZIndex ? prev : current;
    }, this.workflowCanvasService.widgetControls[0]);
  }

  getWidgetControlWithLowestZIndex(): WidgetControl | undefined {
    return this.workflowCanvasService.widgetControls.reduce((prev, current) => {
      return prev.ZIndex < current.ZIndex ? prev : current;
    }, this.workflowCanvasService.widgetControls[0]);
  }

  resizeCanvas() {
    const canvasContainer = document.getElementById('canvasContainer');
    if (this.canvas && canvasContainer) {
      this.canvas.nativeElement.width = canvasContainer.offsetWidth;
      this.canvas.nativeElement.height = canvasContainer.offsetHeight;
    }
  }

  onCloseMountedDrivePanel() {
    this.IsShowingMountedDriveFileSelector = false;
  }

  public AddWidgetControlToCanvas(
    widgetType: WidgetType,
    widgetClientType: WidgetClientType,
    widget_id: string | null = null,
    widget_name: string | null = null,
    positionX: number = -1,
    positionY: number = -1,
  ): WidgetControl | undefined {
    this.workflowCanvasService.changeMadeToWorkflow = true;

    let widgetControl: WidgetControl | undefined =
      this.workflowCanvasService.CreateNewWidgetControl(
        widgetType,
        widgetClientType,
        positionX,
        positionY,
        this.widgetSize,
        widget_id,
        widget_name,
      );

    if (widgetControl) {
      this.workflowCanvasService.selectedWidgetControl = widgetControl;
      this.showConfigByWidgetType();
    }
    let newWidgetUrn = widgetControl?.Widget?.urn;
    this.workflowCanvasService.newDraggedWidgetsList = newWidgetUrn;
    return widgetControl;
  }

  moveCanvasFreely(deltaX: number, deltaY: number) {
    if (!this.canvas) {
      return;
    }

    const canvasEl: HTMLCanvasElement = this.canvas.nativeElement;
    const canvasWidth = canvasEl.offsetWidth;
    const canvasHeight = canvasEl.offsetHeight;

    const allWidgets = this.workflowCanvasService.widgetControls;

    allWidgets.forEach((widget) => {
      widget.Widget.client_tags.PositionX += deltaX;
      widget.Widget.client_tags.PositionY += deltaY;
    });

    this.workflowCanvasService.UpdateConnectors();
  }

  moveCanvas(deltaX: number, deltaY: number) {
    if (!this.canvas) {
      return;
    }

    const canvasEl: HTMLCanvasElement = this.canvas.nativeElement;
    const canvasWidth = canvasEl.offsetWidth;
    const canvasHeight = canvasEl.offsetHeight;

    const allWidgets = this.workflowCanvasService.widgetControls;
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;

    allWidgets.forEach((widget) => {
      const widgetX = widget.Widget.client_tags.PositionX;
      const widgetY = widget.Widget.client_tags.PositionY;
      const widgetWidth = widget.Widget.client_tags.Width || 50;
      const widgetHeight = widget.Widget.client_tags.Height || 50;

      if (widgetX < minX) minX = widgetX;
      if (widgetY < minY) minY = widgetY;
      if (widgetX + widgetWidth > maxX) maxX = widgetX + widgetWidth;
      if (widgetY + widgetHeight > maxY) maxY = widgetY + widgetHeight;
    });

    const newMinX = minX + deltaX;
    const newMinY = minY + deltaY;
    const newMaxX = maxX + deltaX;
    const newMaxY = maxY + deltaY;

    if (newMinX < 0) {
      deltaX = -minX;
    }
    if (newMinY < 0) {
      deltaY = -minY;
    }
    if (newMaxX > canvasWidth) {
      deltaX = canvasWidth - maxX;
    }
    if (newMaxY > canvasHeight) {
      deltaY = canvasHeight - maxY;
    }

    allWidgets.forEach((widget) => {
      widget.Widget.client_tags.PositionX += deltaX;
      widget.Widget.client_tags.PositionY += deltaY;
    });

    this.workflowCanvasService.UpdateConnectors();
  }

  showDataPreviewIcon() {
    if (!this.hoveringArrow) {
      return false;
    }

    if (!this.workflowCanvasService.IsViewingRunMode) return false;

    if (
      this.hoveringArrow.startPoint.widgetControl.Widget.type === WidgetType.UX
    ) {
      return false;
    }

    return true;
  }

  createDataPreviewHoverIcon(connector: Arrow) {
    const curveFactor = 0.6;

    let controlPoints: any = this.workflowCanvasService.calculateControlPoints(
      { x: connector.startPoint.x, y: connector.startPoint.y },
      { x: connector.endPoint.x, y: connector.endPoint.y },
      curveFactor,
    );

    const midpoint = this.workflowCanvasService.getPointOnBezierCurve(
      connector.startPoint,
      controlPoints.controlPoint1,
      controlPoints.controlPoint2,
      connector.endPoint,
      0.5,
    );

    this.workflowCanvasService.createDataPreviewHoverIcon(
      midpoint.x,
      midpoint.y,
    );
  }

  removeUnHoveredIcons() {
    this.workflowCanvasService.arrows.forEach((connector) => {
      if (this.hoverStates.get(connector.uniqueId)) {
        // Previously hovered but now not, hide or remove icon
        const iconId = `icon-${connector.uniqueId}`;
        const existingIcon = document.getElementById(iconId);
        if (existingIcon) {
          existingIcon.remove();
        }
        this.hoverStates.set(connector.uniqueId, false);
      }
    });
  }

  calculateConnectorMidpoint(connector: any): { x: number; y: number } {
    const mx = (connector.startPoint.x + connector.endPoint.x) / 2;
    const my = (connector.startPoint.y + connector.endPoint.y) / 2;
    return { x: mx, y: my };
  }

  drawConnectorHoverEffects(connector: any): void {
    if (!this.hoverStates.get(connector.uniqueId)) return;
    // Assuming calculateConnectorMidpoint correctly calculates the midpoint of the curve
    const midpoint = this.calculateConnectorMidpoint(connector);

    // Draw circle around the midpoint
    const radius = 40; // Adjust as needed for visual preference
    if (this.ctx) {
      this.ctx.beginPath();
      this.ctx.arc(midpoint.x, midpoint.y, radius, 0, 2 * Math.PI);
      this.ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'; // Semi-transparent white for hover effect
      this.ctx.fill();
      this.ctx.strokeStyle = '#007bff'; // Blue border for the circle
      this.ctx.lineWidth = 2;
      this.ctx.stroke();
    }
  }

  hideTooltip(): void {
    const tooltip = document.getElementById('tooltip');
    tooltip!.style.display = 'none';
    clearTimeout(this.tooltipTimeout);
  }

  openDataPreviewDialog(dataset: string | DatasetModel[]) {
    const dialogRef = this.dialog.open(DataPreviewComponent, {
      width: '95vw',
      maxWidth: '95vw',
      height: '95%',
      data: {
        datasetId: dataset,
      },
    });
    dialogRef.afterClosed().subscribe((result) => {});
  }

  async showDataSetPreview() {
    if (!this.hoveringArrow) {
      return;
    }
    let widgetControl: WidgetControl =
      this.hoveringArrow.startPoint.widgetControl;
    let widgetName = widgetControl.Widget.type;
    let widgetUrn = widgetControl.Widget.urn;

    if (!widgetName || !widgetUrn) {
      console.error('Widget name or URN is undefined.');
      return;
    }

    if (
      widgetName === 'RESCALE' &&
      this.checkWidgetStatus(widgetUrn) === 'running'
    ) {
      const widgetStatus = this.checkWidgetStatus(widgetUrn);
      if (widgetStatus === 'running') {
        const rescaleDatasetId =
          this.sharedDataService.getRescaleDatasetId(widgetUrn);
        if (rescaleDatasetId) {
          this.openDataPreviewDialog(rescaleDatasetId);
        } else {
          console.log(
            'Data is not yet available. Please wait for the Rescale widget to finish processing.',
          );
        }
        return;
      } else {
        console.error(
          `Rescale widget is not running. Current status: ${widgetStatus}`,
        );
        return;
      }
    } else {
      let datasetIds: DatasetModel[] | string | undefined =
        await this.workflowCanvasService.GetResultDatasetIdsForWidgetControl(
          widgetControl,
        );

      if (datasetIds) {
        this.openDataPreviewDialog(datasetIds);
      }
    }
  }

  openCPWPreveiwDialog(results: WidgetRunResult[]) {
    if (results.length > 0) {
      let visualizationData = results.filter(
        (result: any) => result.result_type === 'VISUALIZATION',
      );
      if (visualizationData.length > 0) {
        let plots = [];
        for (let i = 0; i < visualizationData.length; i++) {
          let result_value: any = visualizationData[i]?.result_value;
          let url = result_value.string_value;
          if (url && url != '') {
            plots.push(
              this.sanitizer.bypassSecurityTrustResourceUrl(
                `${this.configService.getAppAuxApiURL}/eda/file?path=${url}`,
              ),
            );
          }
          if (i == visualizationData.length - 1) {
            const dialogRef = this.dialog.open(DataVisualizationComponent, {
              width: '95vw',
              maxWidth: '95vw',
              height: '95%',
              data: {
                type: 'CPW',
                plots: plots,
              },
            });
            dialogRef.afterClosed().subscribe((result) => {});
          }
        }
      }
    }
  }

  checkWidgetStatus(widgetUrn: string): string | null {
    const workflowRunStatus = this.workflowCanvasService.WorkflowRunStatus;

    if (workflowRunStatus) {
      const widgetStatus = workflowRunStatus.widgets_status.find(
        (widget) => widget.urn === widgetUrn,
      );

      if (widgetStatus && widgetStatus.status) {
        return widgetStatus.status.toLowerCase();
      }
    }

    return null;
  }

  public handleCanvasKeyDown(event: KeyboardEvent) {
    this.hideTooltip();
    if (event.key === 'Escape') {
      this.showCanvasContextMenu = false;
    } else if (event.key === 'Delete' || event.key === 'Backspace') {
      if (
        this.workflowCanvasService.IsViewingRunMode ||
        this.workflowCanvasService.IsVersionedWorkflow
      ) {
        return;
      }

      // Multiple Arrow Deletion
      if (this.selectedArrows.length > 0) {
        this.selectedArrows.forEach((arrowToDelete) => {
          if (arrowToDelete) {
            // Delete the arrow from the array
            this.workflowCanvasService.arrows =
              this.workflowCanvasService.arrows.filter(
                (arrow) => arrow !== arrowToDelete,
              );

            // Find and remove the corresponding icon
            const iconToRemove = document.querySelector(
              `[data-arrow-id='${arrowToDelete.uniqueId}']`,
            );
            if (iconToRemove) {
              iconToRemove.remove();
            }

            // Update LoopEndWidgetConfig if applicable
            if (
              arrowToDelete.startPoint.widgetControl.Widget.type ===
              WidgetType.LOOP_END
            ) {
              const loopEndWidgetConfig: LoopEndWidgetConfig = arrowToDelete
                .startPoint.widgetControl.Widget.config as LoopEndWidgetConfig;
              if (arrowToDelete.arrowType === ArrowType.OnTermianteLoop) {
                loopEndWidgetConfig.on_termination =
                  loopEndWidgetConfig.on_termination.filter(
                    (c) =>
                      c !== arrowToDelete.startPoint.widgetControl.Widget.urn,
                  );
              } else {
                loopEndWidgetConfig.on_loop =
                  loopEndWidgetConfig.on_loop.filter(
                    (c) =>
                      c !== arrowToDelete.startPoint.widgetControl.Widget.urn,
                  );
              }
            }

            // Update on_success array
            const urn = arrowToDelete.endPoint.widgetControl.Widget.urn;
            if (urn) {
              arrowToDelete.startPoint.widgetControl.Widget.on_success =
                arrowToDelete.startPoint.widgetControl.Widget.on_success.filter(
                  (c) => c !== urn,
                );
            }
          }
        });

        // Clear the selected arrows array after deletion
        this.selectedArrows = [];
      }

      // Multiple Widget Deletion
      const selectedWidgets = this.workflowCanvasService.selectedWidgetControls;
      if (selectedWidgets.length > 0) {
        selectedWidgets.forEach((selectedWidgetControl) => {
          // Remove any arrows connected to the selected widget control
          this.workflowCanvasService.arrows =
            this.workflowCanvasService.arrows.filter(
              (connector) =>
                connector.startPoint.widgetControl !== selectedWidgetControl &&
                connector.endPoint.widgetControl !== selectedWidgetControl,
            );

          // Remove the widget control
          const indexToRemove =
            this.workflowCanvasService.widgetControls.findIndex(
              (widget) =>
                widget.Widget.urn === selectedWidgetControl.Widget.urn,
            );
          if (indexToRemove !== -1) {
            this.workflowCanvasService.widgetControls.splice(indexToRemove, 1);
            this.workflowCanvasService.SelectedWorkflow!.widgets =
              this.workflowCanvasService.SelectedWorkflow!.widgets.filter(
                (widget) => widget.urn !== selectedWidgetControl.Widget.urn,
              );
          }

          // Remove urn from on_success array of any widgets that reference the deleted widget
          this.workflowCanvasService.widgetControls.forEach((widgetControl) => {
            widgetControl.Widget.on_success =
              widgetControl.Widget.on_success.filter(
                (urn) => urn !== selectedWidgetControl.Widget.urn,
              );
          });
        });

        // Clear the selected widgets array after deletion
        this.clearAllHighlights();
        if (this.componentRef) {
          this.componentRef.destroy();
        }
        this.componentRef = null;
        this.workflowCanvasService.setSelectedWidgetControls([]);
        this.workflowCanvasService._selectedWorkflow.next(
          this.workflowCanvasService.SelectedWorkflow,
        );
      }
    } else if (event.ctrlKey && event.key === 'c') {
      // clone widget
      const selectedWidgets = this.workflowCanvasService.selectedWidgetControls;
      if (selectedWidgets.length > 0) {
        this.selectedWidgetsToCopy = selectedWidgets;
      }
    } else if (event.ctrlKey && event.key === 'v') {
      // paste widget
      if (this.selectedWidgetsToCopy.length > 0) {
        this.selectedWidgetsToCopy.forEach((selectedWidgetControl) => {
          if (
            selectedWidgetControl.Widget.urn !== 'START' &&
            selectedWidgetControl.Widget.urn !== 'END'
          ) {
            const indexToPaste =
              this.workflowCanvasService.widgetControls.findIndex(
                (widget) =>
                  widget.Widget.urn === selectedWidgetControl.Widget.urn,
              );
            if (indexToPaste !== -1) {
              let widgetid: any = null;
              let widgetname = null;
              if (selectedWidgetControl.Widget.type === 'CUSTOM_CODE') {
                const config = selectedWidgetControl.Widget
                  .config as CustomCodeWidgetConfig;
                widgetid = config.widget_id;
                if (widgetid) {
                  widgetname = this.customCodePythonWidgets.find(
                    (item) => item.id === widgetid,
                  )?.displayName;
                }
              }

              let newWidget = this.AddWidgetControlToCanvas(
                selectedWidgetControl.Widget.type,
                selectedWidgetControl.Widget.client_tags.ClientType,
                widgetid,
                widgetname,
              );
              if (newWidget && newWidget.Widget) {
                newWidget.Widget.config = selectedWidgetControl.Widget.config;
              }
            }
          }
        });

        // auto select the copied widget
        this.showConfigByWidgetType();

        this.selectedWidgetsToCopy = [];
      }
    }
  }

  public onCanvasMouseDown(event: MouseEvent): void {
    if (!this.workflowCanvasService) {
      return;
    }
    const canvasEl: HTMLCanvasElement = this.canvas!.nativeElement;
    const canvasRect = canvasEl.getBoundingClientRect();

    this.mouseClickPositionX = event.clientX - canvasRect.left;
    this.mouseClickPositionY = event.clientY - canvasRect.top;

    let dataPreviewHoverIconClicked: boolean =
      this.workflowCanvasService.IsDataPreviewHoverButtonClicked(
        this.mouseClickPositionX,
        this.mouseClickPositionY,
      );

    if (dataPreviewHoverIconClicked) {
      this.showDataSetPreview();
      return;
    }

    this.workflowCanvasService.destroyDataPreviewHoverIcon();

    let selectedWidgetControl: WidgetControl | undefined =
      this.workflowCanvasService.GetWidgetUnderPointer(
        this.mouseClickPositionX,
        this.mouseClickPositionY,
      );

    if (selectedWidgetControl) {
      const selectedWidgets = this.workflowCanvasService.selectedWidgetControls;
      if (event.ctrlKey) {
        const index = selectedWidgets.indexOf(selectedWidgetControl);
        if (index !== -1) {
          selectedWidgetControl.backgroundColor = null;
          const updatedSelection = [...selectedWidgets];
          updatedSelection.splice(index, 1);
          this.workflowCanvasService.setSelectedWidgetControls(
            updatedSelection,
          );
        } else {
          this.workflowCanvasService.setSelectedWidgetControls([
            ...selectedWidgets,
            selectedWidgetControl,
          ]);
          if (this.workflowCanvasService.selectedWidgetControls.length > 1) {
            selectedWidgetControl.backgroundColor = 'rgba(173, 216, 230, 0.3)';
          }
        }
      } else {
        // Handle single widget selection
        this.clearAllHighlights();
        selectedWidgetControl.backgroundColor = null; // No background for single selection
        this.workflowCanvasService.setSelectedWidgetControls([
          selectedWidgetControl,
        ]);
      }

      this.workflowCanvasService.IsMovingWidget = true;
      this.dragOffsetX =
        this.mouseClickPositionX - selectedWidgetControl.GetPositionX();
      this.dragOffsetY =
        this.mouseClickPositionY - selectedWidgetControl.GetPositionY();

      this.showConfigByWidgetType();
      if (this.hideConfigs()) {
        return;
      }
      return;
    }

    if (this.hoveringArrow != undefined) {
      const index = this.selectedArrows.indexOf(this.hoveringArrow);

      if (index !== -1) {
        this.selectedArrows[index].hovered = false;
        this.selectedArrows[index].selected = false;
        this.selectedArrows.splice(index, 1);
      } else {
        this.hoveringArrow.selected = true;
        this.selectedArrows.push(this.hoveringArrow);
      }

      this.hoveringArrow = undefined;
    } else if (this.selectedArrows.length > 0) {
      this.selectedArrows.forEach((arrow) => (arrow.selected = false));
      this.selectedArrows = [];
    }

    if (!this.workflowCanvasService.IsVersionedWorkflow) {
      this.workflowCanvasService.IsMovingWidget = false;

      let selectedConnectorPoint =
        this.workflowCanvasService.GetConnectorPointUnderMousePointer(
          this.mouseClickPositionX,
          this.mouseClickPositionY,
        );

      if (selectedConnectorPoint) {
        this.workflowCanvasService.IsDrawingArrow = true;
        this.workflowCanvasService.DrawingStartConnectorPoint =
          selectedConnectorPoint;
        return;
      }
    }

    if (!event.ctrlKey) {
      this.clearAllHighlights();
      this.workflowCanvasService.setSelectedWidgetControls([]);
    }

    // Logic for panning if not over a widget
    this.isPanning = true;
    this.panStartX = event.clientX;
    this.panStartY = event.clientY;
    document.body.style.cursor = 'pointer';
  }

  private clearAllHighlights(): void {
    this.workflowCanvasService.selectedWidgetControls.forEach(
      (widgetControl) => {
        widgetControl.backgroundColor = null;
      },
    );
  }

  public onCanvasMouseUp(): void {
    document.body.style.cursor = 'default';

    if (
      this.workflowCanvasService.IsDrawingArrow &&
      this.workflowCanvasService.HoveringArrowToWidgetControl &&
      this.workflowCanvasService.DrawingStartConnectorPoint
    ) {
      let startPoint: ConnectorPoint =
        this.workflowCanvasService.DrawingStartConnectorPoint;
      let endPoint: ConnectorPoint =
        this.workflowCanvasService.FindClosestConnector(
          this.workflowCanvasService.HoveringArrowToWidgetControl,
          this.mouseX,
          this.mouseY,
        );

      if (
        endPoint.widgetControl.Widget.client_tags.ClientType ===
        WidgetClientType.Filter
      ) {
        const existingConnections = this.workflowCanvasService.arrows.filter(
          (arrow) =>
            arrow.endPoint.widgetControl.Widget.urn ===
            endPoint.widgetControl.Widget.urn,
        );

        if (existingConnections.length >= 1) {
          this.notificationComponent.display(
            'Filter widget can only accept a single input connection.',
            'warning',
          );
          this.resetArrowDrawing();
          return;
        }
      }

      if (
        startPoint.widgetControl.Widget.client_tags.ClientType ===
        WidgetClientType.Start
      ) {
        if (
          this.workflowCanvasService.arrows.find(
            (t) =>
              t.startPoint.widgetControl.Widget.client_tags.ClientType ===
              WidgetClientType.Start,
          )
        ) {
          this.notificationComponent.display(
            'The start widget already has a connection.',
            'success',
          );
          this.resetArrowDrawing();
          return;
        }
      }

      if (
        endPoint.widgetControl.Widget.client_tags.ClientType ===
        WidgetClientType.End
      ) {
        if (
          this.workflowCanvasService.arrows.find(
            (t) =>
              t.endPoint.widgetControl.Widget.client_tags.ClientType ===
              WidgetClientType.End,
          )
        ) {
          this.notificationComponent.display(
            'The end widget already has a connection.',
            'success',
          );
          this.resetArrowDrawing();
          return;
        }
      }

      if (
        this.workflowCanvasService.arrows.find(
          (t) =>
            t.startPoint.widgetControl.Widget.urn ===
              startPoint.widgetControl.Widget.urn &&
            t.endPoint.widgetControl.Widget.urn ===
              endPoint.widgetControl.Widget.urn,
        )
      ) {
        this.notificationComponent.display(
          'That connection already exists.',
          'success',
        );
        this.resetArrowDrawing();
        return;
      }

      let arrow = new Arrow(
        startPoint,
        endPoint,
        this.connectingPointsType,
        `arrow-${Date.now()}${Math.random()}`,
      );
      this.workflowCanvasService.arrows.push(arrow);
      if (
        arrow.startPoint.widgetControl.Widget.client_tags.ClientType ===
        WidgetClientType.Start
      ) {
        if (arrow.startPoint.widgetControl.Widget.urn) {
          let startWidgetUrn = arrow.endPoint.widgetControl.Widget.urn;
          if (startWidgetUrn && this.workflowCanvasService.SelectedWorkflow) {
            this.workflowCanvasService.SelectedWorkflow.start.length = 0;
            this.workflowCanvasService.SelectedWorkflow.start.push(
              startWidgetUrn,
            );
          }
        }
      } else if (
        arrow.endPoint.widgetControl.Widget.client_tags.ClientType ===
        WidgetClientType.End
      ) {
        if (arrow.endPoint.widgetControl.Widget.urn) {
          let endWidgetUrn = arrow.startPoint.widgetControl.Widget.urn;
          if (endWidgetUrn && this.workflowCanvasService.SelectedWorkflow) {
            this.workflowCanvasService.SelectedWorkflow.end.length = 0;
            this.workflowCanvasService.SelectedWorkflow.end.push(endWidgetUrn);
          }
        }
      } else {
        if (arrow.endPoint.widgetControl.Widget.urn) {
          if (
            arrow.startPoint.widgetControl.Widget.on_success.indexOf(
              arrow.endPoint.widgetControl.Widget.urn,
            ) == -1
          ) {
            arrow.startPoint.widgetControl.Widget.on_success.push(
              arrow.endPoint.widgetControl.Widget.urn,
            );
          }
        }
      }
    }

    this.resetArrowDrawing();
  }

  public onCanvasMouseMove(event: MouseEvent): void {
    document.body.style.cursor = 'default';

    this.workflowCanvasService.destroyDataPreviewHoverIcon();

    if (this.promptingToSave) {
      return;
    }

    const canvasEl: HTMLCanvasElement = this.canvas!.nativeElement;
    const canvasRect = canvasEl.getBoundingClientRect();

    this.mouseX = event.clientX - canvasRect.left;
    this.mouseY = event.clientY - canvasRect.top;

    const hoveringWidgetControl =
      this.workflowCanvasService.GetWidgetUnderPointer(
        this.mouseX,
        this.mouseY,
      );

    if (this.isPanning) {
      // Logic to pan all widgets
      const deltaX = event.clientX - this.panStartX;
      const deltaY = event.clientY - this.panStartY;
      this.panStartX = event.clientX;
      this.panStartY = event.clientY;
      // this.moveCanvas(deltaX, deltaY);
      this.moveCanvasFreely(deltaX, deltaY);
      return;
    }

    // let connector = this.findHoveringConnectorArrowLine();
    let connector = this.workflowCanvasService.getHoverConnectorArrow(
      canvasEl,
      event,
    );

    if (connector) {
      if (
        this.hoveringArrow &&
        !this.selectedArrows.includes(this.hoveringArrow)
      ) {
        this.hoveringArrow.hovered = false;
      }
      this.hoveringArrow = connector;
      this.hoveringArrow.hovered = true;
      document.body.style.cursor = 'pointer';

      if (this.showDataPreviewIcon()) {
        this.createDataPreviewHoverIcon(connector);
      }
    } else if (this.hoveringArrow) {
      this.hoveringArrow.hovered = false;
      this.hoveringArrow = undefined;
    }

    if (
      this.workflowCanvasService.IsViewingRunMode ||
      this.workflowCanvasService.IsVersionedWorkflow
    ) {
      return;
    }

    this.hideTooltip();
    this.workflowCanvasService.UpdateConnectors();

    if (this.workflowCanvasService.IsMovingWidget) {
      const canvasWidth = canvasEl.width;
      const canvasHeight = canvasEl.height;
      const widgetWidth =
        this.workflowCanvasService.selectedWidgetControl?.Widget.client_tags
          .Width || 50;
      const widgetHeight =
        this.workflowCanvasService.selectedWidgetControl?.Widget.client_tags
          .Height || 50;

      this.workflowCanvasService.MoveWidget(
        this.mouseX - this.dragOffsetX,
        this.mouseY - this.dragOffsetY,
        canvasWidth,
        canvasHeight,
        widgetWidth,
        widgetHeight,
        this.snapToGrid,
      );
      return;
    }

    if (this.workflowCanvasService.IsDrawingArrow) {
      if (
        hoveringWidgetControl &&
        this.workflowCanvasService.DrawingStartConnectorPoint?.widgetControl !==
          hoveringWidgetControl
      ) {
        this.workflowCanvasService.HoveringArrowToWidgetControl =
          hoveringWidgetControl;
      } else {
        this.workflowCanvasService.HoveringArrowToWidgetControl = null;
      }
      return;
    }
    if (
      hoveringWidgetControl &&
      hoveringWidgetControl.Widget.client_tags?.ClientType === 'CUSTOM_CODE'
    ) {
      const tooltipDiv = document.getElementById('tooltip');
      if (tooltipDiv) {
        const fullName = this.workflowCanvasService.generateUniqueWidgetName(
          hoveringWidgetControl.Widget.client_tags.ClientType,
          hoveringWidgetControl.Widget.name,
        );
        tooltipDiv.textContent = hoveringWidgetControl.Widget.name;
        tooltipDiv.classList.add('tooltip-wrap');
        tooltipDiv.style.display = 'block';
        tooltipDiv.style.left = `${event.pageX - 175}px`;
        tooltipDiv.style.top = `${event.pageY - 175}px`;
      }
    } else {
      const tooltipDiv = document.getElementById('tooltip');
      if (tooltipDiv) {
        tooltipDiv.style.display = 'none';
      }
    }
  }

  private findHoveringConnectorArrowLine(): Arrow | undefined {
    const tolerance = 6; // Adjust this tolerance to fine-tune detection sensitivity
    if (!this.ctx) {
      console.error('Canvas context is null');
      return undefined;
    }

    for (let arrow of this.workflowCanvasService.arrows) {
      const startX = arrow.startPoint.x;
      const startY = arrow.startPoint.y;
      const endX = arrow.endPoint.x;
      const endY = arrow.endPoint.y;

      if (
        Utils.isMouseNearLine(
          this.ctx,
          this.mouseX,
          this.mouseY,
          startX,
          startY,
          endX,
          endY,
          tolerance,
        )
      ) {
        return arrow;
      }
    }
    return undefined;
  }

  resetArrowDrawing() {
    this.workflowCanvasService.HoveringArrowToWidgetControl = null;
    this.workflowCanvasService.DrawingStartConnectorPoint = null;
    this.workflowCanvasService.IsMovingWidget = false;
    this.workflowCanvasService.IsDrawingArrow = false;
    this.isPanning = false;
  }

  draw() {
    if (!this.canvas || !this.ctx) {
      return;
    }
    if (this.isWorkflowSaveApiInprogress) {
      return;
    }

    this.ctx.save();
    this.workflowCanvasService.InitCanvasForRendering(this.ctx, this.canvas);
    this.ctx.save();
    let transform = this.ctx.getTransform();
    this.ctx.setTransform(transform);

    if (this.ctx) {
      this.workflowCanvasService.selectedWidgetControls.forEach(
        (widgetControl) => {
          if (this.workflowCanvasService.selectedWidgetControls.length > 1) {
            widgetControl.backgroundColor = 'rgba(173, 216, 230, 0.3)';
            this.workflowCanvasService.renderWidget(this.ctx!, widgetControl);
          } else {
            widgetControl.backgroundColor = null;
          }
        },
      );
    }

    this.workflowCanvasService.DrawWidgets(
      this.ctx,
      this.canvas,
      this.widgetSize,
      this.mouseX,
      this.mouseY,
    );
    this.ctx.shadowColor = 'transparent';
    this.workflowCanvasService.DrawArrowsAndDataPreviewIcon(
      this.ctx,
      this.arrowColor,
    );

    const curveFactor = 0.6;
    // Draw circles and place icons at the midpoint of each arrow
    this.workflowCanvasService.arrows.forEach((connector) => {
      let controlPoints: any =
        this.workflowCanvasService.calculateControlPoints(
          { x: connector.startPoint.x, y: connector.startPoint.y },
          { x: connector.endPoint.x, y: connector.endPoint.y },
          curveFactor,
        );

      const midpoint = this.workflowCanvasService.getPointOnBezierCurve(
        connector.startPoint,
        controlPoints.controlPoint1,
        controlPoints.controlPoint2,
        connector.endPoint,
        0.5,
      );

      if (this.ctx) {
        this.ctx.globalCompositeOperation = 'destination-out';
        this.ctx.globalCompositeOperation = 'source-over';
      }
    });

    if (this.workflowCanvasService.IsDrawingArrow) {
      this.ctx.beginPath();
      this.ctx.moveTo(
        this.workflowCanvasService.DrawingStartConnectorPoint!.x,
        this.workflowCanvasService.DrawingStartConnectorPoint!.y,
      ); // middle point of the first rectangle
      this.ctx.lineTo(this.mouseX, this.mouseY); // middle point of the second rectangle
      if (this.connectingPointsType === ArrowType.OnCompleted) {
        this.ctx.strokeStyle = 'black';
      } else if (this.connectingPointsType === ArrowType.OnFailed) {
        this.ctx.strokeStyle = 'red';
      } else if (this.connectingPointsType === ArrowType.OnSucceeded) {
        this.ctx.strokeStyle = 'green';
      }

      this.ctx.lineWidth = 2;
      this.ctx.stroke();
    }

    this.ctx.restore();
    this.startCanvasDrawing();
  }

  connectOnCompletedActivities() {
    if (this.workflowCanvasService.widgetControls.length <= 1) {
      this.notificationComponent.display(
        'At least 2 activities are required for a connection.',
        'success',
      );
    } else {
      this.showConnectingPoints = !this.showConnectingPoints;
      this.connectingPointsType = ArrowType.OnCompleted;
    }
  }

  connectOnSuccessActivities() {
    if (this.workflowCanvasService.widgetControls.length <= 1) {
      this.notificationComponent.display(
        'At least 2 activities are required for a connection.',
        'success',
      );
    } else {
      this.showConnectingPoints = !this.showConnectingPoints;
      this.connectingPointsType = ArrowType.OnSucceeded;
    }
  }

  connectOnFailedActivities() {
    if (this.workflowCanvasService.widgetControls.length <= 1) {
      this.notificationComponent.display(
        'At least 2 activities are required for a connection.',
        'success',
      );
    } else {
      this.showConnectingPoints = !this.showConnectingPoints;
      this.connectingPointsType = ArrowType.OnFailed;
    }
  }

  onSnapToGridToggled(event: any) {
    this.snapToGrid = event.target.checked;
  }

  toggleCurationWidgetList() {
    this.showCurationWidgets = !this.showCurationWidgets;
  }

  toggleLoopWidgetList() {
    this.showLoopWidgets = !this.showLoopWidgets;

    this.showGeneralWidgets = false;
    this.showDataWidgets = false;
    this.showCustomCodeWidgets = false;
    this.showThirdPartyAPIWidgets = false;
    this.showMachineLearningWidgets = false;
  }

  toggleCustomPythonWidgetList() {
    this.showCustomPythonWidgets = !this.showCustomPythonWidgets;
  }

  toggleThirdPartyAPIsWidgetList() {
    this.showThirdPartyAPIWidgets = !this.showThirdPartyAPIWidgets;

    this.showGeneralWidgets = false;
    this.showDataWidgets = false;
    this.showCustomCodeWidgets = false;
    this.showLoopWidgets = false;
    this.showMachineLearningWidgets = false;
  }

  toggleIngestionWidgetList() {
    this.showDataWidgets = !this.showDataWidgets;

    this.showCustomCodeWidgets = false;
    this.showThirdPartyAPIWidgets = false;
    this.showLoopWidgets = false;
    this.showGeneralWidgets = false;
    this.showMachineLearningWidgets = false;
  }

  toggleGeneralWidgetList() {
    this.showGeneralWidgets = !this.showGeneralWidgets;

    this.showDataWidgets = false;
    this.showCustomCodeWidgets = false;
    this.showThirdPartyAPIWidgets = false;
    this.showLoopWidgets = false;
    this.showMachineLearningWidgets = false;
  }

  toggleMachineLearningWidgetList() {
    this.showMachineLearningWidgets = !this.showMachineLearningWidgets;

    this.showDataWidgets = false;
    this.showCustomCodeWidgets = false;
    this.showThirdPartyAPIWidgets = false;
    this.showLoopWidgets = false;
    this.showGeneralWidgets = false;
  }

  toggleCustomCodeWidgetList() {
    this.showCustomCodeWidgets = !this.showCustomCodeWidgets;

    this.showGeneralWidgets = false;
    this.showDataWidgets = false;
    this.showThirdPartyAPIWidgets = false;
    this.showLoopWidgets = false;
    this.showMachineLearningWidgets = false;
  }

  validateWorkflow(): boolean {
    if (
      !this.workflowCanvasService.widgetControls.find(
        (t) =>
          t.Widget.type === WidgetType.UX &&
          t.Widget.client_tags.ClientType === WidgetClientType.Start,
      )
    ) {
      this.notificationComponent.display(
        'A start widget is required to run the workflow',
        'error',
      );
      return false;
    }
    if (
      !this.workflowCanvasService.widgetControls.find(
        (t) =>
          t.Widget.type === WidgetType.UX &&
          t.Widget.client_tags.ClientType === WidgetClientType.End,
      )
    ) {
      this.notificationComponent.display(
        'A end widget is required to run the workflow',
        'error',
      );
      return false;
    }

    if (this.workflowCanvasService.widgetControls.length < 3) {
      this.notificationComponent.display(
        'You need at least one functional widget to run the workflow.',
        'error',
      );
      return false;
    }

    return true;
  }

  validateWorkflowToSave(): boolean {
    const startWidget = this.workflowCanvasService.widgetControls.find(
      (t) =>
        t.Widget.type === WidgetType.UX &&
        t.Widget.client_tags.ClientType === WidgetClientType.Start,
    );

    if (!startWidget) {
      this.notificationComponent.display(
        'A start widget is required to save the workflow',
        'error',
      );
      return false;
    }

    const endWidget = this.workflowCanvasService.widgetControls.find(
      (t) =>
        t.Widget.type === WidgetType.UX &&
        t.Widget.client_tags.ClientType === WidgetClientType.End,
    );

    if (!endWidget) {
      this.notificationComponent.display(
        'An end widget is required to save the workflow',
        'error',
      );
      return false;
    }

    // Check if there is at least one functional widget (not Start or End)
    const functionalWidgetExists =
      this.workflowCanvasService.widgetControls.some(
        (t) =>
          !(
            t.Widget.type === WidgetType.UX &&
            (t.Widget.client_tags.ClientType === WidgetClientType.Start ||
              t.Widget.client_tags.ClientType === WidgetClientType.End)
          ),
      );

    if (!functionalWidgetExists) {
      this.notificationComponent.display(
        'You need at least one functional widget to save the workflow.',
        'error',
      );
      return false;
    }

    return true;
  }

  async OnRunWorkflow() {
    this.isExpanded = false;
    this.collapseToFullPage();
    let success = await this.saveWorkflow();
    if (!success) {
      return;
    }
    if (!this.validateWorkflow()) {
      return;
    }

    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    if (!selectedProjectId) {
      return;
    }
    if (
      !this.workflowCanvasService.SelectedWorkflowSession ||
      !this.workflowCanvasService.SelectedWorkflowSession._id
    ) {
      return;
    }

    try {
      if (this.workflowCanvasService.IsVersionedWorkflow) {
        // TODO Save versioned workflow.
      } else {
        let success: boolean = await this.saveWorkflow(true);
        if (!success) {
          this.notificationComponent.display(
            "An error occurred trying to run the workflow: '" +
              this.sharedDataService.LastError +
              "'. Please validate the configuration for each widget.",
            'error',
          );
          return;
        }
      }
    } catch {}
    this.runSessionId = undefined;
    try {
      if (this.workflowCanvasService.IsVersionedWorkflow) {
        await this.apiService.UpdateWorkflow(
          this.configService.SelectedSiteId,
          selectedProjectId,
          this.workflowCanvasService.SelectedWorkflow!,
          this.workflowCanvasService.arrows,
        );
        let runId = await this.apiService.RunVersionedWorkflow(
          this.configService.SelectedSiteId,
          selectedProjectId,
          this.workflowCanvasService.SelectedWorkflow?._id!,
        );
        this.workflowCanvasService.ViewingRunId = runId;
      } else {
        let runId = await this.sessionApi.RunSessionWorkflow(
          this.configService.SelectedSiteId,
          selectedProjectId,
          this.workflowCanvasService.SelectedWorkflowSession._id,
          true,
        );
        this.workflowCanvasService.ViewingRunId = runId;
      }
    } catch {
      let lastError: string | null = this.sharedDataService.LastError;
      if (!lastError) {
        lastError = 'An unknown error occurred';
      }
      this.notificationComponent.display(
        "An error occurred trying to run the workflow: '" +
          lastError +
          "'. Please validate the configuration for each widget.",
        'error',
      );
      return;
    }

    this.startMonitorRunExecutionLoop();
    this.workflowCanvasService.IsViewingRunMode = true;
    if (this.workflowCanvasService.IsVersionedWorkflow) {
      this.notificationComponent.display(
        'Versioned Workflow is running.',
        'success',
      );
    } else {
      this.notificationComponent.display(
        'Master Workflow is running.',
        'success',
      );
      setTimeout(() => {
        this.resizeCanvas();
      }, 1);
    }
  }

  private hideConfigs(): boolean {
    if (this.componentRef) {
      const instance = this.componentRef.instance;
      const widgetControl = instance.widgetControl;
      const widget = widgetControl.Widget;
      instance.inputWidgets = this.workflowCanvasService.findConnectedWidgets(
        widgetControl.Widget.urn,
      );
      if (widget.client_tags.ClientType === 'SAVE') {
        const inputWidgets = instance.inputWidgets;
        if (inputWidgets && inputWidgets.length > 1) {
          this.workflowCanvasService.IsMovingWidget = false;
          document.body.style.cursor = 'default';
          instance.onWidgetClick();
          this.promptingToSave = false;
          return true;
        }
      }
    }
    return false;
  }

  promptToSaveWorkflow() {
    this.promptingToSave = true;
    const dialogRef = this.dialog.open(PromptSaveComponent, {
      width: '300px',
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.navigateBack(true);
      } else {
        this.navigateBack(false);
      }
      this.promptingToSave = false;
    });
  }

  private showConfigByWidgetType() {
    if (
      this.workflowCanvasService.selectedWidgetControl &&
      this.workflowCanvasService.selectedWidgetControl.Widget
    ) {
      let selectedWidget: Widget =
        this.workflowCanvasService.selectedWidgetControl.Widget;
      const widgetClientType =
        this.widgetComponentMap[selectedWidget.client_tags.ClientType];
      if (widgetClientType) {
        this.showWidgetConfiguration(widgetClientType);
      }
    }
  }

  showWidgetConfiguration(widgetClientType: Type<any>) {
    if (this.componentRef) {
      this.componentRef.destroy();
    }
    const topElement = document.getElementById('top');
    const bottomElement = document.getElementById('bottom');
    if (topElement && bottomElement) {
      const isDefaultTopHeight =
        topElement.style.height === '' || topElement.style.height === '50%';
      const isDefaultBottomHeight =
        bottomElement.style.height === '' ||
        bottomElement.style.height === '50%';
      if (isDefaultTopHeight && isDefaultBottomHeight) {
        topElement.style.height = '50%';
        bottomElement.style.height = '50%';
        this.resizeCanvas();
      }
    }

    this.componentRef =
      this.widgetConfigContainer.createComponent(widgetClientType);
  }

  readFileContent(file: File): void {
    const reader = new FileReader();
    reader.onload = (e: any) => {
      // The file content is available as e.target.result
      const fileContent = e.target.result;
      // You can now work with the file content, for example, convert it to bytes
      Utils.ConvertFileContentToBytes(fileContent);
    };

    reader.readAsArrayBuffer(file);
  }

  onFileSelected(event: any) {
    const selectedFile = event.target.files[0];

    if (selectedFile) {
      this.readFileContent(selectedFile);
    }
  }

  saveClicked(
    taskName: string,
    taskDescriptionLine1: string,
    taskDescriptionLine2: string,
    taskDescriptionLine3: string,
  ) {
    if (
      this.workflowCanvasService.selectedWidgetControl &&
      this.workflowCanvasService.selectedWidgetControl.Widget
    ) {
      this.workflowCanvasService.selectedWidgetControl.Widget.name = taskName;
      this.workflowCanvasService.selectedWidgetControl.Widget.description =
        taskDescriptionLine1;
      this.workflowCanvasService.selectedWidgetControl.Widget.description =
        taskDescriptionLine2;
      this.workflowCanvasService.selectedWidgetControl.Widget.description =
        taskDescriptionLine3;
      this.workflowCanvasService.selectedWidgetControl.Widget.client_tags[
        'Color'
      ] = this.selectedColor;
    }
  }
  initResizeVertical(event: MouseEvent) {
    event.preventDefault();
    this.startX = event.pageX; // Store initial horizontal position
    this.startY = event.pageY; // Store initial vertical position
    this.startWidthLeft = document.getElementById('left')!.clientWidth; // Store initial width of the left div
    this.startWidthRight = document.getElementById('designer')!.clientWidth; // Store initial width of the right div
    this.resizeListener = this.renderer.listen(
      'window',
      'mousemove',
      this.doResizeVertical.bind(this),
    );
    this.mouseupListener = this.renderer.listen(
      'window',
      'mouseup',
      this.stopResize.bind(this),
    );
  }

  doResizeVertical(event: MouseEvent) {
    const deltaX = event.pageX - this.startX; // Calculate horizontal delta
    const deltaY = event.pageY - this.startY; // Calculate vertical delta

    // Calculate new dimensions for left and right elements
    const newWidthLeft = this.startWidthLeft + deltaX;
    const newWidthRight = this.startWidthRight - deltaX;

    const leftDiv = document.getElementById('left');
    const rightDiv = document.getElementById('designer');

    if (leftDiv && rightDiv) {
      leftDiv.style.width = `${newWidthLeft}px`;
      rightDiv.style.width = `${newWidthRight}px`;
      // Ensure containers fill the parent container
      leftDiv.style.maxWidth = '100%';
      rightDiv.style.maxWidth = '100%';
    }
  }

  initResize(event: MouseEvent) {
    event.preventDefault();
    this.startY = event.pageY;
    this.startHeightTop = document.getElementById('top')!.clientHeight; // Store the initial height of the top div
    this.startHeightBottom = document.getElementById('bottom')!.clientHeight; // Store the initial height of the bottom div

    this.resizeListener = this.renderer.listen(
      'window',
      'mousemove',
      this.doResize.bind(this),
    );
    this.mouseupListener = this.renderer.listen(
      'window',
      'mouseup',
      this.stopResize.bind(this),
    );
  }

  doResize(event: MouseEvent) {
    if (!this.canvas) {
      return;
    }
    // Calculate the difference in Y position from where the mouse was clicked
    const dy = event.pageY - this.startY;

    // Calculate new heights based on the mouse movement
    const newHeightTop = this.startHeightTop + dy;
    const newHeightBottom = this.startHeightBottom - dy;

    // Apply the new heights to the top and bottom divs
    const topDiv = document.getElementById('top');
    const bottomDiv = document.getElementById('bottom');

    if (topDiv) topDiv.style.height = `${newHeightTop}px`;
    if (bottomDiv) bottomDiv.style.height = `${newHeightBottom}px`;

    this.resizeCanvas();
  }

  stopResize() {
    if (this.resizeListener) {
      this.resizeListener(); // This will remove the 'mousemove' event listener
    }
    if (this.mouseupListener) {
      this.mouseupListener(); // This will remove the 'mouseup' event listener
    }
    this.resizeCanvas();
  }

  expandToFullPage() {
    this.isExpanded = !this.isExpanded;
    const topElement = document.getElementById('top');
    const bottomElement = document.getElementById('bottom');
    if (topElement && bottomElement) {
      if (!this.isExpanded) {
        topElement.style.height = '0';
        bottomElement.style.height = '100%';
      } else {
        topElement.style.height = '50%';
        bottomElement.style.height = '50%';
      }
    }
    this.resizeCanvas();
  }

  collapseToFullPage() {
    this.isExpanded = !this.isExpanded;
    const topElement = document.getElementById('top');
    const bottomElement = document.getElementById('bottom');
    if (topElement && bottomElement) {
      if (this.isExpanded) {
        topElement.style.height = '50%';
        bottomElement.style.height = '50%';
      } else {
        topElement.style.height = '0';
        bottomElement.style.height = '100%';
      }
    }
    this.resizeCanvas();
  }

  showInjestionDialog() {
    const dialogRef = this.dialog.open(InjestionDialogComponent, {
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
    });
    dialogRef.afterClosed().subscribe((result) => {});
  }

  zoomIn() {
    if (this.zoomLevel < this.maxZoom) {
      this.zoomLevel += 10;
      if (this.zoomLevel > this.maxZoom) {
        this.zoomLevel = this.maxZoom;
      }
      this.applyZoom();
    }
  }

  zoomOut() {
    if (this.zoomLevel > this.minZoom) {
      this.zoomLevel -= 10;
      if (this.zoomLevel < this.minZoom) {
        this.zoomLevel = this.minZoom;
      }
      this.applyZoom();
    }
  }

  handleSliderChange(event: any) {
    this.zoomLevel = parseInt(event.target.value, 10);
    this.applyZoom();
  }

  isZoomInDisabled() {
    return this.zoomLevel >= this.maxZoom;
  }

  isZoomOutDisabled() {
    return this.zoomLevel <= this.minZoom;
  }

  applyZoom() {
    const minScale = 0.5;
    const maxScale = 2;
    const previousZoomScale = this.zoomScale;
    this.zoomScale = minScale + (this.zoomLevel / 100) * (maxScale - minScale);
    this.scaleChange = this.zoomScale / previousZoomScale;
    const newCenterX = this.canvas!.nativeElement.width / 2;
    const newCenterY = this.canvas!.nativeElement.height / 2;

    this.widgetSize = this.widgetSize * this.scaleChange;

    this.workflowCanvasService.widgetControls.forEach((item, index) => {
      this.workflowCanvasService.widgetControls[index].Widget.client_tags[
        'PositionX'
      ] =
        (item.Widget.client_tags['PositionX'] - newCenterX) * this.scaleChange +
        newCenterX;
      this.workflowCanvasService.widgetControls[index].Widget.client_tags[
        'PositionY'
      ] =
        (item.Widget.client_tags['PositionY'] - newCenterY) * this.scaleChange +
        newCenterY;
      this.workflowCanvasService.widgetControls[index].Widget.client_tags[
        'Width'
      ] = this.widgetSize;
      this.workflowCanvasService.widgetControls[index].Widget.client_tags[
        'Height'
      ] = this.widgetSize;
    });
    this.ctx!.scale(this.zoomScale, this.zoomScale);
    this.ctx!.clearRect(
      0,
      0,
      this.canvas!.nativeElement.width,
      this.canvas!.nativeElement.height,
    );
    this.ctx!.setTransform(1, 0, 0, 1, 0, 0);
  }

  fitToScreen() {
    this.zoomLevel = 40;
    this.applyZoom();
  }

  onMouseWheel(event: WheelEvent) {
    if (event.ctrlKey) {
      const delta = Math.sign(event.deltaY);
      if (delta < 0) {
        this.zoomIn();
      } else {
        this.zoomOut();
      }
      event.preventDefault();
    }
  }

  onViewRunSummary() {
    const dialogRef = this.dialog.open(RunSummaryComponent, {
      width: '500px',
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result && result.viewDataset) {
        if (this.workflowCanvasService.IsVersionedWorkflow) {
          this.onPreviewDatasetResultsForWorkflowVersion();
        } else {
          this.onPreviewDatasetResultForWorkflowSession();
        }
      }
    });
  }

  onPreviewDatasetResultsForWorkflowVersion() {
    let dialogRef: any;
    dialogRef = this.dialog.open(DataSetResultsComponent, {
      width: '800px',
      data: {
        workflowSessionid:
          this.workflowCanvasService.SelectedWorkflowSession?._id,
        workflowId: this.workflowCanvasService.SelectedWorkflow?._id,
        runId: this.workflowCanvasService.ViewingRunId,
      },
    });

    dialogRef.afterClosed().subscribe(() => {});
  }

  onPreviewDatasetResultForWorkflowSession() {
    let dialogRef: any;
    dialogRef = this.dialog.open(DataSetResultsComponent, {
      width: '800px',
      height: '90%',
      data: {
        workflowSessionId:
          this.workflowCanvasService.SelectedWorkflowSession?._id,
        workflowId: this.workflowCanvasService.SelectedWorkflow?._id,
        runId: undefined,
      },
    });

    dialogRef.afterClosed().subscribe(() => {});
  }

  getTooltipData(widget: any): any {
    let tooltip: any = {
      purpose: widget.widgetPurpose || 'N/A',
      input: widget.expectedInput || 'N/A',
      output: widget.expectedOutput || 'N/A',
    };
    if (widget?.description) {
      tooltip.description = widget.description;
    }
    return tooltip;
  }

  showTooltip(widget: any, event: MouseEvent): void {
    this.tooltipContainer.clear();
    const factory = this.resolver.resolveComponentFactory(
      CustomTooltipComponent,
    );
    const componentRef = this.tooltipContainer.createComponent(factory);
    componentRef.instance.tooltipContent = this.getTooltipData(widget);
    const widgetElement = event.target as HTMLElement;
    const tooltipElement = (componentRef.hostView as any)
      .rootNodes[0] as HTMLElement;
    const widgetRect = widgetElement.getBoundingClientRect();
    let topPosition = widgetRect.top;
    let leftPosition = widgetRect.right + 10;
    tooltipElement.style.position = 'absolute';
    tooltipElement.style.top = `${topPosition}px`;
    tooltipElement.style.left = `${leftPosition}px`;
    tooltipElement.classList.add('leftnav-tooltip');
    requestAnimationFrame(() => {
      const tooltipRect = tooltipElement.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;
      if (tooltipRect.right > viewportWidth) {
        leftPosition = widgetRect.left - tooltipRect.width - 10;
        tooltipElement.style.left = `${leftPosition}px`;
      }
      if (tooltipRect.bottom > viewportHeight) {
        topPosition = viewportHeight - tooltipRect.height - 10;
        tooltipElement.style.top = `${topPosition}px`;
      }
      if (tooltipRect.top < 0) {
        topPosition = 10;
        tooltipElement.style.top = `${topPosition}px`;
      }
    });
  }

  hideTooltipData(): void {
    this.tooltipContainer.clear();
  }
}
