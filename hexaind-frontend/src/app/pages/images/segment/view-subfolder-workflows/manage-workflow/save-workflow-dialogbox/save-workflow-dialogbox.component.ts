import { Component, OnInit, Inject} from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';

export interface DialogData {
  name: string;
}

@Component({
  selector: 'app-save-workflow-dialogbox',
  templateUrl: './save-workflow-dialogbox.component.html',
  styleUrls: ['./save-workflow-dialogbox.component.less']
})
export class SaveWorkflowDialogBox implements OnInit {
  defaultWorkflow = false;
  applyToAllImages = false;
  manual=false;
  currentUser = {};
  analysis = true;
  wf_for_incomingimages = false;

  constructor(
    private toastr: ToastrService,
    public dialogRef: MatDialogRef<SaveWorkflowDialogBox>,
    @Inject(MAT_DIALOG_DATA) public data: any) {
      dialogRef.disableClose = true;
  }

  ngOnInit() {
    this.currentUser = JSON.parse(localStorage.getItem('currentUser')!);
    // if(!this.data['checkscalebar']){
    //   this.scalebar = false;
    // }    
    if(!this.data['checkanalysis']){
      this.analysis = false;
    }
    this.manual = this.data['manual'];
  }

  disableCheckbox(){
    return (this.applyToAllImages)?false:true;
  }

  submitName(name:string){
    if(name!=undefined && name!=""){
      let res = {
        "name": name,
        "default_workflow":this.defaultWorkflow,
        "apply_all":this.applyToAllImages,
        "manual":this.manual,
        // "scalebar":this.scalebar,
        "analysis":this.analysis,
        "wf_for_incomingimages":this.wf_for_incomingimages
      }
      this.dialogRef.close(res);
    }else{
      this.toastr.error('Please enter workflow name', '', {
        positionClass: 'custom-toast-position',
      });
    }
  }

  closeDialog(closeWorkflow:boolean){
    this.dialogRef.close({"closeWorkflow":closeWorkflow});
  }

}
