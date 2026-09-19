# Running the Frontend and Backend

This document outlines the steps to run the frontend and backend locally.

## Prerequisites

- Refer to the Databrick Wiki for initial setup and local deployment instructions: [HEXAIND 3.0 - Local Deployment Instructions](https://databricktech.atlassian.net/wiki/spaces/Databrick/pages/384237573/HEXAIND+3.0+-+Local+Deployment+Instructions)
- Ensure Docker containers for `condescending_rhodes`, Redis, and MongoDB are running.

## Configuration

### Frontend (`hexaind-frontend`)

1.  Navigate to `src/environments/environment.ts`.
2.  Set the `apiUrl` to your local machine's address:

    ```typescript
    export const environment = {
      production: false,
      auxApiUrl: 'http://localhost:8080', // Your local URL
      apiUrl: 'http://localhost:8080', // Your local URL
      tdamUrl: '[http://10.0.5.99:8071](http://10.0.5.99:8071)',
      dbUrl: 'localhost:27017',
      ...
    };
    ```

### Backend (`hexaind_backend`)

1.  Navigate to `app/config/env_vars.py`.
2.  Configure the MongoDB connection string. For local development, it should resemble one of the following (choose the one that matches your setup):

```python
  port = os.environ.get(
      "MONGO_EXPOSED_PORT", "default_port"
  )  # Provide a default port if not found
// return f"{auth_info}@{ip_address}:{port}/"
// return mongodb_url
  return "mongodb://your_auth_info@localhost:27017"
  return "mongodb://localhost:27017"

  hexaind3_database_name: str = "Hexaind"
```

After starting the backend, please sign out and sign back in. This will prevent potential NonXXX errors

API specs: http://localhost:8080/docs

### macOS Users

1.  In the `requirements.txt` file, comment out the following lines as they are not supported on macOS:

    ```
    # lightgbm==4.2.0
    # triton==2.1.0
    ```

## Running the Application

1.  **Frontend:**

    ```bash
    cd hexaind-frontend
    ng s
    ```

2.  **Backend:**
    ```bash
    cd hexaind_backend
    uvicorn app.main:app --port 8080 --reload
    ```

# Angular Style Guide (mst prefix)

This style guide outlines best practices for writing Angular code within our project, using the `mst` component prefix. It emphasizes readability, maintainability, consistency, testability, and scalability. It also covers SCSS styling, Material Component wrapping, and the use of CSS Custom Properties. **All components should be standalone: true.**

## 0. Standalone Components: The Future of Angular

This style guide mandates the use of **standalone components** (`standalone: true` in the `@Component` decorator). This section explains why.

**Standalone Components vs. NgModules:**

Angular historically used NgModules to organize applications. While NgModules still work, **standalone components are the recommended approach for new development and are considered the best practice for the future.**

| Feature               | Standalone Components                  | NgModules                                |
| --------------------- | -------------------------------------- | ---------------------------------------- |
| **Complexity**        | Simpler, easier to understand          | More complex, steeper learning curve     |
| **Code Organization** | More granular, component-centric       | Module-centric, can be less organized    |
| **Bundle Size**       | Smaller (better tree-shaking)          | Potentially larger                       |
| **Lazy Loading**      | Easier (`loadComponent`)               | More complex (requires separate modules) |
| **Testability**       | Easier to test (explicit dependencies) | Can be more difficult to test            |
| **Boilerplate**       | Less boilerplate                       | More boilerplate                         |
| **Future-Proofing**   | Actively developed, future-focused     | Legacy approach                          |
| **Reusability**       | Easier reuse                           | Harder reuse                             |

**Advantages of Standalone Components:**

- **Simplified Mental Model:** No need to manage NgModules for component organization. Import what you need directly into the component.
- **Improved Code Organization:** Each component manages its own dependencies.
- **Smaller Bundle Sizes:** Excellent tree-shaking leads to smaller application sizes and faster load times.
- **Easy Lazy Loading:** Use `loadComponent` in your routing configuration.
- **Better Testability:** Explicit dependencies make mocking and isolation easier.
- **Future-Proof:** Angular's development efforts are focused on standalone components.
- **Eliminates Boilerplate** You no longer have to add components to the declaration arrays.
- **Easier Reuse:** You can import standalone components to another component, or add them to the routing.

**When NgModules Might Still Be Used (Rarely):**

- **Sharing Providers (Very Specific Cases):** _Extremely_ rare cases where you need a very specific provider scope. Even then, prefer standalone-friendly alternatives.
- **Third-Party Libraries:** If a library _requires_ NgModules (this is becoming less common).
- **Migration Phase:** If you are converting an old big application to standalone, modules are unavoidable.

**Conclusion:**

This style guide _requires_ standalone components due to their significant advantages. New projects should _always_ start with standalone components. Existing projects should plan for a gradual migration.

## 0. Reactive Forms vs. Template-Driven Forms

This document outlines the recommended code style guide for choosing between and implementing Reactive Forms and Template-Driven Forms in Angular applications. While both approaches are valid, **Reactive Forms are the strongly preferred and recommended method** for building forms in modern Angular applications due to their enhanced flexibility, testability, and maintainability.

### 1. General Recommendation: Favor Reactive Forms

**Reactive Forms should be your default choice for building forms in Angular.**

**Reasons for preferring Reactive Forms:**

- **Testability:** Reactive Forms are synchronous and easier to test unit tests because form logic is defined in the component class, independent of the template.
- **Flexibility and Control:** Reactive Forms provide more control over form elements and data flow. They are ideal for complex forms with dynamic behavior, custom validation, and asynchronous operations.
- **Maintainability:** Form logic is centralized in the component class, making the code cleaner, more organized, and easier to maintain, especially for complex forms.
- **Scalability:** Reactive Forms scale better for larger applications with numerous forms and complex interactions.
- **Type Safety:** Reactive Forms are inherently type-safe, leveraging TypeScript's strong typing capabilities.

**Template-Driven Forms are acceptable primarily for:**

- **Simple Forms:** Very basic forms where complexity is minimal, and testability is not a primary concern.
- **Legacy Projects:** Maintaining or making minor updates to older Angular projects that heavily rely on Template-Driven Forms.
- **Rapid Prototyping:** Quickly creating simple forms when detailed control and testability are not initial priorities. However, consider migrating to Reactive Forms as the application evolves.

### 2. Reactive Forms Style Guide

#### 2.1. Structure and Organization

- **Form Group and Form Controls in Component Class:** Define `FormGroup` and `FormControl` instances within your component class. This centralizes form logic and makes it testable.

  ```typescript
  import { Component, OnInit } from "@angular/core";
  import { FormGroup, FormControl, Validators } from "@angular/forms";

  @Component({
    /* ... */
  })
  export class MyFormComponent implements OnInit {
    myForm: FormGroup;

    ngOnInit() {
      this.myForm = new FormGroup({
        firstName: new FormControl("", Validators.required),
        lastName: new FormControl("", Validators.required),
        email: new FormControl("", [Validators.required, Validators.email]),
      });
    }

    onSubmit() {
      if (this.myForm.valid) {
        console.log(this.myForm.value);
        // Handle form submission
      }
    }
  }
  ```

- **Separate Form Logic (Optional but Recommended for Complex Forms):** For very complex forms, consider creating a separate service or class to encapsulate form group creation and validation logic, promoting reusability and cleaner components.

#### 2.2. Naming Conventions

- **Form Group Names:** Use descriptive names for `FormGroup` instances, often reflecting the form's purpose (e.g., `userProfileForm`, `productSearchForm`, `myForm`). Suffix with `Form`.
- **Form Control Names:** Use camelCase for `FormControl` names, mirroring the data model properties they represent (e.g., `firstName`, `lastName`, `email`).

#### 2.3. Validation

- **Validators in Component Class:** Define validators directly within the `FormControl` constructor in the component class.

  ```typescript
  new FormControl("", [Validators.required, Validators.minLength(3)]);
  ```

- **Built-in Validators:** Utilize Angular's built-in validators (`Validators.required`, `Validators.email`, `Validators.minLength`, `Validators.maxLength`, `Validators.pattern`, etc.) whenever possible.
- **Custom Validators:** Create custom validator functions or classes for complex or domain-specific validation logic. Place custom validators in a separate `validators` folder or service for reusability.

  ```typescript
  // custom-validators.ts
  import { ValidatorFn, AbstractControl } from "@angular/forms";

  export function forbiddenNameValidator(forbiddenName: RegExp): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } | null => {
      const forbidden = forbiddenName.test(control.value);
      return forbidden ? { forbiddenName: { value: control.value } } : null;
    };
  }
  ```

  ```typescript
  // component.ts
  import { forbiddenNameValidator } from "./custom-validators";

  new FormControl("", [Validators.required, forbiddenNameValidator(/admin/i)]);
  ```

- **Asynchronous Validators:** Implement asynchronous validators when validation requires server-side checks or operations that are not immediately available.

  ```typescript
  // asynchronous-validators.ts
  import { AsyncValidatorFn, AbstractControl, ValidationErrors } from "@angular/forms";
  import { Observable, of } from "rxjs";
  import { map, catchError } from "rxjs/operators";
  import { UserService } from "./user.service";

  export function uniqueEmailValidator(userService: UserService): AsyncValidatorFn {
    return (control: AbstractControl): Observable<ValidationErrors | null> => {
      return userService.checkEmailExists(control.value).pipe(
        map((exists) => (exists ? { uniqueEmail: true } : null)),
        catchError(() => of(null)), // Handle server errors gracefully
      );
    };
  }
  ```

  ```typescript
  // component.ts
  import { uniqueEmailValidator } from './asynchronous-validators';

  constructor(private userService: UserService) {}

  ngOnInit() {
    this.myForm = new FormGroup({
      email: new FormControl('', {
        validators: [Validators.required, Validators.email],
        asyncValidators: [uniqueEmailValidator(this.userService)],
        updateOn: 'blur' // Trigger async validation on blur
      })
    });
  }
  ```

- **UpdateOn Property:** Use the `updateOn` property (`'change'`, `'blur'`, `'submit'`) on `FormControl` to control when validation and value updates occur. `'blur'` is often a good choice for asynchronous validators to avoid excessive calls.

#### 2.4. Data Binding in Template

- **`formGroup` Directive:** Bind the `FormGroup` instance to the `<form>` element using the `formGroup` directive.

  ```html
  <form [formGroup]="myForm" (ngSubmit)="onSubmit()"></form>
  ```

- **`formControlName` Directive:** Bind each `FormControl` to its corresponding input element using the `formControlName` directive, matching the `FormControl` name defined in the component.

  ```html
  <input type="text" id="firstName" formControlName="firstName" />
  ```

- **Access Form Controls in Template:** Access form controls in the template using the `formGroup` instance and the `get()` method or dot notation for cleaner syntax, combined with the `$` pipe for safe navigation.

  ```html
  <div *ngIf="myForm.get('firstName')?.invalid && (myForm.get('firstName')?.dirty || myForm.get('firstName')?.touched)">
    <div *ngIf="myForm.get('firstName')?.errors?.required">First Name is required.</div>
    <div *ngIf="myForm.get('firstName')?.errors?.minlength">First Name must be at least 3 characters long.</div>
  </div>
  ```

  **Preferred (cleaner syntax using dot notation in template):**

  ```html
  <div *ngIf="myForm.controls['firstName'].invalid && (myForm.controls['firstName'].dirty || myForm.controls['firstName'].touched)">
    <div *ngIf="myForm.controls['firstName'].errors?.required">First Name is required.</div>
    <div *ngIf="myForm.controls['firstName'].errors?.minlength">First Name must be at least 3 characters long.</div>
  </div>
  ```

#### 2.5. Handling Form Submission

- **`ngSubmit` Event Binding:** Bind the `ngSubmit` event of the `<form>` element to a component method (e.g., `onSubmit()`).
- **Check `formGroup.valid`:** In the `onSubmit()` method, check `this.myForm.valid` before processing form data to ensure the form is valid.
- **Access Form Values with `formGroup.value`:** Retrieve form data as a JavaScript object using `this.myForm.value`.

  ```typescript
  onSubmit() {
    if (this.myForm.valid) {
      const formData = this.myForm.value;
      console.log('Form Data:', formData);
      // Send formData to a service for processing (e.g., API call)
    } else {
      // Handle invalid form (e.g., display error messages)
      console.error('Form is invalid');
    }
  }
  ```

#### 2.6. Benefits of Reactive Forms (Summary)

- **Testable:** Synchronous validation and logic in the component class.
- **Precise Control:** Fine-grained control over form elements and data flow.
- **Dynamic Forms:** Easy to build dynamic forms that change structure at runtime.
- **Strong Typing:** Leverages TypeScript for type safety.
- **Immutable Data Flow:** Clear and predictable data flow.

### 3. Template-Driven Forms Style Guide (Use Sparingly)

#### 3.1. Structure and Organization

- **Form Logic in Template:** Most form logic is handled implicitly by Angular directives within the template.
- **Component Class for Data Model:** Component class primarily manages the data model bound to the form.

  ```typescript
  import { Component } from "@angular/core";
  import { User } from "./user.model"; // Example data model

  @Component({
    /* ... */
  })
  export class MyTemplateFormComponent {
    user = new User(); // Data model instance

    onSubmit() {
      console.log(this.user);
      // Handle form submission
    }
  }
  ```

#### 3.2. Naming Conventions

- **Template Variables:** Use `#` prefix for template variables to reference form controls and the form itself (e.g., `#firstName`, `#myForm`). Use descriptive names.

#### 3.3. Validation

- **Built-in Directives:** Rely on Angular's built-in validation directives (`required`, `minlength`, `maxlength`, `email`, `pattern`) applied directly in the template.

  ```html
  <input type="text" id="firstName" name="firstName" #firstName="ngModel" [(ngModel)]="user.firstName" required minlength="3" />
  ```

- **Template Variable for Validation State:** Use template variables (e.g., `#firstName="ngModel"`) to access the validation state (`valid`, `invalid`, `errors`) of form controls in the template.

  ```html
  <div *ngIf="firstName.invalid && (firstName.dirty || firstName.touched)">
    <div *ngIf="firstName.errors?.required">First Name is required.</div>
    <div *ngIf="firstName.errors?.minlength">First Name must be at least 3 characters long.</div>
  </div>
  ```

#### 3.4. Data Binding

- **`ngModel` Directive:** Use the `ngModel` directive for two-way data binding between form controls in the template and properties in the component class.

  ```html
  <input type="text" id="firstName" name="firstName" [(ngModel)]="user.firstName" />
  ```

- **`name` Attribute:** Ensure each form control has a `name` attribute. This is crucial for Angular to track form controls and their values in Template-Driven Forms.

#### 3.5. Handling Form Submission

- **`ngSubmit` Event Binding:** Bind the `ngSubmit` event of the `<form>` element to a component method (e.g., `onSubmit()`).
- **Access Data Model:** In the `onSubmit()` method, access the data model (e.g., `this.user`) directly, as `ngModel` updates it automatically.
- **Check Form Validity (Optional):** While less common in Template-Driven Forms (validation is often template-focused), you can access the form's validity using a template variable on the `<form>` element (e.g., `#myForm="ngForm"`) and check `myForm.valid`.

  ```typescript
  onSubmit() {
    console.log('User Data:', this.user);
    // Handle form submission
  }
  ```

#### 3.6. When to Use Template-Driven Forms (Summary)

- **Very Simple Forms:** Minimal validation and logic.
- **Rapid Prototyping (Initial Stages):** Quick setup for basic forms.
- **Learning Angular Forms (Beginners):** Easier to grasp initially.
- **Legacy Code Maintenance:** Working with existing Template-Driven Forms.

### 4. Comparison Table: Reactive Forms vs. Template-Driven Forms

| Feature              | Reactive Forms                               | Template-Driven Forms                            |
| -------------------- | -------------------------------------------- | ------------------------------------------------ |
| **Form Logic**       | Component Class (centralized, testable)      | Template (implicit, less testable)               |
| **Data Binding**     | Explicit, programmatic                       | Implicit, two-way (`ngModel`)                    |
| **Control**          | Fine-grained, more control                   | Less control, relies on directives               |
| **Testability**      | Highly testable                              | Less testable                                    |
| **Complexity**       | Handles complex forms effectively            | Best for simple forms                            |
| **Scalability**      | Scales well for large applications           | Less scalable for complex applications           |
| **Type Safety**      | Inherently type-safe                         | Less type-safe                                   |
| **Verbosity**        | More verbose initially                       | Less verbose initially                           |
| **Initial Learning** | Steeper learning curve                       | Easier to learn initially                        |
| **Recommendation**   | **Strongly Preferred** for most applications | Use sparingly, primarily for simple/legacy forms |

### 5. Conclusion

By adhering to this style guide, you can build robust, maintainable, and testable Angular forms. **Prioritize Reactive Forms** for the majority of your Angular form development. Use Template-Driven Forms judiciously and primarily for very simple scenarios or when working with legacy code. Consistent application of these guidelines will lead to cleaner, more efficient, and easier-to-understand Angular applications.

## I. Core Principles

- **Readability:** Code should be easy to understand.
- **Maintainability:** Code should be easy to update and debug.
- **Consistency:** A uniform style improves collaboration.
- **Testability:** Code should be easily testable.
- **Scalability:** The architecture should support growth.
- **Performance:** Consider performance implications (e.g., change detection).

## II. File Structure and Organization

- **LIFT Principle (Locate, Identify, Flat, T-Try):**

  - **Locate:** Easy to find code.
  - **Identify:** Filenames and folders indicate content.
  - **Flat:** Avoid deeply nested folders _as much as possible_.
  - **T-Try (DRY):** Don't Repeat Yourself in folder structure.

- **Structure:**

  ```
  src/
  ├── app/                         # Application-specific code
  │   ├── shared/                  # Reusable components, directives, pipes
  │   │   ├── components/          # Categorical folder for components
  │   │   │   ├── button/          # Component in its own folder
  │   │   │   │   ├── button.component.ts
  │   │   │   │   ├── button.component.html
  │   │   │   │   ├── button.component.scss
  │   │   │   │   ├── button.component.spec.ts
  │   │   │   │   └── ...
  │   │   │   └── ...  # Other shared components
  │   │   ├── directives/          # Categorical folder for directives
  │   │   │   ├── highlight.directive.ts
  │   │   │   └── ...
  │   │   ├── pipes/               # Categorical folder for pipes
  │   │   │   ├── uppercase.pipe.ts
  │   │   │   └── ...
  │   │   ├── models/                 # Shared models.
  │   │   └── styles--shared.scss
  │   ├── components/                 # components for pages
  │   │   ├── product-list/
  │   │   │   ├── product-list.component.ts
  │   │   │   ├── product-list.component.html
  │   │   │   ├── product-list.component.scss
  │   │   │   ├── product-list.component.spec.ts
  │   │   └── ...
  │   ├── pages/
  │   │   ├── products/
  │   │   │   ├── products.component.ts
  │   │   │   ├── products.component.html
  │   │   │   ├── products.component.scss
  │   │   │   ├── products.component.spec.ts
  │   │   └── ...
  │   ├── services/           # services (auth, logging)
  │   ├── models/             # data models/interfaces
  │   ├── app.component.ts          # Root component
  │   ├── app.component.html
  │   ├── app.component.scss
  │   ├── app.component.spec.ts
  │   ├── app.routes.ts            # Top-level routes
  │   └── ...
  ├── assets/                      # Static assets (images, fonts)
  ├── environments/                # Environment-specific configurations
  │   ├── environment.ts
  │   ├── environment.prod.ts
  │   └── ...
  ├── styles.scss                  # Global styles
  ├── index.html
  ├── main.ts                     # Application entry point
  ├── polyfills.ts                # Polyfills
  └── ...
  ```

- **Avoid `index.ts` Barrel Files:** Generally avoid barrels to prevent large bundle sizes. Use them strategically if at all.

## III. Naming Conventions

(This section remains largely the same, as naming conventions aren't affected by the folder structure change.)

- **General:** Descriptive and consistent names.

- **Files:**

  - kebab-case: `product-list.component.ts`.
  - `feature.type.ts` (e.g., `product-list.component.ts`).
  - Tests: `feature.type.spec.ts`.

- **Classes:**

  - PascalCase: `ProductListComponent`.
  - Components: `ComponentName` (e.g., `ProductListComponent`).
  - Services: `ServiceName` (e.g., `AuthService`).
  - Directives: `DirectiveName` (e.g., `HighlightDirective`).
  - Pipes: `PipeName` (e.g., `UppercasePipe`).
  - Interfaces: `InterfaceName` (e.g., `Product`, `User` - _no_ `I` prefix).
  - Enums: PascalCase: `ProductStatus`.

- **Variables and Functions:**

  - camelCase: `productList`, `getProductDetails()`.
  - Descriptive names.
  - Constants: `UPPER_SNAKE_CASE`.
  - Booleans: Often start with `is`, `has`, `can`, `should`.

- **Selectors:**
  - Components: kebab-case, prefixed with `mst-`: `<mst-product-list>`.
  - Directives: camelCase, prefixed with `mst`: `[mstHighlight]`.

## IV. TypeScript Coding Style

(This section also remains largely the same.)

- **Types:**

  - Explicit type annotations whenever possible.
  - Use interfaces/types for object shapes.
  - `const` for unchanging values, `let` for reassignable variables. Avoid `var`.
  - Avoid `any` as much as possible; prefer `unknown` when the type is truly unknown.
  - Use optional properties sparingly.

- **Classes:**

  - Class properties and methods instead of constructor-declared functions.
  - Define access modifiers (public, private, protected).

- **Strings:**

  - Template literals (backticks) for multi-line strings and interpolation.
  - Single quotes (`'`) for regular strings.

- **Spacing and Indentation:**

  - 2 spaces for indentation.
  - Spaces around operators, after commas, after colons in type annotations.

- **Comments:**

  - Explain _why_, not _what_ (code should be self-documenting for _what_).
  - Use JSDoc-style comments for classes, methods, and properties.

- **Imports:**

  - **Crucial for Standalone Components:** Components _must_ import all their dependencies (other components, directives, pipes) directly in the `@Component` decorator's `imports` array.
  - Group imports logically: Angular, third-party, application, relative.
  - Use absolute imports (configure `tsconfig.json` with `baseUrl` and `paths`).
  - Avoid wildcard imports (`*`).
  - Example:

    ```typescript
    // features/products/components/product-list/product-list.component.ts
    import { Component, OnInit } from "@angular/core";
    import { ProductService } from "../../services/product.service"; // Relative import to services
    import { Product } from "../../models/product.model";
    import { UpperCasePipe } from "@shared/pipes/uppercase.pipe"; // Absolute import from shared
    import { MstButtonComponent } from "@shared/components/button/button.component"; // Import standalone component

    @Component({
      selector: "mst-product-list",
      standalone: true,
      imports: [UpperCasePipe, MstButtonComponent], // Import dependencies!
      templateUrl: "./product-list.component.html",
      styleUrls: ["./product-list.component.scss"],
    })
    export class ProductListComponent implements OnInit {
      // ...
    }
    ```

- **Observables:**
  - `async` pipe in templates whenever possible.
  - Manual subscription: Use `takeUntil` or similar to prevent leaks. _Always_ unsubscribe.
  - Name Observables with a trailing `$`: `products$`.
- **Error Handling**
  - Use `try...catch` or `catchError`
  - Provide user-friendly error messages.
  - Log errors.

## V. Component-Specific Guidelines

- **`standalone: true`:** All components _must_ have this set in the `@Component` decorator.
- **`imports: []`:** The `@Component` decorator's `imports` array _must_ list all dependencies (components, directives, pipes) used in the component's template.
- **`@Input()` and `@Output()`:**

  - `@Input()` for data into the component.
  - `@Output()` for events from the component.
  - Descriptive names, explicit types.

- **Change Detection:**

  - Understand and use Angular's change detection.
  - Consider `ChangeDetectionStrategy.OnPush` for performance.
  - If using `OnPush`, you may need `ChangeDetectorRef.markForCheck()`.

- **Lifecycle Hooks:**

  - Use lifecycle hooks appropriately.
  - `ngOnInit`: Initialization logic.
  - `ngOnDestroy`: Cleanup (unsubscribe from Observables).
  - Avoid complex logic in the constructor.

- **Template Best Practices:**
  - Concise and readable templates.
  - Avoid complex logic in templates.
  - `*ngIf`, `*ngFor`, property binding, event binding, interpolation, pipes.
  - `trackBy` with `*ngFor` for performance.
- **Component Size:** Keep components small and focused. Refactor large components.

- **Avoid Logic in Templates**

## VI. Service-Specific Guidelines

- **`@Injectable({ providedIn: 'root' })`:** For application-wide singleton services. This is still the recommended way to provide most services.
- **Tree-shakable Services:** Using `providedIn: 'root'` makes the service tree-shakable. If a service is _not_ used, it won't be included in the final bundle.
- **Data Access:** Services often handle data access.
- **Business Logic:** Encapsulate business logic in services.
- **Testability:** Design services for easy testing.
- **Alternatives to `providedIn: 'root'` (Rare Cases):**
  - **Feature-Specific Services:** If a service is _only_ used within a single feature, you _can_ provide it directly in the `providers` array of the _component_ that uses it (or a parent component if multiple components need it). This is less common with standalone components, but still possible. _Do not_ create modules just to provide services.
  - Example:
    ```typescript
    @Component({
        // ...
        standalone: true,
        providers: [ProductService] // Only this component (and children) will get this instance
    })
    ```

## VII. Routing

- **`app.routes.ts`:** Defines the top-level application routes.
- **Feature Routes:** Define routes _within_ the feature folder, often in a `feature-name.routes.ts` file.
- **Lazy Loading (Optional, but Recommended):**

  - Use the `loadComponent` syntax for lazy loading standalone components.
  - Example (`app.routes.ts`):

  ```typescript
  // app.routes.ts
  import { Routes } from "@angular/router";
  import { HomeComponent } from "./home.component"; // Example - could be standalone or not

  export const routes: Routes = [
    { path: "", component: HomeComponent },
    {
      path: "products",
      loadComponent: () => import("./features/products/components/product-list/product-list.component").then((c) => c.ProductListComponent),
    },
    // ... other routes
  ];
  ```

  - Example (feature routes, `products.routes.ts`):

    ```typescript
    import { Routes } from "@angular/router";
    import { ProductDetailComponent } from "./components/product-detail/product-detail.component";
    import { ProductListComponent } from "./components/product-list/product-list.component";
    import { ProductsPageComponent } from "./pages/products-page/products-page.component";

    export const productRoutes: Routes = [
      { path: "", component: ProductsPageComponent }, //If no path, take to list.
      { path: ":id", component: ProductDetailComponent }, //If an ID is provided, go to details page
    ];
    ```

    - **Important:** To use feature routes, you need to import them in app.routes.ts.
      ```typescript
      // app.routes.ts
      import { Routes } from "@angular/router";
      import { HomeComponent } from "./home.component"; // Example - could be standalone or not
      import { productRoutes } from "./features/products/products.routes";
      export const routes: Routes = [
        { path: "", component: HomeComponent },
        {
          path: "products",
          children: productRoutes, // Use routes defined for the feature.
        },
        // ... other routes
      ];
      ```

## VII. SCSS Styling Guide

- **File Organization:**

  - **Component-Scoped Styles:** SCSS files in the same folder as the component.
  - **Global Styles:** `/styles.scss` for global styles (resets, typography, base styles).
  - **Shared Styles:** `/shared/shared.scss` (or similar) for variables, mixins, functions, placeholders.

- **Naming Conventions:**

  - Variables, Mixins, Placeholders, Functions: kebab-case.
  - CSS Classes: BEM (Block, Element, Modifier).

- **BEM (Block, Element, Modifier):**

  ```scss
  .product-card {
    // Block
    &__title {
    } // Element
    &__image {
    } // Element
    &--highlighted {
    } // Modifier
  }
  ```

  - Double underscores (`__`) for block/element separation.
  - Double hyphens (`--`) for block/element and modifier separation.
  - Use `&` for parent selector referencing.

- **Nesting:**

  - Reflect HTML structure, but avoid excessive nesting (max 3-4 levels).

- **Variables:**

  - Use SCSS variables extensively for reusable values.
  - Meaningful variable names.

- **Mixins:**

  - Create reusable style blocks (vendor prefixes, common patterns, media queries).

- **Placeholders (Extend):**

  - Define styles to be extended (`%message-box`).

- **Comments:**

  - `//` for single-line comments (not in compiled CSS).
  - `/* ... */` for multi-line comments (in compiled CSS - use sparingly).

- **`!important`:** Avoid unless absolutely necessary.

- **Media Queries:** Organize media queries. Use mixins for breakpoints. Prefer mobile-first.

- **Specificity:** Keep selectors as specific as needed, but no more. BEM helps. Avoid IDs for styling.

- **Don't Optimize Prematurely**

## VIII. Integrating CSS Custom Properties (Variables)

- **Theming and Global Values:** Use for values that change with themes or are used globally.

- **Define at Root:** Define global custom properties in `styles.scss` within `:root`.

  ```scss
  :root {
    --primary-color: #007bff;
    --font-size-base: 1rem;
  }
  ```

- **`var()` Function:** Access custom properties with `var()`.

  ```scss
  .product-card {
    color: var(--text-color);
  }
  ```

- **Fallback Values:** Provide fallback values in `var()`.

  ```scss
  .button {
    background-color: var(--button-background-color, #007bff);
  }
  ```

- **SCSS Variables vs. CSS Custom Properties:**

  - **SCSS Variables (`$variable`):** Compile-time, cannot be changed at runtime, scoped. Use for internal SCSS logic.
  - **CSS Custom Properties (`--variable`):** Runtime, changeable with JavaScript, inherited. Use for theming, global values.
  - **Combined Use:** Use both, leveraging their strengths.

- **Theming:** Use CSS Custom Properties for easy theme switching.

- **Component-Specific Custom Properties (Less Common):** Can be used for external customization of a component's styles.

- **Documentation:** Document your CSS custom properties thoroughly.

## IX. Material Components & Customization

### 1. Introduction

This style guide outlines the visual language for HEXAIND 3.0, utilizing Material Design components as a foundation and a custom component wrapper approach for controlled customization.

**Figma Design Link (Source of Truth for Values):** [HEXAIND 3.0 Figma Design](https://www.figma.com/design/ss0UQYn3u3lAG3t90OQnjy/HEXAIND-3.0?node-id=26-3&p=f&t=nfT6Ymi9hmJjTPRo-0)

**Key Principles:**

- **Material Foundation:** We leverage Google's Material Design components (Angular Material) for basic UI elements.
- **Wrapped Components:** We create custom wrapper components around Material components. This provides:
  - **Controlled API:** We expose only the necessary properties and functionalities, simplifying usage and preventing unintended styling modifications.
  - **Centralized Customization:** Style overrides are managed in a single location (`shared.scss`), promoting consistency and maintainability.
  - **Abstraction:** We can potentially swap out the underlying Material component library in the future without affecting the rest of the application.
- **SCSS Styling:** We use SCSS (Sass) for styling, enabling nesting for efficient and organized stylesheets.
- **CSS Custom Properties (Variables):** We utilize _web standard CSS Custom Properties_ (not SCSS variables) for theming and design tokens. This allows for dynamic theme switching and greater flexibility.
- **Figma as Source of Truth:** All specific values (sizes, precise colors, spacing, etc.) should be obtained from the Figma design file.

### 2. Component Wrapping Strategy

This section details how we wrap and customize Material components.

**2.1. Wrapper Component Structure:**

For each Material component we use (e.g., `MatButton`, `MatInput`, `MatCard`), we create a corresponding wrapper component (e.g., `MstButton`, `MstInput`, `MstCard`).

**Example (Conceptual - TypeScript/Angular):**

```typescript
// mst-button.component.ts
import { Component, Input, Output, EventEmitter } from "@angular/core";
import { MatButton } from "@angular/material/button"; // Import the Material component

@Component({
  selector: "mst-button",
  template: `
    <button mat-button [color]="color" [disabled]="disabled" (click)="onClick.emit($event)">
      <ng-content></ng-content>
    </button>
  `,
  styleUrls: ["./mst-button.component.scss"], // Local styles (if needed)
})
export class ButtonComponent {
  @Input() color: "primary" | "accent" | "warn" = "primary"; // Expose only allowed colors
  @Input() disabled: boolean = false;
  @Output() onClick = new EventEmitter<Event>();

  // ... other properties and logic as needed
}
```

**2.2. `shared.scss` for Global Overrides:**

All global style overrides for Material components are placed in a single `shared.scss` file. This ensures consistency and makes it easy to manage global theme changes.

**Key Points for `shared.scss`:**

- **Specificity:** Use a consistent prefix (e.g., `mst-`) for wrapper component selectors to target overrides effectively. This prevents unintended style conflicts.
- **Nesting:** Utilize SCSS nesting to target Material component classes within our wrapper components.
- **CSS Custom Properties:** Define CSS Custom Properties (e.g., `--mst-primary-color`, `--mst-button-padding`) for colors, spacing, typography, etc., based on the Figma design. This is our primary mechanism for theming.
- **Material Theming** Utilize Angular Material's theming system and set CSS Custom properties based on the Material Theme in theme.scss file.

**Example (`shared.scss`):**

```scss
// shared.scss
// Located in: src/app/shared/styles/shared.scss

// Import Material Theme
@use "src/app/shared/styles/theme.scss" as *;

// --- Component Overrides ---

mst-button {
  // Target our wrapper component
  .mat-mdc-button {
    // Target the Material button class (Use .mat-mdc-button for MDC-based components)
    background-color: var(--mst-primary-color);
    color: var(--mst-text-color-light); // Example: Light text color
    border-radius: var(--mst-border-radius);
    padding: var(--mst-button-padding);

    &:hover {
      background-color: var(--mst-primary-color-hover);
    }

    &[disabled] {
      background-color: var(--mst-disabled-background-color);
      color: var(--mst-disabled-text-color);
    }
    &.mat-mdc-unelevated-button,
    &.mat-mdc-raised-button {
      box-shadow: none; // Remove Shadow
    }
  }
  .mat-mdc-outlined-button {
    border-color: var(--mst-primary-color);
    color: var(--mst-primary-color);
    &:hover {
      background-color: var(--mst-primary-color-light);
    }
  }
}

mst-input {
  .mat-mdc-form-field {
    .mat-mdc-text-field-wrapper {
      border-radius: var(--mst-border-radius);
    }
    .mat-mdc-input-element {
      // Input text styles
    }
    &.mat-focused {
      .mat-mdc-text-field-wrapper {
        // Focused state styles
        box-shadow: var(--mst-input-focus-shadow);
      }
    }
    .mat-mdc-form-field-subscript-wrapper {
      font-size: var(--mst-input-hint-font-size);
    }
  }
}

mst-card {
  .mat-mdc-card {
    box-shadow: var(--mst-card-box-shadow);
    border-radius: var(--mst-card-border-radius);
    .mat-mdc-card-content {
      padding: var(--mst-card-padding);
    }
  }
}
// ... more component overrides
```

**2.3. Local Component Styles (Optional):**

While `shared.scss` handles global overrides, you can also use component-specific stylesheets (e.g., `mst-button.component.scss`) for styles that are _only_ relevant to that particular component instance. Use this sparingly; favor global overrides for consistency.

**2.4. `theme.scss` (Material Theme and CSS Custom Property Definitions):**

This file is crucial for integrating Angular Material's theming system and defining our CSS Custom Properties.

```scss
// theme.scss
// Located in: src/app/shared/styles/theme.scss

@use "@angular/material" as mat;
@include mat.core();

// Define your color palettes (get values from Figma)
$my-primary: mat.define-palette(mat.$indigo-palette, 500, 100, 900); // Example
$my-accent: mat.define-palette(mat.$pink-palette, A200, A100, A400); // Example
$my-warn: mat.define-palette(mat.$red-palette);

// Create a Material theme
$my-theme: mat.define-light-theme(
  (
    color: (
      primary: $my-primary,
      accent: $my-accent,
      warn: $my-warn,
    ),
    typography: mat.define-typography-config(),
    // You can customize typography here
    density: 0,
  )
);

// Apply the theme to all Material components
@include mat.all-component-themes($my-theme);

// Define CSS Custom Properties, deriving values from the Material theme *where possible*.
:root {
  --mst-primary-color: #{mat.get-color-from-palette($my-primary, default)};
  --mst-primary-color-hover: #{mat.get-color-from-palette($my-primary, darker)};
  --mst-primary-color-light: #{mat.get-color-from-palette($my-primary, lighter)};
  --mst-accent-color: #{mat.get-color-from-palette($my-accent, default)};
  --mst-warn-color: #{mat.get-color-from-palette($my-warn, default)};
  --mst-text-color-light: #fff; // Example: Define text color for light backgrounds
  --mst-text-color-dark: #333;
  --mst-disabled-background-color: #bdbdbd;
  --mst-disabled-text-color: #616161;
  --mst-border-radius: 4px; // Get this from Figma!
  --mst-button-padding: 12px 24px; // Get this from Figma!
  --mst-input-focus-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  --mst-input-hint-font-size: 12px;
  --mst-card-box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
  --mst-card-border-radius: 8px;
  --mst-card-padding: 16px;

  // ... define other CSS Custom Properties based on Figma
}
```

**Import theme.scss file:**

```scss
// styles.scss
// Located in: src
@use "src/app/shared/styles/theme.scss" as *;
```

### 3. Color Palette, Typography, Spacing (Refer to Figma and Define as CSS Custom Properties)

- **Color Palette:** Define CSS Custom Properties for all colors in your `theme.scss` file, referencing the hex codes from Figma. Use the Material theme to generate shades where appropriate.
- **Typography:** Define CSS Custom Properties for font families, sizes, weights, and line heights in `theme.scss`, based on Figma.
- **Spacing:** Use an 8-point grid system. Define CSS Custom Properties for standard spacing units in `theme.scss` (e.g., `--mst-spacing-xs: 4px;`, `--mst-spacing-sm: 8px;`, etc.).

### 4. UI Design Elements (Examples)

_These examples demonstrate how to use the wrapper components. Refer to Figma and `shared.scss` for the actual styling._

- **Buttons:**

  ```html
  <mst-button color="primary" (onClick)="handlePrimaryClick()">Primary Button</mst-button>
  <mst-button color="accent" [disabled]="true">Disabled Accent Button</mst-button>
  <mst-button>Default Button</mst-button>
  ```

- **Form Fields:**

  ```html
  <mst-input [placeholder]="'Enter your email'" [type]="'email'"></mst-input> <mst-textarea [placeholder]="'Enter your message'"></mst-textarea>
  ```

- **Cards:**

  ```html
  <mst-card>
    <p>Card Content Here</p>
  </mst-card>
  ```

### 5. Accessibility, Iconography, Responsiveness

- **Accessibility:** Follow WCAG guidelines. Use ARIA attributes where needed. (See previous responses)
- **Iconography:** Use a consistent icon set (refer to Figma). You can create an `MstIcon` wrapper component to manage icons.
- **Responsiveness:** Design for different screen sizes using breakpoints (refer to Figma). Use media queries in `shared.scss` (or component-specific SCSS if absolutely necessary) to adjust styles as needed. You can use CSS Custom Properties within media queries to change values based on screen size.

### 6. Best Practices

- **Consistency:** Always refer to the Figma design and `shared.scss` for styling.
- **Component APIs:** Keep component APIs minimal and focused. Only expose necessary properties.
- **Documentation:** Document any custom components and their usage.
- **Code Reviews:** Review code to ensure adherence to the style guide.
- **Naming Convention:** Use consistent naming convention across the app.
- **Component Organization:** Keep a folder structor for the components.

## X. Recommended VS Code Extensions

These VS Code extensions are recommended to enhance productivity, enforce coding standards, and improve the overall development experience.

- **Angular Language Service:** Provides rich editing features for Angular templates, including autocompletion, error checking, and refactoring support. _Essential_ for Angular development.

  - **Identifier:** `angular.ng-template`
  - **Why:** Provides intelligent code completion, error highlighting, and Go to Definition within Angular templates.

- **ESLint:** Integrates ESLint into VS Code. ESLint is a powerful linter that helps you find and fix problems in your JavaScript/TypeScript code.

  - **Identifier:** `dbaeumer.vscode-eslint`
  - **Why:** Enforces coding style rules, catches potential errors, and helps maintain code quality. You'll need to configure ESLint with your project's rules (e.g., using an `.eslintrc.js` file). The Angular CLI sets this up for you.

- **Prettier - Code formatter:** An opinionated code formatter that automatically formats your code to ensure consistent style.

  - **Identifier:** `esbenp.prettier-vscode`
  - **Why:** Automates code formatting, enforcing consistent spacing, line breaks, and quotes. Configure Prettier with a `.prettierrc` file to match the style guide.

- **Stylelint:** A linter for your stylesheets (SCSS, CSS, etc.). Helps catch errors, enforce conventions, and avoid stylistic inconsistencies.

  - **Identifier:** `stylelint.vscode-stylelint`
  - **Why:** Enforces SCSS style rules (e.g., BEM, nesting depth, variable usage). You'll need a `.stylelintrc.js` (or similar) configuration file.

- **EditorConfig for VS Code:** Helps maintain consistent coding styles (indentation, line endings, etc.) across different editors and IDEs.

  - **Identifier:** `EditorConfig.EditorConfig`
  - **Why:** Ensures consistent basic formatting regardless of individual developer settings. Requires a `.editorconfig` file in your project root.

- **GitLens — Git supercharged:** Supercharges the Git capabilities built into VS Code. Helps you visualize code authorship, navigate and explore Git repositories, and more.

  - **Identifier:** `eamodio.gitlens`
  - **Why:** Provides valuable Git insights directly within the editor (blame annotations, code history, etc.).

- **Auto Import:** Automatically finds, parses and provides code actions and code completion for all available imports.

  - **Identifier:** `steoates.autoimport`
  - **Why:** Speeds up coding and keep the import statements clear.

- **Path Intellisense:** Autocompletes filenames.

  - **Identifier:** `christian-kohler.path-intellisense`
  - **Why:** Helps with file paths in imports, templateUrl, styleUrls, etc.

- **SCSS IntelliSense:** Provides Advanced Autocomplete and Refactoring support for SCSS.

  - **Identifier:** `mrmlnc.vscode-scss`
  - **Why:** Improve the SCSS coding experience

- **Bookmarks:** Allows you to mark lines of code and quickly jump between them.

  - **Identifier:** `alefragnani.bookmarks`
  - **Why:** Useful for navigating large files or marking areas for later review.

- **Bracket Pair Colorization Toggler:** Allows to quickly toggle the global bracket pair colorization setting.

  - **Identifier:** `CoenraadS.bracket-pair-colorizer-2` (Note: VS Code now has built-in bracket pair colorization, so this extension might not be necessary)
  - **Why:** Quickly distinguish the code blocks.

**Configuration:**

Many of these extensions require configuration files in your project root (e.g., `.eslintrc.js`, `.prettierrc`, `.stylelintrc.js`, `.editorconfig`). The Angular CLI often sets up some of these (like ESLint) automatically. Make sure these configuration files are consistent with the coding style guide. You can share these configuration files within your team to ensure everyone uses the same settings.

**Example Configurations (These would be in separate files):**

- **.editorconfig:**

  ```
  root = true

  [*]
  indent_style = space
  indent_size = 2
  end_of_line = lf
  charset = utf-8
  trim_trailing_whitespace = true
  insert_final_newline = true
  ```

- **.prettierrc:**

  ```json
  {
    "singleQuote": true,
    "trailingComma": "all",
    "printWidth": 120,
    "tabWidth": 2,
    "useTabs": false,
    "semi": true,
    "bracketSpacing": true,
    "arrowParens": "always"
  }
  ```

- **.eslintrc.js:** (This is often generated by the Angular CLI, and you'll customize it)

  ```javascript
  module.exports = {
    root: true,
    env: {
      browser: true,
      es2021: true,
      node: true,
    },
    extends: [
      "eslint:recommended",
      "plugin:@typescript-eslint/recommended", // Uses the recommended rules from the @typescript-eslint/eslint-plugin
      "plugin:@angular-eslint/recommended", // Uses the recommended rules from the @angular-eslint/eslint-plugin
      "prettier", // Uses eslint-config-prettier to disable ESLint rules from that would conflict with prettier
    ],
    parser: "@typescript-eslint/parser", // Specifies the ESLint parser
    parserOptions: {
      ecmaVersion: 2020, // Allows for the parsing of modern ECMAScript features
      sourceType: "module", // Allows for the use of imports
      project: "./tsconfig.json", // path to your tsconfig.json
    },
    plugins: ["@typescript-eslint", "@angular-eslint"],
    rules: {
      // Place to specify ESLint rules. Can be used to overwrite rules specified from the extended configs
      // e.g. "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/explicit-function-return-type": ["error"],
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": ["warn"],
      // ... add other custom rules here
    },
  };
  ```

- **.stylelintrc.js:**

  ```javascript
  module.exports = {
    extends: [
      "stylelint-config-standard-scss", // Use a standard SCSS config
      "stylelint-config-prettier-scss", // Turns off rules that conflict with Prettier
    ],
    plugins: ["stylelint-scss"],
    rules: {
      "selector-class-pattern": "^([a-z][a-z0-9]*)((__|--)[a-z0-9]+)*$", // BEM pattern
      "max-nesting-depth": 3,
      "at-rule-no-unknown": null, // Allow SCSS at-rules
      "scss/at-rule-no-unknown": true,
      "no-descending-specificity": null, // Sometimes necessary with component encapsulation.
      // ... add other custom rules here
    },
    ignoreFiles: ["**/node_modules/**"],
  };
  ```

## XII. Angular Unit Testing Style Guide

This section outlines best practices for writing unit tests in Angular applications. We primarily use Jasmine and Karma (or Jest), but the principles apply regardless of the specific testing framework.

**Core Principles:**

- **Isolation:** Test units (components, services, pipes) in _isolation_. Mock or stub dependencies.
- **Fast Execution:** Unit tests should be very fast to run.
- **Readability:** Tests should be easy to understand and maintain.
- **Test-Driven Development (TDD) (Optional but Recommended):** Consider writing tests _before_ writing the code they test. This helps clarify requirements and design.
- **FIRST Principles:**
  - **Fast:** Tests should run quickly.
  - **Independent/Isolated:** Tests should not depend on each other.
  - **Repeatable:** Tests should produce the same result every time.
  - **Self-Validating:** Tests should clearly pass or fail.
  - **Thorough/Timely:** Tests should cover important functionality and be written promptly.

**File Structure and Naming:**

- **Location:** Test files (`.spec.ts`) should be located in the same folder as the code they test (e.g., `product-list.component.spec.ts` alongside `product-list.component.ts`).
- **Naming:** Use the `.spec.ts` suffix for test files.

**Testing Components:**

- **`TestBed`:** Use `TestBed` to configure and create a testing module for your components.
- **`ComponentFixture`:** Use `ComponentFixture` to access the component instance and its associated DOM element.
- **`async` and `waitForAsync`:** Use `async` (or `waitForAsync`) to handle asynchronous operations within tests (e.g., component initialization).
- **`detectChanges()`:** Call `fixture.detectChanges()` to trigger change detection and update the DOM. Call this after setting up initial conditions and after making changes that should affect the view.
- **`beforeEach`:** Use `beforeEach` blocks to set up common test setup logic. This keeps your tests DRY.
- **`it`:** Use `it` blocks to define individual test cases. Use descriptive test names.
- **`expect`:** Use Jasmine's `expect` function to make assertions about the expected behavior of your code.
- **Mocking Dependencies:** Mock services and other dependencies to isolate the component under test. Use Jasmine's `createSpyObj` or create simple mock objects.
- **Shallow testing:** If the component depends on other custom components, it is preferred to use shallow testing with `NO_ERRORS_SCHEMA` to avoid testing nested components.

```typescript
// product-list.component.spec.ts
import { ComponentFixture, TestBed, waitForAsync } from "@angular/core/testing";
import { ProductListComponent } from "./product-list.component";
import { ProductService } from "../services/product.service";
import { of } from "rxjs";
import { NO_ERRORS_SCHEMA } from "@angular/core"; // Import NO_ERRORS_SCHEMA

describe("ProductListComponent", () => {
  let component: ProductListComponent;
  let fixture: ComponentFixture<ProductListComponent>;
  let mockProductService: jasmine.SpyObj<ProductService>; // Use jasmine.SpyObj

  beforeEach(waitForAsync(() => {
    // Create a spy object for the ProductService
    mockProductService = jasmine.createSpyObj("ProductService", ["getProducts"]);
    mockProductService.getProducts.and.returnValue(of([{ id: 1, name: "Product 1" }]));

    TestBed.configureTestingModule({
      declarations: [ProductListComponent],
      providers: [{ provide: ProductService, useValue: mockProductService }],
      schemas: [NO_ERRORS_SCHEMA], // Add NO_ERRORS_SCHEMA here
    }).compileComponents(); // Compile component template and CSS
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ProductListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });

  it("should display products", () => {
    expect(component.products.length).toBe(1);
    expect(component.products[0].name).toBe("Product 1");
  });

  it("should call getProducts on init", () => {
    expect(mockProductService.getProducts).toHaveBeenCalled();
  });

  it("should render product names in the template", () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector(".product-name")?.textContent).toContain("Product 1");
  });
});
```

**Testing Services:**

- **`TestBed.inject()`:** Use `TestBed.inject()` to get an instance of the service within your tests.
- **Mocking Dependencies:** Mock any dependencies of the service (e.g., `HttpClient`).
- **Asynchronous Operations:** Use `async`/`await`, `fakeAsync`, or `done` to handle asynchronous operations in service tests.

```typescript
// product.service.spec.ts
import { TestBed, fakeAsync, tick } from "@angular/core/testing";
import { HttpClientTestingModule, HttpTestingController } from "@angular/common/http/testing";
import { ProductService } from "./product.service";
import { Product } from "../models/product";

describe("ProductService", () => {
  let service: ProductService;
  let httpTestingController: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule], // Import HttpClientTestingModule
      providers: [ProductService],
    });

    service = TestBed.inject(ProductService);
    httpTestingController = TestBed.inject(HttpTestingController); // Get HttpTestingController
  });

  afterEach(() => {
    httpTestingController.verify(); // Ensure no outstanding requests
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  it("should get products", fakeAsync(() => {
    const mockProducts: Product[] = [{ id: 1, name: "Product 1" }];

    service.getProducts().subscribe((products) => {
      expect(products).toEqual(mockProducts);
    });

    const req = httpTestingController.expectOne("/api/products"); // Expect a request
    expect(req.request.method).toBe("GET");
    req.flush(mockProducts); // Respond with mock data
    tick(); // Simulate passage of time for the observable
  }));
});
```

**Testing Pipes:**

- **Instantiate Directly:** Pipes are simple classes, so you can often just create an instance of the pipe and call its `transform` method directly.

```typescript
// uppercase.pipe.spec.ts
import { UppercasePipe } from "./uppercase.pipe";

describe("UppercasePipe", () => {
  let pipe: UppercasePipe;

  beforeEach(() => {
    pipe = new UppercasePipe();
  });

  it("should transform to uppercase", () => {
    expect(pipe.transform("hello")).toBe("HELLO");
  });

  it("should handle null/undefined", () => {
    expect(pipe.transform(null)).toBeNull();
    expect(pipe.transform(undefined)).toBeUndefined();
  });
});
```

**Testing Directives:**

- **Create Test Component:** Create a test component that _uses_ the directive. This allows you to test how the directive interacts with the DOM.

```typescript
// my-directive.directive.spec.ts
import { Component } from "@angular/core";
import { ComponentFixture, TestBed } from "@angular/core/testing";
import { MyDirectiveDirective } from "./my-directive.directive";

@Component({
  template: `<div myDirectiveDirective></div>`, // Use the directive in the template
})
class TestHostComponent {} // Create a test component

describe("MyDirectiveDirective", () => {
  let component: TestHostComponent;
  let fixture: ComponentFixture<TestHostComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MyDirectiveDirective, TestHostComponent], // Declare both
    }).compileComponents();

    fixture = TestBed.createComponent(TestHostComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create an instance", () => {
    expect(component).toBeTruthy();
  });

  // Add tests to verify the directive's behavior,
  // e.g., by inspecting the DOM after triggering events.
});
```

## XIII. Pull Request (PR) Guidelines (Bitbucket)

This section outlines the process for creating and reviewing Pull Requests (PRs) in our Bitbucket repository.

**Branch Naming:**

- All branch names **must** follow the format: `HEXAIND-<issue_number>-<short-description>`.

  - `HEXAIND`: A project prefix (replace with your actual project prefix if different).
  - `<issue_number>`: The Jira/Bitbucket issue number this branch addresses.
  - `<short-description>`: A brief, kebab-cased description of the change.

  _Examples:_

  - `HEXAIND-123-add-product-list-component`
  - `HEXAIND-456-fix-login-button-bug`
  - `HEXAIND-789-refactor-auth-service`

**Automated Checks (Pre-Commit and CI/CD):**

We use automated checks to ensure code quality and consistency before merging PRs. These checks are enforced in two stages:

1.  **Pre-Commit Hooks (Local):**

    - **Purpose:** Run checks _locally_ before you even commit your changes. This catches errors early and prevents them from reaching the repository.
    - **Tool:** We use [Husky](https://typicode.github.io/husky/) to manage Git hooks.
    - **Setup:**
      1.  Install Husky: `npm install husky --save-dev`
      2.  Enable Git hooks: `npx husky install`
      3.  Add a pre-commit hook: `npx husky add .husky/pre-commit "npm run lint && npm run format:check && npm test"`
      - This creates a `.husky/pre-commit` file that will run `npm run lint`, `npm run format:check`, and `npm test` before each commit.
    - **package.json**: Make sure that you define scripts.
      ```json
      {
        "scripts": {
          "lint": "eslint . --ext .ts",
          "format:check": "prettier --check \"src/**/*.ts\" \"src/**/*.html\" \"src/**/*.scss\"",
          "format": "prettier --write \"src/**/*.ts\" \"src/**/*.html\" \"src/**/*.scss\"",
          "test": "ng test --watch=false --browsers=ChromeHeadless"
        }
      }
      ```

2.  **Continuous Integration (CI/CD) Pipeline (Bitbucket Pipelines):**

    - **Purpose:** Run checks on the Bitbucket server whenever a PR is created or updated. This provides a second layer of verification and ensures that all code meets our standards.
    - **Tool:** We use Bitbucket Pipelines for CI/CD.
    - **Setup:**

      1.  Create a `bitbucket-pipelines.yml` file in the root of your repository.
      2.  Define your pipeline steps within this file. A basic pipeline might look like this:

          ```yaml
          # bitbucket-pipelines.yml
          pipelines:
            pull-requests:
              "**": # Run on all pull requests
                - step:
                    name: Build and Test
                    image: node:16 # Or your desired Node.js version
                    caches:
                      - node # Cache node_modules for faster builds
                    script:
                      - npm ci # Use npm ci for consistent installs
                      - npm run lint
                      - npm run format:check
                      - npm run build -- --configuration production
                      - npm run test -- --no-watch --code-coverage # Run unit tests
                      - npm run e2e # Run E2E tests (if applicable)
          ```

    - **Key Pipeline Steps:**
      - **`npm ci`:** Installs dependencies using the exact versions specified in `package-lock.json`. This ensures consistent builds.
      - **`npm run lint`:** Runs ESLint to check for code style and potential errors.
      - **`npm run format:check`:** Checks if code is formatted according to Prettier rules (without modifying files).
      - **`npm run build`:** Builds the Angular application (in production mode). This catches compilation errors.
      - **`npm run test`:** Runs unit tests. `--no-watch` prevents the tests from running continuously. `--code-coverage` generates a coverage report.
      - **`npm run e2e`:** Run E2E tests.

**Creating a Pull Request:**

1.  **Create a Branch:** Create a new branch from the `main` (or `develop`, if you use a Gitflow-like workflow) branch, following the naming convention above.
2.  **Commit Your Changes:** Make your code changes, commit them frequently, and push to your branch. Ensure your pre-commit hooks pass.
3.  **Create the PR:** In Bitbucket, create a pull request from your feature branch to the target branch (`main` or `develop`).
4.  **PR Title:** The PR title should be concise and descriptive. It's often good to start with the issue key (e.g., `HEXAIND-123: Add product list component`).
5.  **PR Description:**
    - Provide a clear and detailed description of the changes.
    - Link to the relevant Jira/Bitbucket issue.
    - Explain the purpose of the change, the approach taken, and any relevant context.
    - If there are UI changes, include screenshots or GIFs.
6.  **Assign Reviewers:** Assign at least one reviewer (ideally, someone familiar with the affected code).
7.  **Address Feedback:** Respond to reviewer comments and make any necessary changes. Push updates to your branch; the PR will update automatically.
8.  **Merge:** Once the PR is approved and all checks pass, it can be merged into the target branch. Use the "Squash and Merge" option in Bitbucket to keep the commit history clean.

**Reviewing a Pull Request:**

1.  **Understand the Changes:** Read the PR description and review the linked issue to understand the context.
2.  **Check Code Quality:** Review the code for:
    - Adherence to the coding style guide.
    - Clarity, readability, and maintainability.
    - Potential bugs or errors.
    - Test coverage (unit and E2E).
    - Security vulnerabilities.
3.  **Test the Changes (Optional but Recommended):** Check out the branch locally and test the changes manually, especially if they involve UI or complex logic.
4.  **Provide Feedback:**
    - Leave clear and constructive comments.
    - Be specific about what needs to be changed and why.
    - Use Bitbucket's comment features (inline comments, suggestions).
    - Approve the PR when you're satisfied.

# HEXAIND 3.0 UI Style Guide

## 1. Introduction

This style guide outlines the visual language for HEXAIND 3.0. It ensures consistency and usability across the user interface. Adhering to these guidelines will create a cohesive and recognizable brand experience.

**Figma Design Link (Source of Truth for Values):** [HEXAIND 3.0 Figma Design](https://www.figma.com/design/ss0UQYn3u3lAG3t90OQnjy/HEXAIND-3.0?node-id=26-3&p=f&t=nfT6Ymi9hmJjTPRo-0)

**All specific values (sizes, precise colors, spacing, etc.) should be obtained from the Figma design file linked above. This document provides the general principles and structure; Figma is the definitive source for implementation details.**

## 2. Color Palette

The color palette is designed to be modern and energetic, reflecting innovation and forward-thinking.

- **Primary Colors:** _(Refer to Figma for definitive hex codes and usage)_

  - **Primary - Main:**

    - **Hex:** (See Figma)
    - **RGB:** (See Figma)
    - **Usage:** Main calls to action, primary buttons, active navigation elements, links.
    - **Accessibility Note:** Ensure sufficient contrast. WCAG AA: 4.5:1 (normal text), 3:1 (large text).

  - **Primary - Dark:**

    - **Hex:** (See Figma)
    - **RGB:** (See Figma)
    - **Usage:** Hover states, active states, text links on light backgrounds.

  - **Primary - Light:**
    - **Hex:** (See Figma)
    - **RGB:** (See Figma)
    - **Usage:** Background for selected items, subtle highlights, separators.

- **Secondary Colors:** _(Refer to Figma for definitive hex codes and usage)_

  - **Secondary - Accent:**

    - **Hex:** (See Figma)
    - **RGB:** (See Figma)
    - **Usage:** Secondary buttons, notifications, progress indicators. Use sparingly.

  - **Secondary - Neutral:**

    - **Hex:** (See Figma)
    - **RGB:** (See Figma)
    - **Usage:** Default background, card backgrounds, inactive form fields.

  - **Secondary - Dark Neutral:**
    - **Hex:** (See Figma)
    - **RGB:** (See Figma)
    - **Usage:** Default text color.

- **Status Colors:** _(Refer to Figma for definitive hex codes and usage)_

  - **Success:**

    - **Hex:** (See Figma)
    - **RGB:** (See Figma)
    - **Usage:** Success messages, validation success, completed actions.

  - **Warning:**

    - **Hex:** (See Figma)
    - **RGB:** (See Figma)
    - **Usage:** Warning messages, potential issues, non-critical alerts.

  - **Error:**

    - **Hex:** (See Figma)
    - **RGB:** (See Figma)
    - **Usage:** Error messages, validation errors, critical alerts.

  - **Information:**
    - **Hex:** (See Figma)
    - **RGB:** (See Figma)
    - **Usage:** Informational messages, tooltips, hints.

## 3. UI Design Elements

- **Buttons:** _(Refer to Figma for all dimensions, visual examples, and specific states)_

  - **Primary Button:** _General Style:_ Filled button with the primary color. _See Figma for all details._
  - **Secondary Button:** _General Style:_ Either a filled button with the accent color or an outlined button with the primary color. _See Figma for all details._
  - \*_Text Button (Link Button):_ _General Style:_ Text-only button using the primary color. _See Figma for all details._

- **Form Fields:** _(Refer to Figma for all dimensions, visual examples, and specific states)_

  - **Input Fields:** _General Style:_ Input fields with a subtle border. _See Figma for all details._
  - **Textarea:** _General Style:_ Larger input field for multi-line text. _See Figma for all details._
  - **Select Dropdowns:** _General Style:_ Dropdown selection. _See Figma for all details; consider a library for implementation._
  - **Checkboxes and Radio Buttons:** _General Style:_ Standard checkbox and radio button styles. _See Figma for all details._
  - **Labels:** _General Style:_ Labels for Form Fields. _See Figma for all details._

- **Cards:** _(Refer to Figma for all dimensions and visual examples)_

  - **General Style:** Containers for displaying content, typically with a subtle background and shadow. _See Figma for all details._

- **Modals/Dialogs:** _(Refer to Figma for all dimensions and visual examples)_

  - **General Style:** Overlays for displaying important information or prompting user interaction. _See Figma for all details._

- **Typography:** _(Refer to Figma for final font choices, sizes, weights, line heights, and usage)_

  - **Heading 1 (H1):** _See Figma_
  - **Heading 2 (H2):** _See Figma_
  - **Heading 3 (H3):** _See Figma_
  - **Heading 4 (H4):** _See Figma_
  - **Body Text:** _See Figma_

## 4. Accessibility Considerations

- **Contrast Ratios:** Meet WCAG AA guidelines (4.5:1 normal text, 3:1 large text). _Verify in Figma using contrast checker plugins._
- **Keyboard Navigation:** All interactive elements navigable by keyboard.
- **ARIA Attributes:** Use ARIA attributes for custom components to improve screen reader compatibility.
- **Alt Text:** Descriptive alt text for all images.
- **Focus Styles:** Clear and visible focus styles.

## 5. Iconography

- Use a consistent icon set. _(Refer to Figma for chosen icon set)_
- Icons should be simple, clear, and recognizable.
- Consistent sizing and styling. _(Refer to Figma)_

## 6. Spacing and Layout

- Use an 8-point grid system. _(Refer to Figma for implementation details)_
- Standard spacing units: 4px, 8px, 16px, 24px, 32px. _(Refer to Figma for consistent application)_
- Use whitespace effectively.

## 7. Responsiveness

- **Breakpoints:** _(Confirm final breakpoints in Figma and during development)_
  - Mobile: < 600px _(Confirm in Figma)_
  - Tablet: 600px - 960px _(Confirm in Figma)_
  - Desktop: > 960px _(Confirm in Figma)_
- _(Refer to Figma for responsive designs and how elements adapt at each breakpoint)_

## 8. CSS Variables and Theming

- All colors must be defined as CSS variables.
- All sizes (padding, margin, icon size, font-size, font-weight, etc.) must be defined as CSS variables.
- Light and dark themes must be implemented using Angular Material's theming system or a similar approach. Refer to the Angular Material documentation for theme customization.
