import { Component, EventEmitter, Input, Output } from '@angular/core';
import { IdNameData } from '../models';
import { SelectListComponent } from '../select-list/select-list.component';

@Component({
  selector: 'mst-select-column',
  templateUrl: './select-column.component.html',
  styleUrls: ['./select-column.component.scss'],
  standalone: true,
  imports: [SelectListComponent],
})
export class SelectColumnComponent {
  @Input() hideSearch = false;
  @Input() title = 'Columns';
  @Input() items: IdNameData[] = [];
  @Output() itemDragStart = new EventEmitter<{
    e: DragEvent;
    item: IdNameData;
  }>();
  @Output() itemDragEnd = new EventEmitter<{
    e: DragEvent;
    item: IdNameData;
  }>();
  onItemDragStart(e: { e: DragEvent; item: IdNameData }) {
    this.itemDragStart.emit(e);
  }
  onItemDragEnd(e: { e: DragEvent; item: IdNameData }) {
    this.itemDragEnd.emit(e);
  }
}
