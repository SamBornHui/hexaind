import { TestBed } from '@angular/core/testing';

import { DataPreviewService } from './data-preview.service';

describe('DataPreviewService', () => {
  let service: DataPreviewService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(DataPreviewService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
