import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-manage-account',
  templateUrl: './manage-account.component.html',
  styleUrls: ['./manage-account.component.less']
})
export class ManageAccountComponent {
  constructor(public dialogRef: MatDialogRef<ManageAccountComponent>) { }

  close(): void {
    this.dialogRef.close();
  }
}
