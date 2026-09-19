import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.less'],
})
export class AppComponent implements OnInit {
  public IsLoggedIn: boolean = true;
  subscription: Subscription = new Subscription();

  currentComponent = 'workflow-designer';

  constructor(
    private authService: AuthService,
    private router: Router,
  ) {
    this.authService.isLoggedIn$.subscribe((isLoggedIn) => {
      this.IsLoggedIn = isLoggedIn;

      if (this.IsLoggedIn) {
        this.router.navigate(['/login']);
      }
    });
  }

  ngOnInit(): void { }
}
