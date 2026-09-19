import { Component, EventEmitter, Output } from '@angular/core';
import { Connector, ConnectorType } from 'src/app/models/connector-models';
import {
  BigQueryDatasetConfig,
  BigQueryDatasetConfiguration,
  BigQueryDatasetTableConfig,
  BigQueryDatasetType,
  DataCopyWidgetConfig,
  Widget,
  WidgetType,
  Sink,
  LocalFileConfiguration,
  PythonWidgetConfig,
} from 'src/app/models/workflow-models';
import { ApiService } from 'src/app/services/api.service';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { Subscription } from 'rxjs';
import { WidgetControl } from '../../widget-control/widget-control';
import { ColorPickerService, Cmyk } from 'ngx-color-picker';
import { SharedDataService } from 'src/app/services/shared services/shared-data.service';

@Component({
  selector: 'app-python-config',
  templateUrl: './python-config.component.html',
  styleUrls: ['./python-config.component.less'],
})
export class PythonConfigComponent {
  files: any;
  config: PythonWidgetConfig | undefined = undefined;
  public widgetControl: WidgetControl | undefined = undefined;
  data = {};

  constructor(
    public workflowCanvasService: WorkflowCanvasService,
    private cpService: ColorPickerService,
    public sharedDataService: SharedDataService,
  ) {
    if (!this.workflowCanvasService.selectedWidgetControl) {
      return;
    }
    this.widgetControl = this.workflowCanvasService.selectedWidgetControl;
    this.config = this.widgetControl.Widget.config as PythonWidgetConfig;
  }

  ngOnInit() {
    this.data = {
      type: this.widgetControl?.Widget.type,
      description: this.widgetControl?.Widget.description,
      version: this.config?.version,
    };
  }

  getDataCsvWidgetConfig(): Widget | null {
    let dataCsvActivityConfig: Widget = this.widgetControl?.Widget as Widget;

    return dataCsvActivityConfig;
  }

  /********************************************************************************************/

  get DefaultName(): string | undefined {
    let dataCsvActivityConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvActivityConfig) return;

    if (dataCsvActivityConfig) {
      let csvDatasetConfiguration = dataCsvActivityConfig;
      if (csvDatasetConfiguration) return csvDatasetConfiguration.name;
    }
    return undefined;
  }

  set DefaultName(value: string) {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration) csvDatasetConfiguration.name = value;
    }
  }

  get DefaultDescription(): string | undefined {
    let dataCsvActivityConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvActivityConfig) return;

    if (dataCsvActivityConfig) {
      let csvDatasetConfiguration = dataCsvActivityConfig;
      if (csvDatasetConfiguration) return csvDatasetConfiguration.description;
    }
    return undefined;
  }

  set DefaultDescription(value: string) {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration) csvDatasetConfiguration.description = value;
    }
  }

  get DefaultRetryCount(): number | undefined {
    let dataCsvActivityConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvActivityConfig) return;

    if (dataCsvActivityConfig) {
      let csvDatasetConfiguration = dataCsvActivityConfig;
      if (csvDatasetConfiguration) return csvDatasetConfiguration.retry_count;
    }
    return undefined;
  }

  set DefaultRetryCount(value: number) {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration) csvDatasetConfiguration.retry_count = value;
    }
  }

  get DefaultGpu(): boolean | undefined {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration) return csvDatasetConfiguration.use_gpu;
    }
    return undefined;
  }

  set DefaultGpu(value: boolean) {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration) csvDatasetConfiguration.use_gpu = value;
    }
  }

  set DefaultColor(value: string) {
    let dataCsvWidgetConfig: Widget | null = this.getDataCsvWidgetConfig();

    if (!dataCsvWidgetConfig) return;

    if (dataCsvWidgetConfig) {
      let csvDatasetConfiguration = dataCsvWidgetConfig;
      if (csvDatasetConfiguration)
        csvDatasetConfiguration.client_tags['Color'] = value;
    }
  }

  get DefaultColor(): string | undefined {
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

  get defaultTabIndex(): number {
    return this.workflowCanvasService.IsViewingRunMode ? 5 : 1;
  }
}
