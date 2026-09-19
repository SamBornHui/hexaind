import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  HostBinding,
  Input,
  Output,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { ButtonComponent } from '../button/button.component';
import { DashboardComponent } from '../dashboard/dashboard.component';
import { EmptyComponent } from '../empty/empty.component';
import { FileUploadComponent } from '../file-upload/file-upload.component';
import { GlobalFilterComponent } from '../global-filter/global-filter.component';
import { ListComponent } from '../list/list.component';
import {
  Dashboard,
  DashboardCell,
  DashboardCellInfo,
  DashboardConfig,
  DashboardRow,
  DataColumn,
  Datas,
  Dataset,
  DefaultDashboardRowHeight,
  Direction,
  Filter,
  IdNameData,
  PageInfo,
  Viz,
  VizData,
} from '../models';
import { SelectDatasetComponent } from '../select-dataset/select-dataset.component';
import { SelectGlobalFilterColumnsComponent } from '../select-global-filter-columns/select-global-filter-columns.component';
import { VizDataConfigComponent } from '../viz-data-config/viz-data-config.component';

const getEmptyCell = (): DashboardCell => ({
  viz: { id: '', name: '' },
});

export const getEmptyDashboard = (): Dashboard => ({
  id: '',
  name: 'My dashboard',
  description: 'My dashboard description',
});

const addEmptyCellsAndReturnOriginalConfig = (dashboard: Dashboard) => {
  // need to add an empty cell if the last cell is not empty
  const origin = structuredClone(dashboard);
  const config: DashboardConfig =
    dashboard.config == null || dashboard.config.rows == null
      ? {
          rows: [{ cells: [getEmptyCell()] }],
        }
      : dashboard.config;
  if (dashboard.config && dashboard.config.rows) {
    config?.rows.forEach((row) => {
      if (row.cells[row.cells.length - 1]?.viz?.type) {
        row.cells.push(getEmptyCell());
      }
    });
    // If the last row has only one cell and the cell has no columns, it is a row with an empty cell. We don't need to add an empty row again.
    if (
      !(
        config.rows[config.rows.length - 1].cells.length === 1 &&
        !config.rows[config.rows.length - 1].cells[0].viz?.type
      )
    ) {
      config.rows.push({ cells: [getEmptyCell()] });
    }
  }
  dashboard.config = config;
  return origin;
};

const removeData = (datas: Datas) => {
  // remove all data and keep the reference. When this.datas = [], it is not the original datas, so it is disconnected from the original datas and the change detection will not work.
  datas.splice(0, datas.length);
};

const deleteEmptyCells = (dashboard: Dashboard) => {
  // if it is a new dashboard, temp viz id should be removed.
  const rows = dashboard.config?.rows || [];
  const lastRow = rows[rows.length - 1];
  if (lastRow.cells.length === 1 && !lastRow.cells[0].viz?.config) {
    rows.pop();
  }
  // delete empty cells
  rows.forEach((row) => {
    const cells: DashboardCell[] = [];
    row.cells.forEach((cell) => {
      if (cell.viz?.query?.dataset) {
        cells.push(cell);
      }
    });
    row.cells = cells;
  });
  return dashboard;
};

const getNewViz = (dataset?: Dataset): Viz => {
  return {
    id: '',
    name: dataset?.name,
    type: 'table',
    query: { dataset },
    description: '',
    config: {},
  };
};

const updateCellFlex = (
  el: HTMLElement,
  rowIndex: number,
  cellIndex: number,
  row: DashboardRow,
  direction: Direction,
  delta: number,
) => {
  const cellEls = Array.from(
    el.querySelectorAll(
      '.mst-dashboard__body__row--' +
        rowIndex +
        ' .mst-dashboard__body__row__cell',
    ),
  );
  // the last cell is empty, so it should be removed.
  cellEls.pop();
  if (cellEls.length > 1) {
    const widths = cellEls.map((cell) => (cell as HTMLElement).clientWidth);
    const width = widths[cellIndex];
    widths[cellIndex] =
      direction === 'left' ? width + -1 * delta : width + delta;
    const smallestWidth = Math.min(...widths);
    const flexes = widths.map((w) => w / smallestWidth);
    row.cells.forEach((cell, i) => {
      cell.flex = flexes[i];
    });
  }
};

@Component({
  selector: 'mst-dashboard-editor',
  templateUrl: './dashboard-editor.component.html',
  styleUrls: ['./dashboard-editor.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ListComponent,
    DashboardComponent,
    VizDataConfigComponent,
    MatDialogModule,
    ButtonComponent,
    EmptyComponent,
    FileUploadComponent,
    SelectGlobalFilterColumnsComponent,
    GlobalFilterComponent,
    SelectDatasetComponent,
  ],
})
export class DashboardEditorComponent {
  private originSelectedDashboard?: Dashboard;
  private _datasetSources: IdNameData[] = [];
  isFullscreen = false;
  dialogData!: { type: 'delete' | 'cancel'; message: string };
  showVizEditor = false;
  selectedVizInfo!: DashboardCellInfo;
  editable = false;
  showEditButton = true;
  selectedDashboard?: Dashboard;
  showGlobalFilterEditor = false;
  selectedDatasetSourceId = '';
  selectedDatasetSourceIndex = 0;

