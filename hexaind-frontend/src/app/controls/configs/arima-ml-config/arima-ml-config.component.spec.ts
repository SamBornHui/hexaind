import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ArimaMlConfigComponent } from './arima-ml-config.component';

describe('ArimaMlConfigComponent', () => {
  let component: ArimaMlConfigComponent;
  let fixture: ComponentFixture<ArimaMlConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ArimaMlConfigComponent],
    });
    fixture = TestBed.createComponent(ArimaMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
