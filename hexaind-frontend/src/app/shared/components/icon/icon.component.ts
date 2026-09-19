import { Component, Input } from '@angular/core';

@Component({
  selector: 'mst-icon',
  templateUrl: './icon.component.html',
  styleUrls: ['./icon.component.scss'],
  standalone: true,
})
export class IconComponent {
  @Input() iconName!: string;

  @Input() options: {
    fill?: number;
    weight?: number;
    grad?: number;
    opsz?: number;
  } = {
    fill: 0,
    weight: 400,
    grad: 0,
    opsz: 20,
  };

  get fontVariationSettings() {
    const { fill = 0, weight = 400, grad = 0, opsz = 20 } = this.options;
    return `'FILL' ${fill}, 'wght' ${weight}, 'GRAD' ${grad}, 'opsz' ${opsz}`;
  }
}
