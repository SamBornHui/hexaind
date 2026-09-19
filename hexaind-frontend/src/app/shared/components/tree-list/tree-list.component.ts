import {
  Component,
  EventEmitter,
  Input,
  Output,
  ViewChild,
} from '@angular/core';
import { addChildren, collapseAll, collapseChildren } from '../../utils/utils';
import { ListComponent } from '../list/list.component';
import { IdNameData, IdNameTreeData, SimpleObject, TreeData } from '../models';
import { TreeItemComponent } from '../tree-item/tree-item.component';

/**
 * flat tree list for pagination.
 * if it has children, it will show a arrow icon.
 * the data has levels property to show the hierarchy.
 * When collapsed, the children will be hidden and be saved in the map because it should not be counted when rendering a page.
 * When expanded, the children will be shown and when the children are not in the map, it will emit the childrenLoad event.
 * "id" field is required for the key of the map.
 */
// TODO: after collapsed nodes, the bottom spacer height should be adjusted. Calculate all the pages and update the spacer height and keep the scroll position.
@Component({
  selector: 'mst-tree-list',
  templateUrl: './tree-list.component.html',
  styleUrls: ['./tree-list.component.scss'],
  standalone: true,
  imports: [ListComponent, TreeItemComponent],
})
export class TreeListComponent {
  private didCollapsedAll = false;
  // when collapsed, the children will be saved in the map and be removed from the items for pagination.
  childrenMap: Map<string, IdNameTreeData[]> = new Map();
  private _items: IdNameTreeData[] = [];
  @Input() set items(items: IdNameTreeData[]) {
    if (!this.didCollapsedAll && this.collapsedAll) {
      this.didCollapsedAll = true;
      collapseAll(this.childrenMap, items);
    }
    this._items = items;
  }
  get items() {
    return this._items;
  }
  @Input() selectedIds?: string[];
  @Input() collapsedAll = false;
  // TODO: need to test this
  @Input() set childrenData(data: {
    children: IdNameTreeData[];
    parentId: string;
  }) {
    addChildren(data, this.items);
  }
  @Input() selectedItemHighlight = true;
  @Output() itemClick = new EventEmitter<{ item: IdNameData; index: number }>();
  @Output() childrenLoad = new EventEmitter<{
    item: TreeData;
    index: number;
  }>();
  @ViewChild(ListComponent) list!: ListComponent;

  onItemClick(e: { item: IdNameData; index: number }) {
    this.itemClick.emit(e);
  }
  onArrowClick(itemInfo: { item: TreeData | SimpleObject; index: number }) {
    const { index } = itemInfo;
    const item = this.items[index];
    item.expanded = !item.expanded;
    if (item.expanded) {
      const children = this.childrenMap.get(item.id);
      if (children?.length) {
        this.childrenMap.delete(item.id);
        this.items.splice(index + 1, 0, ...children);
      } else {
        item.loading = true;
        this.childrenLoad.emit({ index, item });
      }
    } else {
      collapseChildren(this.childrenMap, item, this.items, index);
    }
    this.items[index] = item;
    this.list.removeBottomSpacerHeight();
  }
}
