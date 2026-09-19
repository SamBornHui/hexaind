import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkflowDesignerHeaderComponent } from './workflow-designer-header.component';

describe('WorkflowDesignerHeaderComponent', () => {
  let component: WorkflowDesignerHeaderComponent;
  let fixture: ComponentFixture<WorkflowDesignerHeaderComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [WorkflowDesignerHeaderComponent]
    });
    fixture = TestBed.createComponent(WorkflowDesignerHeaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
