import { Component, Input } from '@angular/core';
import { DataPreviewService } from '../services/data-preview.service'
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';

@Component({
  selector: 'app-visualize',
  templateUrl: './visualize.component.html',
  styleUrls: ['./visualize.component.less']
})
export class VisualizeComponent {
  @Input() dataset_id!: string;

  compareInstances = [1];
  visualizationType: string = "DISTRIBUTION"
  interactive: boolean = false

  constructor() { }

  addCompareInstances(): void {
    if (this.compareInstances.length === 1) {
      this.compareInstances.push(this.compareInstances.length + 1);
    } else {
      this.compareInstances.pop();
    }
  }

  onChangeInteractive(event: MatSlideToggleChange) {
    this.interactive = !event.checked
  }
}
