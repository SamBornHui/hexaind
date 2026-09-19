import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UpdateWorkflowSessionComponent } from './update-workflow-session.component';

describe('UpdateWorkflowComponent', () => {
  let component: UpdateWorkflowSessionComponent;
  let fixture: ComponentFixture<UpdateWorkflowSessionComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [UpdateWorkflowSessionComponent],
    });
    fixture = TestBed.createComponent(UpdateWorkflowSessionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
