import { ComponentFixture, TestBed } from '@angular/core/testing';
import { UC1TrainPredictionsComponent } from './uc1-models-predictions.component';

describe('UC1TrainPredictionsComponent', () => {
  let component: UC1TrainPredictionsComponent;
  let fixture: ComponentFixture<UC1TrainPredictionsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [UC1TrainPredictionsComponent],
    });
    fixture = TestBed.createComponent(UC1TrainPredictionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
