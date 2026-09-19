import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateNewWorkflowTemplateComponent } from './create-new-workflow-template.component';

describe('CreateNewWorkflowTemplateComponent', () => {
  let component: CreateNewWorkflowTemplateComponent;
  let fixture: ComponentFixture<CreateNewWorkflowTemplateComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CreateNewWorkflowTemplateComponent],
    });
    fixture = TestBed.createComponent(CreateNewWorkflowTemplateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
