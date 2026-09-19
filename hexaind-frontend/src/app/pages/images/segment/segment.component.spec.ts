import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImageSegmentComponent } from './segment.component';

describe('ImageSegmentComponent', () => {
  let component: ImageSegmentComponent;
  let fixture: ComponentFixture<ImageSegmentComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ImageSegmentComponent]
    });
    fixture = TestBed.createComponent(ImageSegmentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
