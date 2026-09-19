import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import type { Meta, StoryObj } from '@storybook/angular';
import { LoaderComponent } from './loader.component';

@Component({
  selector: 'mst-loader-example',
  template: `<mst-loader *ngIf="!hasBlock" [diameter]="diameter" />
    <div
      style="position:relative;width:500px;height:500px;background-color:blue;border-radius:10px;text-align:center;color:white;"
      *ngIf="hasBlock"
    >
      loading data...
      <mst-loader [diameter]="diameter" />
    </div>`,
  standalone: true,
  imports: [LoaderComponent, CommonModule],
})
class LoaderExampleComponent {
  @Input() diameter = 100;
  @Input() hasBlock?: boolean;
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<LoaderExampleComponent> = {
  title: 'Components/Loader',
  component: LoaderExampleComponent,
  args: {},
};

export default meta;
type Story = StoryObj<LoaderExampleComponent>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Primary: Story = {};
export const Diameter: Story = {
  args: {
    diameter: 50,
  },
};
export const Block: Story = {
  args: {
    diameter: 50,
    hasBlock: true,
  },
};
