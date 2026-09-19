import { Component, OnInit } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { type Meta, type StoryObj } from '@storybook/angular';
import { ButtonComponent } from '../button/button.component';
import { InputComponent } from './input.component';

@Component({
  selector: 'mst-input-example',
  template: `
    <div>
      <h1>Combined Form Example</h1>
      <form
        class="mst-input-example__form"
        [formGroup]="myForm"
        (ngSubmit)="onSubmit()"
      >
        <mst-input
          label="Name"
          formControlName="name"
          placeholder="Enter your name"
          suffixIconName="badge"
          prefixIconName="person"
        />
        <mst-input
          label="Email"
          type="email"
          formControlName="email"
          placeholder="Enter your email"
          suffix="@example.com"
        />
        <mst-input
          label="Description"
          type="textarea"
          formControlName="description"
          placeholder="Enter your description"
        />
        <mst-input
          type="select"
          formControlName="country"
          label="Country"
          [items]="countryOptions"
        />
        <mst-input
          type="toggle"
          formControlName="notifications"
          label="Notification"
        />
        <mst-input type="toggle" formControlName="darkMode" label="Dark Mode" />
        <mst-input
          type="checkbox"
          formControlName="agreeToTerms"
          label="Agree to Terms"
        />
        <mst-input type="color" formControlName="color" label="Color" />
        <mst-button type="submit" [disabled]="!myForm.valid">Submit</mst-button>
      </form>
    </div>
  `,
  styles: [
    `
      .mst-input-example__form {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
    `,
  ],
  standalone: true,
  imports: [InputComponent, ButtonComponent, FormsModule, ReactiveFormsModule],
})
class InputExampleComponent implements OnInit {
  myForm!: FormGroup;

  // Options for mat-select
  countryOptions = [
    { id: 'us', name: 'United States' },
    { id: 'ca', name: 'Canada' },
    { id: 'uk', name: 'United Kingdom' },
  ];

  constructor(private fb: FormBuilder) {}

  ngOnInit() {
    this.myForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.required, Validators.email]],
      description: [''],
      country: ['', Validators.required],
      notifications: [true], // mat-slide-toggle, initial value: true (checked)
      darkMode: [false], // mat-slide-toggle
      agreeToTerms: [false, Validators.requiredTrue], // mat-checkbox (required to be true)
      color: ['#000000'], // ngx-color-picker
    });
  }

  onSubmit() {
    if (this.myForm.valid) {
      console.log('Form submitted:', this.myForm.value);
      this.myForm.reset(); // Reset the form after submission
    } else {
      console.log('Form is invalid');
      this.myForm.markAllAsTouched(); // Mark all fields as touched to show errors
    }
  }
}
// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<InputExampleComponent> = {
  title: 'Components/Input',
  component: InputExampleComponent,
};

export default meta;
type Story = StoryObj<InputExampleComponent>;

export const Basic: Story = {};
