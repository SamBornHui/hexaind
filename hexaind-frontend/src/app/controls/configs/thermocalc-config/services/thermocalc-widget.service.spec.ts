import { TestBed } from '@angular/core/testing';

import { ThermoCalcWidgetService } from './thermocalc-widget.service';

describe('ThermoCalcWidgetService', () => {
  let service: ThermoCalcWidgetService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ThermoCalcWidgetService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
