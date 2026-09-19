import { Injectable, ElementRef, ViewChild } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { WidgetControl } from '../../controls/widget-control/widget-control';
import {
  DataCopyWidgetConfig,
  InputOutputConfig,
  LocalFileConfiguration,
  MountedDriveConfiguration,
  SourceType,
  Widget,
  WidgetType,
  Workflow,
  RequestType,
  DatasetModel,
  LocalTextConfiguration,
  TextWidgetConfig,
} from 'src/app/models/workflow-models';
import { CanvasUtils } from './canvas_utils';
import {
  ConnectorPoint,
  ConnectorPointType,
} from 'src/app/controls/widget-control/connector-point';
import {
  WidgetClientTags,
  WidgetClientType,
  WorkflowClientTags,
} from './client-tags';
import { Arrow, ArrowType } from 'src/app/controls/widget-control/arrow';
import { ArrowObject } from 'src/app/controls/widget-control/arrowObject';
import { WorkflowConfigService } from './workflow-config.service';
import { NotificationComponent } from '../../controls/notification/notification.component';
import { Utils } from 'src/app/utils';
import { ConfigService } from 'src/app/services/config.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import {
  WidgetStatus,
  WorkflowSession,
  WorkflowRunStatus,
  WidgetRunResult,
} from 'src/app/models/workflow-sessions-api-response.models';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';

export interface CanvasButton {
  buttonImage: HTMLImageElement;
  positionX: number;
  positionY: number;
  width: number;
  height: number;
  buttonName: string;
}

class DataPreviewHoverIcon {
  public Icon: string = 'preview';
  public PositionX: number = 0;
  public PositionY: number = 0;
}

@Injectable({
  providedIn: 'root',
})
export class WorkflowCanvasService {
  @ViewChild('notification') notificationComponent!: NotificationComponent;

  public changeMadeToWorkflow: boolean = false;

  public dotRadius: number = 1; // radius of the dots
  public gridSpacing: number = 20; // space between dots
  public widgetControls: WidgetControl[] = [];
  public IsMovingWidget: boolean = false;
  public IsDrawingArrow: boolean = false;
  public DrawingStartConnectorPoint: ConnectorPoint | null = null;
  public HoveringArrowToWidgetControl: WidgetControl | null = null;
  public arrows: Arrow[] = [];
  private angle: number = 0;
  private startEndNodeImage = new Image();
  private selectedGeneralIconImage = new Image();
  private unSelectedGeneralIconImage = new Image();
  private selectedIngestionIconImage = new Image();
  private unSelectedIngestionIconImage = new Image();
  private selectedCurationIconImage = new Image();
  private unSelectedCurationIconImage = new Image();
  private selectedMLIconImage = new Image();
  private unSelectedMLIconImage = new Image();
  private WidgetStatusFailedImage = new Image();
  private WidgetStatusPendingImage = new Image();
  private WidgetStatusSuccessImage = new Image();
  private WidgetStatusIdleImage = new Image();
  private WidgetStatusScheduledImage = new Image();
  private WidgetStatusStoppedImage = new Image();
  private WidgetStatusPausedImage = new Image();
  private WidgetStatusRunningImage = new Image();
  private selectedDataWidget = new Image();
  private unSelectedDataWidget = new Image();
  private WidgetStatusSuccessImageDesigner = new Image()
  private WidgetStatusPendingImageDesigner = new Image()
  private WidgetStatusWarningImageDesigner = new Image()
  private WidgetStatusInfoWarningImageDesigner = new Image()

  private readonly DEFAULT_WIDGET_HEADER_COLOR = '#1A7A7F';
  private readonly WIDGET_START_RADIUS = 90;
  private circleRadius: number = 6;
  private dataPreviewHoverIcon: DataPreviewHoverIcon | undefined = undefined;
  private colorChangeIntervalId!: ReturnType<typeof setInterval>;

  widgetRunResults: WidgetRunResult[] = [];
  originalSavedWorkflowClone: any = {};
  colors: any[] = [];
  color: any;
  number = 0


  constructor(
    private workflowConfigService: WorkflowConfigService,
    private sessionApiService: WorkflowsSessionsApiService,
    private configService: ConfigService,
  ) {
    this.startEndNodeImage.src = 'assets/StartNode.png';
    this.selectedGeneralIconImage.src = 'assets/SelectedGeneralWidget.png';
    this.unSelectedGeneralIconImage.src = 'assets/UnSelectedGeneralWidget.png';
    this.selectedIngestionIconImage.src = 'assets/SelectedIngestionWidget.png';
    this.unSelectedIngestionIconImage.src =
      'assets/UnSelectedIngestionWidget.png';
    this.selectedCurationIconImage.src = 'assets/SelectedGeneralWidget.png';
    this.unSelectedCurationIconImage.src = 'assets/UnSelectedGeneralWidget.png';
    this.selectedMLIconImage.src = 'assets/SelectedMLWidget.png';
    this.unSelectedMLIconImage.src = 'assets/UnSelectedMLWidget.png';
    this.WidgetStatusFailedImage.src = 'assets/WidgetStatusFailed.png';
    this.WidgetStatusPendingImage.src = 'assets/WidgetStatusPending.png';
    this.WidgetStatusSuccessImage.src = 'assets/WidgetStatusSuccess.png';
    this.WidgetStatusIdleImage.src = 'assets/WidgetStatusIdle.png';
    this.WidgetStatusScheduledImage.src = 'assets/WidgetStatusScheduled.png';
    this.WidgetStatusStoppedImage.src = 'assets/WidgetStatusStopped.png';
    this.WidgetStatusPausedImage.src = 'assets/WidgetStatusPaused.png';
    this.WidgetStatusRunningImage.src = 'assets/WidgetStatusRunning.png';
    this.selectedDataWidget.src = 'assets/selectedDataWidget.png';
    this.unSelectedDataWidget.src = 'assets/UnSelectedDataWidget.png';
    for (let i = 0; i < 100; i++) {
      // Calculate HSL values
      const hue: any = i * 3.6; // 360 degrees divided by 100
      const saturation: any = 70; // Saturation percentage
      const lightness: any = 50; // Lightness percentage
      // Create HSL color string and add to the array
      this.colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
    }

    // setInterval(()=> {
    //   this.color = this.colors[this.number]
    //   this.number++;
    //   if(this.number>100) this.number=0
    // },400)

    this.colorChangeIntervalId = setInterval(() => {
      this.color = this.colors[this.number];
      this.number++;
      if (this.number > 100) this.number = 0;
    }, 400);
    this.WidgetStatusSuccessImageDesigner.src = 'assets/WidgetStatusSuccessRunDesigner.png';
    this.WidgetStatusPendingImageDesigner.src = 'assets/WidgetStatusPendingRunDesigner.png';
    this.WidgetStatusWarningImageDesigner.src = 'assets/WidgetStatusWarningDesigner.png';
    this.WidgetStatusInfoWarningImageDesigner.src = 'assets/WidgetStatusInfoWarningDesigner.png';

  }

  ngOnDestroy(): void {
    if (this.colorChangeIntervalId) {
      clearInterval(this.colorChangeIntervalId);
    }
  }

  setWidgetRunResults(result: WidgetRunResult[]) {
    this.widgetRunResults = result;
  }
  getWidgetRunResults() {
    return this.widgetRunResults;
  }
  async GetResultDatasetIdForWidgetControl(
    widgetControl: WidgetControl,
  ): Promise<string | undefined> {
    if (widgetControl.Widget.type === WidgetType.DATA_COPY) {
      let config: DataCopyWidgetConfig = widgetControl.Widget
        .config as DataCopyWidgetConfig;
      if (config.source.type === SourceType.LOCAL) {
        let source: LocalFileConfiguration = config.source
          .configuration as LocalFileConfiguration;
        return source.dataset_id!;
      } else if (config.source.type === SourceType.MOUNTED_DRIVE) {
        let source: MountedDriveConfiguration = config.source
          .configuration as MountedDriveConfiguration;
        return source.dataset_id!;
      }
    } else {
      if (!this.IsViewingRunMode) {
        this.notificationComponent.display(
          'To view the output of this widget switch to run mode after running the workflow up to this widget.',
          'success',
        );
        return undefined;
      }
      let datasetId: string | undefined =
        await this.sessionApiService.GetDatasetIdFromWidgetRunResult(
          this.IsVersionedWorkflow!,
          this.configService.SelectedSiteId,
          this.configService.SelectedProjectId!,
          this.SelectedWorkflow!._id!,
          this.ViewingRunId!,
          this.SelectedWorkflowSession?._id!,
          widgetControl.Widget.urn!,
        );
      return datasetId;
    }
    return undefined;
  }

