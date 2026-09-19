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
import { getRGBAByIndex } from '../charts/chart-utils';
import { DropListComponent } from '../drop-list/drop-list.component';
import { FilterComponent } from '../filter/filter.component';
import { InputComponent } from '../input/input.component';
import {
  CellStyleColumn,
  CellStyleType,
  Filter,
  getCellStyleTypeList,
  IdNameData,
} from '../models';

@Component({
  selector: 'mst-select-conditional-cell-styles',
  templateUrl: './select-conditional-cell-styles.component.html',
  styleUrls: ['./select-conditional-cell-styles.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    InputComponent,
    ButtonComponent,
    DropListComponent,
    FilterComponent,
  ],
})
export class SelectConditionalCellStylesComponent {
  private _items: CellStyleColumn[] = [];
  item: {
    index: number;
    cellStyleColumn: CellStyleColumn;
    column: string;
    hasStyles: boolean;
  } = {
    index: 0,
    cellStyleColumn: {
      type: 'cell',
      filter: { field: '', value: '' },
      options: { backgroundColor: '' },
    },
    column: '',
    hasStyles: false,
  };
  cellStyleItems: IdNameData[] = [];
  cellStyleTypeItems: IdNameData[] = [];
  @ViewChild('dialogTemplate') dialogTemplate!: TemplateRef<any>;
  @Input() droppable = true;
  @Input() columnItems: IdNameData[] = [];
  @Input() set items(items: CellStyleColumn[]) {
    this._items = items;
    this.updateDataItems(items);
  }
  get items() {
    return this._items;
  }
  @Output() change = new EventEmitter<CellStyleColumn[]>();

  constructor(public dialog: MatDialog) {}
  ngOnInit(): void {
    this.cellStyleTypeItems = getCellStyleTypeList();
  }

  private updateDataItems(items: CellStyleColumn[]) {
    const cellStyleItems: IdNameData[] = [];
    items.forEach((data, i) => {
      const {
        filter: { field, type, value },
        options: { backgroundColor, borderColor },
      } = data;
      const name = `${field} ${type || ''} ${value}`;
      cellStyleItems.push({
        id: String(i),
        name,
        data,
        style: {
          borderColor,
          backgroundColor,
        },
      });
    });
    this.cellStyleItems = cellStyleItems;
  }

  private openDialog(column: string, index?: number) {
    if (index == null) {
      index = this.items.length;
      const cellStyleColumn = {
        filter: { field: column, value: '' },
        options: {
          borderColor: getRGBAByIndex(index),
          backgroundColor: getRGBAByIndex(index, 0.2),
        },
      };
      this.items.push(cellStyleColumn);
      this.item = {
        index: this.items.length - 1,
        cellStyleColumn,
        column,
        hasStyles: true,
      };
      this.updateDataItems(this.items);
    } else {
      const item = this.items[index];
      const {
        options: { backgroundColor, borderColor },
      } = item;
      this.item = {
        index,
        cellStyleColumn: item,
        column,
        hasStyles: backgroundColor !== '' || borderColor !== '',
      };
      // console.log(this.item);
    }
    this.dialog.open(this.dialogTemplate);
  }

  onFilterChange(e: Filter) {
    this.item.cellStyleColumn.filter = e;
  }
  onDrop(id: string) {
    this.openDialog(id);
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
      this.items.splice(index, 1);
      this.updateDataItems(this.items);
      this.change.emit(this.items);
    } else {
      this.openDialog(item['data'].filter.field, index);
    }
  }

  onDialogAction() {
    const { index, cellStyleColumn } = this.item;
    this.items[index] = cellStyleColumn;
    this.updateDataItems(this.items);
    this.dialog.closeAll();
    this.change.emit(this.items);
  }
  onStyleChange(value: string, type: 'backgroundColor' | 'borderColor') {
    this.item.cellStyleColumn.options[type] = value;
  }
  onHasStylesChange(hasStyles: boolean) {
    this.item.hasStyles = hasStyles;
    if (!hasStyles) {
      this.item.cellStyleColumn.options = {};
    } else {
      this.item.cellStyleColumn.options = {
        backgroundColor: getRGBAByIndex(this.item.index, 0.2),
        borderColor: getRGBAByIndex(this.item.index),
      };
    }
  }
  onTypeChange(type: CellStyleType) {
    this.item.cellStyleColumn.type = type;
  }
}
