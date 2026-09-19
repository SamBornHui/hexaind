import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'app-context-menu',
  templateUrl: './context-menu.component.html',
  styleUrls: ['./context-menu.component.less'],
})
export class ContextMenuComponent {
  @Output() viewClick = new EventEmitter<void>();
  @Output() disableClick = new EventEmitter<void>();

  onViewClick(): void {
    this.viewClick.emit();
  }

  onDisableClick(): void {
    this.disableClick.emit();
  }
}
