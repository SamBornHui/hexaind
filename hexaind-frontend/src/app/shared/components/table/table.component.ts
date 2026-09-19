import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import {
  debounceTime,
  distinctUntilChanged,
  fromEvent,
  map,
  Subject,
  Subscription,
} from 'rxjs';
import {
  CellChangeInfo,
  CellInfo,
  Column,
  PageInfo,
  RowMeta,
  SimpleObject,
  SortInfo,
  TreeData,
} from '../models';
import { TableCellComponent } from '../table-cell/table-cell.component';
import { TableHeaderCellComponent } from '../table-header-cell/table-header-cell.component';
import {
  DefaultLimit,
  VirtualScrollComponent,
} from '../virtual-scroll/virtual-scroll.component';

// when returning 0, it means that the column is removed since the previous column spans it.
const getColSpan = (columnIndex: number, item: SimpleObject) => {
  const rowMeta: RowMeta | undefined = item._rowMeta;
  if (!rowMeta) return 1;
  const colSpan = rowMeta.colSpans?.find(
    (span) =>
      span.index <= columnIndex && span.index + span.count > columnIndex,
  );
  return !colSpan ? 1 : colSpan.index === columnIndex ? colSpan.count : 0;
};

@Component({
  selector: 'mst-table',
  templateUrl: './table.component.html',
  styleUrls: ['./table.component.scss'],
  standalone: true,
  imports: [
    VirtualScrollComponent,
    CommonModule,
    TableCellComponent,
    TableHeaderCellComponent,
  ],
})
export class TableComponent implements AfterViewInit, OnDestroy, OnChanges {
  startColumnIndex = 0; // Index of the first visible column
  visibleColumnCount = 0; // Number of visible columns
  leftFillerWidth = 0; // Width of the left filler cell
  rightFillerWidth = 0; // Width of the right filler cell
  sortInfo?: SortInfo;
  selectedIdSet = new Set<string>();
  getColSpan = getColSpan;
  private scrollSubscription!: Subscription;
  private resizeObserver!: ResizeObserver;
  private resizeSubject!: Subject<number>;
  private containerWidth = 0;
  private checkColumns = false;
  private _columns: Column[] = [];
  private _selectedIds: string[] = [];

  constructor(private cd: ChangeDetectorRef) {}

  // when there are more columns than can fit in the viewport, the column width will be set to this value and rendered in a virtual scroll.
  @Input() minColumnWidth = 100;
  @Input() limit = DefaultLimit;
  @Input() items: SimpleObject[] = [];
  @Input() hasMore = false;
  @Input() hasSort = false;
  @Input() hasCheckbox = false;
  @Input() loading?: boolean;
  @Input() columnPagination = true;
  @Input() keyField = 'id';
  @Input() multiSelect = false;
  @Input() set selectedIds(selectedIds: string[] | undefined) {
    this._selectedIds = selectedIds || [];
    this.selectedIdSet = new Set(selectedIds);
  }
  get selectedIds() {
    return this._selectedIds;
  }
  @Input() set columns(columns: Column[]) {
    columns = columns.map((column) => {
      if (this.hasSort) {
        if (
          column.defaultSortDirection &&
          column.defaultSortDirection !== 'none'
        ) {
          this.sortInfo = {
            field: column.field || '',
            direction: column.defaultSortDirection,
          };
        }
        column = {
          ...column,
          hasSort: true,
        };
      }
      column = {
        ...column,
        minWidth: column.minWidth ? column.minWidth : this.minColumnWidth,
      };
      return column;
    });
    if (this.hasCheckbox) {
      columns = [
        {
          _hasCheckbox: true,
          minWidth: 50,
          maxWidth: 50,
        },
        ...columns,
      ];
    }
    this._columns = columns;
  }
  get columns() {
    return this._columns;
  }
  @Output() cellClick = new EventEmitter<CellInfo>();
  @Output() selectedIdsChange = new EventEmitter<string[]>();
  @Output() loadMore = new EventEmitter<PageInfo>();
  @Output() sort = new EventEmitter<SortInfo>();
  @Output() change = new EventEmitter<CellChangeInfo>();
  @Output() arrowClick = new EventEmitter<{
    item: TreeData | SimpleObject;
    index: number;
  }>();

  @ViewChild('root') tableContainer!: ElementRef;
  @ViewChild(VirtualScrollComponent) virtualScroll!: VirtualScrollComponent;

