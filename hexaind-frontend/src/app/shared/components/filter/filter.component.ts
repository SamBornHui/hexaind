import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { InputComponent } from '../input/input.component';
import { ListComponent } from '../list/list.component';
import { Filter, getFilterTypeList, IdNameData } from '../models';
import { SelectVizItemsComponent } from '../select-viz-items/select-viz-items.component';

@Component({
  selector: 'mst-filter',
  templateUrl: './filter.component.html',
  styleUrls: ['./filter.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    InputComponent,
    ListComponent,
    SelectVizItemsComponent,
  ],
})
export class FilterComponent implements OnInit {
  filterTypeItems: IdNameData[] = [];
  private _filter!: Filter;
  @Input() fieldLabel = 'Column';
  @Input() set filter(filter: Filter) {
    this._filter = {
      ...filter,
      global: filter.global === false ? false : true,
    };
  }
  get filter() {
    return this._filter;
  }
  @Input() fields!: IdNameData[];
  @Input() targetItems: IdNameData[] = [];
  @Output() change = new EventEmitter<Filter>();
  ngOnInit(): void {
    this.filterTypeItems = getFilterTypeList();
  }
  onFilterChange(
    value: any,
    type: 'field' | 'type' | 'value' | 'to' | 'target',
  ) {
    switch (type) {
      case 'target':
        const { global, selectedIds: targetIds } = value;
        this.filter = { ...this.filter, global, targetIds };
        break;
      default:
        this.filter[type] = value;
        break;
    }
    this.change.emit(this.filter);
  }
}
