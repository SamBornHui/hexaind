import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { type Meta, type StoryObj } from '@storybook/angular';
import { getCitiesByState } from 'src/tests/mocks/cities';
import { ListComponent } from '../list/list.component';
import { IdNameData } from '../models';
import { DrawerComponent } from './drawer.component';

@Component({
  selector: 'mst-drawer-example',
  template: `
    <button (click)="onToggleClick()">
      <ng-container *ngIf="!isOpen">Open</ng-container
      ><ng-container *ngIf="isOpen">Close</ng-container>
    </button>
    <mst-drawer
      title="My Right Side Drawer"
      [isOpen]="isOpen"
      (isOpenChange)="onIsOpenChange($event)"
      ><mst-list [items]="items"
    /></mst-drawer>
  `,
  standalone: true,
  imports: [CommonModule, DrawerComponent, ListComponent],
})
export class DrawerExampleComponent {
  items = getCitiesByState('US', 'California', false) as IdNameData[];
  isOpen = false;
  onToggleClick() {
    this.isOpen = !this.isOpen;
  }
  onIsOpenChange(isOpen: boolean) {
    this.isOpen = isOpen;
  }
}

const meta: Meta<DrawerExampleComponent> = {
  title: 'Components/Drawer',
  component: DrawerExampleComponent,
  args: {},
};

export default meta;
type Story = StoryObj<DrawerExampleComponent>;

export const Primary: Story = {};
