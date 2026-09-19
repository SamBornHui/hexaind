import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

@Component({
  selector: 'app-prompt-save',
  templateUrl: './prompt-save.component.html',
  styleUrls: ['./prompt-save.component.less'],
})
export class PromptSaveComponent {
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<PromptSaveComponent>,
  ) {}
}
