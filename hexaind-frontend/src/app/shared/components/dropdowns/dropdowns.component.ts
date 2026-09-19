import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { InputComponent } from '../input/input.component';
import { IdNameData } from '../models';

@Component({
  selector: 'mst-dropdowns',
  templateUrl: './dropdowns.component.html',
  styleUrls: ['./dropdowns.component.scss'],
  standalone: true,
  imports: [InputComponent, CommonModule],
})
export class DropdownsComponent {
  selectedIds: string[] = [];
  @Input() datas: IdNameData[][] = [];
  @Input() items: IdNameData[] = [];
  @Output() change = new EventEmitter<{
    filter: IdNameData;
    filterIndex: number;
    id: string;
    item?: IdNameData;
    selectedIds: string[];
    last?: boolean;
  }>();

  onItemChange(id: string, filter: IdNameData, filterIndex: number) {
    this.selectedIds = this.selectedIds.slice(0, filterIndex);
    this.selectedIds.push(id);
    const items = this.datas[filterIndex];
    const item = items.find((item) => item.id === id);
    const last = filterIndex === this.items.length - 1;
    this.change.emit({
      id,
      item,
      filter,
      filterIndex,
      selectedIds: this.selectedIds,
      last,
    });
  }
}
