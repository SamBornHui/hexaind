import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-confirmation-image-promp',
  templateUrl: './confirmation-image-promp.component.html',
  styleUrls: ['./confirmation-image-promp.component.less']
})
export class ConfirmationImagePrompComponent {
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<ConfirmationImagePrompComponent>,
  ) { }

  onConfirm() {
    this.dialogRef.close(true);
  }
  
  onClose() {
    this.dialogRef.close(false);
  }
}
