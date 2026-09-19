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
import { ListComponent } from '../list/list.component';
import { Dashboard, Filter, IdNameData } from '../models';
import { SelectVizItemsComponent } from '../select-viz-items/select-viz-items.component';

// Chart-specific filters are not global.  Applying a chart filter that duplicates an existing global filter's criteria will result in redundant global filters, as the system cannot differentiate them.

@Component({
  selector: 'mst-global-filter',
  templateUrl: './global-filter.component.html',
  styleUrls: ['./global-filter.component.scss'],
  standalone: true,
  imports: [
    ButtonComponent,
    ListComponent,
    MatDialogModule,
    SelectVizItemsComponent,
  ],
})
export class GlobalFilterComponent {
  filter?: Filter;
  selectedFitlerIndex = -1;
  filterItems: IdNameData[] = [];
  vizItems: IdNameData[] = [];
  filters: Filter[] = [];
  @Input() set dashboard(dashboard: Dashboard | undefined) {
    this.filters = dashboard?.filters || [];
    this.filterItems = this.filters.map((filter, i) => ({
      id: i.toString(),
      name: filter.field,
      data: filter,
    }));
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
  @Output() edit = new EventEmitter<Filter[]>();
  @Output() change = new EventEmitter<Filter[]>();
  @ViewChild('dialogTemplate') dialogTemplate!: TemplateRef<any>;
  constructor(public dialog: MatDialog) {}
  onEditClick() {
    this.edit.emit(this.filters);
  }
  onSelectedIdsChange({
    global,
    selectedIds,
  }: {
    global: boolean;
    selectedIds: string[];
  }) {
    if (this.filter) {
      this.filter.global = global;
      this.filter.targetIds = selectedIds;
    }
  }
  onIconClick(e: { item: IdNameData; index: number; name: string }) {
    this.openDialog(e);
  }
  onDialogAction() {
    this.filters[this.selectedFitlerIndex] = this.filter!;
    this.dialog.closeAll();
    this.change.emit(this.filters);
  }
  private openDialog(e: { item: IdNameData; index: number; name: string }) {
    this.selectedFitlerIndex = e.index;
    this.filter = e.item['data'];
    this.dialog.open(this.dialogTemplate);
  }
}