  ngAfterViewInit() {
    if (this.columnPagination) {
      this.setupScrollListener();
      this.setupResizeObserver();
    } else {
      this.visibleColumnCount = this.columns.length;
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    // when ths columns is set by async data, we need to check if the columns are set
    if (
      !this.checkColumns &&
      changes['columns'] &&
      changes['columns'].currentValue?.length > 0 &&
      changes['columns'].previousValue?.length === 0
    ) {
      //console.log(changes['columns']);
      this.checkColumns = true;
      this.calculateVisibleColumns();
      this.cd.detectChanges();
    }
  }

  ngOnDestroy() {
    if (this.scrollSubscription) {
      this.scrollSubscription.unsubscribe();
    }
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    if (this.resizeSubject) {
      this.resizeSubject.complete(); // Complete the subject to prevent memory leaks
    }
  }

  setupScrollListener() {
    if (!this.scrollSubscription) {
      this.scrollSubscription = fromEvent(
        this.tableContainer.nativeElement,
        'scroll',
      )
        .pipe(
          map(() => ({
            scrollLeft: this.tableContainer.nativeElement.scrollLeft,
          })),
          debounceTime(100), // Adjust debounce time as needed
          // check only the horizontal scroll
          distinctUntilChanged(
            (prev, curr) => prev.scrollLeft === curr.scrollLeft,
          ),
        )
        .subscribe(() => {
          this.calculateVisibleColumns();
          this.cd.detectChanges();
        });
    }
  }

  setupResizeObserver() {
    this.resizeObserver = new ResizeObserver((entries) => {
      this.resizeSubject.next(entries[0].contentRect.width); // Emit width to the subject
    });
    this.resizeSubject = new Subject<number>(); // Create a subject
    this.resizeSubject.pipe(debounceTime(100)).subscribe((width) => {
      if (this.containerWidth === width) return; // Check if width has actually changed
      this.containerWidth = width;
      this.calculateVisibleColumns();
      this.cd.detectChanges();
    });

    this.resizeObserver.observe(this.tableContainer.nativeElement);
  }
  calculateVisibleColumns() {
    if (this.columns.length === 0 || !this.tableContainer?.nativeElement)
      return;
    const containerWidth = this.tableContainer.nativeElement.offsetWidth;
    const scrollLeft = this.tableContainer.nativeElement.scrollLeft;
    let width = 0;
    let visibleColumnCount = 0;
    let startColumnIndex = 0;
    let endColumnIndex = 0;
    let leftFillterWidth = 0;
    let rightFillterWidth = 0;
    for (let i = 0; i < this.columns.length; i++) {
      const minWidth = this.columns[i].minWidth || this.minColumnWidth;
      width += minWidth;
      if (width < scrollLeft) {
        leftFillterWidth += minWidth;
      }
      if (width >= scrollLeft && width <= scrollLeft + containerWidth) {
        if (visibleColumnCount === 0) {
          startColumnIndex = i;
        }
        visibleColumnCount++;
      }
      if (endColumnIndex === 0 && width > scrollLeft + containerWidth) {
        endColumnIndex = i;
      }
      // Table will render visibleColumnCount + 1
      if (endColumnIndex > 0 && i > endColumnIndex) {
        rightFillterWidth += minWidth;
      }
    }
    visibleColumnCount = Math.min(visibleColumnCount + 1, this.columns.length); // +1 for the right filler
    this.visibleColumnCount = visibleColumnCount;
    this.startColumnIndex = startColumnIndex;
    this.leftFillerWidth = leftFillterWidth;
    this.rightFillerWidth = rightFillterWidth;
  }
  private updateSelectedIds(item: SimpleObject) {
    const id = item[this.keyField] + '';
    if (this.multiSelect) {
      if (this.selectedIdSet.has(id)) {
        this.selectedIdSet.delete(id);
      } else {
        this.selectedIdSet.add(id);
      }
    } else {
      this.selectedIdSet.clear();
      this.selectedIdSet.add(id);
    }
    this.selectedIdsChange.emit(Array.from(this.selectedIdSet));
  }
  removeBottomSpacerHeight() {
    this.virtualScroll.removeBottomSpacerHeight();
  }
  onCellClick(e: CellInfo) {
    const { item, column } = e;
    if (column._hasCheckbox) this.updateSelectedIds(item);
    this.cellClick.emit(e);
  }
  onLoadMore(e: PageInfo) {
    this.loadMore.emit(e);
  }
  onResetScrolll() {
    this.tableContainer.nativeElement.scrollTo(0, 0);
    this.calculateVisibleColumns();
    this.startColumnIndex = 0;
    this.leftFillerWidth = 0;
    this.rightFillerWidth = 0;
  }
  onSort(sortInfo: SortInfo) {
    this.sortInfo = sortInfo;
    this.sort.emit(sortInfo);
  }
  onCellValueChange(e: CellChangeInfo) {
    this.change.emit(e);
  }
  onArrowClick(e: { item: TreeData | SimpleObject; index: number }) {
    this.arrowClick.emit(e);
  }
}
