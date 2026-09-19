import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { type Meta, type StoryObj } from '@storybook/angular';
import { generateColumnsAndRows, loadData } from 'src/tests/mocks/mocks';
import { ListItemParentNamesComponent } from '../list-item/list-item-parent-names/list-item-parent-names.component';
import { IdNameData, PageInfo } from '../models';
import { ListComponent } from './list.component';

@Component({
  selector: 'mst-list-example',
  template: `
    <ng-template #itemWithParentNamesTemplate let-item="item">
      <mst-list-item-parent-names
        *ngIf="item.parentNames"
        [item]="item"
        separator=">"
      /><ng-container *ngIf="!item.parentNames">{{ item.name }}</ng-container>
    </ng-template>
    <mst-list
      style="width: 500px;height:500px"
      [multiSelect]="multiSelect"
      [items]="items"
      [itemTemplate]="useTemplate ? itemWithParentNamesTemplate : undefined"
      [hasMore]="hasMore"
      (loadMore)="onLoadMore($event)"
    />
  `,
  standalone: true,
  imports: [ListComponent, CommonModule, ListItemParentNamesComponent],
})
export class ListExampleComponent implements OnInit {
  hasMore = true;
  items: IdNameData[] = [];
  @Input() hasPagination = false;
  @Input() rowCount = 1000;
  @Input() multiSelect = false;
  @Input() useTemplate = false;
  ngOnInit() {
    if (this.hasPagination) {
      this.hasMore = true;
    } else {
      const { items } = generateColumnsAndRows(this.rowCount);
      this.items = items;
      this.hasMore = false;
    }
  }
  async onLoadMore(e: PageInfo) {
    const { items, isLastPage } = await loadData(e);
    this.hasMore = !isLastPage;
    const newItems = this.items.slice();
    items.forEach((item, index) => (newItems[e.offset + index] = item));
    this.items = newItems;
    console.log('loadMore', e, this.items.length, this.hasMore);
  }
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<ListExampleComponent> = {
  title: 'Components/List',
  component: ListExampleComponent,
};

export default meta;
type Story = StoryObj<ListExampleComponent>;

export const Basic: Story = {};

export const MultiSelect: Story = {
  args: {
    multiSelect: true,
  },
};

export const Pagination: Story = {
  args: {
    multiSelect: true,
    hasPagination: true,
  },
};

export const Template: Story = {
  args: {
    useTemplate: true,
  },
};
