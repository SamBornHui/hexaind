import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { InputComponent } from '../input/input.component';
import {
  getOptionChartTypeList,
  getPointStyleList,
  IdNameData,
  VizOptions,
  VizType,
} from '../models';

@Component({
  selector: 'mst-chart-options',
  templateUrl: './chart-options.component.html',
  styleUrls: ['./chart-options.component.scss'],
  standalone: true,
  imports: [InputComponent],
})
export class ChartOptionsComponent implements OnInit {
  pointStyleItems: IdNameData[] = [];
  chartTypeItems: IdNameData[] = [];
  @Input() baseVizType: VizType = 'line';
  @Input() options: VizOptions = {};
  @Output() change = new EventEmitter<VizOptions>();

  ngOnInit(): void {
    this.pointStyleItems = getPointStyleList();
    this.chartTypeItems = getOptionChartTypeList(this.baseVizType);
  }

  onChange(value: any, type: keyof VizOptions) {
    this.options[type] = value;
    this.change.emit(this.options);
  }
}
