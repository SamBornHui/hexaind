import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ColumnPickerPanelComponent } from './column-picker-panel.component';

describe('ColumnPickerPanelComponent', () => {
  let component: ColumnPickerPanelComponent;
  let fixture: ComponentFixture<ColumnPickerPanelComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ColumnPickerPanelComponent]
    });
    fixture = TestBed.createComponent(ColumnPickerPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
