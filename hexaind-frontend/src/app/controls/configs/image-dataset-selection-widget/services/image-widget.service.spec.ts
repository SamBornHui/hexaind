import { TestBed } from '@angular/core/testing';

import { ImageWidgetService } from './image-widget.service';

describe('ImageWidgetService', () => {
  let service: ImageWidgetService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ImageWidgetService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