  async GetResultDatasetIdsForWidgetControl(
    widgetControl: WidgetControl,
  ): Promise<DatasetModel[] | string | undefined> {
    if (widgetControl.Widget.type === WidgetType.DATA_COPY) {
      let config: DataCopyWidgetConfig = widgetControl.Widget
        .config as DataCopyWidgetConfig;
      if (config.source.type === SourceType.LOCAL) {
        let source: LocalFileConfiguration = config.source
          .configuration as LocalFileConfiguration;
        return Array.isArray(source.dataset_id) ? source.dataset_id[0] : source.dataset_id;
      } else if (config.source.type === SourceType.MOUNTED_DRIVE) {
        let source: MountedDriveConfiguration = config.source
          .configuration as MountedDriveConfiguration;
        return Array.isArray(source.dataset_id) ? source.dataset_id[0] : source.dataset_id;
      }
    } else if (widgetControl.Widget.type === WidgetType.TEXT_DATA) {
      let config: TextWidgetConfig = widgetControl.Widget
        .config as TextWidgetConfig;
      if (config.source[0].type === SourceType.LOCAL) {
        let source: LocalTextConfiguration = config.source[0]
          .configuration as LocalTextConfiguration;
        return Array.isArray(source.dataset_id) ? source.dataset_id[0] : source.dataset_id;
      } else if (config.source[0].type === SourceType.MOUNTED_DRIVE) {
        let source: MountedDriveConfiguration = config.source[0]
          .configuration as MountedDriveConfiguration;
        return Array.isArray(source.dataset_id) ? source.dataset_id[0] : source.dataset_id;
      }
    } else {
      if (!this.IsViewingRunMode) {
        this.notificationComponent.display(
          'To view the output of this widget switch to run mode after running the workflow up to this widget.',
          'success',
        );
        return undefined;
      }
      let datasetIds: DatasetModel[] | undefined =
        await this.sessionApiService.GetDatasetIdsFromWidgetRunResult(
          this.IsVersionedWorkflow!,
          this.configService.SelectedSiteId,
          this.configService.SelectedProjectId!,
          this.SelectedWorkflow!._id!,
          this.ViewingRunId!,
          this.SelectedWorkflowSession?._id!,
          widgetControl.Widget.urn!,
        );
      return datasetIds;
    }
    return undefined;
  }

  async GetResultCPWForWidgetControl(
    widgetControl: WidgetControl,
  ): Promise<any | undefined> {
    if (!this.IsViewingRunMode) {
      this.notificationComponent.display(
        'To view the output of this widget switch to run mode after running the workflow up to this widget.',
        'success',
      );
      return undefined;
    }
    let results: any | undefined =
      await this.sessionApiService.GetResultCPWFromWidgetRunResult(
        this.IsVersionedWorkflow!,
        this.configService.SelectedSiteId,
        this.configService.SelectedProjectId!,
        this.SelectedWorkflow!._id!,
        this.ViewingRunId!,
        this.SelectedWorkflowSession?._id!,
        widgetControl.Widget.urn!,
      );
    return results;
  }

  getWidgetStartRadius(): number {
    return this.WIDGET_START_RADIUS;
  }

  getRetryCount(): number {
    throw new Error('Method not implemented.');
  }

  createDataPreviewHoverIcon(x: number, y: number) {
    this.dataPreviewHoverIcon = new DataPreviewHoverIcon();
    this.dataPreviewHoverIcon.PositionX = x;
    this.dataPreviewHoverIcon.PositionY = y;
  }

  destroyDataPreviewHoverIcon() {
    this.dataPreviewHoverIcon = undefined;
  }

  // The workflow session we have loaded.
  private _selectedWorkflowSession = new BehaviorSubject<
    WorkflowSession | undefined
  >(undefined);
  _workflowSession$ = this._selectedWorkflowSession.asObservable();

  private _invalid_widgetsList = new BehaviorSubject<any>(undefined);
  private _saveWorkflowResponse = new BehaviorSubject<boolean>(false);
  private _newDraggedWidgetsList = new BehaviorSubject<any[]>([]);

  set SelectedWorkflowSession(value: WorkflowSession | undefined) {
    this._selectedWorkflowSession.next(value);
  }

  get SelectedWorkflowSession(): WorkflowSession | undefined {
    return this._selectedWorkflowSession.getValue();
  }

  set invalid_widgets(data: any | undefined) {
    this._invalid_widgetsList.next(data)
  }

  get invalid_widgets(): any | undefined {
    return this._invalid_widgetsList.getValue();
  }

  set saveWorkflowResponse(clicked: boolean) {
    this._saveWorkflowResponse.next(clicked)
  }

  get saveWorkflowResponse(): boolean {
    return this._saveWorkflowResponse.getValue();
  }

  set newDraggedWidgetsList(data: any | []) {
    const currentList = this._newDraggedWidgetsList.getValue();
    this._newDraggedWidgetsList.next([...currentList, data]);
  }

  get newDraggedWidgetsList(): any | [] {
    return this._newDraggedWidgetsList.getValue();
  }

  clearNewDraggedWidgetsList(): void {
    this._newDraggedWidgetsList.next([]); // Emit an empty array to clear the list
  }

  // The workflow run status.
  private _workflowRunStatus = new BehaviorSubject<
    WorkflowRunStatus | undefined
  >(undefined);
  workflowRunStatus$ = this._workflowRunStatus.asObservable();

  set WorkflowRunStatus(value: WorkflowRunStatus | undefined | undefined) {
    this._workflowRunStatus.next(value);
  }

  get WorkflowRunStatus(): WorkflowRunStatus | undefined | undefined {
    return this._workflowRunStatus.getValue();
  }

  // The workflow we have loaded.
  public _selectedWorkflow = new BehaviorSubject<Workflow | undefined>(
    undefined,
  );
  selectedWorkflow$ = this._selectedWorkflow.asObservable();

  set SelectedWorkflow(value: Workflow | undefined) {
    this._selectedWorkflow.next(value);
  }

  get SelectedWorkflow(): Workflow | undefined {
    return this._selectedWorkflow.getValue();
  }

  // Is selected workflow a versioned workflow?
  private _isVersionedWorkflow = new BehaviorSubject<boolean | undefined>(
    undefined,
  );
  isVersionedWorkflow$ = this._isVersionedWorkflow.asObservable();

  set IsVersionedWorkflow(value: boolean | undefined) {
    this._isVersionedWorkflow.next(value);
  }

  get IsVersionedWorkflow(): boolean | undefined {
    return this._isVersionedWorkflow.getValue();
  }

  //  The ID of the run we are viewing.
  private _viewingRunId = new BehaviorSubject<string | undefined>(undefined);
  viewingRunId$ = this._viewingRunId.asObservable();

  set ViewingRunId(value: string | undefined) {
    this._viewingRunId.next(value);
  }

  get ViewingRunId(): string | undefined {
    return this._viewingRunId.getValue();
  }

  // Are we viewing the run mode?
  private _isViewingRunMode = new BehaviorSubject<boolean>(false);
  isViewingRunMode$ = this._isVersionedWorkflow.asObservable();

  set IsViewingRunMode(value: boolean) {
    this._isViewingRunMode.next(value);
  }

  get IsViewingRunMode(): boolean {
    return this._isViewingRunMode.getValue();
  }

  // The selected widget control
  private _selectedWidgetControls = new BehaviorSubject<WidgetControl[]>([]);
  selectedWidgetControls$ = this._selectedWidgetControls.asObservable();

  set selectedWidgetControl(value: WidgetControl | undefined) {
    if (value) {
      // Single selection: Clear others and set this one
      this._selectedWidgetControls.next([value]);
    } else {
      // Clear selection
      this._selectedWidgetControls.next([]);
    }
  }

  get selectedWidgetControl(): WidgetControl | undefined {
    // Return the first selected widget if there is exactly one, otherwise undefined
    const selectedWidgets = this._selectedWidgetControls.getValue();
    return selectedWidgets.length === 1 ? selectedWidgets[0] : undefined;
  }

  get selectedWidgetControls(): WidgetControl[] {
    // Return all selected widgets
    return this._selectedWidgetControls.getValue();
  }

  setSelectedWidgetControls(value: WidgetControl[]) {
    this._selectedWidgetControls.next(value);
  }

  getDataSetIdFromResults(previousWidgetResults: any, selectedInputWidget: Widget) {
    if (selectedInputWidget.type === 'DATA_COPY') {
      return previousWidgetResults[0].result_value._id;
    }

    let datasetId = null;
    if (previousWidgetResults && previousWidgetResults.length > 0) {
      previousWidgetResults.some((result: any) => {
        if (result.result_value.name === selectedInputWidget.outputs[0].name) {
          datasetId = result.result_value._id;
          return;
        }
      });
    }

    return datasetId;
  }

  private widgetExecutionStatusSubject = new BehaviorSubject<boolean>(false);
  widgetExecutionStatus$ = this.widgetExecutionStatusSubject.asObservable();

  notifyWidgetExecutionStatus(status: boolean) {
    this.widgetExecutionStatusSubject.next(status);
  }

  findWidgetByUrn(urn: string): Widget | undefined {
    let widgetControl: WidgetControl | undefined = this.widgetControls.find(
      (t) => t.Widget.urn === urn,
    );

    if (widgetControl) {
      return widgetControl.Widget;
    }

    return undefined;
  }

  findConnectedWidgets(urn: string): Widget[] {
    return this.widgetControls
      .filter(
        (widgetControl) =>
          widgetControl.Widget.on_success.some(
            (successUrn) => successUrn === urn,
          ) ||
          widgetControl.Widget.on_failure.some(
            (failureUrn) => failureUrn === urn,
          ) ||
          widgetControl.Widget.on_complete.some(
            (completeUrn) => completeUrn === urn,
          ),
      )
      .map((widgetControl) => widgetControl.Widget);
  }

