import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateNewWorkflowSessionComponent } from './create-new-workflow-session.component';

describe('CreateNewWorkflowSessionComponent', () => {
  let component: CreateNewWorkflowSessionComponent;
  let fixture: ComponentFixture<CreateNewWorkflowSessionComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CreateNewWorkflowSessionComponent],
    });
    fixture = TestBed.createComponent(CreateNewWorkflowSessionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
