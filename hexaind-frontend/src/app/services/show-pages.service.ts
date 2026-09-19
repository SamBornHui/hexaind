// show-pages.service.ts
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class ShowPagesService {
  public showingPages: { [key: string]: boolean } = {
    Projects: false, // Set the default state for the 'Projects' page
    Workflows: true,
    AdminUsers: true,
    Data: true,
    Models: true,
    Connectors: true
    // Add other pages and their default states as needed
  };

  constructor() {}
}
