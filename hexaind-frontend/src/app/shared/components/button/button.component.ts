import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  HostBinding,
  Input,
  Output,
  TemplateRef,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { IconComponent } from '../icon/icon.component';

/**
 * Wrapper component for the Material Button component. To override styles or functionality
 */

@Component({
  selector: 'mst-button',
  templateUrl: './button.component.html',
  styleUrls: ['./button.component.scss'],
  standalone: true,
  imports: [IconComponent, CommonModule, MatButtonModule, MatMenuModule],
})
export class ButtonComponent {
  @Input() styleName: 'flat' | 'stroked' | 'raised' | 'icon' | 'menu' =
    'stroked';
  @Input() label = '';
  @Input() type = 'button';
  @Input() iconName = '';
  @Input() disabled = false;
  @Input() color: 'primary' | 'accent' | 'warn' = 'primary';
  @Input() menu?: TemplateRef<any>;
  @Input() @HostBinding('style.width.px') width =
    this.styleName === 'icon' ? 32 : undefined;
  @Output() click = new EventEmitter<Event>();
  @HostBinding('class') get dynamicHostClass() {
    return 'mst-button--' + this.styleName;
  }
  @HostBinding('class.disabled')
  get isDisabled() {
    return this.disabled;
  }

  onClick(e: Event) {
    this.click.emit(e);
    e.stopPropagation();
  }
}
