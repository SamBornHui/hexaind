import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { IdNameData } from '../../models';

@Component({
  selector: 'mst-list-item-parent-names',
  templateUrl: './list-item-parent-names.component.html',
  styleUrls: ['./list-item-parent-names.component.scss'],
  standalone: true,
  imports: [CommonModule],
})
export class ListItemParentNamesComponent {
  @Input() item!: IdNameData;
  @Input() separator = '/';
}
