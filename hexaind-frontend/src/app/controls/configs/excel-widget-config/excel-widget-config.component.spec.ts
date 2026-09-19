import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExcelWidgetConfigComponent } from './excel-widget-config.component';

describe('ExcelWidgetConfigComponent', () => {
  let component: ExcelWidgetConfigComponent;
  let fixture: ComponentFixture<ExcelWidgetConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ExcelWidgetConfigComponent]
    });
    fixture = TestBed.createComponent(ExcelWidgetConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
