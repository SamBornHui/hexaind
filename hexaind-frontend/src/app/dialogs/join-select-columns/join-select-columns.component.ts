import {
  Component,
  Inject,
  OnInit,
  ViewChild,
} from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { UsersService } from '../../pages/users/users.service';
import { SnackBarNotificationService } from 'src/app/services/snack-bar-notification.service';
import { UserLoginService } from 'src/app/pages/login/login.service';
import { ToastrService } from 'ngx-toastr';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';

@Component({
  selector: 'join-select-columns',
  templateUrl: './join-select-columns.component.html',
  styleUrls: ['./join-select-columns.component.css'],
})
export class JoinSelectColumnComponent implements OnInit {
  options1 = ['Option 1', 'Option 2', 'Option 3'];
  options2 = ['Option A', 'Option B', 'Option C'];
  rows = [{ selectedOption1: '', selectedOption2: '' }];
  
  constructor(
    public dialogRef: MatDialogRef<JoinSelectColumnComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    public toaster: ToastrService,
    public errorHandlerService: ErrorHandlerService,
  ) {
    dialogRef.disableClose = true;
  }
  ngOnInit(): void {
    throw new Error('Method not implemented.');
  }

  addRow() {
    this.rows.push({ selectedOption1: '', selectedOption2: '' });
  }

  removeRow(index: number) {
    if (this.rows.length > 1) {
      this.rows.splice(index, 1);
    }
  }

  close(): void {
    this.dialogRef.close();
  }

}