import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  Input,
  Output,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { SQLNamespace } from '@codemirror/lang-sql';
import { ButtonComponent } from '../button/button.component';
import { DropListComponent } from '../drop-list/drop-list.component';
import { EditorComponent } from '../editor/editor.component';
import { InputComponent } from '../input/input.component';
import { getAggregateTypeList, IdNameData, Metric } from '../models';
import { SelectDimensionsComponent } from '../select-dimensions/select-dimensions.component';
import { TabsComponent } from '../tabs/tabs.component';
import { ExpressionType } from './../models';

const updateMetricLabel = (item: Metric) => {
  if (item.expressionType === 'SQL') {
    item.label = item.sql?.trim().split(' ')[0] || 'SQL';
  } else {
    if (item.field && item.aggregateType) {
      item.label = `${item.aggregateType}(${item.field})`;
    } else {
      item.label = item.field || '';
    }
  }
  return item;
};

@Component({
  selector: 'mst-select-metrics',
  templateUrl: './select-metrics.component.html',
  styleUrls: ['./select-metrics.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    ButtonComponent,
    DropListComponent,
    TabsComponent,
    InputComponent,
    EditorComponent,
    SelectDimensionsComponent,
  ],
})
export class SelectMetricsComponent {
  private _items: Metric[] = [];
  item!: { index: number; metric: Metric; column: string };
  metricItems: IdNameData[] = [];
  aggregateTypeItems: IdNameData[] = getAggregateTypeList();
  _columnItems: IdNameData[] = [];
  schema: SQLNamespace | undefined;

  @ViewChild('dialogTemplate') dialogTemplate!: TemplateRef<any>;
  @Input() droppable = true;
  @Input() datasetId = '';
  @Input() set columnItems(columnItems: IdNameData[]) {
    const schema: any = {};
    schema[this.datasetId || 'table'] = columnItems.map((item) => item.name);
    this.schema = schema;
    this._columnItems = columnItems;
  }
  get columnItems() {
    return this._columnItems;
  }
  @Input() set items(items: Metric[]) {
    this._items = items;
    this.updateDataItems(items);
  }
  get items() {
    return this._items;
  }
  @Input() dimensions: string[] = [];
  @Output() change = new EventEmitter<Metric[]>();
  @Output() dimensionsChange = new EventEmitter<string[]>();

  constructor(public dialog: MatDialog) {}

  private updateDataItems(items: Metric[]) {
    const metricItems: IdNameData[] = [];
    items.forEach((data, i) => {
      const { label } = data;
      metricItems.push({
        id: String(i),
        name: label,
        data,
      });
    });
    this.metricItems = metricItems;
  }

  private openDialog(column: string, index?: number) {
    if (index == null) {
      const item: Metric = {
        field: column,
        expressionType: 'SIMPLE',
        label: '',
        aggregateType: 'SUM',
        sql: `(${column})`,
        format: '',
      };
      this.items.push(item);
      this.item = { index: this.items.length - 1, metric: item, column };
      this.updateDataItems(this.items);
    } else {
      const metric = this.items[index];
      this.item = {
        index,
        metric,
        column,
      };
    }
    this.dialog.open(this.dialogTemplate);
  }
  private applyItem() {
    this.updateDataItems(this.items);
    this.change.emit(this.items);
  }

  onMetricChange(
    value: any,
    type: 'field' | 'aggregateType' | 'sql' | 'expressionType',
  ) {
    if (type === 'expressionType') {
      const expressionType: ExpressionType = value === 0 ? 'SIMPLE' : 'SQL';
      this.item.metric.expressionType = expressionType;
    } else {
      this.item.metric[type] = value;
    }
  }
  onDrop(id: string) {
    this.openDialog(id);
  }
  onIconClick({
    item,
    index,
    name,
  }: {
    item: IdNameData;
    index: number;
    name: string;
  }) {
    if (name === 'delete') {
      this.items.splice(index, 1);
      this.applyItem();
    } else {
      this.openDialog(item['data'].field, index);
    }
  }

  onDialogAction() {
    const { index, metric } = this.item;
    this.items[index] = updateMetricLabel(metric);
    this.dialog.closeAll();
    this.applyItem();
  }
  onLabelChange(e: Event, i: number) {
    e.stopPropagation();
    const value = (e.target as HTMLInputElement).value;
    const item = this.items[i] || {};
    item.label = value;
    this.items[i] = item;
    this.applyItem();
  }
  onDimensionsChange(e: string[]) {
    this.dimensionsChange.emit(e);
  }
}
