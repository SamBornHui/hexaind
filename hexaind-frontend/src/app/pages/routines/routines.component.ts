import { ElementRef, Renderer2 } from '@angular/core';
import { Overlay, OverlayConfig } from '@angular/cdk/overlay';
import { ComponentPortal } from '@angular/cdk/portal';
import { ContextMenuComponent } from '../../controls/context-menu/context-menu.component';
import { ActivatedRoute, Router } from '@angular/router';
import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'app-routines',
  templateUrl: './routines.component.html',
  styleUrls: ['./routines.component.less'],
})
export class RoutinesComponent {
  @Output() workflowSelectedEvent = new EventEmitter<number>();

  constructor(
    private renderer: Renderer2,
    private el: ElementRef,
    private overlay: Overlay,
    private route: ActivatedRoute,
    private router: Router,
  ) {}

  displayedColumns: string[] = ['title', 'owner', 'cadence', 'lastRun'];
  dataSource = [
    {
      title: 'Weekly Ingestion',
      workspaceName: 'Workspace #1',
      owner: 'Mike Snow',
      cadence: 'Every Friday 12 AM PST',
      lastRun: '10/20/2023',
      id: 1,
    },
    {
      title: 'Daily Modeling',
      workspaceName: 'Workspace #2',
      owner: 'Rohan Lam',
      cadence: 'Daily 6 PM PST',
      lastRun: '10/26/2023',
      id: 2,
    },
    // ... Add more dummy data as needed
  ];

  onRowDblClick(row: any): void {
    console.log('Row double clicked:', row.id);
    this.workflowSelectedEvent.emit(row.id);
  }

  showContextMenu(event: MouseEvent) {
    const positionStrategy = this.overlay
      .position()
      .flexibleConnectedTo({ x: event.x, y: event.y })
      .withPositions([
        {
          originX: 'center',
          originY: 'center',
          overlayX: 'start',
          overlayY: 'top',
        },
      ]);

    const overlayRef = this.overlay.create(
      new OverlayConfig({
        positionStrategy: positionStrategy,
        hasBackdrop: true,
        backdropClass: 'cdk-overlay-transparent-backdrop',
      }),
    );

    overlayRef.attach(new ComponentPortal(ContextMenuComponent));
    overlayRef.backdropClick().subscribe(() => overlayRef.detach());
  }
}
