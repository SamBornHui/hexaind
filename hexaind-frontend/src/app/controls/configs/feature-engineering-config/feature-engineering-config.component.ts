import { Component, ViewChild } from '@angular/core';
import {
  InputOutputConfig,
  Widget,
  WidgetType,
} from 'src/app/models/workflow-models';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { WidgetControl } from '../../widget-control/widget-control';
import { Subscription } from 'rxjs';
import { FeatureEngineeringWidgetConfig } from 'src/app/models/workflow-models';
import { SettingsComponent } from '../settings/settings.component';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';

@Component({
  selector: 'app-feature-engineering-config',
  templateUrl: './feature-engineering-config.component.html',
  styleUrls: ['./feature-engineering-config.component.less'],
})
export class FeatureEngineeringConfigComponent {
  @ViewChild(SettingsComponent) settingsComponent!: SettingsComponent;
  widgetControl: WidgetControl | undefined = undefined;
  changeMade: boolean = false;
  config: FeatureEngineeringWidgetConfig | undefined = undefined;
  configCache: FeatureEngineeringWidgetConfig | undefined = undefined;
  outputName: string | undefined = undefined;
  inputWidgets: Widget[] = [];
  selectedInputWidget: Widget | undefined = undefined;
  selectAll = false;
  arrayElement = [
    {
      checked: false,
      feature: 'Feature_1',
      type: 'Numeric',
      dropdowns: ['None'],
      std: 'Resultant transformation',
      selectedOption: null,
    },
    {
      checked: false,
      feature: 'Feature_2',
      type: 'String',
      dropdowns: ['None'],
      std: 'Resultant transformation',
      selectedOption: null,
      dropdownValues: Array(3).fill(null),
    },
  ];
  dropdownValue = '';
  dataSourceOptions: any[] = [];
  selectedOption = '';
  data = {
    type: 'Feature Engineering Widget',
    description:
      'The Feature Engineering Widget empowers users to enhance data quality and analysis by providing a streamlined platform for creating, modifying, and optimizing features within datasets, facilitating robust data-driven insights.',
    version: '1.0',
  };

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    public sharedDataService: SharedDataService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.config = this.widgetControl.Widget
      .config as FeatureEngineeringWidgetConfig;
    this.config.widget_type = WidgetType.Feature_Engineering;
    this.configCache = JSON.parse(JSON.stringify(this.config));
    this.outputName = this.widgetControl.Widget.outputs[0].name;
  }

  ngOnInit() {
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
        this.inputWidgets = this.inputWidgets.filter(
          (widget) => widget.outputs.length > 0,
        );

        if (this.widgetControl.Widget.inputs.length > 0) {
          this.selectedInputWidget = this.inputWidgets.find(
            (t) => t.urn === this.widgetControl?.Widget.inputs[0].urn,
          );
        }
      }
    }
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  addDropdown(element: any, index: number): void {
    const newDropdown = { type: 'None' };
    element.dropdowns.splice(index + 1, 0, newDropdown);
  }

  removeDropdown(element: any, index: number): void {
    if (element.dropdowns.length > 1) {
      element.dropdowns.splice(index, 1);
    }
  }

  shouldShowIcons(type: string, index: number): boolean {
    return type !== 'None';
  }

  getDropdownOptions(elementType: any): string[] {
    return elementType === 'Numeric'
      ? ['Min', 'Max', 'Mean', 'Standard Deviation']
      : ['Top', 'Min'];
  }

  onReplaceNullDropdownChanged() {
    this.changeMade = true;
  }

  onTransformationDropdownChanged() {
    this.changeMade = true;
  }

  toggleCheckAll() {
    this.changeMade = true;
    for (const element of this.arrayElement) {
      element.checked = this.selectAll;
    }
  }

  getSelectedInputWidget(): Widget | undefined {
    return this.selectedInputWidget;
  }

  setSelectedInputWidget(widget: Widget) {
    this.selectedInputWidget = widget;
    let inputOutputConfig: InputOutputConfig = new InputOutputConfig();
    inputOutputConfig.name = this.selectedInputWidget.outputs[0].name;
    inputOutputConfig.urn = this.selectedInputWidget.urn;
    if (this.widgetControl) {
      this.changeMade = true;
      this.widgetControl.Widget.inputs.length = 0;
      this.widgetControl.Widget.inputs.push(inputOutputConfig);
    }
  }

  getTransformationDropdown(elementType: any): string[] {
    return elementType === 'Numeric'
      ? [
          'None',
          'Binarize',
          'Bucketizer',
          'Normalizer',
          'Min Max Scaler',
          'Quantile Discretizer',
          'Polynomial Expansion',
          'Discrete Cosine Tranform',
        ]
      : ['None', 'String Indexer', 'One Hot Encoding', 'Convert to Data'];
  }

  getWidgetOutputName(widget: Widget): string {
    if (widget.outputs.length > 0) {
      let outputConfig: InputOutputConfig = widget.outputs[0];
      return outputConfig.name!;
    }

    return 'Not Set';
  }

  getInputWidget(index: number): Widget | undefined {
    if (!this.configCache) {
      return undefined;
    }

    let urn: string | undefined = this.configCache.inputs[index].input_urn;
    if (urn) {
      return this.inputWidgets.find((t) => t.urn === urn);
    }

    return undefined;
  }

  getDataCsvWidgetConfig(): Widget | null {
    let dataCsvActivityConfig: Widget = this.widgetControl?.Widget as Widget;

    return dataCsvActivityConfig;
  }

  onAppSettingsUpdated() {
    this.changeMade = true;
  }

  onSave() {
    this.workflowCanvasService.changeMadeToWorkflow = true;
    this.settingsComponent.SaveAppSettings();
    if (this.widgetControl && this.configCache) {
      this.widgetControl.Widget.config = this.configCache;
      this.config = this.widgetControl?.Widget.config;
      this.configCache = JSON.parse(JSON.stringify(this.config));
    }
    if (!this.widgetControl) {
      return;
    }

    if (this.outputName) {
      this.outputName = this.outputName.trim();
      if (
        this.widgetControl.Widget.outputs &&
        this.widgetControl.Widget.outputs.length > 0
      ) {
        this.widgetControl.Widget.outputs[0].name = this.outputName;
      }
    }

    this.changeMade = false;
  }

  onCancel() {
    this.settingsComponent.RevertAppSetting();
    // Deep clone to prevent updates from modifying original
    this.configCache = JSON.parse(JSON.stringify(this.config));
    if (this.widgetControl) {
      this.outputName = this.widgetControl.Widget.outputs[0].name;
    }
    this.changeMade = false;
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }
}
