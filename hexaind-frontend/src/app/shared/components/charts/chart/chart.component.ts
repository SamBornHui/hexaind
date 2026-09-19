import {
  AfterViewInit,
  Component,
  ElementRef,
  Input,
  ViewChild,
} from '@angular/core';
import { Chart } from 'chart.js';
import { ChartConfig } from '../../models';
import { renderChart } from '../chart-utils';

@Component({
  selector: 'mst-chart',
  templateUrl: './chart.component.html',
  styleUrls: ['./chart.component.scss'],
  standalone: true,
})
export class ChartComponent implements AfterViewInit {
  private chartObj!: Chart;
  private _config!: ChartConfig;
  renderChart(config: ChartConfig) {
    if (this.chart?.nativeElement && config && config.data && config.options) {
      if (this.chartObj) this.chartObj.destroy();
      this.chartObj = renderChart(
        this.chart.nativeElement,
        config.data,
        config.options,
        config.type,
      );
    }
  }

  @Input() set config(config: ChartConfig) {
    this._config = config;
    this.renderChart(config);
  }
  get config() {
    return this._config;
  }
  @ViewChild('chart') chart!: ElementRef;

  ngAfterViewInit() {
    this.renderChart(this.config);
  }
}
