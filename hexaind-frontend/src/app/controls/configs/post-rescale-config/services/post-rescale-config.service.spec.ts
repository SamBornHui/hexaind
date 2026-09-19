import { TestBed } from '@angular/core/testing';

import { PostRescaleConfigService } from './post-rescale-config.service';

describe('PostRescaleConfigService', () => {
  let service: PostRescaleConfigService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PostRescaleConfigService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
