import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TravelerStepsComponent } from './traveler-steps.component';

describe('TravelerStepsComponent', () => {
  let component: TravelerStepsComponent;
  let fixture: ComponentFixture<TravelerStepsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [TravelerStepsComponent]
    });
    fixture = TestBed.createComponent(TravelerStepsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
