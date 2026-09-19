import { Component, Output, EventEmitter, Input, Inject } from "@angular/core";
import { Workflow } from "src/app/models/workflow-models";
import { PlatformFilesDialogService } from "./platform-files-dialog.service";
import { ConfigService } from '../../services/config.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatTableDataSource } from '@angular/material/table';

@Component({
  selector: "app-platform-files-dialog",
  templateUrl: "./platform-files-dialog.component.html",
  styleUrls: ["./platform-files-dialog.component.less"],
})
export class PlatformFilesDialogComponent {
  @Output() closeDialogClicked = new EventEmitter<any>();
  filesData: any = [];
  selectedFiles: any = [];
  dataSource = new MatTableDataSource([]);
  displayedColumns: string[] = ['select', 'name'];

  constructor(
    public dialogRef: MatDialogRef<PlatformFilesDialogComponent>,
    private selectPlatformFilesService: PlatformFilesDialogService,
    private configService: ConfigService,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) { }

  onClosePanel() {
    this.dialogRef.close({ success: false });
  }

  ngOnInit() {
    this.getUploadedFiles();
  }

  getUploadedFiles() {
    this.selectPlatformFilesService.getUploadedFiles(this.data.siteId, this.data.projectId, this.data.connectorId).subscribe({
      next: (response) => {
        this.filesData = response.platform_files;
        this.dataSource = new MatTableDataSource(this.filesData);
      },
      error: (error) => {
        console.error('Upload error', error);
      }
    });
  }
  onClickDone() {
    let files = this.filesData.filter((file: any) => file.selected === true);
    if (files.length > 0) {
      this.onUploadtoRescale(files);
    }
  }
  onUploadtoRescale(files: any) {
    if (files.length > 0) {
      this.selectPlatformFilesService.uploadtoRescale(this.data.siteId, this.data.projectId, this.data.connectorId, files).subscribe({
        next: (response) => {
          this.dialogRef.close({ success: true, files: response.rescale_files });
        },
        error: (error) => {
          console.error('Upload error', error);
        }
      });
    }
  }

  disableDone() {
    let files = this.filesData.filter((file: any) => file.selected === true);
    if (files.length > 0) {
      return false;
    } else {
      return true;
    }
  }

}
