import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ModuleImportService } from './module-import.service';

@Component({
  selector: 'app-module-import-dialog',
  templateUrl: './module-import-dialog.component.html',
  styleUrls: ['./module-import-dialog.component.less'],
})
export class ModuleImportDialogComponent {
  name: string = '';
  description: string = '';
  isDisabled: boolean = false;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<ModuleImportDialogComponent>,
    public moduleImportService: ModuleImportService,
  ) {}

  ngOnInit() {}

  onSubmit() {
    this.isDisabled = true;
    const queryParams = {
      name: this.name,
      description: this.description,
      file_type: this.data.file_type,
      siteId: '1',
      projectId: '1',
    };
    if (this.data.destination_folder && this.data.destination_folder !== undefined && this.data.destination_folder != '') {
      (queryParams as any)['destination_folder'] = this.data.destination_folder;
    }
    const formData: any = new FormData();
    formData.append('file', this.data.file);

    this.moduleImportService
      .importModule(queryParams, formData)
      .subscribe((res: any) => {
        if (res?.module_id && res['module_id'] != '')
          this.dialogRef.close({ success: true, module_id:res['module_id'] });
        else if (res?.detail && res.status != 200)
          this.dialogRef.close({ success: false, error: res['detail'] });
        this.isDisabled = false;
      });
  }
  disabledSubmit() {
    if (this.isDisabled) return true;
    return this.name == '' ? true : false;
  }
}
