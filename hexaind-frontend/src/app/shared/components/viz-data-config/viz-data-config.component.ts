import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { ButtonComponent } from '../button/button.component';
import { InputComponent } from '../input/input.component';
import {
  DashboardCellInfo,
  DataColumn,
  Filter,
  getRowLimitList,
  getVizTypeList,
  IdNameData,
  LabelBubbleColumn,
  LabelDataColumns,
  Metric,
  PageInfo,
  rowLimits,
  SortInfo,
  Viz,
  VizData,
  VizType,
} from '../models';

import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { SelectBubbleColumnsComponent } from '../select-bubble-columns/select-bubble-columns.component';
import { SelectColumnComponent } from '../select-column/select-column.component';
import { SelectConditionalCellStylesComponent } from '../select-conditional-cell-styles/select-conditional-cell-styles.component';
import { SelectDatasetComponent } from '../select-dataset/select-dataset.component';
import { SelectFilterColumnsComponent } from '../select-filter-columns/select-filter-columns.component';
import { SelectLabelDataColumnsComponent } from '../select-label-data-columns/select-label-data-columns.component';
import { SelectMetricsComponent } from '../select-metrics/select-metrics.component';
import { SelectSortColumnComponent } from '../select-sort-column/select-sort-column.component';
import { VizPanelComponent } from '../viz-panel/viz-panel.component';
import { CellStyleColumn } from './../models';

const getMetricColumnItems = (metrics: Metric[], dimentions: string[]) => {
  return metrics.length > 0
    ? [
        {
          id: 'group_by',
          name:
            dimentions.length > 0
              ? `group_by (${dimentions.join('-')})`
              : 'No Dimensions',
          type: 'string',
        },
        ...metrics.map((metric) => ({
          id: metric.label,
          name: metric.label,
          type: 'number',
        })),
      ]
    : [];
};

/**
 * Metrics also generate columns like `group_by` for x-axis label, metrics' label for the data columns. When it has metrics, the visualization fields(label, data, bubble...) can have only the metrics as the data columns. Metrics can't have the metric columns.
 * When adding a metric, the visualization fields can't have the columns.
 * ColumnItems should include all the metrics columns or ColumnItems should have only metrics columns for visualization fields.
 */

@Component({
  selector: 'mst-viz-data-config',
  templateUrl: './viz-data-config.component.html',
  styleUrls: ['./viz-data-config.component.scss'],
  standalone: true,
  imports: [
    InputComponent,
    CommonModule,
    SelectLabelDataColumnsComponent,
    SelectFilterColumnsComponent,
    SelectSortColumnComponent,
    ButtonComponent,
    VizPanelComponent,
    SelectBubbleColumnsComponent,
    SelectConditionalCellStylesComponent,
    SelectColumnComponent,
    SelectMetricsComponent,
    SelectDatasetComponent,
    MatDialogModule,
  ],
})
export class VizDataConfigComponent implements OnInit {
  constructor(public dialog: MatDialog) {}
  private _config!: Viz;
  private _data: VizData | undefined;
  private isLoaded = true;
  private selectedDataset!: IdNameData;
  vizType: VizType = 'table';
  labelDataColumns: LabelDataColumns = { label: '', dataColumns: [] };
  labelBubbleColumns: LabelBubbleColumn[] = [];
  cellStyleColumns: CellStyleColumn[] = [];
  columnItems: IdNameData[] = [];
  vizItems!: IdNameData[];
  filters: Filter[] = [];
  sorts: SortInfo[] = [];
  metrics: Metric[] = [];
  dimensions: string[] = [];
  dataset!: IdNameData;
  rowLimit: number = rowLimits[rowLimits.length - 1];
  nameDescription!: { name?: string; description?: string };
  rowLimitItems!: IdNameData[];
  metricColumnItems: IdNameData[] = [];
  dragItemType?: 'metric' | 'column';
  hasMetrics = false;

  @Input() hasMoreDatasets = false;
  @Input() sourceItems: IdNameData[] = [];
  @Input() datasetItems: IdNameData[] = [];
  @Input() selectedSourceId!: string;
  @Input() isFullscreen = false;
  @Input() rowIndex!: number;
  @Input() cellIndex!: number;
  @Input() set config(config: Viz) {
    //console.log('viz-data config', config);
    this._config = config;
    this.nameDescription = {
      name: config.name,
      description: config.description,
    };
    this.labelDataColumns = config?.config?.labelDataColumns || {
      label: '',
      dataColumns: [],
    };
    this.labelBubbleColumns = config.config?.labelBubbleColumns || [];
    this.cellStyleColumns = config.config?.cellStyleColumns || [];
    this.vizType = config.type || 'table';
    this.filters = config.query?.filters || [];
    this.sorts = config.query?.sorts || [];
    this.metrics = config.query?.metrics || [];
    this.rowLimit = config.query?.limit || 1000;
    this.dimensions = config.query?.groupby || [];
    this.dataset = config.query?.dataset || { id: '', name: '' };
    this.updateMetricColumnItems(true);
  }
  get config() {
    return this._config;
  }
  @Input() set data(data: VizData | undefined) {
    if (data) {
      this.columnItems = data.columns.map(({ name, type }: DataColumn) => ({
        id: name,
        name,
        type,
        style: 'padding-left:8px',
      }));
    }
    this._data = data;
  }
  get data() {
    return this._data;
  }

