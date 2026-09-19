import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-confirmation-promp',
  templateUrl: './confirmation-promp.component.html',
  styleUrls: ['./confirmation-promp.component.less']
})
export class ConfirmationPrompComponent {
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<ConfirmationPrompComponent>,
  ) { }

  navigateToPublishedWorkflow() {
    this.dialogRef.close(true);
  }
  
  onClose() {
    this.dialogRef.close(false);
  }

  onStopAll() {
    this.dialogRef.close('stopAll');
  }

  onStopPending() {
    this.dialogRef.close('stopPending');
  }
}
