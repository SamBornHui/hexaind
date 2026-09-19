import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  Input,
  Output,
  TemplateRef,
} from '@angular/core';
import { InputComponent } from '../input/input.component';
import { ListComponent } from '../list/list.component';
import { IdNameData, PageInfo } from '../models';
import { SearchBoxComponent } from '../search-box/search-box.component';
import { DefaultLimit } from '../virtual-scroll/virtual-scroll.component';

@Component({
  selector: 'mst-select-list',
  templateUrl: './select-list.component.html',
  styleUrls: ['./select-list.component.scss'],
  standalone: true,
  imports: [ListComponent, SearchBoxComponent, CommonModule, InputComponent],
})
export class SelectListComponent {
  searchTerm = '';
  filteredItems: IdNameData[] = [];
  private _items: IdNameData[] = [];
  @Input() hasMore = false;
  @Input() hideSearch = false;
  @Input() title = '';
  @Input() emptyMessage = 'No Data';
  @Input() placeholder = 'Search...';
  @Input() itemTemplate?: TemplateRef<any>;
  @Input() sourceItems?: IdNameData[];
  @Input() selectedSourceId?: any;
  @Input() sourceTitle = '';
  @Input() set items(items: IdNameData[]) {
    this._items = items;
    this.filteredItems = items;
  }
  get items() {
    return this._items;
  }
  @Input() selectedItem?: IdNameData;
  @Input() draggable = false;
  @Input() selectedItemHighlight = true;
  @Output() itemClick = new EventEmitter<{ item: IdNameData; index: number }>();
  @Output() sourceChange = new EventEmitter<{
    item: IdNameData;
    index: number;
  }>();
  @Output() itemDragStart = new EventEmitter<{
    e: DragEvent;
    item: IdNameData;
  }>();
  @Output() itemDragEnd = new EventEmitter<{
    e: DragEvent;
    item: IdNameData;
  }>();
  @Output() loadMore = new EventEmitter<{
    pageInfo: PageInfo;
    sourceId: any;
    searchTerm: string;
  }>();
  initLoadMore() {
    this.loadMore.emit({
      pageInfo: { index: 0, offset: 0, limit: DefaultLimit },
      sourceId: this.selectedSourceId,
      searchTerm: this.searchTerm,
    });
  }
  onItemClick(e: { item: IdNameData; index: number }) {
    this.itemClick.emit(e);
  }
  onSearch(e: string) {
    this.searchTerm = e;
    if (this.hasMore) {
      this.initLoadMore();
    } else {
      this.filteredItems = this.getItems();
    }
  }
  onSourceChange(id: string) {
    if (this.sourceItems) {
      const index = this.sourceItems.findIndex((item) => item.id === id);
      const item = this.sourceItems[index];
      this.sourceChange.emit({ item, index });
      this.searchTerm = '';
      this.selectedSourceId = id;
      this.initLoadMore();
    }
  }
  getItems() {
    return this.searchTerm
      ? this.items.filter(
          ({ name }) =>
            name?.toLowerCase().includes(this.searchTerm.toLowerCase()),
        )
      : this.items;
  }
  onItemDragStart(e: { e: DragEvent; item: IdNameData }) {
    this.itemDragStart.emit(e);
  }
  onItemDragEnd(e: { e: DragEvent; item: IdNameData }) {
    this.itemDragEnd.emit(e);
  }
  onLoadMore(e: PageInfo) {
    this.loadMore.emit({
      pageInfo: e,
      sourceId: this.selectedSourceId,
      searchTerm: this.searchTerm,
    });
  }
}
