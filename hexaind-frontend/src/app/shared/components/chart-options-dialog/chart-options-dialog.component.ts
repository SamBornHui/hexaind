import {
  Component,
  EventEmitter,
  Input,
  Output,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { ButtonComponent } from '../button/button.component';
import { ChartOptionsComponent } from '../chart-options/chart-options.component';
import { VizOptions, VizType } from '../models';

@Component({
  selector: 'mst-chart-options-dialog',
  templateUrl: './chart-options-dialog.component.html',
  styleUrls: ['./chart-options-dialog.component.scss'],
  standalone: true,
  imports: [MatDialogModule, ChartOptionsComponent, ButtonComponent],
})
export class ChartOptionsDialogComponent {
  @Input() baseVizType: VizType = 'line';
  @Input() options: VizOptions = {};
  @Input() set open(open: boolean) {
    if (open) {
      this.openDialog();
    }
  }
  @Output() close = new EventEmitter();
  @Output() save = new EventEmitter<VizOptions>();
  @ViewChild('dialogTemplate') dialogTemplate!: TemplateRef<any>;

  constructor(public dialog: MatDialog) {}

  onChange(options: VizOptions) {
    this.options = options;
  }

  private openDialog() {
    const dialogRef = this.dialog.open(this.dialogTemplate, {
      disableClose: true,
    });
    dialogRef.afterClosed().subscribe(() => {
      this.close.emit();
    });
  }

  onDialogAction() {
    this.dialog.closeAll();
    this.save.emit(this.options);
  }
}
