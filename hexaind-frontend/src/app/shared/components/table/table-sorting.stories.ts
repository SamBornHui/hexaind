import { Component } from '@angular/core';
import type { Meta, StoryObj } from '@storybook/angular';
import { loadData } from 'src/tests/mocks/mocks';
import { Column, IdNameData, PageInfo, SortInfo } from '../models';
import { TableComponent } from './table.component';

@Component({
  selector: 'mst-table-example',
  template: `
    <mst-table
      style="width: 500px;height:500px"
      [columns]="columns"
      [items]="items"
      [hasMore]="hasMore"
      [hasSort]="true"
      [loading]="loading"
      (loadMore)="onLoadMore($event)"
      (sort)="onSort($event)"
    />
  `,
  standalone: true,
  imports: [TableComponent],
})
export class TableExampleComponent {
  hasMore = true;
  items: IdNameData[] = [];
  columns: Column[] = [];
  sortInfo?: SortInfo;
  loading = false;
  async onLoadMore(e: PageInfo) {
    this.loading = true;
    const { items, columns, isLastPage } = await loadData(
      e,
      1000,
      10,
      this.sortInfo,
    );
    this.hasMore = !isLastPage;
    if (this.columns.length === 0) {
      this.columns = columns;
    }
    const newItems = this.items.slice();
    items.forEach((item, index) => (newItems[e.offset + index] = item));
    this.items = newItems;
    // ExpressionChangedAfterItHasBeenCheckedError
    setTimeout(() => (this.loading = false), 0);
    console.log('loadMore', e, this.items.length);
  }
  onSort(sortInfo: SortInfo) {
    // this example sorts only the first page(50 items)
    this.sortInfo = sortInfo;
    this.onLoadMore({ index: 0, offset: 0, limit: 50 });
  }
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<TableExampleComponent> = {
  title: 'Components/Table',
  component: TableExampleComponent,
};

export default meta;
type Story = StoryObj<TableExampleComponent>;

export const Sorting: Story = {};
