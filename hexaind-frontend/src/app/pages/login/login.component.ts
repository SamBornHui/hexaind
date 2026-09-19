import { UsersService } from '../users/users.service';
import { ChangeDetectorRef, Component, ViewChild } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { PrivacyPolicyComponent } from '../../dialogs/privacy-policy/privacy-policy.component';
import { LicenseAgreementComponent } from '../../dialogs/license-agreement/license-agreement.component';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, NgForm, FormGroup, Validators } from '@angular/forms';
import { UserLoginService } from './login.service';
import { OAuthService } from 'angular-oauth2-oidc';
import { authConfig } from 'src/environments/environment';
import { ErrorHandlerService } from 'src/app/services/error-handler.service';
import { ToastrService } from 'ngx-toastr';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.less'],
})
export class LoginComponent {
  usersList: any;
  passwordVisible: boolean = false;
  email: string = '';
  password: string = '';
  rememberMe: boolean = true;
  private dialogRefPrivacyPolicy!: MatDialogRef<PrivacyPolicyComponent>;
  private dialogRefLicenseAgreement!: MatDialogRef<LicenseAgreementComponent>;

  emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  currentYear: number = new Date().getFullYear();
  userInvalid: boolean = false;
  userId: any;
  rememberMeFlag: boolean = false;
  msgtype: string = 'success';
  message: string = '';
  errorMessage: string = ' ';
  showErr: boolean = false;
  showMsg: boolean = false;
  showFGErr: boolean = false;
  loginForm: FormGroup;
  gcpTokenId: string = '';
  showLoader: boolean = false;
  title: string = '';
  loginMethod: any;
  is_valid: boolean = false;

  constructor(
    private authService: AuthService,
    private usersService: UsersService,
    private userLoginService: UserLoginService,
    public dialog: MatDialog,
    private router: Router,
    private fb: FormBuilder,
    private oauthService: OAuthService,
    private activatedRoute: ActivatedRoute,
    private errorHandlerService: ErrorHandlerService,
    public toaster: ToastrService,
  ) {
    this.loginForm = this.fb.group({
      password: ['', [Validators.required]],
      email: ['', [Validators.required]],
      rememberMe: [false],
    });
    const savedEmail = localStorage.getItem('savedEmail');
    const savedPassword = localStorage.getItem('savedPassword');

    if (savedEmail) {
      this.email = savedEmail;
      this.rememberMe = true;
    }
    if (savedPassword) {
      this.password = savedPassword;
      this.rememberMe = true;
    }
  }
  ngOnInit(): void {
    this.getLoginMethods();

    this.oauthService.configure(authConfig.authConfig);
    this.activatedRoute.fragment.subscribe((fragment: any) => {
      if (fragment) {
        this.showLoader = true;
        this.title = 'GCP';
        const params = new URLSearchParams(fragment);
        this.gcpTokenId = params.get('id_token') || '';
        let obj = {
          type: 'GCP',
          gcp_id_token: this.gcpTokenId,
        };
        this.userLoginService.SSOLogin(obj).subscribe({
          next: (response: any) => {
            if (response) {
              this.userId = response.user_data._id;
              var currentUser = response.user_data;
              currentUser['access_token'] = response.access_token;
              currentUser['refresh_token'] = response.refresh_token;
              localStorage.setItem('currUserID', response.user_data._id);
              localStorage.setItem('currentUser', JSON.stringify(currentUser));
              localStorage.setItem(
                'role_id_sso',
                response.user_data.server_role_value,
              );
              localStorage.setItem('access_token', response.access_token);
              this.authService.setLoggedIn(true);
              this.router.navigate(['/']);
              this.toaster.success('Login successful', '', {
                positionClass: 'custom-toast-position',
              });
              this.title = '';
              this.showLoader = false;
            }
          },
          error: (error) => {
            if (error.status == 401) {
              this.showLoader = false;
              this.router.navigate(['/login']);
              this.toaster.error('User not found. Please try again', '', {
                positionClass: 'custom-toast-position',
              });
            } else {
              this.showLoader = false;
              this.router.navigate(['/login']);
              this.toaster.error('Login failed', '', {
                positionClass: 'custom-toast-position',
              });
            }
          },
        });
      }
    });
  }

