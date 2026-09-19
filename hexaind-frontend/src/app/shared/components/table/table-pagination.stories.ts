import { Component } from '@angular/core';
import type { Meta, StoryObj } from '@storybook/angular';
import { loadData } from 'src/tests/mocks/mocks';
import { Column, IdNameData, PageInfo } from '../models';
import { TableComponent } from './table.component';

@Component({
  selector: 'mst-table-example',
  template: `
    <mst-table
      style="width: 500px;height:500px"
      [columns]="columns"
      [items]="items"
      [hasMore]="hasMore"
      (loadMore)="onLoadMore($event)"
    />
  `,
  standalone: true,
  imports: [TableComponent],
})
export class TableExampleComponent {
  hasMore = true;
  items: IdNameData[] = [];
  columns: Column[] = [];
  async onLoadMore(e: PageInfo) {
    const { items, columns, isLastPage } = await loadData(e, 1000, 10);
    this.hasMore = !isLastPage;
    if (this.columns.length === 0) {
      this.columns = columns;
    }
    const newItems = this.items.slice();
    items.forEach((item, index) => (newItems[e.offset + index] = item));
    this.items = newItems;
    console.log('loadMore', e, this.items.length);
  }
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<TableExampleComponent> = {
  title: 'Components/Table',
  component: TableExampleComponent,
};

export default meta;
type Story = StoryObj<TableExampleComponent>;

export const Pagination: Story = {};
