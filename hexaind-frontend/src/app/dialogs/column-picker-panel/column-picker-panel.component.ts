import { Component, Output, EventEmitter, Input } from '@angular/core';
import { WidgetControl } from 'src/app/controls/widget-control/widget-control';

@Component({
  selector: 'app-column-picker-panel',
  templateUrl: './column-picker-panel.component.html',
  styleUrls: ['./column-picker-panel.component.less'],
})
export class ColumnPickerPanelComponent {
  @Input() widgetControl!: WidgetControl;
  @Output() closePanelClicked = new EventEmitter<any>();

  onClosePanel() {
    this.closePanelClicked.emit();
  }
}
