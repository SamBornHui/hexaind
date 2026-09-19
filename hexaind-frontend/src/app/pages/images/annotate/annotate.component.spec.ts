import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImageAnnotateComponent } from './annotate.component';

describe('ImageAnnotateComponent', () => {
  let component: ImageAnnotateComponent;
  let fixture: ComponentFixture<ImageAnnotateComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ImageAnnotateComponent]
    });
    fixture = TestBed.createComponent(ImageAnnotateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
