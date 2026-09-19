import { Component, ViewChild } from '@angular/core';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import {
  InputOutputConfig,
  LoopStartWidgetConfig,
  Widget,
  WidgetType,
} from 'src/app/models/workflow-models';
import { SettingsComponent } from '../settings/settings.component';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';

@Component({
  selector: 'app-loop-start-config',
  templateUrl: './loop-start-config.component.html',
  styleUrls: ['./loop-start-config.component.less'],
})
export class LoopStartConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  public widgetControl: WidgetControl | undefined = undefined;

  data = {};
  config: LoopStartWidgetConfig | undefined = undefined;
  changeMade: boolean = false;
  selectedInputWidget: Widget | undefined = undefined;
  selectedInputWidgetInitiation: Widget | undefined;
  selectedInputWidgetContinuation: Widget | undefined;
  inputWidgets: Widget[] = [];
  outputName: string | undefined = undefined;
  setDefaultInput: boolean = false;
  changeInputMade: boolean = false;
  changeSettingMade: boolean = false;
  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    public sharedDataService: SharedDataService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.config = this.widgetControl.Widget.config as LoopStartWidgetConfig;
    this.config.widget_type = WidgetType.LOOP_START;
  }

  ngOnInit() {
    this.data = {
      type: 'Loop Start',
      description: this.widgetControl?.Widget.description,
      version: this.config?.version,
    };
    this.getInputWidgets();
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

      // Remove any widgets that dont have outputs.
      if (this.inputWidgets && this.inputWidgets.length > 0) {
        if (this.widgetControl.Widget.inputs.length > 0) {
          this.selectedInputWidgetInitiation = this.inputWidgets.find(
            (t) => t.urn === this.widgetControl?.Widget.inputs[0].urn,
          );
          this.selectedInputWidgetContinuation = this.inputWidgets[1];
        }else{
          if(this.inputWidgets.length === 1){
            this.setDefaultInput = true;
            this.setSelectedInputWidgetInitiation(this.inputWidgets[0])
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
    this.changeMade = false;
  }

  onCancel() {
    this.settingsComponent.RevertAppSetting();
    this.changeMade = false;
  }

  getSelectedInputWidget(): Widget | undefined {
    return this.selectedInputWidget;
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

  get getSelectedInputWidgetInitiation(): Widget | undefined {
    return this.selectedInputWidgetInitiation;
  }

  get getSelectedInputWidgetContinuation(): Widget | undefined {
    return this.selectedInputWidgetContinuation;
  }

  setSelectedInputWidgetInitiation(widget: Widget) {
    this.widgetControl!.Widget.inputs = []
    this.widgetControl!.Widget.outputs = []
    this.selectedInputWidgetInitiation = widget;
    let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
    inputOutputConfig.name = this.selectedInputWidgetInitiation.outputs[0].name;
    inputOutputConfig.urn = this.selectedInputWidgetInitiation.urn;
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

  setSelectedInputWidgetContinuation(widget: Widget) {
    this.selectedInputWidgetContinuation = widget;
    let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
    inputOutputConfig.name =
      this.selectedInputWidgetContinuation.outputs[0].name;
    inputOutputConfig.urn = this.selectedInputWidgetContinuation.urn;
    if (this.widgetControl) {
      this.widgetControl.Widget.inputs.length = 0;
      this.widgetControl.Widget.inputs.push(inputOutputConfig);
      this.widgetControl.Widget.outputs.push(inputOutputConfig);
      this.outputName = this.widgetControl.Widget.outputs[0]['name'];
    }
    this.changeInputMade = true;
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }
}