  findConnectedWidgetsAndFilter(urn: string, type?: string): Widget[] {
    return this.widgetControls
      .filter(({ Widget }) =>
        [Widget.on_success, Widget.on_failure, Widget.on_complete].some(arr =>
          arr.includes(urn)
        )
      )
      .flatMap(({ Widget }) =>
        Widget.outputs.map(output => ({ ...Widget, outputs: [output] }))
      )
      .filter((res: any) => !type || res.outputs[0].type === type);
  }

  findConnectedMLWidget(urn: string): Widget[] {
    return this.widgetControls
      .filter((widgetControl) => widgetControl.Widget.urn == urn)
      .map((widgetControl) => widgetControl.Widget);
  }

  findConnectedMLWidgetAndFilter(urn: string, type?: string): Widget[] {
    return this.widgetControls
      .filter(({ Widget }) =>
        [Widget.on_success, Widget.on_failure, Widget.on_complete].some(arr =>
          arr.includes(urn)
        )
      )
      .flatMap(({ Widget }) =>
        Widget.outputs.map(output => ({ ...Widget, outputs: [output] }))
      );
  }

  findConnectedByWidgetType(type: string): Widget[] {
    return this.widgetControls
      .filter((widgetControl) => widgetControl.Widget.type == type)
      .map((widgetControl) => widgetControl.Widget);
  }