  @Input() set selectedDashboardInfo({
    dashboard,
    editable = false,
  }: {
    dashboard?: Dashboard;
    editable?: boolean;
  }) {
    if (dashboard) {
      this.selectedDashboard = dashboard;
      if (editable) {
        this.onEdit();
      }
    }
  }
  @Input() set vizInfo(vizInfo: DashboardCellInfo | undefined) {
    if (vizInfo) this.updateVizInfo(vizInfo);
  }
  @Input() dashboards: Dashboard[] = [];
  @Input() set datasetSources(datasetSources: IdNameData[]) {
    this._datasetSources = datasetSources;
    this.selectedDatasetSourceId = datasetSources[0].id || '';
  }
  get datasetSources() {
    return this._datasetSources;
  }
  @Input() datasetDatas: Dataset[][] = [];
  @Input() hasMoreDatasets = true;
  @Input() configVizData?: VizData;
  @Input() datas: Datas = [];
  @Input() globalFilterDatasetData?: VizData;
  @Input() fileUpload = false;
  @Input() hasMoreDashboards = true;
  @Output() dataSourceLoad = new EventEmitter<{
    pageInfo: PageInfo;
    sourceId: any;
    searchTerm: string;
  }>();
  @Output() itemDrop = new EventEmitter<DashboardCellInfo>();
  @Output() vizUpdate = new EventEmitter<{
    cellInfo: DashboardCellInfo;
    columns: DataColumn[];
  }>();
  @Output() vizDelete = new EventEmitter<{
    cellInfo: DashboardCellInfo;
    datas: Datas;
  }>();
  @Output() vizDataLoad = new EventEmitter<DashboardCellInfo>();
  @Output() configVizDataLoad = new EventEmitter<DashboardCellInfo>();
  @Output() globalFilterDatasetDataLoad = new EventEmitter<Dataset>();
  @Output() update = new EventEmitter<Dashboard>();
  @Output() create = new EventEmitter<void>();
  @Output() delete = new EventEmitter<Dashboard>();
  @Output() cancel = new EventEmitter<Dashboard>();
  @Output() filesSelected = new EventEmitter<File[]>();
  @Output() dashboardsLoad = new EventEmitter<PageInfo>();
  @Output() vizCreate = new EventEmitter<DashboardCellInfo>();

  @ViewChild('dialogTemplate') dialogTemplate!: TemplateRef<any>;
  @HostBinding('class.mst-shared-fullscreen') get fullscreen() {
    return this.isFullscreen;
  }

  deleteVizData(rowIndex: number, cellIndex: number, removeSlot = false) {
    // delete data
    this.datas[rowIndex] = this.datas[rowIndex] || [];
    if (removeSlot) {
      this.datas[rowIndex].splice(cellIndex, 1);
    } else this.datas[rowIndex][cellIndex] = undefined;
  }

  updateVizInfo(e: DashboardCellInfo) {
    if (!this.selectedDashboard) return;
    const { rowIndex = 0, cellIndex = 0, viz } = e;
    const config = this.selectedDashboard.config || { rows: [] };
    let cell = config.rows[rowIndex].cells[cellIndex];
    cell = {
      ...cell,
      viz,
    };
    config.rows[rowIndex].cells[cellIndex] = cell;
    this.deleteVizData(rowIndex, cellIndex);
    // add empty cell
    if (config.rows[rowIndex].cells.length - 1 === cellIndex) {
      config.rows[rowIndex].cells.push(getEmptyCell());
    }
    if (config.rows.length - 1 === rowIndex) {
      config.rows.push({ cells: [getEmptyCell()] });
    }
    this.selectedDashboard.config = config;
  }
  onItemDrop(e: DashboardCellInfo) {
    // TODO: create a chart with API and update the selected Dashboard. When canceling edit, the created charts should be deleted.
    // this.updateVizInfo(e);
    // this.itemDrop.emit(e);
    this.vizCreate.emit(e);
  }
  onVizDatasetChange(e: DashboardCellInfo) {
    this.selectedVizInfo = {
      ...this.selectedVizInfo,
      viz: getNewViz(e.dataset),
    };
    this.configVizData = undefined;
  }
  onVizEdit(e: DashboardCellInfo) {
    this.selectedVizInfo = e;
    this.configVizData = this.datas[e.rowIndex][e.cellIndex];
    this.showVizEditor = !this.showVizEditor;
  }
  onVizChange(viz: Viz) {
    if (!this.selectedDashboard || !this.selectedDashboard.config) return;
    const { rowIndex, cellIndex } = this.selectedVizInfo;
    let cell = this.selectedDashboard.config.rows[rowIndex].cells[cellIndex];
    cell = { ...cell, viz };
    this.selectedDashboard.config.rows[rowIndex].cells[cellIndex] = cell;
    this.datas[rowIndex][cellIndex] = this.configVizData;
    this.showVizEditor = false;
    this.vizUpdate.emit({
      cellInfo: { rowIndex, cellIndex, viz },
      columns: this.configVizData?.columns || [],
    });
  }

