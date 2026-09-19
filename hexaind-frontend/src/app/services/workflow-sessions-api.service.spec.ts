import { TestBed } from '@angular/core/testing';

import { WorkflowsSessionsApiService } from './workflow-sessions-api.service';

describe('WorkflowsApiService', () => {
  let service: WorkflowsSessionsApiService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(WorkflowsSessionsApiService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
