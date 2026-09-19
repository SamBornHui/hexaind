import { TestBed } from '@angular/core/testing';

import { WorkflowCanvasService } from './workflow-canvas.service';

describe('EditWorkflowService', () => {
  let service: WorkflowCanvasService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(WorkflowCanvasService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
