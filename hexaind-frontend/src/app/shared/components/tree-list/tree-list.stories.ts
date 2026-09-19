import { Component, Input, OnInit } from '@angular/core';
import type { Meta, StoryObj } from '@storybook/angular';
import { generateNestedArray } from 'src/tests/mocks/mocks';
import { flattenNestedArray } from '../../utils/utils';
import { IdNameTreeData } from '../models';
import { TreeListComponent } from './tree-list.component';

@Component({
  selector: 'mst-tree-list-example',
  template: `<mst-tree-list [collapsedAll]="collapsedAll" [items]="items" />`,
  standalone: true,
  imports: [TreeListComponent],
})
export class TreeListExampleComponent implements OnInit {
  items: IdNameTreeData[] = [];
  @Input() collapsedAll = false;
  ngOnInit(): void {
    this.items = flattenNestedArray(generateNestedArray(10));
  }
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<TreeListExampleComponent> = {
  title: 'Components/TreeList',
  component: TreeListExampleComponent,
};

export default meta;
type Story = StoryObj<TreeListExampleComponent>;

export const Primary: Story = {};
export const CollapsedAll: Story = {
  args: {
    collapsedAll: true,
  },
};
