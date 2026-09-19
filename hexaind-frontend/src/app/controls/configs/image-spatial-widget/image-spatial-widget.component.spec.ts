import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImageSpatialWidgetComponent } from './image-spatial-widget.component';

describe('ImageSpatialWidgetComponent', () => {
  let component: ImageSpatialWidgetComponent;
  let fixture: ComponentFixture<ImageSpatialWidgetComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ImageSpatialWidgetComponent]
    });
    fixture = TestBed.createComponent(ImageSpatialWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
