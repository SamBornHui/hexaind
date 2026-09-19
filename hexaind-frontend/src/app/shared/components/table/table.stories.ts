import {
  AfterViewInit,
  Component,
  Input,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { MatMenuModule } from '@angular/material/menu';
import type { Meta, StoryObj } from '@storybook/angular';
import { generateColumnsAndRows } from 'src/tests/mocks/mocks';
import { ButtonComponent } from '../button/button.component';
import { Column, IdNameData } from '../models';
import { TableComponent } from './table.component';

@Component({
  selector: 'mst-table-example',
  template: `
    <ng-template #rowMenuTemplate let-item="item" let-column="column">
      <mst-button
        styleName="icon"
        iconName="more_vert"
        [menu]="menu"
      /><mat-menu #menu>
        <button mat-menu-item (click)="onMenuClick('Item 1')">Item 1</button>
        <button mat-menu-item (click)="onMenuClick('Item 2')">Item 2</button>
      </mat-menu>
    </ng-template>
    <mst-table
      style="width: 500px;height:500px"
      [columns]="columns"
      [items]="items"
    />
  `,
  standalone: true,
  imports: [TableComponent, ButtonComponent, MatMenuModule],
})
export class TableExampleComponent implements AfterViewInit {
  items: IdNameData[] = [];
  columns: Column[] = [];
  @Input() columnCount = 10;
  @Input() rowCount = 1000;
  // We can access the template only after the view is initialized.
  @ViewChild('rowMenuTemplate') rowMenuTemplate!: TemplateRef<any>;
  ngAfterViewInit() {
    const { columns, items } = generateColumnsAndRows(
      this.rowCount,
      this.columnCount,
    );
    columns[0].hint = 'hint test';
    columns.push({
      template: this.rowMenuTemplate,
      minWidth: 50,
      maxWidth: 50,
    });
    this.columns = columns;
    this.items = items;
  }
  onMenuClick(menuName: string) {
    console.log(menuName);
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
export const Basic: Story = {};

export const ColumnVirtualScroll: Story = {
  args: {
    columnCount: 1000,
  },
};
