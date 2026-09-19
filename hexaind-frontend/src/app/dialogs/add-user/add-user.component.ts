import { Component, Output, EventEmitter, Input,Inject,ViewChild } from '@angular/core';
import { User, UserRole } from '../../models/user-models';
import { NewUserService } from './new-user.service';
import { MatDialogRef,MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatChipsModule } from '@angular/material/chips';

@Component({
  selector: 'app-add-user',
  templateUrl: './add-user.component.html',
  styleUrls: ['./add-user.component.less'],
})
export class AddUserComponent {
  constructor(
    private createUerService: NewUserService,
    @Inject(MAT_DIALOG_DATA) public data: any,
     public dialogRef: MatDialogRef<AddUserComponent>) {
    if(data && data.edit){
      this.isUpdatingUser = true;
      this.userRole = data.user.sites_and_roles[0].role_id;
      this.email = data.user.email;
      this.name = data.user.name;
    }
   }
  name: string = '';
  email: string = '';
  userRole:string = ''
  isCreatingUser: boolean = false;
  isUpdatingUser:boolean = false; 
  ssoUser:boolean = false; 
 
  userNameError: string = '';
  userEmailError: string = '';
  userRoleError: string = '';
  invitations:string[]  = [];
  
  async addEmail(){
    console.log(this.email)
    if(this.invitations.indexOf(this.email) ==-1){
      this.invitations.push(this.email);
      this.email = '';
    }
  }
  async removeEmail(email:string){
    const index = this.invitations.indexOf(this.email);
    if (index > -1) {
      this.invitations.splice(index, 1);
    }
  }
  async onCreateUser() {
    this.userNameError = '';
    this.userEmailError = '';
    this.userRoleError = '';
    let error = false;

    if (this.invitations.length ==0) {
      this.userEmailError = 'Email(s) is required.';
      error = true;
    }
    if (!this.userRole) {
      this.userRoleError = 'User role is required.';
      error = true;
    }


    let userData = {
      email_ids:this.invitations,
      is_sso_user:this.ssoUser,
      role_id:this.userRole,
      site_id:"1"
    };
    if (!error) {
      this.isCreatingUser = true;
      this.createUerService.CreateMultipleUsers(userData).subscribe(
        (response) => {
            this.isCreatingUser = false;
          if (response.status == 200 && response.body) {
            this.dialogRef.close({success: true,message:response.body,edit:this.isUpdatingUser})
          } else if (response.status == 401) {
            this.dialogRef.close({success: false,message:response.body,edit:this.isUpdatingUser})
          } else {
            this.dialogRef.close({success: false,message:"Failed to add user. Try again later.",edit:this.isUpdatingUser})
          }
        },
        (error) => {
          this.dialogRef.close({success: false,message:"Failed to add user. Try again later.",edit:this.isUpdatingUser})
        },
      );
    }
  }
}
