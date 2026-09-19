import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';

@Injectable({
  providedIn: 'root',
})
export class SnackBarNotificationService {
  constructor(private _snackBar: MatSnackBar) {}

  openSnackBar(message: string, type: 'success' | 'error') {
    let snackBarClass = type === 'success' ? 'snack-bar-success' : 'snack-bar-error';
    this._snackBar.open(message, '', {
      horizontalPosition: 'end',
      verticalPosition: "bottom",
      duration: 4000,
      panelClass: [snackBarClass]
    });
  }
}
