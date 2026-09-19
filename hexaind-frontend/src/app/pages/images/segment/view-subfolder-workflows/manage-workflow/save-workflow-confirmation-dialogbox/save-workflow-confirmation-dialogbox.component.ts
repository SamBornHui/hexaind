import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-save-workflow-confirmation-dialogbox',
  templateUrl: './save-workflow-confirmation-dialogbox.component.html',
  styleUrls: ['./save-workflow-confirmation-dialogbox.component.less']
})
export class SaveWorkflowConfirmationDialogboxComponent implements OnInit {

  constructor(public dialogRef: MatDialogRef<SaveWorkflowConfirmationDialogboxComponent>,
    @Inject(MAT_DIALOG_DATA) public data:any) {
      dialogRef.disableClose = true;
  }

  ngOnInit() {
  }

  closeDialog(type:boolean,closeWorkflow:boolean){
    this.dialogRef.close({'save':type,"closeWorkflow":closeWorkflow});
  }
  
  closeSaveDialog(type:string){
    this.dialogRef.close({'save':type});
  }

}
