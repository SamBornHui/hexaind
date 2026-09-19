import { TestBed } from '@angular/core/testing';

import { PredictionWidgetService } from './prediction-widget.service';

describe('PredictionWidgetService', () => {
  let service: PredictionWidgetService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PredictionWidgetService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
