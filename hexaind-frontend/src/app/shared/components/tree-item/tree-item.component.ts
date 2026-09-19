import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ButtonComponent } from '../button/button.component';
import { IconComponent } from '../icon/icon.component';
import { LoaderComponent } from '../loader/loader.component';
import { SimpleObject, TreeData } from '../models';

@Component({
  selector: 'mst-tree-item',
  templateUrl: './tree-item.component.html',
  styleUrls: ['./tree-item.component.scss'],
  standalone: true,
  imports: [ButtonComponent, IconComponent, LoaderComponent, CommonModule],
  host: {
    '[style.paddingLeft.px]': 'levelIndent * item.level',
  },
})
export class TreeItemComponent {
  @Input() index = 0;
  @Input() item!: TreeData | SimpleObject;
  @Input() levelIndent = 16;
  @Input() keyField = 'id';
  @Input() nameField = 'name';
  @Input() iconField = 'iconName';
  @Output() arrowClick = new EventEmitter<{
    item: TreeData | SimpleObject;
    index: number;
  }>();
  onArrowClick(e: Event) {
    this.arrowClick.emit({ item: this.item, index: this.index });
  }
}
