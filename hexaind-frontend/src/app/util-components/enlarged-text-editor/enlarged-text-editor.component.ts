import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-enlarged-text-editor',
  templateUrl: './enlarged-text-editor.component.html',
  styleUrls: ['./enlarged-text-editor.component.less']
})
export class EnlargedTextEditorComponent {

  displayedData: any;
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<EnlargedTextEditorComponent>,
  ) {}

  ngOnInit() {
    this.displayedData = this.data.dataTobeDisplayed;
  }

  onSave() {
    this.dialogRef.close({
      isSaved: true,
      data: this.displayedData
    })
  }

  onCancel() {
    this.dialogRef.close({
      isSaved: false
    })
  }
  
}
