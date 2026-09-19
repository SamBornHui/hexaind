import { TestBed } from '@angular/core/testing';

import { RescaleWidgetService } from './rescale-widget.service';

describe('RescaleService', () => {
  let service: RescaleWidgetService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(RescaleWidgetService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
