import { Component, Inject, OnDestroy } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ApiService } from 'src/app/services/api.service';
import { ConfigService } from '../../services/config.service';
import { takeUntil } from 'rxjs/operators';
import { Subject } from 'rxjs';
import { ThemePalette } from '@angular/material/core';
import { ProgressBarMode } from '@angular/material/progress-bar';
import { HttpParams } from '@angular/common/http';
import { AccessMode } from 'src/app/models/data-models';

@Component({
  selector: 'app-data-import-dialog',
  templateUrl: './data-import-dialog.component.html',
  styleUrls: ['./data-import-dialog.component.less'],
})
export class DataImportDialogComponent {
  private cancelRequestSubject = new Subject();
  name: string = '';
  disablesubmit: boolean = true;
  description: string = '';
  size: string = '';
  fileName: string = '';
  progress = 0;
  color: ThemePalette = 'primary';
  mode: ProgressBarMode = 'determinate';
  bufferValue = 100;
  dateSetTypes = [
    'MOBO_RECOMMENDATIONS',
    'IMAGE',
    'VIDEO',
    'PDF',
    'JSON',
    'TEXT',
  ];
  fileTypes = ['CSV', 'PARQUET', 'JSON', 'TEXT','EXCEL'];
  selectedMetaDataFileName: string | undefined;
  headerMessage = "Add Dataset"

