import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImageRegionPropertiesWidgetComponent } from './image-region-properties-widget.component';

describe('ImageRegionPropertiesWidgetComponent', () => {
  let component: ImageRegionPropertiesWidgetComponent;
  let fixture: ComponentFixture<ImageRegionPropertiesWidgetComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ImageRegionPropertiesWidgetComponent]
    });
    fixture = TestBed.createComponent(ImageRegionPropertiesWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
