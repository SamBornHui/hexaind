import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  Output,
  ViewChild,
} from '@angular/core';
import { Direction, ResizeInfo } from '../models';

@Component({
  selector: 'mst-resizer',
  templateUrl: './resizer.component.html',
  styleUrls: ['./resizer.component.scss'],
  standalone: true,
  imports: [CommonModule],
})
export class ResizerComponent {
  @ViewChild('indicator') indicator!: ElementRef;

  @Input() directions: Direction[] = ['left', 'right', 'top', 'bottom'];
  @Output() resize = new EventEmitter<ResizeInfo>();

  private isResizing = false;
  private initialXY!: { x: number; y: number };
  private parentSize!: { width: number; height: number };
  private initialIndicatorPosition = 0;
  indicatorPosition = 0;
  direction: Direction = 'left';

  updateIndicatorPosition(event: MouseEvent) {
    let offsetX = 0;
    let offsetY = 0;
    if (this.direction === 'right') {
      offsetX = this.parentSize.width;
    }
    if (this.direction === 'bottom') {
      offsetY = this.parentSize.height;
    }
    this.indicatorPosition = ['left', 'right'].includes(this.direction)
      ? event.clientX - this.initialXY.x + offsetX
      : event.clientY - this.initialXY.y + offsetY;
  }

  onResizeStart(event: MouseEvent, direction: Direction) {
    event.preventDefault();
    const size = this.el.nativeElement.parentElement.getBoundingClientRect();
    this.parentSize = { width: size.width, height: size.height };
    this.direction = direction;
    this.isResizing = true;
    this.initialXY = { x: event.clientX, y: event.clientY };
    this.indicator.nativeElement.classList.add(
      `mst-resizer__bar--${direction}`,
    );
    this.updateIndicatorPosition(event);
    this.initialIndicatorPosition = this.indicatorPosition;
    this.indicator.nativeElement.style.display = 'block';
    // console.log('onResizeStart', this.indicator.nativeElement);
  }

  @HostListener('document:mousemove', ['$event'])
  onResize(event: MouseEvent) {
    if (!this.isResizing) {
      return;
    }
    this.updateIndicatorPosition(event);
  }

  @HostListener('document:mouseup')
  onResizeEnd() {
    if (!this.isResizing) {
      return;
    }
    this.isResizing = false;
    this.indicator.nativeElement.style.display = 'none';
    this.indicator.nativeElement.classList.remove(
      `mst-resizer__bar--${this.direction}`,
    );
    // Calculate deltaX and resize panels only after resizing is done
    const delta = this.indicatorPosition - this.initialIndicatorPosition;
    // console.log('onResizeEnd', delta);
    this.resize.emit({ delta, direction: this.direction, ...this.parentSize });
  }

  constructor(private el: ElementRef) {}
}
