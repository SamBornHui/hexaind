import { Component, OnInit } from '@angular/core';
import { RegisterAccountService } from './services/register-user.service';
import { MatDialog } from '@angular/material/dialog';
import { Router, ActivatedRoute } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';

@Component({
  selector: 'app-register-account',
  templateUrl: './register-account.component.html',
  styleUrls: ['./register-account.component.less'],
})
export class RegisterAccountComponent implements OnInit {
  passwordVisible: boolean = false;
  confirmPasswordVisible: boolean = false;
  fname: string = '';
  lname: string = '';
  password: string = '';
  confirmPassword: string = '';
  email: string = '';
  emailVerificationToken: string = '';
  rememberMe: boolean = false;
  error: boolean = false;
  errorMessage: string = '';
  form!: FormGroup;

  currentYear: number = new Date().getFullYear();
  user_type: string = '';
  showLoader: boolean = false;

  constructor(
    private authService: RegisterAccountService,
    public dialog: MatDialog,
    private router: Router,
    public activatedRoute: ActivatedRoute,
    private fb: FormBuilder,
    public toaster: ToastrService,
    public errorHandlerService: ErrorHandlerService,
  ) {
    this.form = this.fb.group(
      {
        firstName: ['', Validators.required],
        lastName: ['', Validators.required],
        email: [{ value: '', disabled: true }],
        password: [
          '',
          [
            Validators.required,
            Validators.minLength(12),
            Validators.pattern(
              '^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[\\W_]).{12,}$',
            ),
          ],
        ],
        confirmPassword: ['', Validators.required],
      },
      { validator: this.passwordMatchValidator },
    );
  }

  passwordMatchValidator(fg: FormGroup): { [key: string]: boolean } | null {
    const password = fg.get('password')?.value ?? '';
    const confirmPassword = fg.get('confirmPassword')?.value ?? '';
    return password === confirmPassword ? null : { mismatch: true };
  }

  get formValues() {
    return this.form.controls;
  }

  ngOnInit() {
    if (this.activatedRoute.snapshot.queryParams['email_verification_token']) {
      this.showLoader = true;
      this.user_type = this.activatedRoute.snapshot.queryParams['user_type'];
      if (this.user_type === 'SSO') {
        let object = {
          email: this.activatedRoute.snapshot.queryParams['email'],
          email_verification_token:
            this.activatedRoute.snapshot.queryParams[
              'email_verification_token'
            ],
        };
        this.authService.activateSSOUser(object).subscribe({
          next: (response) => {
            if (response.status) {
              this.toaster.success('User registered successfully', '', {
                positionClass: 'custom-toast-position',
              });
              this.router.navigate(['/login']);
              this.showLoader = false;
            } else {
              this.toaster.error('User not registered', '', {
                positionClass: 'custom-toast-position',
              });
              this.showLoader = false;
            }
          },
          error: (error) => {
            console.log(error);
            this.errorHandlerService.handleError(error);
            setTimeout(() => {
              this.toaster.error('User not registered', '', {
                positionClass: 'custom-toast-position',
              });
            }, 5000);
            this.router.navigate(['/login']);
            this.showLoader = false;
          },
        });
      } else {
        this.handleUserRegistration();
      }
    }
  }

  togglePasswordVisibility() {
    this.passwordVisible = !this.passwordVisible;
  }

  toggleConfirmPasswordVisibility() {
    this.confirmPasswordVisible = !this.confirmPasswordVisible;
  }

  async handleUserRegistration() {
    this.email = this.activatedRoute.snapshot.queryParams['email'];
    const isAlreadyRegistered = await this.isUserAlreadyRegistered(this.email);
    if (isAlreadyRegistered) {
      this.toaster.success('User already registered', '', {
        positionClass: 'custom-toast-position',
      });
      this.router.navigate(['/login']);
      this.showLoader = false;
    } else {
      this.form.patchValue({ email: this.email });
      this.emailVerificationToken =
        this.activatedRoute.snapshot.queryParams['email_verification_token'];
      this.user_type = this.activatedRoute.snapshot.queryParams['user_type'];
      this.showLoader = false;
    }
  }

  async isUserAlreadyRegistered(email: string): Promise<boolean> {
    try {
      const response = await this.authService
        .isUserAlreadyRegistered(email)
        .toPromise();
      return response;
    } catch (error) {
      console.error('Error checking user registration:', error);
      return false;
    }
  }

  async onSubmit() {
    let userData = {
      email: this.email,
      password: this.form.value.password,
      conf_password: this.form.value.confirmPassword,
      email_verification_token: this.emailVerificationToken,
      first_name: this.form.value.firstName,
      last_name: this.form.value.lastName,
    };
    try {
      const response = await this.authService.registerAccount(userData);
      if (response.status) {
        this.toaster.success('User registered successfully', '', {
          positionClass: 'custom-toast-position',
        });
        this.router.navigate(['/login']);
      } else {
        this.toaster.error('User not registered', '', {
          positionClass: 'custom-toast-position',
        });
      }
    } catch (error: any) {
      console.error('API Error:', error);
      this.errorHandlerService.handleError(error);
    }
  }
}
