import { Component, OnInit, Inject } from '@angular/core';
import { MatDialogRef,  MAT_DIALOG_DATA} from '@angular/material/dialog';



/**
 * Class to represent confirm dialog model.
 *
 * It has been kept here to keep it as part of shared component.
 */
 export class ImageAnalysisDialogBoxModel {
 
  constructor(public dialogInfo:any) {
  }
}

@Component({
  selector: 'app-image-analysis-dialog-box',
  templateUrl: './image-analysis-dialog-box.component.html',
  styleUrls: ['./image-analysis-dialog-box.component.less']
})
export class ImageAnalysisDialogBoxComponent implements OnInit {

  dialogInfo: any;
  
  constructor(public dialogRef: MatDialogRef<ImageAnalysisDialogBoxComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ImageAnalysisDialogBoxModel) {
    // Update view with given values
    this.dialogInfo = data['dialogInfo'];
  }

  ngOnInit() {
  }

  onConfirm(): void {
    // Close the dialog, return true
    this.dialogRef.close(true);
  }
 
  onDismiss(): void {
    // Close the dialog, return false
    this.dialogRef.close(false);
  }

}

