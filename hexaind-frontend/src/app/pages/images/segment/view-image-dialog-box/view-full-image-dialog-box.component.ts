import { Component, OnInit, Inject } from '@angular/core';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
export interface DialogData {
  name: string;
}

@Component({
  selector: 'app-view-full-image-dialog-box',
  templateUrl: './view-full-image-dialog-box.component.html',
  styleUrls: ['./view-full-image-dialog-box.component.less']
})
export class ViewFullImageDialogBox implements OnInit {
  
  imageDisplayUrl = '/imageAnalysis/showImage?file=';

  constructor(
    public dialogRef: MatDialogRef<ViewFullImageDialogBox>,
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