  getLoginMethods() {
    this.userLoginService.loginMethod().subscribe({
      next: (response: any) => {
        console.log(response);
        this.loginMethod = response;
        this.userLoginService.setLoginMethod(response);
      },
      error: (error: any) => {
        console.log(error);
        this.errorHandlerService.handleError(error);
      },
    });
  }

  togglePasswordVisibility() {
    this.passwordVisible = !this.passwordVisible;
  }

  forgotPassword() {
    const email = this.loginForm.value.email.trim();
    if (email === '') {
      this.toaster.error('Please enter your email', '', {
        positionClass: 'custom-toast-position',
      });
      return;
    }
    this.isValidEmail(email).subscribe((valid_email) => {
      console.log(valid_email);
      if (!valid_email) {
        // this.toaster.error('Enter valid email address', '', {
        //   positionClass: 'custom-toast-position',
        // });
        // return;
        this.showFGErr = true;
        this.errorMessage = 'User not found. Enter valid email address.';
        this.msgtype = 'fail';
        this.showMsg = true;
        this.showLoader = false;
        this.title = '';
      } else {
        this.showFGErr = false;
        this.userLoginService
          .resetPasswordByUser(email, 'User initiated')
          .subscribe({
            next: (response: any) => {
              console.log(response);
              if (response) {
                this.toaster.success(
                  'Reset password link sent to your email',
                  '',
                  {
                    positionClass: 'custom-toast-position',
                  },
                );
              }
            },
            error: (error: any) => {
              this.errorHandlerService.handleError(error);
            },
          });
      }
    });
  }

  isValidEmail(email: string): Observable<boolean> {
    return this.userLoginService.getUsersList(email).pipe(
      map((response: any) => {
        console.log(response);
        return true;
      }),
      catchError((error) => {
        console.error(error);
        return of(false);
      }),
    );
  }

  showEULA() {
    this.dialogRefLicenseAgreement = this.dialog.open(
      LicenseAgreementComponent,
      {
        width: '100%', // Optional: You can set width, height, etc.
      },
    );

    this.dialogRefLicenseAgreement.componentInstance.requestClose.subscribe(
      () => {
        this.dialogRefLicenseAgreement.close();
      },
    );
  }

  showPrivacyPolicy() {
    this.dialogRefPrivacyPolicy = this.dialog.open(PrivacyPolicyComponent, {
      width: '100%', // Optional: You can set width, height, etc.
    });

    this.dialogRefPrivacyPolicy.componentInstance.requestClose.subscribe(() => {
      this.dialogRefPrivacyPolicy.close();
    });
  }

