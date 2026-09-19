import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  HostBinding,
  HostListener,
  Input,
  Output,
  TemplateRef,
} from '@angular/core';
import { ButtonComponent } from '../button/button.component';
import { IconComponent } from '../icon/icon.component';
import { InputComponent } from '../input/input.component';
import { IdNameData } from '../models';

@Component({
  selector: 'mst-list-item',
  templateUrl: './list-item.component.html',
  styleUrls: ['./list-item.component.scss'],
  standalone: true,
  imports: [CommonModule, IconComponent, ButtonComponent, InputComponent],
})
export class ListItemComponent {
  @Input() index = 0;
  @Input() multiSelect = false;
  @Input() className = '';
  @Input() iconNames?: string[];
  @Input() rightIconNames?: string[];
  @Input() template?: TemplateRef<any>;
  @Input() item!: IdNameData;
  @Input() draggable = false;
  @Input() selected = false;
  @Input() selectedItemHighlight = true;
  @Input() keepBottomBorder = false;
  @Output() iconClick = new EventEmitter<{
    index: number;
    name: string;
    item: IdNameData;
  }>();
  @Output() itemDragStart = new EventEmitter<{
    e: DragEvent;
    item: IdNameData;
  }>();
  @Output() itemDragEnd = new EventEmitter<{
    e: DragEvent;
    item: IdNameData;
  }>();
  @HostBinding('draggable') get isDraggable() {
    return this.draggable;
  }
  @HostBinding('class.keep-border') get keepBorder() {
    return this.keepBottomBorder;
  }
  @HostBinding('class.selected') get isSelected() {
    return this.selected;
  }
  @HostBinding('class.no-selected-style') get isSelectedItemHighlight() {
    return !this.selectedItemHighlight;
  }
  @HostBinding('class.has-left-icon') get hasLeftIcon() {
    return (this.iconNames && this.iconNames.length > 0) || this.multiSelect;
  }
  @HostBinding('class.has-right-icon') get hasRightIcon() {
    return this.rightIconNames && this.rightIconNames.length > 0;
  }
  @HostListener('dragstart', ['$event'])
  onDragStart(event: DragEvent) {
    this.el.nativeElement.classList.add('dragging');
    event.dataTransfer?.setData('application/json', JSON.stringify(this.item));
    this.itemDragStart.emit({ e: event, item: this.item });
  }
  @HostListener('dragend', ['$event'])
  onDragEnd(event: DragEvent) {
    this.el.nativeElement.classList.remove('dragging');
    this.itemDragEnd.emit({ e: event, item: this.item });
  }

  constructor(private el: ElementRef) {}

  onIconClick(e: Event, name = '') {
    e.stopPropagation();
    this.iconClick.emit({ index: this.index, name, item: this.item });
  }
}
