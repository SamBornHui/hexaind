import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UC2SigmaDataPreviewComponent } from './uc2-sigma-data-preview.component';

describe('UC2SigmaDataPreviewComponent', () => {
  let component: UC2SigmaDataPreviewComponent;
  let fixture: ComponentFixture<UC2SigmaDataPreviewComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [UC2SigmaDataPreviewComponent]
    });
    fixture = TestBed.createComponent(UC2SigmaDataPreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
