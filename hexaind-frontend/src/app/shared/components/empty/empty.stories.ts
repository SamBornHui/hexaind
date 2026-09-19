import { Component } from '@angular/core';
import type { Meta, StoryObj } from '@storybook/angular';
import { ButtonComponent } from '../button/button.component';
import { EmptyComponent } from './empty.component';

@Component({
  selector: 'mst-empty-example',
  template: `
    <mst-empty message="No dashboards"
      ><mst-button>Create a dashboard</mst-button></mst-empty
    >
  `,
  standalone: true,
  imports: [EmptyComponent, ButtonComponent],
})
class EmptyExampleComponent {}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<EmptyExampleComponent> = {
  title: 'Components/Empty',
  component: EmptyExampleComponent,
  args: {},
};

export default meta;
type Story = StoryObj<EmptyExampleComponent>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Primary: Story = {};
