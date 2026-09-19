import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  HostBinding,
  Input,
  Optional,
  Output,
  Self,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import {
  ControlValueAccessor,
  FormGroupDirective,
  FormsModule,
  NgControl,
  ReactiveFormsModule,
  ValidationErrors,
} from '@angular/forms';
import {
  MatCheckboxChange,
  MatCheckboxModule,
} from '@angular/material/checkbox';
import {
  MatDialog,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectChange, MatSelectModule } from '@angular/material/select';
import {
  MatSlideToggleChange,
  MatSlideToggleModule,
} from '@angular/material/slide-toggle';
import { ColorPickerModule } from 'ngx-color-picker';
import { ButtonComponent } from '../button/button.component';
import { IdNameData, InputType } from '../models';

// TODO: implement mat-chip-grid

export function generateErrorMessage(
  errors: ValidationErrors | null,
  fieldName: string | null,
): string {
  if (!errors) {
    return '';
  }

  const field = fieldName ? `The field '${fieldName}'` : 'This field';

  if (errors['required']) {
    return `${field} is required.`;
  }
  if (errors['email']) {
    return `Invalid email format.`;
  }
  if (errors['minlength']) {
    return `${field} must be at least ${errors['minlength'].requiredLength} characters long.`;
  }
  if (errors['maxlength']) {
    return `${field} cannot be more than ${errors['maxlength'].requiredLength} characters long.`;
  }
  if (errors['min']) {
    return `${field} must be greater than or equal to ${errors['min'].min}.`;
  }
  if (errors['max']) {
    return `${field} must be less than or equal to ${errors['max'].max}.`;
  }
  if (errors['pattern']) {
    return `${field} has an invalid format.`;
  }
  if (errors['requiredTrue']) {
    return `${field} must be checked.`;
  }
  if (errors['passwordMismatch']) {
    return `Passwords do not match.`;
  }
  if (errors['forbiddenName']) {
    return `The value is not allowed for ${field}.`;
  }

  return 'Invalid input.';
}

@Component({
  selector: 'mst-input',
  templateUrl: './input.component.html',
  styleUrls: ['./input.component.scss'],
  standalone: true,
  imports: [
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    CommonModule,
    ColorPickerModule,
    MatDialogModule,
    ButtonComponent,
    MatCheckboxModule,
    MatSlideToggleModule,
    FormsModule,
    ReactiveFormsModule,
  ],
})
export class InputComponent implements ControlValueAccessor {
  dialogRef: MatDialogRef<any> | null = null;
  @Input() label = '';
  @Input() placeholder = '';
  @Input() type: InputType = 'text';
  @Input() disabled = false;
  @Input() required = false;
  @Input() hint = '';
  @Input() errorMessage = '';
  @Input() items?: IdNameData[] = [];
  @Input() value: any = '';
  @Input() generateErrorMessage = true;
  @Input() prefix = '';
  @Input() suffix = '';
  @Input() prefixIconName = '';
  @Input() suffixIconName = '';
  @Output() change = new EventEmitter<any>();
  @Output() blur = new EventEmitter<Event>();
  @Output() input = new EventEmitter<any>();
  @Output() keyDown = new EventEmitter<KeyboardEvent>();
  @Output() prefixIconClick = new EventEmitter<{
    value: any;
    iconName: string;
  }>();
  @Output() suffixIconClick = new EventEmitter<{
    value: any;
    iconName: string;
  }>();

  @HostBinding('class.no-subscript')
  get noSubscript() {
    return !this.hint;
  }
  @HostBinding('class.no-underline')
  get noUnderline() {
    return ['checkbox', 'toggle'].includes(this.type);
  }
  @ViewChild('dialogTemplate') dialogTemplate!: TemplateRef<any>;
  constructor(
    public dialog: MatDialog,
    @Optional() @Self() public ngControl: NgControl,
    @Optional() private formGroupDirective: FormGroupDirective,
  ) {
    if (this.ngControl != null) {
      this.ngControl.valueAccessor = this;
    }
  }
  @ViewChild('inputEl', { static: false })
  inputEl!: ElementRef<HTMLInputElement>;

  onChange: any = () => {};
  onTouched: any = () => {};

  focus(selectText = false) {
    //console.log('InputComponent.inputEl', this.inputEl);
    if (this.inputEl?.nativeElement?.focus) {
      this.inputEl.nativeElement.focus();
      if (selectText) {
        this.inputEl.nativeElement.select();
      }
    }
  }

  writeValue(value: any): void {
    this.value = value;
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState?(isDisabled: boolean): void {
    this.disabled = isDisabled;
    // Handle the disabled state if needed
  }

  getErrorMessage(): string {
    const fieldName =
      this.ngControl && this.ngControl.path
        ? this.ngControl.path[this.ngControl.path.length - 1]
        : null;
    return generateErrorMessage(
      this.ngControl ? this.ngControl.errors : null,
      fieldName,
    );
  }

  applyChange(value: any) {
    this.value = value;
    this.onChange(value);
    this.onTouched();
    if (this.formGroupDirective && this.ngControl?.path) {
      //console.log(this.formGroupDirective, this.ngControl.errors);
      this.formGroupDirective.control.get(this.ngControl.path)?.markAsDirty();
      this.formGroupDirective.control
        .get(this.ngControl.path)
        ?.updateValueAndValidity();
    }
    this.change.emit(value);
  }

  onValueChange(e: Event) {
    e.stopPropagation();
    const value = (e.target as HTMLInputElement).value;
    this.applyChange(value);
  }

  onCheckedChange(e: MatCheckboxChange | MatSlideToggleChange) {
    const value = e.checked;
    this.applyChange(value);
  }

  onColorChange(color: string) {
    this.applyChange(color);
  }

  onSelectionChange(e: MatSelectChange) {
    this.applyChange(e.value);
    this.change.emit(e.value);
  }
  onClick() {
    this.dialogRef = this.dialog.open(this.dialogTemplate);
  }
  onCloseClick() {
    this.dialogRef?.close();
  }
  onInput(e: Event) {
    e.stopPropagation();
    this.input.emit((e.target as HTMLInputElement).value);
  }
  onBlur(e: Event) {
    e.stopPropagation();
    this.blur.emit(e);
  }
  onKeyDown(e: KeyboardEvent) {
    e.stopPropagation();
    this.keyDown.emit(e);
  }
  onPrefixIconClick() {
    this.prefixIconClick.emit({
      value: this.value,
      iconName: this.prefixIconName,
    });
  }
  onSuffixIconClick() {
    this.suffixIconClick.emit({
      value: this.value,
      iconName: this.suffixIconName,
    });
  }
}
