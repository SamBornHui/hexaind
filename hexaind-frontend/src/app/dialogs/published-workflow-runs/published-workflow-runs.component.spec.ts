import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PublishedWorkflowRunsComponent } from './published-workflow-runs.component';

describe('PublishedWorkflowRunsComponent', () => {
  let component: PublishedWorkflowRunsComponent;
  let fixture: ComponentFixture<PublishedWorkflowRunsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PublishedWorkflowRunsComponent]
    });
    fixture = TestBed.createComponent(PublishedWorkflowRunsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
