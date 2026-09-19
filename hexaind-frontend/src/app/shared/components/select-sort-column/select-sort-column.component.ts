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
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { ButtonComponent } from '../button/button.component';
import { DropListComponent } from '../drop-list/drop-list.component';
import { InputComponent } from '../input/input.component';
import { IdNameData, SortInfo } from '../models';
import { getSortDirectionList } from './../models';

@Component({
  selector: 'mst-select-sort-column',
  templateUrl: './select-sort-column.component.html',
  styleUrls: ['./select-sort-column.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    InputComponent,
    ButtonComponent,
    DropListComponent,
  ],
})
export class SelectSortColumnComponent implements OnInit {
  private _items: SortInfo[] = [];
  sortDirectionList!: IdNameData[];
  item!: { index: number; sort: SortInfo; column: string };
  sortItems: IdNameData[] = [];
  @ViewChild('dialogTemplate') dialogTemplate!: TemplateRef<any>;
  @Input() columnItems: IdNameData[] = [];
  @Input() set items(items: SortInfo[]) {
    this._items = items;
    this.updateDataItems(items);
  }
  get items() {
    return this._items;
  }
  @Output() change = new EventEmitter<SortInfo[]>();
  constructor(public dialog: MatDialog) {}
  ngOnInit(): void {
    this.sortDirectionList = getSortDirectionList(true);
  }

  private updateDataItems(items: SortInfo[]) {
    const sortItems: IdNameData[] = [];
    items.forEach((data, i) => {
      const { field, direction } = data;
      const name = `${field} ${direction}`;
      sortItems.push({
        id: String(i),
        name,
        data,
      });
    });
    this.sortItems = sortItems;
  }

  private openDialog(column: string, index?: number) {
    if (index == null) {
      const item: SortInfo = { field: column, direction: 'asc' };
      this.items.push(item);
      this.item = { index: this.items.length - 1, sort: item, column };
      this.updateDataItems(this.items);
    } else {
      this.item = {
        index: this.items.length - 1,
        sort: this.items[index],
        column,
      };
    }
    this.dialog.open(this.dialogTemplate);
  }

  onSortChange(value: any, type: 'field' | 'direction') {
    this.item.sort[type] = value;
  }
  onDrop(id: string) {
    this.openDialog(id);
  }
  onSortListIconClick({
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
    const { index, sort } = this.item;
    this.items[index] = sort;
    this.updateDataItems(this.items);
    this.dialog.closeAll();
    this.change.emit(this.items);
  }
}
