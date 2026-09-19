import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  HostBinding,
  HostListener,
  Input,
  Output,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { ChartData, ChartType } from 'chart.js';
import { getCellStyleByFilter } from '../../utils/utils';
import { ButtonComponent } from '../button/button.component';
import { getChartConfig } from '../charts/chart-utils';
import { ChartComponent } from '../charts/chart/chart.component';
import { EmptyComponent } from '../empty/empty.component';
import { LoaderComponent } from '../loader/loader.component';
import {
  CellStyleColumn,
  Column,
  IdNameData,
  ResizeInfo,
  Viz,
  VizData,
  VizType,
} from '../models';
import { ResizerComponent } from '../resizer/resizer.component';
import { TableComponent } from '../table/table.component';

@Component({
  selector: 'mst-viz-panel',
  templateUrl: './viz-panel.component.html',
  styleUrls: ['./viz-panel.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ChartComponent,
    TableComponent,
    MatSlideToggleModule,
    EmptyComponent,
    LoaderComponent,
    ButtonComponent,
    ResizerComponent,
  ],
})
export class VizPanelComponent {
  chartConfig: {
    data?: ChartData;
    options?: any;
    type?: ChartType;
  } = {};
  columns: Column[] = [];
  loading = false;
  vizType: VizType = 'table';
  isFullscreen = false;
  private _config!: Viz;
  private _data!: VizData;

  private initData = (data: VizData) => {
    const viz = this.config;
    this.vizType = viz.type || 'table';
    if (data) {
      const cellStyleColumns = viz.config?.cellStyleColumns || [];
      const cellStyleColumnsMap = cellStyleColumns.reduce(
        (acc, item) => {
          const items = acc[item.filter.field] || [];
          items.push(item);
          acc[item.filter.field] = items;
          return acc;
        },
        {} as Record<string, any[]>,
      );
      //console.log('cellStyleColumnsMap', cellStyleColumnsMap);
      this.columns = data.columns.map(({ name, type }) => {
        const cellStyleColumnItems = cellStyleColumnsMap[name] || [];
        let styleItems: CellStyleColumn[] = [];
        let barItem: CellStyleColumn | undefined = undefined;
        cellStyleColumnItems.forEach((item) => {
          if (item.type === 'bar') {
            barItem = item;
          } else {
            styleItems.push(item);
          }
        });
        const styleFn = styleItems?.length
          ? (data: any, column: Column, rowIndex: number) => {
              return getCellStyleByFilter(
                data,
                column,
                rowIndex,
                cellStyleColumnItems,
              );
            }
          : undefined;
        return {
          name,
          field: name,
          styleFn,
          template: barItem ? this.barColumnTemplate : undefined,
          type,
          data: barItem,
        };
      });
    }
    this.chartConfig = getChartConfig(this.vizType, data, viz.config);
  };

  @Input() set config(config: Viz) {
    this._config = config;
    if (config.query) {
      this.loading = true;
      this.load.emit(config);
    }
  }
  get config() {
    return this._config;
  }
  @Input() set data(data: VizData | undefined) {
    // the dashboard loads data for every cell one by one, so we need to check if the data is undefined.
    //console.log('data set, end loading', data);
    if (this.loading && data) {
      // console.log('data set, end loading', data);
      this._data = data;
      this.initData(data);
      this.loading = false;
      this.loaded.emit({ config: this.config, data });
    }
  }
  get data() {
    return this._data;
  }
  @Input() editable = false;

  @Output()
  itemDrop = new EventEmitter<{ viz: Viz; dataset: IdNameData }>();
  @Output() edit = new EventEmitter<Viz>();
  @Output() delete = new EventEmitter<Viz>();
  @Output() load = new EventEmitter<Viz>();
  @Output() loaded = new EventEmitter<{ config: Viz; data?: VizData }>();
  @Output() resize = new EventEmitter<{ viz: Viz; resizeInfo: ResizeInfo }>();

  @HostBinding('class.mst-shared-fullscreen') get fullscreen() {
    return this.isFullscreen;
  }
  @HostListener('dragover', ['$event'])
  onDragStart(event: DragEvent) {
    event.preventDefault();
    this.el.nativeElement.classList.add('dragover');
  }
  @HostListener('dragleave', ['$event'])
  onDragEnd(event: DragEvent) {
    this.el.nativeElement.classList.remove('dragover');
  }
  @HostListener('drop', ['$event'])
  onDrop(event: DragEvent) {
    event.preventDefault();
    this.el.nativeElement.classList.remove('dragover');
    const item = JSON.parse(
      event.dataTransfer?.getData('application/json') || '{}',
    );
    this.itemDrop.emit({
      viz: this.config,
      dataset: item,
    });
  }

  @ViewChild('vizContainer') vizContainer!: ElementRef;
  @ViewChild('barColumnTemplate') barColumnTemplate!: TemplateRef<any>;

  onEdit() {
    this.edit.emit(this.config);
  }

  onDelete() {
    this.delete.emit(this.config);
  }

  onFullscreen() {
    this.isFullscreen = !this.isFullscreen;
  }

  onResize(e: ResizeInfo) {
    this.resize.emit({ viz: this.config, resizeInfo: e });
  }
  constructor(private el: ElementRef) {}
}
