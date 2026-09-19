import { TestBed } from '@angular/core/testing';
import { DataVisualizationService } from './data-visualization.service';

describe('DataVisualizationService', () => {
  let service: DataVisualizationService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(DataVisualizationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
