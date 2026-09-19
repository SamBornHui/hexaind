import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ColumnDropDownComponent } from './column-drop-down.component';

describe('ColumnDropDownComponent', () => {
  let component: ColumnDropDownComponent;
  let fixture: ComponentFixture<ColumnDropDownComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ColumnDropDownComponent]
    });
    fixture = TestBed.createComponent(ColumnDropDownComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
