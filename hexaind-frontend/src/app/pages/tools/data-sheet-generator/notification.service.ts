import { Injectable } from '@angular/core';
import { ToastrService } from 'ngx-toastr';

@Injectable({
  providedIn: 'root',
})
export class NotificationService {
  constructor(private toastr: ToastrService) { }

  private getErrorMessage(error: any): string {
    if (error && typeof error === 'object') {
      const errorKeys = ['detail', 'reason', 'message'];

      // Check error object directly
      for (const key of errorKeys) {
        if (error[key]) {
          return error[key];
        }
      }

      // Check nested error.error object
      if (error.error && typeof error.error === 'object') {
        for (const key of errorKeys) {
          if (error.error[key]) {
            return error.error[key];
          }
        }
      }
    }
    return 'An unexpected error occurred.';
  }

  public showError(error: string | any, title: string = ''): void {
    const message = typeof error === 'string' ? error : this.getErrorMessage(error);
    this.toastr.error(message, title, {
      positionClass: 'custom-toast-position',
      disableTimeOut: true,
      closeButton: true,
      tapToDismiss: false,
    });
  }
}
