import { Component, Inject, OnInit, ViewChild } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import { ConfigService } from 'src/app/services/config.service';
import { WorkflowsSessionsApiService } from 'src/app/services/workflow-sessions-api.service';
import { Utils } from 'src/app/utils';
import { NgForm } from '@angular/forms';


@Component({
  selector: 'app-publish-workflow',
  templateUrl: './publish-workflow.component.html',
  styleUrls: ['./publish-workflow.component.less'],
})
export class PublishWorkflowComponent implements OnInit{
  public name: string | undefined = undefined;
  public description: string | undefined = undefined;
  public version: string | undefined = undefined;
  public nameError: string = '';
  public descriptionError: string = '';
  public versionError: string = '';
  public ownerError: string = '';
  ownerNameArray: any = [];
  fullName: string = '';
  userId: string = '';
  isDuplicate: boolean = false;
  isExport: boolean = false;
  @ViewChild('workflowForm') workflowForm!: NgForm;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public configService: ConfigService,
    public sessionApi: WorkflowsSessionsApiService,
    public dialogRef: MatDialogRef<PublishWorkflowComponent>,
    public toaster: ToastrService,
    //private usersService: UsersService,
  ) {}

  ngOnInit() {

    if(this.data && ('isDuplicate' in this.data)){
      this.isDuplicate = this.data.isDuplicate;  
    }
    this.getCurrentUserData();
  }

  getCurrentUserData() {
    let user: any = localStorage.getItem('currentUser');
    let userInfo: any = JSON.parse(user);
    this.userId = userInfo._id;
    this.fullName = Utils.getUserFullName(userInfo);
  }

  onClosePanel() {
    this.dialogRef.close();
  }
  checkNameField(){
    if (!this.name) {
      this.nameError = 'Name is required';
    } else {
      this.nameError = '';
    }
    
  }
  
  onPublishWorkflow(workflowForm: NgForm) {
    if (workflowForm.invalid) {
      workflowForm.form.markAllAsTouched();
      return; // Stop further processing if the form is invalid
    }
    this.dialogRef.close({
      name: this.name,
      description: this.description,
      version: this.version,
      owner: this.fullName,
      ownerId: this.userId,
    });
}

}
