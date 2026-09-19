import { Component, OnInit, Inject} from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
export interface DialogData {
  name: string;
}

@Component({
  selector: 'app-apply-workflows-dialogbox',
  templateUrl: './apply-workflows-dialogbox.component.html',
  styleUrls: ['./apply-workflows-dialogbox.component.less']
})
export class ApplyWorkflowsDialogboxComponent implements OnInit {
  defaultWorkflow = false;
  applyToAllImages = false;
  manual=false;
  currentUser = {};
  analysis = true;
  wf_for_incomingimages = false;

  constructor(
    public dialogRef: MatDialogRef<ApplyWorkflowsDialogboxComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData) {
      dialogRef.disableClose = true;
  }

  ngOnInit() {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);
  }

  applyNow(){
    this.dialogRef.close({apply: true});
  }

  closeDialog(){
    this.dialogRef.close();
  }

}
