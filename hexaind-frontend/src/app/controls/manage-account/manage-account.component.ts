import { Component, ViewChild } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { ManageAccountService } from './manage-account.service';
import { NotificationComponent } from '../notification/notification.component';

@Component({
  selector: 'app-manage-account',
  templateUrl: './manage-account.component.html',
  styleUrls: ['./manage-account.component.less'],
})
export class ManageAccountComponent {
  @ViewChild('notification') notificationComponent!: NotificationComponent;
  fullNameUpdate: Boolean = false;
  updateEmail: Boolean = false;
  updatePassword: Boolean = false;
  user: any;
  name: any;
  email: any;
  resetPassowrd: any;
  old_password: string = '';
  password: string = '';
  conf_password: string = '';
  passwordMismatchError: string = 'Passwords do not match';
  notifyMSG: string = 'Success';
  notifyType: 'success' | 'error' = 'success';
  passwordVisible: boolean = false;
  oldPasswordVisible: boolean = false;
  newPasswordVisible: boolean = false;
  confPasswordVisible: boolean = false;
  constructor(
    public dialogRef: MatDialogRef<ManageAccountComponent>,
    public manageAccountService: ManageAccountService,
  ) {
    this.user = localStorage.getItem('currentUser');
    this.user = JSON.parse(this.user);
    this.email = this.user.email;
    this.name = this.user.name;
  }

  close(): void {
    this.dialogRef.close();
  }

  updateNameFunc() {
    this.fullNameUpdate = true;
  }

  cancelUpdateName() {
    this.fullNameUpdate = false;
  }

  updateName() {
    this.fullNameUpdate = false;
    if (this.name) {
      let data = {
        email: this.user.email,
        name: this.name,
      };
      this.manageAccountService.updateUserName(data).subscribe(
        (response) => {
          if (response.status == 200 && response.body) {
            if(response.body.name){
              this.user.name = response.body.name;
              localStorage.setItem('currentUser', JSON.stringify(this.user));
            }
            this.notificationComponent.display(
              'Your name has been succesfully updated.',
              'success',
            );
          } else if (response.status == 401) {
            this.notificationComponent.display(
              'Your token is not valid.',
              'error',
            );
          } else {
            this.notificationComponent.display(
              'Cannot Update.Try again!',
              'error',
            );
          }
        },
        (error) => {
          console.error('API Request Error:', error);
          // Handle the error appropriately, e.g., display an error message.
          this.notificationComponent.display(
            'Cannot Update.Try again!',
            'error',
          );
        },
      );
    }
  }

  emailUpdate() {
    this.updateEmail = false;
  }

  cancelUpdateEmail() {
    this.updateEmail = false;
  }

  updatePasswordFunc() {
    this.updatePassword = true;
  }

  updatePass() {
    this.updatePassword = false;

    if (this.password === this.conf_password) {
      let data = {
        email: this.user.email,
        old_password: this.old_password,
        password: this.password,
        conf_password: this.conf_password,
      };
      this.manageAccountService.changePassword(data).subscribe(
        (response) => {
          if (response.status == 200 && response.body) {
            this.notificationComponent.display(
              'Your password has been succesfully changed.',
              'success',
            );
          } else if (response.status == 401) {
            this.notificationComponent.display(
              'Your token is not valid.',
              'error',
            );
          } else {
            this.notificationComponent.display('Incorrect Password.', 'error');
          }
        },
        (error) => {
          console.error('API Request Error:', error);
          // Handle the error appropriately, e.g., display an error message.
          this.notificationComponent.display(
            error.error.reason,
            'error',
          );
        },
      );
      // Clear error message if it was previously displayed
      this.passwordMismatchError = '';
    } else {
      // Passwords do not match, show error message
      this.notificationComponent.display('Passwords do not match.', 'error');
      this.passwordMismatchError = 'Passwords do not match';
    }
  }

  cancelupdatePassword() {
    this.updatePassword = false;
  }

  togglePasswordVisibility(type: string) {
    if (type == 'old') {
      this.oldPasswordVisible = !this.oldPasswordVisible;
    }
    if (type == 'new') {
      this.newPasswordVisible = !this.newPasswordVisible;
    }
    if (type == 'conf') {
      this.confPasswordVisible = !this.confPasswordVisible;
    }
  }
}
