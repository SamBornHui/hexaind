import { Component, ViewChild } from '@angular/core';
import { WidgetControl } from '../../widget-control/widget-control';
import {
  CustomCodeTerminationCriteriaConfig,
  InputOutputConfig,
  LoopEndWidgetConfig,
  MOBOWidgetConfig,
  OnLoopTerminationCriteriaConfig,
  TerminationCriteria,
  Widget,
  WidgetType,
} from 'src/app/models/workflow-models';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ShowModuleDialogComponent } from 'src/app/dialogs/show-module-dialog/show-module-dialog.component';
import { Module } from 'src/app/models/module-models';
import { MatDialog } from '@angular/material/dialog';
import { SettingsComponent } from '../settings/settings.component';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';

@Component({
  selector: 'app-loop-end-config',
  templateUrl: './loop-end-config.component.html',
  styleUrls: ['./loop-end-config.component.less'],
})
export class LoopEndConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  public widgetControl: WidgetControl | undefined = undefined;
  TerminationCriteria = TerminationCriteria;
  terminationOptions = Object.values(TerminationCriteria).filter(
    (value) => typeof value === 'string',
  );
  data = {};

  changeMade: boolean = false;
  config: LoopEndWidgetConfig | undefined = undefined;
  configCache: LoopEndWidgetConfig | undefined = undefined;
  selectedInputWidget: Widget | undefined = undefined;
  selectedOnLoopWidget: Widget | undefined = undefined;
  selectedOnTerminateWidget: Widget | undefined = undefined;
  inputWidgets: Widget[] = [];
  outputWidgets: Widget[] = [];
  outputName: string | undefined = undefined;
  selectedModule: Module | undefined = undefined;
  setDefaultInput: boolean = false;
  changeInputMade: boolean = false;
  changeSettingMade: boolean = false;

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    public dialog: MatDialog,
    public sharedDataService: SharedDataService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.config = this.widgetControl.Widget.config as LoopEndWidgetConfig;
    this.config.widget_type = WidgetType.LOOP_END;
    this.configCache = JSON.parse(JSON.stringify(this.config));
  }

  ngOnInit() {
    this.data = {
      type: 'Loop End',
      description: this.widgetControl?.Widget.description,
      version: this.config?.version,
    };
    this.getInputWidgets();
    this.getOutputWidgets();
  }

  getInputWidgets() {
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.inputWidgets = this.workflowCanvasService.findConnectedWidgets(
        this.widgetControl.Widget.urn,
      );

      if (this.inputWidgets && this.inputWidgets.length > 0) {
        if (this.widgetControl.Widget.inputs.length > 0) {
          this.selectedInputWidget = this.inputWidgets.find(
            (t) => t.urn === this.widgetControl?.Widget.inputs[0].urn,
          );
        }else{
          if(this.inputWidgets.length === 1){
            this.setDefaultInput = true;
            this.setSelectedInputWidget(this.inputWidgets[0]);
          }
        }
      }else{
        this.widgetControl!.Widget.outputs = []
      }
      if (this.widgetControl.Widget.outputs.length) {
        this.outputName = this.widgetControl.Widget.outputs[0].name;
      }
    }
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  getOutputWidgets() {
    if (
      this.widgetControl &&
      this.widgetControl.Widget &&
      this.widgetControl.Widget.urn
    ) {
      this.widgetControl.Widget.on_success.forEach((urn) => {
        if (urn) {
          let widget: Widget | undefined =
            this.workflowCanvasService.findWidgetByUrn(urn);
          if (widget) {
            this.outputWidgets.push(widget);
          }
          if (this.configCache?.on_termination[0] === urn) {
            this.selectedOnTerminateWidget = widget;
          } else if (this.config?.on_loop[0] === urn) {
            this.selectedOnLoopWidget = widget;
          }
        }
      });
    }
  }

  getTerminationCriteria() {
    return this.configCache?.termination_criteria;
  }

  setTerminationCriteria(value: TerminationCriteria) {
    if (this.configCache) {
      this.changeMade = true;
      this.configCache.termination_criteria = value;
      if (
        this.configCache.termination_criteria ===
        TerminationCriteria.ON_LOOP_COUNT
      ) {
        this.configCache.loop_end_config =
          new OnLoopTerminationCriteriaConfig();
        (
          this.configCache.loop_end_config as OnLoopTerminationCriteriaConfig
        ).loop_count = 1;
      } else {
        this.configCache.loop_end_config =
          new CustomCodeTerminationCriteriaConfig();
      }
    }
  }

  getLoopCount() {
    if (this.config) {
      let loopEndConfig: OnLoopTerminationCriteriaConfig = this.config.loop_end_config as OnLoopTerminationCriteriaConfig;
      if (this.inputWidgets && this.inputWidgets.length > 0 && this.inputWidgets[0].config) {
        loopEndConfig.loop_count = (Number((this.inputWidgets[0].config as MOBOWidgetConfig).num_iterations) + 1)
        return loopEndConfig.loop_count;
      }
    }
    return 0;
  }

  setLoopCount(value: number) {
    if (this.configCache) {
      let loopEndConfig: OnLoopTerminationCriteriaConfig = this.configCache
        .loop_end_config as OnLoopTerminationCriteriaConfig;
      loopEndConfig.loop_count = value;
      this.changeMade = true;
    }
  }

  setModule(module: Module) {
    this.selectedModule = module;
    if (this.configCache) {
      (
        this.configCache.loop_end_config as CustomCodeTerminationCriteriaConfig
      ).module_id = module._id ?? '';
    }
  }

  showModulesDialog() {
    const dialogRef = this.dialog.open(ShowModuleDialogComponent, {
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.changeMade = true;
        this.setModule(result.module);
        this.selectedModule = result.module;
      }
    });
  }

  onAppSettingsUpdated() {
    this.changeSettingMade = true;
  }


  onInputSave() {
    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.changeInputMade = false;
    this.setDefaultInput = false;
  }


  onInputCancel() {
    this.settingsComponent.RevertAppSetting();
    this.changeMade = false;
  }



  onSettingSave() {
    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.settingsComponent.SaveAppSettings();
    this.changeSettingMade = false;
  }
  onSettingCancel() {
    this.settingsComponent.RevertAppSetting();
    this.changeSettingMade = false;
  }

  onSave() {
    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.settingsComponent.SaveAppSettings();

    if (!this.widgetControl) {
      return;
    }

    if (this.configCache) {
      this.widgetControl.Widget.config = this.configCache;
      this.config = this.widgetControl?.Widget.config;
      this.configCache = JSON.parse(JSON.stringify(this.config));
    }
    this.setDefaultInput = false;
    this.changeMade = false;
  }

  onCancel() {
    this.settingsComponent.RevertAppSetting();
    this.configCache = JSON.parse(JSON.stringify(this.config));
    this.changeMade = false;
  }

  getSelectedOnLoopWidget(): Widget | undefined {
    return this.selectedOnLoopWidget;
  }

  setSelectedOnLoopWidget(widget: Widget) {
    this.selectedOnLoopWidget = widget;

    if (this.configCache && widget.urn) {
      this.configCache.on_loop.length = 0;
      this.configCache.on_loop.push(widget.urn);
    }

    this.changeMade = true;
  }

  getSelectedOnTerminateWidget(): Widget | undefined {
    return this.selectedOnTerminateWidget;
  }

  setSelectedOnTerminateWidget(widget: Widget) {
    this.selectedOnTerminateWidget = widget;
    if (this.configCache && widget.urn) {
      this.configCache.on_termination.length = 0;
      this.configCache.on_termination.push(widget.urn);
    }
    this.changeMade = true;
  }

  getSelectedInputWidget(): Widget | undefined {
    return this.selectedInputWidget;
  }

  setSelectedInputWidget(widget: Widget) {
    this.widgetControl!.Widget.inputs = []
    this.widgetControl!.Widget.outputs = []
    this.selectedInputWidget = widget;
    let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
    inputOutputConfig.name = this.selectedInputWidget.outputs[0].name;
    inputOutputConfig.urn = this.selectedInputWidget.outputs[0].urn;
    if (this.widgetControl) {
      this.widgetControl.Widget.inputs.length = 0;
      this.widgetControl.Widget.inputs.push(inputOutputConfig);
      this.widgetControl.Widget.outputs.push(inputOutputConfig);
      this.outputName = this.widgetControl.Widget.outputs[0]['name'];
    }
    this.changeInputMade = true;
    if(this.setDefaultInput){
      this.onInputSave();
    }
  }

  getWidgetName(widget: Widget): string {
    return widget.name;
  }

  getWidgetOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let outputConfig: InputOutputConfig = widget.outputs[0];
      return outputConfig.name!;
    }

    return 'Not Set';
  }

  get widgetOutput(): string | undefined {
    return this.outputName;
  }

  set widgetOutput(value: string | undefined) {
    this.outputName = value;
    this.changeMade = true;
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }
}
