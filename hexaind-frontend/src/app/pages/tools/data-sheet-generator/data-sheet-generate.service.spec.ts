import { TestBed } from '@angular/core/testing';

import { DataSheetGenerateService } from './data-sheet-generate.service';

describe('DataSheetGenerateService', () => {
  let service: DataSheetGenerateService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(DataSheetGenerateService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