  @Output() change = new EventEmitter<Viz>();
  @Output() vizDataLoad = new EventEmitter<DashboardCellInfo>();
  @Output() cancel = new EventEmitter();
  @Output() fullscreen = new EventEmitter<boolean>();
  @Output() dataSourceChange = new EventEmitter<{
    item: IdNameData;
    index: number;
  }>();
  @Output() dataSourceLoad = new EventEmitter<{
    pageInfo: PageInfo;
    sourceId: any;
    searchTerm: string;
  }>();
  @Output() datasetChange = new EventEmitter<DashboardCellInfo>();
  @ViewChild('dialogTemplate') dialogTemplate!: TemplateRef<any>;
  ngOnInit(): void {
    this.vizItems = getVizTypeList();
    this.rowLimitItems = getRowLimitList();
  }
  private getConfig(): Viz {
    return {
      ...this.config,
      ...this.nameDescription,
      type: this.vizType,
      config: {
        ...this.config.config,
        labelDataColumns: this.labelDataColumns,
        labelBubbleColumns: this.labelBubbleColumns,
        cellStyleColumns: this.cellStyleColumns,
      },
      query: {
        ...this.config.query,
        dataset: this.dataset,
        filters: this.filters,
        sorts: this.sorts,
        limit: this.rowLimit,
        metrics: this.metrics,
        groupby: this.dimensions,
      },
    };
  }
  private updateMetricColumnItems(init = false) {
    // visualization fields can have only the metrics columns when it has metrics.
    this.metricColumnItems = getMetricColumnItems(
      this.metrics,
      this.dimensions,
    );
    if (this.metricColumnItems.length > 0) {
      // label data columns can have only metrics columns
      this.labelDataColumns = {
        label: this.metricColumnItems[0].id, // group_by column for x-axis label
        dataColumns: this.metricColumnItems.slice(1).map((item) => {
          // keep the existing information
          const dataColumn = this.labelDataColumns.dataColumns.find(
            (column) => column.field === item.id,
          );
          return dataColumn
            ? dataColumn
            : {
                field: item.id,
              };
        }),
      };
      // bubble columns can have only metrics columns
      this.labelBubbleColumns = this.labelBubbleColumns.filter((column) => {
        const { x, y, r } = column.bubbleColumn;
        const hasX = x && this.metricColumnItems.some((item) => item.id === x);
        const hasY = y && this.metricColumnItems.some((item) => item.id === y);
        const hasR = r && this.metricColumnItems.some((item) => item.id === r);
        if (!hasX && !hasY && !hasR) {
          return false;
        } else {
          if (!hasX) {
            column.bubbleColumn.x = '';
          }
          if (!hasY) {
            column.bubbleColumn.y = '';
          }
          if (!hasR) {
            column.bubbleColumn.r = '';
          }
          return true;
        }
      });
      this.hasMetrics = true;
      // cell style columns are ok since they are based on the filters. so, keep them.
    } else {
      if (!init) {
        this.labelDataColumns = { label: '', dataColumns: [] };
        this.labelBubbleColumns = [];
      }
      this.hasMetrics = false;
    }
  }
  onLabelDataColumnsChange(e: LabelDataColumns) {
    this.labelDataColumns = e;
  }
  onLabelBubbleColumnChange(e: LabelBubbleColumn[]) {
    this.labelBubbleColumns = e;
  }
  onCellStyleColumnChange(e: CellStyleColumn[]) {
    this.cellStyleColumns = e;
  }
  onFilterColumnChange(e: Filter[]) {
    this.filters = e;
  }
  onSortColumnChange(e: SortInfo[]) {
    this.sorts = e;
  }
  onMetricsChange(e: Metric[]) {
    this.metrics = e;
    this.updateMetricColumnItems();
  }
  onDimensionsChange(e: string[]) {
    this.dimensions = e;
    this.updateMetricColumnItems();
  }
  onVizTypeChange(value: VizType) {
    this.vizType = value;
  }
  onRowLimitChange(value: string) {
    this.rowLimit = +value;
  }
  onApply() {
    this.change.emit(this.getConfig());
  }
  onCancel() {
    this.cancel.emit();
  }
  onReloadClick() {
    this.config = this.getConfig();
  }
  onNameDescriptionChange(e: Event, type: 'name' | 'description') {
    this.nameDescription[type] = (e.target as HTMLInputElement).value;
  }
  onVizDataLoad(viz: Viz) {
    // skip the first loading since UI already have the data.
    if (this.isLoaded) {
      this.isLoaded = false;
    } else {
      this.vizDataLoad.emit({
        viz,
        rowIndex: this.rowIndex,
        cellIndex: this.cellIndex,
      });
    }
  }
  onFullscreen() {
    this.isFullscreen = !this.isFullscreen;
    this.fullscreen.emit(this.isFullscreen);
  }
  onItemDragStart(type: 'metric' | 'column') {
    this.dragItemType = type;
  }
  onItemDragEnd() {
    this.dragItemType = undefined;
  }
  onSelectDatasetClick() {
    this.dialog.open(this.dialogTemplate);
  }
  onDatasetSelect() {
    this.dialog.closeAll();
    this.datasetChange.emit({
      dataset: this.selectedDataset,
      viz: this.config,
      rowIndex: this.rowIndex,
      cellIndex: this.cellIndex,
    });
  }
  onDataSourceChange(e: { index: number; item: IdNameData }) {
    this.dataSourceChange.emit(e);
  }
  onDataSourceLoad(e: {
    pageInfo: PageInfo;
    sourceId: any;
    searchTerm: string;
  }) {
    this.dataSourceLoad.emit(e);
  }
  onDatasetItemClick(e: { item: IdNameData; index: number }) {
    this.selectedDataset = e.item;
  }
}
