import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { ChartOptionsDialogComponent } from '../chart-options-dialog/chart-options-dialog.component';
import { initVizOptions } from '../charts/chart-utils';
import { DropListComponent } from '../drop-list/drop-list.component';
import { ListComponent } from '../list/list.component';
import { IdNameData, LabelBubbleColumn, VizOptions } from '../models';

const initOptions = (items: LabelBubbleColumn[]) => {
  items.forEach((column, i) => {
    column.options = initVizOptions(column.options, i);
  });
  return items;
};

@Component({
  selector: 'mst-select-bubble-columns',
  templateUrl: './select-bubble-columns.component.html',
  styleUrls: ['./select-bubble-columns.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    DropListComponent,
    ListComponent,
    ChartOptionsDialogComponent,
    MatButtonModule,
  ],
})
export class SelectBubbleColumnsComponent {
  private _items: LabelBubbleColumn[] = [];
  optionsDialogOpen = false;
  xItems: IdNameData[] = [];
  yItems: IdNameData[] = [];
  labelItems: IdNameData[] = [];
  selectedItemInfo: { item: LabelBubbleColumn; index: number } | null = null;
  @Input() droppable = true;
  @Input() columnItems: IdNameData[] = [];
  @Input() set items(items: LabelBubbleColumn[]) {
    this._items = initOptions(items);
    this.updateDataItems(items);
  }
  get items() {
    return this._items;
  }
  @Output() change = new EventEmitter<LabelBubbleColumn[]>();

  private updateDataItems(items: LabelBubbleColumn[]) {
    const xItems: IdNameData[] = [];
    const yItems: IdNameData[] = [];
    const labelItems: IdNameData[] = [];
    items.forEach((item, i) => {
      const {
        label,
        bubbleColumn: { x, y, r },
        options: { backgroundColor, borderColor } = {},
      } = item;
      if (x) xItems.push({ id: x, name: `${i + 1}.x: ${x}` });
      if (y) yItems.push({ id: x, name: `${i + 1}.y: ${y}` });
      labelItems.push({
        id: label,
        name: label,
        style: {
          backgroundColor,
          borderColor,
        },
      });
    });
    this.xItems = xItems;
    this.yItems = yItems;
    this.labelItems = labelItems;
  }

  private applyItem() {
    this.updateDataItems(this.items);
    this.change.emit(this.items);
  }

  onDrop(id: string, type: 'x' | 'y') {
    let item: LabelBubbleColumn;
    let i: number;
    if (type === 'x') {
      i = this.xItems.length;
      item = this.items[i] || { bubbleColumn: { x: '' } };
      item.bubbleColumn.x = id;
    } else {
      i = this.yItems.length;
      item = this.items[i] || { bubbleColumn: { y: '' } };
      item.bubbleColumn.y = id;
    }
    if (item.bubbleColumn.x && item.bubbleColumn.y && !item.label) {
      item.label = `x:${item.bubbleColumn.x}/y:${item.bubbleColumn.y}`;
      item.options = initVizOptions(item.options, i);
    }
    this.items[i] = item;
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
  onLabelListIconClick({
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
      this.selectedItemInfo = { item: this.items[index], index };
      this.optionsDialogOpen = true;
    }
  }

  onOptionsSave(options: VizOptions) {
    this.items[this.selectedItemInfo!.index].options = options;
    this.applyItem();
  }
  onOptionsDialogClose() {
    this.optionsDialogOpen = false;
  }
}
