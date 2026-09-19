import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParquetWidgetConfigComponent } from './parquet-widget-config.component';

describe('ParquetWidgetConfigComponent', () => {
  let component: ParquetWidgetConfigComponent;
  let fixture: ComponentFixture<ParquetWidgetConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ParquetWidgetConfigComponent]
    });
    fixture = TestBed.createComponent(ParquetWidgetConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
