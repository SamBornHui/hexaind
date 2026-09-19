import { Component, Input, OnChanges, SimpleChanges, OnInit } from '@angular/core';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';

@Component({
  selector: 'app-configs-information',
  templateUrl: './configs-information.component.html',
  styleUrls: ['./configs-information.component.less'],
})
export class ConfigsInformationComponent implements OnInit, OnChanges {
  @Input() widgetData: any;
  @Input() widgetConfig: any;  // This receives getWidgetDetails

  public widgetControl: WidgetControl | undefined = undefined;
  public data: any = {};

  constructor(private editWorkflowService: WorkflowCanvasService) {}

  // ngOnInit runs only once when the component is initialized
  ngOnInit(): void {

    if (this.editWorkflowService.selectedWidgetControl) {
      this.widgetControl = this.editWorkflowService.selectedWidgetControl;
    }
  }

  // ngOnChanges runs every time an input property changes
  ngOnChanges(changes: SimpleChanges): void {
    if (changes['widgetConfig']) {
      this.widgetConfig = this.widgetConfig;
      //console.log(this.widgetConfig, 'widgetConfig after change');  // Should now display the updated value
    }
  }

  // Method to get the widget type safely
  widgetType(): string | undefined {
    return this.widgetControl?.Widget?.type;
  }

  // Method to check if the widget is a custom code widget
  isCustomCodeWidget(): boolean {
    return this.widgetControl?.Widget?.type === 'CUSTOM_CODE';
  }
}
