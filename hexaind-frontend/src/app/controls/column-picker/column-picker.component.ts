import { Component, Input } from '@angular/core';
import { WidgetControl } from 'src/app/controls/widget-control/widget-control';

@Component({
  selector: 'app-column-picker',
  templateUrl: './column-picker.component.html',
  styleUrls: ['./column-picker.component.less'],
})
export class ColumnPickerComponent {
  @Input() widgetControl: WidgetControl | null = null;

  toggleAllChecked: boolean = true;

  toggleAll(): void {
    // this.widgetControl!.csvHeadersWithTypes.forEach((column) => {
    //   column.checked = this.toggleAllChecked;
    // });
  }
}
