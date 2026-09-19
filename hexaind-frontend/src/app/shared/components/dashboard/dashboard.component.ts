import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatInputModule } from '@angular/material/input';
import { ButtonComponent } from '../button/button.component';
import { EmptyComponent } from '../empty/empty.component';
import {
  Dashboard,
  DashboardCell,
  DashboardCellInfo,
  DashboardRow,
  Dataset,
  DefaultDashboardRowHeight,
  ResizeInfo,
  Viz,
  VizData,
} from '../models';
import { VizPanelComponent } from '../viz-panel/viz-panel.component';

const isEmpty = (dashboard: Dashboard) => {
  const config = dashboard.config || { rows: [] };
  return (
    config.rows == null ||
    config.rows.length === 0 ||
    config.rows[0].cells.length === 0 ||
    config.rows[0].cells[0].viz?.query == null
  );
};

type Datas = (VizData | undefined)[][];

@Component({
  selector: 'mst-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatInputModule,
    VizPanelComponent,
    ButtonComponent,
    EmptyComponent,
  ],
})
export class DashboardComponent {
  isEmpty = true;

  private _config!: Dashboard;
  @Input() isFullscreen = false;
  @Input() editable = false;
  @Input() showEditButton = false;
  @Input() set config(value: Dashboard) {
    this._config = value;
    this.isEmpty = isEmpty(value);
  }
  get config() {
    return this._config;
  }
  @Input() datas: Datas = [];

  @Output() itemDrop = new EventEmitter<DashboardCellInfo>();
  @Output() vizEdit = new EventEmitter<DashboardCellInfo>();
  @Output() vizDelete = new EventEmitter<DashboardCellInfo>();
  @Output() vizResize = new EventEmitter<DashboardCellInfo>();
  @Output() update = new EventEmitter<Dashboard>();
  @Output() delete = new EventEmitter<Dashboard>();
  @Output() vizDataLoad = new EventEmitter<DashboardCellInfo>();
  @Output() cancel = new EventEmitter<Dashboard>();
  @Output() edit = new EventEmitter<Dashboard>();
  @Output() fullscreen = new EventEmitter<boolean>();

  defaultRowHeight = DefaultDashboardRowHeight;

  trackByCell(_i: number, item: DashboardCell) {
    return item.viz?.id;
  }
  trackByRow(i: number, _item: DashboardRow) {
    return i;
  }

  onItemDrop(
    e: { viz: Viz; dataset: Dataset },
    rowIndex: number,
    cellIndex: number,
  ) {
    this.isEmpty = false;
    this.itemDrop.emit({ ...e, rowIndex, cellIndex });
  }

  onVizEdit(viz: Viz, rowIndex: number, cellIndex: number) {
    this.vizEdit.emit({ viz, rowIndex, cellIndex });
  }

  onVizDelete(viz: Viz, rowIndex: number, cellIndex: number) {
    this.isEmpty =
      rowIndex === 0 &&
      cellIndex === 0 &&
      this.config.config?.rows.length === 2 &&
      this.config.config.rows[0].cells.length === 2 &&
      this.config.config.rows[1].cells.length === 1;
    this.vizDelete.emit({ viz, rowIndex, cellIndex });
  }

  onVizDataLoad(viz: Viz, rowIndex: number, cellIndex: number) {
    this.vizDataLoad.emit({ viz, rowIndex, cellIndex });
  }

  onConfigUpdate(e: Event, field: 'name' | 'description') {
    const value = (e.target as HTMLInputElement).value;
    this.config[field] = value;
  }

  onDelete() {
    this.delete.emit(this.config);
  }
  onUpdate() {
    this.update.emit(this.config);
  }
  onCancel() {
    this.cancel.emit(this.config);
  }
  onEdit() {
    this.edit.emit(this.config);
  }
  onFullscreen() {
    this.isFullscreen = !this.isFullscreen;
    this.fullscreen.emit(this.isFullscreen);
  }
  onVizResize(
    info: { viz: Viz; resizeInfo: ResizeInfo },
    rowIndex: number,
    cellIndex: number,
  ) {
    this.vizResize.emit({ ...info, rowIndex, cellIndex });
  }
}
