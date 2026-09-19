import { Component, Input, OnInit } from '@angular/core';
import type { Meta, StoryObj } from '@storybook/angular';
import { generateNestedArray } from 'src/tests/mocks/mocks';
import { flattenNestedArray } from '../../utils/utils';
import { Column, TreeData } from '../models';
import { TreeTableComponent } from './tree-table.component';

@Component({
  selector: 'mst-tree-table-example',
  template: `<mst-tree-table
    [collapsedAll]="collapsedAll"
    [columns]="columns"
    [items]="items"
  />`,
  standalone: true,
  imports: [TreeTableComponent],
})
export class TreeTableExampleComponent implements OnInit {
  items: TreeData[] = [];
  columns: Column[] = [];
  @Input() collapsedAll = false;
  ngOnInit(): void {
    const items = flattenNestedArray(generateNestedArray(10));
    this.columns = Object.keys(items[0]).map((key) => ({
      name: key,
      field: key,
    }));
    this.items = items;
  }
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<TreeTableExampleComponent> = {
  title: 'Components/TreeTable',
  component: TreeTableExampleComponent,
};

export default meta;
type Story = StoryObj<TreeTableExampleComponent>;

export const Primary: Story = {};
export const CollapsedAll: Story = {
  args: {
    collapsedAll: true,
  },
};
