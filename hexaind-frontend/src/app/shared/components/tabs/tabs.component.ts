import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatTabsModule } from '@angular/material/tabs';

@Component({
  selector: 'mst-tabs',
  templateUrl: './tabs.component.html',
  styleUrls: ['./tabs.component.scss'],
  standalone: true,
  imports: [MatTabsModule, CommonModule],
})
export class TabsComponent {
  @Input() tabs: { label: string; content: any }[] = []; // Array of tab data
  @Input() selectedIndex = 0; // Index of the selected tab
  @Output() tabChanged = new EventEmitter<number>();

  onTabChange(index: number) {
    this.tabChanged.emit(index);
  }
}
