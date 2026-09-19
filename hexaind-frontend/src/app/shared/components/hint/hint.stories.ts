import type { Meta, StoryObj } from '@storybook/angular';
import { HintComponent } from './hint.component';

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<HintComponent> = {
  title: 'Components/Hint',
  component: HintComponent,
  args: {
    hint: 'This is a hint',
  },
};

export default meta;
type Story = StoryObj<HintComponent>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Primary: Story = {};
