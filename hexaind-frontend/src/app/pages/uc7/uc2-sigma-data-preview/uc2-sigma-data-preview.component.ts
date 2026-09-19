import { Component, Inject, Optional } from '@angular/core';
import { DataCatalogService } from '../../tools/data-catalog/data-catalog.service';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from '@angular/material/dialog';
import { DataPreviewComponent } from 'src/app/dialogs/data-preview/data-preview.component';
import { AddToDatasetComponent } from '../add-to-dataset/add-to-dataset.component';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-uc2-sigma-data-preview',
  templateUrl: './uc2-sigma-data-preview.component.html',
  styleUrls: ['./uc2-sigma-data-preview.component.less'],
})
export class UC2SigmaDataPreviewComponent {
  listOfFilePaths: any;
  selectedFilePath: any;
  selectAll: boolean = false;
  selectedFilePaths: any = {};
  dialogTitle: any;
  constructor(
    private dataCatService: DataCatalogService,
    @Optional() private dialogRef: MatDialogRef<UC2SigmaDataPreviewComponent>,
    private dialog: MatDialog,
    private toaster: ToastrService,
    @Optional() @Inject(MAT_DIALOG_DATA) public dialogData: any,
  ) {}

  ngOnInit() {
    this.dialogTitle = this.dialogData.dataSourceName;
    this.listOfFilePaths = this.dialogData.paths;
    this.listOfFilePaths.forEach((filePath: any) => {
      this.selectedFilePaths[filePath] = false;
    });
  }

  toggleSelectAll() {
    this.listOfFilePaths.forEach((filePath: any) => {
      this.selectedFilePaths[filePath] = this.selectAll;
    });
  }

  toggleIndividualSelection() {
    this.selectAll = this.listOfFilePaths.every(
      (filePath: any) => this.selectedFilePaths[filePath],
    );
  }

  openDataPreviewComponent() {
    let path = Object.entries(this.selectedFilePaths).find(
      ([key, value]) => value === true,
    );
    if (path) {
      const dialogRef = this.dialog.open(DataPreviewComponent, {
        width: '95vw',
        maxWidth: '95vw',
        height: '95%',
        data: {
          uc2SigmaFilePath: path[0],
        },
      });
      dialogRef.afterClosed().subscribe(() => {});
    }
  }

  openDataSetCreation() {
    let data = {
      source: 'mounted',
      file: {
        full_path: this.selectedFilePath,
        name: this.selectedFilePath,
        description: '',
        access_mode: 'EXTERNAL',
      },
      file_type: 'PARQUET',
      destination_folder: '',
      selected_file_names: this.selectedFilePaths,
    };

    const dialogRef = this.dialog.open(AddToDatasetComponent, {
      width: '90%',
      height: '90%',
      data: data,
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result.success) {
        this.toaster.success('Dataset(s) created successfully', '', {
          positionClass: 'custom-toast-position',
        });
        this.dialogRef.close({ success: true });
      }
      if (result.success === false) {
        this.toaster.error('Error while creating dataset', '', {
          positionClass: 'custom-toast-position',
        });
        this.dialogRef.close({ success: false });
      }
    });
  }

  isAnyFileSelected(): boolean {
    return Object.values(this.selectedFilePaths).some((selected) => selected);
  }

  isSingleFileSelected(): boolean {
    const selectedFiles = Object.values(this.selectedFilePaths).filter(
      (selected) => selected === true,
    );
    return selectedFiles.length === 1;
  }
}
