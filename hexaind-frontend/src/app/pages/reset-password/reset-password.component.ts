import { Component,OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { SnackBarNotificationService } from 'src/app/services/snack-bar-notification.service';
import { UsersService } from '../users/users.service';
import { ToastrService } from 'ngx-toastr';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';


@Component({
  selector: 'app-reset-password',
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.less']
})
export class ResetPasswordComponent implements OnInit {

  newPasswordVisible: boolean = false;
  confirmPasswordVisible: boolean = false;
  form!: FormGroup;
  email: string ='';
  email_verification_token: string = '';

  constructor(private fb: FormBuilder, 
              private SnackBarNotificationService:SnackBarNotificationService,
              public activatedRoute: ActivatedRoute,
              private usersService:UsersService,
              private router: Router,
              public toaster: ToastrService,
              private errorHandlerService:ErrorHandlerService){}

  get f() { return this.form.controls; }

  ngOnInit() {
    this.form = this.fb.group({
      password: ['', [
        Validators.required, 
        Validators.minLength(12),
        Validators.pattern('^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[\\W_]).{12,}$')
      ]],
      confirmPassword: ['', Validators.required]
    }, { validator: this.passwordMatchValidator });

    if(this.activatedRoute.snapshot.queryParams["email_verification_token"]){
      this.email = this.activatedRoute.snapshot.queryParams["email"];
      this.email_verification_token = this.activatedRoute.snapshot.queryParams["email_verification_token"];
    }

  }

  passwordMatchValidator(fg: FormGroup): { [key: string]: boolean } | null {
    const password = fg.get('password')?.value ?? '';
    const confirmPassword = fg.get('confirmPassword')?.value ?? '';
    return password === confirmPassword ? null : { 'mismatch': true };
  }
  
  toggleNewPasswordVisibility() { 
    this.newPasswordVisible = !this.newPasswordVisible;
  }

  toggleConfirmPasswordVisibility() { 
    this.confirmPasswordVisible = !this.confirmPasswordVisible;
  }

  onSubmit(){
     let object={
      "email":this.email,
      "email_verification_token": this.email_verification_token,
      "first_name": "",
      "last_name": "",
      "password": this.form.value.password,
      "conf_password": this.form.value.confirmPassword,
    }
    this.usersService.updatePasswordByEmailToken(object).subscribe({
      next: (response) => {
        if (response.status) {
          this.toaster.success('Password updated successfully', '',{
            positionClass: 'custom-toast-position'
          });
          this.router.navigate(['/login']);
        }
      },
      error: (error) => {
        console.log(error);
        this.errorHandlerService.handleError(error);
      } 
    })
  }
}
