import { Component, Input } from '@angular/core';
import { MatTooltipModule } from '@angular/material/tooltip';
import { IconComponent } from '../icon/icon.component';

@Component({
  selector: 'mst-hint',
  templateUrl: './hint.component.html',
  styleUrls: ['./hint.component.scss'],
  standalone: true,
  imports: [IconComponent, MatTooltipModule],
})
export class HintComponent {
  @Input() hint!: string;
  @Input() iconName = 'info';
  @Input() titleOnly = true; // Material Tooltip doesn't support position:sticky. this will be removed after we have a new tooltip component.
}
