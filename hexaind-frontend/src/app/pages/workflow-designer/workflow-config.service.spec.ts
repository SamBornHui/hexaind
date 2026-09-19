import { TestBed } from '@angular/core/testing';

import { WorkflowConfigService } from './workflow-config.service';

describe('WorkflowConfigService', () => {
  let service: WorkflowConfigService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(WorkflowConfigService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
