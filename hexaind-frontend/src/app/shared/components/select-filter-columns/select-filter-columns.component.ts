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
import { ButtonComponent } from '../button/button.component';
import { DropListComponent } from '../drop-list/drop-list.component';
import { FilterComponent } from '../filter/filter.component';
import { Filter, IdNameData } from '../models';

@Component({
  selector: 'mst-select-filter-columns',
  templateUrl: './select-filter-columns.component.html',
  styleUrls: ['./select-filter-columns.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    ButtonComponent,
    DropListComponent,
    FilterComponent,
  ],
})
export class SelectFilterColumnsComponent {
  private _items: Filter[] = [];
  item!: { index: number; filter: Filter; column: string };
  filterItems: IdNameData[] = [];

  @ViewChild('dialogTemplate') dialogTemplate!: TemplateRef<any>;

  @Input() columnItems: IdNameData[] = [];
  @Input() targetItems: IdNameData[] = [];
  @Input() set items(items: Filter[]) {
    this._items = items;
    this.updateDataItems(items);
  }
  get items() {
    return this._items;
  }
  @Output() change = new EventEmitter<Filter[]>();

  constructor(public dialog: MatDialog) {}

  private updateDataItems(items: Filter[]) {
    const filterItems: IdNameData[] = [];
    items.forEach((data, i) => {
      const { field, value, type } = data;
      const name = `${field} ${type || ''} ${value}`;
      filterItems.push({
        id: String(i),
        name,
        data,
      });
    });
    this.filterItems = filterItems;
  }

  private openDialog(column: string, index?: number) {
    if (index == null) {
      const item = { field: column, value: '' };
      this.items.push(item);
      this.item = { index: this.items.length - 1, filter: item, column };
      this.updateDataItems(this.items);
    } else {
      this.item = {
        index,
        filter: this.items[index],
        column,
      };
    }
    this.dialog.open(this.dialogTemplate);
  }

  onFilterChange(e: Filter) {
    this.item.filter = e;
  }
  onDrop(id: string) {
    this.openDialog(id);
  }
  onFilterListIconClick({
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
      this.updateDataItems(this.items);
      this.change.emit(this.items);
    } else {
      this.openDialog(item['data'].field, index);
    }
  }

  onDialogAction() {
    const { index, filter } = this.item;
    this.items[index] = filter;
    this.updateDataItems(this.items);
    this.dialog.closeAll();
    this.change.emit(this.items);
  }
}