  onVizDelete(e: DashboardCellInfo) {
    if (!this.selectedDashboard || !this.selectedDashboard.config) return;
    const { rowIndex, cellIndex } = e;
    const cells = [...this.selectedDashboard.config.rows[rowIndex].cells];
    cells.splice(cellIndex, 1);
    this.selectedDashboard.config.rows[rowIndex].cells = cells;
    // if the next row is empty, the row should be deleted.
    const rows = this.selectedDashboard.config.rows;
    if (cells.length === 1 && rows[rowIndex + 1].cells.length === 1) {
      rows.splice(rowIndex + 1, 1);
      this.selectedDashboard.config.rows = rows;
    }
    // delete data
    this.deleteVizData(rowIndex, cellIndex, true);
    // if this.datas doesn't refer to the original datas, the original datas should be updated.
    this.vizDelete.emit({ cellInfo: e, datas: this.datas });
  }
  onVizDataLoad(e: DashboardCellInfo) {
    this.vizDataLoad.emit(e);
  }
  onConfigVizDataLoad(e: DashboardCellInfo) {
    this.configVizDataLoad.emit(e);
  }
  onGlobalFilterDatasetDataLoad(e: Dataset) {
    this.globalFilterDatasetDataLoad.emit(e);
  }
  onDialogAction() {
    switch (this.dialogData.type) {
      case 'delete':
        const db = structuredClone(this.selectedDashboard);
        this.selectedDashboard = undefined;
        this.delete.emit(db);
        removeData(this.datas);
        break;
      case 'cancel':
        this.selectedDashboard = this.originSelectedDashboard;
        this.originSelectedDashboard = undefined;
        this.cancel.emit(this.selectedDashboard);
        break;
    }
    this.dialog.closeAll();
    this.showEditButton = true;
    this.editable = false;
  }

  onDelete() {
    this.dialogData = {
      type: 'delete',
      message: 'Delete this dashboard?',
    };
    this.dialog.open(this.dialogTemplate);
  }
  onCancel() {
    this.dialogData = {
      type: 'cancel',
      message: 'Cancel changes?',
    };
    this.dialog.open(this.dialogTemplate);
  }
  onVizCancel() {
    this.showVizEditor = false;
  }
  onUpdate(dashboard: Dashboard) {
    this.showEditButton = true;
    this.editable = false;
    this.update.emit(deleteEmptyCells(dashboard));
  }
  onEdit() {
    if (!this.selectedDashboard) return;
    // when it has previous dashboard after creating it, it doesn't update the dashboard so it will has `update` button.
    this.selectedDashboard = structuredClone(this.selectedDashboard);
    this.originSelectedDashboard = addEmptyCellsAndReturnOriginalConfig(
      this.selectedDashboard,
    );
    this.showEditButton = false;
    this.editable = true;
  }

  onCreate() {
    removeData(this.datas);
    this.create.emit();
  }

  onSelect({ item }: { item: IdNameData }) {
    const dashboard = this.dashboards.find((d) => d.id === item.id);
    if (dashboard) {
      removeData(this.datas);
      this.selectedDashboard = structuredClone(dashboard);
    }
  }

  onFullscreen(isFullscreen: boolean) {
    this.isFullscreen = isFullscreen;
  }

  onFilesSelected(files: File[]) {
    this.filesSelected.emit(files);
  }

  onEditFilter() {
    this.showGlobalFilterEditor = true;
  }
  onFilterApply(filters: Filter[]) {
    // reload
    const dashboard = {
      ...this.selectedDashboard!,
      filters,
    };
    this.selectedDashboard = this.editable
      ? dashboard
      : structuredClone(dashboard);
    this.showGlobalFilterEditor = false;
    if (!this.editable) this.onUpdate(this.selectedDashboard!);
  }
  onFilterCancel() {
    this.showGlobalFilterEditor = false;
  }
  onDatasetSourceChange(e: { index: number; item: IdNameData }) {
    this.selectedDatasetSourceIndex = e.index;
  }
  onDashboardsLoad(e: PageInfo) {
    this.dashboardsLoad.emit(e);
  }
  onDataSourceLoad(e: {
    pageInfo: PageInfo;
    sourceId: any;
    searchTerm: string;
  }) {
    this.dataSourceLoad.emit(e);
  }
  onVizResize({ resizeInfo, cellIndex, rowIndex }: DashboardCellInfo) {
    if (!this.selectedDashboard?.config || !resizeInfo) return;
    const { delta, direction } = resizeInfo;
    const row = this.selectedDashboard.config.rows[rowIndex];
    row.height = row.height || DefaultDashboardRowHeight;
    switch (direction) {
      case 'right':
      case 'left':
        updateCellFlex(
          this.el.nativeElement,
          rowIndex,
          cellIndex,
          row,
          direction,
          delta,
        );
        break;
      case 'top':
      case 'bottom':
        row.height += direction === 'top' ? -1 * delta : delta;
        break;
    }
    this.selectedDashboard.config.rows[rowIndex] = row;
  }
  constructor(
    public dialog: MatDialog,
    private el: ElementRef,
  ) {}
}
