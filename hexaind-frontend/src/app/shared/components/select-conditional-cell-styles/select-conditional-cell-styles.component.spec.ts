/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SelectConditionalCellStylesComponent } from './select-conditional-cell-styles.component';

describe('SelectConditionalCellStylesComponent', () => {
  let component: SelectConditionalCellStylesComponent;
  let fixture: ComponentFixture<SelectConditionalCellStylesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [SelectConditionalCellStylesComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SelectConditionalCellStylesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
