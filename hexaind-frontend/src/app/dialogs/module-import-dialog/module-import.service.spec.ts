import { TestBed } from '@angular/core/testing';

import { ModuleImportService } from './module-import.service';

describe('ModuleImportService', () => {
  let service: ModuleImportService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ModuleImportService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
