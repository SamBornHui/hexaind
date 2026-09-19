import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ShareWorkflowTemplateComponent } from './share-workflow-template.component';

describe('CreateNewWorkflowTemplateComponent', () => {
  let component: ShareWorkflowTemplateComponent;
  let fixture: ComponentFixture<ShareWorkflowTemplateComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ShareWorkflowTemplateComponent],
    });
    fixture = TestBed.createComponent(ShareWorkflowTemplateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
