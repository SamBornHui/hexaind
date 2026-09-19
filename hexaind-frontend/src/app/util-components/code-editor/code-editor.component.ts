import {
  Component,
  ElementRef,
  Input,
  OnInit,
  OnDestroy,
  Output,
  EventEmitter,
  SimpleChanges,
} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { python } from '@codemirror/lang-python';
import { javascript } from '@codemirror/lang-javascript';
import { autocompletion, completionKeymap } from '@codemirror/autocomplete';
import { Diagnostic, lintGutter, setDiagnostics } from '@codemirror/lint';
import { EditorView, keymap, lineNumbers } from '@codemirror/view';
import { EditorState, StateEffect } from '@codemirror/state';
import { oneDark } from '@codemirror/theme-one-dark';
import { defaultKeymap, historyKeymap, indentWithTab } from '@codemirror/commands';
import { indentUnit, LanguageSupport } from '@codemirror/language';
import { history } from '@codemirror/commands';
import { debounceTime, switchMap } from 'rxjs';
import { ConfigService } from 'src/app/services/config.service';
import { vscodeDark } from '@uiw/codemirror-theme-vscode';
interface CodeMirrorLanguages {
  [key: string]: () => LanguageSupport;
}

@Component({
  selector: 'app-code-editor',
  template: `<div class="editor-container"></div>`,
  styles: [
    `
      .editor-container {
        width: 90vw;
        height: 86vh; /* Set the container height */
        overflow: auto; /* Hide the scrollbars of the container itself */
        display: flex;
        flex-direction: column;
        padding: 5px;
      }
      .editor-container:hover {
        cursor: text
      }
    `,
  ],
})

export class CodeEditorComponent implements OnInit, OnDestroy {
  @Input() code: string = '';
  @Input() readonly: boolean = false;
  @Input() linesToHighlight: any;
  @Input() language: 'python' | 'javascript' = 'python';
  @Output() codeChange = new EventEmitter<string>();
  editor!: EditorView;
  codeChangeSubjectForErrorcheck: any = new EventEmitter<any>();

  private supportedLanguages: CodeMirrorLanguages = {
    python: () => python(),
    javascript: () => javascript(),
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (
      changes['code'] &&
      this.editor &&
      this.editor.state.doc.toString() !== this.code
    ) {
      this.editor.dispatch({
        changes: {
          from: 0,
          to: this.editor.state.doc.length,
          insert: this.code,
        },
      });
    }
  }
  constructor(private el: ElementRef, private http: HttpClient, private configService: ConfigService) {}

  ngOnInit(): void {
    const editorContainer =
      this.el.nativeElement.querySelector('.editor-container');

    const languageExtension = this.supportedLanguages[this.language]
      ? this.supportedLanguages[this.language]()
      : null;
    const pythonIndent = this.language === 'python' ? indentUnit.of('    ') : []; // 4 spaces for Python

    this.editor = new EditorView({
      state: EditorState.create({
        doc: this.code,
        extensions: [
          languageExtension ? languageExtension : [],
          autocompletion(),
          lintGutter(),
          history(), // Enables undo/redo functionality
          vscodeDark,
          pythonIndent,
          lineNumbers(),
          keymap.of([
            ...defaultKeymap, // Default key bindings
            ...historyKeymap, // Undo/Redo key bindings
            ...completionKeymap, // Autocomplete-related key bindings
            indentWithTab, // Tab indentation
          ]),
          EditorView.editable.of(!this.readonly),
          EditorView.updateListener.of((update) => {
            if (update.docChanged) {
              const updatedCode = update.state.doc.toString()
              this.codeChange.emit(updatedCode);
              this.codeChangeSubjectForErrorcheck.emit(updatedCode)
            }
          }),
        ],
      }),
      parent: editorContainer,
    });

    this.codeChangeSubjectForErrorcheck.pipe(
      debounceTime(500), // Wait 500ms after the user stops typing
      switchMap((code:any) => this.lintPythonCode(code)) // Call the linting function
    ).subscribe();

    this.lintPythonCode(this.code).subscribe()

  }
  ngAfterViewInit(): void {
    // Access cm-editor after view is initialized
    const cmEditorElement = this.el.nativeElement.querySelector('.cm-editor');
    if (cmEditorElement) {
      cmEditorElement.style.height = '79vh';
      cmEditorElement.style.width = '63vw';
      cmEditorElement.style.padding = '4px';
    }
    const cmScroller = cmEditorElement.querySelector(
      '.cm-scroller',
    ) as HTMLElement;
    if (cmScroller) {
      // Style the scrollbar directly.
      cmScroller
        .querySelectorAll<HTMLElement>('.cm-scroller::-webkit-scrollbar')
        .forEach((scrollbar) => {
          scrollbar.style.width = '10px';
        });

      cmScroller
        .querySelectorAll<HTMLElement>('.cm-scroller::-webkit-scrollbar-track')
        .forEach((track) => {
          track.style.background = '#f1f1f1';
        });

      cmScroller
        .querySelectorAll<HTMLElement>('.cm-scroller::-webkit-scrollbar-thumb')
        .forEach((thumb) => {
          thumb.style.background = '#888';
          thumb.style.borderRadius = '5px';
        });

      cmScroller
        .querySelectorAll<HTMLElement>(
          '.cm-scroller::-webkit-scrollbar-thumb:hover',
        )
        .forEach((thumb) => {
          thumb.style.background = '#555';
        });

      cmScroller.style.setProperty('scrollbar-width', 'thin');
      cmScroller.style.setProperty('scrollbar-color', '#888 #f1f1f1');
    }
  }


  lintPythonCode(updatedCode: string) {
    return this.http.post<any[]>(`${this.configService.getAppApiURL}/custom_python/lint`, { code: updatedCode }).pipe(
      switchMap(errors => {
        
        const linterErrors: Diagnostic[] = errors.map(error => {
          const line = this.editor.state.doc.line(error.line); 

          return ({
            from: line.from,
            to: line.to,
            message: error.message,
            severity: 'error',
          })
        })
  
        // Create a transaction using setDiagnostics
        const transaction = this.editor.state.update(
          setDiagnostics(this.editor.state, linterErrors)
        );
  
        // Dispatch the transaction to the editor
        this.editor.dispatch(transaction);
  
        return [];
      })
    );
  }
  


  ngOnDestroy(): void {
    if (this.editor) {
      this.editor.destroy();
    }
  }
}
