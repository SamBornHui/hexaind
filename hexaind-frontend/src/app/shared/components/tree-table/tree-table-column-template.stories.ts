import {
  AfterViewInit,
  Component,
  Input,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { MatMenuModule } from '@angular/material/menu';
import type { Meta, StoryObj } from '@storybook/angular';
import { generateNestedArray } from 'src/tests/mocks/mocks';
import { flattenNestedArray } from '../../utils/utils';
import { ButtonComponent } from '../button/button.component';
import { Column, RowMeta, TreeData } from '../models';
import { TreeTableComponent } from './tree-table.component';

const iconMap = new Map<string, string>([
  ['workflow', 'account_tree'],
  ['run', 'content_copy'],
  ['widget', 'widget_small'],
  ['output', 'article'],
]);

@Component({
  selector: 'mst-tree-table-example',
  template: `<ng-template #rowMenuTemplate let-item="item" let-column="column">
      <mst-button
        styleName="icon"
        iconName="more_vert"
        [menu]="menu"
      /><mat-menu #menu>
        <button mat-menu-item (click)="onMenuClick('Item 1')">Item 1</button>
        <button mat-menu-item (click)="onMenuClick('Item 2')">Item 2</button>
      </mat-menu> </ng-template
    ><mst-tree-table
      [collapsedAll]="collapsedAll"
      [columns]="columns"
      [items]="items"
    />`,
  standalone: true,
  imports: [TreeTableComponent, ButtonComponent, MatMenuModule],
})
export class TreeTableExampleComponent implements AfterViewInit {
  items: TreeData[] = [];
  columns: Column[] = [];
  @Input() collapsedAll = false;
  @ViewChild('rowMenuTemplate') rowMenuTemplate!: TemplateRef<any>;
  // We can access the template only after the view is initialized.
  ngAfterViewInit(): void {
    const items = flattenNestedArray(generateNestedArray(10));
    const columns: Column[] = Object.keys(items[0]).map((key) => ({
      name: key,
      field: key,
    }));
    columns.push({
      template: this.rowMenuTemplate,
      minWidth: 50,
      maxWidth: 50,
    });
    this.columns = columns;
    const widgetRowMeta: RowMeta = {
      colSpans: [
        {
          index: 1,
          count: 3,
        },
      ],
    };
    this.items = items.map((item, i) => ({
      ...item,
      iconName: iconMap.get(item.nodeType) || 'description',
      _rowMeta: item.nodeType === 'output' ? widgetRowMeta : undefined,
    }));
  }
  onMenuClick(menuName: string) {
    console.log(menuName);
  }
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<TreeTableExampleComponent> = {
  title: 'Components/TreeTable',
  component: TreeTableExampleComponent,
};

export default meta;
type Story = StoryObj<TreeTableExampleComponent>;

export const ColumnTemplate: Story = {};
