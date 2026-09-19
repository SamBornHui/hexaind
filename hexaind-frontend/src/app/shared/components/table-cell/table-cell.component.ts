import { CommonModule } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  HostBinding,
  HostListener,
  Input,
  Output,
  ViewChild,
} from '@angular/core';
import { getClassNames } from '../../utils/utils';
import { InputComponent } from '../input/input.component';
import {
  CellChangeInfo,
  CellInfo,
  Column,
  SimpleObject,
  TreeData,
} from '../models';
import { TreeItemComponent } from '../tree-item/tree-item.component';

const getValueChangeInfo = (item: { [key: string]: any }, field?: string) => {
  const valueChanges = item['__valueChanges'] || {};
  return field ? valueChanges[field] : undefined;
};
const setValueChange = (item: { [key: string]: any }, field?: string) => {
  if (!field) {
    return;
  }
  const valueChanges = item['__valueChanges'] || {};
  if (valueChanges[field] === undefined) {
    valueChanges[field] = { origin: item[field] };
    item['__valueChanges'] = valueChanges;
  }
};

const isEdited = (item: { [key: string]: any }, field?: string) => {
  if (!field) {
    return false;
  }
  const valueChangeInfo = getValueChangeInfo(item, field);
  return (
    valueChangeInfo !== undefined && item[field] !== valueChangeInfo.origin
  );
};

const isRowChanged = (item: { [key: string]: any }) => {
  const valueChanges = item['__valueChanges'] || {};
  return Object.keys(valueChanges).some(
    (field) => item[field] !== valueChanges[field].origin,
  );
};

@Component({
  selector: 'mst-table-cell',
  templateUrl: './table-cell.component.html',
  styleUrls: ['./table-cell.component.scss'],
  standalone: true,
  imports: [CommonModule, InputComponent, TreeItemComponent],
})
export class TableCellComponent {
  constructor(
    private cdr: ChangeDetectorRef,
    private el: ElementRef,
  ) {}
  editing = false;
  value: any;
  @Input() selectedRow = false;
  @Input() rowIndex!: number;
  @Input() columnIndex!: number;
  @Input() column!: Column;
  @Input() columns: Column[] = [];
  @Input() item: SimpleObject = {};
  @Input() keyField = 'id';
  @Output() change = new EventEmitter<CellChangeInfo>();
  @Output() cellClick = new EventEmitter<CellInfo>();
  @Output() arrowClick = new EventEmitter<{
    item: TreeData | SimpleObject;
    index: number;
  }>();
  @ViewChild(InputComponent) inputEl!: InputComponent;
  @HostListener('click', ['$event']) onClick(e: MouseEvent) {
    e.stopPropagation();
    if (this.column.editable && !this.editing) {
      this.editing = true;
      this.value = this.item[this.column.field as string];
      this.el.nativeElement.classList.add('editing');
      setTimeout(() => {
        this.inputEl?.focus(true);
      }, 0);
      // Why do we need this? but it works.
      this.cdr.detectChanges();
    }
    this.cellClick.emit({
      column: this.column,
      field: this.column.field,
      value: this.item[this.column.field as string],
      rowIndex: this.rowIndex,
      columnIndex: this.columnIndex,
      item: this.item,
    });
  }
  @HostBinding('class') get class() {
    return getClassNames(
      this.column.className,
      `mst-table-cell--type-${this.column.type || 'string'}`,
      `mst-table-cell--index-${this.rowIndex}-${this.columnIndex}`,
      isEdited(this.item, this.column.field) ? 'edited' : '',
    );
  }
  @HostBinding('title') get title() {
    return this.column.field ? this.item[this.column.field] : '';
  }
  @HostBinding('style') get style() {
    return this.column.styleFn
      ? this.column.styleFn(this.item, this.column, this.rowIndex)
      : undefined;
  }
  onEdit(value: any) {
    this.value = value;
  }
  onBlur() {
    this.endEdit();
  }
  onKeyDown(e: KeyboardEvent) {
    switch (e.key) {
      case 'Tab':
      case 'Enter':
        this.moveNextEditableCell();
        break;
      case 'Esc':
      case 'Escape':
        this.endEdit();
        break;
    }
  }
  moveNextEditableCell() {
    let firstEditableColumnIndex = -1;
    let nextEditableColumnIndex = -1;
    let rowIndex = this.rowIndex;
    for (let i = 0; i < this.columns.length; i++) {
      if (this.columns[i].editable) {
        if (firstEditableColumnIndex === -1 && i < this.columnIndex) {
          firstEditableColumnIndex = i;
        }
        if (i > this.columnIndex) {
          nextEditableColumnIndex = i;
          break;
        }
      }
    }
    if (nextEditableColumnIndex === -1) {
      nextEditableColumnIndex = firstEditableColumnIndex;
      rowIndex++;
    }
    if (nextEditableColumnIndex !== -1) {
      //console.log(rowIndex, nextEditableColumnIndex);
      const tableContainerEl = this.el.nativeElement.closest(
        '.mst-table__container',
      );
      const nextCellEl = tableContainerEl.querySelector(
        `.mst-table-cell--index-${rowIndex}-${nextEditableColumnIndex}`,
      );
      if (nextCellEl) {
        (nextCellEl as HTMLElement).click();
      }
    }
  }
  endEdit() {
    this.editing = false;
    this.el.nativeElement.classList.remove('editing');
    // for original value
    setValueChange(this.item, this.column.field);
    if (this.column.field && this.item[this.column.field] !== this.value) {
      this.item[this.column.field] = this.value;
      const edited = isEdited(this.item, this.column.field);
      if (edited) {
        this.el.nativeElement.classList.add('edited');
      } else {
        this.el.nativeElement.classList.remove('edited');
      }
      const item = { ...this.item };
      delete item['__valueChanges'];
      this.change.emit({
        column: this.column,
        field: this.column.field,
        value: this.value,
        rowIndex: this.rowIndex,
        columnIndex: this.columnIndex,
        item,
        isCellChanged: edited,
        isRowChanged: isRowChanged(this.item),
      });
    }
    this.cdr.detectChanges();
  }
  onArrowClick(e: { item: TreeData | SimpleObject; index: number }) {
    this.arrowClick.emit(e);
  }
}
