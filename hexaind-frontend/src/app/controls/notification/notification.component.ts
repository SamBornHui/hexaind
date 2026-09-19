import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-notification',
  templateUrl: './notification.component.html',
  styleUrls: ['./notification.component.less'],
})
export class NotificationComponent {
  @Input() message: string = '';
  @Input() type: 'success' | 'error' | 'warning' = 'success'; // default to 'success'
  show: boolean = false;

  constructor() { }

  // Function to display notification
  public display(message: string, type: 'success' | 'error' | 'warning'): void {
    this.message = message;
    this.type = type;
    this.show = true;

    if (type === 'success') {
      // Set a timer to hide the notification after 5 seconds
      setTimeout(() => {
        this.show = false;
      }, 4000);
    } else {
      // Set a timer to hide the notification after 5 seconds
      setTimeout(() => {
        this.show = false;
      }, 7000);
    }
  }
}
