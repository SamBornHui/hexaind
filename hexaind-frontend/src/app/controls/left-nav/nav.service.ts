// nav.service.ts
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class NavService {
  isNavCollapsed = false;

  toggleNav(): void {
    this.isNavCollapsed = !this.isNavCollapsed;
  }
}
