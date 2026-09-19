import {
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { Project } from 'src/app/models/project-models';
import { ConfigService } from 'src/app/services/config.service';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { NotificationComponent } from '../../notification/notification.component';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ApiService } from 'src/app/services/api.service';
import { DataPreviewComponent } from 'src/app/dialogs/data-preview/data-preview.component';
import { MatDialog, MatDialogRef, MatDialogState } from '@angular/material/dialog';
import { WidgetControl } from '../../widget-control/widget-control';
import { WebSocketService } from 'src/app/services/web-sockets.service';
import { interval, Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { DatasetModel } from 'src/app/models/workflow-models';
import { WorkflowDesignerServiceService } from 'src/app/pages/workflow-designer/workflow-designer-service.service';
import { WidgetRunResult } from 'src/app/models/workflow-sessions-api-response.models';
import { VisualizeTextdataComponent } from 'src/app/dialogs/data-preview/visualize/visualize-textdata/visualize-textdata.component';



@Component({
  selector: 'app-config-action-bar',
  templateUrl: './config-action-bar.component.html',
  styleUrls: ['./config-action-bar.component.less'],
})
export class ConfigActionBarComponent implements OnInit, OnDestroy {
  supportedWidgets: string[] = [];
  tabularWidgets: string[] = [];
  tabularDirectWidgets: string[] = [];
  MlWidgets: string[] = [];
  filterMlWidgets: any;
  @ViewChild('notification') notificationComponent!: NotificationComponent;
  @Output() callParentFunction: EventEmitter<any> = new EventEmitter<any>();
  @Input() widgetName: string = '';
  @Input() TextWidgetconfig: any;
  @Input() widgetUrn: string = '';
  @Input() siteId: string = '';
  pollingSubscription!: Subscription;
  private rescaleSocketSubscription: Subscription | null = null;
  dialogRef: MatDialogRef<DataPreviewComponent> | null = null;
  dialogRefText: MatDialogRef<VisualizeTextdataComponent> | null = null;

  constructor(
    private apiService: ApiService,
    private sessionApis: WorkflowsSessionsApiService,
    private sharedDataService: SharedDataService,
    private configService: ConfigService,
    public workflowCanvasService: WorkflowCanvasService,
    private dialog: MatDialog,
    private webSocketService: WebSocketService,
    private cdr: ChangeDetectorRef,
    public workflowDesignerService: WorkflowDesignerServiceService
  ) {
    this.MlWidgets = [
      'AUTOML',
      'LINEAR_REGRESSION',
      'LGBM',
      'RF',
      'NNFASTAI',
      'NN_TORCH',
      'XGBOOST',
      'CATBOOST',
      'KNEIGHBORS',
      'EXTRA_TREES',
      'ARIMA',
      'SVM',
      'GPC',
      'GPR',
      'MPR'
    ];

    this.supportedWidgets = [
      'Auto ML Widget',
      'RF ML Widget',
      'CAT BOOST ML Widget',
      'Extra Trees ML Widget',
      'K-Nearest Neighbors ML Widget',
      'GPR Widget',
      'XG BOOST ML Widget',
      'Linear Regression ML Widget',
      'LGBM ML Widget',
      'NN Torch ML Widget',
      'NNFASTAI ML Widget',
      'ARIMA ML Widget',
      'SVM Widget',
      'GPC Widget',
      'MPR Widget'
    ];

    this.tabularWidgets = [
      'CSV Widget',
      'Parquet Widget',
      'Prediction Widget',
      'ThermoCalc Widget',
      'MOBO',
      'Save',
      'Drop Columns Widget',
      'Drop Missing Widget',
      'Rename Columns',
      'Filter',
      'Rescale',
      'Join',
      'Datatype Conversion',
      'CPW Widget',
      'Excel Widget',
      'Region Property Widget',
      'Spatial Statistics Widget',
      'Text Widget'
    ];

    this.tabularDirectWidgets = [
      'CSV Widget',
      'Parquet Widget',
      'Excel Widget'
    ];

  }

  private saveCompleteSubscription: Subscription | undefined;

  ngOnInit(): void {
    this.workflowCanvasService.workflowRunStatus$.subscribe(status => {
      if (status && status.run_status?.toLowerCase() === 'running') {
        const hasRescaleWidget = this.workflowCanvasService.SelectedWorkflow?.widgets.some(widget => {
          return widget.type === 'RESCALE';
        });
        if (hasRescaleWidget) {
          if (!this.isRescaleSocketConnected()) {
            this.connectToRescaleWebSocket();
            this.startPollingForWidgetStatus(this.widgetUrn, this.widgetName);
          }
        }
      }
    });

    this.saveCompleteSubscription = this.workflowDesignerService.triggerExecuteWidget$.subscribe(value => {
      if (value === true) {
        this.workflowDesignerService.setTriggerExecuteWidget(false);
        this.executeWidget();
      }
    });
    this.filterMlWidgets = this.workflowCanvasService.SelectedWorkflow?.widgets.filter(widget => this.MlWidgets.includes(widget.type))
  }

  ngOnDestroy(): void {
    this.saveCompleteSubscription?.unsubscribe();
  }


  startPollingForWidgetStatus(widgetUrn: string, widgetName: String) {
    const intervalId = setInterval(() => {
      const status = this.checkWidgetStatus(widgetUrn);
      if ((status === 'succeeded' || status === 'failed') && widgetName == 'Rescale') {
        clearInterval(intervalId);
        setTimeout(() => {
          this.webSocketService.disconnectRescaleSocket();
          this.sharedDataService.clearRescaleDatasetId(this.widgetUrn);
          if (this.rescaleSocketSubscription) {
            this.rescaleSocketSubscription.unsubscribe();
            this.rescaleSocketSubscription = null;
          }
        }, 2000);
      }
    }, 5000);
  }

  onPreviewDataButton() {
    if (this.widgetName === 'Rescale' && this.isRescaleWidgetRunning()) {
      const rescaleDatasetId = this.sharedDataService.getRescaleDatasetId(this.widgetUrn);
      if (rescaleDatasetId) {
        this.openDataPreviewDialog(rescaleDatasetId);
      }
    } else if (this.widgetName === 'CPW Widget') {
      let results: WidgetRunResult[] = this.workflowCanvasService.getWidgetRunResults();
      if (results.length > 0) {
        let visualizationData = results.filter((result: any) => result.result_type === 'VISUALIZATION' || result.result_type === 'STRINGS_LIST');
        if (visualizationData.length > 0) {
          this.callParentFunction.emit({ view: 'multiple' });
        } else {
          this.onPreviewDataButtonClicked();
        }
      }
    } else if (this.tabularWidgets.includes(this.widgetName)) {
      this.onPreviewDataButtonClicked();
    } else if (this.supportedWidgets.includes(this.widgetName)) {
      this.callParentFunction.emit({ view: 'multiple' });
    }
  }

  onMLPreviewData(view: any) {
    if (this.supportedWidgets.includes(this.widgetName)) {
      this.callParentFunction.emit({ view: view });
    }
  }


  private isRescaleWidgetRunning(): boolean {
    return this.widgetName === 'Rescale' && this.checkIfWidgetIsRunning(this.widgetUrn);
  }

  connectToRescaleWebSocket() {
    this.webSocketService.connectRescaleSocket();

    const rescaleSocketMessages = this.webSocketService.rescaleSocketMessages;
    if (rescaleSocketMessages) {
      this.rescaleSocketSubscription = rescaleSocketMessages.subscribe(
        (msg) => {
          if (msg.dataset_id) {
            this.sharedDataService.setRescaleDatasetId(this.widgetUrn, msg.dataset_id);
          } else {
            this.sharedDataService.clearRescaleDatasetId(this.widgetUrn);
          }
          const widgetStatus = this.checkWidgetStatus(this.widgetUrn);

          if (this.isDialogOpen() && widgetStatus === 'running' && this.widgetName === 'Rescale') {
            const dataPreviewDialog = this.dialog.openDialogs.find(
              dialog => dialog.componentInstance instanceof DataPreviewComponent
            );
            dataPreviewDialog?.componentInstance.refreshData();
          }

          this.cdr.detectChanges();
        },
        (err) => {
          console.error('Error from Rescale WebSocket:', err);
          this.sharedDataService.clearRescaleDatasetId(this.widgetUrn);
          this.cdr.detectChanges();
        },
        () => {
          this.sharedDataService.clearRescaleDatasetId(this.widgetUrn);
          if (this.rescaleSocketSubscription) {
            this.rescaleSocketSubscription.unsubscribe();
            this.rescaleSocketSubscription = null;
          }
          this.cdr.detectChanges();
        }
      );
    } else {
      console.error('Rescale WebSocket is not connected.');
    }
  }

  isRescaleSocketConnected(): boolean {
    return this.rescaleSocketSubscription !== null && !this.rescaleSocketSubscription.closed;
  }

  async onPreviewDataButtonClicked() {
    const widgetControl: WidgetControl | undefined = this.workflowCanvasService.selectedWidgetControl;
    if (!widgetControl) {
      return;
    }
    const dataSetIds: DatasetModel[] | string | undefined = await this.workflowCanvasService.GetResultDatasetIdsForWidgetControl(widgetControl);
    if (dataSetIds && dataSetIds.length > 0) {
      this.openDataPreviewDialog(dataSetIds);
    }
    else {
      console.error('No dataset IDs available for widget:', widgetControl.Widget.urn);
    }
  }

  openDataPreviewDialog(dataset: string | DatasetModel[]) {
    if (this.widgetName !== 'Text Widget') {
      this.dialogRef = this.dialog.open(DataPreviewComponent, {
        width: '95vw',
        maxWidth: '95vw',
        height: '95%',
        data: {
          datasetId: dataset
        },
      });
      this.dialogRef.afterClosed().subscribe((result) => {
        this.dialogRef = null;
        this.cdr.detectChanges();
      });
    }

    if (this.widgetName == 'Text Widget') {
      this.dialogRefText = this.dialog.open(VisualizeTextdataComponent, {
        width: '75vw',
        maxWidth: '75vw',
        height: '75%',
        data: {
          datasetId: dataset,
        },
      });
    }
  }

  onExecuteWidgetClicked() {
    this.workflowDesignerService.setSaveTriggeredFrom("INTERACTIVE");
    this.workflowDesignerService.setTriggerSave(true);
  }

  async executeWidget() {
    try {
      let result: any;
      let projectId: string | undefined = this.configService.SelectedProjectId;
      if (!projectId) {
        return;
      }

      this.workflowDesignerService.setTriggerMonitorRun(true);
      result = await this.sessionApis.RunWidget(
        this.siteId,
        projectId,
        this.workflowCanvasService.SelectedWorkflowSession?._id!,
        this.widgetUrn,
      );

      if (result) {
        this.notificationComponent.display(
          'Widget is running. Switch to Run View to observe.',
          'success',
        );
      }
    } catch {
      if (this.sharedDataService.LastError) {
        this.notificationComponent.display(
          this.sharedDataService.LastError,
          'error',
        );
      } else {
        this.notificationComponent.display(
          'An unknown error occurred running the widget.',
          'error',
        );
      }
    }
  }

  getWidgetName() {
    return this.widgetName;
  }

  isSucceededWidget() {
    if (this.workflowCanvasService.WorkflowRunStatus) {
      let results = this.workflowCanvasService.WorkflowRunStatus?.widgets_status.find((t) => t.urn === this.widgetUrn);
      if (results && results.status) {
        if (results.status.toLocaleLowerCase() === 'succeeded') {
          return true;
        } else {
          return false;
        }
      } else {
        return false;
      }
    } else {
      return false;
    }
  }

  checkForTheRunStatus() {
    if (this.widgetName === 'Rescale') {
      const rescaleDatasetId = this.sharedDataService.getRescaleDatasetId(this.widgetUrn);
      if (this.checkIfWidgetIsRunning(this.widgetUrn) && rescaleDatasetId) {
        return true;
      }
    }

    if (this.widgetName === 'Rescale') {
      const workflowRunStatus = this.workflowCanvasService.WorkflowRunStatus;
      const rescaleWidget = this.workflowCanvasService.SelectedWorkflow?.widgets.find(
        widget => widget.type === 'RESCALE'
      );

      if (rescaleWidget) {
        const rescaleWidgetStatus = workflowRunStatus?.widgets_status.find(
          status => status.urn === rescaleWidget.urn && status.status === 'STOPPED'
        );
        // Check if the "Rescale" widget has results
        if (rescaleWidgetStatus && this.workflowCanvasService.getWidgetRunResults()?.length > 0) {
          return true;
        }
      }
    }

    if (this.tabularDirectWidgets.includes(this.widgetName)) {
      return true;
    } else {
      if (this.workflowCanvasService.viewingRunMode()) {
        if (
          this.isSucceededWidget() &&
          this.workflowCanvasService.getWidgetRunResults() &&
          this.workflowCanvasService.getWidgetRunResults().length > 0
        ) {
          return true;
        } else {
          return false;
        }
      } else {
        return false;
      }
    }
  }

  checkIfWidgetIsRunning(widgetUrn: string): boolean {
    const workflowRunStatus = this.workflowCanvasService.WorkflowRunStatus;

    if (workflowRunStatus) {
      const widgetStatus = workflowRunStatus.widgets_status.find(
        (widget) => widget.urn === widgetUrn
      );

      if (widgetStatus && widgetStatus.status?.toLowerCase() === 'running') {
        return true;
      }
    }
    return false;
  }


  checkWidgetStatus(widgetUrn: string): string | null {
    const workflowRunStatus = this.workflowCanvasService.WorkflowRunStatus;
    if (workflowRunStatus) {
      const widgetStatus = workflowRunStatus.widgets_status.find(
        (widget) => widget.urn === widgetUrn
      );
      if (widgetStatus && widgetStatus.status) {
        return widgetStatus.status.toLowerCase();
      }
    }
    return null;
  }

  isDialogOpen(): boolean {
    const isOpen = this.dialog.openDialogs.some(
      dialog => dialog.componentInstance instanceof DataPreviewComponent
    );
    return isOpen;
  }

  checkTheSelectedWidget(): boolean {
    const widgetControl: WidgetControl | undefined = this.workflowCanvasService.selectedWidgetControl;
    if (!widgetControl) {
      return false;
    }
    return this.MlWidgets.includes(widgetControl.Widget.type) ?? false;
  }

  datasetsLengthCheck() {
    if (this.TextWidgetconfig.source && this.TextWidgetconfig.source.length > 1) {
      return true;
    } else if (this.TextWidgetconfig.source.length == 1) {
      return false
    }else{
      return false
    }
  }

  multiTextFilesPreview(dataset_id: string) {
    this.dialogRefText = this.dialog.open(VisualizeTextdataComponent, {
      width: '75vw',
      maxWidth: '75vw',
      height: '75%',
      data: {
        datasetId: dataset_id,
      },
    });
  }
}
