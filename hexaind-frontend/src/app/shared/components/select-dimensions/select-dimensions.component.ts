import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatDialogModule } from '@angular/material/dialog';
import { DropListComponent } from '../drop-list/drop-list.component';
import { IdNameData } from '../models';

@Component({
  selector: 'mst-select-dimensions',
  templateUrl: './select-dimensions.component.html',
  styleUrls: ['./select-dimensions.component.scss'],
  standalone: true,
  imports: [CommonModule, MatDialogModule, DropListComponent],
})
export class SelectDimensionsComponent {
  private _items: string[] = [];
  dimensionItems: IdNameData[] = [];
  @Input() droppable = true;
  @Input() columnItems: IdNameData[] = [];
  @Input() set items(items: string[]) {
    this._items = items;
    this.updateDataItems(items);
  }
  get items() {
    return this._items;
  }
  @Output() change = new EventEmitter<string[]>();

  private updateDataItems(items: string[] = []) {
    this.dimensionItems = items.map((id) => ({
      id,
      name: id,
    }));
  }
  private applyItem() {
    this.updateDataItems(this.items);
    this.change.emit(this.items);
  }
  onDrop(id: string) {
    if (!this.items.includes(id)) {
      this.items = [...this.items, id];
      this.applyItem();
    }
  }
  onListIconClick({
    item,
    name,
  }: {
    item: IdNameData;
    index: number;
    name: string;
  }) {
    if (name === 'delete') {
      this.items = this.items.filter((id) => id !== item.id);
      this.applyItem();
    }
  }
}
