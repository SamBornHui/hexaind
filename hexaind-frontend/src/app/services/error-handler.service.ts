import { Injectable } from '@angular/core';
import { ToastrService } from 'ngx-toastr';


@Injectable({
  providedIn: 'root'
})
export class ErrorHandlerService {

  constructor(public toaster: ToastrService,) { }

  private getErrorMessage(error: any): string {
    if (error.error && typeof error.error === 'object') {
      const errorKeys = ['detail', 'reason', 'message'];
      for (const key of errorKeys) {
        if (error.error[key]) {
          return error.error[key];
        }
      }
    }
    return 'An unexpected error occurred.';
  }

  public handleError(error: any) {
    const errorMessage = this.getErrorMessage(error);
    this.toaster.error(errorMessage, '',{
      positionClass: 'custom-toast-position'
    });
  }
}
