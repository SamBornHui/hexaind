import { Component, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { ConfigService } from 'src/app/services/config.service';

@Component({
  selector: 'app-image-details',
  templateUrl: './details.component.html',
  styleUrls: ['./details.component.less'],
})
export class ImageDetailsComponent {
  attributeForm: boolean = false;
  selectedMetadataOption: string = 'None';

  constructor(
  ) {
  }

  ngOnInit(): void {
  }

  ngAfterViewInit() {
  }

  ngOnDestroy() {
  }

  onResize(event?: Event) {
  }

  addAttribute() {
    this.attributeForm = !this.attributeForm;
  }
  
}