  isLoading: boolean = false;
  isDisabled: boolean = false;
  accessMode: string = AccessMode.EXTERNAL;
  tags: string[] = [];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<DataImportDialogComponent>,
    public apiService: ApiService,
    public configService: ConfigService,
  ) {}

  ngOnInit() {
    console.log('import data received',this.data)
    if (this.data.uploadType == "image") this.headerMessage = "Create Dataset Folder"
    if (this.data.source && this.data.source == 'mounted') {
      this.size = this.transform(this.data.file.size, 1);
      this.fileName = this.data.file.name;
      let fileSplit = this.data.file.name.split('.');
      this.name = fileSplit[0];
      this.description = this.data.file.description;
    } else {
      this.size = this.transform(this.data?.file?.size, 1);
      this.fileName = this.data?.file?.name;
    }

    if(this.data.tags && this.data.tags.length>0){
      this.tags = this.data.tags
    }
    if(this.data.accessMode && this.data.accessMode !=''){
      this.accessMode = this.data.accessMode
    }
    
  }

  validate() {
    this.name = this.name.trim();
    this.description = this.description.trim();
    if (this.progress > 0 || this.name.length == 0) {
      this.disablesubmit = true;
    } else {
      this.disablesubmit = false;
    }
  }

  disableSubmit() {
    if (this.isDisabled) return true;
    return this.name == '' ? true : false;
  }

  onSubmit() {
    this.isLoading = true;
    this.isDisabled = true;
    
    if(this.data.uploadType === 'image') {
      this.saveImageDataset()
      return;
    }
    const file = this.data.file;
    if (file) {
      let dataset_type = this.dateSetTypes.includes(this.data.file_type)
        ? this.data.file_type
        : 'TABULAR';
      let file_type = this.fileTypes.includes(this.data.file_type)
        ? this.data.file_type
        : 'CSV';

      if (this.data.source && this.data.source == 'mounted') {
        this.importMountedData();
      } else {
        if(this.tags.length>0){
          this.apiService
          .ImportFileWithTags(
            file,
            this.name,
            this.description,
            this.accessMode,
            file_type,
            (progress) => {
              this.progress = progress;
            },
            dataset_type.trim(),
            this.data.destination_folder,
            this.tags
          )
          .pipe(takeUntil(this.cancelRequestSubject))
          .subscribe({
            next: (response) => {
              this.isLoading = false;
              if (response?.dataset_id && response['dataset_id'] != '') {
                this.dialogRef.close({ success: true });
                this.isDisabled = false;
              }
            },
            error: (error) => {
              this.dialogRef.close({ success: false, error: error });
              console.error('Upload failed:', error);
              this.isLoading = false;
              this.isDisabled = false;
            },
          });
        }else{
          this.apiService
          .ImportFile(
            file,
            this.name,
            this.description,
            this.accessMode,
            file_type,
            (progress) => {
              this.progress = progress;
            },
            dataset_type.trim(),
            this.data.destination_folder,
          )
          .pipe(takeUntil(this.cancelRequestSubject))
          .subscribe({
            next: (response) => {
              this.isLoading = false;
              if (response?.dataset_id && response['dataset_id'] != '') {
                this.dialogRef.close({ success: true });
                this.isDisabled = false;
              }
            },
            error: (error) => {
              this.dialogRef.close({ success: false, error: error });
              console.error('Upload failed:', error);
              this.isLoading = false;
              this.isDisabled = false;
            },
          });
        }
        
      }
    }
  }
  importMountedData() {
    const file = this.data.file;
    if (file) {
      if (this.data.file_type.toLowerCase() === 'csv' || this.data.file_type.toLowerCase() === 'parquet') {
        this.apiService
          .importDatasetMountedDriveFile(
            file.full_path,
            this.name,
            this.description,
            this.data.destination_folder,
            'TABULAR',
          )
          .then((response) => {
            this.isLoading = false;

            if (response) {
              this.dialogRef.close({
                success: true,
                dataset_id: response.dataset_id,
              });
              this.isDisabled = false;
            }
          })
          .catch((error) => {
            this.isLoading = false;
            this.isDisabled = false;
            console.error('Error fetching mounted drive data:', error);
          });
      }
      else if (this.data.file_type.toLowerCase() === 'json') {
        this.apiService
          .importDatasetMountedDriveFile(
            file.full_path,
            this.name,
            this.description,
            this.data.destination_folder,
            'JSON',
          )
          .then((response) => {
            this.isLoading = false;
            if (response) {
              this.dialogRef.close({
                success: true,
                dataset_id: response.dataset_id,
              });
              this.isDisabled = false;
            }
          })
          .catch((error) => {
            this.isLoading = false;
            this.isDisabled = false;
            console.error('Error fetching mounted drive data:', error);
          });
      }
      else if (this.data.file_type.toLowerCase() === 'py') {
        this.apiService
          .importDatasetMountedDriveFile(
            file.full_path,
            this.name,
            this.description,
            this.data.destination_folder,
            'PYTHON',
          )
          .then((response) => {
            if (response) {
              this.isLoading = false;
              this.dialogRef.close({
                success: true,
                dataset_id: response.dataset_id,
              });
              this.isDisabled = false;
            }
          })
          .catch((error) => {
            this.isLoading = false;
            this.isDisabled = false;
            console.error('Error fetching mounted drive data:', error);
          });
      }
      else if (this.data.file_type.toLowerCase() === 'text') {
        this.apiService
          .importDatasetMountedDriveFile(
            file.full_path,
            this.name,
            this.description,
            this.data.destination_folder,
            'TEXT'
          )
          .then((response) => {
            this.isLoading = false;

            if (response) {
              this.dialogRef.close({
                success: true,
                dataset_id: response.dataset_id,
              });
              this.isDisabled = false;
            }
          })
          .catch((error) => {
            this.isLoading = false;
            this.isDisabled = false;
            console.error('Error fetching mounted drive data:', error);
          });
      } else if (this.data.file_type.toLowerCase() === 'zip') {
        this.dialogRef.close({
          success: true,
          name: this.name,
          pathname: file.full_path,
        });
      } else {
        this.apiService
          .importDatasetMountedDriveFile(
            file.full_path,
            this.name,
            this.description,
            this.data.destination_folder,
            ''
          )
          .then((response) => {
            this.isLoading = false;

            if (response) {
              this.dialogRef.close({
                success: true,
                dataset_id: response.dataset_id,
              });
              this.isDisabled = false;
            }
          })
          .catch((error) => {
            this.isLoading = false;
            this.isDisabled = false;
            console.error('Error fetching mounted drive data:', error);
          });
      }
    } else {
      this.isLoading = false;
      this.isDisabled = false;
      console.log('No node selected');
    }
  }

  onCancle() {}

  transform(bytes: number, decimalPoint: number) {
    if (bytes == 0) return '0 Bytes';
    const k = 1000;
    const dm = decimalPoint;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  cancelRequest() {
    this.isLoading = false;
    this.isDisabled = false;
    this.dialogRef.close();
    this.cancelRequestSubject.next(true);
  }

  ngOnDestroy() {
    this.cancelRequestSubject.complete();
  }

  onFileSelected(event: any) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) {
      return;
    }
    this.data.file = input.files[0];
    this.fileName = this.data.file.name;
  }

  async uploadImageMetadata($event: any) {
    const file = $event.target.files[0];
    this.selectedMetaDataFileName = file.name
    const formData = new FormData();
    formData.append('files',file)
    let uploadApiResponse =  await this.apiService.uploadImages(formData, 'csv_metadata', this.data.metadata.base_folder)
  }

  async saveImageDataset() {
    let queryParams = new HttpParams()
    .set('name', this.name)
    .set('base_folder', this.data.metadata.base_folder)
    .set('description', this.description)

    try {
      // Show loader
      this.isLoading = true;   
      this.isDisabled = true;   
      // Wait for the API response
      let response = await this.apiService.saveImageDataset(queryParams);

      if (response?.dataset_id && response['dataset_id'] != '') {
        this.isLoading = false;
        this.dialogRef.close({ success: true });
      }
      else {
        this.isLoading = false;
        this.dialogRef.close({ success: false, error: "" });
      }
    } catch (error) {
      // Handle error if needed
      console.error("Error uploading images:", error);
      this.isLoading = false;
      this.dialogRef.close({ success: false, error: "" });
    } finally {
      // Hide loader after the response is received
      this.isLoading = false;
      this.isDisabled = false;
    }
  }
}
