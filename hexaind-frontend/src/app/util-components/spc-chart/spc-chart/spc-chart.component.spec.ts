import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SpcChartComponent } from './spc-chart.component';

describe('SpcChartComponent', () => {
  let component: SpcChartComponent;
  let fixture: ComponentFixture<SpcChartComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [SpcChartComponent]
    });
    fixture = TestBed.createComponent(SpcChartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
