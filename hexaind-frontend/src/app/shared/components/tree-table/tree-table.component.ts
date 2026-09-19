import {
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  Output,
  ViewChild,
} from '@angular/core';
import { collapseAll, collapseChildren } from '../../utils/utils';
import {
  CellChangeInfo,
  CellInfo,
  Column,
  PageInfo,
  SimpleObject,
  SortInfo,
  TreeData,
} from '../models';
import { TableComponent } from '../table/table.component';
import { DefaultLimit } from '../virtual-scroll/virtual-scroll.component';

@Component({
  selector: 'mst-tree-table',
  templateUrl: './tree-table.component.html',
  styleUrls: ['./tree-table.component.scss'],
  standalone: true,
  imports: [TableComponent],
})
export class TreeTableComponent {
  constructor(private cd: ChangeDetectorRef) {}
  private didCollapsedAll = false;
  private _columns: Column[] = [];
  private _items: SimpleObject[] = [];
  childrenMap: Map<string, TreeData[]> = new Map();
  @Output() childrenLoad = new EventEmitter<{
    item: TreeData;
    index: number;
  }>();
  @Input() set columns(columns: Column[]) {
    if (columns.length > 0) columns[0]._hasTreeArrow = true;
    this._columns = columns;
  }
  get columns() {
    return this._columns;
  }
  @Input() collapsedAll = false;
  @Input() set items(items: SimpleObject[]) {
    if (!this.didCollapsedAll && this.collapsedAll) {
      this.didCollapsedAll = true;
      collapseAll(this.childrenMap, items);
    }
    this._items = items;
  }
  get items() {
    return this._items;
  }
  /** copy from table component start */
  @Input() minColumnWidth = 100;
  @Input() limit = DefaultLimit;
  @Input() hasMore = false;
  @Input() hasSort = false;
  @Input() hasCheckbox = false;
  @Input() loading?: boolean;
  @Input() columnPagination = true;
  @Input() keyField = 'id';
  @Input() multiSelect = false;
  @Input() selectedIds?: string[];
  @Output() cellClick = new EventEmitter<CellInfo>();
  @Output() selectedIdsChange = new EventEmitter<string[]>();
  @Output() loadMore = new EventEmitter<PageInfo>();
  @Output() sort = new EventEmitter<SortInfo>();
  @Output() change = new EventEmitter<CellChangeInfo>();

  onCellClick(e: CellInfo) {
    this.cellClick.emit(e);
  }
  onSelectedIdsChange(selectedIds: string[]) {
    this.selectedIdsChange.emit(selectedIds);
  }
  onLoadMore(pageInfo: PageInfo) {
    this.loadMore.emit(pageInfo);
  }
  onSort(sortInfo: SortInfo) {
    this.sort.emit(sortInfo);
  }
  onChange(cellChangeInfo: CellChangeInfo) {
    this.change.emit(cellChangeInfo);
  }
  /** copy from table component end */
  @ViewChild(TableComponent) table!: TableComponent;
  onArrowClick(itemInfo: { item: TreeData | SimpleObject; index: number }) {
    const { index } = itemInfo;
    const item = { ...this.items[index] } as TreeData;
    item.expanded = !item.expanded;
    if (item.expanded) {
      const children = this.childrenMap.get(item[this.keyField]);
      if (children?.length) {
        this.childrenMap.delete(item[this.keyField]);
        this.items.splice(index + 1, 0, ...children);
      } else {
        item.loading = true;
        this.childrenLoad.emit({ index, item });
      }
    } else {
      collapseChildren(this.childrenMap, item, this.items, index);
    }
    this.items[index] = item;
    this.table.removeBottomSpacerHeight();
    this.cd.detectChanges();
  }
}
