import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  HostBinding,
  HostListener,
  Input,
  Output,
} from '@angular/core';
import { HintComponent } from '../hint/hint.component';
import { IconComponent } from '../icon/icon.component';
import { Column, SortDirection, SortInfo } from '../models';

const getNextSortDirection = (direction: SortDirection) =>
  direction === 'asc' ? 'desc' : direction === 'desc' ? 'none' : 'asc';

@Component({
  selector: 'mst-table-header-cell',
  templateUrl: './table-header-cell.component.html',
  styleUrls: ['./table-header-cell.component.scss'],
  standalone: true,
  imports: [IconComponent, CommonModule, HintComponent],
})
export class TableHeaderCellComponent {
  @Input() column!: Column;
  @Input() sortDirection: SortDirection = 'none';
  @Output() sort = new EventEmitter<SortInfo>();
  @HostBinding('title') get title() {
    return this.column.name;
  }
  @HostBinding('class.has-sort') get hasSort() {
    return this.column.hasSort;
  }
  @HostListener('click', ['$event'])
  onClick(event: MouseEvent) {
    if (!this.column.hasSort) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    this.sort.emit({
      field: this.column.field || '',
      direction: getNextSortDirection(this.sortDirection),
    });
  }
}
