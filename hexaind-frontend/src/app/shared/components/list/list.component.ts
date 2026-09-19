import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  Input,
  Output,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { ListItemComponent } from '../list-item/list-item.component';
import {
  DefaultLimit,
  VirtualScrollComponent,
} from '../virtual-scroll/virtual-scroll.component';
import { IdNameData, PageInfo } from './../models';

@Component({
  selector: 'mst-list',
  templateUrl: './list.component.html',
  styleUrls: ['./list.component.scss'],
  standalone: true,
  imports: [CommonModule, VirtualScrollComponent, ListItemComponent],
})
export class ListComponent {
  selectedIdSet = new Set<string>();
  private _selectedIds: string[] = [];
  @Input() items: IdNameData[] = [];
  @Input() multiSelect = false;
  @Input() set selectedIds(selectedIds: string[] | undefined) {
    this._selectedIds = selectedIds || [];
    this.selectedIdSet = new Set(selectedIds);
  }
  get selectedIds() {
    return this._selectedIds;
  }
  @Input() listItemClassName = '';
  @Input() itemTemplate?: TemplateRef<any>;
  @Input() limit = DefaultLimit;
  @Input() hasMore = false;
  @Input() draggable = false;
  @Input() iconNames?: string[];
  @Input() rightIconNames?: string[];
  @Input() emptyMessage = '';
  @Input() keepBottomBorder = false;
  @Input() selectedItemHighlight = true;
  @Output() loadMore = new EventEmitter<PageInfo>();
  @Output() itemClick = new EventEmitter<{ item: IdNameData; index: number }>();
  @Output() iconClick = new EventEmitter<{
    item: IdNameData;
    index: number;
    name: string;
  }>();
  @Output() selectedIdsChange = new EventEmitter<string[]>();
  @Output() itemDragStart = new EventEmitter<{
    e: DragEvent;
    item: IdNameData;
  }>();
  @Output() itemDragEnd = new EventEmitter<{
    e: DragEvent;
    item: IdNameData;
  }>();
  @ViewChild(VirtualScrollComponent) virtualScroll!: VirtualScrollComponent;

  private updateSelectedIds(item: IdNameData) {
    if (this.multiSelect) {
      if (this.selectedIdSet.has(item.id)) {
        this.selectedIdSet.delete(item.id);
      } else {
        this.selectedIdSet.add(item.id);
      }
    } else {
      this.selectedIdSet.clear();
      this.selectedIdSet.add(item.id);
    }
    this.selectedIdsChange.emit(Array.from(this.selectedIdSet));
  }

  removeBottomSpacerHeight() {
    this.virtualScroll.removeBottomSpacerHeight();
  }

  onItemClick(item: IdNameData, index: number) {
    this.updateSelectedIds(item);
    this.itemClick.emit({ item, index });
  }
  onIconClick({
    index,
    item,
    name,
  }: {
    index: number;
    name: string;
    item: IdNameData;
  }) {
    this.updateSelectedIds(item);
    this.iconClick.emit({ item, index, name });
  }
  onItemDragStart(e: { e: DragEvent; item: IdNameData }) {
    this.itemDragStart.emit(e);
  }
  onItemDragEnd(e: { e: DragEvent; item: IdNameData }) {
    this.itemDragEnd.emit(e);
  }
  onLoadMore(e: PageInfo) {
    this.loadMore.emit(e);
  }
}
