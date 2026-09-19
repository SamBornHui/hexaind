import { NgFor, NgIf, NgTemplateOutlet } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  Output,
  SimpleChanges,
  TemplateRef,
  ViewChild,
  ViewChildren,
} from '@angular/core';
import {
  debounceTime,
  distinctUntilChanged,
  fromEvent,
  map,
  Subscription,
} from 'rxjs';
import { arraysEqual } from '../../utils/utils';
import { EmptyComponent } from '../empty/empty.component';
import { LoaderComponent } from '../loader/loader.component';
import { PageInfo } from '../models';

export const DefaultLimit = 50;
// TODO: when it has multiple pages and a full page height is smaller than the container height, UI should display an error message. The container height should be smaller than the page height(page size). The default page size is 50, but sometimes the container height is bigger than the screen height by mistake. In that case, the page size should be bigger than the container height.
/**
Infinite scroll + pagination
The cdk-virtual-scroll-viewport requires styles for the scrollbar, while mst-virtual-scroll does not. Additionally, cdk-virtual-scroll-viewport renders every row, whereas mst-virtual-scroll renders data page by page, offering better rendering performance. We can also add custom functionalities to our component if needed.
 */
@Component({
  selector: '[mstVirtualScroll]',
  templateUrl: './virtual-scroll.component.html',
  styleUrls: ['./virtual-scroll.component.scss'],
  standalone: true,
  imports: [NgFor, NgIf, NgTemplateOutlet, LoaderComponent, EmptyComponent],
})
export class VirtualScrollComponent
  implements OnInit, AfterViewInit, OnChanges, OnDestroy
{
  private resetting = false;
  pageHeights: number[] = [];
  isScrollDown = true;
  lastScrollTop = 0;
  isEnd = false;
  scrollSubscription!: Subscription;
  topSpacerHeight = 0;
  bottomSpacerHeight = 0;
  visiblePages = [0];
  loadingData = false;
  @Input() loading?: boolean; // manually set the loading state
  @Input() limit = DefaultLimit;
  @Input() items: any[] = [];
  @Input() pageTemplate!: TemplateRef<any>;
  @Input() headerTemplate?: TemplateRef<any>;
  @Input() hasMore = true;
  @Input() isTable = false;
  @Input() emptyMessage = '';
  @Input() containerEl!: HTMLElement;

  @Output() loadMore = new EventEmitter<PageInfo>();
  @Output() reset = new EventEmitter<void>();

  rootTemplate!: TemplateRef<any>;
  @ViewChild('topSpacer') topSpacer!: ElementRef;
  @ViewChild('bottomSpacer') bottomSpacer!: ElementRef;
  @ViewChildren('pages') pages!: ElementRef[];

  constructor(private el: ElementRef) {}

  /**
   * visiblePages can be updated by the scroll height if we have the pageHeights for the visible area
   */
  updatePageHeights() {
    this.pages?.forEach((page) => {
      const pageIndex = +page.nativeElement.getAttribute('data-page-index');
      if (!this.pageHeights[pageIndex])
        this.pageHeights[pageIndex] = page.nativeElement.offsetHeight || 0;
    });
    //console.log('updatePageHeights', this.pageHeights);
  }

  // manually reset the scroll position when items are new.
  resetScroll() {
    if (!this.el.nativeElement) return;
    this.lastScrollTop = 0;
    this.isScrollDown = true;
    this.isEnd = false;
    this.loadingData = false;
    this.pageHeights = [];
    const el = this.el.nativeElement;
    this.resetting = true;
    if (el && el.scrollTo) {
      el.scrollTo(0, 0);
    }
    this.topSpacerHeight = 0;
    this.bottomSpacerHeight = 0;
    this.updateVisiblePages(el);
    this.reset.emit();
  }

  ngOnInit(): void {
    if (!this.containerEl) this.containerEl = this.el.nativeElement;
    this.initScroll();
  }

  checkScrollDirection(el: HTMLElement) {
    const scrollTop = el.scrollTop;
    this.isScrollDown = this.lastScrollTop < scrollTop;
    this.lastScrollTop = scrollTop;
  }

  initScroll() {
    const scroll$ = fromEvent(this.containerEl, 'scroll').pipe(
      map((event) => ({
        event,
        scrollTop: this.containerEl.scrollTop,
      })),
      debounceTime(100),
      // check only the vertical scroll
      distinctUntilChanged((prev, curr) => prev.scrollTop === curr.scrollTop),
    );
    this.scrollSubscription = scroll$.subscribe(({ event }) => {
      // console.log('scroll', event);
      this.handleScroll(event.target as HTMLElement);
    });
  }

  /**
   * 1. UI always have the first page.
   * 2. the first page size is smaller than the page size - end pagination.
   * 3. the first page size is the same as the page size and the scrollbar is at the end of the scroll -> load the next page.
   * 4. scroll down: visible area page + page index + 1
   * 5. scroll up: visible area page index - 1, visiblar area page index
   */

  handleScroll(el: HTMLElement) {
    // console.log('handleScroll', el.scrollTop);
    if (!el) return;
    this.items = this.items || [];
    this.updatePageHeights();
    this.updateVisiblePages(el);
  }

  checkAndUpdateVisiblePages(visiblePages: number[]) {
    if (!arraysEqual(this.visiblePages, visiblePages)) {
      this.visiblePages = visiblePages;
      this.updateSpacerHeight();
      if (this.resetting) {
        this.resetting = false;
        this.containerEl.scrollTo(0, 0);
        return;
      }
    }
  }

  updateVisiblePages(el: HTMLElement) {
    const startHeight = el.scrollTop;
    // console.log('updateVisiblePages', el.scrollTop);
    if (this.isEndOfTheContent(el)) {
      const lastPage = this.pageHeights.length
        ? this.pageHeights.length - 1
        : 0;
      const newPage = this.items.length === 0 ? 0 : lastPage + 1;
      const offset = newPage * this.limit;
      if (!this.items[offset]) {
        if (this.hasMore) {
          if (!this.loadingData) {
            // the default value of loading is false. when it has more data, it will be set to true and that causes the NG0100: ExpressionChangedAfterItHasBeenCheckedError. used setTimeout to avoid the error.
            setTimeout(() => (this.loadingData = true), 0);
            this.loadMore.emit({
              index: newPage,
              offset: offset,
              limit: this.limit,
            });
          }
        } else {
          let visiblePages: number[];
          if (startHeight === 0) {
            visiblePages = [0];
          } else {
            // set the last pages as the visible pages
            visiblePages = [lastPage];
            if (this.pageHeights.length > 1) visiblePages.unshift(lastPage - 1);
          }
          this.checkAndUpdateVisiblePages(visiblePages);
        }
      } else {
        const visiblePages = startHeight === 0 ? [0] : [lastPage, lastPage + 1];
        this.checkAndUpdateVisiblePages(visiblePages);
      }
      return;
    }
    // check the curruent area displays the correct page data
    if (startHeight === 0) {
      this.checkAndUpdateVisiblePages([0]);
      return;
    }
    this.checkScrollDirection(el);
    const endHeight = startHeight + el.clientHeight;
    let totalHeight = 0;
    let startPageNum = -1;
    let endPageNum = -1;
    for (let i = 0; i < this.pageHeights.length; i++) {
      totalHeight += this.pageHeights[i];
      if (startPageNum === -1 && totalHeight > startHeight) startPageNum = i;
      if (endPageNum === -1 && totalHeight > endHeight) endPageNum = i;
      if (startPageNum !== -1 && endPageNum !== -1) break;
    }
    if (startPageNum === -1) startPageNum = 0;
    if (endPageNum === -1) endPageNum = 0;
    let visiblePages: number[];
    if (this.isScrollDown) {
      visiblePages = [startPageNum];
      if (startPageNum + 1 < this.pageHeights.length)
        visiblePages.push(startPageNum + 1);
    } else {
      // scroll up
      visiblePages = [endPageNum];
      if (endPageNum - 1 >= 0) visiblePages.unshift(endPageNum - 1);
    }
    this.checkAndUpdateVisiblePages(visiblePages);
  }

  updateSpacerHeight() {
    let topHeight = 0;
    let bottomHeight = 0;
    this.pageHeights.forEach((h, i) => {
      if (i < this.visiblePages[0]) {
        topHeight += h;
      }
      if (i > this.visiblePages[this.visiblePages.length - 1]) {
        bottomHeight += h;
      }
    });
    if (this.topSpacerHeight !== topHeight) this.topSpacerHeight = topHeight;
    if (this.bottomSpacerHeight !== bottomHeight)
      this.bottomSpacerHeight = bottomHeight;
  }

  // when it is a tree list and when collapse an item, the bottom spacer height should be recalculated. so we need to remove the bottom spacer height manually.
  removeBottomSpacerHeight() {
    this.pageHeights = this.pageHeights.slice(0, this.visiblePages[0] + 1);
    this.bottomSpacerHeight = 0;
    this.handleScroll(this.containerEl);
  }

  isEndOfTheContent(el: HTMLElement) {
    const buffer = 50;
    const scrollHeight = el.scrollHeight;
    const scrollTop = el.scrollTop;
    const clientHeight = el.clientHeight;
    this.isEnd = scrollTop + clientHeight + buffer >= scrollHeight;
    return this.isEnd;
  }

  ngAfterViewInit() {
    this.handleScroll(this.containerEl);
  }

  ngOnChanges(changes: SimpleChanges) {
    const items = changes['items'];
    if (items) {
      if (this.loadingData) {
        //console.log('loading items', items);
        this.loadingData = false;
        const remainCount = items.currentValue.length % this.limit;
        if (
          items.currentValue.length === 0 ||
          (remainCount !== 0 && remainCount < this.limit)
        ) {
          this.hasMore = false;
        }
        if (this.containerEl) this.handleScroll(this.containerEl);
      } else {
        // reset the scroll position when items are new.
        // if it is not loading, it means the items are new.
        if (
          !items.isFirstChange() &&
          !arraysEqual(items.previousValue, items.currentValue)
        ) {
          this.resetScroll();
          // console.log('reset scroll', items);
        }
      }
    }
  }

  ngOnDestroy() {
    if (this.scrollSubscription) {
      this.scrollSubscription.unsubscribe();
    }
  }
}
