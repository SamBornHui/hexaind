import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from 'src/app/services/api.service';
import { DataCatalogService } from '../../tools/data-catalog/data-catalog.service';
DataCatalogService

@Component({
  selector: 'app-add-to-dataset',
  templateUrl: './add-to-dataset.component.html',
  styleUrls: ['./add-to-dataset.component.less'],
})
export class AddToDatasetComponent {
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<AddToDatasetComponent>,
    public apiService: ApiService,
    private toastr: ToastrService,
    private dataCatService: DataCatalogService,
  ) {}

  displayedColumns: string[] = ['filePath', 'fileName'];
  dataSource: { filePath: string; fileName: string }[] = [];
  headerMessage = 'Add to Dataset';
  ngOnInit() {
    this.dataSource = Object.keys(this.data.selected_file_names)
      .filter((filePath) => this.data.selected_file_names[filePath]) // Filter for true values
      .map((filePath) => ({
        filePath,
        fileName: '', // Initialize with empty string or any default value
      }));
  }
  cancelRequest() {
    this.dialogRef.close();
  }
  disableSubmit() {
    return !this.allFileNamesFilled();
  }

  allFileNamesFilled(): boolean {
    return this.dataSource.every((row) => row.fileName.trim() !== '');
  }

  async onSubmit() {
    try {
      let allSuccessful = true;

      for (const file of this.dataSource) {
        if (this.data.source && this.data.source === 'mounted') {
          try {
            let payload = {
              name: file.fileName,
              description: 'test',
              file: file.filePath,
            };
            await this.dataCatService.addToDataset(payload).subscribe((res) => {
              if (res) {
                console.log(`Success for file: ${file.filePath}`);
              }
            });
          } catch (error) {
            allSuccessful = false;
            this.toastr.error(
              `Error processing file ${file.filePath}`,
              'Upload Error',
            );
          }
        }
      }

      if (allSuccessful) {
        // this.toastr.success('All files processed successfully!', 'Success');
      } else {
        this.toastr.info(
          'Some files encountered errors during processing.',
          'Partial Success',
        );
      }

      this.dialogRef.close({
        success: allSuccessful,
      });
    } catch (error) {
      this.toastr.error('An error occurred during submission.', 'Error');
      // console.error('Error during submission:', error);
    }
  }
}
