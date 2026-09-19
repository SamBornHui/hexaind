import { Component, Output, EventEmitter, Inject, OnInit } from '@angular/core';
import {
  MatDialogRef,
  MAT_DIALOG_DATA,
  MatDialog,
} from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import { SnackBarNotificationService } from 'src/app/services/snack-bar-notification.service';
import { ApiService } from 'src/app/services/api.service';
import { UsersService } from 'src/app/pages/users/users.service';
import { AddUsersComponent } from '../add-users/add-users.component';
import { CopyPasswordComponent } from '../copy-password/copy-password.component';

export interface CreateNewPasswordResponse {
  status: boolean;
  message: string;
  new_pwd: string;
}
@Component({
  selector: 'app-create-new-password',
  templateUrl: './create-new-password.component.html',
  styleUrls: ['./create-new-password.component.less'],
})
export class CreateNewPasswordComponent implements OnInit {
  @Output() closePanelClicked = new EventEmitter<any>();
  @Output() passwordEvent: EventEmitter<any> = new EventEmitter<any>();
  _data: any;
  //updateButton: boolean;
  email: string | undefined;
  reason: string | undefined;
  isCreatingProject: boolean = false;
  newPassword: any;

  constructor(
    private dialogRef: MatDialogRef<CreateNewPasswordComponent>,
    @Inject(MAT_DIALOG_DATA) public dialogData: any,
    private apiService: ApiService,
    public toaster: ToastrService,
    public usersservice: UsersService,
    private snackBarNotification: SnackBarNotificationService,
    private dialog: MatDialog,
  ) {
    this._data = dialogData;
    console.log(this._data.email,"dtaa console");
    dialogRef.disableClose = true;
  }

  ngOnInit(): void {
    console.log('test component');
  }

  onClosePanel() {
    this.closePanelClicked.emit();
  }

  async onCreatePassword() { 
    if (!this._data.email || !this.reason) {
      this.toaster.error('Both fields are required.');
      return;
    }

    try {
      let response = await this.usersservice.createNewPassword(
        this._data.email,
        this.reason,
      );
      console.log(response,"response values");
      if (response.status) {
        this.newPassword = response.new_pwd;
        this.toaster.success(response.message);
        this.copyPassword(this.newPassword);
        this.dialogRef.close(true);
      } else {
        this.toaster.error('Password creation failed.');
      }
    } catch (error) {
      this.toaster.error('Failed to create password.');
    } finally {
    }
  }

  copyPassword(password: string) {
    const dialogRef = this.dialog.open(CopyPasswordComponent, {
      width: '750px',
      data: password,
    });
    dialogRef.componentInstance.passwordEvent.subscribe((result: any) => {
      //this.fetchUsersList();
    });
  }
}
