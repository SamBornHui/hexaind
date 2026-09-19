import { Component, EventEmitter, Output } from '@angular/core';
import { ApiService } from 'src/app/services/api.service';
import {
  ConfigService,
  WorkflowCanvasService,
} from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { Subscription } from 'rxjs';
import { WidgetControl } from '../../widget-control/widget-control';
import {
  DecisionWidgetConfig,
  FilterOperator,
  WidgetType,
} from 'src/app/models/workflow-models';
import { ColorPickerService, Cmyk } from 'ngx-color-picker';
import { Widget } from 'src/app/models/workflow-models';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';

@Component({
  selector: 'app-decision-config',
  templateUrl: './decision-config.component.html',
  styleUrls: ['./decision-config.component.less'],
})
export class DecisionConfigComponent {
  config: DecisionWidgetConfig | undefined = undefined;
  public widgetControl: WidgetControl | undefined = undefined;
  filterOperator = Object.values(FilterOperator).filter(
    (value) => typeof value === 'string',
  );
  data = {};

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    public sharedDataService: SharedDataService,
    private cpService: ColorPickerService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.config = this.widgetControl.Widget.config as DecisionWidgetConfig;
    this.config.widget_type = WidgetType.DECISION;
  }

  ngOnInit() {
    this.initializeInformation();
  }

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }

  initializeInformation() {
    this.data = {
      type: this.widgetControl!.Widget.type,
      description: this.widgetControl!.Widget.description,
      version: this.config?.version,
    };
  }

  get version(): string | undefined {
    if (!this.config) {
      return undefined;
    }
    return this.config.version;
  }
  get type(): string | undefined {
    if (!this.widgetControl) {
      return undefined;
    }
    return this.widgetControl!.Widget.type;
  }
  get description(): string | undefined {
    if (!this.widgetControl) {
      return undefined;
    }
    return this.widgetControl!.Widget.description;
  }
  get field(): string | undefined {
    if (!this.config) {
      return undefined;
    }

    return this.config.criteria?.field;
  }

  set field(value: string) {
    if (!this.config) {
      return;
    }

    if (this.config.criteria) {
      this.config.criteria.field = value;
    }
  }

  get value(): string | undefined {
    if (!this.config) {
      return undefined;
    }

    return this.config.criteria?.value;
  }

  set value(value: string) {
    if (!this.config) {
      return;
    }

    if (this.config.criteria) {
      this.config.criteria.value = value;
    }
  }

  getOperator() {
    return this.config?.criteria?.operator;
  }

  setOperator(value: FilterOperator) {
    if (this.config) {
      if (this.config.criteria) {
        this.config.criteria.operator = value;
      }
    }
  }

  getDataCsvWidgetConfig(): Widget | null {
    let dataCsvActivityConfig: Widget = this.widgetControl?.Widget as Widget;

    return dataCsvActivityConfig;
  }

  /********************************************************************************************/

  get CsvName(): string | undefined {
    let dataCsvActivityConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvActivityConfig) return;

    if (dataCsvActivityConfig) {
      let csvDatasetConfiguration = dataCsvActivityConfig;
      if (csvDatasetConfiguration) return csvDatasetConfiguration.name;
    }
    return undefined;
  }

  set CsvName(value: string) {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration) csvDatasetConfiguration.name = value;
    }
  }

  get CsvDescription(): string | undefined {
    let dataCsvActivityConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvActivityConfig) return;

    if (dataCsvActivityConfig) {
      let csvDatasetConfiguration = dataCsvActivityConfig;
      if (csvDatasetConfiguration) return csvDatasetConfiguration.description;
    }
    return undefined;
  }

  set CsvDescription(value: string) {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration) csvDatasetConfiguration.description = value;
    }
  }

  get CsvRetryCount(): number | undefined {
    let dataCsvActivityConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvActivityConfig) return;

    if (dataCsvActivityConfig) {
      let csvDatasetConfiguration = dataCsvActivityConfig;
      if (csvDatasetConfiguration) return csvDatasetConfiguration.retry_count;
    }
    return undefined;
  }

  set CsvRetryCount(value: number) {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration) csvDatasetConfiguration.retry_count = value;
    }
  }

  get CsvGpu(): boolean | undefined {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration) return csvDatasetConfiguration.use_gpu;
    }
    return undefined;
  }

  set CsvGpu(value: boolean) {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration) csvDatasetConfiguration.use_gpu = value;
    }
  }

  set CsvColor(value: string) {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration)
        csvDatasetConfiguration.client_tags['Color'] = value;
    }
  }

  get CsvColor(): string | undefined {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;
    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration)
        return csvDatasetConfiguration.client_tags['Color'];
    }
    return undefined;
  }

  public onEventLog(event: string, data: any): void {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration)
        csvDatasetConfiguration.client_tags['Color'] = data;
    }
  }

  public onChangeColorCmyk(color: string): Cmyk {
    const hsva = this.cpService.stringToHsva(color);

    if (hsva) {
      const rgba = this.cpService.hsvaToRgba(hsva);

      return this.cpService.rgbaToCmyk(rgba);
    }

    return new Cmyk(0, 0, 0, 0);
  }

  public onChangeColorHex8(color: string): string {
    const hsva = this.cpService.stringToHsva(color, true);

    if (hsva) {
      return this.cpService.outputFormat(hsva, 'rgba', null);
    }

    return '';
  }

  getWidgetUrn(): string | undefined {
    if (this.widgetControl) {
      return this.widgetControl.Widget.urn;
    }
    return undefined;
  }
}
