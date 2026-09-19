import { CodeEditor, Setup } from '@acrodata/code-editor';
import {
  Component,
  EventEmitter,
  HostBinding,
  Input,
  Output,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { sql, SQLNamespace } from '@codemirror/lang-sql';
import { languages } from '@codemirror/language-data';
import { Extension } from '@codemirror/state';

/**
 * Jupyter Notebook utilizes the CodeMirror library, while Superset employs the Ace editor. I selected CodeMirror due to its more permissive licensing compared to Ace, which I found to be overly restrictive.
 * https://github.com/codemirror/codemirror5/blob/master/LICENSE
 * https://github.com/ajaxorg/ace/blob/master/LICENSE
 */

/**
 * @ctrl/ngx-codemirror(v5) is deprecated. Use @acrodata/code-editor(v6) instead.
 * required npms
 * @codemirror/language-data
 * @codemirror/theme-one-dark
 * @codemirror/lang-sql
 * @codemirror/state
 */
// languages has the language list. See the following example:
// https://acrodata.github.io/code-editor/home
// https://github.com/acrodata/code-editor/blob/main/projects/dev-app/src/app/home/home.component.ts
/**
 * languages
        .map(lang => ({ label: lang.name, value: lang.name.toLowerCase() }))
        .concat([{ label: 'Plain Text', value: 'plaintext' }])
        .sort((a, b) => a.label.localeCompare(b.label))
 */
// sql doesn't support avg, count, .... so we replace it with postgresql.
type LanguageType = 'python' | 'sql' | 'postgresql' | 'mysql' | 'plaintext';
type ThemeType = 'light' | 'dark';

@Component({
  selector: 'mst-editor',
  styleUrls: ['./editor.component.scss'],
  template: `<code-editor
    style="height: 100%; width: 100%;"
    [theme]="theme"
    [setup]="setup"
    [(ngModel)]="value"
    [language]="language === 'sql' ? 'postgresql' : language"
    [disabled]="disabled"
    [placeholder]="placeholder"
    [languages]="languages"
    [extensions]="extensions"
    (ngModelChange)="onChange($event)"
  ></code-editor>`,
  standalone: true,
  imports: [FormsModule, CodeEditor],
})
export class EditorComponent {
  languages = languages;
  extensions: Extension[] = [];
  @Input() lineNumbers = true;
  @Input() setup: Setup = 'basic';
  @Input() language: LanguageType = 'python';
  @Input() value = '';
  @Input() theme: ThemeType = 'light';
  @Input() disabled = false;
  @Input() placeholder = 'Type here...';
  @Input() set schema(schema: SQLNamespace | undefined) {
    if (schema) {
      const defaultTable = Object.keys(schema)[0];
      this.extensions = [sql({ schema, defaultTable })];
    }
  }
  @Output() change = new EventEmitter<string>();

  @HostBinding('class.hide-line-numbers') get hideLineNumbers() {
    return !this.lineNumbers;
  }

  onChange(newValue: string) {
    this.value = newValue;
    this.change.emit(newValue);
  }
}
