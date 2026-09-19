import { Component, Output, EventEmitter, Input, Inject, ViewChild, AfterViewInit } from "@angular/core";
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';


@Component({
  selector: "app-file-editor-dialog",
  templateUrl: "./file-editor-view-dialog.component.html",
  styleUrls: ["./file-editor-view-dialog.component.less"]
})
export class FileEditorDialogComponent {
  @Output() closeDialogClicked = new EventEmitter<any>();
  editorContent: string = "";
  fileName: string = "";
  mode: string = "python";

  constructor(
    public dialogRef: MatDialogRef<FileEditorDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) { 
    this.editorContent = data.content;
    this.fileName = data.file_name;
    this.mode = data.mode;
  }

  onClosePanel() {
    this.dialogRef.close({ success: false });
  }

  ngOnInit() {
    
  }
}
