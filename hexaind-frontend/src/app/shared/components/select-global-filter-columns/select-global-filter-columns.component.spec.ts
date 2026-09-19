/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { SelectGlobalFilterColumnsComponent } from './select-global-filter-columns.component';

describe('SelectGlobalFilterColumnsComponent', () => {
  let component: SelectGlobalFilterColumnsComponent;
  let fixture: ComponentFixture<SelectGlobalFilterColumnsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SelectGlobalFilterColumnsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SelectGlobalFilterColumnsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
