import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { type Meta, type StoryObj } from '@storybook/angular';
import { generateColumnsAndRows, loadData } from 'src/tests/mocks/mocks';
import { IdNameData, PageInfo } from '../models';
import { VirtualScrollComponent } from './virtual-scroll.component';

@Component({
  selector: 'mst-virtual-scroll-example',
  template: `<ng-template #page let-startIndex="startIndex">
      <div
        [style.line-height.px]="32"
        *ngFor="
          let item of items | slice: startIndex : startIndex + 50;
          let i = index
        "
      >
        Index: {{ i + startIndex }}, Item: {{ item['name'] }}
      </div>
    </ng-template>
    <div style="width: 500px; height: 500px;position:relative;">
      <div
        mstVirtualScroll
        style="height:100%;overflow:auto;"
        [pageTemplate]="page"
        [items]="items"
        [hasMore]="hasMore"
        (loadMore)="onLoadMore($event)"
      ></div>
    </div>`,
  standalone: true,
  imports: [VirtualScrollComponent, CommonModule],
})
export class VirtualScrollExampleComponent implements OnInit {
  hasMore = true;
  loading = true;
  items: IdNameData[] = [];
  @Input() hasPagination = false;
  ngOnInit() {
    if (this.hasPagination) {
      this.hasMore = true;
    } else {
      this.items = generateColumnsAndRows(1000).items;
      this.loading = false;
      this.hasMore = false;
    }
  }
  async onLoadMore(e: PageInfo) {
    const { items, isLastPage } = await loadData(e);
    this.hasMore = !isLastPage;
    const newItems = this.items.slice();
    items.forEach((item, index) => (newItems[e.offset + index] = item));
    this.items = newItems;
    console.log('loadMore', e, this.items.length);
  }
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<VirtualScrollExampleComponent> = {
  title: 'Components/VirtualScroll',
  component: VirtualScrollExampleComponent,
};

export default meta;
type Story = StoryObj<VirtualScrollExampleComponent>;

export const Basic: Story = {};

export const Pagination: Story = {
  args: {
    hasPagination: true,
  },
};
