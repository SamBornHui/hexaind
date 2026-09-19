import { Injectable } from '@angular/core';
import {
  Router,
  CanActivate,
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
} from '@angular/router';

// import { ToastrService } from 'ngx-toastr';

@Injectable()
export class AuthGuard implements CanActivate {
  moduleList: any;
  permittedUrls: any = [];
  constructor(private router: Router) {}

  activeStatus = false;
  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot) {
    var stateurl = state.url;
    //return true; //TODO: @rohan - remove this once user login is implemented.

    if (localStorage.getItem('currentUser')) {
      return true;
    } else {
      // not logged in so redirect to login page with the return url
      this.router.navigate(['login'], {
        //queryParams: { returnUrl: state.url }, 
      });
      return false;
    }
  }
}
