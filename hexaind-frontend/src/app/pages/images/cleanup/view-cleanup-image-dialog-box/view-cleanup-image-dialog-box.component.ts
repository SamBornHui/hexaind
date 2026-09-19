import { Component, OnInit, Inject } from '@angular/core';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
export interface DialogData {
  name: string;
}

@Component({
  selector: 'app-view-cleanup-image-dialog-box',
  templateUrl: './view-cleanup-image-dialog-box.component.html',
  styleUrls: ['./view-cleanup-image-dialog-box.component.less']
})
export class ViewCleanFullImageDialogBox implements OnInit {

  constructor(
    public dialogRef: MatDialogRef<ViewCleanFullImageDialogBox>,
    @Inject(MAT_DIALOG_DATA) public data: any) {

  }

  ngOnInit() {
  }

  imageLoaded(){
  }
 
  close(): void {
    // Close the dialog, return false
    this.dialogRef.close(false);
  }

}

