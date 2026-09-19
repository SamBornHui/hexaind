import { Component } from '@angular/core';
import type { Meta, StoryObj } from '@storybook/angular';
import { generateColumnsAndRows } from 'src/tests/mocks/mocks';
import { CellChangeInfo, Column, IdNameData } from '../models';
import { TableComponent } from './table.component';

const { columns, items } = generateColumnsAndRows(500, 20);

// columnPagination should be false, since when inputing tab or enter, it moves to the next editable cell. If there is no cell because the next page is not loaded, it will lose focus. However, if you want to edit a cell with clicking a cell, we can use the column pagination.
@Component({
  selector: 'mst-table-example',
  template: `
    <mst-table
      [columns]="columns"
      [items]="items"
      [columnPagination]="false"
      (change)="onCellChange($event)"
    />
  `,
  standalone: true,
  imports: [TableComponent],
})
export class TableExampleComponent {
  items: IdNameData[] = items;
  columns: Column[] = columns.map((column) => ({ ...column, editable: true }));
  onCellChange(e: CellChangeInfo) {
    console.log(e);
  }
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<TableExampleComponent> = {
  title: 'Components/Table',
  component: TableExampleComponent,
};

export default meta;
type Story = StoryObj<TableExampleComponent>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Edit: Story = {};
