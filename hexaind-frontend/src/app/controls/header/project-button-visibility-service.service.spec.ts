import { TestBed } from '@angular/core/testing';

import { ProjectButtonVisibilityServiceService } from './project-button-visibility-service.service';

describe('ProjectButtonVisibilityServiceService', () => {
  let service: ProjectButtonVisibilityServiceService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ProjectButtonVisibilityServiceService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
