import { Component } from '@angular/core';
import type { Meta, StoryObj } from '@storybook/angular';
import { TabsComponent } from './tabs.component';

@Component({
  selector: 'mst-tabs-example',
  template: `<mst-tabs
      [tabs]="[
        { label: 'Datasets', content: tab1Content },
        { label: 'Workflows', content: tab2Content }
      ]"
    />
    <ng-template #tab1Content> Tab1 contents </ng-template>
    <ng-template #tab2Content> Tab2 contents </ng-template>`,
  standalone: true,
  imports: [TabsComponent],
})
export class TabsExampleComponent {}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<TabsExampleComponent> = {
  title: 'Components/Tabs',
  component: TabsExampleComponent,
};

export default meta;
type Story = StoryObj<TabsExampleComponent>;

export const Primary: Story = {};
