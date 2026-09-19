import { Component, EventEmitter, Output } from '@angular/core';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { Widget } from 'src/app/models/workflow-models';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.less'],
})
export class SettingsComponent {
  @Output() notifyParent: EventEmitter<any> = new EventEmitter(); // Use 'any' or define a more specific type

  public widgetControl: WidgetControl | undefined = undefined;
  public color1: string = '#2889e9';
  public activeWidgetConfigData: Widget | undefined;

  widgetName: string | undefined = undefined;
  widgetDescription: string | undefined = undefined;
  useGPU: boolean | undefined = undefined;

  constructor(
    public sharedDataService: SharedDataService,
    public workflowCanvasService: WorkflowCanvasService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.activeWidgetConfigData = this.widgetControl?.Widget;

    this.widgetName = this.activeWidgetConfigData.name;
    this.widgetDescription = this.activeWidgetConfigData.description;
    this.useGPU = this.activeWidgetConfigData.use_gpu;
  }

  set Name(value: string) { 
    this.notifyParent.emit();
    this.widgetName = value;
    if (this.widgetName && this.activeWidgetConfigData) {
      this.activeWidgetConfigData.name = this.widgetName;
    }
  }

  get Name() {
    return this.widgetName ?? '';
  }

  set Description(value: string) {
    this.notifyParent.emit();
    this.widgetDescription = value;
    if (this.widgetDescription && this.activeWidgetConfigData) {
      this.activeWidgetConfigData.description = this.widgetDescription;
    }
  }

  get Description() {
    return this.widgetDescription ?? '';
  }

  set GPU(value: boolean) {
    this.notifyParent.emit();
    this.useGPU = value;
  }

  get GPU() {
    return this.useGPU ?? false;
  }

  // TODO - reimplement in a way that allows us to update the widget background image color.
  // set widgetColor(value: string) {
  //   if (!this.activeWidgetConfigData) return;
  //   if (this.activeWidgetConfigData)
  //     this.activeWidgetConfigData.client_tags["Color"] = value;
  // }

  // get widgetColor(): string | undefined {
  //   if (!this.activeWidgetConfigData) return;
  //   if (this.activeWidgetConfigData)
  //     return this.activeWidgetConfigData.client_tags["Color"];
  //   return undefined;
  // }

  public onEventLog(event: any) {
    if (!this.activeWidgetConfigData) return;
    if (this.activeWidgetConfigData)
      this.activeWidgetConfigData.client_tags['Color'] = event;
  }

  public SaveAppSettings() {
    if (!this.activeWidgetConfigData) {
      return;
    }
    if (this.widgetName) {
      this.activeWidgetConfigData.name = this.widgetName;
    }
    if (this.widgetDescription) {
      this.activeWidgetConfigData.description = this.widgetDescription;
    }
    if (this.useGPU) {
      this.activeWidgetConfigData.use_gpu = this.useGPU;
    }
  }

  public RevertAppSetting() {
    if (!this.activeWidgetConfigData) {
      return;
    }

    this.widgetName = this.activeWidgetConfigData.name;
    this.widgetDescription = this.activeWidgetConfigData.description;
    this.useGPU = this.activeWidgetConfigData.use_gpu;
  }
}
