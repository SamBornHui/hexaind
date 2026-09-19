import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ListItemParentNamesComponent } from '../list-item/list-item-parent-names/list-item-parent-names.component';
import { IdNameData, PageInfo } from '../models';
import { SelectListComponent } from '../select-list/select-list.component';

/**
Users can create dashboards by selecting a workflow, then a widget, and finally an output.
Dashboards display the latest output data upon opening.
A dropdown menu allows users to select an output version; the default is the latest output. Users can choose older versions to view historical data.
 */

@Component({
  selector: 'mst-select-dataset',
  templateUrl: './select-dataset.component.html',
  styleUrls: ['./select-dataset.component.scss'],
  standalone: true,
  imports: [CommonModule, ListItemParentNamesComponent, SelectListComponent],
})
export class SelectDatasetComponent {
  @Input() hasMore = false;
  @Input() sourceItems?: IdNameData[];
  @Input() selectedSourceId?: any;
  @Input() items: IdNameData[] = [];
  @Input() draggable = false;
  @Input() selectedItemHighlight = true;
  @Output() sourceChange = new EventEmitter<{
    item: IdNameData;
    index: number;
  }>();
  @Output() loadMore = new EventEmitter<{
    pageInfo: PageInfo;
    sourceId: any;
    searchTerm: string;
  }>();
  @Output() itemClick = new EventEmitter<{ item: IdNameData; index: number }>();
  onSourceChange(e: { item: IdNameData; index: number }) {
    this.sourceChange.emit(e);
  }
  onLoadMore(e: { pageInfo: PageInfo; sourceId: any; searchTerm: string }) {
    this.loadMore.emit(e);
  }
  onItemClick(e: { item: IdNameData; index: number }) {
    this.itemClick.emit(e);
  }
}
