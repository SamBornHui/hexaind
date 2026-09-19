import { type Meta, type StoryObj } from '@storybook/angular';
import { EditorComponent } from './editor.component';

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<EditorComponent> = {
  title: 'Components/Editor',
  component: EditorComponent,
};

export default meta;
type Story = StoryObj<EditorComponent>;

export const Python: Story = {
  args: {
    language: 'python',
    placeholder: 'Type Python code here...',
  },
};

export const SQLDark: Story = {
  args: {
    theme: 'dark',
    language: 'sql',
    lineNumbers: false,
    placeholder: 'Type SQL code here...',
    schema: {
      users: ['name', 'id', 'address'],
      products: ['name', 'cost', 'description'],
    },
  },
};
