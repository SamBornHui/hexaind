import { Component, Inject, OnDestroy } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ApiService } from 'src/app/services/api.service';
import { Subject } from 'rxjs';
import { ThemePalette } from '@angular/material/core';
import { ProgressBarMode } from '@angular/material/progress-bar';
import { ConfigService } from 'src/app/services/config.service';
import { DataStructureService } from 'src/app/pages/data-structure/services/data-structure.service';

@Component({
  selector: 'app-edit-image-folder',
  templateUrl: './edit-image-folder.component.html',
  styleUrls: ['./edit-image-folder.component.less']
})
export class EditImageFolderComponent {

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
  fileTypes = ['CSV', 'PARQUET', 'JSON', 'TEXT'];
  metaDataFiles : any[] = []
  metaDataButtonMessage = "Add Material Metadata"
  headerMessage = "Add Dataset"
  originalFolderName: string | undefined;
  originalDescription: string | undefined;
  nameInputErrorMessage: string | undefined;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public apiService: ApiService,
    public configService: ConfigService,
    public dialogRef: MatDialogRef<EditImageFolderComponent>,
    public dataStructureService: DataStructureService
  ) {}

  ngOnInit() {
    this.name = this.data.name
    this.description = this.data.description
    this.originalFolderName = this.data.name
    this.originalDescription = this.data.description

    if(this.data.metadataFileName == "" || this.data.metaDataFiles == undefined) {
      this.metaDataButtonMessage = "Add material Metadata" 
    }
    else {
      this.metaDataFiles = this.data.metaDataFiles
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
    if(this.data.type == 'file') {
      let fileExtension = this.getFileExtension()
      if(fileExtension != this.data.extension.toLowerCase()) {
        this.nameInputErrorMessage = "File extension is not matching"
        return
      }
    }
    this.nameInputErrorMessage = undefined
  }

  getFileExtension() {
    const parts = this.name.split('.');
    return parts.length > 1 ? parts.pop() : '';
  }


  isFileExternsionMatches(fileName: string): any {
  
  }
  
  disableSubmit() {
    return this.name == '' ? true : false;
  }

  importMountedData() {
    
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
  
  uploadImageMetadata($event: any) {
    if($event.target.files.length == 0) return 
    this.metaDataFiles = [...this.metaDataFiles, ...$event.target.files]
  }

  async onSubmit() {
    try {      
      if(this.metaDataFiles) {
        const formData = new FormData();
        let isAnyNewFileAdded = false
        let uploadApiResponse : any;
        this.metaDataFiles.forEach((element:any) => {
           if(element.lastModifiedDate ) {
            isAnyNewFileAdded = true
            formData.append('files', element)
           }
        })
        if(isAnyNewFileAdded) {
          let uploadType = this.data.dataset_type  === "IMAGE_DATASET" ? 'csv_metadata' : 'uploaded'  
          uploadApiResponse =  await this.apiService.uploadImages(formData, uploadType, this.data.full_path)
        }
        if(this.originalFolderName != this.name || this.originalDescription != this.description) {
          await this.reNameDataset()
        } 
      }      
      this.dialogRef.close({ success: true });
    }
    catch(error: any) {
      console.log(error);
      this.nameInputErrorMessage = "Error while saving"
    }
   
  }

  /**
   * MetaDataFiles has two types of elements 1. The files metadata which are already present in the database 2. The metadata files which are
   * freshly uploaded from local machine which does not have any fullpath details.
   */

  async deleteMetaDataFile(metaDataDetails: any) {
    if(!metaDataDetails.full_path) {
      this.metaDataFiles = this.metaDataFiles.filter((element: any) => {
        return (element.lastModified != metaDataDetails.lastModified && element.name != metaDataDetails.name)
      })
    }
    else {
      await this.apiService.deleteImageDatasetEntity(metaDataDetails.dataset_path, metaDataDetails.full_path)
      this.metaDataFiles = this.metaDataFiles.filter((element: any) => {
        return element.full_path != metaDataDetails.full_path
      })
    }
    
  }


  modifyFullPathWithChangedName() {
    let individualParts = this.data.full_path.split('/')
    individualParts[individualParts.length-1] = this.name
    this.data.full_path = individualParts.join('/'); 
  }

  async reNameDataset() {
    if(this.data.dataset_type === 'IMAGE_DATASET') {
      let payload = {
        new_name: this.name,
        description: this.description,
        source: this.data.full_path,
        dataset_type: this.data.dataset_type
      }
      await this.dataStructureService.renameFolderData(payload)
    }
    else {
      let nameEditResponse: any = await this.apiService.renameImageFolder(this.name, this.data.dataset_path, this.data.full_path)
    }

  }

}
