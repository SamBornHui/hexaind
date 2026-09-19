import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImagesPreviewComponent } from './preview.component';

describe('ImagesPreviewComponent', () => {
  let component: ImagesPreviewComponent;
  let fixture: ComponentFixture<ImagesPreviewComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ImagesPreviewComponent]
    });
    fixture = TestBed.createComponent(ImagesPreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
