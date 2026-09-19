import { TestBed } from '@angular/core/testing';

import { WorkflowDesignerServiceService } from './workflow-designer-service.service';

describe('WorkflowDesignerServiceService', () => {
  let service: WorkflowDesignerServiceService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(WorkflowDesignerServiceService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
