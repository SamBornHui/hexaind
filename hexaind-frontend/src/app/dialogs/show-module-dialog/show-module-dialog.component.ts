import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { ModuleService } from '../../pages/data/services/module.service';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { Utils } from 'src/app/utils';

@Component({
  selector: 'app-show-module-dialog',
  templateUrl: './show-module-dialog.component.html',
  styleUrls: ['./show-module-dialog.component.less'],
})
export class ShowModuleDialogComponent {
  private searchTerms = new Subject<string>();
  searchText: string = '';
  dataSource: any;
  displayedColumns: string[] = ['name', 'type', 'created_by', 'created_at'];
  selectedRow: any;

  constructor(
    private moduleService: ModuleService,
    public dialogRef: MatDialogRef<ShowModuleDialogComponent>,
  ) {
    this.searchTerms.pipe(debounceTime(300)).subscribe((term) => {
      this.dataSource.filter = term.trim().toLowerCase();
    });
  }

  ngOnInit() {
    this.getModules();
  }

  async getModules() {
    let modules = await this.moduleService.GetModules('');
    if (modules) {
      this.dataSource = modules.modules;
    }
  }

  onRadioChange(row: any) {
    this.selectedRow = row;
  }

  onSubmit() {
    this.dialogRef.close({ success: true, module: this.selectedRow });
  }

  lastAccessedDate(date: string) {
    if (!date.endsWith('Z')) {
      date += 'Z';
      return Utils.formatDateTime(date);
    } else {
      return Utils.formatDateTime(date);
    }
  }

}
