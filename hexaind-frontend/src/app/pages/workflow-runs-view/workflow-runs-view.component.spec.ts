import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkflowRunsViewComponent } from './workflow-runs-view.component';

describe('WorkflowRunsViewComponent', () => {
  let component: WorkflowRunsViewComponent;
  let fixture: ComponentFixture<WorkflowRunsViewComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [WorkflowRunsViewComponent]
    });
    fixture = TestBed.createComponent(WorkflowRunsViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
