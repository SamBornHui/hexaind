import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ProjectButtonVisibilityServiceService {
  private projectsButtonShown = new BehaviorSubject<boolean>(true);
  projectsButtonShown$ = this.projectsButtonShown.asObservable();

  constructor() {}

  // Method to hide button
  hideProjectsButton() {
    this.projectsButtonShown.next(false);
  }

  // Method to show button
  showProjectsButton() {
    this.projectsButtonShown.next(true);
  }
}
