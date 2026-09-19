import {
  Component,
  EventEmitter,
  Inject,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Role } from 'src/app/pages/users/users.component';
import { FormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';
import { MatTabChangeEvent } from '@angular/material/tabs';
import { UsersService } from '../../pages/users/users.service';
import { SnackBarNotificationService } from 'src/app/services/snack-bar-notification.service';
import { UserLoginService } from 'src/app/pages/login/login.service';
import { ToastrService } from 'ngx-toastr';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';

@Component({
  selector: 'app-add-users',
  templateUrl: './add-users.component.html',
  styleUrls: ['./add-users.component.css'],
})
export class AddUsersComponent implements OnInit {
  @Output() addEvent: EventEmitter<any> = new EventEmitter<any>();
  _serveRoles: Role[] = [];
  private selectedRoleIndex!: string;
  emails: string[] = [];
  emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  form!: FormGroup;
  inviteType: string = '';
  isSsoUser: any;
  loginMethod: any;
  loginMethods: any = [];
  loginMethodSelections: { [index: number]: string } = {};
  loginMethodBulk: boolean = false;

  @ViewChild('emailInput') emailInput: any;
  allowedBoth: boolean = false;

  userRoles = [
    { _id: '1', role_name: 'Server Admin', role_value: 1 },
    { _id: '2', role_name: 'Project Admin', role_value: 2 },
    { _id: '3', role_name: 'Default User', role_value: 4 },
  ];
  role_value: any;

  constructor(
    public dialogRef: MatDialogRef<AddUsersComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fb: FormBuilder,
    private usersService: UsersService,
    private snackBarNotification: SnackBarNotificationService,
    public toaster: ToastrService,
    private userLoginService: UserLoginService,
    public errorHandlerService: ErrorHandlerService,
  ) {
    dialogRef.disableClose = true;
    this.form = this.fb.group({
      rows: this.fb.array([]),
    });
    this.addCustomInviteRow();
    this.getLoginMethods();
  }

  close(): void {
    this.dialogRef.close();
  }

  getLoginMethods() {
    this.userLoginService.loginMethod().subscribe({
      next: (response: any) => {
        this.loginMethod = response;
        if (
          this.loginMethod.form_login_allowed == true &&
          this.loginMethod.sso_login_allowed == true
        ) {
          this.allowedBoth = true;
        } else if (
          this.loginMethod.form_login_allowed == true &&
          this.loginMethod.sso_login_allowed == false
        ) {
          this.isSsoUser = false;
        } else if (
          this.loginMethod.form_login_allowed == false &&
          this.loginMethod.sso_login_allowed == true
        ) {
          this.isSsoUser = true;
        }
      },
      error: (error: any) => {
        console.log(error);
        this.errorHandlerService.handleError(error);
      },
    });
  }

  ngOnInit() {
    this.inviteType = 'Bulk Invite';
    this.serveRoles = [
      { role_id: '1', role_name: 'Server Administrator' },
      { role_id: '2', role_name: 'Project Administrator' },
      { role_id: '3', role_name: 'Default User' },
    ];
    this.loginMethods = ['FORM_USER', 'SSO_USER'];
  }

  get serveRoles(): Role[] {
    return this._serveRoles;
  }

  set serveRoles(roles: Role[]) {
    this._serveRoles = roles;
  }

  onRoleSelectionChange(roleId: string) {
    this.selectedRoleIndex = roleId;
  }

  onEmailInput(event: any): void {
    const input = event.target.value;
    const lastChar = input.charAt(input.length - 1);
    if (lastChar === ',') {
      const enteredEmails = input
        .slice(0, -1)
        .split(',')
        .map((email: any) => email.trim());
      for (const email of enteredEmails) {
        if (this.isValidEmail(email)) {
          this.emails.push(email);
        }
      }
      event.target.value = '';
    }
  }

  isValidEmail(email: string): boolean {
    return this.emailPattern.test(email);
  }

  removeEmail(email: string): void {
    const index = this.emails.indexOf(email);
    if (index >= 0) {
      this.emails.splice(index, 1);
    }
  }

  get rows(): FormArray {
    return this.form.get('rows') as FormArray;
  }

  addCustomInviteRow() {
    const rowForm = this.fb.group({
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      loginMethod: [''],
      server_role_id: [''],
    });
    this.rows.push(rowForm);
  }

  removeRow(index: number) {
    if (this.rows.length > 1) {
      this.rows.removeAt(index);
    }
  }

  tabChanged(event: MatTabChangeEvent) {
    if (event.tab.textLabel === 'Bulk Invite') {
      this.inviteType = event.tab.textLabel;
    } else {
      this.inviteType = event.tab.textLabel;
    }
  }

  submitInvite() {
    if (this.inviteType === 'Bulk Invite') {
      let is_sso_user;
      if (this.allowedBoth) {
        is_sso_user = this.isSsoUser;
      } else {
        is_sso_user = this.isSsoUser;
      }
      let object = {
        email_ids: this.emails,
        server_role_id: this.role_value,
        is_sso_user: is_sso_user,
      };
      this.usersService.bulkInvite(object).subscribe({
        next: (response) => {
          if (response) {
            this.addEvent.emit();
            this.dialogRef.close();
            this.toaster.success('Invite sent successfully', '', {
              positionClass: 'custom-toast-position',
            });
          }
        },
        error: (error) => {
          console.log(error);
          this.errorHandlerService.handleError(error);
        },
      });
    } else {
      const usersData = this.form.value.rows.map((row: any, index: any) => {
        let isSsoUser;
        if (this.allowedBoth == false) {
          isSsoUser = this.isSsoUser;
        } else {
          isSsoUser = this.loginMethodSelections[index] !== 'FORM_USER';
        }

        const newUser = {
          ...row,
          is_sso_user: isSsoUser,
        };
        delete newUser.loginMethod;
        return newUser;
      });
      this.usersService.customInvite(usersData).subscribe({
        next: (response) => {
          if (response) {
            this.addEvent.emit();
            this.dialogRef.close();
            this.toaster.success('Invite sent successfully', '', {
              positionClass: 'custom-toast-position',
            });
          }
        },
        error: (error) => {
          console.log(error);
          this.errorHandlerService.handleError(error);
        },
      });
    }
  }

  isFormValid(): boolean {
    if (this.inviteType === 'Bulk Invite') {
      if (!this.allowedBoth) {
        return this.emails.length > 0;
      } else {
        return (
          this.emails.length > 0 &&
          this.loginMethodBulk &&
          this.role_value != undefined
        );
      }
    } else {
      const usersData = this.form.value.rows;
      if (!this.allowedBoth) {
        const nameAndEmailNotEmpty = usersData.every(
          (user: any) => user.name !== '' && user.email !== '',
        );
        const allEmailsValid = usersData.every((user: any) =>
          this.isValidEmail(user.email),
        );
        return usersData.length > 0 && nameAndEmailNotEmpty && allEmailsValid;
      } else {
        const allFieldsNotEmpty = usersData.every((user: any) =>
          Object.values(user).every((value) => value !== ''),
        );
        if (allFieldsNotEmpty) {
          const allEmailsValid = usersData.every((user: any) =>
            this.isValidEmail(user.email),
          );
          return usersData.length > 0 && allEmailsValid;
        }
        return false;
      }
    }
  }

  onLoginMethodChange(rowIndex: number, method: string) {
    this.loginMethodSelections[rowIndex] = method;
  }

  onBulkChange(value: any) {
    this.loginMethodBulk = true;
    if (value == 'FORM_USER') {
      this.isSsoUser = false;
    } else {
      this.isSsoUser = true;
    }
  }

  onRoleChange(value: any) {
    this.role_value = value;
  }
}
