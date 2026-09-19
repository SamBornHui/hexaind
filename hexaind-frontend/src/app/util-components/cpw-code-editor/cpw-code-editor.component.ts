import { Component, EventEmitter, Inject, Output, ViewChild } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ConfigService } from 'src/app/services/config.service';

@Component({
  selector: 'app-cpw-code-editor',
  templateUrl: './cpw-code-editor.component.html',
  styleUrls: ['./cpw-code-editor.component.less'],
})
export class CpwCodeEditorComponent {
  @Output() saveEvent = new EventEmitter<any>()
  arrayOfFiles: any;
  selectedFileContent: string = "";
  selectedFileName: string = "";
  selectedFileIndex: any;
  argumentsForPythonFunction: any;
  isTerminalVisible = true;
  backendLogs: any = [];
  isEditingInWorkflow = false;
  isSavingInProgress = false;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<CpwCodeEditorComponent>,
  ) {}

  ngOnInit() {
    this.arrayOfFiles = this.data.arrayOfFiles;
    this.argumentsForPythonFunction = this.data.argumentsForPythonFunction
    this.isEditingInWorkflow = this.data.isEditingInWorkflow
    if(this.arrayOfFiles[0]) {
      this.selectedFileIndex = 0
      this.selectedFileContent = this.arrayOfFiles[0].content
      this.selectedFileName = this.arrayOfFiles[0].name
    }
  }

  objectEntries(obj: any): [string, any][] {
    return Object.entries(obj);
  }

  changeFileContentInTheEditor(file: any, index: any) {
    this.selectedFileIndex = index
    this.selectedFileContent = file.content
  }

  saveFileChanges($event: any) {
    this.arrayOfFiles[this.selectedFileIndex].content = $event
  }

  updateBackendLogs(logMessage: any) {
    
    this.backendLogs[0] = logMessage
  }

  async runThePythonCode() {
    let data = {
      code:  this.arrayOfFiles[this.selectedFileIndex].content,
      arguments: this.argumentsForPythonFunction
    }
    let response = await fetch('http://127.0.0.1:8000/execute', {
      method: 'POST', // HTTP method
      headers: {
        'Content-Type': 'application/json', // Indicate that we are sending JSON data
      },
      body: JSON.stringify(data) // Convert the JavaScript object to a JSON string
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    let processResponse = await response.json()
    this.backendLogs = [processResponse.success,processResponse.output,processResponse.result]
    if(processResponse.success) {
      this.backendLogs[0] = "Function got executed successfully with the give parameters"
    }
    else {
      this.backendLogs[1] = "FUNCTION EXECUTION FAILED"
    }

  }

  onSave() {
   this.saveEvent.emit()
  }

  onCancel() {
    this.dialogRef.close({
      isSaved: false,
    });
  }
}


