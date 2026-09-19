import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { type Meta, type StoryObj } from '@storybook/angular';
import { ButtonComponent } from './button.component';

@Component({
  selector: 'mst-button-example',
  template: `<mst-button
      [styleName]="styleName"
      [iconName]="iconName"
      [menu]="hasMenu ? menu : undefined"
      >Button</mst-button
    ><mat-menu #menu>
      <button mat-menu-item>Item 1</button>
      <button mat-menu-item>Item 2</button>
    </mat-menu>`,
  standalone: true,
  imports: [ButtonComponent, CommonModule, MatButtonModule, MatMenuModule],
})
class ButtonExampleComponent {
  @Input() styleName = 'stroked';
  @Input() iconName = '';
  @Input() hasMenu = false;
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<ButtonExampleComponent> = {
  title: 'Components/Button',
  component: ButtonExampleComponent,
};

export default meta;
type Story = StoryObj<ButtonExampleComponent>;

export const Default: Story = {};
export const Flat: Story = {
  args: {
    styleName: 'flat',
  },
};
export const Raised: Story = {
  args: {
    styleName: 'raised',
  },
};
export const Icon: Story = {
  args: {
    styleName: 'icon',
    iconName: 'add',
  },
};
export const Menu: Story = {
  args: {
    styleName: 'menu',
    iconName: 'more_vert',
    hasMenu: true,
  },
};
