import type { Meta, StoryObj } from '@storybook/angular';
import { IconComponent } from './icon.component';

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<IconComponent> = {
  title: 'Components/Icon',
  component: IconComponent,
  args: {
    iconName: 'add',
  },
};

export default meta;
type Story = StoryObj<IconComponent>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Primary: Story = {};
