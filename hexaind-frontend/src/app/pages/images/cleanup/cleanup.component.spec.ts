import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImageCleanupComponent } from './cleanup.component';

describe('ImageCleanupComponent', () => {
  let component: ImageCleanupComponent;
  let fixture: ComponentFixture<ImageCleanupComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ImageCleanupComponent]
    });
    fixture = TestBed.createComponent(ImageCleanupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