  getMousePosition(canvas: HTMLCanvasElement, event: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top
    };
  }
  getHoverConnectorArrow(canvasEl: HTMLCanvasElement, event: MouseEvent): Arrow | undefined {
    const mousePos = this.getMousePosition(canvasEl, event);
    for (const connector of this.arrows) {  // Use 'for...of' to allow returning
      const hoverState = this.isMouseNearConnector(mousePos, connector);
      if (hoverState) {  // If mouse is near the connector
        return connector;  // Return the hovered connector
      }
    }
    return undefined;
  }


  isMouseNearConnector(mousePos: { x: number, y: number }, connector: any) {
    const curveFactor = 0.6;
    const controlPoints = this.calculateControlPoints(
      { x: connector.startPoint.x, y: connector.startPoint.y },
      { x: connector.endPoint.x, y: connector.endPoint.y },
      curveFactor,
    );

    // You can use a more precise Bezier distance check here, but for simplicity:
    const distance = this.distanceFromBezier(
      mousePos, connector.startPoint, controlPoints.controlPoint1, controlPoints.controlPoint2, connector.endPoint
    );

    // Hover if the mouse is within 10 pixels of the curve
    return distance < 10;
  }



  distanceFromBezier(mousePos: { x: number, y: number }, start: { x: number, y: number }, cp1: any, cp2: any, end: any): number {
    // Calculate distance between the mouse and the bezier curve
    // For simplicity, you can use an approximation like sampling multiple points on the curve
    // and checking their distance from the mouse.

    let minDistance = Infinity;
    const steps = 100;  // Number of samples along the curve

    for (let t = 0; t <= 1; t += 1 / steps) {
      const pointOnCurve = this.getPointOnBezierCurve(start, cp1, cp2, end, t);
      const distance = Math.sqrt(
        (pointOnCurve.x - mousePos.x) ** 2 + (pointOnCurve.y - mousePos.y) ** 2
      );
      if (distance < minDistance) {
        minDistance = distance;
      }
    }
    return minDistance;
  }



  private drawGridOfDots(
    ctx: CanvasRenderingContext2D | null,
    canvas: ElementRef<HTMLCanvasElement>,
  ): void {
    if (!ctx || !canvas || !canvas.nativeElement) {
      return;
    }

    // Draw grid of dots
    for (let x = 0; x <= canvas.nativeElement.width; x += this.gridSpacing) {
      for (let y = 0; y <= canvas.nativeElement.height; y += this.gridSpacing) {
        ctx.beginPath();
        ctx.arc(x, y, this.dotRadius, 0, 2 * Math.PI);
        ctx.fillStyle = '#00000033';
        ctx.fill();
        ctx.closePath();
      }
    }
  }

  public InitCanvasForRendering(
    ctx: CanvasRenderingContext2D | null,
    canvas: ElementRef<HTMLCanvasElement>,
  ) {
    if (!ctx || !canvas) {
      return;
    }
    ctx.clearRect(
      0,
      0,
      canvas.nativeElement.width,
      canvas.nativeElement.height,
    );
    if (!this.IsViewingRunMode && !this.IsVersionedWorkflow) {
      this.drawGridOfDots(ctx, canvas);
    }
  }

  findClosestPoints(
    startWidgetControlConnectorPoints: ConnectorPoint[],
    endWidgetControlConnectorPoints: ConnectorPoint[],
  ): [ConnectorPoint, ConnectorPoint] {
    let minDistance = Infinity;
    let closestPoints: [ConnectorPoint, ConnectorPoint] = [
      startWidgetControlConnectorPoints[0],
      endWidgetControlConnectorPoints[0],
    ];

    for (let pointA of startWidgetControlConnectorPoints) {
      for (let pointB of endWidgetControlConnectorPoints) {
        let distance = this.calculateDistance(pointA, pointB);
        if (distance < minDistance) {
          minDistance = distance;
          closestPoints = [pointA, pointB];
        }
      }
    }

    return closestPoints;
  }

  public UpdateConnectors() {
    this.arrows.forEach((arrow, index, array) => {
      let startWidgetControl: WidgetControl = arrow.startPoint.widgetControl;
      let endWidgetControl: WidgetControl = arrow.endPoint.widgetControl;
      let closestPoints = this.findClosestPoints(
        startWidgetControl.ConnectorPoints,
        endWidgetControl.ConnectorPoints,
      );
      arrow.startPoint = closestPoints[0];
      arrow.endPoint = closestPoints[1];
    });
  }

  calculateControlPoints(startPoint: any, endPoint: any, curveFactor: any) {
    // Control points are a fraction of the way from the start and end points
    const controlPoint1 = {
      x: startPoint.x + curveFactor * (endPoint.x - startPoint.x),
      y: startPoint.y,
    };
    const controlPoint2 = {
      x: endPoint.x - curveFactor * (endPoint.x - startPoint.x),
      y: endPoint.y,
    };

    return { controlPoint1, controlPoint2 };
  }

  calculateDistance(point1: ConnectorPoint, point2: ConnectorPoint): number {
    return Math.sqrt(
      Math.pow(point1.x - point2.x, 2) + Math.pow(point1.y - point2.y, 2),
    );
  }

  drawCircle(ctx: any, x: any, y: any, radius: any, color: any) {
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.stroke();
  }

  getPointOnBezierCurve(
    startPoint: any,
    controlPoint1: any,
    controlPoint2: any,
    endPoint: any,
    t: any,
  ) {
    const x =
      (1 - t) ** 3 * startPoint.x +
      3 * (1 - t) ** 2 * t * controlPoint1.x +
      3 * (1 - t) * t ** 2 * controlPoint2.x +
      t ** 3 * endPoint.x;
    const y =
      (1 - t) ** 3 * startPoint.y +
      3 * (1 - t) ** 2 * t * controlPoint1.y +
      3 * (1 - t) * t ** 2 * controlPoint2.y +
      t ** 3 * endPoint.y;
    return { x, y };
  }

  public DrawArrowsAndDataPreviewIcon(ctx: CanvasRenderingContext2D, arrowColor?: any) {
    this.arrows.forEach((connector, index, array) => {
      ctx.beginPath();

      let color: any = arrowColor;
      if (connector.selected) {
        color = '#40E0D0';
      } else if (connector.hovered) {
        color = '#333';
      }
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.lineWidth = 2;
      const curveFactor = 0.6;
      let controlPoints: any = this.calculateControlPoints(
        { x: connector.startPoint.x, y: connector.startPoint.y },
        { x: connector.endPoint.x, y: connector.endPoint.y },
        curveFactor,
      );
      ctx.moveTo(connector.startPoint.x, connector.startPoint.y);
      ctx.bezierCurveTo(
        controlPoints.controlPoint1.x,
        controlPoints.controlPoint1.y,
        controlPoints.controlPoint2.x,
        controlPoints.controlPoint2.y,
        connector.endPoint.x,
        connector.endPoint.y,
      );
      ctx.stroke();

      const pointNearEnd1 = this.getPointOnBezierCurve(
        connector.startPoint,
        controlPoints.controlPoint1,
        controlPoints.controlPoint2,
        connector.endPoint,
        0.9999,
      );

      ctx!.strokeStyle = color;
      ctx!.fillStyle = color;
      ctx!.lineWidth = 2;
      ctx!.stroke();

      // Calculate the angle of the line
      let dx = connector.endPoint.x - pointNearEnd1.x;
      let dy = connector.endPoint.y - pointNearEnd1.y;
      let angle = Math.atan2(dy, dx);

      // Check if the line is almost vertical
      const almostVertical = Math.abs(dx) < 0.01; // Adjust this threshold as needed

      if (almostVertical) {
        // Adjust angle based on whether we are going up or down
        angle = dy > 0 ? Math.PI / 2 : -Math.PI / 2; // π/2 radians is straight down, -π/2 is straight up
      }

      // Continue with your existing arrow drawing logic
      let arrowLength = 10; // Adjust as needed
      const arrowWidth = Math.PI / 6; // 30 degrees for each side of the arrow

      let arrowPoint1 = {
        x: connector.endPoint.x - arrowLength * Math.cos(angle - arrowWidth),
        y: connector.endPoint.y - arrowLength * Math.sin(angle - arrowWidth),
      };

      let arrowPoint2 = {
        x: connector.endPoint.x - arrowLength * Math.cos(angle + arrowWidth),
        y: connector.endPoint.y - arrowLength * Math.sin(angle + arrowWidth),
      };

      // Draw the arrowhead
      ctx.beginPath();
      ctx.moveTo(arrowPoint1.x, arrowPoint1.y);
      ctx.lineTo(connector.endPoint.x, connector.endPoint.y);
      ctx.lineTo(arrowPoint2.x, arrowPoint2.y);
      ctx.fill();
    });

    if (this.dataPreviewHoverIcon) {
      this.drawDataPreviewHoverIcon(
        ctx,
        this.dataPreviewHoverIcon.Icon,
        this.dataPreviewHoverIcon.PositionX,
        this.dataPreviewHoverIcon.PositionY,
      );
    }
  }

  drawDataPreviewHoverIcon(
    ctx: CanvasRenderingContext2D,
    icon: string,
    posX: number,
    posY: number,
  ) {
    ctx.font = '18px "Material Icons Outlined"';
    const metrics = ctx.measureText(icon);
    const textWidth = metrics.width;
    const textHeight = 18; // Approximate height based on the font size

    // Calculate the rectangle dimensions
    const padding = 10; // Extra padding around text
    const rectWidth = textWidth + padding;
    const rectHeight = textHeight + padding;
    const borderRadius = 7;
    const borderWidth = 2;

    // Calculate the position of the rectangle
    const rectX = posX - rectWidth / 2;
    const rectY = posY - rectHeight / 2;

    // Set up the border properties
    ctx.lineWidth = borderWidth;
    ctx.strokeStyle = 'gray'; // Color of the border

    // Draw the rounded rectangle background
    ctx.fillStyle = 'white';
    ctx.beginPath();
    ctx.moveTo(rectX + borderRadius, rectY);
    ctx.lineTo(rectX + rectWidth - borderRadius, rectY);
    ctx.quadraticCurveTo(
      rectX + rectWidth,
      rectY,
      rectX + rectWidth,
      rectY + borderRadius,
    );
    ctx.lineTo(rectX + rectWidth, rectY + rectHeight - borderRadius);
    ctx.quadraticCurveTo(
      rectX + rectWidth,
      rectY + rectHeight,
      rectX + rectWidth - borderRadius,
      rectY + rectHeight,
    );
    ctx.lineTo(rectX + borderRadius, rectY + rectHeight);
    ctx.quadraticCurveTo(
      rectX,
      rectY + rectHeight,
      rectX,
      rectY + rectHeight - borderRadius,
    );
    ctx.lineTo(rectX, rectY + borderRadius);
    ctx.quadraticCurveTo(rectX, rectY, rectX + borderRadius, rectY);
    ctx.closePath();
    ctx.fill();
    ctx.stroke(); // Apply the border

    // Draw the text
    ctx.fillStyle = 'gray'; // Set fill style for the text
    ctx.textAlign = 'center'; // Horizontal centering
    ctx.textBaseline = 'middle'; // Vertical centering
    ctx.fillText(icon, posX, posY);

    return { x: rectX, y: rectY, width: rectWidth, height: rectHeight }; // Return the rectangle info for click detection
  }

  public DrawWidgets(
    ctx: CanvasRenderingContext2D,
    canvas: ElementRef<HTMLCanvasElement>,
    widgetSize: number,
    mouseX: number,
    mouseY: number,
  ) {
    this.widgetControls.forEach((widgetControl, index, array) => {
      if (ctx && canvas) {
        this.DrawWidgetControl(ctx, canvas, widgetControl, widgetSize);
        let widgetStatus: WidgetStatus | undefined;
        let iconToDraw: HTMLImageElement | undefined = this.WidgetStatusPendingImage;
        let rotate: boolean = false;
        if (this.IsViewingRunMode && this.WorkflowRunStatus) {
          widgetStatus =
            this.WorkflowRunStatus?.widgets_status?.find(
              (t) => t.urn === widgetControl.Widget.urn,
            );
          if (widgetStatus) {
            switch (widgetStatus.status) {
              case 'IDLE':
                iconToDraw = this.WidgetStatusPendingImage;
                break;
              case 'SCHEDULED':
                iconToDraw = this.WidgetStatusPendingImage;
                break;
              case 'RUNNING':
                iconToDraw = this.WidgetStatusRunningImage;
                rotate = true;
                break;
              case 'FAILED':
                iconToDraw = this.WidgetStatusFailedImage;
                break;
              case 'PAUSED':
                iconToDraw = this.WidgetStatusPausedImage;
                break;
              case 'STOPPED':
                iconToDraw = this.WidgetStatusStoppedImage;
                break;
              case 'SUCCEEDED':
                iconToDraw = this.WidgetStatusSuccessImage;
                break;
            }
            if (iconToDraw) {
              this.setIconToWidgets(widgetStatus, iconToDraw, rotate, ctx, widgetControl, mouseX, mouseY)
            }
          }
        }
        else if (this.invalid_widgets) {
          iconToDraw = this.WidgetStatusPendingImageDesigner
          let statusInfo = 'Pending'
          let invalid_widgetsList = this.invalid_widgets
          let widgetStatus: WidgetStatus | undefined = invalid_widgetsList.find(
            (t: any) => t.urn === widgetControl.Widget.urn,
          );
          //for non configured widgets & saved          
          if (widgetStatus) {
            iconToDraw = this.WidgetStatusWarningImageDesigner
            statusInfo = 'Saved without configuring'
          }
          let newWidgetList = this.newDraggedWidgetsList
          let isNewWidget = widgetControl.Widget.type !== 'UX' && newWidgetList.find((widget: any) => widget === widgetControl.Widget.urn)
          if (newWidgetList && isNewWidget) {
            iconToDraw = this.WidgetStatusPendingImageDesigner;
            statusInfo = 'Not configured yet'
            if (!widgetStatus) {
              widgetStatus = widgetControl.Widget;
            }
          }
          //for saved configured widgets
          if (!widgetStatus && widgetControl.Widget.type !== 'UX' && !isNewWidget) { 
            iconToDraw = this.WidgetStatusSuccessImageDesigner;
            statusInfo = 'Configured Successfully';
            if (!widgetStatus) {
              widgetStatus = widgetControl.Widget;
            }
          }
          if (!this.saveWorkflowResponse) {
            iconToDraw = this.WidgetStatusRunningImage
            statusInfo = 'Fetching Status'
            rotate = true
          }
          if (widgetStatus && widgetControl.Widget.type !== 'UX') {
            this.setIconToWidgets(widgetStatus, iconToDraw, rotate, ctx, widgetControl, mouseX, mouseY, statusInfo)
          }
        }
      }
    });
  }

  setIconToWidgets(widgetStatus: WidgetStatus, iconToDraw: HTMLImageElement, rotate: boolean, ctx: CanvasRenderingContext2D, widgetControl: WidgetControl, mouseX: number, mouseY: number, statusInfo: any = '') {
    if (widgetStatus && widgetControl.Widget.type !== 'UX') {
      let mouseHoversIcon: boolean = false;
      let iconX: number =
        widgetControl.GetPositionX() + widgetControl.GetWidth() - 12;
      let iconY: number = widgetControl.GetPositionY() - 12;
      if (mouseX >= iconX && mouseX <= iconX + 24) {
        if (mouseY >= iconY && mouseY <= iconY + 24) {
          mouseHoversIcon = true;
        }
      }
      if (mouseHoversIcon) {
        document.body.style.cursor = 'pointer';
        if (statusInfo) {
          const padding = 6;
          const fontSize = 12;

          ctx.font = `${fontSize}px Arial`;
          const textWidth = ctx.measureText(statusInfo).width;

          // Background box
          ctx.fillStyle = 'black';
          ctx.fillRect(mouseX, mouseY - fontSize - padding, textWidth + padding * 2, fontSize + padding);

          // Text
          ctx.fillStyle = 'white';
          ctx.fillText(statusInfo, mouseX + padding, mouseY - padding);
        }

      } else {
        document.body.style.cursor = 'default';
      }
      ctx.save();
      ctx.translate(
        widgetControl.GetPositionX() + widgetControl.GetWidth(),
        widgetControl.GetPositionY(),
      );

      if (rotate) {
        this.angle += 0.09;
        ctx.rotate(this.angle);
      }
      ctx.drawImage(iconToDraw, -12, -12, 24, 24);
      ctx.restore();
    }
  }

  public DrawRoundedRect(
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    width: number,
    height: number,
    cornerRadius: number,
  ) {
    ctx.beginPath();
    ctx.moveTo(x + cornerRadius, y);
    ctx.lineTo(x + width - cornerRadius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + cornerRadius);
    ctx.lineTo(x + width, y + height - cornerRadius);
    ctx.quadraticCurveTo(
      x + width,
      y + height,
      x + width - cornerRadius,
      y + height,
    );
    ctx.lineTo(x + cornerRadius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - cornerRadius);
    ctx.lineTo(x, y + cornerRadius);
    ctx.quadraticCurveTo(x, y, x + cornerRadius, y);
    ctx.closePath();
  }

  drawTooltip(text: string, x: number, y: number): void {

  }

  private distance(
    connectorPoint: ConnectorPoint,
    x: number,
    y: number,
  ): number {
    return Math.sqrt(
      Math.pow(connectorPoint.x - x, 2) + Math.pow(connectorPoint.y - y, 2),
    );
  }

  CreateWidgetControlFromWidget(widget: Widget): WidgetControl {
    let widgetControl = new WidgetControl(widget);
    this.widgetControls.push(widgetControl);
    return widgetControl;
  }

  async applyTemplateWidgets(
    widgetRadius: number,
  ) {
    this.widgetControls = [];
    this.arrows = [];
    let workflowClientTags: WorkflowClientTags = this.SelectedWorkflow!.client_tags;
    let startWidgetControl: WidgetControl | undefined = undefined;
    let endWidgetControl: WidgetControl | undefined = undefined;

    // Create the Start Node for the UX.
    if (this.SelectedWorkflow!.client_tags) {
      if (workflowClientTags.StartWidgetPosition) {
        startWidgetControl = this.CreateNewWidgetControl(
          WidgetType.UX,
          WidgetClientType.Start,
          workflowClientTags.StartWidgetPosition.X,
          workflowClientTags.StartWidgetPosition.Y,
          widgetRadius,
        );
        if (startWidgetControl) {
          startWidgetControl.Widget.name = 'Start';
          startWidgetControl.Widget.description =
            'Connect this to a widget to mark it as the beginning of the workflow';
        }
      }

      // Create the Start Node for the UX.
      if (workflowClientTags.EndWidgetPosition) {
        endWidgetControl = this.CreateNewWidgetControl(
          WidgetType.UX,
          WidgetClientType.End,
          workflowClientTags.EndWidgetPosition.X,
          workflowClientTags.EndWidgetPosition.Y,
          widgetRadius,
        );
        if (endWidgetControl) {
          endWidgetControl.Widget.name = 'End';
          endWidgetControl.Widget.description =
            'Connect this to a widget to mark it as the end of the workflow';
        }
      }
    }
    this.SelectedWorkflow!.widgets.forEach((widget) => {
      // Already added start node
      widget.client_tags.Width = this.WIDGET_START_RADIUS;
      widget.client_tags.Height = this.WIDGET_START_RADIUS;
      if (
        widget.client_tags.ClientType !== WidgetClientType.Start &&
        widget.client_tags.ClientType != WidgetClientType.End
      ) {
        let widgetControl: WidgetControl =
          this.CreateWidgetControlFromWidget(widget);
        if (!this.selectedWidgetControl) {
          this.selectedWidgetControl = widgetControl;
        }
      }
    });
    let arrows: ArrowObject[] | undefined = workflowClientTags.Arrows;
    if (arrows) {
      arrows.forEach((arrow) => {
        if (arrow.start_urn === '0') {
          arrow.start_urn = startWidgetControl?.Widget.urn ?? '0';
        }
        const startWidgetControlIndex = this.widgetControls.findIndex(
          (widgetControl) => widgetControl.Widget.urn === arrow.start_urn,
        );
        const endWidgetControlIndex = this.widgetControls.findIndex(
          (widgetControl) => widgetControl.Widget.urn === arrow.end_urn,
        );
        if (startWidgetControlIndex >= 0 && endWidgetControlIndex >= 0) {
          const startConnectorPointType: ConnectorPointType =
            arrow.start_connector_point_type;
          const endConnectorPointType: ConnectorPointType =
            arrow.end_connector_point_type;
          const arrowType: ArrowType = arrow.arrow_type;
          let startConnectorPoint: ConnectorPoint = new ConnectorPoint(
            this.widgetControls[startWidgetControlIndex],
            startConnectorPointType,
          );
          let endConnectorPoint: ConnectorPoint = new ConnectorPoint(
            this.widgetControls[endWidgetControlIndex],
            endConnectorPointType,
          );
          let newArrow: Arrow = new Arrow(
            startConnectorPoint,
            endConnectorPoint,
            arrowType,
            `arrow-${Date.now()}${Math.random()}`,
          );
          this.arrows.push(newArrow);
        }
      });
    }

  }

  async LoadSessionAndWorkflow(
    siteId: string,
    projectId: string,
    sessionId: string,
    workflowId: string | undefined,
    widgetRadius: number,
    runworkflow: string | undefined,
    run_id: string | undefined,
  ): Promise<string | undefined> {
    this.saveWorkflowResponse = false
    this.widgetControls = [];
    this.arrows = [];

    this.selectedWidgetControl = undefined;
    if (sessionId !== 'skip') {
      this.SelectedWorkflowSession =
        await this.sessionApiService.GetWorkflowSession(
          siteId,
          projectId,
          sessionId,
        );
      if (!this.SelectedWorkflowSession) {
        return undefined;
      }

      if (!workflowId) {
        workflowId = this.SelectedWorkflowSession.workflow_id;
      }
    }

    if (runworkflow == 'true') {
      this.SelectedWorkflow = await this.sessionApiService.GetWorkflowByRunId(
        siteId,
        projectId,
        workflowId!,
        run_id,
      );
    } else {
      this.SelectedWorkflow = await this.sessionApiService.GetWorkflowById(
        siteId,
        projectId,
        workflowId!,
      );
    }
    if (!this.SelectedWorkflow) {
      return undefined;
    }


    let workflowClientTags: WorkflowClientTags =
      this.SelectedWorkflow.client_tags;
    let startWidgetControl: WidgetControl | undefined = undefined;
    let endWidgetControl: WidgetControl | undefined = undefined;

    // Create the Start Node for the UX.
    if (this.SelectedWorkflow.client_tags) {
      if (workflowClientTags.StartWidgetPosition) {
        startWidgetControl = this.CreateNewWidgetControl(
          WidgetType.UX,
          WidgetClientType.Start,
          workflowClientTags.StartWidgetPosition.X,
          workflowClientTags.StartWidgetPosition.Y,
          widgetRadius,
        );
        if (startWidgetControl) {
          startWidgetControl.Widget.name = 'Start';
          startWidgetControl.Widget.description =
            'Connect this to a widget to mark it as the beginning of the workflow';
        }
      }

      // Create the Start Node for the UX.
      if (workflowClientTags.EndWidgetPosition) {
        endWidgetControl = this.CreateNewWidgetControl(
          WidgetType.UX,
          WidgetClientType.End,
          workflowClientTags.EndWidgetPosition.X,
          workflowClientTags.EndWidgetPosition.Y,
          widgetRadius,
        );
        if (endWidgetControl) {
          endWidgetControl.Widget.name = 'End';
          endWidgetControl.Widget.description =
            'Connect this to a widget to mark it as the end of the workflow';
        }
      }
    }
    this.originalSavedWorkflowClone = structuredClone(this.SelectedWorkflow)

    this.SelectedWorkflow.widgets.forEach((widget) => {
      // Already added start node
      widget.client_tags.Width = this.WIDGET_START_RADIUS;
      widget.client_tags.Height = this.WIDGET_START_RADIUS;
      if (
        widget.client_tags.ClientType !== WidgetClientType.Start &&
        widget.client_tags.ClientType != WidgetClientType.End
      ) {
        let widgetControl: WidgetControl =
          this.CreateWidgetControlFromWidget(widget);
        if (!this.selectedWidgetControl) {
          this.selectedWidgetControl = widgetControl;
        }
      }
    });

    let arrows: ArrowObject[] | undefined = workflowClientTags.Arrows;
    if (arrows) {
      let uniqueArrows = new Set()
      arrows.forEach((arrow) => {
        if (arrow.start_urn && arrow.end_urn) {
          let key = arrow.start_urn + arrow.end_urn
          if (uniqueArrows.has(key)) return;
          uniqueArrows.add(key)
        }
        if (arrow.start_urn === '0') {
          arrow.start_urn = startWidgetControl?.Widget.urn ?? '0';
        }
        const startWidgetControlIndex = this.widgetControls.findIndex(
          (widgetControl) => widgetControl.Widget.urn === arrow.start_urn,
        );
        const endWidgetControlIndex = this.widgetControls.findIndex(
          (widgetControl) => widgetControl.Widget.urn === arrow.end_urn,
        );
        if (startWidgetControlIndex >= 0 && endWidgetControlIndex >= 0) {
          const startConnectorPointType: ConnectorPointType =
            arrow.start_connector_point_type;
          const endConnectorPointType: ConnectorPointType =
            arrow.end_connector_point_type;
          const arrowType: ArrowType = arrow.arrow_type;
          let startConnectorPoint: ConnectorPoint = new ConnectorPoint(
            this.widgetControls[startWidgetControlIndex],
            startConnectorPointType,
          );
          let endConnectorPoint: ConnectorPoint = new ConnectorPoint(
            this.widgetControls[endWidgetControlIndex],
            endConnectorPointType,
          );
          let newArrow: Arrow = new Arrow(
            startConnectorPoint,
            endConnectorPoint,
            arrowType,
            `arrow-${Date.now()}${Math.random()}`,
          );
          this.arrows.push(newArrow);
        }
      });
    }
    if (this.SelectedWorkflow?.partial_widgets) {
      this.invalid_widgets = this.SelectedWorkflow.partial_widgets
      this.saveWorkflowResponse = true;
    }
    return workflowId;
  }

  updateWorkflowToBeSaved() {
    this.originalSavedWorkflowClone = structuredClone(this.SelectedWorkflow)
  }

  createOutputConfig(widget: Widget) {
    let selectedProjectId: string | undefined =
      this.configService.SelectedProjectId;
    let selectedProjectName: string | undefined =
      this.configService.SelectedProjectName;
    if (!selectedProjectId || !selectedProjectName) {
      return;
    }
    let name = Utils.GetNamedOutput(widget, selectedProjectName);
    let outputConfig: InputOutputConfig = new InputOutputConfig();
    outputConfig.urn = widget.urn!;
    outputConfig.name = name!;

    let outputConfig2: InputOutputConfig = new InputOutputConfig();
    outputConfig2.urn = widget.urn!;
    outputConfig2.name = name + '_Table';

    let outputConfig3: InputOutputConfig = new InputOutputConfig();
    outputConfig3.urn = widget.urn!;
    outputConfig3.name = name + '_Model_artifacts';


    switch (widget.type) {
      case WidgetType.DATA_COPY:
      case WidgetType.PIVOT:
      case WidgetType.FILTER:
      case WidgetType.JUPYTER:  
      case WidgetType.DROP_COLUMNS:
      case WidgetType.DROP_MISSING:
      case WidgetType.RENAME_COLUMNS:
      case WidgetType.DATATYPE_CONVERSION:
      case WidgetType.DECISION:
      case WidgetType.JOIN:
      case WidgetType.APPEND:
      case WidgetType.MOBO:
      case WidgetType.RESCALE:
      case WidgetType.THERMOCALC:
      case WidgetType.POST_RESCALE:
      case WidgetType.Feature_Engineering:
      case WidgetType.CUSTOM_CODE:
      case WidgetType.ACTIVE_LEARNING:
      case WidgetType.PREDICTION:
      case WidgetType.IMAGE_DATASET:
      case WidgetType.REGION_PROPERTY:
      case WidgetType.IMAGE_SPATIAL_STATISTICS:
      case WidgetType.ARIMA:
      case WidgetType.TEXT_DATA:
        widget.outputs.push(outputConfig);
        if (widget.type === 'CUSTOM_CODE') {
          setTimeout(() => {
            widget.outputs = widget.outputs.map((item: any) => {
              if (item.name.includes("Tabular")) {
                const newName = item.type
                  ? item.name.replace(/Tabular\d*/, item.type)
                  : item.name;
                return {
                  ...item,
                  name: newName,
                };
              }
              return item;
            });
          }, 1000);
        };
        break;
      case WidgetType.AUTOML:
      case WidgetType.RF:
      case WidgetType.SVM:
      case WidgetType.NNFASTAI:
      case WidgetType.NN_TORCH:
      case WidgetType.MPR:
      case WidgetType.KNEIGHBORS:
      case WidgetType.GPR:
      case WidgetType.GPC:
      case WidgetType.EXTRA_TREES:
      case WidgetType.CATBOOST:
      case WidgetType.XGBOOST:
      case WidgetType.LINEAR_REGRESSION:
        widget.outputs.push(outputConfig);
        widget.outputs.push(outputConfig3);
        break;
      case WidgetType.LGBM:
        widget.outputs.push(outputConfig);
        widget.outputs.push(outputConfig2);
        widget.outputs.push(outputConfig3);
        break;
      case WidgetType.SAVE:
        return;
    }

    switch (widget.client_tags.ClientType) {
      case WidgetClientType.Pivot:
        widget.outputs.push(outputConfig);
        break;
    }
  }

  public CreateNewWidgetControl(
    widgetType: WidgetType,
    widgetClientType: WidgetClientType,
    positionX: number,
    positionY: number,
    widgetRadius: number,
    widgetId: string | null = null,
    widgetName: string | null = null,
  ): WidgetControl | undefined {
    if (!this.SelectedWorkflow) {
      return;
    }
    if (positionX === -1 || positionY === -1) {
      positionX = Math.floor(Math.random() * (200 - 50 + 1)) + 50;
      positionY = Math.floor(Math.random() * (200 - 50 + 1)) + 50;
    }

    let defaultWidgetConfiguration: any =
      this.workflowConfigService.CreateDefaultConfigurationForWidgetType(
        widgetType,
        widgetClientType,
      );

    if (!defaultWidgetConfiguration && this.notificationComponent) {
      this.notificationComponent.display(
        'Support for this widget will be added soon.',
        'success',
      );
      return undefined;
    }

    let tags: WidgetClientTags = new WidgetClientTags();
    tags.PositionX = positionX;
    tags.PositionY = positionY;
    tags.Width = widgetRadius;
    tags.Height = widgetRadius;
    tags.Color = this.DEFAULT_WIDGET_HEADER_COLOR;
    tags.ClientType = widgetClientType;
    let DefaultWidgetName = this.generateUniqueWidgetName(widgetClientType, widgetName);

    let widget: Widget = this.workflowConfigService.createNewWidget(
      defaultWidgetConfiguration,
      widgetType,
      tags,
      DefaultWidgetName,
      widgetId,
    );

    if (widgetClientType === WidgetClientType.Start) {
      widget.urn = 'START';
    } else if (widgetClientType === WidgetClientType.End) {
      widget.urn = 'END';
    } else {
      widget.urn = Utils.GenerateGuid();
      this.createOutputConfig(widget);
    }

    let widgetControl = new WidgetControl(widget);
    let zIndex = 0;
    if (this.widgetControls.length > 0) {
      let highestWidget = this.getWidgetControlWithHighestZIndex();
      if (highestWidget) {
        zIndex = highestWidget.ZIndex + 1;
      }
    }
    widgetControl.ZIndex = zIndex;
    this.widgetControls.push(widgetControl);
    this.widgetControls = this.sortWidgetControlsByZIndexDesc();

    this.SelectedWorkflow.widgets.push(widget);
    this._selectedWorkflow.next(this.SelectedWorkflow);

    return widgetControl;
  }

  generateUniqueWidgetName(widgetClientType: any, widgetName: any): string {
    const randomString = this.generateRandomString(4);
    if (widgetClientType == 'CUSTOM_CODE') {
      const baseName = `${widgetName}-`;
      const fullname = `${baseName}${randomString}`;
      return fullname
    }
    const baseName = `${widgetClientType}-`;
    return `${baseName}${randomString}`;
  }

  generateRandomString(length: number): string {
    const characters =
      'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let randomString = '';

    for (let i = 0; i < length; i++) {
      const randomIndex = Math.floor(Math.random() * characters.length);
      randomString += characters.charAt(randomIndex);
    }

    return randomString;
  }

  private sortWidgetControlsByZIndexDesc(): WidgetControl[] {
    // Create a copy of the activities array to avoid mutating the original array
    return [...this.widgetControls].sort((a, b) => a.ZIndex - b.ZIndex);
  }

  getWidgetControlWithHighestZIndex(): WidgetControl | undefined {
    return this.widgetControls.reduce((prev, current) => {
      return prev.ZIndex > current.ZIndex ? prev : current;
    }, this.widgetControls[0]);
  }

  public FindClosestConnector(
    widgetControl: WidgetControl,
    mouseX: number,
    mouseY: number,
  ) {
    let closestPoint = widgetControl.ConnectorPoints[0];
    let minDistance = this.distance(closestPoint, mouseX, mouseY);

    for (let i = 1; i < widgetControl.ConnectorPoints.length; i++) {
      const point = widgetControl.ConnectorPoints[i];
      const dist = this.distance(point, mouseX, mouseY);

      if (dist < minDistance) {
        minDistance = dist;
        closestPoint = point;
      }
    }
    return closestPoint;
  }

  drawWidgetIconTextToFit(
    ctx: CanvasRenderingContext2D,
    canvas: ElementRef<HTMLCanvasElement>,
    iconCode: string,
    positionX: number,
    positionY: number,
    maxWidth: number,
    maxHeight: number,
  ) {
    if (!ctx) {
      return;
    }

    let fontSize = Math.min(maxWidth, maxHeight); // Start with a font size that fits within both maxWidth and maxHeight
    ctx.font = `${fontSize}px "Material Symbols Outlined"`;

    // Measure text width once
    let textMetrics = ctx.measureText(iconCode);

    // Adjust font size if needed
    if (textMetrics.width > maxWidth || fontSize > maxHeight) {
      fontSize = Math.min((maxWidth / textMetrics.width) * fontSize, maxHeight);
      ctx.font = `${fontSize}px "Material Symbols Outlined"`;
      textMetrics = ctx.measureText(iconCode); // Re-measure text width after adjusting font size
    }

    // Set text properties
    ctx.fillStyle = 'white';

    // Calculate the centered position
    const textX = positionX + textMetrics.width / 2;
    const textY = positionY + maxHeight * 1.5;

    // Draw text
    ctx.fillText(iconCode, textX, textY);
  }

  drawStartIconTextToFit(
    ctx: CanvasRenderingContext2D,
    iconCode: string,
    positionX: number,
    positionY: number,
    maxWidth: number,
    maxHeight: number,
  ) {
    if (!ctx) {
      return;
    }

    positionX += maxWidth / 2;
    positionY += maxHeight / 2;
    let fontSize = 300; // Start with a large font size

    ctx.font = `006 ${fontSize}px "Roboto"`;

    // Measure text and adjust font size
    let textMetrics = ctx.measureText(iconCode);
    while (textMetrics.width > maxWidth || fontSize > maxHeight) {
      fontSize -= 1; // Decrease font size
      ctx.font = `006 ${fontSize}px "Roboto"`;
      textMetrics = ctx.measureText(iconCode);
    }

    // Set text properties
    ctx.fillStyle = 'white';

    // Draw text
    ctx.fillText(iconCode, positionX, positionY + fontSize);
  }

  drawWidgetName(
    ctx: CanvasRenderingContext2D,
    widgetX: number,
    widgetY: number,
    widgetRadius: number,
    text: string,
  ): void {
    // Set initial font for measurement
    ctx.font = `12px "Roboto"`;
    let fittedText = text;
    let textWidth = ctx.measureText(fittedText).width;

    // Check if text width exceeds widget width and truncate if necessary
    if (textWidth > widgetRadius * 2) {
      // Multiply by 2 because radius is only half the width
      while (
        ctx.measureText(fittedText + '...').width > widgetRadius * 2 &&
        fittedText.includes(' ')
      ) {
        // Shorten the string by one word each loop
        fittedText = fittedText.substring(0, fittedText.lastIndexOf(' '));
      }
      fittedText += '...'; // Add ellipsis
      textWidth = ctx.measureText(fittedText).width; // Update text width
    }

    // Calculate the starting position to center the truncated text in the widget
    const x = widgetX + (widgetRadius - textWidth) / 2; // Adjusted for correct centering
    const textHeight = ctx.measureText('M').actualBoundingBoxAscent; // Approximate height for vertical centering
    const y = widgetY + widgetRadius + textHeight / 2 + 10; // Center vertically in widget

    // Draw the text
    ctx.fillStyle = 'black';
    ctx.fillText(fittedText, x, y); // Draw the text centered in the widget
  }

  public DrawWidgetControl(
    ctx: CanvasRenderingContext2D | null,
    canvas: ElementRef<HTMLCanvasElement>,
    widgetControl: WidgetControl,
    widgetRadius: number,
  ) {
    if (!ctx || !canvas) {
      return;
    }

    let positionX: number = widgetControl.GetPositionX();
    let positionY: number = widgetControl.GetPositionY();
    let color: string = widgetControl.GetColor();
    let widgetName: string = '';
    widgetName = widgetControl.Widget.name;
    if (widgetControl.Widget.client_tags?.widget_number)
      widgetName = widgetControl.Widget.client_tags?.widget_number + ' - ' + widgetControl.Widget.name

    if (
      this.HoveringArrowToWidgetControl === widgetControl ||
      this.selectedWidgetControl == widgetControl
    ) {
      ctx.lineWidth = 3;
    } else {
      ctx.lineWidth = 1;
    }
    ctx.fillStyle = 'white';
    ctx.strokeStyle = color;

    let imageToDraw: any = undefined;

    let selected = this.selectedWidgetControl === widgetControl;
    let iconCode: any = undefined;
    imageToDraw = selected
      ? this.selectedIngestionIconImage
      : this.unSelectedIngestionIconImage;

    // To pick out an icon, visit: https://fonts.google.com/icons

    switch (widgetControl.Widget.client_tags.ClientType) {
      case WidgetClientType.LoopStart:
        iconCode = 'line_start_circle';
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        break;
      case WidgetClientType.LoopEnd:
        iconCode = 'line_end_circle';
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        break;
      case WidgetClientType.Filter:
        iconCode = 'filter_alt';
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        break;
      case WidgetClientType.BigQuery:
        iconCode = 'search_insights';
        imageToDraw = selected
          ? this.selectedDataWidget
          : this.unSelectedDataWidget;
        break;
      case WidgetClientType.CSVFile:
        imageToDraw = selected
          ? this.selectedDataWidget
          : this.unSelectedDataWidget;
        iconCode = 'csv';
        break;
      case WidgetClientType.Jupyter:
        imageToDraw = selected
          ? this.selectedDataWidget
          : this.unSelectedDataWidget;
        iconCode = 'jupyter';
        break;  
      case WidgetClientType.Join:
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        iconCode = 'join_inner';
        break;
      case WidgetClientType.Append:
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        iconCode = 'add';
        break;
      case WidgetClientType.ConfigFile:
        imageToDraw = selected
          ? this.selectedIngestionIconImage
          : this.unSelectedIngestionIconImage;
        iconCode = 'manufacturing';
        break;
      case WidgetClientType.CustomCode:
        imageToDraw = selected
          ? this.selectedMLIconImage
          : this.unSelectedMLIconImage;
        iconCode = 'code';
        break;
      case WidgetClientType.LGBM:
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        iconCode = 'share';
        break;
      case WidgetClientType.ExcelFile:
        imageToDraw = selected
          ? this.selectedDataWidget
          : this.unSelectedDataWidget;
        iconCode = 'table_view';
        break;
      case WidgetClientType.MOBO:
        iconCode = 'stacked_line_chart';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.Pivot:
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        iconCode = 'pivot_table_chart';
        break;
      case WidgetClientType.Python:
        imageToDraw = selected
          ? this.selectedMLIconImage
          : this.unSelectedMLIconImage;
        iconCode = 'developer_mode_tv';
        break;
      case WidgetClientType.Union:
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        iconCode = 'join';
        break;

      case WidgetClientType.POST_RESCALE:
        imageToDraw = selected
          ? this.selectedMLIconImage
          : this.unSelectedMLIconImage;
        iconCode = 'aspect_ratio';
        break;
      case WidgetClientType.Rescale:
        imageToDraw = selected
          ? this.selectedMLIconImage
          : this.unSelectedMLIconImage;
        iconCode = 'filter_drama';
        break;
      case WidgetClientType.ThermoCalc:
        imageToDraw = selected
          ? this.selectedMLIconImage
          : this.unSelectedMLIconImage;
        iconCode = 'change_history';
        break;

      case WidgetClientType.RescaleTemplateConnector:
        imageToDraw = selected
          ? this.selectedMLIconImage
          : this.unSelectedMLIconImage;
        iconCode = 'hub';
        break;
      case WidgetClientType.Save:
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        iconCode = 'save';
        break;
      case WidgetClientType.Decision:
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        iconCode = 'fence';
        break;
      case WidgetClientType.Feature_Engineering:
        iconCode = 'manufacturing';
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        break;
      case WidgetClientType.Start:
      case WidgetClientType.End:
        imageToDraw = selected
          ? this.startEndNodeImage
          : this.startEndNodeImage;
        break;
      case WidgetClientType.ACTIVE_LEARNING:
        iconCode = 'repeat';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.GPR:
        iconCode = 'ssid_chart';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.MPR:
        iconCode = 'ssid_chart';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.PREDICTION:
        iconCode = 'query_stats';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.SVM:
        iconCode = 'scatter_plot';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.AutoML:
        iconCode = 'settings_motion_mode';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.LINEAR_REGRESSION:
        iconCode = 'analytics';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.RF:
        iconCode = 'network_node';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.NNFASTAI:
        iconCode = 'hub';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.NN_TORCH:
        iconCode = 'grain';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.XGBOOST:
        iconCode = 'linked_services';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.CATBOOST:
        iconCode = 'tenancy';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.KNEIGHBORS:
        iconCode = 'blur_circular';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.EXTRA_TREES:
        iconCode = 'spoke';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.IMAGE_DATASET:
        iconCode = 'photo';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.REGION_PROPERTY:
        iconCode = 'grid_on';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.IMAGE_SPATIAL_STATISTICS:
        iconCode = 'stacks';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.ARIMA:
        iconCode = 'hub';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.GPC:
        iconCode = 'bubble_chart';
        imageToDraw = selected
          ? this.selectedGeneralIconImage
          : this.unSelectedGeneralIconImage;
        break;
      case WidgetClientType.ParquetFile:
        iconCode = 'data_table';
        imageToDraw = selected
          ? this.selectedDataWidget
          : this.unSelectedDataWidget;
        break;
      case WidgetClientType.DropColumns:
        iconCode = 'view_column';
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        break;
      case WidgetClientType.DropMissing:
        iconCode = 'delete_sweep';
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        break;
      case WidgetClientType.RenameColumns:
        iconCode = 'edit_note';
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        break;
      case WidgetClientType.DatatypeConversion:
        iconCode = 'convert_to_text';
        imageToDraw = selected
          ? this.selectedCurationIconImage
          : this.unSelectedCurationIconImage;
        break;
      case WidgetClientType.TEXT_FILE:
        iconCode = 'text_fields';
        imageToDraw = selected
          ? this.selectedDataWidget
          : this.unSelectedDataWidget;
        break;
    }

    if (imageToDraw) {
      if (selected) {
        ctx.shadowOffsetX = 5; // Horizontal distance of the shadow, in relation to the text.
        ctx.shadowOffsetY = 5; // Vertical distance of the shadow, in relation to the text.
        ctx.shadowBlur = 22; // The blur level for the shadow.
        ctx.shadowColor = 'rgba(0,0,0,0.5)'; // Shadow color in RGBA format for transparency.
      }
      ctx.drawImage(
        imageToDraw,
        positionX,
        positionY,
        widgetRadius,
        widgetRadius,
      );

      // Reset shadow properties to remove the shadow effect
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 0;
      ctx.shadowBlur = 0;
      ctx.shadowColor = 'rgba(0, 0, 0, 0)'; // Alternatively, 'transparent'
    }

    if (iconCode) {
      this.drawWidgetIconTextToFit(
        ctx,
        canvas,
        iconCode,
        positionX,
        positionY,
        widgetRadius / 2,
        widgetRadius / 2,
      );
    }

    if (
      widgetControl.Widget.client_tags.ClientType === WidgetClientType.Start
    ) {
      this.drawStartIconTextToFit(
        ctx,
        'Start',
        positionX,
        positionY + widgetRadius / 9,
        widgetRadius / 2,
        widgetRadius / 2,
      );
    } else if (
      widgetControl.Widget.client_tags.ClientType === WidgetClientType.End
    ) {
      this.drawStartIconTextToFit(
        ctx,
        'End',
        positionX,
        positionY + widgetRadius / 9,
        widgetRadius / 2,
        widgetRadius / 2,
      );
    }
    if (widgetControl.Widget.type !== WidgetType.UX) {
      this.drawWidgetName(ctx, positionX, positionY, widgetRadius, widgetName);
    }

    if (this.IsViewingRunMode) {
      return;
    }

    if (this.selectedWidgetControl === widgetControl) {
      CanvasUtils.DrawHollowCircle(
        ctx,
        positionX + widgetRadius / 2,
        positionY,
        this.circleRadius,
        color,
      );
      CanvasUtils.DrawHollowCircle(
        ctx,
        positionX + widgetRadius / 2,
        positionY + widgetRadius,
        this.circleRadius,
        color,
      );
      CanvasUtils.DrawHollowCircle(
        ctx,
        positionX,
        positionY + widgetRadius / 2,
        this.circleRadius,
        color,
      );
      CanvasUtils.DrawHollowCircle(
        ctx,
        positionX + widgetRadius,
        positionY + widgetRadius / 2,
        this.circleRadius,
        color,
      );
    }
  }

  public GetClosestConnectionPoints(startWidget: Widget, endWidget: Widget) {
    let minDistance = Infinity;
    let closestPoints: [[number, number], [number, number]] | null = null;

    for (let pos1 of Widget.GetConnectorPointPositions(startWidget)) {
      for (let pos2 of Widget.GetConnectorPointPositions(endWidget)) {
        let distance = Math.sqrt(
          Math.pow(pos2[0] - pos1[0], 2) + Math.pow(pos2[1] - pos1[1], 2),
        );
        if (distance < minDistance) {
          minDistance = distance;
          closestPoints = [pos1, pos2];
        }
      }
    }

    return closestPoints!;
  }

  public GetWidgetNameByType(
    widgetType: WidgetType,
    widgetClientType: WidgetClientType,
  ): string {
    switch (widgetType) {
      case WidgetType.DATA_COPY:
        switch (widgetClientType) {
          case WidgetClientType.BigQuery:
            return 'Big Query';
          case WidgetClientType.CSVFile:
            return 'CSV File';
          case WidgetClientType.ImageFile:
            return 'Image File';
          case WidgetClientType.ParquetFile:
            return 'Parquet File';
          case WidgetClientType.ExcelFile:
            return 'Excel File';
          case WidgetClientType.TEXT_FILE:
            return 'Text File';
          default:
            return 'Unknown';
        }
        break;
      case WidgetType.CONFIG_FILE:
        return 'Config File';
      case WidgetType.CUSTOM_CODE:
        return 'Custom Code';
      case WidgetType.FILTER:
        return 'Filter';
      case WidgetType.JUPYTER:
        return 'Jupyter';  
      case WidgetType.DROP_COLUMNS:
        return 'Drop Columns';
      case WidgetType.DROP_MISSING:
        return 'Drop Missing'
      case WidgetType.RENAME_COLUMNS:
        return 'Rename Columns'
      case WidgetType.DATATYPE_CONVERSION:
        return 'Datatype Conversion'
      case WidgetType.PIVOT:
        return 'Pivot';
      case WidgetType.JOIN:
        return 'Join';
      case WidgetType.UNION:
        return 'Union';
      case WidgetType.APPEND:
        return 'Append';
      case WidgetType.MODEL_BUILDER:
        switch (widgetClientType) {
          default:
            return 'LGBM';
        }
        break;
      case WidgetType.PYTHON:
        return 'Python';
      case WidgetType.SAVE:
        return 'SAVE';
      case WidgetType.POST_RESCALE:
        return 'Post Rescale';
      case WidgetType.RESCALE:
        return 'Rescale';
      case WidgetType.DECISION:
        return 'Decision';
      case WidgetType.Feature_Engineering:
        return 'Feature Engineering';
      case WidgetType.MOBO:
        return 'MOBO';
      case WidgetType.THERMOCALC:
        return 'ThermoCalc';
      case WidgetType.ACTIVE_LEARNING:
        return 'ACTIVE_LEARNING';
      case WidgetType.GPR:
        return 'GPR';
      case WidgetType.MPR:
        return 'MPR';
      case WidgetType.PREDICTION:
        return 'PREDICTION';
      case WidgetType.SVM:
        return 'SVM';
      case WidgetType.AUTOML:
        return 'AutoML';
      case WidgetType.LGBM:
        return 'LGBM';
      case WidgetType.LINEAR_REGRESSION:
        return 'LINEAR_REGRESSION';
      case WidgetType.RF:
        return 'RF';
      case WidgetType.NNFASTAI:
        return 'NNFASTAI';
      case WidgetType.NN_TORCH:
        return 'NN_TORCH';
      case WidgetType.ARIMA:
        return 'ARIMA';
      case WidgetType.EXTRA_TREES:
        return 'EXTRA TREES';
      case WidgetType.IMAGE_DATASET:
        return 'IMAGE DATASET';
      case WidgetType.REGION_PROPERTY:
        return 'REGION PROPERTY';
      case WidgetType.IMAGE_SPATIAL_STATISTICS:
        return 'Image Special Statistics';
      case WidgetType.GPC:
        return 'GPC';
      case WidgetType.TEXT_DATA:
        return 'VPSC_DATA';
      default:
        return 'Unknown';
    }
  }

  public IsDataPreviewHoverButtonClicked(mouseX: number, mouseY: number) {
    if (this.dataPreviewHoverIcon === undefined) {
      return false;
    }

    return (
      mouseX >= this.dataPreviewHoverIcon.PositionX - 20 &&
      mouseX <= this.dataPreviewHoverIcon.PositionX + 20 &&
      mouseY >= this.dataPreviewHoverIcon.PositionY - 20 &&
      mouseY <= this.dataPreviewHoverIcon.PositionY + 20
    );
  }

  public GetWidgetUnderPointer(mouseX: number, mouseY: number) {
    return this.widgetControls.find((widget) => {
      const posX = widget.Widget.client_tags.PositionX;
      const posY = widget.Widget.client_tags.PositionY;
      const width = widget.Widget.client_tags.Width;
      const height = widget.Widget.client_tags.Height;
      return (
        mouseX >= posX &&
        mouseX <= posX + width &&
        mouseY >= posY &&
        mouseY <= posY + height
      );
    });
  }

  public GetConnectorPointUnderMousePointer(
    mouseX: number,
    mouseY: number,
    tolerance: number = 15,
  ): ConnectorPoint | undefined {
    if (!this.selectedWidgetControl) {
      return undefined;
    }
    for (const point of this.selectedWidgetControl.ConnectorPoints) {
      if (
        Math.abs(point.x - mouseX) <= tolerance &&
        Math.abs(point.y - mouseY) <= tolerance
      ) {
        return point;
      }
    }
    return undefined;
  }

  public MoveWidget(newX: number, newY: number, canvasWidth: number, canvasHeight: number, widgetWidth: number, widgetHeight: number, snapToGrid: boolean = false): void {
    if (this.selectedWidgetControl) {
      this.changeMadeToWorkflow = true;
      if (snapToGrid) {
        newX = Math.round(newX / this.gridSpacing) * this.gridSpacing;
        newY = Math.round(newY / this.gridSpacing) * this.gridSpacing;
      }
      newX = Math.max(0, Math.min(newX, canvasWidth - widgetWidth));
      newY = Math.max(0, Math.min(newY, canvasHeight - widgetHeight));
      this.selectedWidgetControl.Widget.client_tags.PositionX = newX;
      this.selectedWidgetControl.Widget.client_tags.PositionY = newY;
    }
  }


  public renderWidget(
    ctx: CanvasRenderingContext2D,
    widgetControl: WidgetControl,
  ): void {
    if (widgetControl.backgroundColor) {
      ctx.fillStyle = widgetControl.backgroundColor;
      ctx.fillRect(
        widgetControl.GetPositionX(),
        widgetControl.GetPositionY(),
        widgetControl.GetWidth(),
        widgetControl.GetHeight(),
      );
    }
    ctx.strokeStyle = widgetControl.GetColor();
    ctx.strokeRect(
      widgetControl.GetPositionX(),
      widgetControl.GetPositionY(),
      widgetControl.GetWidth(),
      widgetControl.GetHeight(),
    );
  }

  public viewingRunMode() {
    if (this.IsViewingRunMode) {
      return true;
    } else {
      return false;
    }
  }

  public containsRescaleWidget(): boolean {
    return this.widgetControls.some(
      (widgetControl) => widgetControl.Widget.type === WidgetType.RESCALE
    );
  }
}
export { ConfigService };
