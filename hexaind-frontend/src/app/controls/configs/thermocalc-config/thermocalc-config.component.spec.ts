import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ThermoCalcConfigComponent } from './thermocalc-config.component';

describe('ThermoCalcConfigComponent', () => {
  let component: ThermoCalcConfigComponent;
  let fixture: ComponentFixture<ThermoCalcConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ThermoCalcConfigComponent]
    });
    fixture = TestBed.createComponent(ThermoCalcConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
