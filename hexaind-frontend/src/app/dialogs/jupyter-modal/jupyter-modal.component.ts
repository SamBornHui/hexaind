import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-jupyter-modal',
  templateUrl: './jupyter-modal.component.html',
  styleUrls: ['./jupyter-modal.component.less']
})
export class JupyterModalComponent {
  safeUrl: SafeResourceUrl;

  constructor(
    public dialogRef: MatDialogRef<JupyterModalComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { url: string },
    private sanitizer: DomSanitizer
  ) {
    this.safeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(this.data.url);
  }

  closeModal(): void {
    this.dialogRef.close();
  }
}
