import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { filterAndSortData } from '../../utils/utils';
import { ButtonComponent } from '../button/button.component';
import {
  Column,
  Dashboard,
  DataColumn,
  Filter,
  IdNameData,
  PageInfo,
  VizData,
} from '../models';
import { SelectColumnComponent } from '../select-column/select-column.component';
import { SelectDatasetComponent } from '../select-dataset/select-dataset.component';
import { SelectFilterColumnsComponent } from '../select-filter-columns/select-filter-columns.component';
import { TableComponent } from '../table/table.component';

@Component({
  selector: 'mst-select-global-filter-columns',
  templateUrl: './select-global-filter-columns.component.html',
  styleUrls: ['./select-global-filter-columns.component.scss'],
  standalone: true,
  imports: [
    SelectFilterColumnsComponent,
    SelectColumnComponent,
    TableComponent,
    ButtonComponent,
    CommonModule,
    SelectDatasetComponent,
  ],
})
export class SelectGlobalFilterColumnsComponent {
  columnItems: IdNameData[] = [];
  columns: Column[] = [];
  rowCount = 0;
  filteredRows: any[] = [];
  selectedDataset?: IdNameData;
  selectedSourceIndex = 0;
  filters: Filter[] = [];
  vizItems: IdNameData[] = [];
  private _data: VizData = { dataset: { id: '' }, columns: [], rows: [] };
  @Input() hasMoreDatasets = false;
  @Input() set dashboard(dashboard: Dashboard | undefined) {
    this.filters = dashboard?.filters || [];
    this.vizItems =
      dashboard?.config?.rows?.reduce((items: IdNameData[], row) => {
        row.cells.forEach(({ viz }) => {
          if (viz && viz.id && viz.name) {
            items.push(viz);
          }
        });
        return items;
      }, []) || [];
  }
  @Input() selectedSourceId = '';
  @Input() sourceItems: IdNameData[] = [];
  @Input() datasetItems: IdNameData[] = [];
  @Input() set data(data: VizData) {
    data = data || { dataset: { id: '' }, columns: [], rows: [] };
    const columnItems: IdNameData[] = [];
    const columns: Column[] = [];
    data.columns.forEach(({ name, type }: DataColumn) => {
      columnItems.push({
        id: name,
        name,
        type,
        style: 'padding-left:8px',
      });
      columns.push({ field: name, name, type });
    });
    this.columnItems = columnItems;
    this.columns = columns;
    this._data = data;
    this.filteredRows = this.getFilteredRows();
  }
  get data() {
    return this._data;
  }
  @Output() load = new EventEmitter<IdNameData>();
  @Output() change = new EventEmitter<Filter[]>();
  @Output() cancel = new EventEmitter();
  @Output() dataSourceChange = new EventEmitter<{
    index: number;
    item: IdNameData;
  }>();
  @Output() dataSourceLoad = new EventEmitter<{
    pageInfo: PageInfo;
    sourceId: any;
    searchTerm: string;
  }>();
  getFilteredRows() {
    const data = filterAndSortData(this.data, this.filters);
    this.rowCount = data.rows.length;
    return data.rows;
  }
  onFilterColumnChange(e: Filter[]) {
    this.filters = e;
    this.filteredRows = this.getFilteredRows();
  }
  onApply() {
    this.change.emit(this.filters);
  }
  onCancel() {
    this.cancel.emit();
  }
  onDataSourceLoad(e: {
    pageInfo: PageInfo;
    sourceId: any;
    searchTerm: string;
  }) {
    this.dataSourceLoad.emit(e);
  }
  onDataSourceChange(e: { index: number; item: IdNameData }) {
    this.selectedSourceIndex = e.index;
    this.dataSourceChange.emit(e);
  }
  onDatasetItemClick({ item }: { index: number; item: IdNameData }) {
    this.selectedDataset = item;
    this.load.emit(item);
  }
}
