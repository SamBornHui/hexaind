import { Component, ViewChild } from '@angular/core';
import { Location } from '@angular/common';
import { NotificationComponent } from '../../controls/notification/notification.component';

@Component({
  selector: 'app-change-password',
  templateUrl: './change-password.component.html',
  styleUrls: ['./change-password.component.less'],
})
export class ChangePasswordComponent {
  @ViewChild('notification') notificationComponent!: NotificationComponent;

  oldPassword: string | null = null;
  newPassword: string | null = null;
  newPasswordRepeat: string | null = null;
  oldPasswordVisible: boolean | null = false;
  newPasswordVisible: boolean | null = false;
  newPasswordRepeatVisible: boolean | null = false;
  changingPassword: boolean | null = false;

  constructor(private location: Location) {}

  togglePasswordVisibility() {
    this.oldPasswordVisible = !this.oldPasswordVisible;
  }
  toggleNewPasswordVisibility() {
    this.newPasswordVisible = !this.newPasswordVisible;
  }
  toggleNewPasswordRepeatVisibility() {
    this.newPasswordRepeatVisible = !this.newPasswordRepeatVisible;
  }

  isValidPassword(password: string): boolean {
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    return hasUpperCase && hasLowerCase && hasSpecialChar;
  }

  onChangePassword() {
    if (this.newPassword === this.oldPassword) {
      this.notificationComponent.display(
        'New and old password should not match.',
        'error',
      );
    } else if (this.newPassword !== this.newPasswordRepeat) {
      this.notificationComponent.display(
        'The new passwords do not match.',
        'error',
      );
    } else if (!this.newPassword || this.newPassword.length < 8) {
      this.notificationComponent.display(
        'Password must be at least 8 characters in length.',
        'error',
      );
    } else if (!this.isValidPassword(this.newPassword)) {
      this.notificationComponent.display(
        'Password must contains at least one upper case, one lower case, and one special character.',
        'error',
      );
    } else {
      this.changingPassword = true;
      this.notificationComponent.display(
        'Your password has been succesfully changed.',
        'success',
      );
      setTimeout(() => {
        // TODO REPLACE THIS WITH API CALL.
        this.location.back();
      }, 4000); // 400 milliseconds del
    }
  }

  onCancel() {
    this.location.back();
  }
}
