import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImageVideoPreviewComponent } from './image-video-preview.component';

describe('ImageVideoPreviewComponent', () => {
  let component: ImageVideoPreviewComponent;
  let fixture: ComponentFixture<ImageVideoPreviewComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ImageVideoPreviewComponent]
    });
    fixture = TestBed.createComponent(ImageVideoPreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
