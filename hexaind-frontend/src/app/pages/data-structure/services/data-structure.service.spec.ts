import { TestBed } from '@angular/core/testing';

import { DataStructureService } from './data-structure.service';

describe('DataService', () => {
  let service: DataStructureService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(DataStructureService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
