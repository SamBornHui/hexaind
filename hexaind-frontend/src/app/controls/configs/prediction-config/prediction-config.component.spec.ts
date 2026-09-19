import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PredictionConfigComponent } from './prediction-config.component';

describe('PredictionConfigComponent', () => {
  let component: PredictionConfigComponent;
  let fixture: ComponentFixture<PredictionConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PredictionConfigComponent]
    });
    fixture = TestBed.createComponent(PredictionConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
