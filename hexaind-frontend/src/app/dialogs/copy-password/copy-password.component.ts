import { Component, Output, EventEmitter, Inject, OnInit } from "@angular/core";
import { MatDialogRef, MAT_DIALOG_DATA, MatDialog } from "@angular/material/dialog";
import { ToastrService } from "ngx-toastr";
import { SnackBarNotificationService } from "src/app/services/snack-bar-notification.service";
import { ApiService } from "src/app/services/api.service";
import { UsersService } from "src/app/pages/users/users.service";
import { AddUsersComponent } from "../add-users/add-users.component";

@Component({
  selector: 'app-copy-password',
  templateUrl: './copy-password.component.html',
  styleUrls: ['./copy-password.component.less'],
})
export class CopyPasswordComponent implements OnInit {
  @Output() closePanelClicked = new EventEmitter<any>();
  @Output() passwordEvent: EventEmitter<any> = new EventEmitter<any>();

  //updateButton: boolean;
  email: string | undefined;
  reason: string | undefined;
  isCreatingProject: boolean = false;
  private _data: any;
  textToCopy: any;
  password_copy: string | undefined;

  constructor(
    private dialogRef: MatDialogRef<CopyPasswordComponent>,
    @Inject(MAT_DIALOG_DATA) public dialogData: any,
    private apiService: ApiService,
    public toaster: ToastrService,
    public usersservice: UsersService,
    private snackBarNotification: SnackBarNotificationService,
    private dialog: MatDialog,
  ) {
    this._data = dialogData;
    dialogRef.disableClose = true;
  }

  ngOnInit(): void {
    console.log("test component",this._data);
    this.password_copy = this._data;
  }

  onClosePanel() {
    this.closePanelClicked.emit();
  }

  copyText() {
    const inputElement = document.getElementById('password') as HTMLInputElement;
    if (inputElement && inputElement.value) {
      const tempTextarea = document.createElement('textarea');
      tempTextarea.value = inputElement.value;
      document.body.appendChild(tempTextarea);
      tempTextarea.select();
      document.execCommand('copy');
      document.body.removeChild(tempTextarea);
      this.toaster.success('Password copied', 'Close');
    }
  }
}
