import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ChartOptionsDialogComponent } from '../chart-options-dialog/chart-options-dialog.component';
import { initVizOptions } from '../charts/chart-utils';
import { DropListComponent } from '../drop-list/drop-list.component';
import {
  IdNameData,
  LabelDataColumns,
  VizDataColumn,
  VizOptions,
} from '../models';

const initOptions = (item: LabelDataColumns) => {
  item.dataColumns.forEach((column, i) => {
    column.options = initVizOptions(column.options, i);
  });
  return item;
};

@Component({
  selector: 'mst-select-label-data-columns',
  templateUrl: './select-label-data-columns.component.html',
  styleUrls: ['./select-label-data-columns.component.scss'],
  standalone: true,
  imports: [CommonModule, DropListComponent, ChartOptionsDialogComponent],
})
export class SelectLabelDataColumnsComponent {
  private _item: LabelDataColumns = { label: '', dataColumns: [] };
  labelItems: IdNameData[] = [];
  dataItems: IdNameData[] = [];
  optionsDialogOpen = false;
  selectedItemInfo: { item: VizDataColumn; index: number } | null = null;
  @Input() droppable = true;
  @Input() columnItems: IdNameData[] = [];
  @Input() set item(item: LabelDataColumns) {
    this._item = initOptions(item);
    this.updateDataItems(item);
  }
  get item() {
    return this._item;
  }
  @Output() change = new EventEmitter<LabelDataColumns>();

  private updateDataItems(item: LabelDataColumns) {
    const { dataColumns, label } = item;
    this.labelItems = label ? [{ id: label, name: label }] : [];
    this.dataItems = dataColumns.map(
      ({ field, options: { backgroundColor, borderColor } = {} }) => ({
        id: field,
        name: field,
        style: {
          backgroundColor,
          borderColor,
        },
      }),
    );
  }
  private applyItem() {
    this.updateDataItems(this.item);
    this.change.emit(this.item);
  }
  onDrop(id: string, type: 'label' | 'data') {
    if (type === 'label') {
      this.item.label = id;
    } else {
      if (!this.item.dataColumns?.some(({ field }) => field === id)) {
        this.item.dataColumns.push({
          field: id,
          options: initVizOptions({}, this.item.dataColumns.length),
        });
      }
    }
    this.updateDataItems(this.item);
    if (this.item.label) this.change.emit(this.item);
  }
  onDeleteIconClick({ item }: { item: IdNameData }) {
    const dataColumns = this.item.dataColumns?.filter(
      ({ field }) => field !== item.id,
    );
    this.item.dataColumns = dataColumns;
    this.updateDataItems(this.item);
    this.change.emit(this.item);
  }

  onListIconClick({
    item,
    index,
    name,
  }: {
    item: IdNameData;
    index: number;
    name: string;
  }) {
    if (name === 'delete') {
      const dataColumns = this.item.dataColumns?.filter(
        ({ field }) => field !== item.id,
      );
      this.item.dataColumns = dataColumns;
      this.applyItem();
    } else {
      this.selectedItemInfo = { item: this.item.dataColumns[index], index };
      this.optionsDialogOpen = true;
    }
  }
  onOptionsSave(options: VizOptions) {
    this.item.dataColumns[this.selectedItemInfo!.index].options = options;
    this.applyItem();
  }
  onOptionsDialogClose() {
    this.optionsDialogOpen = false;
  }
}
