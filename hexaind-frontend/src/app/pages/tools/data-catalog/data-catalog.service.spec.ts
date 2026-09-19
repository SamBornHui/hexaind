import { TestBed } from '@angular/core/testing';

import { DataCatalogService } from './data-catalog.service';

describe('DataCatalogService', () => {
  let service: DataCatalogService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(DataCatalogService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
