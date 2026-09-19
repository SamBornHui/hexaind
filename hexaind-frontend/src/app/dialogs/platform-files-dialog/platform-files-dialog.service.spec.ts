import { TestBed } from '@angular/core/testing';

import { PlatformFilesDialogService } from "./platform-files-dialog.service";

describe('PlatformFilesDialogService', () => {
  let service: PlatformFilesDialogService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PlatformFilesDialogService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
