import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkflowRunPreviewComponent } from './workflow-run-preview.component';

describe('WorkflowRunPreviewComponent', () => {
  let component: WorkflowRunPreviewComponent;
  let fixture: ComponentFixture<WorkflowRunPreviewComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [WorkflowRunPreviewComponent]
    });
    fixture = TestBed.createComponent(WorkflowRunPreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
