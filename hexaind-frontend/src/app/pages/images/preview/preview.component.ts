import { Component, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { ConfigService } from 'src/app/services/config.service';
import { ImagePreviewComponent } from 'src/app/dialogs/image-preview/image-preview.component';

@Component({
  selector: 'app-images-preview',
  templateUrl: './preview.component.html',
  styleUrls: ['./preview.component.less'],
})
export class ImagesPreviewComponent {

  constructor(public dialog: MatDialog) { }

  ngOnInit(): void {
  }

  ngAfterViewInit() {
  }

  ngOnDestroy() {
  }

  onResize(event?: Event) {
  }

  imagePreview(): void {
    const dialogRef = this.dialog.open(ImagePreviewComponent, {
      width: '90%',
      height: '90%',
    });
  }

}
