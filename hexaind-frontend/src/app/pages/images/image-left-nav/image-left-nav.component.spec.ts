import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImageLeftNavComponent } from './image-left-nav.component';

describe('ImageLeftNavComponent', () => {
  let component: ImageLeftNavComponent;
  let fixture: ComponentFixture<ImageLeftNavComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ImageLeftNavComponent]
    });
    fixture = TestBed.createComponent(ImageLeftNavComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
