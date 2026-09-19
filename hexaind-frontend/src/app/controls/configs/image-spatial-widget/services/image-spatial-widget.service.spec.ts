import { TestBed } from '@angular/core/testing';

import { ImageSpatialWidgetService } from './image-spatial-widget.service';

describe('ImageSpatialWidgetService', () => {
  let service: ImageSpatialWidgetService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ImageSpatialWidgetService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