  loginUser() {
    this.showLoader = true;
    this.title = 'Databrick';
    this.showMsg = false;
    var loginInfo = {
      email: this.email,
      password: this.password,
    };
    this.userLoginService.userLogin(loginInfo).subscribe(
      (response) => {
        console.log(response);
        if (response.status == '200') {
          this.userId = response.body.user_data._id;
          var currentUser = response.body.user_data;
          console.log(currentUser, 'current user value');
          currentUser['access_token'] = response.body.access_token;
          currentUser['refresh_token'] = response.body.refresh_token;
          if (this.rememberMe) {
            this.rememberUser();
          }
          localStorage.setItem('currUserID', response.body.user_data._id);
          localStorage.setItem('currentUser', JSON.stringify(currentUser));
          localStorage.setItem('access_token', response.body.access_token);
          localStorage.setItem('role_id', currentUser.server_role_value);
          this.authService.setLoggedIn(true);
          this.showLoader = false;
          this.title = '';
          this.toaster.success('Login successful', '', {
            positionClass: 'custom-toast-position',
          });
          this.router.navigate(['/']);
        } else {
          this.message = 'Invalid Email or Password. Please try again.';
          this.msgtype = 'fail';
          this.showMsg = true;
          this.showLoader = false;
          this.title = '';
          this.toaster.error(this.message, '', {
            positionClass: 'custom-toast-position',
          });
        }
      },
      (error) => {
        console.log(error);
        if (error.status == 401) {
          this.message = error.error.reason
            ? error.error.reason
            : 'User not found. Please try again.';
          this.msgtype = 'fail';
          this.showMsg = true;
          this.showLoader = false;
          this.title = '';
          this.toaster.error(this.message, '', {
            positionClass: 'custom-toast-position',
          });
        } else if (error.status == 404) {
          this.message = 'User not found. Please try again.';
          this.msgtype = 'fail';
          this.showMsg = true;
          this.showLoader = false;
          this.title = '';
          this.toaster.error(this.message, '', {
            positionClass: 'custom-toast-position',
          });
        } else if (
          error.error.detail.includes(
            "Failed with exception 'JSONResponse' object has no attribute 'user_data'",
          )
        ) {
          this.errorMessage = 'Username or Password invalid. Please try again.';
          this.showErr = true;
          this.message = 'User not found. Please try again.';
          this.msgtype = 'fail';
          this.showMsg = true;
          this.showLoader = false;
          this.title = '';
          // this.toaster.error(this.message, '', {
          //   positionClass: 'custom-toast-position',
          // });
        } else {
          this.showMsg = true;
          this.showLoader = false;
          this.title = '';
          this.errorHandlerService.handleError(error);
        }
      },
    );
  }

  rememberUser() {
    localStorage.setItem('savedEmail', this.email);
    localStorage.setItem('savedPassword', this.password);
  }

  azurelogin() {
    this.authService.azureAuthentication().subscribe({
      next: (data) => {
        if (data) {
          let obj = {
            type: 'Azure',
            access_token: data.accessToken,
            raw_token: data.idToken.rawIdToken,
          };
          this.showLoader = true;
          this.title = 'Azure';
          this.userLoginService.SSOLogin(obj).subscribe({
            next: (response: any) => {
              if (response) {
                this.userId = response.user_data._id;
                var currentUser = response.user_data;
                currentUser['access_token'] = response.access_token;
                currentUser['refresh_token'] = response.refresh_token;
                localStorage.setItem('access_token', response.access_token);
                if (this.rememberMe) {
                  this.rememberUser();
                }
                localStorage.setItem('currUserID', response.user_data._id);
                localStorage.setItem('role_id', currentUser.server_role_value);
                localStorage.setItem(
                  'currentUser',
                  JSON.stringify(currentUser),
                );
                this.authService.setLoggedIn(true);
                this.toaster.success('Login successful', '', {
                  positionClass: 'custom-toast-position',
                });
                this.router.navigate(['/']);
                this.showLoader = false;
                this.title = '';
              }
            },
            error: (error) => {
              if (error.status == 401) {
                this.showLoader = false;
                this.title = '';
                this.toaster.error('User not found. Please try again', '', {
                  positionClass: 'custom-toast-position',
                });
              } else {
                console.error('Login failed', error);
                // this.errorHandlerService.handleError(error);
                this.showLoader = false;
                this.title = '';
                this.toaster.error(
                  'Login issue with Azure. Please try again',
                  '',
                  {
                    positionClass: 'custom-toast-position',
                  },
                );
              }
            },
          });
        }
      },
      error: (error) => {
        this.showLoader = false;
        this.title = '';
        console.error('Login or token acquisition failed', error);
        this.toaster.error(
          'Login or token acquisition failed ClientAuthError',
          '',
          {
            positionClass: 'custom-toast-position',
          },
        );
      },
    });
  }

  GCPlogin(): void {
    this.showLoader = true;
    this.title = 'GCP';
    this.oauthService.initCodeFlow();
  }
}
