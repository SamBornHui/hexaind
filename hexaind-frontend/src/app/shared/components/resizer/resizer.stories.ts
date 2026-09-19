import { Component } from '@angular/core';
import type { Meta, StoryObj } from '@storybook/angular';
import { ResizeInfo } from '../models';
import { ResizerComponent } from './resizer.component';

@Component({
  selector: 'mst-resizer-example',
  template: ` <div
    style="position:relative;border-radius:10px;text-align:center;color:white;border:1px solid black;"
    [style.width.px]="width"
    [style.height.px]="height"
  >
    <mst-resizer (resize)="onResize($event)" />
  </div>`,
  standalone: true,
  imports: [ResizerComponent],
})
class ResizerExampleComponent {
  width = 500;
  height = 500;
  onResize({ delta, direction }: ResizeInfo) {
    if (direction === 'left' || direction === 'right') {
      this.width += direction === 'left' ? -1 * delta : delta;
    } else {
      this.height += direction === 'top' ? -1 * delta : delta;
    }
  }
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<ResizerExampleComponent> = {
  title: 'Components/Resizer',
  component: ResizerExampleComponent,
  args: {},
};

export default meta;
type Story = StoryObj<ResizerExampleComponent>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Primary: Story = {};
