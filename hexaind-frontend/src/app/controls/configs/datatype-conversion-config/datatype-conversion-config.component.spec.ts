import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DatatypeConversionConfigComponent } from './datatype-conversion-config.component';

describe('DatatypeConversionConfigComponent', () => {
  let component: DatatypeConversionConfigComponent;
  let fixture: ComponentFixture<DatatypeConversionConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DatatypeConversionConfigComponent]
    });
    fixture = TestBed.createComponent(DatatypeConversionConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
