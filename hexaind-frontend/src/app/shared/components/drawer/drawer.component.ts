import {
  animate,
  state,
  style,
  transition,
  trigger,
} from '@angular/animations';
import {
  Component,
  EventEmitter,
  HostBinding,
  Input,
  Output,
} from '@angular/core';
import { ButtonComponent } from '../button/button.component';

@Component({
  selector: 'mst-drawer',
  templateUrl: './drawer.component.html',
  styleUrls: ['./drawer.component.scss'],
  standalone: true,
  imports: [ButtonComponent],
  animations: [
    trigger('slideInOut', [
      state('openRight', style({ transform: 'translateX(0%)' })),
      state('closed', style({ transform: 'translateX(100%)' })), // Adjust for initial state
      transition('closed => openRight', [animate('250ms ease-in-out')]),
      transition('openRight => closed', [animate('250ms ease-in-out')]),
    ]),
  ],
})
export class DrawerComponent {
  // support the right side only for now.
  private openDirection = 'right';
  @Input() title = '';
  @Input() isOpen = false;
  @Input() width = '300px';
  @Input() zIndex = 1000;
  @Output() isOpenChange = new EventEmitter<boolean>();
  @HostBinding('@slideInOut') get slideInOut() {
    return this.isOpen
      ? `open${this.openDirection
          .charAt(0)
          .toUpperCase()}${this.openDirection.slice(1)}`
      : 'closed';
  }

  @HostBinding('class.hidden') get hidden() {
    return !this.isOpen;
  }
  @HostBinding('style.--panel-width') get hostWidth() {
    return this.width;
  }
  @HostBinding('style.--panel-z-index') get hostZIndex() {
    return this.zIndex;
  }

  toggle() {
    this.isOpen = !this.isOpen;
    this.isOpenChange.emit(this.isOpen);
  }
}
