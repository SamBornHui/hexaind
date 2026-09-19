import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  Input,
  Output,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import {
  MatDialog,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { ButtonComponent } from '../button/button.component';
import { ListComponent } from '../list/list.component';
import { IdNameData } from '../models';

@Component({
  selector: 'mst-drop-list',
  templateUrl: './drop-list.component.html',
  styleUrls: ['./drop-list.component.scss'],
  standalone: true,
  imports: [CommonModule, ListComponent, MatDialogModule, ButtonComponent],
})
export class DropListComponent {
  private dialogRef!: MatDialogRef<any>;
  private selectedIconInfo?: { item: IdNameData; index: number; name: string };
  @Input() droppable = true;
  @Input() items: IdNameData[] = [];
  @Input() rightIconNames: string[] = ['delete'];
  @Input() name = '';
  @Input() placeholder = 'Drop item here';
  @Input() keepBottomBorder = false;
  @Input() itemTemplate?: TemplateRef<any>;
  @Output() iconClick = new EventEmitter<{
    item: IdNameData;
    index: number;
    name: string;
  }>();
  @Output() drop = new EventEmitter<string>();
  @ViewChild('dialogTemplate') dialogTemplate!: TemplateRef<any>;
  constructor(public dialog: MatDialog) {}
  onDragOver(event: DragEvent) {
    event.preventDefault();
    if (!this.droppable) return;
    const el = event.currentTarget as HTMLElement;
    el.classList.add('dragover');
  }
  onDragLeave(event: DragEvent) {
    if (!this.droppable) return;
    const el = event.currentTarget as HTMLElement;
    el.classList.remove('dragover');
  }
  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    if (!this.droppable) return;
    const el = event.currentTarget as HTMLElement;
    el.classList.remove('dragover');
    const id = JSON.parse(
      event.dataTransfer?.getData('application/json') || '{}',
    ).id;
    this.drop.emit(id);
  }
  onIconClick(e: { item: IdNameData; index: number; name: string }) {
    if (e.name === 'delete') this.openDialog(e);
    else this.iconClick.emit(e);
  }
  private openDialog(e: { item: IdNameData; index: number; name: string }) {
    this.selectedIconInfo = e;
    this.dialogRef = this.dialog.open(this.dialogTemplate, {
      disableClose: true,
    });
  }
  onDialogAction() {
    this.dialogRef.close();
    this.iconClick.emit(this.selectedIconInfo);
    this.selectedIconInfo = undefined;
  }
}
