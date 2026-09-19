import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateJupyterNotebookComponent } from './create-jupyter-notebook.component';

describe('CreateJupyterNotebookComponent', () => {
  let component: CreateJupyterNotebookComponent;
  let fixture: ComponentFixture<CreateJupyterNotebookComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CreateJupyterNotebookComponent]
    });
    fixture = TestBed.createComponent(CreateJupyterNotebookComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
