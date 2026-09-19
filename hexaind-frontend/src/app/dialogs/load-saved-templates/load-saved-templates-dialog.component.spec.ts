import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LoadWorkflowTemplatesDialogComponent } from './load-saved-templates-dialog.component';

describe('LoadWorkflowTemplatesDialogComponent', () => {
  let component: LoadWorkflowTemplatesDialogComponent;
  let fixture: ComponentFixture<LoadWorkflowTemplatesDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [LoadWorkflowTemplatesDialogComponent]
    });
    fixture = TestBed.createComponent(LoadWorkflowTemplatesDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
