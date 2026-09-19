import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { InputComponent } from '../input/input.component';
import { ListComponent } from '../list/list.component';
import { IdNameData } from '../models';

@Component({
  selector: 'mst-select-viz-items',
  templateUrl: './select-viz-items.component.html',
  styleUrls: ['./select-viz-items.component.scss'],
  standalone: true,
  imports: [CommonModule, InputComponent, ListComponent],
})
export class SelectVizItemsComponent {
  private _global: boolean = false;
  @Input() set global(value: boolean | undefined) {
    this._global = value === false ? false : true;
  }
  get global() {
    return this._global;
  }
  @Input() items: IdNameData[] = [];
  @Input() selectedIds: string[] = [];
  @Input() toggleLabel = 'Apply to All';
  @Output() change = new EventEmitter<{
    global: boolean;
    selectedIds: string[];
  }>();
  onChange(value: any, type: 'global' | 'selectedIds') {
    if (type === 'global') {
      this.global = value;
      if (this.global) this.selectedIds = [];
    } else {
      this.selectedIds = value;
    }
    this.change.emit({ global: this._global, selectedIds: this.selectedIds });
  }
}
