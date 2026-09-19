import { Component, Inject, OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

@Component({
  selector: 'app-save-analysis-confirmation-dialog',
  templateUrl: './save-analysis-confirmation-dialog.component.html',
  styleUrls: ['./save-analysis-confirmation-dialog.component.less']
})
export class SaveAnalysisConfirmationDialogComponent implements OnInit {

  analysis:Boolean = true;

  constructor(public dialogRef: MatDialogRef<SaveAnalysisConfirmationDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data:any) {
      dialogRef.disableClose = true; 
  }

  ngOnInit() {
  }

  closeDialog(type:boolean){
    this.dialogRef.close({'save':type,"analysis":this.analysis});
  }

}
