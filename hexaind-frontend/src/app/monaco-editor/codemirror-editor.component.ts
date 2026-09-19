import { Component, OnInit, Inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { CodeMirrorEditorService } from './codemirror-editor.service';


@Component({
  selector: 'app-codemirror-editor',
  templateUrl: './codemirror-editor.component.html',
  styleUrls: ['./codemirror-editor.component.less']
})
export class CodeMirrorEditorComponent implements OnInit {
  editorOptions!: any;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
  ) { }

  ngOnInit(): void {
    this.editorOptions = {
      lineNumbers: true,
      mode: this.data.mode,
      theme: 'eclipse',
      tabSize: 2,
      smartIndent: true,
      matchBrackets: true,
      autofocus: true,
      readOnly: true
    };
  }
}

