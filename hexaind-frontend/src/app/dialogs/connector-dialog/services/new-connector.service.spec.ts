import { TestBed } from '@angular/core/testing';

import { NewConnectorService } from './new-connector.service';

describe('NewConnectorService', () => {
  let service: NewConnectorService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(NewConnectorService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
