import { ComponentFixture, TestBed } from '@angular/core/testing';

import { JupyterNotebooksComponent } from './jupyter-notebooks.component';

describe('JupyterNotebooksComponent', () => {
  let component: JupyterNotebooksComponent;
  let fixture: ComponentFixture<JupyterNotebooksComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [JupyterNotebooksComponent],
    });
    fixture = TestBed.createComponent(JupyterNotebooksComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
